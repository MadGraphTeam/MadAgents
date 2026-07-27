"""Run-instance harness — materialize the agent system into a self-contained run dir.

``python3 -m launcher setup <source> [--dest DIR] [--name NAME] [--memory PACK] [--run]``

*source* is a directory holding ``config.yaml`` + ``.claude/`` — the shipped
``madagents/``, or an existing run instance. A *run instance* has that same
shape, which is what makes it both re-runnable and forkable:

    <dest>/
      .claude/       copy of the source's .claude (symlinks dereferenced); the
                     lead + consultant memory is written back here during a run
      config.yaml    the configuration, with paths repointed to this folder
      prompts/       (and any other assets the configuration references)
      overlay.img    fresh per-instance writable overlay (apptainer overlay create)
      run.sh         generated launcher invocation — `cd <dest> && ./run.sh`
      run/           runtime scratch (created on first run)
      output/        deliverables + the wiki at output/.madagents/wiki/; this is
                     the session's project root (/output in the container)
      memory-pack.txt  which shipped pack seeded this instance, if any

``--memory`` selects the *learned tier* the instance starts from — one of the
packs in ``memory/`` (see ``memory/README.md``). A pack is copied in, never
bound, so the session extends its own copy and the shipped pack stays fixed.
The learned tier spans both ``.claude/`` (slates) and ``output/.madagents/``
(wiki), which is why forking preserves the latter rather than treating all of
``output/`` as disposable.

Seeding the files is only half of it: the tier is *loaded* by Claude Code's
auto-memory, which has to be pointed at this layout. ``_apply_memory_settings``
pins that into the instance's ``.claude/settings.local.json`` — see its
docstring.

The harness only builds the folder; it does not launch a container (``--run``
chains into the generated ``run.sh`` for convenience). Point ``setup`` at a
finished instance to start a new one from its accumulated state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import images
from .errors import die
from .paths import REPO_ROOT, SRC_ROOT
from .workdir import make_stamp

DEFAULT_SYSTEM = REPO_ROOT / "madagents"

#: Shipped memory packs — the learned tier the system starts from. See memory/README.md.
MEMORY_DIR = REPO_ROOT / "memory"
#: Seeded when the source is the shipped system and no --memory was given.
DEFAULT_MEMORY = "pretrained"
#: --memory values meaning "start cold".
NO_MEMORY = ("none", "off", "cold", "")
#: Name shown for the cold option, which is an absence rather than a pack dir.
NO_MEMORY_NAME = "none"
#: Its description, kept here because there is no pack directory to hold one.
NO_MEMORY_DESCRIPTION = (
    "Nothing — the shipped system as-is, with an empty learned tier."
)
#: Filename a pack uses to describe itself, read by ``memory_pack_description``.
MEMORY_DESCRIPTION_FILE = "DESCRIPTION"

#: What a memory pack contributes, as (path in the pack, path in the instance).
#: The wiki lands under ``output/`` because the instance's ``output/`` is the
#: session's project root (``/output`` in the container), which is where the
#: agent system reads and writes it.
_MEMORY_TIERS = (
    (".claude/lead-memory", ".claude/lead-memory"),
    (".claude/agent-memory", ".claude/agent-memory"),
    (".madagents/wiki", "output/.madagents/wiki"),
)

#: Where the lead's slate lives *inside the container*. The instance's
#: ``.claude/`` is bind-mounted at ``/output/.claude`` and the session runs with
#: ``/output`` as its project root, so this is the in-container spelling of
#: ``<instance>/.claude/lead-memory`` — the first tier of ``_MEMORY_TIERS``.
LEAD_MEMORY_CONTAINER_DIR = "/output/.claude/lead-memory"


def _available_memory_packs() -> list[str]:
    if not MEMORY_DIR.is_dir():
        return []
    return sorted(
        d.name for d in MEMORY_DIR.iterdir()
        if d.is_dir() and (d / ".claude").is_dir()
    )


def memory_pack_description(name: str) -> str:
    """One-line description of a memory option, for menus and listings.

    Each shipped pack describes itself in ``memory/<pack>/DESCRIPTION``, so the
    description ships with the pack rather than being hardcoded in the launcher
    — add a pack and it introduces itself. ``none`` is not a directory, so its
    description is the constant above. A pack without the file (or with an empty
    one) simply has no description; it is never an error.
    """
    if name.lower() in NO_MEMORY:
        return NO_MEMORY_DESCRIPTION
    try:
        text = (MEMORY_DIR / name / MEMORY_DESCRIPTION_FILE).read_text()
    except OSError:
        return ""
    return next((ln.strip() for ln in text.splitlines() if ln.strip()), "")


def memory_options() -> list[tuple[str, str]]:
    """Every startable memory option as ``(name, description)``.

    The shipped packs with the default first, then ``none`` — the order the
    menu and ``--list-memory`` both present, so the two never disagree.
    """
    packs = _available_memory_packs()
    ordered = ([DEFAULT_MEMORY] if DEFAULT_MEMORY in packs else []) + [
        p for p in packs if p != DEFAULT_MEMORY
    ]
    ordered.append(NO_MEMORY_NAME)
    return [(p, memory_pack_description(p)) for p in ordered]


def _resolve_memory_pack(name: str) -> Path:
    pack = MEMORY_DIR / name
    if not (pack / ".claude").is_dir():
        available = _available_memory_packs()
        die(
            f"no memory pack named {name!r} in {MEMORY_DIR}",
            hint=f"Available: {', '.join(available) or '(none)'} — or 'none' to start cold.",
        )
    return pack


def _is_instance(source: Path) -> bool:
    """True when *source* is a finished run instance rather than the shipped system.

    Only an instance carries these: ``run.sh`` and ``overlay.img`` are generated
    by this harness, and ``output/`` is created on first run. The distinction
    matters for ``--memory``: forking an instance must inherit *its* accumulated
    memory by default, never silently overwrite it with a shipped pack.
    """
    return any((source / n).exists() for n in ("run.sh", "overlay.img", "output"))


def _resolve_source(source: str):
    """Resolve *source* to the agent system to materialize.

    *source* is a directory containing ``config.yaml`` — the shipped
    ``madagents/``, or an existing run instance (which has the same shape, and
    so can be forked to carry its accumulated memory forward). Accepted either
    as given (relative to the current directory) or relative to the repo root,
    so ``madagents`` works from anywhere.
    """
    from .presets_loader import load_preset

    for candidate in (Path(source), REPO_ROOT / source):
        if (candidate / "config.yaml").is_file():
            resolved = candidate.resolve()
            try:
                return load_preset(resolved), resolved.name
            except (ValueError, FileNotFoundError) as e:
                die(f"failed to load the agent system at {resolved}: {e}")
    die(
        f"no agent system found at {source!r}",
        hint=f"Pass a directory containing config.yaml — the shipped "
             f"'{DEFAULT_SYSTEM.name}', or an existing run instance to fork.",
    )


def _repoint(literal: str, source_preset_dir: Path, instance: Path) -> str:
    """Map a config.yaml path value into the instance.

    Repo-relative or absolute paths that point *inside* the source preset are
    rewritten to the matching absolute path inside the instance (which holds a
    copy). Paths pointing outside the preset (e.g. a shared canonical corpus)
    are left as a resolved absolute path so they still resolve at run time.
    """
    p = Path(literal)
    abs_src = (p if p.is_absolute() else (REPO_ROOT / p)).resolve()
    try:
        rel = abs_src.relative_to(source_preset_dir.resolve())
    except ValueError:
        return str(abs_src)
    return str(instance / rel)


def _materialize_yaml(preset, instance: Path) -> None:
    """Repoint madgraph_docs_path + append_system_prompt_file in the instance's config.yaml.

    Done as literal-string replacement on the copied YAML so comments/formatting
    survive. The source values are specific enough that they don't collide with
    prose in the file.
    """
    yaml_path = instance / "config.yaml"
    text = yaml_path.read_text()
    src_dir = preset.preset_dir

    # load_preset enforces name == directory name, so the instance's name must
    # match its dir — this is also what lets a finished instance be forked.
    text = re.sub(r"^name:.*$", f"name: {instance.name}", text, count=1, flags=re.MULTILINE)

    if preset.madgraph_docs_path:
        text = text.replace(
            preset.madgraph_docs_path, _repoint(preset.madgraph_docs_path, src_dir, instance)
        )
    asp = preset.append_system_prompt_file
    if asp:
        entries = [asp] if isinstance(asp, str) else list(asp)
        for entry in entries:
            text = text.replace(entry, _repoint(entry, src_dir, instance))
    yaml_path.write_text(text)


def _copy_preset_tree(source: Path, instance: Path) -> None:
    """Copy the preset tree into the instance — reflink + sparse (CoW-shared, sparse-aware).

    A drop-in for ``shutil.copytree(..., symlinks=False)`` that shells out to
    ``cp`` so it shares blocks via reflink on CoW filesystems and stays
    sparse-aware. ``-L`` dereferences symlinks so the instance is a
    self-contained, symlink-free copy. On filesystems without reflink (e.g. NFS)
    ``--reflink=auto`` falls back to a normal copy; ``--sparse=always`` still
    preserves holes. The instance dir must not pre-exist (cp then creates it as
    a copy of *source*).
    """
    subprocess.run(
        ["cp", "-RL", "--reflink=auto", "--sparse=always",
         "--preserve=mode,timestamps", str(source), str(instance)],
        check=True,
    )


#: Top-level entries that belong to a *run* rather than to the agent system.
#: Copying a shipped system never produces them, but a finished instance has
#: them all — and each is either regenerated here or actively harmful to
#: inherit (``overlay.img`` makes ``apptainer overlay create`` fail outright).
#: They are skipped at copy time rather than deleted afterwards: the repo can
#: sit on a filesystem without reflink support (NFS), where copy-then-delete
#: means dragging a multi-GB overlay and a full deliverables tree across the
#: wire only to unlink them.
_INSTANCE_ARTIFACTS = ("overlay.img", "run.sh", "run", "output")


def _copy_system_tree(source: Path, instance: Path) -> None:
    """Copy the *agent system* out of *source*, leaving run artifacts behind.

    Everything at the top level except ``_INSTANCE_ARTIFACTS`` — for the
    shipped system that is all of it, for an instance it is the part that
    survives a fork (``.claude/``, ``config.yaml``, ``prompts/``, …).
    """
    instance.mkdir(parents=True)
    for child in sorted(source.iterdir()):
        if child.name in _INSTANCE_ARTIFACTS:
            continue
        _copy_preset_tree(child, instance / child.name)


def _inherit_wiki(source: Path, instance: Path) -> None:
    """Carry a forked instance's wiki (``output/.madagents/``) into the new one.

    The agent's memory is deliberately kept, so a fork starts warm — and that
    memory lives in two places, not one: the slates under ``.claude/`` (copied
    with the system tree) and the **wiki** under ``output/.madagents/``, which
    sits inside the otherwise-disposable deliverables tree. Dropping it with the
    rest of ``output/`` would silently fork a system that still has 46
    consultant slates but no longer has the pages they point at.
    """
    src = source / "output" / ".madagents"
    if not src.is_dir():
        return
    dst = instance / "output" / ".madagents"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    _copy_preset_tree(src, dst)


def _create_overlay(instance: Path) -> bool:
    """Create a FRESH per-instance writable overlay via ``apptainer overlay create``.

    Not a clone of ``image/mad_overlay.img``: a fresh overlay gives each instance
    a clean, user-owned, writable scratch layer with a unique filesystem UUID.
    The MG5 stack lives in the SIF, so the overlay carries no baseline content —
    cloning the canonical overlay instead reproduces its upper-dir ownership +
    UUID, which breaks no-fakeroot ``apptainer instance start`` (verified: a
    `cp`-cloned overlay and the canonical both fail "upper not writable", while a
    fresh ``overlay create`` starts cleanly). Returns True on success.
    """
    from . import apptainer
    from .settings import load_config_env

    if (REPO_ROOT / "config.env").is_file():
        try:
            load_config_env()  # populate APPTAINER_DIR from config.env
        except Exception:
            pass
    try:
        apptainer_bin = apptainer.locate()
    except Exception as e:
        # The instance's run.sh points at <instance>/overlay.img REGARDLESS, so
        # the run fails with a clear "overlay not found" rather than silently
        # falling back to the shared image/mad_overlay.img — which two instances
        # would then write to concurrently.
        print(
            f"madrun setup: WARNING — apptainer not found ({e}); this instance has NO "
            f"overlay yet and will not start until one exists at {instance}/overlay.img.\n"
            f"madrun setup:   Set APPTAINER_DIR in config.env and re-run setup, or create it "
            f"manually:\n"
            f"madrun setup:   apptainer overlay create --sparse --size 10240 "
            f"{instance}/overlay.img",
            file=sys.stderr,
        )
        return False
    subprocess.run(
        [str(apptainer_bin), "overlay", "create", "--sparse", "--size", "10240",
         str(instance / "overlay.img")],
        check=True,
    )
    return True


def _prepare_output_root(instance: Path) -> None:
    """Make the instance's ``output/`` a deterministic Claude Code project root.

    The trained madagents preset's ``memory: project`` agents read/write
    per-subagent memory at the absolute path ``/output/.claude/agent-memory/
    <name>/MEMORY.md`` — the layout the memory packs were accumulated under.
    For the trained memory to load **warm**, the instance must run with
    ``/output`` as the CC project root and the trained ``.claude`` mounted at
    ``/output/.claude`` (the launcher does the binds + CWD). Two host-side
    Two host-side pieces:

    - ``git init`` the output dir so CC's project-root resolver pins
      ``<project_root>`` to ``/output`` deterministically (independent of where
      the agent ``cd``s). Because the launcher mounts the trained ``.claude`` at
      ``/output/.claude`` (→ ``<instance>/.claude``), memory round-trips back to
      the instance's promotable ``.claude``.
    - Pre-create the ``.claude`` mountpoint inside it so the nested
      ``/output/.claude`` bind attaches deterministically.

    Idempotent (the ``.git`` guard). Harmless for presets without memory agents.
    """
    output_dir = instance / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".claude").mkdir(exist_ok=True)
    # The wiki's two halves, present even on a cold start so the layout is the
    # same whether or not a memory pack was seeded.
    for sub in ("consultants", "lead"):
        (output_dir / ".madagents" / "wiki" / sub).mkdir(parents=True, exist_ok=True)
    if not (output_dir / ".git").exists():
        subprocess.run(["git", "init", "-q", str(output_dir)], check=True)


def _seed_environment(instance: Path) -> None:
    """Seed the run's environment description at ``output/CLAUDE.md``.

    The session starts with ``output/`` as both its CWD and its project root, so
    a ``CLAUDE.md`` there is picked up by Claude Code on its own — no preset
    change, nothing to wire. The text comes from the *image* the run will use
    (``images.seed_text``): what is installed, and where, is a property of the
    build, and nothing else in the run knows it.

    Written once, here, and never touched again. The overlay is writable, so the
    filesystem a run ends with is not the one the image shipped — the seed asks
    the session to keep the description current, and that only works if the
    launcher is not going to overwrite its edits on the next start. A fork is a
    new run, so it seeds fresh rather than inheriting a description of software
    its own fresh overlay may not have.
    """
    target = instance / "output" / "CLAUDE.md"
    if target.exists():
        return
    if (REPO_ROOT / "config.env").is_file():
        try:
            from .settings import load_config_env

            load_config_env()  # APPTAINER_IMAGE, when config.env pins one
        except Exception:
            pass
    seed = images.seed_file(images.resolve_image(os.environ.get("APPTAINER_IMAGE")))
    if seed is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"madrun setup: environment seeded from {seed}", flush=True)


def _seed_memory(pack: Path, instance: Path) -> None:
    """Copy a shipped memory pack's learned tier into the instance.

    The pack itself is never touched again after this: the instance holds a full
    copy, the container binds only the instance, and the session reads and writes
    that copy. So a run extends the memory it was given while ``memory/<pack>/``
    stays fixed — which is what makes the packs reproducible starting points.

    Each tier replaces rather than merges, and **a tier the pack does not carry
    means an empty tier, not an inherited one**. Both halves matter when seeding
    over an instance that already had memory (``--memory`` on a fork): keeping
    what the pack omits would produce a learned tier that never existed as a
    whole — e.g. ``bare-local``'s empty lead slate sitting on top of 46
    inherited consultant slates pointing at an inherited wiki.
    """
    for src_rel, dst_rel in _MEMORY_TIERS:
        src = pack / src_rel
        dst = instance / dst_rel
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            _copy_preset_tree(src, dst)
        else:
            dst.mkdir()
    (instance / "memory-pack.txt").write_text(
        f"{pack.name}\n"
        f"# Seeded from {pack} by `madrun setup`.\n"
        f"# This instance now owns its copy; the pack is unchanged. See memory/README.md.\n"
    )


def _record_fork_lineage(source: Path, instance: Path) -> None:
    """Mark an inherited ``memory-pack.txt`` as a fork of *source*.

    A fork copies the source's file verbatim, which would report the pack name
    as if the instance still held that pack — the menu reads line 1 for its
    MEMORY column. The memory has moved on since, so say so, and keep the
    provenance underneath. Idempotent across repeated forks.
    """
    marker = instance / "memory-pack.txt"
    try:
        lines = marker.read_text().splitlines()
    except OSError:
        lines = []
    origin = (lines[0].strip() if lines else "") or "cold"
    label = origin if origin.endswith("+fork") else f"{origin}+fork"
    body = "\n".join(line for line in lines[1:] if line.startswith("#"))
    marker.write_text(
        f"{label}\n"
        f"# Forked from {source} by `madrun setup`.\n"
        + (body + "\n" if body else "")
    )


def _apply_memory_settings(preset, instance: Path) -> None:
    """Pin auto-memory on/off and point it at the instance, in settings.local.json.

    Seeding the files is not enough: the learned tier is *loaded* by Claude
    Code's auto-memory, and both halves of that need saying out loud.

    - ``autoMemoryEnabled`` — CC's built-in default is on, but the effective
      value is merged over ``userSettings`` → ``projectSettings`` →
      ``localSettings``, and the launcher bind-mounts the user's own Claude
      config into the container. A user whose ``settings.json`` turns
      auto-memory off would silently get a run where none of the 46 consultant
      slates load. Writing the flag here (localSettings, so it wins) makes the
      ``auto_memory_enabled:`` key in config.yaml real, and keeps activation
      independent of both the user's config and the binary's default. Pinned in
      both directions for the same reason.
    - ``autoMemoryDirectory`` — the lead's slate has no ``memory: project``
      card to place it, and CC's default is
      ``<config>/projects/<slug>/memory/``: outside the instance, shared by
      every run (all instances have project root ``/output``, hence one slug),
      and not carried by a fork. Point it at the seeded tier instead.

    The directory key is dropped when auto-memory is off — the flag alone then
    carries the decision, with nothing pointing at a tier no one will read.
    """
    settings_path = instance / ".claude" / "settings.local.json"
    try:
        data = json.loads(settings_path.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    data["autoMemoryEnabled"] = bool(preset.auto_memory_enabled)
    if preset.auto_memory_enabled:
        data["autoMemoryDirectory"] = LEAD_MEMORY_CONTAINER_DIR
    else:
        data.pop("autoMemoryDirectory", None)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n")


def _describe_memory(instance: Path) -> str:
    """Count what the instance's learned tier actually holds, for the setup log."""
    slates = instance / ".claude" / "agent-memory"
    lead = instance / ".claude" / "lead-memory"
    wiki = instance / "output" / ".madagents" / "wiki"
    n_slates = len([d for d in slates.iterdir() if d.is_dir()]) if slates.is_dir() else 0
    n_lead = len(list(lead.glob("*.md"))) if lead.is_dir() else 0
    n_wiki = len(list(wiki.rglob("*.md"))) if wiki.is_dir() else 0
    return f"{n_slates} slates, {n_lead} lead files, {n_wiki} wiki pages"


def _write_run_sh(instance: Path, instance_name: str) -> Path:
    """Write the instance's launcher invocation.

    ``APPTAINER_OVERLAY`` is pinned to this instance's own overlay
    unconditionally — including when setup could not create one. Omitting it
    would let the run fall back to the shared ``image/mad_overlay.img`` (or a
    config.env value), which two instances would then write to concurrently;
    two apptainer instances cannot safely share one ext3 overlay. Pinning it
    turns that silent corruption into a clear "Overlay image not found" at
    startup.
    """
    run_sh = instance / "run.sh"
    run_sh.write_text(
        "#!/usr/bin/env bash\n"
        "# Generated by `python3 -m launcher setup`. Starts this run instance.\n"
        "# Re-run freely (--resume / --continue forward to claude). Edits to .claude/ —\n"
        "# including memory the agent writes during a run — stay in this folder, so\n"
        "# re-running picks up where the last run left off.\n"
        "set -euo pipefail\n"
        'INSTANCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
                'exec env MADRUN_SYSTEM_DIR="$INSTANCE" \\\n'
        f'         MADRUN_INSTANCE="{instance_name}" \\\n'
        '         RUN_DIR="$INSTANCE/run" \\\n'
        '         OUTPUT_DIR="$INSTANCE/output" \\\n'
        '         APPTAINER_OVERLAY="$INSTANCE/overlay.img" \\\n'
        f'         PYTHONPATH="{SRC_ROOT}${{PYTHONPATH:+:$PYTHONPATH}}" \\\n'
        '         python3 -m launcher code "$@"\n'
    )
    run_sh.chmod(0o755)
    return run_sh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="madrun setup",
        description="Materialize the agent system into a self-contained run instance.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="madagents",
        help="The agent system to materialize: the shipped 'madagents' (default), "
             "or the path to an existing run instance to fork — which carries its "
             "accumulated memory into the new instance.",
    )
    parser.add_argument(
        "--dest", default=None,
        help="Instance dir. Default: run_dir/instances/<name>__<stamp>/ (gitignored).",
    )
    parser.add_argument(
        "--name", default=None,
        help="Instance label (used in the dir name + the apptainer instance prefix). "
             "Default: the source preset name.",
    )
    parser.add_argument(
        "--memory", default=None, metavar="PACK",
        help="Learned tier to start from, copied into the instance: "
             f"{', '.join(_available_memory_packs()) or '(no packs installed)'}, "
             "or 'none' to start cold. Default: "
             f"'{DEFAULT_MEMORY}' when materializing the shipped system; when forking "
             "an instance, inherit its own memory instead. See memory/README.md.",
    )
    parser.add_argument(
        "--run", action="store_true",
        help="After building the instance, launch it (exec its run.sh).",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    instance = build_instance(
        source=args.source, dest=args.dest, name=args.name, memory=args.memory,
    )
    run_sh = instance / "run.sh"
    print(f"madrun setup: instance ready at {instance}")
    print(f"madrun setup: run it →  (cd {instance} && ./run.sh)")
    if args.run:
        print("madrun setup: launching (--run)...", flush=True)
        os.execv(str(run_sh), [str(run_sh)])
    return 0


def sanitize_name(name: str) -> str:
    """Reduce a user-supplied run name to something safe for a dir + instance name."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip("-._")
    return cleaned or "madagents"


def instance_label(dir_name: str) -> str:
    """The user-chosen label inside an instance dir name (``<label>__<stamp>``)."""
    return dir_name.partition("__")[0]


def build_instance(
    source: str = "madagents",
    dest: str | None = None,
    name: str | None = None,
    memory: str | None = None,
) -> Path:
    """Materialize *source* into a run instance and return its path.

    The engine behind both ``madrun setup`` and the interactive front end.
    *memory* is a pack name, ``"none"`` for cold, or ``None`` to use the default
    (a pack for the shipped system; inherit for a fork).
    """
    preset, default_name = _resolve_source(source)
    forking = _is_instance(preset.preset_dir)
    if name:
        name = sanitize_name(name)
    elif forking:
        # Not the source's dir name: that is already ``<label>__<stamp>``, so
        # reusing it would build ``<label>__<stamp>__<stamp>`` — and since the
        # menu shows the text before the first ``__``, every fork of a run would
        # list under the same label as the original. Fork off the label instead.
        name = f"{instance_label(preset.preset_dir.name)}-fork"
    else:
        name = default_name

    # Resolve the memory pack before doing any work, so a typo fails immediately
    # rather than after building the instance.
    if memory is None:
        memory_name = None if forking else DEFAULT_MEMORY
    else:
        memory_name = None if memory.lower() in NO_MEMORY else memory
    memory_pack = _resolve_memory_pack(memory_name) if memory_name else None
    if memory_pack and forking:
        print(
            f"madrun setup: WARNING — source is a run instance, so memory "
            f"{memory_name!r} REPLACES the memory it accumulated.",
            file=sys.stderr, flush=True,
        )

    if dest:
        instance = Path(dest).resolve()
    else:
        instance = (REPO_ROOT / "run_dir" / "instances" / f"{name}__{make_stamp()}").resolve()
    if instance.exists():
        die(f"instance dir already exists: {instance}",
            hint="Pick a different name, or remove the existing dir.")

    print(f"madrun setup: materializing {preset.name!r} → {instance}", flush=True)
    instance.parent.mkdir(parents=True, exist_ok=True)
    # Self-contained copy (dereference any symlinks), run artifacts left behind.
    _copy_system_tree(preset.preset_dir, instance)
    if forking:
        _inherit_wiki(preset.preset_dir, instance)
        _record_fork_lineage(preset.preset_dir, instance)
    _materialize_yaml(preset, instance)
    if memory_pack:
        _seed_memory(memory_pack, instance)
    _apply_memory_settings(preset, instance)
    # After seeding, not before: seeding replaces whole tiers, so this is what
    # restores the project-root scaffolding (git repo, .claude mountpoint, the
    # wiki's two halves) that a replaced tier may have taken with it. Idempotent.
    _prepare_output_root(instance)
    _seed_environment(instance)
    if memory_pack:
        print(f"madrun setup: memory pack {memory_pack.name!r} seeded "
              f"({_describe_memory(instance)})", flush=True)
    elif forking:
        print(f"madrun setup: inherited memory from the source instance "
              f"({_describe_memory(instance)})", flush=True)
    else:
        print("madrun setup: no memory pack — starting cold", flush=True)
    if not preset.auto_memory_enabled:
        print(
            "madrun setup: WARNING — auto_memory_enabled is false in config.yaml, "
            "so the learned tier will not be loaded or extended by the session.",
            file=sys.stderr, flush=True,
        )
    _create_overlay(instance)
    _write_run_sh(instance, instance.name)
    return instance


if __name__ == "__main__":
    sys.exit(main())
