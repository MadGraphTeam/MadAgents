"""Validation for triage output files (flat list of database IDs)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TriageValidationResult:
    """Result of validating a triage output file."""
    ok: bool
    ids: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_triage_file(
    path: Path,
    *,
    valid_ids: set[int] | None = None,
) -> TriageValidationResult:
    """Validate a triage output file.

    Checks:
    1. File exists and contains valid JSON
    2. Top-level value is a list
    3. All items are integers
    4. All IDs exist in the database (if valid_ids provided)
    """
    if not path.exists():
        return TriageValidationResult(
            ok=False,
            errors=["File not found: triage output was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return TriageValidationResult(ok=False, errors=["Triage file is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return TriageValidationResult(
            ok=False, errors=[f"Invalid JSON: {e}"],
        )

    if not isinstance(data, list):
        return TriageValidationResult(
            ok=False,
            errors=[f"Expected a JSON array, got {type(data).__name__}."],
        )

    # Empty list is valid — no relevant claims found.
    if len(data) == 0:
        return TriageValidationResult(ok=True, ids=[])

    errors: list[str] = []
    valid: list[int] = []

    non_ints = [x for x in data if not isinstance(x, int)]
    if non_ints:
        errors.append(f"Array contains non-integer values: {non_ints[:5]}")
        return TriageValidationResult(ok=False, errors=errors)

    if valid_ids is not None:
        unknown = [x for x in data if x not in valid_ids]
        if unknown:
            errors.append(f"Unknown database IDs: {unknown}")
            return TriageValidationResult(ok=False, errors=errors)

    return TriageValidationResult(ok=True, ids=data)
