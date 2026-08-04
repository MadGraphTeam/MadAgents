"""Start a session against a self-hosted endpoint.

Mirrors ``launcher.code.main`` for everything about the container — image,
overlay, binds, instance lifecycle, scheduler passthrough — by importing that
machinery rather than copying it. What differs is only how the endpoint reaches
the session, and that depends on the provider the run was built for:

1. **opencode** (the default here) reaches it through a *config file*:
   ``OPENCODE_CONFIG`` points at a per-run overlay whose ``apiKey`` is a
   ``{file:}`` reference to a ``0600`` token file. Nothing credential-shaped
   enters the environment, so the exec-time ``assert_no_api_keys()`` still runs
   on this path exactly as it does in the main launcher — the guarantee is
   asserted here, not merely claimed.
2. **claude_code** has no such indirection: ``ANTHROPIC_BASE_URL`` /
   ``ANTHROPIC_AUTH_TOKEN`` *must* reach the session as variables, and are
   placed on the container environment at exec time from ``local/config.env``.
   The assertion is therefore skipped — on that path alone.

Ambient scrubbing is *kept* either way: ``scrub_api_keys()`` runs exactly as it
does in the main launcher, so whatever happens to be exported in your shell
still never reaches the session. Only the values you declared in
``local/config.env`` are added back, by name, at the last step.
"""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
from pathlib import Path

import json

from launcher import apptainer, claude_binary, images, opencode_binary, scheduler
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
from launcher.settings import assert_no_api_keys, load_config_env, scrub_api_keys
from launcher.workdir import make_session_uuid, make_stamp, make_workdir

from .config import (
    CONFIG_ENV,
    endpoint_env,
    load_local_config,
    model_args,
    opencode_overlay_config,
    redacted_summary,
    write_token_file,
)

_DEFAULT_RUN_DIR = "run_dir"
_DEFAULT_OVERLAY = "image/mad_overlay.img"

#: Where the host's opencode home (its four XDG roots) is bound.
OPENCODE_HOME_CONTAINER = "/opt/.config/opencode-home"
#: Where this launch's endpoint overlay + token file are bound, read-only.
OPENCODE_RUN_DIR_CONTAINER = "/opt/.config/opencode-run"


#: config.env values meaning "on". Anything else — including empty — is off.
_TRUTHY = ("1", "true", "yes", "on")


def websearch_enabled() -> bool:
    """Whether this run opts in to opencode's Exa-backed ``websearch`` tool."""
    return os.environ.get("OPENCODE_ENABLE_WEBSEARCH", "").strip().lower() in _TRUTHY


def _opencode_envs(opencode_home) -> dict[str, str]:
    """The container environment opencode needs.

    **The four XDG roots.** opencode has no ``OPENCODE_HOME`` of its own:
    ``HOME`` alone moves only its config and state, so all four must be named
    explicitly — and under ``--cleanenv`` nothing is inherited, so "explicitly"
    means here. Unset ``OPENCODE_HOME`` leaves them alone and opencode falls
    back to the container's own ``$HOME``, fresh every run.

    **Web search, opt-in.** opencode hides its ``websearch`` tool unless
    ``OPENCODE_ENABLE_EXA`` is set (verified: the tool list gains ``websearch``
    exactly when it is). It is off here by default, and that is a deliberate
    choice for a self-hosted deployment, not an oversight:

    - the keyless path sends every query to **Exa's hosted service**, a third
      party the operator has no contract with — usually the very thing running
      your own model is meant to avoid;
    - it is rate-limited by an undocumented quota (opencode issue #15953 reports
      ``Exa hit rate limit``), so a consultant relying on it fails
      *intermittently*, which is harder to diagnose than a tool that is simply
      absent;
    - it needs general internet egress, which a compute node may not have.

    Set ``OPENCODE_ENABLE_WEBSEARCH=1`` in ``config.env`` to opt in. See the
    note beside it there about what the two literature-checking consultants do
    without it.
    """
    envs: dict[str, str] = {}
    if opencode_home is not None:
        envs.update({
            "XDG_CONFIG_HOME": f"{OPENCODE_HOME_CONTAINER}/config",
            "XDG_DATA_HOME": f"{OPENCODE_HOME_CONTAINER}/data",
            "XDG_CACHE_HOME": f"{OPENCODE_HOME_CONTAINER}/cache",
            "XDG_STATE_HOME": f"{OPENCODE_HOME_CONTAINER}/state",
        })
    if websearch_enabled():
        envs["OPENCODE_ENABLE_EXA"] = "1"
    return envs


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
    # Guard before anything is bound: this launcher assumes a Claude Code
    # system throughout (it binds preset.claude_dir, appends the prompt with
    # --append-system-prompt, and points CLAUDE_CONFIG_DIR at the bound config
    # dir). A codex preset leaves claude_dir as None, so without this the run
    # dies at bind time with an unrecognisable apptainer error instead of a
    # sentence explaining the combination is not supported.
    from launcher.setup import LOCAL_BACKEND, PROVIDERS_BY_BACKEND

    if preset.provider not in PROVIDERS_BY_BACKEND[LOCAL_BACKEND]:
        die(
            f"the agent system at {system_dir} is built for {preset.provider!r}, which "
            f"cannot run against a self-hosted endpoint",
            hint=f"Local runs support: "
                 f"{', '.join(PROVIDERS_BY_BACKEND[LOCAL_BACKEND])}. Build the run with "
                 f"./local/madrun.sh, or start this instance hosted with ./madrun.sh.",
        )
    trees = ", ".join(c for _, c in preset.agent_dirs())
    print(f"madrun-local: agent system {system_dir} [{preset.provider}] ({trees})", flush=True)

    instance_prefix = _instance_prefix()
    output_dir = resolve_path(os.environ.get("OUTPUT_DIR") or "output") or REPO_ROOT / "output"
    run_dir = (
        resolve_path(os.environ.get("RUN_DIR") or _DEFAULT_RUN_DIR)
        or REPO_ROOT / _DEFAULT_RUN_DIR
    )
    claude_config_dir = resolve_path(os.environ.get("CLAUDE_CONFIG_DIR"))
    # opencode splits across four XDG roots (config, data-with-auth, cache, and
    # state) with no single relocation variable of its own, so one host
    # directory holds all four and the launcher points XDG_* at subdirectories
    # of it. This is the opencode analogue of CLAUDE_CONFIG_DIR / CODEX_HOME:
    # the one thing a run cannot obtain for itself.
    opencode_home = resolve_path(os.environ.get("OPENCODE_HOME"))
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

        if claude_config_dir is not None and not preset.is_opencode:
            claude_config_dir.mkdir(parents=True, exist_ok=True)
            _seed_trusted_projects(claude_config_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # --- the endpoint, for opencode: a config overlay plus the token it
        #     references, both written into this launch's workdir.
        run_config_dir = workdir / "opencode"
        if preset.is_opencode:
            run_config_dir.mkdir(parents=True, exist_ok=True)
            token_path = write_token_file(run_config_dir)
            container_token = (
                f"{OPENCODE_RUN_DIR_CONTAINER}/{token_path.name}" if token_path else None
            )
            (run_config_dir / "endpoint.json").write_text(
                json.dumps(opencode_overlay_config(container_token), indent=2) + "\n",
                encoding="utf-8",
            )
            if opencode_home is not None:
                for sub in ("config", "data", "cache", "state"):
                    (opencode_home / sub).mkdir(parents=True, exist_ok=True)
            else:
                print(
                    "madrun-local: NOTE — OPENCODE_HOME is not set, so opencode starts with "
                    "empty config/data/cache inside the container. It fetches its ~3.4 MB "
                    "model catalogue at startup, which needs network egress. Set "
                    "OPENCODE_HOME in config.env to reuse one across runs.",
                    flush=True,
                )

        host_cli = (
            opencode_binary.detect_host_opencode() if preset.is_opencode
            else claude_binary.detect_host_claude()
        )
        cli_install_container = (
            opencode_binary.CONTAINER_INSTALL_DIR if preset.is_opencode else "/opt/claude"
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
            if claude_config_dir is not None and not preset.is_opencode:
                binds.append((str(claude_config_dir), "/opt/.config/.claude", None))
            binds.append((str(output_dir), "/output", None))
            # The agent system's trees, in whatever shape this provider wants
            # them: one for Claude Code, three for opencode. Asking the preset
            # rather than hardcoding .claude is what lets this launcher serve
            # both without knowing which it has.
            for host_dir, container_dir in preset.agent_dirs():
                binds.append((str(host_dir), container_dir, None))
            if preset.is_opencode:
                # One host directory carries opencode's four XDG roots, so a
                # run inherits the models.dev catalogue it already downloaded
                # (opencode fetches ~3.4 MB at startup, which a node without
                # egress cannot) along with any auth and session history.
                if opencode_home is not None:
                    binds.append((str(opencode_home), OPENCODE_HOME_CONTAINER, None))
                # The endpoint overlay + the 0600 token it references. Read-only,
                # and in the run workdir rather than the instance, so a fork
                # inherits neither.
                binds.append((str(run_config_dir), OPENCODE_RUN_DIR_CONTAINER, "ro"))
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
            if host_cli is not None:
                binds.append((str(host_cli.install_dir), cli_install_container, "ro"))
            host_internals = REPO_ROOT / "internals"
            if host_internals.is_dir():
                binds.append((str(host_internals), "/internals", None))
            if sched_binds:
                binds.extend(sched_binds)

            instance_envs = {
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
            }
            if claude_config_dir is not None and not preset.is_opencode:
                instance_envs["CLAUDE_CONFIG_DIR"] = "/opt/.config/.claude"
            if preset.is_opencode:
                instance_envs.update(_opencode_envs(opencode_home))
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
                binary = opencode_binary if preset.is_opencode else claude_binary
                cli_label = "opencode" if preset.is_opencode else "Claude Code"
                if host_cli is not None:
                    claude_container_bin = host_cli.container_bin_path
                else:
                    claude_container_bin = binary.resolve_in_container(
                        apptainer_bin, instance_name,
                    )
                    if not claude_container_bin:
                        print(f"{cli_label} not found on host. Installing inside the container...")
                        claude_container_bin = binary.install_in_container(
                            apptainer_bin, instance_name,
                        )
                if preset.is_opencode and host_cli is not None:
                    # opencode is dynamically linked, unlike the static-pie Codex
                    # binary — so a host install newer than the image's glibc
                    # fails at exec with a loader error that reads like a broken
                    # launcher. Say what it actually is.
                    why = opencode_binary.check_container_compat(
                        apptainer_bin, instance_name, claude_container_bin,
                    )
                    if why:
                        die(
                            f"the host's opencode cannot run inside this image: {why}",
                            hint="opencode links against glibc (floor: 2.17). Rebuild the "
                                 "image, or unset OPENCODE_BIN / remove it from PATH to let "
                                 "the launcher install opencode inside the container instead.",
                        )

                exec_envs = {
                    "TERM": os.environ.get("TERM", "xterm-256color"),
                    "LANG": os.environ.get("LANG", "C.UTF-8"),
                }
                if claude_config_dir is not None and not preset.is_opencode:
                    exec_envs["CLAUDE_CONFIG_DIR"] = "/opt/.config/.claude"
                if preset.is_opencode:
                    exec_envs.update(_opencode_envs(opencode_home))
                    exec_envs["OPENCODE_CONFIG"] = f"{OPENCODE_RUN_DIR_CONTAINER}/endpoint.json"
                exec_envs.update(sched_envs)
                if not preset.is_opencode:
                    exec_envs.update(_claude_code_env_passthrough())
                if preset.is_opencode:
                    # NOTHING credential-shaped goes into the environment here.
                    # opencode reaches the endpoint through OPENCODE_CONFIG,
                    # whose apiKey is a {file:} reference to a 0600 file — so
                    # the guarantee the main launcher asserts still holds on
                    # this path, and we assert it rather than merely claiming
                    # it. The Claude Code branch below cannot do this: it has
                    # no file-based key indirection, so ANTHROPIC_AUTH_TOKEN
                    # must reach the session as a variable.
                    assert_no_api_keys()
                else:
                    # The whole point of this launcher. Added last so nothing
                    # above can shadow it, and never sourced from the ambient
                    # environment — only from local/config.env.
                    exec_envs.update(local_envs)

                claude_argv = [
                    "bash", "-c",
                    'export PATH="/root/.local/bin:${PATH}"; exec "$@"', "_",
                    claude_container_bin,
                ]
                if preset.is_opencode:
                    # No prompt append: the lead's discipline and slate are
                    # declared in the instance's opencode.json `instructions`,
                    # which opencode loads as session context. No --model or
                    # --session-id either — the model default is set in the
                    # endpoint overlay, and opencode names and resumes sessions
                    # itself. The user's own argv still passes straight through.
                    if preset.disallowed_tools:
                        print(
                            "madrun-local: NOTE — disallowed_tools is set in config.yaml but "
                            "has no opencode equivalent; restrict tools with the `permission` "
                            "block in the rendered opencode.json instead. Ignoring it.",
                            flush=True,
                        )
                else:
                    system_prompt_append = preset.resolve_system_prompt(REPO_ROOT)
                    if system_prompt_append:
                        claude_argv += ["--append-system-prompt", system_prompt_append]
                    if preset.disallowed_tools:
                        claude_argv += ["--disallowed-tools", *preset.disallowed_tools]
                    # config.yaml's model/effort are for the hosted path; the
                    # local endpoint's model name comes from local/config.env.
                    # The user's own argv is appended last, so an explicit
                    # --model still wins.
                    claude_argv += model_args()
                    claude_argv += [*session_id_args]
                claude_argv += [*argv]

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
