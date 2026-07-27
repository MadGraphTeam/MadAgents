from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Iterable

from .errors import LaunchError
from .paths import resolve_path


def locate(apptainer_dir_env: str | None = None) -> Path:
    if apptainer_dir_env is None:
        apptainer_dir_env = os.environ.get("APPTAINER_DIR", "")
    if apptainer_dir_env:
        apptainer_dir = resolve_path(apptainer_dir_env)
        candidate = (apptainer_dir / "apptainer") if apptainer_dir else None
        if candidate and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise LaunchError(
            f"apptainer not found at {candidate}.",
            hint="Set APPTAINER_DIR in config.env or add apptainer to PATH.",
        )
    which = shutil.which("apptainer")
    if which:
        return Path(which)
    raise LaunchError(
        "apptainer not found.",
        hint="Set APPTAINER_DIR in config.env or add apptainer to PATH.",
    )


def list_instances(apptainer_bin: Path) -> list[str]:
    result = subprocess.run(
        [str(apptainer_bin), "instance", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    names: list[str] = []
    for i, line in enumerate(result.stdout.splitlines()):
        if i == 0:
            continue
        parts = line.split()
        if parts:
            names.append(parts[0])
    return names


def instance_exists(apptainer_bin: Path, name: str) -> bool:
    return name in list_instances(apptainer_bin)


def stop_instance(apptainer_bin: Path, name: str, *, force: bool = False) -> None:
    cmd = [str(apptainer_bin), "instance", "stop"]
    if force:
        cmd.append("-F")
    cmd.append(name)
    subprocess.run(cmd, capture_output=True)


Bind = tuple[str, str, str | None]  # (host, container, options)


def start_instance(
    apptainer_bin: Path,
    name: str,
    image: Path,
    *,
    fakeroot: bool = True,
    cleanenv: bool = False,
    overlay: Path | None = None,
    binds: Iterable[Bind] = (),
    envs: dict[str, str] | None = None,
    env_files: Iterable[str] | None = None,
    log_path: Path | None = None,
    no_mount: Iterable[str] | None = None,
) -> subprocess.CompletedProcess:
    cmd: list[str] = [str(apptainer_bin), "instance", "start"]
    if fakeroot:
        cmd.append("--fakeroot")
    if cleanenv:
        cmd.append("--cleanenv")
    if no_mount:
        cmd += ["--no-mount", ",".join(no_mount)]
    for k, v in (envs or {}).items():
        cmd += ["--env", f"{k}={v}"]
    # --env-file keeps secrets off the argv (only the path shows in ``ps``).
    for env_file in (env_files or ()):
        cmd += ["--env-file", str(env_file)]
    for host, cont, opts in binds:
        spec = f"{host}:{cont}" + (f":{opts}" if opts else "")
        cmd += ["-B", spec]
    if overlay:
        cmd += ["--overlay", str(overlay)]
    cmd += [str(image), name]

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "wb") as f:
            return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    return subprocess.run(cmd, capture_output=True)


def fakeroot_exec(
    apptainer_bin: Path,
    image: Path,
    overlay: Path,
    script: str,
    *,
    timeout: float | None = None,
    check: bool = False,
    fakeroot: bool = True,
    binds: Iterable[tuple[str, str, str | None]] | None = None,
    envs: dict[str, str] | None = None,
    cleanenv: bool = False,
) -> subprocess.CompletedProcess:
    cmd = [str(apptainer_bin), "exec"]
    if fakeroot:
        cmd.append("--fakeroot")
    if cleanenv:
        cmd.append("--cleanenv")
    for host, cont, opts in (binds or ()):
        spec = f"{host}:{cont}" + (f":{opts}" if opts else "")
        cmd += ["-B", spec]
    for k, v in (envs or {}).items():
        cmd += ["--env", f"{k}={v}"]
    cmd += ["--overlay", str(overlay), str(image), "bash", "-c", script]
    return subprocess.run(cmd, capture_output=True, timeout=timeout, check=check)


def release_overlay(
    overlay: Path,  # noqa: ARG001 — kept for call-site stability
    apptainer_bin: Path,
    *,
    instance_prefixes: Iterable[str] = ("madagents-cc",),
) -> bool:
    """Stop any matching apptainer instance that may be holding the overlay.

    We do not use ``fuser`` here: on hosts with stale autofs mounts, ``fuser``
    can sit in uninterruptible D-state and hang the launcher. If something
    *other* than a matching apptainer instance is holding the overlay,
    apptainer's own start will surface that error.

    Uses ``-F`` so ``instance stop`` never blocks waiting for SIGTERM to be
    honored by the daemon (which a fakeroot wrapper can swallow).
    """
    stopped_any = False
    for inst in list_instances(apptainer_bin):
        if any(inst == p or inst.startswith(p) for p in instance_prefixes):
            print(f"Stopping stale apptainer instance: {inst}", flush=True)
            stop_instance(apptainer_bin, inst, force=True)
            stopped_any = True
    if stopped_any:
        time.sleep(1)
    return True


def prep_overlay_dirs(
    apptainer_bin: Path,
    image: Path,
    overlay: Path,
    dirs: Iterable[str],
    *,
    fakeroot: bool = True,
) -> None:
    """Create directories inside the overlay for bind-mount targets."""
    dir_list = " ".join(dirs)
    script = (
        f'for d in {dir_list}; do\n'
        f'  [ -e "$d" ] || [ -L "$d" ] || mkdir -p "$d"\n'
        f'done'
    )
    fakeroot_exec(apptainer_bin, image, overlay, script, fakeroot=fakeroot)


def remove_workspace_symlink(
    apptainer_bin: Path, image: Path, overlay: Path, *, fakeroot: bool = True,
) -> None:
    """Remove stale /workspace symlink (left by v1.1 api mode).

    Claude Code needs /workspace as a real directory for bind mounts.
    """
    fakeroot_exec(
        apptainer_bin, image, overlay,
        'if [ -L /workspace ]; then rm /workspace; fi',
        fakeroot=fakeroot,
    )


def remove_workspace_dir(
    apptainer_bin: Path, image: Path, overlay: Path, *, fakeroot: bool = True,
) -> None:
    """Remove /workspace directory on code-mode exit so api mode can use a symlink."""
    fakeroot_exec(
        apptainer_bin, image, overlay,
        'if [ -d /workspace ] && [ ! -L /workspace ]; then rmdir /workspace 2>/dev/null || true; fi',
        timeout=10,
        fakeroot=fakeroot,
    )


def _instance_state_root() -> Path:
    """Apptainer per-user instance state dir: ~/.apptainer/instances/app/<host>/<user>."""
    base = os.environ.get("APPTAINER_CONFIGDIR") or os.path.join(
        os.path.expanduser("~"), ".apptainer",
    )
    host = subprocess.run(
        ["hostname", "-s"], capture_output=True, text=True,
    ).stdout.strip() or "localhost"
    user = subprocess.run(
        ["id", "-un"], capture_output=True, text=True,
    ).stdout.strip() or os.environ.get("USER", "unknown")
    return Path(base) / "instances" / "app" / host / user


def _state_pid(state_file: Path) -> int | None:
    try:
        import json
        data = json.loads(state_file.read_text())
    except (OSError, ValueError):
        return None
    pid = data.get("ppid") or data.get("pid")
    try:
        pid = int(pid) if pid is not None else None
    except (TypeError, ValueError):
        return None
    return pid


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False
    return True


def cleanup_orphan_instance_state(prefix: str) -> None:
    """Remove orphan apptainer instance state dirs for ``<prefix>*``.

    A previous SIGKILL'd run can leave ``~/.apptainer/instances/.../<name>/<name>.json``
    behind even though the daemon process is gone. The next ``instance start``
    would then pick a non-default suffix (``-1``, ``-2``, ...) to dodge the
    stale entry, and the stop trap would not find it. Deleting those dirs
    when the recorded PID is dead lets the new run reuse the canonical name.
    """
    root = _instance_state_root()
    if not root.is_dir():
        return
    for inst_dir in root.glob(f"{prefix}*"):
        if not inst_dir.is_dir():
            continue
        state_file = inst_dir / f"{inst_dir.name}.json"
        if not state_file.is_file():
            continue
        pid = _state_pid(state_file)
        if pid is None or not _pid_alive(pid):
            shutil.rmtree(inst_dir, ignore_errors=True)


def force_kill_instance_state(name: str) -> None:
    """SIGKILL the daemon recorded in ``<name>/<name>.json`` and remove the dir.

    Used as a backstop when ``instance stop -F`` was ignored (e.g. the signal
    was swallowed by a fakeroot wrapper). Safe to call when the state file is
    already gone — no-op in that case.
    """
    state_file = _instance_state_root() / name / f"{name}.json"
    if not state_file.is_file():
        return
    pid = _state_pid(state_file)
    if pid is not None and _pid_alive(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
    shutil.rmtree(state_file.parent, ignore_errors=True)
