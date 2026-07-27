"""Remember harness: select which verified claims are new and worth caching.

Uses a cheap LLM (haiku) to compare verified claims against the known
database and output indices of genuinely new claims.

Graph shape::

    START → remember → json_validate ─(valid)──→ END
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
from eval.verify.remember_validator import validate_remember_file


REMEMBER_FILENAME = "remember.json"
DEFAULT_MAX_RETRIES = 2


class RememberState(TypedDict, total=False):
    attempt: int
    indices: list[int]
    validation_errors: list[str]
    done: bool


_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def _build_initial_prompt(
    verdicts_path: str,
    known_claims_path: str,
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    return (
        _load_template("remember.md", prompts_dir)
        .replace("{verdicts_path}", verdicts_path)
        .replace("{known_claims_path}", known_claims_path)
        .replace("{output_path}", output_path)
        .strip()
    )


def _build_retry_prompt(
    errors: list[str],
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("remember_retry.md", prompts_dir).format(
        error_list=error_list,
        output_path=output_path,
    ).strip()


def build_remember_graph(
    session: QuerySession | None = None,
    *,
    verdicts_path: Path | None = None,
    known_claims_path: Path | None = None,
    output_path: Path | None = None,
    max_verdict_index: int | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build the remember graph."""
    _map = getattr(session, "map_path", str) if session else str
    _verdicts_str = _map(verdicts_path) if verdicts_path else ""
    _known_str = _map(known_claims_path) if known_claims_path else ""
    _output_str = _map(output_path) if output_path else ""

    async def remember_node(state: RememberState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                _verdicts_str, _known_str,
                _output_str, prompts_dir=prompts_dir,
            )
        else:
            print(f"  Remember retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    def json_validate_node(state: RememberState) -> dict:
        if session is None:
            return {"indices": [], "done": True}

        validation = validate_remember_file(
            output_path, max_index=max_verdict_index,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            print(f"  {len(validation.indices)} new claims to remember.")
            return {"indices": validation.indices, "done": True}

        print(f"  Remember validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Remember failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    def route_after_json_validate(state: RememberState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    graph = StateGraph(RememberState)
    graph.add_node("remember", remember_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "remember")
    graph.add_edge("remember", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "remember", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


async def run_remember(
    session: QuerySession,
    verdicts_path: Path,
    known_claims_path: Path,
    output_path: Path,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> list[int]:
    """Select which verified claims are new and worth caching.

    Args:
        session: Query session (haiku).
        verdicts_path: Path to the verdicts file.
        known_claims_path: Path to the simplified known claims file.
        output_path: Where to write the selected indices.
        max_retries: Retry attempts.
        prompts_dir: Custom prompts directory.

    Returns:
        List of verdict indices (0-based) to add to the database.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    # Determine max valid index from verdicts file.
    max_index = None
    if verdicts_path.exists():
        verdicts = json.loads(verdicts_path.read_text())
        if isinstance(verdicts, list):
            max_index = len(verdicts) - 1

    print(f"\n  Selecting new claims to remember...")

    graph = build_remember_graph(
        session,
        verdicts_path=verdicts_path,
        known_claims_path=known_claims_path,
        output_path=output_path,
        max_verdict_index=max_index,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: RememberState = {
        "attempt": 0,
        "indices": [],
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("indices", [])
