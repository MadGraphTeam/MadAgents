from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

from .errors import LaunchError


@contextmanager
def madrun_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            os.close(fd)
            # One run per run dir. A run instance owns its overlay and its
            # memory tree, and two apptainer instances cannot safely write one
            # ext3 overlay — so a second run of the SAME instance is refused
            # here. Different instances have different run dirs, hence
            # different locks, and run concurrently.
            raise LaunchError(
                f"this run instance is already running (lock: {lock_path})",
                hint="Wait for it to exit, or start a separate instance with "
                     "./madrun.sh — different instances run concurrently.",
            ) from e
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(fd)
        except OSError:
            pass
