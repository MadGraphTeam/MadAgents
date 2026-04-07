"""Validation for diagnose output files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_FINDING_KEYS = {"problem", "correct_info", "recommendation"}


@dataclass
class DiagnoseValidationResult:
    """Result of validating a diagnose output file."""
    ok: bool
    diagnoses: dict | None = None
    errors: list[str] = field(default_factory=list)


def validate_diagnose_file(
    path: Path,
    *,
    valid_categories: set[str] | None = None,
) -> DiagnoseValidationResult:
    """Validate a diagnose output file.

    Checks:
    1. File exists and contains valid JSON
    2. Top-level value is an object
    3. All expected category keys are present
    4. Each category contains a list
    5. Each finding has ``problem``, ``correct_info``, ``recommendation``
    """
    if not path.exists():
        return DiagnoseValidationResult(
            ok=False,
            errors=["File not found: diagnose output was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return DiagnoseValidationResult(ok=False, errors=["File is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return DiagnoseValidationResult(ok=False, errors=[f"Invalid JSON: {e}"])

    if not isinstance(data, dict):
        return DiagnoseValidationResult(
            ok=False,
            errors=[f"Expected a JSON object, got {type(data).__name__}."],
        )

    errors: list[str] = []

    # Check category keys are present.
    if valid_categories:
        missing = valid_categories - set(data.keys())
        if missing:
            errors.append(f"Missing category keys: {', '.join(sorted(missing))}")

    # Validate each category's contents.
    for key, value in data.items():
        if not isinstance(value, list):
            errors.append(f"'{key}' must be a list, got {type(value).__name__}.")
            continue

        for i, finding in enumerate(value):
            if not isinstance(finding, dict):
                errors.append(f"'{key}[{i}]': expected an object.")
                continue

            missing_keys = REQUIRED_FINDING_KEYS - set(finding.keys())
            if missing_keys:
                errors.append(f"'{key}[{i}]': missing keys: {', '.join(sorted(missing_keys))}")
                continue

            for k in REQUIRED_FINDING_KEYS:
                val = finding.get(k, "")
                if not isinstance(val, str) or not val.strip():
                    errors.append(f"'{key}[{i}]': '{k}' must be a non-empty string.")

    if errors:
        return DiagnoseValidationResult(ok=False, diagnoses=data, errors=errors)

    return DiagnoseValidationResult(ok=True, diagnoses=data)
