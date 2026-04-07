"""Claim extraction harness built on LangGraph.

Splits an agent's answer into individual verifiable claims via an
extract → json_validate → retry loop.  Analogous to
:mod:`eval.generate.generator`.

Graph shape::

    START → extract → json_validate ─(valid)──→ END
                ↑          │
                └──(retry)─┘
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.session import QuerySession
from eval.verify.claim_validator import validate_claims_file


CLAIMS_FILENAME = "claims.json"
DEFAULT_MAX_RETRIES = 3


# ═══════════════════════════════════════════════════════════════════════
#  Graph state
# ═══════════════════════════════════════════════════════════════════════

class ExtractState(TypedDict, total=False):
    """LangGraph state for the claim extraction loop."""

    attempt: int
    claims: list[dict]
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
    agent_response: str,
    output_path: str,
    known_claims: list[str] | None = None,
    prompts_dir: Path | None = None,
    **extra_replacements: str,
) -> str:
    known_section = ""
    if known_claims:
        claims_list = "\n".join(f"- {c}" for c in known_claims[:100])
        known_section = _load_template(
            "_known_claims.md", prompts_dir,
        ).replace("{known_claims_list}", claims_list)

    prompt = (
        _load_template("extract.md", prompts_dir)
        .replace("{question}", question_text)
        .replace("{agent_response}", agent_response)
        .replace("{known_claims_section}", known_section)
        .replace("{output_path}", output_path)
    )
    for key, value in extra_replacements.items():
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt.strip()


def _build_retry_prompt(
    errors: list[str],
    output_path: str,
    prompts_dir: Path | None = None,
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    return _load_template("extract_retry.md", prompts_dir).format(
        error_list=error_list,
        output_path=output_path,
    ).strip()


# ═══════════════════════════════════════════════════════════════════════
#  Graph builder
# ═══════════════════════════════════════════════════════════════════════

def build_extract_graph(
    session: QuerySession | None = None,
    *,
    question_text: str = "",
    agent_response: str = "",
    output_path: Path | None = None,
    known_claims: list[str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
    **extra_replacements: str,
) -> CompiledStateGraph:
    """Build and compile the claim extraction graph.

    When *session* is ``None`` (visualization mode), nodes are no-ops.

    Args:
        known_claims: Previously extracted claim texts. The extractor
            will reuse the same wording when the same fact appears,
            improving cache hit rates.
        **extra_replacements: Additional placeholder substitutions
            for the extract prompt template.
    """
    _map = getattr(session, "map_path", str) if session else str
    _output_str = _map(output_path) if output_path else ""

    # ── Node: extract ─────────────────────────────────────────────────
    async def extract_node(state: ExtractState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = _build_initial_prompt(
                question_text, agent_response,
                _output_str, known_claims=known_claims,
                prompts_dir=prompts_dir,
                **extra_replacements,
            )
        else:
            print(f"  Retry {attempt}/{max_retries}...")
            prompt = _build_retry_prompt(
                state.get("validation_errors", []),
                _output_str, prompts_dir=prompts_dir,
            )

        await session.ask(prompt)
        return {}

    # ── Node: json_validate ───────────────────────────────────────────
    def json_validate_node(state: ExtractState) -> dict:
        if session is None:
            return {"claims": [], "done": True}

        validation = validate_claims_file(output_path)
        attempt = state.get("attempt", 0)

        if validation.ok:
            print(f"  Extracted {len(validation.claims)} claims.")
            return {"claims": validation.claims, "done": True}

        print(f"  Validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            raise RuntimeError(
                f"Claim extraction failed after {max_retries} retries: "
                f"{'; '.join(validation.errors)}"
            )

        return {
            "validation_errors": validation.errors,
            "attempt": attempt + 1,
        }

    # ── Routing ──────────────────────────────────────────────────────
    def route_after_json_validate(state: ExtractState) -> str:
        if state.get("done", False):
            return "valid"
        return "retry"

    # ── Build graph ──────────────────────────────────────────────────
    graph = StateGraph(ExtractState)
    graph.add_node("extract", extract_node)
    graph.add_node("json_validate", json_validate_node)

    graph.add_edge(START, "extract")
    graph.add_edge("extract", "json_validate")
    graph.add_conditional_edges(
        "json_validate", route_after_json_validate,
        {"retry": "extract", "valid": END},
    )

    return graph.compile().with_config(
        {"recursion_limit": 2 * (1 + max_retries) + 5},
    )


# ═══════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════

async def extract_claims(
    question_text: str,
    agent_response: str,
    session: QuerySession,
    output_path: Path,
    *,
    known_claims: list[str] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
    **extra_replacements: str,
) -> list[dict]:
    """Extract verifiable claims from an agent's answer.

    Sends the question and answer to the session, validates the output
    file, and retries with feedback if the content is invalid.

    Args:
        question_text: The question that was answered.
        agent_response: The agent's response to split into claims.
        session: Query interface to the extraction agent.
        output_path: Full path where the agent should write the
            claims JSON file.
        known_claims: Previously extracted claim texts. The extractor
            reuses the same wording for matching facts, improving
            cache hit rates.
        max_retries: Retry attempts after validation failure.
        prompts_dir: Custom prompts directory.
        **extra_replacements: Additional placeholder substitutions
            for the extract prompt template.

    Returns:
        List of claim dicts, each with a ``claim`` key.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None

    print(f"\n  Extracting claims...")

    graph = build_extract_graph(
        session,
        question_text=question_text,
        agent_response=agent_response,
        output_path=output_path,
        known_claims=known_claims,
        max_retries=max_retries,
        prompts_dir=_prompts_dir,
        **extra_replacements,
    )

    initial_state: ExtractState = {
        "attempt": 0,
        "claims": [],
        "validation_errors": [],
        "done": False,
    }

    final_state = await graph.ainvoke(initial_state)
    return final_state.get("claims", [])
