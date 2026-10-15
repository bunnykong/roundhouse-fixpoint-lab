#!/usr/bin/env python3
"""flock(1) stand-in for macOS: `python3 flock.py [--shared|--exclusive] <lockfile> <command> [args...]`.

--exclusive (or HEAVY_LOCK_MODE=exclusive): takes an exclusive flock(2) on <lockfile>, runs the
command, and exits with its status. Use it for timing measurements, which need the host to themselves.

Shared (the default since 2026-10-11; --shared is accepted): holds a shared flock on <lockfile> plus one of HEAVY_SLOTS (default 6) slot locks,
<lockfile>.slot0, .slot1, …, so up to that many shared commands run together. Use it for builds,
test suites and analysis runs whose results don't depend on timing. Shared and exclusive holders
exclude each other.

An exclusive request first waits politely (HEAVY_EXCLUSIVE_POLITE_SECONDS, default 600) for a natural
gap without blocking shared work; after that it blocks new shared holders through <lockfile>.gate,
so a stream of shared commands can't starve it. Interoperates with any other flock(2)/fcntl.flock holder of
<lockfile>, including older copies of this script, which always lock exclusively.
"""
import fcntl
import os
import random
import subprocess
import sys
import time


def open_lock(path):
    # Sandboxed reviewers may only read outside their directory: flock works on a read-only fd.
    try:
        return open(path, "a")
    except OSError:
        return open(path, "r")


def main(argv):
    shared = os.environ.get("HEAVY_LOCK_MODE", "shared") != "exclusive"
    if argv and argv[0] in ("--shared", "--exclusive"):
        shared, argv = argv[0] == "--shared", argv[1:]
    if len(argv) < 2:
        sys.exit(__doc__)
    lock_path, command = argv[0], argv[1:]
    started = time.monotonic()
    main_lock = open_lock(lock_path)
    gate = open_lock(lock_path + ".gate")
    slot = None
    acquired = False
    if not shared:
        # Polite phase: take the host only in a natural gap, without blocking new shared work, so one
        # timing request doesn't idle the machine while long shared holders drain. After the window,
        # claim priority through the gate so timing work can't starve.
        polite = time.monotonic() + float(os.environ.get("HEAVY_EXCLUSIVE_POLITE_SECONDS", "600"))
        while time.monotonic() < polite:
            try:
                fcntl.flock(main_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except BlockingIOError:
                time.sleep(2 + random.random())
    if not acquired:
        fcntl.flock(gate, fcntl.LOCK_EX)
        try:
            fcntl.flock(main_lock, fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
        finally:
            fcntl.flock(gate, fcntl.LOCK_UN)
    if shared:
        slots = max(1, int(os.environ.get("HEAVY_SLOTS", "6")))
        order = list(range(slots))
        while slot is None:
            random.shuffle(order)
            for index in order:
                candidate = open_lock(f"{lock_path}.slot{index}")
                try:
                    fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    slot = candidate
                    break
                except BlockingIOError:
                    candidate.close()
            if slot is None:
                time.sleep(1 + random.random())
    waited = time.monotonic() - started
    if waited > 1:
        mode = "a shared slot of" if shared else "exclusive"
        print(f"flock.py: waited {waited:.0f}s for {mode} {lock_path}", file=sys.stderr, flush=True)
    try:
        return subprocess.call(command)
    finally:
        if slot is not None:
            fcntl.flock(slot, fcntl.LOCK_UN)
        fcntl.flock(main_lock, fcntl.LOCK_UN)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
