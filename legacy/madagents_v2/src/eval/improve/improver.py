"""Improve pipeline: improve docs → verify → revise loop.

Improves documentation based on diagnoses, then runs three parallel
checks (factual verification, style, quality). If any check fails,
feeds back all issues and revises. Loops up to N rounds.

Flow::

    improve → [verify_facts, verify_style, verify_quality] → decide
                                                                 │
                                                       (pass) → END
                                                       (fail) → revise → [verify...] → decide → ...
"""
from __future__ import annotations

import asyncio
import filecmp
import json
import shutil
import subprocess
from pathlib import Path

from eval.session import QuerySession
from eval.improve.style_checker import run_style_check
from eval.improve.quality_checker import run_quality_check
from eval.verify.extractor import extract_claims
from eval.verify.verifier import verify_claims
from eval.verify.claim_db import load_db, write_new_claims


MAX_ROUNDS = 10

_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_VERIFY_PROMPTS_DIR = _DEFAULT_PROMPTS_DIR  # improve-specific verify/extract prompts


def _load_template(name: str, prompts_dir: Path | None = None) -> str:
    d = prompts_dir or _DEFAULT_PROMPTS_DIR
    path = d / name
    if not path.exists():
        path = _DEFAULT_PROMPTS_DIR / name
    return path.read_text()


def _detect_changed_files(source_dir: Path, working_dir: Path) -> list[str]:
    """Detect files that differ between source and working directory.

    Returns relative paths of changed or new files in working_dir.
    """
    changed = []
    for f in sorted(working_dir.rglob("*")):
        if f.is_dir():
            continue
        rel = f.relative_to(working_dir)
        orig = source_dir / rel
        if not orig.exists() or not filecmp.cmp(orig, f, shallow=False):
            changed.append(str(rel))
    return changed


# ═══════════════════════════════════════════════════════════════════════
#  Improve / Revise
# ═══════════════════════════════════════════════════════════════════════

def _format_reference_answers(answers: list[dict] | None) -> str:
    """Format reference answers as an inline prompt section."""
    if not answers:
        return ""
    lines = [
        "## Reference Answers (unverified)\n",
        "The following reference answers were generated alongside the evaluation "
        "questions. They are **unverified** — produced by a language model and "
        "not checked by the verification pipeline. They may contain errors.\n",
        "Use them as inspiration for understanding what the docs should cover, "
        "not as ground truth. Do not copy content from reference answers into "
        "the documentation without verifying it first.\n",
    ]
    for a in answers:
        lines.append(f"**Q:** {a['question']}")
        lines.append(f"**A:** {a.get('reference_answer', '(none)')}\n")
    return "\n".join(lines) + "\n"


async def _improve_or_revise(
    session: QuerySession,
    *,
    diagnoses_path: Path | None = None,
    reference_answers: list[dict] | None = None,
    docs_dir: Path,
    feedback: dict[str, str] | None = None,
    is_revise: bool = False,
) -> None:
    """Send the improve or revise prompt to the session."""
    _map = getattr(session, "map_path", str)

    if is_revise:
        prompt = _load_template("revise.md").replace("{docs_dir}", _map(docs_dir))
        for key, value in (feedback or {}).items():
            prompt = prompt.replace(f"{{{key}}}", value)
        prompt = prompt.strip()
    else:
        prompt = (
            _load_template("improve.md")
            .replace("{diagnoses_path}", _map(diagnoses_path))
            .replace("{reference_answers_section}", _format_reference_answers(reference_answers))
            .replace("{docs_dir}", _map(docs_dir))
            .strip()
        )

    await session.ask(prompt)


# ═══════════════════════════════════════════════════════════════════════
#  Full pipeline
# ═══════════════════════════════════════════════════════════════════════

async def run_improve(
    diagnoses_path: Path,
    docs_source_dir: Path,
    docs_working_dir: Path,
    output_dir: Path,
    *,
    improver_session: QuerySession,
    fact_verifier_session: QuerySession,
    style_session: QuerySession,
    quality_session: QuerySession,
    initial_claims: list[dict] | None = None,
    run_id: str = "",
    db_path: Path | None = None,
    staging_dir: Path | None = None,
    max_rounds: int = MAX_ROUNDS,
    reference_answers: list[dict] | None = None,
) -> dict:
    """Run the full improve pipeline.

    Args:
        diagnoses_path: Path to diagnoses.json from the diagnose phase.
        docs_source_dir: Original docs directory (read-only reference).
        docs_working_dir: Working copy of docs (will be modified).
        output_dir: Directory for output files.
        improver_session: Session for improving/revising doc edits (sonnet).
        fact_verifier_session: Session for factual verification (MadAgents).
        style_session: Session for style checking (haiku).
        quality_session: Session for quality checking (haiku).
        initial_claims: Pre-verified claims from verify phase + DB.
        run_id: Unique identifier for staging files.
        db_path: Path to claim DB (for staging new claims).
        staging_dir: Directory for staging files.
        max_rounds: Maximum revision rounds.
        reference_answers: Unverified reference answers for failed questions.
            Passed inline to the improver prompt as inspiration, never
            written to disk (answerers must not see them during re-eval).

    Returns:
        Summary dict with changes, verification results, and round count.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if not run_id:
        import uuid
        run_id = uuid.uuid4().hex[:8]

    if staging_dir is None:
        staging_dir = output_dir / "staging"

    # Copy docs to working dir (clear contents first, keep the dir itself
    # since it may be a bind mount point).
    if docs_working_dir.exists():
        for item in docs_working_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        docs_working_dir.mkdir(parents=True)
    shutil.copytree(docs_source_dir, docs_working_dir, dirs_exist_ok=True)

    # Accumulate all verified claims across rounds.
    all_verified_claims = list(initial_claims or [])

    # Load DB claims if available.
    if db_path:
        db = load_db(db_path)
        if db:
            all_verified_claims.extend(db)

    n_initial = len(all_verified_claims)

    summary = {"rounds": [], "final_changes": [], "approved": False}
    feedback_parts: dict[str, str] = {}

    for round_idx in range(max_rounds):
        round_num = round_idx + 1
        round_dir = output_dir / f"round_{round_num}"
        round_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'=' * 40} Round {round_num}/{max_rounds} {'=' * 40}")

        # ── Improve or Revise ─────────────────────────────────────────
        if round_idx == 0:
            print("  Improving documentation...")
            await _improve_or_revise(
                improver_session,
                diagnoses_path=diagnoses_path,
                reference_answers=reference_answers,
                docs_dir=docs_working_dir,
            )
        else:
            print("  Revising documentation...")
            await _improve_or_revise(
                improver_session,
                docs_dir=docs_working_dir,
                feedback=feedback_parts,
                is_revise=True,
            )

        changed_files = _detect_changed_files(docs_source_dir, docs_working_dir)
        if not changed_files:
            print("  No changes made — stopping.")
            break

        print(f"  Changed {len(changed_files)} files: {', '.join(changed_files)}")

        # ── Generate diff for fact extraction ─────────────────────────
        diff_path = round_dir / "changes.diff"
        diff_result = subprocess.run(
            ["diff", "-ruN", str(docs_source_dir), str(docs_working_dir)],
            capture_output=True, text=True,
        )
        diff_path.write_text(diff_result.stdout)

        # ── Write known claims file for verifier ──────────────────────
        known_claims_path = round_dir / "known_claims.json"
        known_claims_path.write_text(json.dumps(all_verified_claims, indent=2))

        # ── Extract claims from changed content ───────────────────────
        claims_path = round_dir / "claims.json"
        verdicts_path = round_dir / "verdicts.json"
        style_path = round_dir / "style.json"
        quality_path = round_dir / "quality.json"

        _map = getattr(fact_verifier_session, "map_path", str)
        known_claim_texts = [c["claim"] for c in all_verified_claims if "claim" in c]
        print("  Extracting claims from changed content...")
        claims = await extract_claims(
            question_text="Documentation content verification",
            agent_response="",  # not used — extractor reads diff and docs directly
            session=fact_verifier_session,
            output_path=claims_path,
            known_claims=known_claim_texts,
            prompts_dir=str(_VERIFY_PROMPTS_DIR),
            diff_path=_map(diff_path),
            docs_dir=_map(docs_working_dir),
        )

        # ── Parallel: verify facts, check style, check quality ────────
        # Style and quality sessions are multi-turn (--resume) so they
        # accumulate context across rounds.
        print("  Running parallel checks (facts, style, quality)...")

        async def _verify_facts():
            if not claims:
                return {"passed": True, "issues": [], "verdicts": []}
            verdicts = await verify_claims(
                question_text="Documentation content verification",
                claims=claims,
                session=fact_verifier_session,
                verdicts_path=verdicts_path,
                known_claims_path=known_claims_path,
                prompts_dir=str(_VERIFY_PROMPTS_DIR),
            )
            incorrect = [v for v in verdicts if v.get("correct") is False]
            return {
                "passed": len(incorrect) == 0,
                "issues": [
                    f"Incorrect: {v['claim'][:80]} — {v.get('explanation', '')[:100]}"
                    for v in incorrect
                ],
                "verdicts": verdicts,
            }

        async def _verify_style():
            if round_idx > 0:
                # Follow-up on existing session — it has context from prior rounds.
                recheck_prompt = (
                    f"The documentation was revised to address your previous feedback. "
                    f"Please check the changed files again and write your assessment "
                    f"to `{style_path}`.\n\n"
                    f"Changed files:\n"
                    + "\n".join(f"- {f}" for f in changed_files)
                )
                await style_session.ask(recheck_prompt)
                from eval.improve.check_validator import validate_check_file
                validation = validate_check_file(style_path)
                if validation.ok:
                    return validation.result
                return {"passed": True, "issues": []}
            return await run_style_check(
                style_session,
                docs_dir=docs_working_dir, changed_files=changed_files,
                output_path=style_path,
            )

        async def _verify_quality():
            if round_idx > 0:
                # Follow-up on existing session.
                recheck_prompt = (
                    f"The documentation was revised to address your previous feedback. "
                    f"Please check the changed files again and write your assessment "
                    f"to `{quality_path}`.\n\n"
                    f"Changed files:\n"
                    + "\n".join(f"- {f}" for f in changed_files)
                )
                await quality_session.ask(recheck_prompt)
                from eval.improve.check_validator import validate_check_file
                validation = validate_check_file(quality_path)
                if validation.ok:
                    return validation.result
                return {"passed": True, "issues": []}
            return await run_quality_check(
                quality_session,
                docs_dir=docs_working_dir, changed_files=changed_files,
                output_path=quality_path,
            )

        facts_result, style_result, quality_result = await asyncio.gather(
            _verify_facts(), _verify_style(), _verify_quality(),
        )

        # ── Accumulate verified claims ────────────────────────────────
        new_verdicts = facts_result.get("verdicts", [])
        non_null = [v for v in new_verdicts if v.get("correct") is not None]
        all_verified_claims.extend(non_null)

        # ── Decide ────────────────────────────────────────────────────
        all_passed = (
            facts_result.get("passed", True)
            and style_result.get("passed", True)
            and quality_result.get("passed", True)
        )

        round_summary = {
            "round": round_num,
            "changed_files": changed_files,
            "facts_passed": facts_result.get("passed", True),
            "style_passed": style_result.get("passed", True),
            "quality_passed": quality_result.get("passed", True),
            "n_claims": len(claims),
            "n_incorrect": len(facts_result.get("issues", [])),
        }
        summary["rounds"].append(round_summary)

        if all_passed:
            print(f"\n  All checks passed!")
            summary["final_changes"] = changed_files
            summary["approved"] = True
            break

        # ── Build feedback for revision ───────────────────────────────
        def _render_feedback(template: str, result: dict) -> str:
            if result.get("passed", True):
                return ""
            issues_list = "\n".join(f"- {issue}" for issue in result.get("issues", []))
            return _load_template(template).replace("{issues_list}", issues_list)

        feedback_parts = {
            "factual_feedback": _render_feedback("_feedback_factual.md", facts_result),
            "style_feedback": _render_feedback("_feedback_style.md", style_result),
            "quality_feedback": _render_feedback("_feedback_quality.md", quality_result),
        }
        print(f"  Issues found — revising (round {round_idx + 2})...")

    else:
        raise RuntimeError(
            f"Improve phase failed: checks did not pass after {max_rounds} rounds."
        )

    # ── Generate diff ─────────────────────────────────────────────────
    diff_path = output_dir / "docs.diff"
    try:
        result = subprocess.run(
            ["diff", "-ruN", str(docs_source_dir), str(docs_working_dir)],
            capture_output=True, text=True,
        )
        diff_text = result.stdout
        if diff_text:
            diff_path.write_text(diff_text)
            summary["diff_path"] = str(diff_path)
            n_lines = len(diff_text.splitlines())
            print(f"\n  Diff: {diff_path} ({n_lines} lines)")
        else:
            print("\n  No diff — docs unchanged.")
    except Exception as e:
        print(f"\n  Could not generate diff: {e}")

    # ── Stage new claims for DB merge ─────────────────────────────────
    if db_path:
        new_claims = all_verified_claims[n_initial:]
        non_null_new = [c for c in new_claims if c.get("correct") is not None]
        if non_null_new:
            write_new_claims(staging_dir, run_id, non_null_new)
            print(f"  Staged {len(non_null_new)} new claims for DB merge.")

    # Write summary.
    (output_dir / "improve_summary.json").write_text(json.dumps(summary, indent=2))

    return summary
