"""Validation for claim verification verdict files.

After the verifier agent writes ``verdicts.json``, this module reads
the file, validates its structure, and returns a result with
human-readable errors suitable for LLM feedback on retry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


VALID_METHODS = {"execution", "inspection", "source_inspection", "physics_reasoning"}


@dataclass
class VerdictValidationResult:
    """Result of validating a verdicts file."""
    ok: bool
    verdicts: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_verdicts_file(
    path: Path,
    *,
    expected_count: int = 0,
) -> VerdictValidationResult:
    """Validate a JSON verdicts file written by the verifier.

    Checks (in order):

    1. File exists and contains valid JSON
    2. Top-level value is a non-empty list
    3. Each item has required keys: ``claim``, ``correct``, ``method``,
       ``evidence``, ``explanation``
    4. ``correct`` is bool or None
    5. ``evidence`` is a list of strings
    6. ``method`` is a valid string or None (only when ``correct`` is None)
    7. ``explanation`` is a non-empty string
    8. Count matches expected (soft warning)

    Returns:
        :class:`VerdictValidationResult` with ``ok=True`` if all hard
        checks pass, or ``ok=False`` with errors.
    """
    if not path.exists():
        return VerdictValidationResult(
            ok=False,
            errors=["File not found: verdicts.json was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return VerdictValidationResult(ok=False, errors=["verdicts.json is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return VerdictValidationResult(
            ok=False,
            errors=[f"Invalid JSON in verdicts.json: {e}"],
        )

    if not isinstance(data, list):
        return VerdictValidationResult(
            ok=False,
            errors=[f"Expected a JSON array, got {type(data).__name__}."],
        )

    if len(data) == 0:
        return VerdictValidationResult(
            ok=False,
            errors=["JSON array is empty (0 verdicts)."],
        )

    errors: list[str] = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: expected an object, got {type(item).__name__}.")
            continue

        claim = item.get("claim", "")
        label = f"Item {i} ('{claim[:40]}...')" if claim else f"Item {i}"

        # Required string fields.
        if not isinstance(claim, str) or not claim.strip():
            errors.append(f"{label}: missing or empty 'claim'.")

        explanation = item.get("explanation", "")
        if not isinstance(explanation, str) or not explanation.strip():
            errors.append(f"{label}: missing or empty 'explanation'.")

        # correct: bool or None.
        correct = item.get("correct")
        if correct is not None and not isinstance(correct, bool):
            errors.append(
                f"{label}: 'correct' must be true, false, or null — "
                f"got {type(correct).__name__}: {correct!r}"
            )

        # evidence: list of strings.
        evidence = item.get("evidence")
        if evidence is None:
            errors.append(f"{label}: missing 'evidence'.")
        elif not isinstance(evidence, list):
            errors.append(
                f"{label}: 'evidence' must be a list — "
                f"got {type(evidence).__name__}."
            )
        elif not all(isinstance(e, str) for e in evidence):
            errors.append(f"{label}: all 'evidence' items must be strings.")

        # method: valid string or None (only when correct is None).
        method = item.get("method")
        if correct is None:
            if method is not None:
                errors.append(
                    f"{label}: 'method' must be null when 'correct' is null."
                )
        else:
            if method is None:
                errors.append(
                    f"{label}: 'method' must not be null when 'correct' is {correct}."
                )
            elif method not in VALID_METHODS:
                errors.append(
                    f"{label}: invalid method '{method}'. "
                    f"Must be one of: {', '.join(sorted(VALID_METHODS))}."
                )

    # Count check — soft warning.
    if expected_count > 0 and len(data) != expected_count:
        errors.append(
            f"Expected {expected_count} verdicts, got {len(data)}."
        )

    if errors:
        return VerdictValidationResult(ok=False, verdicts=data, errors=errors)

    return VerdictValidationResult(ok=True, verdicts=data)
