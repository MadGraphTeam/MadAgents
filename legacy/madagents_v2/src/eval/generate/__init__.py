"""LLM-based question generation for eval harnesses.

Provides a LangGraph-based prompt → validate → retry loop that is
agnostic to the query backend.  The caller provides a ``QuerySession``;
the harness sends prompts, validates the output file, and retries
with feedback.

- ``generator``  — graph builder, prompt building, validation/retry loop
- ``validator``  — file and content validation
"""
from eval.generate.generator import (
    QUESTIONS_FILENAME,
    GenerateState,
    build_generate_graph,
    generate_questions,
)
from eval.generate.validator import ValidationResult, validate_questions_file
from eval.session import QuerySession

__all__ = [
    "QUESTIONS_FILENAME",
    "GenerateState",
    "QuerySession",
    "ValidationResult",
    "build_generate_graph",
    "generate_questions",
    "validate_questions_file",
]
