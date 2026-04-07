"""Validation for remember output files (flat list of verdict indices)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RememberValidationResult:
    """Result of validating a remember output file."""
    ok: bool
    indices: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_remember_file(
    path: Path,
    *,
    max_index: int | None = None,
) -> RememberValidationResult:
    """Validate a remember output file.

    Checks:
    1. File exists and contains valid JSON
    2. Top-level value is a list
    3. All items are integers
    4. All indices are within range (if max_index provided)
    """
    if not path.exists():
        return RememberValidationResult(
            ok=False,
            errors=["File not found: remember output was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return RememberValidationResult(ok=False, errors=["File is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return RememberValidationResult(
            ok=False, errors=[f"Invalid JSON: {e}"],
        )

    if not isinstance(data, list):
        return RememberValidationResult(
            ok=False,
            errors=[f"Expected a JSON array, got {type(data).__name__}."],
        )

    # Empty list is valid — nothing new to remember.
    if len(data) == 0:
        return RememberValidationResult(ok=True, indices=[])

    non_ints = [x for x in data if not isinstance(x, int)]
    if non_ints:
        return RememberValidationResult(
            ok=False,
            errors=[f"Array contains non-integer values: {non_ints[:5]}"],
        )

    if max_index is not None:
        out_of_range = [x for x in data if x < 0 or x > max_index]
        if out_of_range:
            return RememberValidationResult(
                ok=False,
                errors=[f"Indices out of range (0-{max_index}): {out_of_range}"],
            )

    return RememberValidationResult(ok=True, indices=data)
