"""Triage harness: select relevant known claims for verification.

Uses a cheap LLM (haiku) to read new claims and the known claims
database from the filesystem, and output a flat list of relevant
database IDs.

Graph shape::

    START → triage → json_validate ─(valid)──→ END
               ↑          │
               └──(retry)─┘
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.session import QuerySession
from eval.verify.triage_validator import validate_triage_file


TRIAGE_FILENAME = "triage.json"
DEFAULT_MAX_RETRIES = 2


class TriageState(TypedDict, total=False):
    attempt: int
    ids: list[int]
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
    claims_path: str,
    known_claims_path: str,
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    return (
        _load_template("triage.md", prompts_dir)
        .replace("{claims_path}", claims_path)
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
    return _load_template("triage_retry.md", prompts_dir).format(
        error_list=error_list,
        output_path=output_path,
    ).strip()


def build_triage_graph(
    session: QuerySession | None = None,
    *,
    claims_path: Path | None = None,
    known_claims_path: Path | None = None,
    output_path: Path | None = None,
    valid_db_ids: set[int] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build the triage graph."""
    _map = getattr(session, "map_path", str) if session else str
    _claims_str = _map(claims_path) if claims_path else ""
    _known_str = _map(known_claims_path) if known_claims_path else ""
    _output_str = _map(output_path) if output_path else ""

    async def triage_node(state: TriageState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                _claims_str, _known_str,
                _output_str, prompts_dir=prompts_dir,
            )
        else:
            print(f"  Triage retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    def json_validate_node(state: TriageState) -> dict:
        if session is None:
            return {"ids": [], "done": True}

        validation = validate_triage_file(
            output_path, valid_ids=valid_db_ids,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            print(f"  Triage selected {len(validation.ids)} known claims.")
            return {"ids": validation.ids, "done": True}

        print(f"  Triage validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Triage failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    def route_after_json_validate(state: TriageState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    graph = StateGraph(TriageState)
    graph.add_node("triage", triage_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "triage")
    graph.add_edge("triage", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "triage", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


async def run_triage(
    claims_path: Path,
    known_claims_path: Path,
    output_path: Path,
    session: QuerySession,
    *,
    valid_db_ids: set[int] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> list[int]:
    """Run triage: select relevant known claims.

    Returns:
        List of database IDs that are relevant to the new claims.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    print(f"\n  Triaging claims against known database...")

    graph = build_triage_graph(
        session,
        claims_path=claims_path,
        known_claims_path=known_claims_path,
        output_path=output_path,
        valid_db_ids=valid_db_ids,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: TriageState = {
        "attempt": 0,
        "ids": [],
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("ids", [])
