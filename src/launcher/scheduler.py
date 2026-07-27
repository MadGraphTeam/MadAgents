"""Make the host's SLURM reachable from inside the container.

Scope is deliberately narrow: bind the host's SLURM configuration and its munge
auth socket, so the ``sbatch`` / ``squeue`` / ``sacct`` clients baked into the
image talk to the same controller the host does. That is the whole integration.

Nothing here provisions *storage* for jobs, and nothing recreates the
container's software stack on a compute node — a job submitted from inside the
container runs on the bare node, seeing only what the shared filesystem gives
it. Those are site-specific problems with site-specific answers, so they are
left to the user rather than guessed at by the launcher.

Other schedulers (Torque/PBS, LSF, …) are not integrated. Their clients may
still be present in the image; wiring one up is the user's call.

Controlled by ``BIND_SLURM`` (config.env or the caller env):

- unset / ``auto`` — bind when the host looks like a SLURM submit host.
- ``0`` — never bind, even on a SLURM host.
- ``1`` — require it; fail at launch if the host has no SLURM configuration,
  rather than starting a session whose ``sbatch`` silently cannot submit.
"""
from __future__ import annotations

import os
from pathlib import Path

from .errors import LaunchError

SLURM_CONF = Path("/etc/slurm/slurm.conf")
#: Munge's socket directory, wherever this distribution puts it.
MUNGE_DIRS = ("/var/run/munge", "/run/munge")


def _bind_slurm_setting() -> str:
    return (os.environ.get("BIND_SLURM") or "auto").strip().lower()


def host_passthrough() -> tuple[
    list[tuple[str, str, str | None]], dict[str, str], list[str]
]:
    """Probe the host for SLURM and return the integration data.

    Returns a triple ``(binds, env_vars, detected)``:

    - ``binds`` are ``(host_path, container_path, mode)`` tuples; ``mode`` is
      ``"ro"`` or ``None`` (None == rw, apptainer's default).
    - ``env_vars`` are env vars the container should see. Empty today; kept in
      the signature because callers pass it straight through.
    - ``detected`` is a list of human-readable names for logging.

    All three are empty when SLURM is absent or switched off — the same image
    runs unchanged on a workstation.
    """
    binds: list[tuple[str, str, str | None]] = []
    envs: dict[str, str] = {}
    detected: list[str] = []

    setting = _bind_slurm_setting()
    if setting in ("0", "off", "no", "false"):
        return binds, envs, detected

    if not SLURM_CONF.is_file():
        if setting in ("1", "on", "yes", "true"):
            raise LaunchError(
                f"BIND_SLURM is set but this host has no {SLURM_CONF}.",
                hint="Unset BIND_SLURM (or set it to 0) to run without a "
                     "scheduler, or launch from a host that can submit.",
            )
        return binds, envs, detected

    binds.append(("/etc/slurm", "/etc/slurm", "ro"))
    # Without the munge socket the clients are present but cannot authenticate,
    # so every submission fails on credentials rather than on anything the agent
    # could act on.
    for munge_dir in MUNGE_DIRS:
        if Path(munge_dir).is_dir():
            binds.append((munge_dir, munge_dir, None))
            break
    detected.append("SLURM")
    return binds, envs, detected
