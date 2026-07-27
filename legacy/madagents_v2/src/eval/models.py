"""Dataclasses and loaders for eval harnesses.

Provides the core data types used across evaluation phases —
questions, grades, verification results, trace metrics — plus
loaders for reading them from JSON/JSONL files.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════
#  Dataclasses
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class QuestionEntry:
    id: str
    text: str
    source: str         # where this question came from
    added_in_run: str   # timestamp of run when added
    reference_answer: str = ""


@dataclass
class TraceMetrics:
    total_turns: int = 0
    duration_ms: int = 0
    subagents_dispatched: list = field(default_factory=list)
    web_searches: list = field(default_factory=list)
    docs_read: list = field(default_factory=list)
    bash_errors: list = field(default_factory=list)
    tools_used: list = field(default_factory=list)
    clarifying_questions: list = field(default_factory=list)


@dataclass
class GradeResult:
    question_id: str
    category: str           # one of CATEGORIES
    confidence: float
    explanation: str
    doc_file_affected: str
    suggested_fix: str
    trace_metrics: TraceMetrics
    prompt_suggested_fix: str = ""


@dataclass
class VerificationClaim:
    description: str
    method: str | None = "execution"   # execution | inspection | physics_reasoning | web | None
    passed: bool | None = None         # True/False/None (inconclusive)
    evidence: list = field(default_factory=list)
    explanation: str = ""


@dataclass
class VerificationResult:
    question_id: str
    claims: list = field(default_factory=list)
    agent_verified: bool | None = None  # None = no testable claims
    summary: str = ""


# ═══════════════════════════════════════════════════════════════════════
#  Loaders
# ═══════════════════════════════════════════════════════════════════════

def load_questions(path: Path) -> list[QuestionEntry]:
    """Load questions from a JSONL file."""
    valid_fields = {f.name for f in QuestionEntry.__dataclass_fields__.values()}
    questions = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        questions.append(QuestionEntry(**filtered))
    return questions


def load_grades(run_dir: Path) -> list[GradeResult]:
    """Load all grading results from a run directory."""
    grades = []
    for grade_file in sorted(run_dir.glob("questions/*/grade.json")):
        data = json.loads(grade_file.read_text())
        tm_data = data.pop("trace_metrics", {})
        trace_metrics = TraceMetrics(**tm_data)
        grades.append(GradeResult(trace_metrics=trace_metrics, **data))
    return grades


def load_verification(q_dir: Path, suffix: str = "") -> VerificationResult | None:
    """Load a VerificationResult from a question directory.

    Args:
        suffix: File suffix, e.g. "_reeval". Loads ``verification{suffix}.json``.
    """
    vpath = q_dir / f"verification{suffix}.json"
    if not vpath.exists():
        return None
    data = json.loads(vpath.read_text())
    raw_claims = data.pop("claims", None) or data.pop("agent_steps", [])
    claims = []
    for s in raw_claims:
        if isinstance(s, dict):
            valid_claim_fields = {f.name for f in VerificationClaim.__dataclass_fields__.values()}
            filtered_claim = {k: v for k, v in s.items() if k in valid_claim_fields}
            claims.append(VerificationClaim(**filtered_claim))
        else:
            claims.append(s)
    valid_fields = {f.name for f in VerificationResult.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return VerificationResult(claims=claims, **filtered)


def extract_json_object(text: str, required_key: str) -> dict | None:
    """Extract the first JSON object from text that contains the required key.

    Handles markdown fences and surrounding prose.
    """
    clean = text
    if "```" in clean:
        lines = clean.split("\n")
        clean = "\n".join(l for l in lines if not l.strip().startswith("```"))

    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(clean):
        start = clean.find("{", idx)
        if start == -1:
            break
        try:
            candidate, end_idx = decoder.raw_decode(clean, start)
            if isinstance(candidate, dict) and required_key in candidate:
                return candidate
        except json.JSONDecodeError:
            pass
        idx = start + 1
    return None
