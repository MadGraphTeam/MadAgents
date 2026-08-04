from __future__ import annotations

import atexit
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import apptainer, claude_binary, codex_binary, images, scheduler
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
# Both providers' mountpoints are prepared regardless of which one this run
# uses: creating a directory in the overlay is free, and an overlay stays with
# its instance across restarts, so pinning them to the provider would strand an
# instance the first time it was started the other way.
_OVERLAY_DIRS_BASE: tuple[str, ...] = (
    "/workspace", "/output", "/madgraph_docs",
    "/opt/claude", "/opt/.config/.claude",
    "/opt/codex", "/opt/.config/.codex",
    # opencode: the bound host binary, its four XDG roots, and this launch's
    # endpoint config + token file. A bind whose destination does not exist in
    # the container is a FATAL instance-start failure, not a warning — so every
    # path any provider might bind has to be prepared here, whether or not this
    # run uses it.
    "/opt/opencode", "/opt/.config/opencode-home", "/opt/.config/opencode-run",
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


def _with_lead_slate(append_text: str, output_dir: Path) -> str:
    """Concatenate the lead's slate onto its appended instructions."""
    from .codex_memory import LEAD_SLATE_REL, lead_slate_header

    try:
        text = (output_dir / LEAD_SLATE_REL).read_text(encoding="utf-8").strip()
    except OSError:
        return append_text
    if not text:
        return append_text
    block = f"{lead_slate_header()}\n\n{text}"
    return f"{append_text}\n\n{block}" if append_text else block


def _seed_codex_trust(codex_config_dir: Path, paths: tuple[str, ...]) -> None:
    """Mark the in-container bind-mount paths trusted in ``config.toml``.

    The Codex counterpart of ``_seed_trusted_projects``, and **not** cosmetic
    the way that one is. Claude Code's trust dialog blocks startup, which is
    loud; Codex's untrusted state is silent — it simply ignores the project's
    whole ``.codex/`` layer, so the 46 consultants do not exist and nothing
    says so. The run would come up looking like plain Codex.

    Appends only: an existing ``[projects."…"]`` entry is left alone, and any
    other config in the file is untouched. TOML is written by hand rather than
    round-tripped because the stdlib can read it but not write it, and
    reformatting a user's config to add one key would be a poor trade.
    """
    config_path = codex_config_dir / "config.toml"
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    missing = [p for p in paths if f'[projects."{p}"]' not in text]
    if not missing:
        return
    block = "".join(
        f'\n[projects."{p}"]\ntrust_level = "trusted"\n' for p in missing
    )
    header = "" if text else (
        "# Written by madrun: the container's bind-mount roots are trusted so\n"
        "# Codex loads the project's .codex/ layer (the agent roster).\n"
    )
    if text and not text.endswith("\n"):
        text += "\n"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(header + text + block, encoding="utf-8")


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
    trees = ", ".join(str(host) for host, _ in preset.agent_dirs())
    print(f"madrun: agent system {system_dir} [{preset.provider}] ({trees})", flush=True)
    print("madrun: starting...", flush=True)

    instance_prefix = _instance_prefix()

    output_dir = resolve_path(os.environ.get("OUTPUT_DIR") or "output") or REPO_ROOT / "output"
    run_dir = (
        resolve_path(os.environ.get("RUN_DIR") or _DEFAULT_RUN_DIR)
        or REPO_ROOT / _DEFAULT_RUN_DIR
    )
    # The CLI's config directory — where its login lives, and the one thing a
    # run cannot obtain for itself. Precedence: caller shell env, else
    # config.env (load_config_env populates it via setdefault). If neither sets
    # it, this stays None: the launcher then binds no host config dir and sets
    # no variable in the container, so the in-container CLI falls back to its
    # own default (and will ask the user to log in).
    if preset.is_codex:
        cli_config_var, cli_config_container = "CODEX_HOME", "/opt/.config/.codex"
    else:
        cli_config_var, cli_config_container = "CLAUDE_CONFIG_DIR", "/opt/.config/.claude"
    cli_config_dir = resolve_path(os.environ.get(cli_config_var))

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

        if cli_config_dir is not None:
            cli_config_dir.mkdir(parents=True, exist_ok=True)
            if preset.is_codex:
                _seed_codex_trust(cli_config_dir, _TRUSTED_CONTAINER_PATHS)
            else:
                _seed_trusted_projects(cli_config_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Cosmetic cleanup: legacy /output/.mcp.json from pre-refactor launches.
        stale_mcp = output_dir / ".mcp.json"
        if stale_mcp.exists():
            stale_mcp.unlink()

        host_cli = (
            codex_binary.detect_host_codex() if preset.is_codex
            else claude_binary.detect_host_claude()
        )
        cli_install_container = (
            codex_binary.CONTAINER_INSTALL_DIR if preset.is_codex else "/opt/claude"
        )

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

        # Without the harness (a bare ``python3 -m launcher code``) the bound
        # trees ARE the shipped ones, so the session writes its memory straight
        # into git-tracked state. True of both providers — and worse on Codex,
        # where a consultant's slate lives inside the tracked role file itself.
        if Path(preset.preset_dir).resolve() in (
            (REPO_ROOT / "madagents").resolve(), (REPO_ROOT / "madagents_codex").resolve(),
        ):
            print(
                f"madrun: NOTE — running the tracked {preset.preset_dir.name}/ directly, so "
                "the session's memory writes land in the shipped tree. Build a run "
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
            # Host CLI config dir. Omitted when the variable is unset — the
            # in-container CLI then uses its own default config location.
            if cli_config_dir is not None:
                binds.append((str(cli_config_dir), cli_config_container, None))
            binds.append((str(output_dir), "/output", None))
            # The instance's agent-system tree(s) under /output — appended
            # AFTER /output so the parent bind is in place. One directory for
            # Claude Code, two for Codex; see Preset.agent_dirs().
            for host_dir, container_path in preset.agent_dirs():
                binds.append((str(host_dir), container_path, None))
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
            if host_cli is not None:
                binds.append((str(host_cli.install_dir), cli_install_container, "ro"))

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
            if cli_config_dir is not None:
                instance_envs[cli_config_var] = cli_config_container
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
                binary = codex_binary if preset.is_codex else claude_binary
                cli_label = "Codex" if preset.is_codex else "Claude Code"
                if host_cli is not None:
                    cli_container_bin = host_cli.container_bin_path
                else:
                    cli_container_bin = binary.resolve_in_container(
                        apptainer_bin, instance_name,
                    )
                    if not cli_container_bin:
                        print(f"{cli_label} not found on host. Installing inside the container...")
                        cli_container_bin = binary.install_in_container(
                            apptainer_bin, instance_name,
                        )

                exec_envs = {
                    "TERM": os.environ.get("TERM", "xterm-256color"),
                    "LANG": os.environ.get("LANG", "C.UTF-8"),
                }
                if cli_config_dir is not None:
                    exec_envs[cli_config_var] = cli_config_container
                exec_envs.update(sched_envs)
                if not preset.is_codex:
                    exec_envs.update(_claude_code_env_passthrough())

                cli_argv = [
                    "bash", "-c",
                    'export PATH="/root/.local/bin:${PATH}"; exec "$@"', "_",
                    cli_container_bin,
                ]
                system_prompt_append = preset.resolve_system_prompt(REPO_ROOT)
                if preset.is_codex:
                    # No --sandbox flag: the sandbox posture is the operator's
                    # to choose, the same way the Claude Code path pre-approves
                    # nothing.
                    #
                    # Know what you are choosing between. Codex's sandbox is
                    # bubblewrap, and bubblewrap cannot nest inside Apptainer's
                    # user namespace — so under Codex's default workspace-write
                    # mode every command inside the container dies with
                    #   bwrap: Can't bind mount /oldroot/ on /newroot/
                    # and comes back as an approval request. A containerized
                    # session that needs to run commands therefore wants
                    # `--sandbox danger-full-access` passed through run.sh
                    # (argv is forwarded to codex verbatim, below); the
                    # container itself is then the boundary — a per-instance
                    # overlay under --cleanenv, seeing only the bound paths,
                    # exactly the boundary the Claude Code path relies on.
                    #
                    # An install (no container) has no such conflict and keeps
                    # Codex's own sandbox, which there is the only boundary.
                    # The lead's slate has no per-role file to ride in, so it is
                    # concatenated onto the append here. That makes it loaded at
                    # session start, which also means a slate the lead writes is
                    # live from the *next* session — the same as Claude Code,
                    # where auto-memory is read once at start-up.
                    system_prompt_append = _with_lead_slate(system_prompt_append, output_dir)
                    if system_prompt_append:
                        # Additive: Codex splices this into its own developer
                        # message rather than replacing it (unlike
                        # model_instructions_file, which would drop the built-in
                        # tool and sandbox instructions along with it).
                        cli_argv += ["-c", f"developer_instructions={system_prompt_append}"]
                    if preset.disallowed_tools:
                        # Codex scopes tools by sandbox and permission profile,
                        # per role, not by a global deny-list — so this key has
                        # no equivalent to translate into.
                        print(
                            "madrun: NOTE — disallowed_tools is set in config.yaml but has no "
                            "Codex equivalent; restrict tools per role (sandbox_mode) or via "
                            "the permission profile in .codex/config.toml. Ignoring it.",
                            flush=True,
                        )
                else:
                    if system_prompt_append:
                        cli_argv += ["--append-system-prompt", system_prompt_append]
                    if preset.disallowed_tools:
                        cli_argv += ["--disallowed-tools", *preset.disallowed_tools]
                    # --session-id is Claude-Code-only; Codex names sessions itself
                    # and resumes them with its `resume` subcommand.
                    cli_argv += [*session_id_args]
                if preset.max_turns is not None:
                    # No interactive equivalent on either CLI — Claude Code's
                    # --max-turns is a print-mode (-p) flag. Say so rather than
                    # dropping the key silently.
                    print(
                        "madrun: NOTE — max_turns is set in config.yaml but only "
                        "applies to non-interactive runs; ignoring it.",
                        flush=True,
                    )
                # No --model / --effort: this is an interactive session with a
                # human at the terminal, so the model and the reasoning effort
                # are theirs to pick — in-session, or on the command line, which
                # the passthrough below forwards verbatim. (The benchmark
                # spawner is the opposite case and does pin them: a bench spawn
                # is unattended and the (preset, model, effort) cell IS the
                # experiment. Don't copy that here.)
                cli_argv += [*argv]

                cmd = [str(apptainer_bin), "exec", "--cleanenv"]
                for k, v in exec_envs.items():
                    cmd += ["--env", f"{k}={v}"]
                # CWD is /output: the project root, where the instance's .claude
                # is mounted and where `memory: project` resolves.
                cmd += ["--pwd", "/output", f"instance://{instance_name}", *cli_argv]

                # Final guard: nothing auth-related may be in the env passed
                # to the claude subprocess. apptainer --cleanenv strips host
                # env, but this catches a programming error (e.g. an exec_envs
                # entry accidentally re-introducing one).
                for k in exec_envs:
                    if k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"):
                        die(f"refusing to exec {cli_label}: exec_envs contains {k!r}")
                assert_no_api_keys()

                subprocess.run(cmd)
            except LaunchError as e:
                die(e.message, e.hint)
        finally:
            _do_cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
