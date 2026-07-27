"""Lightweight container configuration for wrapping claude invocations.

Describes how to run a command inside an Apptainer container.
Used by sessions to wrap ``claude`` calls in ``apptainer exec``.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path


def find_apptainer_bin() -> str:
    """Locate the apptainer binary.

    Checks (in order):
    1. ``APPTAINER_DIR`` environment variable
    2. ``apptainer`` on PATH
    """
    import os
    apptainer_dir = os.environ.get("APPTAINER_DIR", "")
    if apptainer_dir:
        candidate = Path(apptainer_dir.rstrip("/")) / "apptainer"
        if not candidate.exists():
            # APPTAINER_DIR might point to bin/ or to the parent.
            candidate = Path(apptainer_dir.rstrip("/"))
            if candidate.name == "apptainer" and candidate.exists():
                return str(candidate)
            candidate = Path(apptainer_dir.rstrip("/")) / "apptainer"
        if candidate.exists():
            return str(candidate)

    found = shutil.which("apptainer")
    if found:
        return found
    return "apptainer"


def find_claude_container_path() -> str:
    """Find the container-side path to the claude binary.

    Resolves the host claude binary's real path to determine the
    version, then returns the container-side path assuming the host
    install is bind-mounted at ``/opt/claude``.
    """
    host_bin = shutil.which("claude")
    if host_bin:
        real = Path(host_bin).resolve()
        # e.g., ~/.local/share/claude/versions/2.1.87
        return f"/opt/claude/versions/{real.name}"
    return "claude"


def find_claude_host_install() -> Path | None:
    """Find the host Claude install directory (containing versions/)."""
    host_bin = shutil.which("claude")
    if not host_bin:
        return None
    real = Path(host_bin).resolve()
    candidate = real.parent.parent  # versions/<ver> -> versions -> install_dir
    if (candidate / "versions").is_dir():
        return candidate
    return None


@dataclass
class ContainerConfig:
    """Configuration for running commands inside an Apptainer container.

    Usage::

        config = ContainerConfig(image=Path("image.sif"))
        config.add_bind("run/output", "/output")
        config.add_bind("run/claude_config", "/claude_config")

        wrapped = config.wrap_command(["claude", "-p", "hello"])
        # → ["apptainer", "exec", "--fakeroot", ..., "image.sif", "claude", "-p", "hello"]
    """

    image: Path
    apptainer_bin: str = ""
    overlay: Path | None = None
    fakeroot: bool = True
    cleanenv: bool = True
    writable_tmpfs: bool = False
    no_mount: list[str] = field(default_factory=lambda: ["home", "cwd"])
    binds: list[tuple[str, str, str]] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    workdir: str = ""

    def __post_init__(self):
        if not self.apptainer_bin:
            self.apptainer_bin = find_apptainer_bin()

    def add_bind(self, host: str | Path, container: str, mode: str = "rw") -> "ContainerConfig":
        """Add a bind mount."""
        self.binds.append((str(host), container, mode))
        return self

    def host_to_container(self, host_path: str | Path) -> str:
        """Map a host path to its container-side equivalent.

        Uses the bind mounts to find the mapping.  Returns the host
        path unchanged if no bind covers it.
        """
        host_str = str(Path(host_path).resolve())
        for host, container, _mode in self.binds:
            host_resolved = str(Path(host).resolve())
            if host_str.startswith(host_resolved):
                suffix = host_str[len(host_resolved):]
                return container + suffix
        return host_str

    def wrap_command(self, cmd: list[str]) -> list[str]:
        """Wrap a command in ``apptainer exec``."""
        args = [self.apptainer_bin, "exec"]

        if self.fakeroot:
            args.append("--fakeroot")
        if self.cleanenv:
            args.append("--cleanenv")
        if self.no_mount:
            args.extend(["--no-mount", ",".join(self.no_mount)])
        if self.writable_tmpfs:
            args.append("--writable-tmpfs")
        if self.overlay:
            args.extend(["--overlay", str(self.overlay)])

        for key, value in self.env.items():
            args.extend(["--env", f"{key}={value}"])

        for host, container, mode in self.binds:
            mount = f"{host}:{container}"
            if mode == "ro":
                mount += ":ro"
            args.extend(["-B", mount])

        if self.workdir:
            args.extend(["--pwd", self.workdir])

        args.append(str(self.image))
        args.extend(cmd)
        return args


def make_base_container(
    image: Path,
    claude_config_dir: Path,
    src_dir: Path,
    docs_dir: Path | None = None,
    claude_code_dir: Path | None = None,
) -> ContainerConfig:
    """Create a base container config with standard bind mounts.

    Returns a config with:
    - Credentials at ``/claude_config``
    - Source code at ``/src``
    - Claude binary at ``/opt/claude``
    - Standard environment variables
    """
    claude_install = find_claude_host_install()

    config = ContainerConfig(
        image=image,
        writable_tmpfs=True,
        env={
            "CLAUDE_CONFIG_DIR": "/claude_config",
            "TERM": "xterm-256color",
            "LANG": "en_US.UTF-8",
            "NPM_CONFIG_CACHE": "/tmp/.npm",
            "PATH": "/opt/claude/versions:/root/.local/bin:/usr/local/bin:/usr/bin:/bin",
        },
    )

    config.add_bind(claude_config_dir, "/claude_config")
    config.add_bind(src_dir, "/src", "ro")

    if claude_code_dir:
        config.add_bind(claude_code_dir, "/src/claude_code", "ro")

    if docs_dir:
        config.add_bind(docs_dir, "/madgraph_docs", "ro")

    if claude_install:
        config.add_bind(claude_install, "/opt/claude", "ro")

    return config


def make_question_container(
    base: ContainerConfig,
    overlay: Path,
    workdir_host: Path,
    workdir_container: str = "/output",
    extra_binds: list[tuple[str, str, str]] | None = None,
) -> ContainerConfig:
    """Create a container config for a question phase.

    Copies the base config and adds:
    - The question's overlay (rw)
    - The question's workdir bind
    - Removes writable_tmpfs (overlay provides writable layer)
    """
    import copy
    config = copy.deepcopy(base)
    config.overlay = overlay
    config.writable_tmpfs = False
    config.workdir = workdir_container
    config.add_bind(workdir_host, workdir_container)

    if extra_binds:
        for bind in extra_binds:
            config.binds.append(bind)

    return config
