"""Verification phase: extract → triage → verify → remember.

Full pipeline:

1. **Extract** — split answer into individual claims (haiku)
2. **Triage** — match claims against known database (haiku)
3. **Verify** — verify each claim with MadAgents (sonnet)
4. **Remember** — cache newly verified claims for future runs

The claim database is read-only during parallel runs.  Each run stages
its results (count bumps + new claims) to separate files.  Call
:func:`merge_db` after all runs complete to consolidate.

Use :func:`run_verification` for the full pipeline, or individual
functions for fine-grained control.
"""
from eval.session import QuerySession
from eval.verify.extractor import CLAIMS_FILENAME, extract_claims
from eval.verify.verifier import VERDICTS_FILENAME, verify_claims
from eval.verify.triage import TRIAGE_FILENAME, run_triage
from eval.verify.pipeline import run_verification
from eval.verify.claim_db import load_db, merge_db

__all__ = [
    "CLAIMS_FILENAME",
    "QuerySession",
    "TRIAGE_FILENAME",
    "VERDICTS_FILENAME",
    "extract_claims",
    "load_db",
    "merge_db",
    "run_triage",
    "run_verification",
    "verify_claims",
]
