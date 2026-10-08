#!/usr/bin/env python3
"""Emit, compile, and compare the three controller walks with CRuby 4.0.7."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
FLAGS = dict(RH_FOLD='1', RH_FOLD_SLOTS='1', RH_FOLD_JOIN='1', RH_BRK_ALLARMS='1',
             RH_FOLD_TAIL='1', RH_SCHED='sccq', RH_EMIT_REC='1', RH_FOLD_PRINT='1')


def clean_env():
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('RH_', 'ROUNDHOUSE_', 'BUNDLE_'))}


def run(command, cwd, env, log):
    result = subprocess.run([str(x) for x in command], cwd=cwd, env=env, capture_output=True, text=True)
    log.write_text(result.stdout + result.stderr)
    return result


def fetch_page(command, cwd, env, path, log):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with log.open('w') as handle:
        server = subprocess.Popen([str(x) for x in command], cwd=cwd,
                                  env=dict(env, PORT=str(port)), stdout=handle, stderr=handle,
                                  start_new_session=True)
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError('server exited before answering')
                try:
                    with urlopen('http://127.0.0.1:' + str(port) + path, timeout=1) as response:
                        return response.read()
                except (URLError, TimeoutError):
                    time.sleep(0.2)
            raise RuntimeError('server did not answer in 20 seconds')
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


def rust_template(body):
    opening = b'<main class="container mx-auto mt-28 px-5 flex flex-col">\n      '
    start, end = body.find(opening), body.rfind(b'\n    </main>')
    if start < 0 or end < 0:
        raise RuntimeError('missing real-blog layout yield region')
    return body[start + len(opening):end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--crystal', type=Path, required=True)
    parser.add_argument('--sqlite3', type=Path, required=True, help='crystal-sqlite3 checkout, version 0.23.0')
    parser.add_argument('--db', type=Path, required=True, help='crystal-db checkout, version 0.15.0')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--targets', choices=['rust', 'crystal'], nargs='+', default=['rust', 'crystal'])
    args = parser.parse_args()
    binary, crystal = args.binary.resolve(), args.crystal.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ruby = subprocess.check_output(['ruby', '-e', 'print RUBY_VERSION'], env=clean_env(), text=True)
    if ruby != '4.0.7':
        raise RuntimeError('CRuby 4.0.7 required, found ' + ruby)
    base_env = dict(clean_env(), CARGO_BUILD_JOBS='4', CARGO_TARGET_DIR=str(out / 'rust-target'),
                    CRYSTAL_CACHE_DIR=str(out / 'crystal-cache'))
    rows = []
    for shape in ('cycle2', 'f2_merge', 'selfrec'):
        app = HERE / 'apps' / shape
        blog = out / ('blog-' + shape)
        shutil.copytree(HERE / 'apps/real-blog', blog)
        shutil.copyfile(app / 'app/controllers/trees_controller.rb', blog / 'app/controllers/trees_controller.rb')
        (blog / 'app/views/trees').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(app / 'app/views/trees/index.html.erb', blog / 'app/views/trees/index.html.erb')
        routes = blog / 'config/routes.rb'
        routes.write_text(routes.read_text().replace('  root "articles#index"',
                                                    '  root "articles#index"\n  get "/tree", to: "trees#index"'))
        reference = subprocess.check_output(['ruby', str(HERE / 'reference.rb'), str(app)], env=clean_env())
        (out / (shape + '.cruby.html')).write_bytes(reference)
        for target in args.targets:
            for enabled in (False, True):
                name = shape + '-' + target + ('-on' if enabled else '-off')
                emitted = out / name
                env = dict(base_env)
                if enabled:
                    env.update(FLAGS)
                    if shape == 'f2_merge':
                        env['RH_SOUND'] = '1'
                result = run([binary, '--target', target, blog if target == 'rust' else app, '-o', emitted],
                             out, env, out / (name + '.emit.log'))
                if result.returncode:
                    raise RuntimeError(name + ': emission failed')
                row = dict(shape=shape, target=target, recursive_emission=enabled, reference_bytes=len(reference))
                if target == 'rust':
                    shutil.copyfile(HERE / 'rust-app.Cargo.lock', emitted / 'Cargo.lock')
                    patched = run(['python3', HERE / 'patch_rust_runtime.py', emitted], out, env,
                                  out / (name + '.runtime-patch.log'))
                    if patched.returncode:
                        raise RuntimeError(name + ': runtime harness patch failed')
                    check = run(['cargo', 'check', '--locked', '--message-format=json'], emitted, env,
                                out / (name + '.check.log'))
                    codes = []
                    for line in check.stdout.splitlines():
                        try:
                            message = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if message.get('reason') == 'compiler-message' and message['message']['level'] == 'error':
                            code = message['message'].get('code')
                            codes.append(code['code'] if code else 'uncoded')
                    row.update(build_ok=check.returncode == 0, errors=len(codes), error_codes=dict(Counter(codes)))
                    if check.returncode == 0:
                        built = run(['cargo', 'build', '--locked'], emitted, env, out / (name + '.build.log'))
                        if built.returncode:
                            raise RuntimeError(name + ': cargo build failed after cargo check')
                        (emitted / 'storage').mkdir(exist_ok=True)
                        with sqlite3.connect(emitted / 'storage/development.sqlite3') as conn:
                            conn.executescript((emitted / 'db/seed.sql').read_text())
                        body = fetch_page([out / 'rust-target/debug/app'], emitted, env, '/tree',
                                          out / (name + '.server.log'))
                        page = rust_template(body)
                else:
                    (emitted / 'lib').mkdir(exist_ok=True)
                    for source, dest in ((args.sqlite3, 'sqlite3'), (args.db, 'db')):
                        shutil.copytree(source, emitted / 'lib' / dest, ignore=shutil.ignore_patterns('.git'))
                    built = run([crystal, 'build', 'src/main.cr', '-o', 'server'], emitted, env,
                                out / (name + '.build.log'))
                    row['build_ok'] = built.returncode == 0
                    if built.returncode == 0:
                        (emitted / 'storage').mkdir(exist_ok=True)
                        page = fetch_page([emitted / 'server'], emitted, env, '/', out / (name + '.server.log'))
                if row['build_ok']:
                    (out / (name + '.page.html')).write_bytes(page)
                    row['page_equals_cruby'] = page == reference
                    row['page_sha256'] = hashlib.sha256(page).hexdigest()
                else:
                    row['page_equals_cruby'] = None
                rows.append(row)
                print(json.dumps(row), flush=True)
    report = dict(condition='emit-rec-phase-c-v1', ruby=ruby,
                  binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), rows=rows)
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    for row in rows:
        if row['recursive_emission'] and (not row['build_ok'] or not row['page_equals_cruby']):
            raise RuntimeError('the enabled arm failed; inspect results.json and logs')


if __name__ == '__main__':
    main()
