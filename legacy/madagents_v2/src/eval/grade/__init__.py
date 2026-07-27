"""Grading phase: classify overall answer quality.

Assigns a primary grade (CORRECT / INCORRECT) plus zero or more
tags (has_mistakes, inefficient).  Configuration is defined in
``prompts/categories.json``.
"""
from eval.grade.grader import (
    GRADE_FILENAME,
    GradeState,
    build_grade_graph,
    is_improved,
    load_grade_config,
    needs_improvement,
    run_grading,
)

__all__ = [
    "GRADE_FILENAME",
    "GradeState",
    "build_grade_graph",
    "is_improved",
    "load_grade_config",
    "needs_improvement",
    "run_grading",
]
