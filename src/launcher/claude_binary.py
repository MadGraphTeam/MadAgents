from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import LaunchError


@dataclass
class HostClaude:
    install_dir: Path
    version: str
    container_bin_path: str


def _find_on_host() -> Path | None:
    override = os.environ.get("CLAUDE_BIN")
    if override:
        p = Path(override)
        if p.is_file() and os.access(p, os.X_OK):
            return p
    which = shutil.which("claude")
    if which:
        return Path(which)
    for candidate in (Path.home() / ".local/bin/claude", Path("/usr/local/bin/claude")):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def detect_host_claude() -> HostClaude | None:
    bin_path = _find_on_host()
    if bin_path is None:
        return None
    real = bin_path.resolve()
    version = real.name
    install_dir = real.parent.parent
    if not (install_dir / "versions").is_dir():
        return None
    return HostClaude(
        install_dir=install_dir,
        version=version,
        container_bin_path=f"/opt/claude/versions/{version}",
    )


def resolve_in_container(apptainer_bin: Path, instance_name: str) -> str | None:
    result = subprocess.run(
        [str(apptainer_bin), "exec", f"instance://{instance_name}",
         "bash", "-c", "command -v claude 2>/dev/null || true"],
        capture_output=True, text=True,
    )
    path = result.stdout.strip()
    return path or None


def install_in_container(apptainer_bin: Path, instance_name: str) -> str:
    result = subprocess.run(
        [str(apptainer_bin), "exec", "--cleanenv", f"instance://{instance_name}",
         "npm", "install", "-g", "@anthropic-ai/claude-code"],
    )
    if result.returncode != 0:
        raise LaunchError(
            "Failed to install Claude Code inside the container.",
            hint="Install Claude Code on the host first, or ensure npm is available in the container.",
        )
    path = resolve_in_container(apptainer_bin, instance_name)
    if not path:
        raise LaunchError("Claude Code binary not found after installation.")
    return path
