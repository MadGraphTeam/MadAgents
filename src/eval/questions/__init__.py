"""Question I/O: loading, deduplication, and reuse.

This package handles non-generation operations on evaluation questions:

- ``loader`` — Load questions from JSONL files (curated banks, run outputs)
- ``dedup``  — Collect question texts from prior runs for deduplication
- ``reuse``  — Append questions from previous runs into the current run
"""
from eval.questions.loader import load_questions_jsonl
from eval.questions.dedup import load_previous_run_questions
from eval.questions.reuse import reuse_questions

__all__ = [
    "load_questions_jsonl",
    "load_previous_run_questions",
    "reuse_questions",
]
