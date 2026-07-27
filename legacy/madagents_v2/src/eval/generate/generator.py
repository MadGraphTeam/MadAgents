"""Generic question generation harness built on LangGraph.

Provides a generate → validate → retry loop that is agnostic to the
query backend.  The caller provides a :class:`QuerySession`; the
harness sends prompts, validates the output file, and retries with
feedback if the content is invalid.

Graph shape::

    START → generate → validate ─(valid)──→ END
                ↑        │
                └(retry)─┘
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.generate.validator import validate_questions_file
from eval.session import QuerySession


QUESTIONS_FILENAME = "questions.json"
DEFAULT_MAX_RETRIES = 3


# ═══════════════════════════════════════════════════════════════════════
#  Graph state
# ═══════════════════════════════════════════════════════════════════════

class GenerateState(TypedDict, total=False):
    """LangGraph state for the question generation loop."""

    attempt: int                # current attempt (0-based)
    questions: list[dict]       # validated output
    validation_errors: list[str]  # errors from last validation
    done: bool                  # stop flag


# ═══════════════════════════════════════════════════════════════════════
#  Prompt loading
# ═══════════════════════════════════════════════════════════════════════

_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    """Load a prompt template, falling back to the built-in defaults."""
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def _build_initial_prompt(
    num_questions: int,
    dedup_questions: list[str],
    focus: str,
    requirements: str,
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    existing_section = ""
    if dedup_questions:
        existing_list = "\n".join(f"- {q}" for q in dedup_questions)
        existing_section = _load_template(
            "_existing.md", prompts_dir,
        ).replace("{existing_list}", existing_list)
    focus_section = (
        _load_template("_focus.md", prompts_dir).format(focus=focus)
        if focus else ""
    )
    requirements_section = requirements if requirements else ""

    # Use .replace() instead of .format() because the template
    # contains JSON examples with literal curly braces.
    return (
        _load_template("generate.md", prompts_dir)
        .replace("{focus_section}", focus_section)
        .replace("{requirements_section}", requirements_section)
        .replace("{existing_section}", existing_section)
        .replace("{num_questions}", str(num_questions))
        .replace("{output_path}", output_path)
        .strip()
    )


def _build_retry_prompt(
    num_questions: int,
    errors: list[str],
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("retry.md", prompts_dir).format(
        error_list=error_list,
        num_questions=num_questions,
        output_path=output_path,
    ).strip()


# ═══════════════════════════════════════════════════════════════════════
#  Graph builder
# ═══════════════════════════════════════════════════════════════════════

def build_generate_graph(
    session: QuerySession | None = None,
    *,
    num_questions: int = 0,
    output_path: Path | None = None,
    focus: str = "",
    requirements: str = "",
    dedup_questions: list[str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build and compile the question generation graph.

    When *session* is ``None`` (visualization mode), nodes are no-ops.

    Args:
        session: Query interface to the generation agent.
        num_questions: Number of questions to generate.
        output_path: Full path where the agent writes the JSON file.
        focus: Optional topic guidance.
        requirements: Additional requirements.
        dedup_questions: Questions the agent should not duplicate.
        max_retries: Maximum retry attempts.
        prompts_dir: Custom prompts directory.

    Returns:
        Compiled :class:`StateGraph` ready for ``ainvoke()``.
    """
    _dedup = dedup_questions or []
    # Container-side path for prompts; host path for validation.
    _map = getattr(session, "map_path", str) if session else str
    _output_str = _map(output_path) if output_path else ""

    # ── Node: generate ────────────────────────────────────────────────
    async def generate_node(state: GenerateState) -> dict:
        if session is None:
            return {"done": True}

        # Delete output file before each attempt (host path).
        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                num_questions, _dedup, focus, requirements,
                _output_str, prompts_dir=prompts_dir,
            )
        else:
            print(f"  Retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                num_questions, state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    # ── Node: json_validate ──────────────────────────────────────────
    def json_validate_node(state: GenerateState) -> dict:
        if session is None:
            return {"questions": [], "done": True}

        validation = validate_questions_file(
            output_path, expected_count=num_questions,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            print(f"  Generated {len(validation.questions)} questions.")
            return {"questions": validation.questions, "done": True}

        print(f"  Validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Question generation failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    # ── Routing ──────────────────────────────────────────────────────
    def route_after_json_validate(state: GenerateState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    # ── Build graph ──────────────────────────────────────────────────
    graph = StateGraph(GenerateState)
    graph.add_node("generate", generate_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "generate", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


# ═══════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════

async def generate_questions(
    num_questions: int,
    session: QuerySession,
    output_path: Path,
    *,
    focus: str = "",
    requirements: str = "",
    dedup_questions: list[str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> list[dict]:
    """Generate evaluation questions via a query session.

    Sends prompts to the session, validates the output file, and
    retries with feedback if the content is invalid.

    Args:
        num_questions: Number of questions to generate.
        session: Query interface to the generation agent.  The agent's
            system prompt, model, and working directory are internal
            to the session — the harness only sends user prompts.
        output_path: Full path where the agent should write the
            questions JSON file.
        focus: Optional topic guidance injected into the prompt.
        requirements: Additional requirements (e.g. difficulty).
        dedup_questions: Question texts the agent should not duplicate.
        max_retries: Retry attempts after validation failure.
        prompts_dir: Custom prompts directory.  Falls back to built-in
            defaults for any missing file.

    Returns:
        List of question dicts with ``text`` and ``reference_answer``.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    print(f"\nGenerating {num_questions} questions")
    if focus:
        print(f"  Focus: {focus}")

    graph = build_generate_graph(
        session,
        num_questions=num_questions,
        output_path=output_path,
        focus=focus,
        requirements=requirements,
        dedup_questions=dedup_questions,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: GenerateState = {
        "attempt": 0,
        "questions": [],
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("questions", [])
