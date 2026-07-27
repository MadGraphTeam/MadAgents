from __future__ import annotations

import sys
from typing import Optional


class LaunchError(Exception):
    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.hint = hint


def die(message: str, hint: Optional[str] = None, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if hint:
        print(f"       {hint}", file=sys.stderr)
    sys.exit(code)
