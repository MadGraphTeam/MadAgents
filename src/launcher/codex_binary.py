"""Find a Codex CLI to run inside the container — the sibling of claude_binary.

Same shape as the Claude Code case and the same preference order: bind the
host's own install if there is one, otherwise fall back to whatever the
container has, otherwise install it there. Binding the host's install is what
lets a run use the version the user already trusts, and keeps the image from
having to track CLI releases.

The two differ in how the CLI is laid out on disk. Claude Code installs a
``versions/`` directory and is launched by version; the Codex standalone
package is a single self-contained binary under
``$CODEX_HOME/packages/standalone/current/bin/codex``. It is a static-pie ELF,
which is why binding it into the image works at all — it brings its own
dependencies, so the container's glibc is not in play.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import LaunchError

#: Where the bound host install appears inside the container.
CONTAINER_INSTALL_DIR = "/opt/codex"


@dataclass
class HostCodex:
    install_dir: Path        # host dir to bind (holds bin/codex and its resources)
    version: str
    container_bin_path: str  # the executable, as seen inside the container


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def _find_on_host() -> Path | None:
    override = os.environ.get("CODEX_BIN")
    if override:
        p = Path(override)
        if p.is_file() and os.access(p, os.X_OK):
            return p
    which = shutil.which("codex")
    if which:
        return Path(which)
    for candidate in (
        _codex_home() / "packages" / "standalone" / "current" / "bin" / "codex",
        Path.home() / ".local/bin/codex",
        Path("/usr/local/bin/codex"),
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _version(bin_path: Path) -> str:
    try:
        result = subprocess.run(
            [str(bin_path), "--version"], capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return (result.stdout or result.stderr).strip().splitlines()[-1] if result.stdout or result.stderr else "unknown"


def detect_host_codex() -> HostCodex | None:
    """Resolve the host's Codex install, or None to fall back to the container.

    ``codex`` on ``PATH`` is usually a symlink into the standalone package, so
    the *resolved* path is what locates the install root. The package root is
    bound rather than the bare executable: it also carries ``codex-resources/``
    (the sandbox helpers and a bundled zsh), and a binary bound without them
    loses features with no obvious cause.
    """
    bin_path = _find_on_host()
    if bin_path is None:
        return None
    real = bin_path.resolve()
    # .../packages/standalone/current/bin/codex -> bind .../current
    install_dir = real.parent.parent if real.parent.name == "bin" else real.parent
    container_bin = f"{CONTAINER_INSTALL_DIR}/bin/{real.name}"
    if not (install_dir / "bin" / real.name).is_file():
        # A layout we do not recognise (a distro package, a wrapper script).
        # Bind the containing directory and call the file by name.
        install_dir = real.parent
        container_bin = f"{CONTAINER_INSTALL_DIR}/{real.name}"
    return HostCodex(
        install_dir=install_dir,
        version=_version(real),
        container_bin_path=container_bin,
    )


def resolve_in_container(apptainer_bin: Path, instance_name: str) -> str | None:
    result = subprocess.run(
        [str(apptainer_bin), "exec", f"instance://{instance_name}",
         "bash", "-c", "command -v codex 2>/dev/null || true"],
        capture_output=True, text=True,
    )
    path = result.stdout.strip()
    return path or None


def install_in_container(apptainer_bin: Path, instance_name: str) -> str:
    result = subprocess.run(
        [str(apptainer_bin), "exec", "--cleanenv", f"instance://{instance_name}",
         "npm", "install", "-g", "@openai/codex"],
    )
    if result.returncode != 0:
        raise LaunchError(
            "Failed to install Codex inside the container.",
            hint="Install the Codex CLI on the host first, or ensure npm is available "
                 "in the container.",
        )
    path = resolve_in_container(apptainer_bin, instance_name)
    if not path:
        raise LaunchError("Codex binary not found after installation.")
    return path
