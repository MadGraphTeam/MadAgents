"""Interactive front end — pick a run, then start it.

``./madrun.sh`` lands here. It shows the runs you already have, lets you resume
one or start a new one (optionally forking an old run's memory), and then execs
that run instance's ``run.sh`` so the session starts immediately. Arguments it
does not recognise are forwarded verbatim to ``claude``, so
``./madrun.sh --resume`` and ``./madrun.sh --model opus`` work.

Non-interactive (no TTY, or with ``--new``/``--instance``/``--fork``) it skips
the menu and does the obvious thing, so scripts and CI keep working.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import sys
import time
from pathlib import Path

from .errors import die
from .paths import REPO_ROOT
from .setup import (
    DEFAULT_MEMORY,
    MEMORY_DIR,
    NO_MEMORY,
    NO_MEMORY_NAME,
    _available_memory_packs,
    build_instance,
    instance_label,
    memory_options,
    sanitize_name,
)

INSTANCES_DIR = REPO_ROOT / "run_dir" / "instances"


def _is_running(instance: Path) -> bool:
    """True when a session currently holds this instance's run lock.

    Best effort, for the menu's [RUNNING] marker: if the probe cannot decide we
    report False, because the authority is ``madrun_lock`` in ``code.py``, which
    refuses the second run regardless of what this says.

    Opened O_RDWR, never O_RDONLY: on NFS — where a shared repo usually lives —
    flock() is emulated with POSIX record locks, and taking LOCK_EX on a
    read-only fd fails with EBADF. No O_CREAT and no truncation: probing must
    not create or disturb the lock file.
    """
    lock = instance / "run" / ".madrun.lock"
    if not lock.is_file():
        return False
    try:
        fd = os.open(str(lock), os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    except OSError:
        return False
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def _age(ts: float) -> str:
    secs = max(0, time.time() - ts)
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs >= size:
            return f"{int(secs // size)}{unit} ago"
    return "just now"


class Instance:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        # Instance dirs are "<label>__<stamp>"; show the label the user chose,
        # with the stamp as secondary detail.
        self.label = instance_label(path.name)
        self.stamp = path.name.partition("__")[2]
        self.running = _is_running(path)

    @property
    def memory(self) -> str:
        f = self.path / "memory-pack.txt"
        if f.is_file():
            return f.read_text().splitlines()[0].strip() or "?"
        return "cold"

    @property
    def wiki_pages(self) -> int:
        wiki = self.path / "output" / ".madagents" / "wiki"
        return len(list(wiki.rglob("*.md"))) if wiki.is_dir() else 0

    @property
    def touched(self) -> float:
        # The run dir is rewritten every launch; fall back to the instance dir.
        run = self.path / "run"
        return (run if run.is_dir() else self.path).stat().st_mtime

    def describe(self) -> str:
        flag = "   [RUNNING]" if self.running else ""
        return (f"{self.label:<22} {self.memory:<17} "
                f"{self.wiki_pages:>4} wiki pages   {_age(self.touched):<10}{flag}")


def _list_instances() -> list[Instance]:
    if not INSTANCES_DIR.is_dir():
        return []
    # run.sh is written last, so requiring it hides instances whose build was
    # interrupted — they would otherwise list as usable and fail at launch.
    found = [
        Instance(d) for d in INSTANCES_DIR.iterdir()
        if d.is_dir() and (d / "config.yaml").is_file() and (d / "run.sh").is_file()
    ]
    return sorted(found, key=lambda i: i.touched, reverse=True)


def _ask(prompt: str, default: str = "") -> str:
    try:
        answer = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(130)
    return answer or default


def _print_memory_options() -> list[str]:
    """Print the memory options with their descriptions; return their names.

    Descriptions come from each pack's own ``DESCRIPTION`` file, so a pack
    dropped into ``memory/`` introduces itself here with no launcher change.
    """
    options = memory_options()
    for n, (name, description) in enumerate(options, 1):
        mark = "  (default)" if name == DEFAULT_MEMORY else ""
        print(f"  {n}) {name:<18} {description}{mark}")
    return [name for name, _ in options]


def _choose_memory_pack() -> str | None:
    """Menu for the starting memory. Returns a pack name, or None for cold."""
    if not _available_memory_packs():
        # Nothing to choose between: cold is the only possible start.
        return None
    print("\nStarting memory:\n")
    names = _print_memory_options()
    print()
    while True:
        raw = _ask(f"Select [1-{len(names)}, default 1]: ", "1")
        chosen = None
        if raw.isdigit() and 1 <= int(raw) <= len(names):
            chosen = names[int(raw) - 1]
        elif raw in names:
            chosen = raw
        elif raw.lower() in NO_MEMORY:
            chosen = NO_MEMORY_NAME
        if chosen is not None:
            return None if chosen.lower() in NO_MEMORY else chosen
        print("  ? pick one of the listed numbers.")


def _ask_name(default: str) -> str:
    """Name the run. It becomes the instance dir, so you can find it again."""
    print()
    raw = _ask(f"Name this run [{default}]: ", default)
    return sanitize_name(raw)


def _menu(instances: list[Instance]) -> tuple[str, Instance | None]:
    """Top-level menu. Returns (action, instance) with action in
    {"resume", "new", "fork"}."""
    print("\nMadAgents runs:\n")
    print(f"     {'NAME':<22} {'MEMORY':<17} {'WIKI':>4}              LAST USED")
    for n, inst in enumerate(instances, 1):
        print(f"  {n}) {inst.describe()}")
    if instances:
        print()
    print("  n) new run")
    if instances:
        print("  f) fork an existing run (inherit its memory, fresh workspace)")
    print("  q) quit\n")

    default = "1" if instances else "n"
    while True:
        raw = _ask(f"Select [default {default}]: ", default).lower()
        if raw == "q":
            sys.exit(0)
        if raw == "n":
            return "new", None
        if raw == "f" and instances:
            return "fork", _pick(instances, "Fork which run")
        if raw.isdigit() and 1 <= int(raw) <= len(instances):
            chosen = instances[int(raw) - 1]
            if chosen.running:
                print("  ! that run is already active — only one session per run "
                      "instance.\n    Pick another, or 'f' to fork it into a new one.")
                continue
            return "resume", chosen
        print("  ? pick a number, or n / f / q.")


def _pick(instances: list[Instance], prompt: str) -> Instance:
    print()
    for n, inst in enumerate(instances, 1):
        print(f"  {n}) {inst.describe()}")
    print()
    while True:
        raw = _ask(f"{prompt} [1-{len(instances)}]: ")
        if raw.isdigit() and 1 <= int(raw) <= len(instances):
            return instances[int(raw) - 1]
        print("  ? pick one of the listed numbers.")


def _launch(instance: Path, claude_args: list[str]) -> None:
    run_sh = instance / "run.sh"
    if not run_sh.is_file():
        die(f"{instance} has no run.sh", hint="Rebuild it with ./madrun.sh --new.")
    print(f"\nmadrun: starting {instance.name}\n", flush=True)
    os.execv(str(run_sh), [str(run_sh), *claude_args])


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="madrun.sh",
        description="Pick a MadAgents run and start it. Unrecognised arguments "
                    "are forwarded to claude (e.g. --resume, --model).",
        add_help=True,
    )
    parser.add_argument("--new", action="store_true",
                        help="Skip the menu; start a new run.")
    parser.add_argument("--instance", metavar="PATH",
                        help="Skip the menu; run this existing instance.")
    parser.add_argument("--fork", metavar="PATH",
                        help="Skip the menu; new run inheriting this one's memory.")
    parser.add_argument("--memory", metavar="PACK",
                        help=f"Memory for a new run: "
                             f"{', '.join(_available_memory_packs()) or '(none installed)'}, "
                             f"or 'none' to start with an empty learned tier. "
                             f"Default: {DEFAULT_MEMORY!r}. "
                             f"See --list-memory for what each one carries.")
    parser.add_argument("--name", metavar="NAME", help="Label for the new instance.")
    parser.add_argument("--list", action="store_true",
                        help="List existing runs and exit.")
    parser.add_argument("--list-memory", action="store_true",
                        help="Describe the available memory options and exit.")
    parser.add_argument("--setup-only", action="store_true",
                        help="Build the instance but do not start a session.")
    args, claude_args = parser.parse_known_args(argv)

    if args.list_memory:
        print("\nMemory options for a new run "
              "(./madrun.sh --new --memory PACK):\n")
        _print_memory_options()
        print(f"\nA pack is copied into the run, so the session extends its own "
              f"copy.\nDetails: {MEMORY_DIR / 'README.md'}\n")
        return 0

    instances = _list_instances()

    if args.list:
        if not instances:
            print("No runs yet. `./madrun.sh --new` creates one.")
        for inst in instances:
            print(f"  {inst.describe()}")
            print(f"     {inst.path}")
        return 0

    # --- explicit, non-interactive selections -------------------------------
    if args.instance:
        _launch(Path(args.instance).resolve(), claude_args)

    source: Path | None = None
    memory: str | None = args.memory
    name: str | None = args.name
    interactive = sys.stdin.isatty() and not (args.new or args.fork or args.memory)

    fork_of: Instance | None = None
    if args.fork:
        source = Path(args.fork).resolve()
    elif interactive:
        if instances:
            action, chosen = _menu(instances)
            if action == "resume":
                if args.setup_only:
                    print(chosen.path)
                    return 0
                _launch(chosen.path, claude_args)
            elif action == "fork":
                fork_of = chosen
                source = chosen.path
        # New or fork: choose the starting memory (a fork inherits its source's,
        # so skip the question there), then name it.
        if source is None:
            memory = _choose_memory_pack() or "none"
        if name is None:
            name = _ask_name(f"{fork_of.label}-fork" if fork_of else "madagents")

    instance = build_instance(
        source=str(source) if source else "madagents",
        dest=None,
        name=name,
        memory=memory,
    )
    if args.setup_only:
        print(instance)
        return 0
    _launch(instance, claude_args)
    return 0
