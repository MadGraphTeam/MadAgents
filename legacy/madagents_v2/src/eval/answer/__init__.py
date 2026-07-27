"""Answer phase: generic answer → supervise harness.

Provides a LangGraph-based loop that sends a question to any query
backend, classifies the response via a supervisor session, and
optionally sends follow-up instructions.  Agnostic to the agent being
tested (MadAgents, vanilla Claude Code, direct API, etc.).

- ``answerer``  -- graph builder, data types, template loading
"""
from eval.answer.answerer import (
    AnswerResult,
    AnswerState,
    AnswerTurn,
    GradeCategory,
    build_answer_graph,
    load_categories,
    run_answer_loop,
)
from eval.session import QuerySession

__all__ = [
    "AnswerResult",
    "AnswerState",
    "AnswerTurn",
    "GradeCategory",
    "QuerySession",
    "build_answer_graph",
    "load_categories",
    "run_answer_loop",
]
