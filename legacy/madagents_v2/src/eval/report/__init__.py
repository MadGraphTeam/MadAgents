"""Summary report generation for evaluation runs.

Aggregates grades, verification results, and documentation changes
into a Markdown report with category breakdowns and per-question tables.

- ``reporter``  -- report generation, run-to-run comparison
"""
from eval.report.reporter import generate_report, find_previous_run

__all__ = [
    "generate_report",
    "find_previous_run",
]
