"""Validation for LLM-generated question files.

After the LLM writes ``questions.json`` via tool calling, this module
reads the file, validates its structure and content, and returns a
result with human-readable errors suitable for LLM feedback on retry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of validating a questions file."""
    ok: bool
    questions: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_questions_file(
    path: Path,
    *,
    expected_count: int = 0,
    require_reference_answer: bool = True,
) -> ValidationResult:
    """Validate a JSON questions file written by the LLM.

    Checks (in order):

    1. File exists
    2. File contains valid JSON
    3. Top-level value is a non-empty list
    4. Each item is a dict with non-empty ``text``
    5. Each item has ``reference_answer`` (if *require_reference_answer*)
    6. Count matches *expected_count* (soft warning)

    Returns:
        :class:`ValidationResult` with ``ok=True`` if all hard checks
        pass, or ``ok=False`` with errors describing what went wrong.
    """
    if not path.exists():
        return ValidationResult(
            ok=False,
            errors=["File not found: questions.json was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return ValidationResult(ok=False, errors=["questions.json is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return ValidationResult(
            ok=False,
            errors=[f"Invalid JSON in questions.json: {e}"],
        )

    if not isinstance(data, list):
        return ValidationResult(
            ok=False,
            errors=[f"Expected a JSON array, got {type(data).__name__}."],
        )

    if len(data) == 0:
        return ValidationResult(
            ok=False,
            errors=["JSON array is empty (0 questions)."],
        )

    # Per-item validation.
    errors: list[str] = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: expected an object, got {type(item).__name__}.")
            continue

        text = item.get("text", "").strip() if isinstance(item.get("text"), str) else ""
        if not text:
            errors.append(f"Item {i}: missing or empty 'text' field.")

        if require_reference_answer:
            ref = item.get("reference_answer", "").strip() if isinstance(item.get("reference_answer"), str) else ""
            if not ref:
                errors.append(
                    f"Item {i}: missing or empty 'reference_answer' field."
                )

    # Count check — soft warning.
    if expected_count > 0 and len(data) != expected_count:
        errors.append(
            f"Expected {expected_count} questions, got {len(data)}."
        )

    if errors:
        return ValidationResult(ok=False, errors=errors)

    return ValidationResult(ok=True, questions=data)
