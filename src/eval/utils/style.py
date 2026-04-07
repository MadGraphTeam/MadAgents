"""Deterministic style validation for documentation drafts."""
from __future__ import annotations

import re


def validate_style(draft: dict) -> dict:
    """Check that a doc draft follows documentation style rules.

    Returns:
        dict with: passed, issues, errors, warnings.
    """
    content = draft.get("content", draft.get("new_text", ""))
    if not content:
        return {"passed": True, "issues": [], "errors": [], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []

    lines = content.split("\n")

    # Heading hierarchy: no skipped levels
    in_code_block = False
    prev_level = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        match = re.match(r"^(#{1,6})\s+", line)
        if match:
            level = len(match.group(1))
            if prev_level and level > prev_level + 1:
                errors.append(
                    f"Line {i}: heading level skips from h{prev_level} to h{level}"
                )
            prev_level = level

    # **Details ->** link syntax
    bad_details = re.findall(r"\*\*Details\s*->\*\*(?!\s*\[)", content)
    if bad_details:
        errors.append(
            "**Details ->** without following markdown link -- "
            "use `**Details ->** [text](path)`"
        )

    # Terminology consistency
    prose = _strip_code(content)
    _check_terms(prose, errors)

    issues = errors + warnings
    return {
        "passed": len(errors) == 0,
        "issues": issues,
        "errors": errors,
        "warnings": warnings,
    }


def _strip_code(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return text


def _check_terms(prose: str, issues: list[str]):
    checks = [
        (r"\brun card\b", 'Use "run_card" (underscored) not "run card"'),
        (r"\bparam card\b", 'Use "param_card" (underscored) not "param card"'),
        (r"\bproc card\b", 'Use "proc_card" (underscored) not "proc card"'),
    ]
    for pattern, msg in checks:
        if re.search(pattern, prose, re.IGNORECASE):
            issues.append(msg)

    if re.search(r"(?<![/A-Za-z])madgraph(?![/A-Za-z5_])", prose):
        issues.append('Use "MadGraph" (capitalized) not "madgraph"')
