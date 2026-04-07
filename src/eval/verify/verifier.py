"""Claim verification harness built on LangGraph.

Takes a list of pre-extracted claims and verifies each one via a
MadAgents session.  Uses the same verify → json_validate → retry
pattern as the other harnesses.

Graph shape::

    START → verify → json_validate ─(valid)──→ END
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
from eval.verify.verdict_validator import validate_verdicts_file


VERDICTS_FILENAME = "verdicts.json"
DEFAULT_MAX_RETRIES = 2


# ═══════════════════════════════════════════════════════════════════════
#  Graph state
# ═══════════════════════════════════════════════════════════════════════

class VerifyState(TypedDict, total=False):
    """LangGraph state for the claim verification loop."""

    attempt: int
    verdicts: list[dict]
    validation_errors: list[str]
    done: bool


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
    question_text: str,
    verdicts_path: str,
    known_claims_path: str = "",
    prompts_dir: Path | None = None,
) -> str:
    return (
        _load_template("verify.md", prompts_dir)
        .replace("{question}", question_text)
        .replace("{verdicts_path}", verdicts_path)
        .replace("{known_claims_path}", known_claims_path or "(not available)")
        .strip()
    )


def _build_retry_prompt(
    errors: list[str],
    verdicts_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("verify_retry.md", prompts_dir).format(
        error_list=error_list,
        verdicts_path=verdicts_path,
    ).strip()


# ═══════════════════════════════════════════════════════════════════════
#  Graph builder
# ═══════════════════════════════════════════════════════════════════════

def build_verify_graph(
    session: QuerySession | None = None,
    *,
    question_text: str = "",
    verdicts_path: Path | None = None,
    known_claims_path: Path | None = None,
    expected_count: int = 0,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    """Build and compile the claim verification graph.

    The verifier reads claims from *verdicts_path* (a copy of
    ``claims.json``), enriches each object with verdict fields
    (``correct``, ``method``, ``evidence``, ``explanation``),
    and edits the file in place.

    When *session* is ``None`` (visualization mode), nodes are no-ops.
    """
    _map = getattr(session, "map_path", str) if session else str
    _verdicts_str = _map(verdicts_path) if verdicts_path else ""
    _known_str = _map(known_claims_path) if known_claims_path else ""

    # ── Node: verify_claims ───────────────────────────────────────────
    async def verify_claims_node(state: VerifyState) -> dict:
        if session is None:
            return {"done": True}

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                question_text,
                _verdicts_str, _known_str,
                prompts_dir=prompts_dir,
            )
        else:
            print(f"  Retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _verdicts_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    # ── Node: json_validate ───────────────────────────────────────────
    def json_validate_node(state: VerifyState) -> dict:
        if session is None:
            return {"verdicts": [], "done": True}

        validation = validate_verdicts_file(
            verdicts_path, expected_count=expected_count,
        )
        attempt = state.get("attempt", 0)

        if validation.ok:
            print(f"  Verified {len(validation.verdicts)} claims.")
            return {"verdicts": validation.verdicts, "done": True}

        print(f"  Validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Claim verification failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    # ── Routing ──────────────────────────────────────────────────────
    def route_after_json_validate(state: VerifyState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    # ── Build graph ──────────────────────────────────────────────────
    graph = StateGraph(VerifyState)
    graph.add_node("verify_claims", verify_claims_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "verify_claims")
    graph.add_edge("verify_claims", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "verify_claims", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


# ═══════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════

async def verify_claims(
    question_text: str,
    claims: list[dict],
    session: QuerySession,
    verdicts_path: Path,
    *,
    known_claims_path: Path | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> list[dict]:
    """Verify pre-extracted claims by enriching them with verdicts.

    Copies *claims* to *verdicts_path*, then asks the verifier session
    to read the file, verify each claim, and edit it in place by adding
    ``correct``, ``confidence``, ``method``, and ``explanation`` fields.

    Args:
        question_text: The original question (context for the verifier).
        claims: List of claim dicts from the extraction step.
        session: Query interface to the verifier agent (typically a
            MadAgentsSession with tool access for code execution,
            source inspection, etc.).
        verdicts_path: Path where the enriched verdicts file will be
            written.  Starts as a copy of the claims.
        known_claims_path: Path to relevant known claims from the
            database (optional context for the verifier).
        max_retries: Retry attempts after validation failure.
        prompts_dir: Custom prompts directory.

    Returns:
        List of verdict dicts, each with ``claim``, ``correct``,
        ``method``, ``evidence``, and ``explanation``.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    # Write claims to verdicts_path as starting point.
    verdicts_path.parent.mkdir(parents=True, exist_ok=True)
    verdicts_path.write_text(json.dumps(claims, indent=2))

    print(f"\n  Verifying {len(claims)} claims...")

    graph = build_verify_graph(
        session,
        question_text=question_text,
        verdicts_path=verdicts_path,
        known_claims_path=known_claims_path,
        expected_count=len(claims),
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
    )

    initial_state: VerifyState = {
        "attempt": 0,
        "verdicts": [],
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("verdicts", [])
