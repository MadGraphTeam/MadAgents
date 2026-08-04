"""The local menu — ``./local/madrun.sh``, the sibling of ``./madrun.sh``.

Delegates to :mod:`launcher.interactive` so there is exactly one menu in the
repo: the run listing, resume/fork, the memory question and the naming are all
the same code, and a fix to any of them lands on both paths at once. Instances
live in the same ``run_dir/instances/`` either way, so ``--list`` shows your
runs, not half of them; the ``BACKEND`` column is what tells them apart.

What this module adds is only what is specific to running against your own
endpoint:

1. **Refusing to start without one.** The check lives here rather than in
   ``code.py`` so it fires before the menu rather than after you have answered
   its questions. Listing is exempt — showing which runs exist needs no model.
2. **Saying which endpoint a new run will use**, redacted, as a banner.

``launcher.interactive`` takes both as parameters and knows nothing about this
folder, preserving the one-directional dependency the package docstring
describes.
"""
from __future__ import annotations

from launcher import interactive
from launcher.errors import die
from launcher.settings import load_config_env
from launcher.setup import LOCAL_BACKEND

from .config import CONFIG_ENV, endpoint_env, load_local_config, redacted_summary

#: Arguments that only read state, and so need no endpoint to be configured.
_LISTING_FLAGS = ("--list", "--list-memory", "-h", "--help")


def main(argv: list[str] | None = None) -> int:
    load_config_env()
    load_local_config()

    args = argv if argv is not None else []
    if not any(a in _LISTING_FLAGS for a in args) and not endpoint_env():
        die(
            "no local endpoint configured",
            hint=f"Set LOCAL_MODEL_BASE_URL in {CONFIG_ENV}. Copy "
                 f"{CONFIG_ENV.name}.example to start. To run against the hosted API "
                 f"instead, use ./madrun.sh in the repo root.",
        )

    return interactive.main(
        argv,
        backend=LOCAL_BACKEND,
        banner=f"\nmadrun-local: endpoint {redacted_summary()}",
    )
