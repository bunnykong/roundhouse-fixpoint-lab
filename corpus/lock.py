"""Serialize checks on one host with an advisory POSIX lock."""
from contextlib import contextmanager
import fcntl
from pathlib import Path


@contextmanager
def locked():
    with Path(__file__).with_name("run.lock").open("a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
