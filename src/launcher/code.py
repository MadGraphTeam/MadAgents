from __future__ import annotations

import atexit
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import apptainer, claude_binary, images, scheduler
from .errors import LaunchError, die
from .lock import madrun_lock
from .paths import REPO_ROOT, ensure_file, resolve_path
from .settings import (
    assert_no_api_keys,
    load_config_env,
    scrub_api_keys,
)
from .workdir import make_session_uuid, make_stamp, make_workdir


# Mountpoints that must exist inside the overlay for the binds below to attach.
_OVERLAY_DIRS_BASE: tuple[str, ...] = (
    "/workspace", "/output", "/madgraph_docs", "/opt/claude", "/opt/.config/.claude",
)


def _overlay_dirs() -> list[str]:
    dirs = [*_OVERLAY_DIRS_BASE]
    # The instance's .claude mounts at /output/.claude and the session runs with
    # CWD /output, so the project root is /output and the agent system's
    # `memory: project` agents (which target /output/.claude/agent-memory) load
    # warm. That nested mountpoint lives in the host /output bind (created by the
    # setup harness), not the overlay — so nothing extra is prepped for it here.
    if (REPO_ROOT / "internals").is_dir():
        dirs.append("/internals")
    return dirs


# Stable in-container paths that may surface as a session cwd (lead cwd, or a
# teammate inheriting it through TeamCreate). Pre-trusting them in the lead's
# .claude.json prevents the first-time-trust dialog from blocking startup. The
# container is the security boundary (overlay + cleanenv + IS_SANDBOX=1), so
# trust on these mount roots is infrastructure, not a security boundary.
# Note: trust is exact-match; subdirs (e.g. /workspace/q3) do not inherit.
_TRUSTED_CONTAINER_PATHS: tuple[str, ...] = (
    "/output",
    "/workspace",
    "/tmp",
    "/madgraph_docs",
)

WORKFLOW = "madagents"

# Defaults for a bare run. Run instances override RUN_DIR / APPTAINER_OVERLAY /
# MADRUN_INSTANCE per-instance (see src/launcher/setup.py) so several can run
# concurrently — each holds a distinct lock, overlay and instance prefix.
_DEFAULT_RUN_DIR = "run_dir"
_DEFAULT_OVERLAY = "image/mad_overlay.img"


def _instance_prefix() -> str:
    # When ``MADRUN_INSTANCE`` is set (a setup-harness run dir), qualify the
    # prefix by the instance. ``release_overlay`` /
    # ``cleanup_orphan_instance_state`` match running instances **by prefix,
    # not by overlay**, so a shared ``madagents-cc-madagents`` prefix would
    # make starting one instance stop a concurrently-running sibling. A
    # per-instance prefix scopes release/cleanup to this instance's own prior
    # runs; ``cleanup_madrun.sh``'s broader ``madagents-`` match still covers
    # all of them.
    instance = os.environ.get("MADRUN_INSTANCE")
    if instance:
        return f"madagents-cc-inst-{_sanitize_instance(instance)}"
    return f"madagents-cc-{WORKFLOW}"


def _sanitize_instance(name: str) -> str:
    """Reduce an instance name to apptainer-instance-safe chars."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", name) or "inst"


def _resume_or_continue_flag(argv: list[str]) -> bool:
    return any(a in ("--resume", "--continue") for a in argv)


def _seed_trusted_projects(claude_config_dir: Path) -> None:
    """Mark the well-known in-container bind-mount paths as trusted in
    ``<claude_config_dir>/.claude.json``.

    Idempotent: existing project entries are preserved (only the
    ``hasTrustDialogAccepted`` flag is added if missing). Other top-level keys
    are left untouched. If the file is missing or unreadable, write a fresh
    minimal JSON containing just the trust map — Claude Code will fill in the
    rest on first run.
    """
    config_path = claude_config_dir / ".claude.json"
    try:
        data = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    projects = data.get("projects")
    if not isinstance(projects, dict):
        projects = {}
        data["projects"] = projects
    changed = False
    for path in _TRUSTED_CONTAINER_PATHS:
        entry = projects.get(path)
        if not isinstance(entry, dict):
            entry = {}
            projects[path] = entry
            changed = True
        if not entry.get("hasTrustDialogAccepted"):
            entry["hasTrustDialogAccepted"] = True
            changed = True
    if changed:
        config_path.write_text(json.dumps(data, indent=2) + "\n")


def _claude_code_env_passthrough() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k.startswith("CLAUDE_CODE_")}


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    load_config_env()
    scrub_api_keys()

    # The agent system is a directory holding config.yaml + .claude/. Normal
    # path: a run instance built by ``madrun.sh`` sets MADRUN_SYSTEM_DIR in its
    # generated run.sh. A bare run without the harness falls back to the shipped
    # ``madagents/`` (which starts cold — the harness is what seeds a memory
    # pack; see memory/README.md).
    from .presets_loader import load_preset

    system_dir = resolve_path(
        os.environ.get("MADRUN_SYSTEM_DIR") or os.environ.get("MADRUN_PRESET_DIR")
    ) or (REPO_ROOT / "madagents")
    try:
        preset = load_preset(system_dir)
    except (ValueError, FileNotFoundError) as e:
        die(
            f"failed to load the agent system at {system_dir}: {e}",
            hint="Build a run instance with ./madrun.sh and launch it "
                 "with its own ./run.sh.",
        )
    print(f"madrun: agent system {system_dir} (.claude: {preset.claude_dir})", flush=True)
    print("madrun: starting...", flush=True)

    instance_prefix = _instance_prefix()

    output_dir = resolve_path(os.environ.get("OUTPUT_DIR") or "output") or REPO_ROOT / "output"
    run_dir = (
        resolve_path(os.environ.get("RUN_DIR") or _DEFAULT_RUN_DIR)
        or REPO_ROOT / _DEFAULT_RUN_DIR
    )
    # CLAUDE_CONFIG_DIR precedence: caller shell env, else config.env
    # (load_config_env populates it via setdefault). If neither sets it,
    # claude_config_dir stays None — the launcher then binds no host config
    # dir and sets no CLAUDE_CONFIG_DIR in the container, so the in-container
    # claude falls back to its own default.
    claude_config_dir = resolve_path(os.environ.get("CLAUDE_CONFIG_DIR"))

    # Each image type is built into its own folder (image/<type>/madagents.sif),
    # so with no APPTAINER_IMAGE the launcher picks whichever is built rather
    # than a single fixed filename. See src/launcher/images.py.
    image = images.resolve_image(os.environ.get("APPTAINER_IMAGE"))
    overlay = (
        resolve_path(os.environ.get("APPTAINER_OVERLAY") or _DEFAULT_OVERLAY)
        or REPO_ROOT / _DEFAULT_OVERLAY
    )
    # These all raise LaunchError, whose whole point is a message + an actionable
    # hint ("run image/create_image.sh first"). Catch it here so a missing image
    # or overlay prints that hint rather than a Python traceback.
    try:
        apptainer_bin = apptainer.locate()
        ensure_file(image, "Container image", "Run image/create_image.sh first.")
        # The overlay's upper dir must be **user-owned**: the container starts
        # WITHOUT --fakeroot (see the start_instance call), so it runs as the
        # invoking uid and an overlay made by `apptainer overlay create
        # --fakeroot` (upper dir owned by uid 65534) would fail "upper dir is
        # not writable". image/create_overlay.sh and the setup harness both
        # produce user-owned ones.
        ensure_file(
            overlay, "Overlay image",
            "Each run instance owns a fresh sparse overlay; re-run ./madrun.sh, "
            "or create one: apptainer overlay create --sparse --size 10240 <path>.",
        )
    except LaunchError as e:
        die(e.message, e.hint)

    print(f"madrun: image {image}", flush=True)

    run_dir.mkdir(parents=True, exist_ok=True)
    with madrun_lock(run_dir / ".madrun.lock"):
        workdirs_base = run_dir / "workdirs"
        stamp = make_stamp()
        workdir = make_workdir(workdirs_base, stamp=stamp)
        session_uuid = make_session_uuid()
        (workdir / "logs" / "session_uuid").write_text(session_uuid)

        session_id_args: list[str] = (
            [] if _resume_or_continue_flag(argv) else ["--session-id", session_uuid]
        )

        if claude_config_dir is not None:
            claude_config_dir.mkdir(parents=True, exist_ok=True)
            _seed_trusted_projects(claude_config_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Cosmetic cleanup: legacy /output/.mcp.json from pre-refactor launches.
        stale_mcp = output_dir / ".mcp.json"
        if stale_mcp.exists():
            stale_mcp.unlink()

        host_claude = claude_binary.detect_host_claude()

        instance_name: str | None = None
        cleaned = [False]

        def _do_cleanup() -> None:
            if cleaned[0]:
                return
            cleaned[0] = True
            if instance_name is not None:
                try:
                    apptainer.stop_instance(apptainer_bin, instance_name, force=True)
                    # Backstop: if -F was swallowed (e.g. by a fakeroot wrapper),
                    # SIGKILL the daemon PID recorded in the state file and remove
                    # the orphan state dir so the next run can reuse the name.
                    apptainer.force_kill_instance_state(instance_name)
                    apptainer.remove_workspace_dir(
                        apptainer_bin, image, overlay, fakeroot=False,
                    )
                except Exception as exc:
                    print(f"WARN: instance cleanup raised {exc!r}", file=sys.stderr)

        atexit.register(_do_cleanup)

        # SLURM passthrough — bind the host's scheduler config + munge socket so
        # the image's sbatch/squeue talk to the host's controller. Nothing more:
        # job storage and what a compute node can see of the container's software
        # are site-specific, and the launcher does not guess at them. Set
        # BIND_SLURM=0 to skip, =1 to require. See launcher/scheduler.py.
        sched_binds, sched_envs, sched_detected = scheduler.host_passthrough()
        if sched_detected:
            print(
                "madrun: SLURM detected — /etc/slurm and the munge socket are "
                "bound, so sbatch/squeue in the container submit to this host's "
                "controller.",
                flush=True,
            )

        # Without the harness (a bare ``python3 -m launcher code``)
        # preset.claude_dir IS madagents/.claude, so the session writes its
        # memory straight into git-tracked state.
        if Path(preset.preset_dir).resolve() == (REPO_ROOT / "madagents").resolve():
            print(
                "madrun: NOTE — running the tracked madagents/ directly, so the "
                "session's memory writes land in the shipped tree. Build a run "
                "instance with ./madrun.sh instead.",
                flush=True,
            )

        try:
            apptainer.release_overlay(
                overlay, apptainer_bin, instance_prefixes=(instance_prefix,),
            )
            # Drop orphan instance state dirs left by SIGKILL'd runs so the new
            # instance can reuse the canonical name instead of being bumped to
            # ``<prefix>-1``/``-2`` (which would dodge the stop trap on exit).
            apptainer.cleanup_orphan_instance_state(instance_prefix)
            # No --fakeroot in code mode: the host-bind-mounted claude binary
            # (Bun) deadlocks under apptainer's LD_PRELOAD/libfakeroot path,
            # and the no-fakeroot overlay (see image/create_image.sh) is
            # user-owned so /opt, /workspace, etc. are writable without it.
            apptainer.remove_workspace_symlink(
                apptainer_bin, image, overlay, fakeroot=False,
            )
            apptainer.prep_overlay_dirs(
                apptainer_bin, image, overlay, _overlay_dirs(), fakeroot=False,
            )

            instance_name = f"{instance_prefix}-{stamp}"
            apptainer_log = workdir / "logs" / "apptainer.log"

            # The instance's .claude mounts at /output/.claude (appended AFTER
            # the /output bind, so the parent mount is in place) and the session
            # runs with CWD /output (--pwd), making the project root /output.
            # The agent system's `memory: project` agents hardcode
            # /output/.claude/agent-memory/<name>/MEMORY.md, and CC's project-root
            # memory resolver (the setup harness git-inits /output) reads from
            # there — so a seeded memory pack loads warm and round-trips back to
            # the instance's own .claude.
            binds: list[tuple[str, str, str | None]] = [
                (str(workdir / "workspace"), "/workspace", None),
            ]
            # Host claude config dir → /opt/.config/.claude. Omitted when
            # CLAUDE_CONFIG_DIR is unset — the in-container claude then uses
            # its own default config location.
            if claude_config_dir is not None:
                binds.append((str(claude_config_dir), "/opt/.config/.claude", None))
            binds.append((str(output_dir), "/output", None))
            # The instance's .claude at /output/.claude — appended AFTER /output
            # so the parent bind is in place.
            binds.append((str(preset.claude_dir), "/output/.claude", None))
            if preset.mount_madgraph_docs:
                # Either the system's declared corpus, or one shipped alongside
                # its config.yaml. The canonical madagents system sets
                # mount_madgraph_docs: false and ships neither.
                docs_src = (
                    (REPO_ROOT / preset.madgraph_docs_path)
                    if preset.madgraph_docs_path
                    else preset.preset_dir / "software_instructions" / "madgraph"
                )
                if not docs_src.is_dir():
                    die(
                        f"mount_madgraph_docs is set but no doc corpus at {docs_src}",
                        hint="Point madgraph_docs_path at one, or set "
                             "mount_madgraph_docs: false in config.yaml.",
                    )
                binds.append((str(docs_src), "/madgraph_docs", "ro"))
            # System-declared extra mounts (host already resolved+created by the
            # loader). Empty for the canonical madagents system.
            for eb in preset.extra_binds:
                binds.append((str(eb.host), eb.container, eb.mode))
            if host_claude is not None:
                binds.append((str(host_claude.install_dir), "/opt/claude", "ro"))

            # Site-specific bucket — bound rw at /internals/ in the container.
            # Holds cluster_info.md and any future host-specific facts.
            # Gracefully absent when the host directory does not exist.
            host_internals = REPO_ROOT / "internals"
            if host_internals.is_dir():
                binds.append((str(host_internals), "/internals", None))

            # ``sched_binds`` / ``sched_envs`` were computed before the instance
            # started — reuse them here. The startup log line was emitted at
            # detection time.
            if sched_binds:
                binds.extend(sched_binds)

            instance_envs = {
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
            }
            if claude_config_dir is not None:
                instance_envs["CLAUDE_CONFIG_DIR"] = "/opt/.config/.claude"
            instance_envs.update(sched_envs)

            try:
                # Intentionally no --fakeroot: the LD_PRELOAD/libfakeroot path
                # used in the absence of /etc/subuid entries deadlocks
                # claude 2.1.x at startup. With a no-fakeroot overlay
                # (see image/create_image.sh) the user can still write to
                # /opt, /usr/local, etc. inside the container and have those
                # writes persist in the overlay. The user keeps their host
                # UID inside, which is fine for pip/npm/file installs; the
                # rare ops that strictly require uid 0 (apt) should be done
                # in a separate "apptainer exec --fakeroot --overlay"
                # maintenance shell outside the madrun run path.
                result = apptainer.start_instance(
                    apptainer_bin, instance_name, image,
                    fakeroot=False,
                    cleanenv=True,
                    overlay=overlay,
                    binds=binds,
                    envs=instance_envs,
                    log_path=apptainer_log,
                )
                if result.returncode != 0:
                    die(
                        f"failed to start Apptainer instance '{instance_name}'. See {apptainer_log}"
                    )
                (workdir / "logs" / "instance_name.txt").write_text(f"{instance_name}\n")
                print(f"Apptainer instance: {instance_name}")
            except Exception as e:
                die(f"failed to start Apptainer instance: {e}")

            try:
                if host_claude is not None:
                    claude_container_bin = host_claude.container_bin_path
                else:
                    claude_container_bin = claude_binary.resolve_in_container(
                        apptainer_bin, instance_name,
                    )
                    if not claude_container_bin:
                        print("Claude Code not found on host. Installing inside the container...")
                        claude_container_bin = claude_binary.install_in_container(
                            apptainer_bin, instance_name,
                        )

                exec_envs = {
                    "TERM": os.environ.get("TERM", "xterm-256color"),
                    "LANG": os.environ.get("LANG", "C.UTF-8"),
                }
                if claude_config_dir is not None:
                    exec_envs["CLAUDE_CONFIG_DIR"] = "/opt/.config/.claude"
                exec_envs.update(sched_envs)
                exec_envs.update(_claude_code_env_passthrough())

                claude_argv = [
                    "bash", "-c",
                    'export PATH="/root/.local/bin:${PATH}"; exec "$@"', "_",
                    claude_container_bin,
                ]
                system_prompt_append = preset.resolve_system_prompt(REPO_ROOT)
                if system_prompt_append:
                    claude_argv += ["--append-system-prompt", system_prompt_append]
                if preset.disallowed_tools:
                    claude_argv += ["--disallowed-tools", *preset.disallowed_tools]
                if preset.max_turns is not None:
                    # No interactive equivalent — --max-turns is a print-mode
                    # (-p) flag. Say so rather than dropping the key silently.
                    print(
                        "madrun: NOTE — max_turns is set in config.yaml but only "
                        "applies to non-interactive (-p) runs; ignoring it.",
                        flush=True,
                    )
                if preset.model:
                    claude_argv += ["--model", preset.model]
                if preset.reasoning_effort:
                    claude_argv += ["--effort", preset.reasoning_effort]
                claude_argv += [*session_id_args, *argv]

                cmd = [str(apptainer_bin), "exec", "--cleanenv"]
                for k, v in exec_envs.items():
                    cmd += ["--env", f"{k}={v}"]
                # CWD is /output: the project root, where the instance's .claude
                # is mounted and where `memory: project` resolves.
                cmd += ["--pwd", "/output", f"instance://{instance_name}", *claude_argv]

                # Final guard: nothing auth-related may be in the env passed
                # to the claude subprocess. apptainer --cleanenv strips host
                # env, but this catches a programming error (e.g. an exec_envs
                # entry accidentally re-introducing one).
                for k in exec_envs:
                    if k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"):
                        die(f"refusing to exec claude: exec_envs contains {k!r}")
                assert_no_api_keys()

                subprocess.run(cmd)
            except LaunchError as e:
                die(e.message, e.hint)
        finally:
            _do_cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
