"""Validation for style/quality check output files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CheckValidationResult:
    ok: bool
    result: dict | None = None
    errors: list[str] = field(default_factory=list)


def validate_check_file(path: Path) -> CheckValidationResult:
    """Validate a style or quality check output file.

    Checks: file exists, valid JSON, has ``passed`` (bool) and
    ``issues`` (list of strings).
    """
    if not path.exists():
        return CheckValidationResult(
            ok=False, errors=["File not found: check result was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return CheckValidationResult(ok=False, errors=["File is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return CheckValidationResult(ok=False, errors=[f"Invalid JSON: {e}"])

    if not isinstance(data, dict):
        return CheckValidationResult(
            ok=False, errors=[f"Expected a JSON object, got {type(data).__name__}."],
        )

    errors: list[str] = []

    passed = data.get("passed")
    if not isinstance(passed, bool):
        errors.append("'passed' must be true or false.")

    issues = data.get("issues")
    if not isinstance(issues, list):
        errors.append("'issues' must be a list.")
    elif not all(isinstance(i, str) for i in issues):
        errors.append("All items in 'issues' must be strings.")

    if errors:
        return CheckValidationResult(ok=False, result=data, errors=errors)

    return CheckValidationResult(ok=True, result=data)
