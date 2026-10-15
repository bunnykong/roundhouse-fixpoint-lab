#!/usr/bin/env python3
"""Resume only our descriptor-identified parent-profile controller before its deadline."""
import datetime
import json
import os
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parent
pid = 97514
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
os.kill(pid, signal.SIGSTOP)
target = datetime.datetime.fromisoformat("2026-10-15T07:14:30+00:00")
while datetime.datetime.now(datetime.timezone.utc) < target:
    time.sleep(min(5, max(.01, (target-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
os.kill(pid, signal.SIGCONT)
(ROOT / "evidence/parent-resumed.json").write_text(json.dumps(dict(pid=pid,
    paused_utc=started, resumed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope="orchestrator only; native pair child was never signalled"), indent=2) + "\n")
