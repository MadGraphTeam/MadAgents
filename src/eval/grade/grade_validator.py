"""Validation for grade output files."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GradeValidationResult:
    """Result of validating a grade output file."""
    ok: bool
    grade: dict | None = None
    errors: list[str] = field(default_factory=list)


def validate_grade_file(
    path: Path,
    *,
    valid_grades: set[str] | None = None,
    valid_tags: set[str] | None = None,
) -> GradeValidationResult:
    """Validate a grade output file.

    Checks:
    1. File exists and contains valid JSON
    2. Top-level value is an object
    3. Has ``grade`` (string matching valid_grades)
    4. Has ``tags`` (list of strings, each in valid_tags, no duplicates)
    5. Has ``explanation`` (non-empty string)
    """
    if not path.exists():
        return GradeValidationResult(
            ok=False,
            errors=["File not found: grade was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return GradeValidationResult(ok=False, errors=["File is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return GradeValidationResult(ok=False, errors=[f"Invalid JSON: {e}"])

    if not isinstance(data, dict):
        return GradeValidationResult(
            ok=False,
            errors=[f"Expected a JSON object, got {type(data).__name__}."],
        )

    errors: list[str] = []

    # Validate grade.
    grade = data.get("grade")
    if not isinstance(grade, str) or not grade.strip():
        errors.append("Missing or empty 'grade' field.")
    elif valid_grades and grade not in valid_grades:
        errors.append(
            f"Unknown grade '{grade}'. Must be one of: {', '.join(sorted(valid_grades))}"
        )

    # Validate tags.
    tags = data.get("tags")
    if tags is None:
        errors.append("Missing 'tags' field. Must be a list of strings (can be empty).")
    elif not isinstance(tags, list):
        errors.append(f"'tags' must be a list, got {type(tags).__name__}.")
    else:
        seen = set()
        for i, tag in enumerate(tags):
            if not isinstance(tag, str):
                errors.append(f"tags[{i}]: expected a string, got {type(tag).__name__}.")
            elif valid_tags and tag not in valid_tags:
                errors.append(
                    f"Unknown tag '{tag}'. Must be one of: {', '.join(sorted(valid_tags))}"
                )
            elif tag in seen:
                errors.append(f"Duplicate tag: '{tag}'.")
            else:
                seen.add(tag)

    # Validate explanation.
    explanation = data.get("explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        errors.append("Missing or empty 'explanation' field.")

    if errors:
        return GradeValidationResult(ok=False, grade=data, errors=errors)

    return GradeValidationResult(ok=True, grade=data)
