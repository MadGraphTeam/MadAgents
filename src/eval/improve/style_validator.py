"""Deterministic style validation for documentation drafts.

Checks formatting, terminology, and structural rules without LLM calls.

Issues are classified as errors (block the draft) or warnings (advisory
feedback included in revision prompts but do not block acceptance).
"""

import re


def validate_style(draft: dict) -> dict:
    """Check that a doc draft follows documentation style rules.

    Returns:
        dict with:
            passed (bool): No errors found (warnings don't block).
            issues (list[str]): All issues (errors + warnings) for revision feedback.
            errors (list[str]): Hard blockers only.
            warnings (list[str]): Advisory issues only.
    """
    content = draft.get("content", draft.get("new_text", ""))
    if not content:
        return {"passed": True, "issues": [], "errors": [], "warnings": []}

    errors = []
    warnings = []

    lines = content.split("\n")

    # ── 1. Heading hierarchy: no skipped levels (error) ──────────────
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

    # ── 2. **Details ->** link syntax (error) ────────────────────────
    # Broken syntax means cross-reference won't render correctly.
    bad_details = re.findall(r"\*\*Details\s*->\*\*(?!\s*\[)", content)
    if bad_details:
        errors.append(
            "**Details ->** without following markdown link — "
            "use `**Details ->** [text](path)`"
        )

    # ── 3. Terminology consistency (error) ───────────────────────────
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
    """Remove fenced and inline code from text for prose-only checks."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return text


def _check_terms(prose: str, issues: list[str]):
    """Flag common MadGraph terminology inconsistencies in prose."""
    checks = [
        (r"\brun card\b", 'Use "run_card" (underscored) not "run card"'),
        (r"\bparam card\b", 'Use "param_card" (underscored) not "param card"'),
        (r"\bproc card\b", 'Use "proc_card" (underscored) not "proc card"'),
    ]
    for pattern, msg in checks:
        if re.search(pattern, prose, re.IGNORECASE):
            issues.append(msg)

    # "madgraph" all-lowercase outside code → should be "MadGraph"
    if re.search(r"(?<![/A-Za-z])madgraph(?![/A-Za-z5_])", prose):
        issues.append('Use "MadGraph" (capitalized) not "madgraph"')
