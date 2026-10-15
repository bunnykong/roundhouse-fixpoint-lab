#!/usr/bin/env python3
"""Enforce the user's wall budget on this task's isolated app-driver session only."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time
D=Path(__file__).resolve().parent
PID=20201
DEADLINE=datetime.fromisoformat('2026-10-15T18:53:00+00:00')
LOG=D/'results/apps-driver.log'
OUT=D/'results/budget-watch.json'

def owners():
    p=subprocess.run(['lsof','-t','-a','-d','1,2',str(LOG)],capture_output=True,text=True)
    return {int(s) for s in p.stdout.split()}

def save(status, **extra):
    OUT.write_text(json.dumps(dict(status=status,deadline=DEADLINE.isoformat(),owned_pid=PID,
                                  at=datetime.now(timezone.utc).isoformat(),**extra),indent=2)+'\n')

assert PID in owners() and os.getpgid(PID)==PID and os.getsid(PID)==PID
save('watching')
while True:
    try:
        os.kill(PID,0)
    except ProcessLookupError:
        save('driver-finished');break
    if datetime.now(timezone.utc)>=DEADLINE:
        # A reused PID or changed session is never sufficient authority to send a signal.
        if PID not in owners() or os.getpgid(PID)!=PID or os.getsid(PID)!=PID:
            save('ownership-check-failed');break
        os.killpg(PID,signal.SIGTERM)
        save('budget-stop',reason='Leave final two minutes for receipts, report and owned Cargo cleanup.')
        break
    time.sleep(1)
