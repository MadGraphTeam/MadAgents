"""Image selection, and the environment description that ships beside an image.

Each image type owns a folder under ``image/`` holding three things: the
definition it is built from, the ``.sif`` built from it, and a ``CLAUDE.md``
describing what that build actually installs.

That description belongs to the **image**, not to the agent system. The same
preset runs on a preinstall image (MadGraph under ``/opt/MG5_aMC``, HEPTools
beside it), on a minimal one (MadGraph and ROOT, no HEPTools) and on a clean one
(neither) — and only the image knows which. Keeping the file next to the ``.sif``
is what makes the pairing discoverable without a registry: the launcher reads the
``CLAUDE.md`` sitting beside the image it is about to run.

The description is a *seed*, not a managed file. ``setup.py`` copies it into a new
run once, at creation; from then on it is the session's own file to correct and
extend as it learns where things really are — which matters because the overlay
is writable, so the filesystem a run ends with is not the one the image shipped.
"""
from __future__ import annotations

from pathlib import Path

from .paths import REPO_ROOT, resolve_path

#: Filename of the built image inside an image-type folder.
IMAGE_NAME = "madagents.sif"

#: Where the image-type folders live.
IMAGE_DIR: Path = REPO_ROOT / "image"

#: Filename of the environment description beside an image.
SEED_NAME = "CLAUDE.md"

#: Fallback seed, used when the image has no description beside it — a foreign
#: ``.sif`` shared from another site, or one built before image folders existed.
#: It claims no software: an image we cannot identify gets no assertions made
#: about it, only the two paths the launcher itself guarantees by binding them.
_FALLBACK_SEED = REPO_ROOT / "src" / "launcher" / "default_env.md"

#: Order preferred when no ``APPTAINER_IMAGE`` is set and several types are
#: built. Richest first: a user who built more than one almost always means the
#: fuller stack, and the choice is always overridable by APPTAINER_IMAGE.
_TYPE_PREFERENCE = ("preinstall", "minimal", "clean")


def resolve_image(env_value: str | None) -> Path:
    """Pick the image to run: ``APPTAINER_IMAGE`` if set, else what is built.

    Returns a path that may not exist — the caller reports a missing image with
    its own hint (``ensure_file``). When nothing is built at all, the returned
    path is the preinstall one, so that hint names the file the standard build
    command produces.

    Search order after the env var: the known types richest-first, then any
    other ``image/<name>/madagents.sif``, then the flat ``image/madagents.sif``
    that predates image folders (kept so an existing build keeps working
    without a rebuild).
    """
    explicit = resolve_path(env_value)
    if explicit is not None:
        return explicit

    for type_name in _TYPE_PREFERENCE:
        candidate = IMAGE_DIR / type_name / IMAGE_NAME
        if candidate.is_file():
            return candidate

    if IMAGE_DIR.is_dir():
        for folder in sorted(p for p in IMAGE_DIR.iterdir() if p.is_dir()):
            candidate = folder / IMAGE_NAME
            if candidate.is_file():
                return candidate

    legacy = IMAGE_DIR / IMAGE_NAME
    if legacy.is_file():
        return legacy

    return IMAGE_DIR / _TYPE_PREFERENCE[0] / IMAGE_NAME


def seed_file(image: Path) -> Path | None:
    """The file whose text seeds a new run built on *image*.

    The ``CLAUDE.md`` beside the image when there is one, else the fallback,
    else ``None``. Never raises: a run is better off with a generic description
    than none, and neither case is worth failing a launch over.
    """
    for candidate in (image.parent / SEED_NAME, _FALLBACK_SEED):
        try:
            if candidate.read_text(encoding="utf-8").strip():
                return candidate
        except OSError:
            continue
    return None
