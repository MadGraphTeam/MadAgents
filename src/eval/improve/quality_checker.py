"""Quality check harness: verify documentation structure and appropriateness.

Graph shape::

    START → check_quality → json_validate ─(valid)──→ END
                    ↑             │
                    └──(retry)────┘
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from eval.session import QuerySession
from eval.improve.check_validator import validate_check_file


DEFAULT_MAX_RETRIES = 2


class QualityState(TypedDict, total=False):
    attempt: int
    result: dict
    validation_errors: list[str]
    done: bool


_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def build_quality_graph(
    session: QuerySession | None = None,
    *,
    docs_dir: Path | None = None,
    changed_files: list[str] | None = None,
    output_path: Path | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: Path | None = None,
) -> CompiledStateGraph:
    _map = getattr(session, "map_path", str) if session else str
    _docs_str = _map(docs_dir) if docs_dir else ""
    _output_str = _map(output_path) if output_path else ""
    _changed = changed_files or []
    _changed_str = "\n".join(f"- {f}" for f in _changed)

    async def check_quality_node(state: QualityState) -> dict:
        if session is None:
            return {"done": True}

        if output_path and output_path.exists():
            output_path.unlink()

        attempt = state.get("attempt", 0)
        if attempt == 0:
            prompt = (
                _load_template("quality.md", prompts_dir)
                .replace("{docs_dir}", _docs_str)
                .replace("{changed_files}", _changed_str)
                .replace("{output_path}", _output_str)
                .strip()
            )
        else:
            errors = state.get("validation_errors", [])
            error_list = "\n".join(f"- {e}" for e in errors)
            prompt = (
                f"Your previous output had issues:\n\n{error_list}\n\n"
                f"Please write a corrected file to `{_output_str}`. "
                f"Must be a JSON object with `passed` (bool) and `issues` (list of strings)."
            )

        await session.ask(prompt)
        return {}

    def json_validate_node(state: QualityState) -> dict:
        if session is None:
            return {"result": {"passed": True, "issues": []}, "done": True}

        validation = validate_check_file(output_path)
        attempt = state.get("attempt", 0)

        if validation.ok:
            return {"result": validation.result, "done": True}

        print(f"  Quality validation failed: {'; '.join(validation.errors)}")

        if attempt >= max_retries:
            return {"result": {"passed": True, "issues": []}, "done": True}

        return {"validation_errors": validation.errors, "attempt": attempt + 1}

    def route(state: QualityState) -> str:
        return "valid" if state.get("done", False) else "retry"

    graph = StateGraph(QualityState)
    graph.add_node("check_quality", check_quality_node)
    graph.add_node("json_validate", json_validate_node)
    graph.add_edge(START, "check_quality")
    graph.add_edge("check_quality", "json_validate")
    graph.add_conditional_edges("json_validate", route, {"retry": "check_quality", "valid": END})
    return graph.compile().with_config({"recursion_limit": 2 * (1 + max_retries) + 5})


async def run_quality_check(
    session: QuerySession,
    docs_dir: Path,
    changed_files: list[str],
    output_path: Path,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    prompts_dir: str | Path | None = None,
) -> dict:
    """Run quality check. Returns {"passed": bool, "issues": [...]}."""
    _prompts_dir = Path(prompts_dir) if prompts_dir else None
    print(f"\n  Checking quality...")

    graph = build_quality_graph(
        session, docs_dir=docs_dir, changed_files=changed_files,
        output_path=output_path, max_retries=max_retries, prompts_dir=_prompts_dir,
    )
    final = await graph.ainvoke({"attempt": 0, "result": {}, "validation_errors": [], "done": False})
    return final.get("result", {"passed": True, "issues": []})
