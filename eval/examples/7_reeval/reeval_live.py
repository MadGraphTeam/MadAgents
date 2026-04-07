#!/usr/bin/env python3
"""Re-evaluate: answer the same question with improved docs, verify, grade.

Chains the answer, verify, and grade phases in one run to test whether
the documentation improvements from the improve phase actually help.

The container mounts the improved docs (from 6_improve) as /madgraph_docs
instead of the original docs.  No previous evaluation artifacts (grade,
verdicts, etc.) are mounted — the comparison is done by run.sh on the
host after this script exits.

The container provides:
- /output — fresh output directory
- /input/results.json — the answer phase result (question text only)
- /madgraph_docs — improved docs (read-only)
- /db — claim database
- /src on PYTHONPATH

Usage (via run.sh):
    ./eval/examples/7_reeval/run.sh
    ./eval/examples/7_reeval/run.sh --model sonnet
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

from eval.answer import run_answer_loop
from eval.grade import GRADE_FILENAME, run_grading
from eval.session import ClaudeCodeSession, MadAgentsSession
from eval.transcript import write_summary, write_transcript, write_workflow
from eval.verify import run_verification

WORK_DIR = Path("/output")
RESULTS_FILE = Path("/input/results.json")
LOG_DIR = WORK_DIR / "logs"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
DB_PATH = Path("/db/claim_db.json")

# Session workdirs.
ANSWERER_DIR = WORK_DIR
SUPERVISOR_DIR = Path("/session_supervisor")
EXTRACTOR_DIR = Path("/session_extractor")
TRIAGE_DIR = Path("/session_triage")
VERIFIER_DIR = Path("/session_verifier")
REMEMBER_DIR = Path("/session_remember")
GRADER_DIR = Path("/session_grader")


async def run(args: argparse.Namespace) -> dict:
    if not RESULTS_FILE.exists():
        print("ERROR: Original results not found.")
        sys.exit(1)

    original = json.loads(RESULTS_FILE.read_text())
    question_text = original["question"]

    print(f"\n{'=' * 60}")
    print(f"  Re-evaluating with improved docs:")
    print(f"  {question_text[:80]}...")
    print(f"{'=' * 60}\n")

    transcript = []

    # ══════════════════════════════════════════════════════════════
    #  Phase 1: Answer (with improved docs)
    # ══════════════════════════════════════════════════════════════
    print("--- Phase: Answer ---")

    answerer = MadAgentsSession(
        cwd=str(ANSWERER_DIR),
        name="answerer",
        model=args.model,
        permission_mode="default",
        setting_sources=["project", "local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )
    supervisor = ClaudeCodeSession(
        cwd=str(SUPERVISOR_DIR),
        name="supervisor",
        model=args.supervisor_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    supervision_dir = WORK_DIR / "supervision"
    answer = await run_answer_loop(
        question_text=question_text,
        session=answerer,
        supervisor=supervisor,
        output_dir=supervision_dir,
        max_turns=args.max_turns,
    )

    # Save answer result (no reference_answer — not available here).
    answer_result = {
        "question": question_text,
        "final_response": answer.final_response,
        "final_category": answer.final_category,
        "num_turns": len(answer.turns),
        "all_messages": answerer.messages,
    }
    (WORK_DIR / "results.json").write_text(json.dumps(answer_result, indent=2))
    print(f"  Answer: {answer.final_category} ({len(answer.turns)} turns)")

    # ══════════════════════════════════════════════════════════════
    #  Phase 2: Verify
    # ══════════════════════════════════════════════════════════════
    print("\n--- Phase: Verify ---")

    # Use all messages for verification.
    all_messages = answerer.messages
    agent_response = "\n\n".join(all_messages) if all_messages else answer.final_response

    extractor = ClaudeCodeSession(
        cwd=str(EXTRACTOR_DIR), name="extractor",
        model=args.extractor_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript,
        log_dir=str(LOG_DIR),
    )
    triage = ClaudeCodeSession(
        cwd=str(TRIAGE_DIR), name="triage",
        model=args.triage_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript,
        log_dir=str(LOG_DIR),
    )
    verifier = MadAgentsSession(
        cwd=str(VERIFIER_DIR), name="verifier",
        model=args.model, permission_mode="default",
        setting_sources=["project", "local"], transcript=transcript,
        log_dir=str(LOG_DIR),
    )
    remember = ClaudeCodeSession(
        cwd=str(REMEMBER_DIR), name="remember",
        model=args.remember_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript,
        log_dir=str(LOG_DIR),
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
    print(f"  Verified: {n_correct} correct, {n_incorrect} incorrect ({len(claims)} claims)")

    # ══════════════════════════════════════════════════════════════
    #  Phase 3: Grade
    # ══════════════════════════════════════════════════════════════
    print("\n--- Phase: Grade ---")

    grader = ClaudeCodeSession(
        cwd=str(GRADER_DIR), name="grader",
        model=args.grader_model, permission_mode="default",
        setting_sources=["local"], transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    grade_dir = WORK_DIR / "grade"
    grade_dir.mkdir(parents=True, exist_ok=True)
    verdicts_path = verification_dir / "verdicts.json"
    grade_path = grade_dir / GRADE_FILENAME

    grade = await run_grading(
        question_text=question_text,
        verdicts=verdicts,
        session=grader,
        verdicts_path=verdicts_path,
        output_path=grade_path,
    )

    grade_name = grade.get("grade", "?")
    tags = grade.get("tags", [])
    tags_str = f" [{', '.join(tags)}]" if tags else ""
    print(f"\n  Grade: {grade_name}{tags_str}")
    print(f"  {grade.get('explanation', '')}")

    # Write transcripts.
    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return grade


def main():
    parser = argparse.ArgumentParser(
        description="Re-evaluate with improved docs: answer + verify + grade",
    )
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model for answerer and verifier (default: sonnet)")
    parser.add_argument("--supervisor-model", type=str, default="haiku",
                        help="Model for the supervisor (default: haiku)")
    parser.add_argument("--extractor-model", type=str, default="haiku",
                        help="Model for claim extraction (default: haiku)")
    parser.add_argument("--triage-model", type=str, default="haiku",
                        help="Model for triage (default: haiku)")
    parser.add_argument("--remember-model", type=str, default="haiku",
                        help="Model for remember (default: haiku)")
    parser.add_argument("--grader-model", type=str, default="haiku",
                        help="Model for grading (default: haiku)")
    parser.add_argument("--max-turns", type=int, default=3,
                        help="Max answer turns (default: 3)")
    args = parser.parse_args()

    asyncio.run(run(args))

    print(f"\n  Output: {WORK_DIR}")


if __name__ == "__main__":
    main()
