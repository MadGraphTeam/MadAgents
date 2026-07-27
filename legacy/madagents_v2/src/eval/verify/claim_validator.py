"""Validation for extracted claim files.

After the LLM writes ``claims.json`` via tool calling, this module
reads the file, validates its structure and content, and returns a
result with human-readable errors suitable for LLM feedback on retry.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ClaimValidationResult:
    """Result of validating a claims file."""
    ok: bool
    claims: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_claims_file(path: Path) -> ClaimValidationResult:
    """Validate a JSON claims file written by the LLM.

    Checks (in order):

    1. File exists
    2. File contains valid JSON
    3. Top-level value is a non-empty list
    4. Each item is a dict with a non-empty ``claim`` string

    Returns:
        :class:`ClaimValidationResult` with ``ok=True`` if all checks
        pass, or ``ok=False`` with errors describing what went wrong.
    """
    if not path.exists():
        return ClaimValidationResult(
            ok=False,
            errors=["File not found: claims.json was not written."],
        )

    raw = path.read_text().strip()
    if not raw:
        return ClaimValidationResult(ok=False, errors=["claims.json is empty."])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return ClaimValidationResult(
            ok=False,
            errors=[f"Invalid JSON in claims.json: {e}"],
        )

    if not isinstance(data, list):
        return ClaimValidationResult(
            ok=False,
            errors=[f"Expected a JSON array, got {type(data).__name__}."],
        )

    if len(data) == 0:
        return ClaimValidationResult(
            ok=False,
            errors=["JSON array is empty (0 claims)."],
        )

    errors: list[str] = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: expected an object, got {type(item).__name__}.")
            continue

        claim = item.get("claim", "").strip() if isinstance(item.get("claim"), str) else ""
        if not claim:
            errors.append(f"Item {i}: missing or empty 'claim' field.")

    if errors:
        return ClaimValidationResult(ok=False, errors=errors)

    return ClaimValidationResult(ok=True, claims=data)
