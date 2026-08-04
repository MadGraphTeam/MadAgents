"""Find an opencode CLI to run inside the container — the third sibling.

Same shape and same preference order as ``claude_binary`` and
``codex_binary``: bind the host's own install if there is one, otherwise fall
back to whatever the container has, otherwise install it there. **opencode is
never vendored into this repository** — it is a ~171 MB binary that belongs on
the machine, obtained the same way the other two CLIs are.

Two differences from the Codex case are worth knowing:

* **The upstream layout is a bare binary**, not a package directory. The
  official installer hardcodes ``$HOME/.opencode/bin`` and edits shell rc files;
  many people therefore extract the release tarball to a prefix of their own.
  Both are handled — what is bound is the directory holding the executable, and
  ``OPENCODE_DIR`` in ``config.env`` names it the same way ``APPTAINER_DIR``
  names apptainer's.

* **It is dynamically linked** (Codex ships a static-pie), so binding the host
  binary into the image depends on the image's glibc. Its floor is glibc 2.17,
  which every realistic image clears, but that is a fact about the binary and
  not a guarantee: :func:`check_container_compat` probes it rather than assuming.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import LaunchError

#: Where the bound host install appears inside the container.
CONTAINER_INSTALL_DIR = "/opt/opencode"


@dataclass
class HostOpencode:
    install_dir: Path        # host dir to bind (holds the executable)
    version: str
    container_bin_path: str  # the executable, as seen inside the container


def _find_on_host() -> Path | None:
    """Locate the host's opencode, or None to fall back to the container.

    Precedence mirrors ``apptainer.locate``: an explicitly configured location
    wins, and if it is wrong we say so rather than quietly doing something else.

    - ``OPENCODE_BIN`` — the executable itself, for a non-standard filename.
    - ``OPENCODE_DIR`` — the directory holding it, the same shape as
      ``APPTAINER_DIR`` in ``config.env``. This is the one most setups want:
      opencode ships as a single binary that often lives outside ``PATH``.
    - then ``PATH``, then the usual install prefixes.

    Both are **hard** when set: falling back to a container install because a
    configured path was a typo would look like the setting had no effect.
    """
    override = os.environ.get("OPENCODE_BIN", "").strip()
    if override:
        p = Path(override)
        if p.is_file() and os.access(p, os.X_OK):
            return p
        raise LaunchError(
            f"OPENCODE_BIN is set to {override}, which is not an executable file.",
            hint="Point it at the opencode binary, set OPENCODE_DIR to the directory "
                 "holding it, or unset both to use PATH.",
        )
    opencode_dir = os.environ.get("OPENCODE_DIR", "").strip()
    if opencode_dir:
        candidate = Path(opencode_dir).expanduser() / "opencode"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise LaunchError(
            f"opencode not found at {candidate}.",
            hint="Set OPENCODE_DIR in config.env to the directory containing the "
                 "`opencode` binary, or add opencode to PATH.",
        )
    which = shutil.which("opencode")
    if which:
        return Path(which)
    for candidate in (
        Path.home() / ".opencode" / "bin" / "opencode",
        Path.home() / ".local" / "bin" / "opencode",
        Path("/usr/local/bin/opencode"),
        Path("/opt/opencode/bin/opencode"),
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
    out = (result.stdout or result.stderr).strip()
    return out.splitlines()[-1] if out else "unknown"


def detect_host_opencode() -> HostOpencode | None:
    """Resolve the host's opencode install, or None to fall back to the container.

    ``opencode`` on ``PATH`` is often a symlink into an install prefix, so the
    *resolved* path is what locates the directory to bind.
    """
    bin_path = _find_on_host()
    if bin_path is None:
        return None
    real = bin_path.resolve()
    install_dir = real.parent
    return HostOpencode(
        install_dir=install_dir,
        version=_version(real),
        container_bin_path=f"{CONTAINER_INSTALL_DIR}/{real.name}",
    )


def check_container_compat(
    apptainer_bin: Path, instance_name: str, container_bin: str,
) -> str | None:
    """Return a human-readable reason the bound binary cannot run, or None.

    Worth the extra exec: a glibc mismatch surfaces as a loader error at the
    moment the session starts, which reads like the launcher is broken rather
    than like the host binary is too new for the image.
    """
    result = subprocess.run(
        [str(apptainer_bin), "exec", f"instance://{instance_name}",
         container_bin, "--version"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return None
    err = (result.stderr or result.stdout).strip().splitlines()
    return err[-1] if err else f"exit status {result.returncode}"


def resolve_in_container(apptainer_bin: Path, instance_name: str) -> str | None:
    result = subprocess.run(
        [str(apptainer_bin), "exec", f"instance://{instance_name}",
         "bash", "-c", "command -v opencode 2>/dev/null || true"],
        capture_output=True, text=True,
    )
    path = result.stdout.strip()
    return path or None


def install_in_container(apptainer_bin: Path, instance_name: str) -> str:
    """Install opencode inside the container, the way the other two do."""
    result = subprocess.run(
        [str(apptainer_bin), "exec", "--cleanenv", f"instance://{instance_name}",
         "npm", "install", "-g", "opencode-ai"],
    )
    if result.returncode != 0:
        raise LaunchError(
            "Failed to install opencode inside the container.",
            hint="Install the opencode CLI on the host first (a single binary from "
                 "the upstream release; point OPENCODE_BIN at it if it is not on "
                 "PATH), or ensure npm is available in the container.",
        )
    path = resolve_in_container(apptainer_bin, instance_name)
    if not path:
        raise LaunchError("opencode binary not found after installation.")
    return path
