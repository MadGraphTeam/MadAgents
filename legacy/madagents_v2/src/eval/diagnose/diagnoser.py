"""Diagnose harness: identify documentation issues from errors.

Examines verification failures and reviewer-caught errors to find
documentation gaps, inaccuracies, and ambiguities.

Graph shape::

    START → diagnose → json_validate ─(valid)──→ END
                ↑           │
                └──(retry)──┘
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.session import QuerySession
from eval.diagnose.diagnose_validator import validate_diagnose_file


DIAGNOSE_FILENAME = "diagnoses.json"
DEFAULT_MAX_RETRIES = 2


class DiagnoseState(TypedDict, total=False):
    attempt: int
    diagnoses: dict
    validation_errors: list[str]
    done: bool


_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def load_categories(prompts_dir: Path | None = None) -> list[dict]:
    """Load diagnose categories from ``categories.json``."""
    text = _load_template("categories.json", prompts_dir)
    return json.loads(text)


def _format_categories(categories: list[dict]) -> str:
    lines = []
    for c in categories:
        lines.append(f"- {c['name']}: {c['description']}")
    return "\n".join(lines)


def _format_grade_summary(grade: dict | None) -> str:
    """Format a grade dict as a one-line summary for the diagnose prompt."""
    if not grade:
        return "Not available."
    name = grade.get("grade", "?")
    tags = grade.get("tags", [])
    tags_str = f" [{', '.join(tags)}]" if tags else ""
    explanation = grade.get("explanation", "")
    parts = [f"{name}{tags_str}"]
    if explanation:
        parts.append(explanation)
    return " — ".join(parts)


def _build_initial_prompt(
    question_text: str,
    verdicts_path: str,
    transcript_path: str,
    output_path: str,
    categories_str: str,
    grade_summary: str,
    prompts_dir: Path | None = None,
) -> str:
    return (
        _load_template("diagnose.md", prompts_dir)
        .replace("{question}", question_text)
        .replace("{verdicts_path}", verdicts_path)
        .replace("{transcript_path}", transcript_path)
        .replace("{output_path}", output_path)
        .replace("{categories}", categories_str)
        .replace("{grade_summary}", grade_summary)
        .strip()
    )


def _build_retry_prompt(
    errors: list[str],
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("diagnose_retry.md", prompts_dir).format(
        error_list=error_list,
        output_path=output_path,
    ).strip()


def build_diagnose_graph(
    session: QuerySession | None = None,
    *,
    question_text: str = "",
    verdicts_path: Path | None = None,
    transcript_path: Path | None = None,
    output_path: Path | None = None,
    categories: list[dict] | None = None,
    grade: dict | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build the diagnose graph."""
    _map = getattr(session, "map_path", str) if session else str
    _verdicts_str = _map(verdicts_path) if verdicts_path else ""
    _transcript_str = _map(transcript_path) if transcript_path else ""
    _output_str = _map(output_path) if output_path else ""
    _categories = categories or load_categories(prompts_dir)
    _categories_str = _format_categories(_categories)
    _valid_names = {c["name"] for c in _categories}
    _grade_summary = _format_grade_summary(grade)

    async def diagnose_node(state: DiagnoseState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                question_text, _verdicts_str, _transcript_str,
                _output_str, _categories_str, _grade_summary,
                prompts_dir=prompts_dir,
            )
        else:
            print(f"  Diagnose retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    def json_validate_node(state: DiagnoseState) -> dict:
        if session is None:
            return {"diagnoses": {}, "done": True}

        validation = validate_diagnose_file(
            output_path, valid_categories=_valid_names,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            total = sum(len(v) for v in validation.diagnoses.values())
            print(f"  {total} findings diagnosed.")
            return {"diagnoses": validation.diagnoses, "done": True}

        print(f"  Diagnose validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Diagnosis failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    def route_after_json_validate(state: DiagnoseState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    graph = StateGraph(DiagnoseState)
    graph.add_node("diagnose", diagnose_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "diagnose")
    graph.add_edge("diagnose", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "diagnose", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


async def run_diagnose(
    question_text: str,
    session: QuerySession,
    verdicts_path: Path,
    transcript_path: Path,
    output_path: Path,
    *,
    grade: dict | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> dict:
    """Diagnose documentation issues from errors.

    Args:
        question_text: The original question.
        session: Query session (sonnet, needs file read access).
        verdicts_path: Path to the verdicts file.
        transcript_path: Path to the answer transcript.
        output_path: Where to write the diagnoses JSON.
        grade: Grade dict with ``grade``, ``tags``, ``explanation``.
        max_retries: Retry attempts.
        prompts_dir: Custom prompts directory.

    Returns:
        Dict with category keys, each containing a list of findings.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    print(f"\n  Diagnosing documentation issues...")

    graph = build_diagnose_graph(
        session,
        question_text=question_text,
        verdicts_path=verdicts_path,
        transcript_path=transcript_path,
        output_path=output_path,
        grade=grade,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: DiagnoseState = {
        "attempt": 0,
        "diagnoses": {},
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("diagnoses", {})
