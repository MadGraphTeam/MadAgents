"""Grading harness: classify overall answer quality.

Takes verification verdicts and classifies the answer as CORRECT,
INCORRECT, or INCONCLUSIVE, plus zero or more tags (has_mistakes,
inefficient).

Graph shape::

    START → grade → json_validate ─(valid)──→ END
              ↑          │
              └──(retry)─┘
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.session import QuerySession
from eval.grade.grade_validator import validate_grade_file


GRADE_FILENAME = "grade.json"
DEFAULT_MAX_RETRIES = 2


class GradeState(TypedDict, total=False):
    attempt: int
    grade: dict
    validation_errors: list[str]
    done: bool


_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def load_grade_config(prompts_dir: Path | None = None) -> dict:
    """Load grade configuration from ``categories.json``.

    Returns a dict with ``grades`` and ``tags`` keys.
    """
    text = _load_template("categories.json", prompts_dir)
    return json.loads(text)


def get_improve_sets(config: dict | None = None) -> tuple[set[str], set[str]]:
    """Return ``(improve_grades, improve_tags)`` from a grade config.

    Each set contains the names where ``improve`` is ``true``.
    """
    cfg = config or load_grade_config()
    improve_grades = {g["name"] for g in cfg["grades"] if g.get("improve", False)}
    improve_tags = {t["name"] for t in cfg["tags"] if t.get("improve", False)}
    return improve_grades, improve_tags


def needs_improvement(grade: dict, config: dict | None = None) -> bool:
    """Check whether a grade result should trigger the improve cycle."""
    improve_grades, improve_tags = get_improve_sets(config)
    if grade.get("grade") in improve_grades:
        return True
    return bool(set(grade.get("tags", [])) & improve_tags)


def is_improved(original: dict, new: dict, config: dict | None = None) -> bool:
    """Check whether *new* grade is strictly better than *original*.

    Returns ``True`` if:
    - The grade no longer needs improvement (e.g. INCORRECT → CORRECT), OR
    - The set of improvement-triggering tags strictly decreased
      (e.g. ``[has_mistakes, inefficient]`` → ``[has_mistakes]``).
    """
    _, improve_tags = get_improve_sets(config)
    if needs_improvement(original, config) and not needs_improvement(new, config):
        return True
    orig_tags = set(original.get("tags", [])) & improve_tags
    new_tags = set(new.get("tags", [])) & improve_tags
    return new_tags < orig_tags  # strict subset


def _format_grades(grades: list[dict]) -> str:
    lines = []
    for g in grades:
        lines.append(f"- **{g['name']}**: {g['description']}")
    return "\n".join(lines)


def _format_tags(tags: list[dict]) -> str:
    lines = []
    for t in tags:
        lines.append(f"- **{t['name']}**: {t['description']}")
    return "\n".join(lines)


def _build_initial_prompt(
    question_text: str,
    verdicts_path: str,
    output_path: str,
    transcript_path: str,
    n_claims: int,
    n_correct: int,
    n_incorrect: int,
    n_inconclusive: int,
    grades_str: str,
    tags_str: str,
    prompts_dir: Path | None = None,
) -> str:
    return (
        _load_template("grade.md", prompts_dir)
        .replace("{question}", question_text)
        .replace("{verdicts_path}", verdicts_path)
        .replace("{output_path}", output_path)
        .replace("{transcript_path}", transcript_path)
        .replace("{n_claims}", str(n_claims))
        .replace("{n_correct}", str(n_correct))
        .replace("{n_incorrect}", str(n_incorrect))
        .replace("{n_inconclusive}", str(n_inconclusive))
        .replace("{grades}", grades_str)
        .replace("{tags}", tags_str)
        .strip()
    )


def _build_retry_prompt(
    errors: list[str],
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("grade_retry.md", prompts_dir).format(
        error_list=error_list,
        output_path=output_path,
    ).strip()


def build_grade_graph(
    session: QuerySession | None = None,
    *,
    question_text: str = "",
    verdicts_path: Path | None = None,
    transcript_path: Path | None = None,
    output_path: Path | None = None,
    n_claims: int = 0,
    n_correct: int = 0,
    n_incorrect: int = 0,
    n_inconclusive: int = 0,
    grade_config: dict | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build the grading graph."""
    _map = getattr(session, "map_path", str) if session else str
    _verdicts_str = _map(verdicts_path) if verdicts_path else ""
    _transcript_str = _map(transcript_path) if transcript_path else ""
    _output_str = _map(output_path) if output_path else ""
    _config = grade_config or load_grade_config(prompts_dir)
    _grades_str = _format_grades(_config["grades"])
    _tags_str = _format_tags(_config["tags"])
    _valid_grades = {g["name"] for g in _config["grades"]}
    _valid_tags = {t["name"] for t in _config["tags"]}

    async def grade_node(state: GradeState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                question_text, _verdicts_str, _output_str,
                _transcript_str,
                n_claims, n_correct, n_incorrect, n_inconclusive,
                _grades_str, _tags_str,
                prompts_dir=prompts_dir,
            )
        else:
            print(f"  Grade retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    def json_validate_node(state: GradeState) -> dict:
        if session is None:
            return {"grade": {}, "done": True}

        validation = validate_grade_file(
            output_path,
            valid_grades=_valid_grades,
            valid_tags=_valid_tags,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            grade_name = validation.grade["grade"]
            tags = validation.grade.get("tags", [])
            tags_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"  Grade: {grade_name}{tags_str}")
            return {"grade": validation.grade, "done": True}

        print(f"  Grade validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Grading failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    def route_after_json_validate(state: GradeState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    graph = StateGraph(GradeState)
    graph.add_node("grade", grade_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "grade")
    graph.add_edge("grade", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "grade", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


async def run_grading(
    question_text: str,
    verdicts: list[dict],
    session: QuerySession,
    verdicts_path: Path,
    output_path: Path,
    *,
    transcript_path: Path | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> dict:
    """Grade an answer based on verification verdicts.

    Args:
        question_text: The original question.
        verdicts: List of verdict dicts from the verify phase.
        session: Query session (haiku).
        verdicts_path: Path to the verdicts file (for the grader to read).
        output_path: Where to write the grade JSON.
        transcript_path: Path to the answer transcript (for efficiency assessment).
        max_retries: Retry attempts.
        prompts_dir: Custom prompts directory.

    Returns:
        Grade dict with ``grade``, ``tags``, and ``explanation``.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    n_claims = len(verdicts)
    n_correct = sum(1 for v in verdicts if v.get("correct") is True)
    n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)
    n_inconclusive = sum(1 for v in verdicts if v.get("correct") is None)

    print(f"\n  Grading answer ({n_correct}/{n_claims} correct)...")

    graph = build_grade_graph(
        session,
        question_text=question_text,
        verdicts_path=verdicts_path,
        transcript_path=transcript_path,
        output_path=output_path,
        n_claims=n_claims,
        n_correct=n_correct,
        n_incorrect=n_incorrect,
        n_inconclusive=n_inconclusive,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: GradeState = {
        "attempt": 0,
        "grade": {},
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("grade", {})
