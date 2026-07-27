from __future__ import annotations

from pathlib import Path

from .errors import LaunchError

# .../<repo>/src/launcher/paths.py -> <repo>
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# Where ``python3 -m launcher`` is importable from — the parent every entry point
# (madrun.sh, cleanup_madrun.sh, a generated run.sh) puts on PYTHONPATH.
SRC_ROOT: Path = REPO_ROOT / "src"


def resolve_path(p: str | Path | None, base: Path = REPO_ROOT) -> Path | None:
    if p is None or p == "":
        return None
    p = Path(p)
    return p if p.is_absolute() else base / p


def ensure_file(path: Path, kind: str, hint: str | None = None) -> None:
    if not path.is_file():
        raise LaunchError(f"{kind} not found at {path}.", hint)
