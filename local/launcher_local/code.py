"""Start a session against a self-hosted, Anthropic-compatible endpoint.

Mirrors ``launcher.code.main`` for everything about the container — image,
overlay, binds, instance lifecycle, scheduler passthrough — by importing that
machinery rather than copying it. The two differences are both about auth, and
both are deliberate:

1. ``ANTHROPIC_BASE_URL`` / ``ANTHROPIC_AUTH_TOKEN`` are placed on the
   container environment at exec time, from ``local/config.env``.
2. The exec-time assertion that no auth variable is present is therefore not
   run here. Ambient host credentials are still scrubbed — see below.

Ambient scrubbing is *kept*: ``scrub_api_keys()`` runs exactly as it does in
the main launcher, so whatever happens to be exported in your shell still never
reaches the session. Only the two values you declared in ``local/config.env``
are added back, by name, at the last step.
"""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
from pathlib import Path

from launcher import apptainer, claude_binary, images, scheduler
from launcher.code import (
    _claude_code_env_passthrough,
    _instance_prefix,
    _overlay_dirs,
    _resume_or_continue_flag,
    _seed_trusted_projects,
)
from launcher.errors import LaunchError, die
from launcher.lock import madrun_lock
from launcher.paths import REPO_ROOT, ensure_file, resolve_path
from launcher.settings import load_config_env, scrub_api_keys
from launcher.workdir import make_session_uuid, make_stamp, make_workdir

from .config import CONFIG_ENV, endpoint_env, load_local_config, model_args, redacted_summary

_DEFAULT_RUN_DIR = "run_dir"
_DEFAULT_OVERLAY = "image/mad_overlay.img"


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    load_config_env()
    load_local_config()
    # Kept, not skipped: ambient credentials must not reach the session here
    # either. The declared endpoint is re-added by name at exec time.
    scrub_api_keys()

    local_envs = endpoint_env()
    if not local_envs:
        die(
            "no local endpoint configured",
            hint=f"Set LOCAL_MODEL_BASE_URL in {CONFIG_ENV}. "
                 f"Copy {CONFIG_ENV.name}.example to start. To run against "
                 f"Anthropic instead, use ./madrun.sh in the repo root.",
        )
    print(f"madrun-local: endpoint {redacted_summary()}", flush=True)

    from launcher.presets_loader import load_preset

    system_dir = resolve_path(
        os.environ.get("MADRUN_SYSTEM_DIR") or os.environ.get("MADRUN_PRESET_DIR")
    ) or (REPO_ROOT / "madagents")
    try:
        preset = load_preset(system_dir)
    except (ValueError, FileNotFoundError) as e:
        die(
            f"failed to load the agent system at {system_dir}: {e}",
            hint="Build a run instance with local/madrun.sh and launch it "
                 "with its own ./run.sh.",
        )
    print(f"madrun-local: agent system {system_dir} (.claude: {preset.claude_dir})", flush=True)

    instance_prefix = _instance_prefix()
    output_dir = resolve_path(os.environ.get("OUTPUT_DIR") or "output") or REPO_ROOT / "output"
    run_dir = (
        resolve_path(os.environ.get("RUN_DIR") or _DEFAULT_RUN_DIR)
        or REPO_ROOT / _DEFAULT_RUN_DIR
    )
    claude_config_dir = resolve_path(os.environ.get("CLAUDE_CONFIG_DIR"))
    # Same resolution as the root launcher: each image type is built into its
    # own folder, so with no APPTAINER_IMAGE we run whichever is built.
    image = images.resolve_image(os.environ.get("APPTAINER_IMAGE"))
    overlay = (
        resolve_path(os.environ.get("APPTAINER_OVERLAY") or _DEFAULT_OVERLAY)
        or REPO_ROOT / _DEFAULT_OVERLAY
    )
    try:
        apptainer_bin = apptainer.locate()
        ensure_file(image, "Container image", "Run image/create_image.sh first.")
        ensure_file(
            overlay, "Overlay image",
            "Each run instance owns a fresh sparse overlay; re-run local/madrun.sh, "
            "or create one: apptainer overlay create --sparse --size 10240 <path>.",
        )
    except LaunchError as e:
        die(e.message, e.hint)

    run_dir.mkdir(parents=True, exist_ok=True)
    with madrun_lock(run_dir / ".madrun.lock"):
        workdir = make_workdir(run_dir / "workdirs", stamp=(stamp := make_stamp()))
        session_uuid = make_session_uuid()
        (workdir / "logs" / "session_uuid").write_text(session_uuid)
        session_id_args: list[str] = (
            [] if _resume_or_continue_flag(argv) else ["--session-id", session_uuid]
        )

        if claude_config_dir is not None:
            claude_config_dir.mkdir(parents=True, exist_ok=True)
            _seed_trusted_projects(claude_config_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

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
                    apptainer.force_kill_instance_state(instance_name)
                    apptainer.remove_workspace_dir(
                        apptainer_bin, image, overlay, fakeroot=False,
                    )
                except Exception as exc:
                    print(f"WARN: instance cleanup raised {exc!r}", file=sys.stderr)

        atexit.register(_do_cleanup)

        sched_binds, sched_envs, sched_detected = scheduler.host_passthrough()
        if sched_detected:
            print(
                "madrun-local: SLURM detected — /etc/slurm and the munge socket "
                "are bound.",
                flush=True,
            )

        if Path(preset.preset_dir).resolve() == (REPO_ROOT / "madagents").resolve():
            print(
                "madrun-local: NOTE — running the tracked madagents/ directly, so "
                "the session's memory writes land in the shipped tree. Build a run "
                "instance with local/madrun.sh instead.",
                flush=True,
            )

        try:
            apptainer.release_overlay(
                overlay, apptainer_bin, instance_prefixes=(instance_prefix,),
            )
            apptainer.cleanup_orphan_instance_state(instance_prefix)
            apptainer.remove_workspace_symlink(
                apptainer_bin, image, overlay, fakeroot=False,
            )
            apptainer.prep_overlay_dirs(
                apptainer_bin, image, overlay, _overlay_dirs(), fakeroot=False,
            )

            instance_name = f"{instance_prefix}-{stamp}"
            apptainer_log = workdir / "logs" / "apptainer.log"

            binds: list[tuple[str, str, str | None]] = [
                (str(workdir / "workspace"), "/workspace", None),
            ]
            if claude_config_dir is not None:
                binds.append((str(claude_config_dir), "/opt/.config/.claude", None))
            binds.append((str(output_dir), "/output", None))
            binds.append((str(preset.claude_dir), "/output/.claude", None))
            if preset.mount_madgraph_docs:
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
            for eb in preset.extra_binds:
                binds.append((str(eb.host), eb.container, eb.mode))
            if host_claude is not None:
                binds.append((str(host_claude.install_dir), "/opt/claude", "ro"))
            host_internals = REPO_ROOT / "internals"
            if host_internals.is_dir():
                binds.append((str(host_internals), "/internals", None))
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
                        f"failed to start Apptainer instance '{instance_name}'. "
                        f"See {apptainer_log}"
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
                # The whole point of this launcher. Added last so nothing above
                # can shadow it, and never sourced from the ambient environment
                # — only from local/config.env.
                exec_envs.update(local_envs)

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
                # config.yaml's model/effort are for the hosted path; the local
                # endpoint's model name comes from local/config.env. The user's
                # own argv is appended last, so an explicit --model still wins.
                claude_argv += model_args()
                claude_argv += [*session_id_args, *argv]

                cmd = [str(apptainer_bin), "exec", "--cleanenv"]
                for k, v in exec_envs.items():
                    cmd += ["--env", f"{k}={v}"]
                cmd += ["--pwd", "/output", f"instance://{instance_name}", *claude_argv]

                subprocess.run(cmd)
            except LaunchError as e:
                die(e.message, e.hint)
        finally:
            _do_cleanup()

    return 0
