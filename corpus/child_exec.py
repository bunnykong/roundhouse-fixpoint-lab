#!/usr/bin/env python3
"""Bounded diagnostic reduction with exact wait4 peak usage."""
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
from common import write_json
from metrics import Reducer

MAX_LINE = 2 * 1024 * 1024


def main():
    pidfile = Path(sys.argv[1])
    started = time.monotonic()
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.setpgid(0, 0)
        os.close(read_fd)
        os.dup2(write_fd, 1)
        os.dup2(write_fd, 2)
        os.close(write_fd)
        pidfile.write_text(str(os.getpid()) + "\n")
        try:
            os.execv(sys.argv[2], sys.argv[2:])
        except OSError:
            os._exit(127)
    os.close(write_fd)
    reducer = Reducer()
    # Bound memory even when a checker prints an enormous inferred type on one line.
    pending = b""
    dropping = False
    with os.fdopen(read_fd, "rb", buffering=0) as pipe:
        while True:
            block = pipe.read(65536)
            if not block:
                break
            parts = (pending + block).split(b"\n")
            for part in parts[:-1]:
                if not dropping:
                    if len(part) <= MAX_LINE:
                        reducer.feed(part.decode("utf-8", errors="replace"))
                    else:
                        reducer.truncated_lines += 1
                dropping = False
            pending = parts[-1]
            if dropping:
                pending = b""
            elif len(pending) > MAX_LINE:
                reducer.truncated_lines += 1
                pending = b""
                dropping = True
        if pending and not dropping:
            reducer.feed(pending.decode("utf-8", errors="replace"))
    _, status, usage = os.wait4(pid, 0)
    exit_code = os.waitstatus_to_exitcode(status)
    directory = pidfile.parent
    write_json(directory / "diagnostics.json", reducer.data())
    write_json(directory / "wait4.json", {
        "exit_code": exit_code, "wall_seconds": time.monotonic() - started,
        "peak_rss_bytes": usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024,
        "user_seconds": usage.ru_utime, "system_seconds": usage.ru_stime,
        "rss_units": "bytes"})
    # Retain only a numeric summary for the original watchdog's completion criterion.
    summary = reducer.summary
    if summary is not None:
        print("roundhouse-check: <input> — "
              + "{parse_errors} parse error(s), {errors} error(s), {warnings} warning(s), "
                "{notes} gap-attributed note(s), {survey_gaps} survey gap(s)".format(**summary), flush=True)
    return exit_code if exit_code >= 0 else 128 - exit_code


if __name__ == "__main__":
    sys.exit(main())
