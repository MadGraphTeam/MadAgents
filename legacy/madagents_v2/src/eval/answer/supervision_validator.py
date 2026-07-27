"""Validation for supervision verdict files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SupervisionValidationResult:
    """Result of validating a supervision verdict file."""
    ok: bool
    verdict: dict | None = None
    errors: list[str] = field(default_factory=list)


def validate_supervision_file(
    path: Path,
    valid_categories: set[str] | None = None,
) -> SupervisionValidationResult:
    """Validate a supervision verdict file.

    Checks:
    1. File exists and contains valid JSON
    2. Top-level value is an object
    3. Has a ``category`` string field
    4. Category is one of the valid categories (if provided)
    """
    if not path.exists():
        return SupervisionValidationResult(
            ok=False,
            errors=["File not found: supervision verdict was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return SupervisionValidationResult(ok=False, errors=["File is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return SupervisionValidationResult(
            ok=False, errors=[f"Invalid JSON: {e}"],
        )

    if not isinstance(data, dict):
        return SupervisionValidationResult(
            ok=False,
            errors=[f"Expected a JSON object, got {type(data).__name__}."],
        )

    category = data.get("category")
    if not isinstance(category, str) or not category.strip():
        return SupervisionValidationResult(
            ok=False, verdict=data,
            errors=["Missing or empty 'category' field."],
        )

    if valid_categories and category not in valid_categories:
        return SupervisionValidationResult(
            ok=False, verdict=data,
            errors=[f"Unknown category '{category}'. Must be one of: {', '.join(sorted(valid_categories))}"],
        )

    return SupervisionValidationResult(ok=True, verdict=data)
