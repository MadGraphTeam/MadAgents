"""Generic answer supervision harness built on LangGraph.

Provides a configurable answer → supervise loop that is agnostic to
the query backend (MadAgents, vanilla Claude Code, direct API, etc.).

The caller provides:

- A :class:`QuerySession` for the agent under test — any object with an
  ``ask(prompt)`` method.  The harness calls it repeatedly for
  follow-ups; the session maintains conversation context internally.
- A second :class:`QuerySession` for the supervisor — a stateful supervisor
  that classifies the agent's response and generates follow-up
  instructions.  Writes verdicts to numbered files
  (``supervision_0.json``, ``supervision_1.json``, etc.).

All prompts and categories are loaded from Markdown / JSON templates in
``prompts/`` and can be overridden via *prompts_dir*.

Graph shape::

    START → answer → supervise ─(done)──────→ END
              ↑         │
              └(follow_up)┘
"""
from __future__ import annotations

import json
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.answer.supervision_validator import validate_supervision_file
from eval.session import QuerySession


# ═══════════════════════════════════════════════════════════════════════
#  Data types
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class GradeCategory:
    """A single supervision category for the answer loop.

    Attributes:
        name: Category identifier (e.g. ``"COMPLETE"``).
        description: Explanation fed to the supervision LLM.
        action: ``"done"`` (return result) or ``"continue"`` (send
            follow-up and re-ask).
        follow_up_guidance: Guidance for the supervisor on what kind of
            follow-up to produce when the category is ``"continue"``.
            The supervisor uses this to write a specific, tailored
            follow-up instruction.
    """

    name: str
    description: str
    action: str  # "done" or "continue"
    follow_up_guidance: str = ""


@dataclass
class AnswerTurn:
    """A single turn in the answer loop."""

    user_prompt: str
    response: str
    category: str


@dataclass
class AnswerResult:
    """Final result of the answer supervision loop."""

    final_response: str
    final_category: str
    turns: list[AnswerTurn] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
#  Graph state
# ═══════════════════════════════════════════════════════════════════════

class AnswerState(TypedDict, total=False):
    """LangGraph state for the answer supervision loop."""

    question_text: str          # immutable — the original question
    user_prompt: str            # current prompt to send
    response: str               # latest response from agent
    category_name: str          # latest grade category
    turns: Annotated[list, operator.add]  # accumulated turn dicts
    turn_idx: int               # current turn number


# ═══════════════════════════════════════════════════════════════════════
#  Prompt / category loading
# ═══════════════════════════════════════════════════════════════════════

_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

_DEFAULT_FOLLOW_UP = "Please try again and provide a more complete answer."


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    """Load a prompt template, falling back to the built-in defaults."""
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def load_categories(prompts_dir: Path | None = None) -> list[GradeCategory]:
    """Load grade categories from ``categories.json``."""
    text = _load_template("categories.json", prompts_dir)
    return [GradeCategory(**entry) for entry in json.loads(text)]


def _format_categories_for_prompt(categories: list[GradeCategory]) -> str:
    """Format categories as a bulleted list for the supervision prompt."""
    lines = []
    for c in categories:
        line = f"- {c.name}: {c.description}"
        if c.follow_up_guidance:
            line += f" (follow-up guidance: {c.follow_up_guidance})"
        if c.action == "continue":
            line += " [action: continue]"
        lines.append(line)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Graph builder
# ═══════════════════════════════════════════════════════════════════════

def build_answer_graph(
    session: QuerySession | None = None,
    supervisor: QuerySession | None = None,
    *,
    categories: list[GradeCategory] | None = None,
    supervision_template: str = "",
    supervision_followup_template: str = "",
    categories_str: str = "",
    max_turns: int = 3,
    output_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build and compile the answer supervision graph.

    When *session* and *supervisor* are ``None`` (visualization mode),
    nodes are no-ops that pass through state unchanged.

    Args:
        session: Query interface to the agent under test.
        supervisor: Stateful supervision session.  The supervisor writes
            verdicts to ``output_dir/supervision_N.json`` files.
        categories: Grade categories (needed for action lookup).
        supervision_template: User prompt template for the first turn.
        supervision_followup_template: Shorter template for follow-up
            turns (supervisor already has context from turn 0).
        categories_str: Pre-formatted category list for the prompt.
        max_turns: Maximum conversation turns.
        output_dir: Directory for supervision verdict files.

    Returns:
        Compiled :class:`StateGraph` ready for ``ainvoke()``.
    """
    category_lookup = {c.name: c for c in categories} if categories else {}
    valid_category_names = set(category_lookup.keys()) if category_lookup else None

    # ── Node: answer ──────────────────────────────────────────────────
    async def answer_node(state: AnswerState) -> dict:
        if session is None:
            return {}
        response = await session.ask(state["user_prompt"])
        return {"response": response}

    # Path mapper for container-aware prompt paths.
    _map = getattr(supervisor, "map_path", str) if supervisor else str

    # ── Node: supervise ───────────────────────────────────────────────
    async def supervise_node(state: AnswerState) -> dict:
        if supervisor is None:
            return {"category_name": "COMPLETE", "turns": [], "turn_idx": 1}

        turn_idx = state.get("turn_idx", 0)

        # Build output path for this turn's verdict.
        verdict_path = output_dir / f"supervision_{turn_idx}.json" if output_dir else None
        output_path_str = _map(verdict_path) if verdict_path else ""

        # Delete previous file if it exists (retry safety).
        if verdict_path and verdict_path.exists():
            verdict_path.unlink()

        template = supervision_template if turn_idx == 0 else supervision_followup_template
        prompt = template.replace(
            "{question}", state["question_text"],
        ).replace(
            "{response}", state["response"],
        ).replace(
            "{categories}", categories_str,
        ).replace(
            "{output_path}", output_path_str,
        ).strip()

        await supervisor.ask(prompt)

        # Read and validate the verdict file, retrying on failure.
        category_name = None
        follow_up = ""
        max_supervision_retries = 2

        if verdict_path:
            for attempt in range(1 + max_supervision_retries):
                validation = validate_supervision_file(
                    verdict_path, valid_categories=valid_category_names,
                )
                if validation.ok and validation.verdict:
                    category_name = validation.verdict["category"]
                    follow_up = validation.verdict.get("follow_up", "")
                    break

                errors = "; ".join(validation.errors) if validation.errors else "unknown"
                if attempt < max_supervision_retries:
                    print(f"  Supervision verdict invalid ({errors}), retrying ({attempt + 1}/{max_supervision_retries})...")
                    if verdict_path.exists():
                        verdict_path.unlink()
                    retry_prompt = (
                        f"Your supervision verdict was invalid: {errors}. "
                        f"Please write a corrected JSON verdict to `{output_path_str}`."
                    )
                    await supervisor.ask(retry_prompt)
                else:
                    raise RuntimeError(
                        f"Supervision verdict invalid after {max_supervision_retries} retries: {errors}"
                    )

        turn = {
            "user_prompt": state["user_prompt"],
            "response": state["response"],
            "category": category_name,
        }
        result: dict = {
            "category_name": category_name,
            "turns": [turn],
            "turn_idx": turn_idx + 1,
        }

        # If continuing, use the supervisor's tailored follow-up.
        cat = category_lookup.get(category_name)
        if cat and cat.action == "continue":
            result["user_prompt"] = follow_up or _DEFAULT_FOLLOW_UP

        return result

    # ── Routing ──────────────────────────────────────────────────────
    def route_after_supervise(state: AnswerState) -> str:
        cat = category_lookup.get(state.get("category_name", ""))
        if cat is None or cat.action == "done":
            return "done"
        if state.get("turn_idx", 0) >= max_turns:
            return "done"
        return "follow_up"

    # ── Build graph ──────────────────────────────────────────────────
    graph = StateGraph(AnswerState)
    graph.add_node("answer", answer_node)
    graph.add_node("supervise", supervise_node)

    graph.add_edge(START, "answer")
    graph.add_edge("answer", "supervise")
    graph.add_conditional_edges(
        "supervise", route_after_supervise,
        {"follow_up": "answer", "done": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * max_turns + 5},
    )


# ═══════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════

async def run_answer_loop(
    question_text: str,
    session: QuerySession,
    supervisor: QuerySession,
    *,
    output_dir: str | Path | None = None,
    prompts_dir: str | Path | None = None,
    categories: list[GradeCategory] | None = None,
    max_turns: int = 3,
) -> AnswerResult:
    """Run the answer → supervise loop.

    Args:
        question_text: The question to send to the agent.
        session: Query interface to the agent under test (MadAgents,
            vanilla Claude, etc.).  The agent's system prompt and
            configuration are internal to the session — the harness
            only sends user prompts.
        supervisor: Stateful supervision session that classifies responses
            and generates follow-up instructions.  Writes verdicts to
            ``output_dir/supervision_N.json``.
        output_dir: Directory for supervision verdict files.
        prompts_dir: Custom prompts directory.  Falls back to built-in
            defaults for any missing file.
        categories: Grade categories.  If ``None``, loads from
            ``categories.json`` in *prompts_dir*.
        max_turns: Maximum conversation turns before returning.

    Returns:
        :class:`AnswerResult` with the final response, grade category,
        and full turn history.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None
    _output_dir = Path(output_dir) if output_dir else None
    if _output_dir:
        _output_dir.mkdir(parents=True, exist_ok=True)

    if categories is None:
        categories = load_categories(_prompts_dir)

    question_template = _load_template("question.md", _prompts_dir).strip()
    supervision_template = _load_template("supervision.md", _prompts_dir)
    supervision_followup_template = _load_template("supervision_followup.md", _prompts_dir)
    categories_str = _format_categories_for_prompt(categories)

    graph = build_answer_graph(
        session, supervisor,
        categories=categories,
        supervision_template=supervision_template,
        supervision_followup_template=supervision_followup_template,
        categories_str=categories_str,
        max_turns=max_turns,
        output_dir=_output_dir,
    )

    initial_state: AnswerState = {
        "question_text": question_text,
        "user_prompt": question_template.format(question=question_text),
        "response": "",
        "category_name": "",
        "turns": [],
        "turn_idx": 0,
    }

    final_state = await graph.ainvoke(initial_state)

    # Convert turn dicts back to AnswerTurn dataclasses.
    turns = [
        AnswerTurn(
            user_prompt=t["user_prompt"],
            response=t["response"],
            category=t["category"],
        )
        for t in final_state.get("turns", [])
    ]

    if turns:
        return AnswerResult(
            final_response=turns[-1].response,
            final_category=turns[-1].category,
            turns=turns,
        )

    return AnswerResult(final_response="", final_category="", turns=[])
