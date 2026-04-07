"""Diagnose phase: identify documentation issues from errors.

Examines verification failures and reviewer-caught errors to produce
actionable findings categorized as doc_gap, doc_incorrect, or
doc_ambiguous.
"""
from eval.diagnose.diagnoser import (
    DIAGNOSE_FILENAME,
    DiagnoseState,
    build_diagnose_graph,
    load_categories,
    run_diagnose,
)

__all__ = [
    "DIAGNOSE_FILENAME",
    "DiagnoseState",
    "build_diagnose_graph",
    "load_categories",
    "run_diagnose",
]
