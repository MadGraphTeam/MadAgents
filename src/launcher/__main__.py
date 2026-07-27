from __future__ import annotations

import signal
import sys

from .errors import LaunchError, die


def _install_signal_handlers() -> None:
    for sig, code in [(signal.SIGINT, 130), (signal.SIGTERM, 143), (signal.SIGHUP, 129)]:
        signal.signal(sig, lambda *_args, c=code: sys.exit(c))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 -m launcher {run,code,setup,cleanup} [args...]", file=sys.stderr)
        return 2
    sub = sys.argv[1]
    argv = sys.argv[2:]
    if sub == "run":
        from .interactive import main as run
    elif sub == "code":
        from .code import main as run
    elif sub == "setup":
        from .setup import main as run
    elif sub == "cleanup":
        from .cleanup import main as run
    else:
        print(f"Unknown subcommand: {sub}", file=sys.stderr)
        return 2
    _install_signal_handlers()
    try:
        return run(argv)
    except LaunchError as e:
        # LaunchError exists to carry a user-facing message + hint. Anything
        # that reaches here uncaught should print those, not a traceback.
        die(e.message, e.hint)


if __name__ == "__main__":
    sys.exit(main())
