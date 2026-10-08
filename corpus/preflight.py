"""Read-only overlap check. ps first; libproc is conservative if ps is unavailable."""
import ctypes
import errno
import os
from pathlib import Path
import re
import subprocess
import sys

from watchdog import rss_reader

CHECKER = re.compile(r"(?:^|\s)\S*roundhouse[^\s]*\s+check(?:\s|$)")


def running_checks():
    try:
        result = subprocess.run(["ps", "-axo", "rss,command"], capture_output=True,
                                text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        if sys.platform != "darwin":
            raise RuntimeError("process_preflight_unavailable")
        return libproc_checks()
    rss = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit() and CHECKER.search(parts[1]):
            rss.append(int(parts[0]) * 1024)
    return {"method": "ps", "processes": len(rss), "total_gib": sum(rss) / 1024 ** 3}


def libproc_checks():
    # Same OS process inventory, without launching the unavailable ps utility.
    # Treat every Roundhouse executable as busy, including non-check subcommands.
    lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    lib.proc_listpids.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_int]
    lib.proc_listpids.restype = ctypes.c_int
    size = lib.proc_listpids(1, 0, None, 0)
    if size <= 0:
        raise RuntimeError("process_preflight_unavailable")
    pids = (ctypes.c_int * (size // 4 + 1024))()
    got = lib.proc_listpids(1, 0, pids, ctypes.sizeof(pids))
    if got <= 0:
        raise RuntimeError("process_preflight_unavailable")
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int
    read_rss = rss_reader()
    checks = []
    readable = 0
    vanished = 0
    for pid in pids[:got // 4]:
        if pid <= 0:
            continue
        buffer = ctypes.create_string_buffer(4096)
        ctypes.set_errno(0)
        if lib.proc_pidpath(pid, buffer, len(buffer)) <= 0:
            if ctypes.get_errno() in (errno.ENOENT, errno.ESRCH):
                vanished += 1
                continue
            # Incomplete visibility never grants permission to launch a heavy run.
            raise RuntimeError("incomplete_process_preflight")
        readable += 1
        name = Path(os.fsdecode(buffer.value)).name
        if re.fullmatch(r"roundhouse(?:[-_].*)?", name):
            try:
                rss = read_rss(pid)
            except OSError:
                rss = None
            checks.append(rss)
    return {"method": "libproc_conservative", "processes": len(checks),
            "total_gib": sum(rss or 0 for rss in checks) / 1024 ** 3,
            "unknown_rss_processes": sum(rss is None for rss in checks),
            "readable_process_paths": readable, "vanished_processes": vanished}
