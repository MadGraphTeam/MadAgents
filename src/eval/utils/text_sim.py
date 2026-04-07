"""Shared text-similarity helpers for documentation analysis.

Used by both duplicate_detector.py and quality.py to compute
token-level cosine similarity between documentation sections.
"""
from __future__ import annotations

import math
import re
from collections import Counter


# ── Stop words ────────────────────────────────────────────────────────
# These are excluded from tokenization to focus similarity scores on
# domain-meaningful terms rather than common English or MadGraph boilerplate.

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

_STOP_DOMAIN = frozenset({
    # MadGraph-specific terms that appear everywhere and don't
    # discriminate between topics.
    "madgraph", "madgraph5", "mg5_amc", "mg5",
    "set", "launch", "generate", "output", "import", "done",
    "run_card", "param_card", "proc_card", "pythia8_card",
    "model", "process", "events", "command", "script",
    "card", "parameter", "default", "value", "example",
    "directory", "run", "shower", "detector", "analysis",
    "pythia8", "delphes", "madspin", "madwidth",
})

STOP_WORDS = _STOP_ENGLISH | _STOP_DOMAIN


# ── Tokenizer ────────────────────────────────────────────────────────

def tokenize(text: str) -> list[str]:
    """Extract lowercase alphanumeric tokens, filtering stop words.

    Keeps only words starting with a letter that are at least 3 chars
    long and not in the combined stop-word set.
    """
    words = re.findall(r"[a-z][a-z0-9_]+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


# ── Cosine similarity ────────────────────────────────────────────────

def cosine_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Compute cosine similarity between two token lists.

    Uses term-frequency vectors (bag-of-words).  Returns 0.0 if either
    list is empty.
    """
    if not tokens_a or not tokens_b:
        return 0.0
    ca, cb = Counter(tokens_a), Counter(tokens_b)
    terms = set(ca) | set(cb)
    dot = sum(ca.get(t, 0) * cb.get(t, 0) for t in terms)
    ma = math.sqrt(sum(v * v for v in ca.values()))
    mb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (ma * mb) if ma and mb else 0.0
