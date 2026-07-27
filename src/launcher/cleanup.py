"""Stop the apptainer instance(s) a run left behind.

``./cleanup_madrun.sh`` lands here. Runs are independent by design — each holds
its own lock, overlay and instance name, and several can be live at once — so
this never assumes there is exactly one thing to stop. With a terminal it shows
what is running and lets you pick; without one it acts only when the choice is
unambiguous.

It stops *sessions*. It does not delete run directories: those hold the memory
the next fork inherits, and removing them is a decision for you, not for a
cleanup script.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import apptainer
from .errors import LaunchError, die
from .paths import REPO_ROOT, resolve_path
from .settings import load_config_env
from .setup import instance_label


USAGE = """\
Usage: cleanup_madrun.sh [options]

With no options: show the running sessions and ask which to stop.

Options:
      --run_dir DIR           Run directory (defaults to repo run_dir)
      --instance_name NAME    Stop this apptainer instance, no questions asked
      --all                   Stop every running madagents session
  -h, --help                  Show this help and exit

Stops sessions only — run directories (and the memory in them) are left alone.
"""


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--run_dir", default=None)
    p.add_argument("--instance_name", default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("-h", "--help", action="store_true")
    args, _ = p.parse_known_args(argv)
    return args


def _madagents_instances(apptainer_bin: Path) -> list[str]:
    return [
        name for name in apptainer.list_instances(apptainer_bin)
        if name == "madagents" or name.startswith("madagents-")
    ]


def _instance_owners(run_dir: Path) -> dict[str, Path]:
    """Map apptainer instance name → the run directory that started it.

    Every run records its instance name under
    ``<RUN_DIR>/workdirs/<stamp>/logs/instance_name.txt``. A run instance sets
    RUN_DIR to ``<instance>/run``, so from the repo-level run_dir those sit one
    level deeper under ``instances/``; a bare run puts them directly under
    ``workdirs/``. Read both, so a session can be shown by the name its owner
    chose rather than by an opaque apptainer instance id.
    """
    owners: dict[str, Path] = {}
    # (glob, how many levels up from the marker file the owner sits)
    #   <instance>/run/workdirs/<stamp>/logs/instance_name.txt -> <instance>
    #   <run_dir>/workdirs/<stamp>/logs/instance_name.txt      -> <run_dir>
    sources = [
        ((run_dir / "instances").glob("*/run/workdirs/*/logs/instance_name.txt"), 4),
        ((run_dir / "workdirs").glob("*/logs/instance_name.txt"), 3),
    ]
    marks = [(mark, depth) for glob, depth in sources for mark in glob]
    for mark, depth in sorted(marks, key=lambda pair: pair[0].stat().st_mtime):
        try:
            name = mark.read_text().splitlines()[0].strip()
        except (OSError, IndexError):
            continue
        if name:
            owners[name] = mark.parents[depth]
    return owners


def _describe(name: str, owners: dict[str, Path]) -> str:
    owner = owners.get(name)
    if owner is None:
        return f"{name}\n       (no run directory claims this — orphan?)"
    return f"{instance_label(owner.name)}\n       {owner}\n       {name}"


def _choose(running: list[str], owners: dict[str, Path]) -> list[str]:
    """Ask which sessions to stop. Returns the chosen instance names."""
    print("\nRunning MadAgents sessions:\n")
    for n, name in enumerate(running, 1):
        print(f"  {n}) {_describe(name, owners)}")
    print("\n  a) all of them")
    print("  q) quit, stop nothing\n")

    # One session is unambiguous, so make Enter mean "that one". With several,
    # Enter must not stop anything by default.
    default = "1" if len(running) == 1 else ""
    hint = f" [default {default}]" if default else " (e.g. 1,3)"
    while True:
        try:
            raw = input(f"Stop which?{hint}: ").strip().lower() or default
        except (EOFError, KeyboardInterrupt):
            print()
            return []
        if raw in ("q", "quit"):
            return []
        if raw in ("a", "all"):
            return list(running)
        picks = [tok for tok in raw.replace(",", " ").split() if tok]
        chosen = [
            running[int(tok) - 1] for tok in picks
            if tok.isdigit() and 1 <= int(tok) <= len(running)
        ]
        if chosen and len(chosen) == len(picks):
            return chosen
        print("  ? pick numbers from the list, or a / q.")


def _stop(apptainer_bin: Path, names: list[str]) -> None:
    for name in names:
        print(f"  stopping {name}")
        apptainer.stop_instance(apptainer_bin, name, force=True)
    print("madrun is closed now.")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = _parse_args(argv)
    if args.help:
        print(USAGE)
        return 0

    load_config_env()

    cli_run_dir: Path | None = None
    if args.run_dir is not None:
        p = Path(args.run_dir)
        cli_run_dir = p if p.is_absolute() else Path.cwd() / p

    run_dir_raw = args.run_dir if cli_run_dir else os.environ.get("RUN_DIR") or ""
    if cli_run_dir:
        run_dir = cli_run_dir
    elif run_dir_raw:
        run_dir = resolve_path(run_dir_raw) or (REPO_ROOT / "run_dir")
    else:
        run_dir = REPO_ROOT / "run_dir"

    try:
        apptainer_bin = apptainer.locate()
    except LaunchError as e:
        die(e.message, e.hint)

    if args.instance_name:
        if apptainer.instance_exists(apptainer_bin, args.instance_name):
            subprocess.run(
                [str(apptainer_bin), "instance", "stop", "-F", args.instance_name],
            )
            print("madrun is closed now.")
        else:
            print(f"No running instance named {args.instance_name!r}.")
        return 0

    running = _madagents_instances(apptainer_bin)
    if not running:
        print("madrun is already closed.")
        return 0

    if args.all:
        print(f"Stopping all {len(running)} madagents session(s):")
        _stop(apptainer_bin, running)
        return 0

    if sys.stdin.isatty():
        chosen = _choose(running, _instance_owners(run_dir))
        if not chosen:
            print("Nothing stopped.")
            return 0
        _stop(apptainer_bin, chosen)
        return 0

    # No terminal to ask at. One candidate is unambiguous; more than one is a
    # choice we must not make for the user — stopping a sibling would kill a
    # live session that has nothing to do with why this was run.
    if len(running) == 1:
        _stop(apptainer_bin, running)
        return 0
    owners = _instance_owners(run_dir)
    print(f"{len(running)} madagents sessions are running:")
    for name in running:
        print(f"  {_describe(name, owners)}")
    print(
        "\nRefusing to guess which one to stop. Re-run with "
        "--instance_name NAME, or --all to stop them all."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
