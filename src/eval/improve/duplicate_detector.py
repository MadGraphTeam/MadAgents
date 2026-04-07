"""Detect content overlap between new doc additions and existing docs.

Uses bag-of-words cosine similarity to flag sections where the proposed
content substantially duplicates what already exists, so the draft can
cross-reference instead.

Issues are classified as errors (hard blockers) or warnings (advisory
feedback for revisions). Topical overlap in MadGraph documentation is
expected — only near-copy duplication blocks a draft.
"""

import math
import re
from collections import Counter
from pathlib import Path

from eval.config import DOCS_DIR

# Similarity thresholds:
#   >= ERROR_THRESHOLD  → near-copy, hard blocker (must deduplicate)
#   >= WARN_THRESHOLD   → topical overlap, advisory (suggest cross-ref)
#   < WARN_THRESHOLD    → fine, no issue
ERROR_THRESHOLD = 0.85
WARN_THRESHOLD = 0.50
MIN_CONTENT_LENGTH = 100

# Common English stop words
_STOP_ENGLISH = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "and", "but", "or", "not", "no", "if", "then",
    "than", "that", "this", "these", "those", "it", "its", "they", "them",
    "their", "we", "our", "you", "your", "which", "who", "what", "when",
    "where", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "also", "very", "just", "about",
    "use", "using", "used", "see", "file",
})

# MadGraph domain terms that appear across most doc sections.
# Without filtering these, any two sections discussing MG5 scripting
# would have high cosine similarity purely from shared vocabulary.
_STOP_DOMAIN = frozenset({
    "madgraph", "madgraph5", "mg5_amc", "mg5",
    "set", "launch", "generate", "output", "import", "done",
    "run_card", "param_card", "proc_card", "pythia8_card",
    "model", "process", "events", "command", "script",
    "card", "parameter", "default", "value", "example",
    "directory", "run", "shower", "detector", "analysis",
    "pythia8", "delphes", "madspin", "madwidth",
})

_STOP = _STOP_ENGLISH | _STOP_DOMAIN


def check_duplicates(draft: dict) -> dict:
    """Check if draft content duplicates existing documentation.

    Returns:
        dict with:
            passed (bool): No errors found (warnings don't block).
            overlaps (list[dict]): Sections with notable similarity.
            issues (list[str]): All issues (errors + warnings) for revision feedback.
            errors (list[str]): Hard blockers only.
            warnings (list[str]): Advisory issues only.
    """
    content = draft.get("content", draft.get("new_text", ""))
    if not content or len(content) < MIN_CONTENT_LENGTH:
        return {"passed": True, "overlaps": [], "issues": [],
                "errors": [], "warnings": []}

    new_tokens = _tokenize(content)
    if len(new_tokens) < 10:
        return {"passed": True, "overlaps": [], "issues": [],
                "errors": [], "warnings": []}

    target_file = draft.get("file_path", "")

    # Detect cross-references in the draft content (markdown links)
    cross_ref_targets = set()
    for match in re.finditer(r"\]\(([^)]+)\)", content):
        link = match.group(1).lstrip("./").lstrip("../")
        cross_ref_targets.add(link)
        # Also add without detailed/ prefix
        if link.startswith("detailed/"):
            cross_ref_targets.add(link[len("detailed/"):])
        # And with detailed/ prefix
        cross_ref_targets.add("detailed/" + link)

    # Collect all existing doc files
    all_files = list(DOCS_DIR.glob("*.md"))
    detailed_dir = DOCS_DIR / "detailed"
    if detailed_dir.exists():
        all_files.extend(detailed_dir.glob("*.md"))

    overlaps = []
    for doc_file in all_files:
        # Skip the file being modified (for extend/correct)
        rel = str(doc_file.relative_to(DOCS_DIR))
        if rel == target_file:
            continue

        for section in _split_sections(doc_file):
            section_tokens = _tokenize(section["content"])
            if len(section_tokens) < 10:
                continue
            sim = _cosine(new_tokens, section_tokens)
            if sim >= WARN_THRESHOLD:
                # Check if the draft cross-references this file
                has_xref = (
                    rel in cross_ref_targets
                    or doc_file.name in cross_ref_targets
                )
                overlaps.append({
                    "file": rel,
                    "section": section["heading"],
                    "similarity": round(sim, 3),
                    "has_cross_ref": has_xref,
                })

    overlaps.sort(key=lambda x: x["similarity"], reverse=True)

    errors = []
    warnings = []
    for ov in overlaps:
        sim = ov["similarity"]
        loc = f"{ov['file']} :: {ov['section']}"
        if sim >= ERROR_THRESHOLD and not ov["has_cross_ref"]:
            errors.append(
                f"Near-copy ({sim:.0%}) of {loc} — "
                f"deduplicate or add a cross-reference"
            )
        elif sim >= ERROR_THRESHOLD and ov["has_cross_ref"]:
            # Cross-referenced near-copy: downgrade to warning
            warnings.append(
                f"High overlap ({sim:.0%}) with {loc} "
                f"(cross-reference present — consider reducing duplication)"
            )
        elif not ov["has_cross_ref"]:
            warnings.append(
                f"Content overlaps ({sim:.0%}) with {loc} — "
                f"consider adding a cross-reference"
            )
        # If < ERROR_THRESHOLD and has cross-ref: no issue at all

    issues = errors + warnings
    return {
        "passed": len(errors) == 0,
        "overlaps": overlaps,
        "issues": issues,
        "errors": errors,
        "warnings": warnings,
    }


# ── Helpers ───────────────────────────────────────────────────────────


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer with stop-word removal."""
    words = re.findall(r"[a-z][a-z0-9_]+", text.lower())
    return [w for w in words if w not in _STOP and len(w) > 2]


def _cosine(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Cosine similarity between two token lists."""
    if not tokens_a or not tokens_b:
        return 0.0
    ca, cb = Counter(tokens_a), Counter(tokens_b)
    terms = set(ca) | set(cb)
    dot = sum(ca.get(t, 0) * cb.get(t, 0) for t in terms)
    ma = math.sqrt(sum(v * v for v in ca.values()))
    mb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (ma * mb) if ma and mb else 0.0


def _split_sections(filepath: Path) -> list[dict]:
    """Split a markdown file into sections by headings."""
    if not filepath.exists():
        return []
    content = filepath.read_text()
    sections = []
    heading = ""
    buf: list[str] = []
    for line in content.split("\n"):
        if line.startswith("#"):
            if buf:
                sections.append({"heading": heading, "content": "\n".join(buf)})
            heading = line.lstrip("# ").strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections.append({"heading": heading, "content": "\n".join(buf)})
    return sections
