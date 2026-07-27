from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path


def make_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S_%f")


def make_workdir(base: Path, stamp: str | None = None) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    stamp = stamp or make_stamp()
    workdir = base / stamp
    suffix = 0
    while workdir.exists():
        suffix += 1
        workdir = base / f"{stamp}_{suffix}"
    (workdir / "workspace").mkdir(parents=True)
    (workdir / "logs").mkdir(parents=True)
    return workdir


def make_session_uuid() -> str:
    return str(uuid.uuid4())
