#!/usr/bin/env python3
"""Iterate: diagnose + improve + reeval in two isolated phases.

Split into two container invocations by run.sh for isolation:

- **Phase 1 (improve)**: diagnose previous errors, improve docs.
- **Phase 2 (reeval)**: answer + verify + grade with improved docs
  in a clean container — no access to diagnose/improve output.

Phase 1 container provides:
- /output — output directory
- /docs_current — writable working copy of docs
- /docs_source — read-only source docs for diffing
- /input/results.json — previous results
- /input/verdicts.json — previous verdicts
- /input/grade.json — previous grade
- /input/questions_full.json — questions with reference answers (optional)
- /madgraph_docs — current docs (read-only, for agents)
- /db — claim database
- /src on PYTHONPATH

Phase 2 container provides:
- /output — fresh output directory (no diagnose/improve output)
- /input/results.json — previous results (question text)
- /input/grade.json — previous grade (for comparison)
- /input/improve_phase.json — summary from phase 1 (optional)
- /madgraph_docs — improved docs (read-only)
- /db — claim database
- /src on PYTHONPATH

Usage (via run.sh):
    ./eval/examples/8_iterate/run.sh --from-7
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_src = Path("/src")
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

WORK_DIR = Path("/output")
RESULTS_FILE = Path("/input/results.json")
PREV_GRADE_FILE = Path("/input/grade.json")
LOG_DIR = WORK_DIR / "logs"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
DB_PATH = Path("/db/claim_db.json")


def _fmt_grade(g: dict) -> str:
    name = g.get("grade", "?")
    tags = g.get("tags", [])
    return f"{name} [{', '.join(tags)}]" if tags else name


# ═══════════════════════════════════════════════════════════════════
#  Phase 1: diagnose + improve
# ═══════════════════════════════════════════════════════════════════

VERDICTS_FILE = Path("/input/verdicts.json")
QUESTIONS_FULL_FILE = Path("/input/questions_full.json")
DOCS_SOURCE = Path("/docs_source")
DOCS_WORKING = Path("/docs_current")


async def run_improve_phase(args: argparse.Namespace) -> dict:
    """Diagnose previous errors and improve documentation."""
    from eval.diagnose import DIAGNOSE_FILENAME, run_diagnose
    from eval.improve import run_improve
    from eval.session import ClaudeCodeSession, MadAgentsSession
    from eval.transcript import write_summary, write_transcript, write_workflow

    if not RESULTS_FILE.exists():
        print("ERROR: Previous results not found.")
        sys.exit(1)

    prev_results = json.loads(RESULTS_FILE.read_text())
    question_text = prev_results["question"]

    prev_grade = {}
    if PREV_GRADE_FILE.exists():
        prev_grade = json.loads(PREV_GRADE_FILE.read_text())

    print(f"\n{'=' * 60}")
    print(f"  Iterating on: {question_text[:80]}...")
    print(f"  Previous grade: {_fmt_grade(prev_grade)}")
    print(f"{'=' * 60}")

    transcript = []

    # ── Step 1: Diagnose ──────────────────────────────────────────
    print("\n--- Step 1: Diagnose ---")

    diagnose_dir = WORK_DIR / "diagnose"
    diagnose_dir.mkdir(parents=True, exist_ok=True)
    diagnose_path = diagnose_dir / DIAGNOSE_FILENAME

    prev_transcript = WORK_DIR / "prev_transcripts" / "full.json"

    diagnoser = ClaudeCodeSession(
        cwd=str(Path("/session_diagnoser")),
        name="diagnoser",
        model=args.model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    diagnoses = await run_diagnose(
        question_text=question_text,
        session=diagnoser,
        verdicts_path=VERDICTS_FILE,
        transcript_path=prev_transcript,
        output_path=diagnose_path,
        grade=prev_grade or None,
    )

    total_findings = sum(len(v) for v in diagnoses.values())
    print(f"  Findings: {total_findings}")

    if total_findings == 0:
        print("  No documentation issues found -- nothing to improve.")
        result = {"findings": 0, "approved": False, "improved": False}
        (WORK_DIR / "improve_phase.json").write_text(json.dumps(result, indent=2))
        write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
        return result

    # ── Step 2: Improve ───────────────────────────────────────────
    print("\n--- Step 2: Improve ---")

    improve_dir = WORK_DIR / "improve"

    initial_claims = []
    if VERDICTS_FILE.exists():
        verdicts = json.loads(VERDICTS_FILE.read_text())
        initial_claims = [v for v in verdicts if v.get("correct") is not None]

    ref_answers = None
    if QUESTIONS_FULL_FILE.exists():
        questions = json.loads(QUESTIONS_FULL_FILE.read_text())
        ref_answers = [
            {"question": q["text"], "reference_answer": q.get("reference_answer", "")}
            for q in questions if q.get("reference_answer")
        ] or None

    improver = ClaudeCodeSession(
        cwd=str(Path("/session_improver")),
        name="improver", model=args.model,
        permission_mode="default", setting_sources=["local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )
    fact_verifier = MadAgentsSession(
        cwd=str(Path("/session_fact_verifier")),
        name="fact_verifier", model=args.model,
        permission_mode="default", setting_sources=["project", "local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )
    style_checker = ClaudeCodeSession(
        cwd=str(Path("/session_style")),
        name="style_checker", model=args.check_model,
        permission_mode="default", setting_sources=["local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )
    quality_checker = ClaudeCodeSession(
        cwd=str(Path("/session_quality")),
        name="quality_checker", model=args.check_model,
        permission_mode="default", setting_sources=["local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )

    improve_summary = await run_improve(
        diagnoses_path=diagnose_path,
        docs_source_dir=DOCS_SOURCE,
        docs_working_dir=DOCS_WORKING,
        output_dir=improve_dir,
        improver_session=improver,
        fact_verifier_session=fact_verifier,
        style_session=style_checker,
        quality_session=quality_checker,
        initial_claims=initial_claims,
        db_path=DB_PATH,
        max_rounds=args.max_improve_rounds,
        reference_answers=ref_answers,
    )

    approved = improve_summary.get("approved", False) or bool(improve_summary.get("final_changes"))

    result = {
        "findings": total_findings,
        "approved": approved,
        "improve_rounds": len(improve_summary.get("rounds", [])),
    }
    (WORK_DIR / "improve_phase.json").write_text(json.dumps(result, indent=2))

    if not approved:
        print("  Improvement failed -- skipping reeval.")
        result["improved"] = False

    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return result


# ═══════════════════════════════════════════════════════════════════
#  Phase 2: reeval (clean container)
#
#  No previous evaluation artifacts are mounted — only the question
#  text (from results.json) and improved docs (as /madgraph_docs).
#  The comparison is done by run.sh on the host after this exits.
# ═══════════════════════════════════════════════════════════════════


async def run_reeval_phase(args: argparse.Namespace) -> dict:
    """Re-evaluate: answer + verify + grade in a clean container."""
    from eval.answer import run_answer_loop
    from eval.grade import GRADE_FILENAME, run_grading
    from eval.session import ClaudeCodeSession, MadAgentsSession
    from eval.transcript import write_summary, write_transcript, write_workflow
    from eval.verify import run_verification

    if not RESULTS_FILE.exists():
        print("ERROR: Previous results not found.")
        sys.exit(1)

    prev_results = json.loads(RESULTS_FILE.read_text())
    question_text = prev_results["question"]

    print(f"\n{'=' * 60}")
    print(f"  Re-evaluating: {question_text[:80]}...")
    print(f"{'=' * 60}")

    transcript = []

    # ── Answer ────────────────────────────────────────────────────
    print("\n--- Answer ---")

    answerer = MadAgentsSession(
        cwd=str(WORK_DIR),
        name="answerer", model=args.model,
        permission_mode="default", setting_sources=["project", "local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )
    supervisor = ClaudeCodeSession(
        cwd=str(Path("/session_supervisor")),
        name="supervisor", model=args.check_model,
        permission_mode="default", setting_sources=["local"],
        transcript=transcript, log_dir=str(LOG_DIR),
    )

    answer = await run_answer_loop(
        question_text=question_text,
        session=answerer,
        supervisor=supervisor,
        output_dir=WORK_DIR / "supervision",
        max_turns=args.max_turns,
    )

    answer_result = {
        "question": question_text,
        "final_response": answer.final_response,
        "final_category": answer.final_category,
        "all_messages": answerer.messages,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(answer_result, indent=2))
    print(f"  Answer: {answer.final_category} ({len(answer.turns)} turns)")

    # ── Verify ────────────────────────────────────────────────────
    print("\n--- Verify ---")

    agent_response = "\n\n".join(answerer.messages) if answerer.messages else answer.final_response

    extractor = ClaudeCodeSession(
        cwd=str(Path("/session_extractor")), name="extractor",
        model=args.check_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript, log_dir=str(LOG_DIR),
    )
    triage = ClaudeCodeSession(
        cwd=str(Path("/session_triage")), name="triage",
        model=args.check_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript, log_dir=str(LOG_DIR),
    )
    verifier = MadAgentsSession(
        cwd=str(Path("/session_verifier")), name="verifier",
        model=args.model, permission_mode="default",
        setting_sources=["project", "local"], transcript=transcript, log_dir=str(LOG_DIR),
    )
    remember = ClaudeCodeSession(
        cwd=str(Path("/session_remember")), name="remember",
        model=args.check_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript, log_dir=str(LOG_DIR),
    )

    verification_dir = WORK_DIR / "verification"
    claims, verdicts = await run_verification(
        question_text=question_text,
        agent_response=agent_response,
        extractor_session=extractor,
        triage_session=triage,
        verifier_session=verifier,
        remember_session=remember,
        output_dir=verification_dir,
        db_path=DB_PATH,
    )

    n_correct = sum(1 for v in verdicts if v.get("correct") is True)
    n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)
    print(f"  Verified: {n_correct} correct, {n_incorrect} incorrect")

    # ── Grade ─────────────────────────────────────────────────────
    print("\n--- Grade ---")

    grader = ClaudeCodeSession(
        cwd=str(Path("/session_grader")), name="grader",
        model=args.check_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript, log_dir=str(LOG_DIR),
    )

    grade_dir = WORK_DIR / "grade"
    grade_dir.mkdir(parents=True, exist_ok=True)
    verdicts_path = verification_dir / "verdicts.json"

    grade = await run_grading(
        question_text=question_text,
        verdicts=verdicts,
        session=grader,
        verdicts_path=verdicts_path,
        output_path=grade_dir / GRADE_FILENAME,
    )

    grade_name = grade.get("grade", "?")
    tags = grade.get("tags", [])
    tags_str = f" [{', '.join(tags)}]" if tags else ""
    print(f"\n  Grade: {grade_name}{tags_str}")
    print(f"  {grade.get('explanation', '')[:120]}")

    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return grade


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Iterate: diagnose + improve + reeval (two-phase)",
    )
    parser.add_argument("--phase", choices=["improve", "reeval"], required=True,
                        help="Which phase to run")
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model for main tasks (default: sonnet)")
    parser.add_argument("--check-model", type=str, default="haiku",
                        help="Model for cheap checks (default: haiku)")
    parser.add_argument("--max-improve-rounds", type=int, default=10,
                        help="Max improve revision rounds (default: 10)")
    parser.add_argument("--max-turns", type=int, default=3,
                        help="Max answer turns (default: 3)")
    args = parser.parse_args()

    if args.phase == "improve":
        result = asyncio.run(run_improve_phase(args))
        if not result.get("approved"):
            sys.exit(0)
    else:
        result = asyncio.run(run_reeval_phase(args))

    print(f"  Output: {WORK_DIR}")


if __name__ == "__main__":
    main()
