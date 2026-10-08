"""RSS supervision and wait4 child usage, with aggregate diagnostics."""
import ctypes
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from common import ROOT, write_json

GIB = 1024 ** 3
SAMPLE_SECONDS = 0.1


def environment(directory, overrides):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("RH_", "ROUNDHOUSE_", "BUNDLE_"))
           and key not in ("RUBYOPT", "RUBYLIB", "GEM_HOME", "GEM_PATH")}
    tmp = directory / "tmp"
    tmp.mkdir()
    env.update(TMPDIR=str(tmp), GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
               ROUNDHOUSE_TIMINGS="1", NO_COLOR="1", RUST_BACKTRACE="0",
               LC_ALL="C", TZ="UTC", PYTHONDONTWRITEBYTECODE="1")
    env.update(overrides)
    return env


def rss_reader():
    if sys.platform != "darwin":
        def read(pid):
            try:
                fields = Path("/proc/%s/statm" % pid).read_text().split()
                return int(fields[1]) * os.sysconf("SC_PAGE_SIZE")
            except FileNotFoundError:
                return None
        return read
    lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64,
                                ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int

    def read(pid):
        buf = (ctypes.c_uint64 * 16)()
        got = lib.proc_pidinfo(pid, 4, 0, ctypes.byref(buf), ctypes.sizeof(buf))
        if got == 96:
            return int(buf[1])
        if ctypes.get_errno() == 3:  # ESRCH: it exited between poll and sample
            return None
        raise OSError("sampler_error")
    return read


def kill_checker(process, pid):
    try:
        # child_exec puts only the checker (and its children) in this group.
        os.killpg(pid if pid is not None else process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_check(directory, binary, app, limit_gib=4.0, seconds=120.0, overrides=None):
    directory, binary, app = Path(directory).resolve(), Path(binary).resolve(), Path(app).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    read_rss = rss_reader()
    pidfile = directory / "pid"
    command = [sys.executable, str(ROOT / "child_exec.py"), str(pidfile), str(binary),
               "check", "--continue", "."]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    beginning = time.monotonic()
    peak = 0
    pid = None
    reason = None
    samples = 0
    signal_seconds = None
    print(json.dumps({"event": "check_start", "app": app.name, "limit_gib": limit_gib,
                      "deadline_seconds": seconds}), flush=True)
    with (directory / "stdout.txt").open("wb") as stdout, \
         (directory / "stderr.txt").open("wb") as stderr, \
         (directory / "rss.csv").open("w", buffering=1) as csv:
        csv.write("wall_seconds,rss_bytes\n")
        process = subprocess.Popen(command, cwd=app, env=environment(directory, overrides or {}),
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        last_status = 0
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - beginning
                if pid is None and pidfile.exists():
                    try:
                        pid = int(pidfile.read_text())
                    except ValueError:
                        pass
                if pid is not None:
                    try:
                        rss = read_rss(pid)
                    except OSError:
                        reason = "sampler_error"
                        rss = None
                    if rss is not None:
                        peak = max(peak, rss)
                        csv.write("%0.4f,%s\n" % (elapsed, rss))
                        samples += 1
                        if rss >= limit_gib * GIB:
                            reason = "rss_limit"
                if elapsed >= seconds and reason is None:
                    reason = "wall_limit"
                if reason is not None:
                    signal_seconds = time.monotonic() - beginning
                    kill_checker(process, pid)
                    break
                if elapsed - last_status >= 30:
                    print(json.dumps({"event": "check_progress", "app": app.name,
                                      "wall_seconds": round(elapsed, 2),
                                      "peak_gib": round(peak / GIB, 3)}), flush=True)
                    last_status = elapsed
                time.sleep(SAMPLE_SECONDS if pid is not None else 0.01)
            wrapper_exit_code = process.wait(timeout=30)
        except KeyboardInterrupt:
            reason = "interrupted"
            signal_seconds = time.monotonic() - beginning
            kill_checker(process, pid)
            wrapper_exit_code = process.wait(timeout=30)
        finally:
            if process.poll() is None:
                kill_checker(process, pid)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    elapsed = time.monotonic() - beginning
    wait4_file = directory / "wait4.json"
    wait4 = json.loads(wait4_file.read_text()) if wait4_file.exists() else {}
    exit_code = wait4.get("exit_code", wrapper_exit_code)
    metrics_file = directory / "diagnostics.json"
    metrics = json.loads(metrics_file.read_text()) if metrics_file.exists() else {}
    has_summary = metrics.get("summary_counts") is not None
    if reason is not None:
        outcome = "killed"
    elif exit_code < 0:
        outcome, reason = "killed", "signal_%s" % -exit_code
    elif exit_code in (0, 1) and has_summary:
        outcome = "completed"
    else:
        outcome, reason = "failed", "missing_summary" if exit_code in (0, 1) else "checker_exit"
    result = {
        "started_at_utc": started, "command": [binary.name, "check", "--continue", "."],
        "limit_gib": limit_gib, "deadline_seconds": seconds,
        "sample_interval_seconds": SAMPLE_SECONDS,
        "peak_rss_bytes": max(peak, wait4.get("peak_rss_bytes", 0)),
        "sampled_peak_rss_bytes": peak, "wait4_peak_rss_bytes": wait4.get("peak_rss_bytes"),
        "wall_seconds": wait4.get("wall_seconds", elapsed), "watchdog_wall_seconds": elapsed,
        "user_seconds": wait4.get("user_seconds"), "system_seconds": wait4.get("system_seconds"),
        "exit_code": exit_code, "wrapper_exit_code": wrapper_exit_code,
        "outcome": outcome, "reason": reason,
        "watchdog_signal_seconds": signal_seconds, "samples": samples, **metrics}
    result["peak_gib"] = result["peak_rss_bytes"] / GIB
    write_json(directory / "result.json", result)
    return result
