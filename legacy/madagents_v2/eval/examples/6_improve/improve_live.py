#!/usr/bin/env python3
"""Apply and verify documentation improvements.

Designed to run inside an Apptainer container started by run.sh.
The container provides:
- /output — copy of diagnose phase output
- /madgraph_docs — original docs (read-only)
- /docs_working — writable working copy of docs
- /src on PYTHONPATH
- /db/claim_db.json — persistent claim database (read-only during run)

Four sessions:
- Improver (ClaudeCodeSession) — improves/revises doc edits
- Fact verifier (MadAgentsSession) — verifies claims and code blocks
- Style checker (ClaudeCodeSession) — checks formatting/style
- Quality checker (ClaudeCodeSession) — checks structure/appropriateness

Usage (via run.sh):
    ./eval/examples/6_improve/run.sh
    ./eval/examples/6_improve/run.sh --model sonnet --max-rounds 5
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure /src is on PYTHONPATH (for container use).
_src = Path("/src")
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from eval.improve import run_improve
from eval.session import ClaudeCodeSession, MadAgentsSession
from eval.transcript import write_summary, write_transcript, write_workflow

WORK_DIR = Path("/output")
DIAGNOSES_PATH = WORK_DIR / "diagnose" / "diagnoses.json"
VERDICTS_PATH = WORK_DIR / "verification" / "verdicts.json"
QUESTIONS_FILE = Path("/input/questions.json")
DOCS_SOURCE = Path("/docs_source")   # madgraph/ docs + madgraph_overview.md
DOCS_WORKING = Path("/docs_working")  # writable copy for editing
IMPROVE_DIR = WORK_DIR / "improve"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
LOG_DIR = WORK_DIR / "logs"
DB_PATH = Path("/db/claim_db.json")

# Session workdirs.
IMPROVER_DIR = Path("/session_improver")
VERIFIER_DIR = Path("/session_verifier")
STYLE_DIR = Path("/session_style")
QUALITY_DIR = Path("/session_quality")


async def run(args: argparse.Namespace) -> dict:
    if not DIAGNOSES_PATH.exists():
        print(f"ERROR: Diagnoses not found: {DIAGNOSES_PATH}")
        print("Run the diagnose phase first:  ./eval/examples/5_diagnose/run.sh")
        sys.exit(1)

    diagnoses = json.loads(DIAGNOSES_PATH.read_text())
    total_findings = sum(len(v) for v in diagnoses.values())

    if total_findings == 0:
        print("No diagnoses to apply — nothing to improve.")
        return {"approved": True, "rounds": []}

    print(f"\n{'=' * 60}")
    print(f"  Improving docs: {total_findings} findings to apply")
    print(f"{'=' * 60}\n")

    # Load initial claims from verify phase.
    initial_claims = []
    if VERDICTS_PATH.exists():
        verdicts = json.loads(VERDICTS_PATH.read_text())
        initial_claims = [v for v in verdicts if v.get("correct") is not None]

    # Load reference answers (unverified) for the improver.
    ref_answers = None
    if QUESTIONS_FILE.exists():
        questions = json.loads(QUESTIONS_FILE.read_text())
        ref_answers = [
            {"question": q["text"], "reference_answer": q.get("reference_answer", "")}
            for q in questions if q.get("reference_answer")
        ] or None

    transcript = []

    improver = ClaudeCodeSession(
        cwd=str(IMPROVER_DIR),
        name="improver",
        model=args.model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    fact_verifier = MadAgentsSession(
        cwd=str(VERIFIER_DIR),
        name="fact_verifier",
        model=args.model,
        permission_mode="default",
        setting_sources=["project", "local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    style_checker = ClaudeCodeSession(
        cwd=str(STYLE_DIR),
        name="style_checker",
        model=args.check_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    quality_checker = ClaudeCodeSession(
        cwd=str(QUALITY_DIR),
        name="quality_checker",
        model=args.check_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    summary = await run_improve(
        diagnoses_path=DIAGNOSES_PATH,
        docs_source_dir=DOCS_SOURCE,
        docs_working_dir=DOCS_WORKING,
        output_dir=IMPROVE_DIR,
        improver_session=improver,
        fact_verifier_session=fact_verifier,
        style_session=style_checker,
        quality_session=quality_checker,
        initial_claims=initial_claims,
        db_path=DB_PATH,
        max_rounds=args.max_rounds,
        reference_answers=ref_answers,
    )

    # Summary.
    print(f"\n{'=' * 60}")
    print(f"  Rounds: {len(summary.get('rounds', []))}")
    print(f"  Approved: {summary.get('approved', False)}")
    if summary.get("final_changes"):
        print(f"  Changed files:")
        for f in summary["final_changes"]:
            print(f"    - {f}")
    print(f"{'=' * 60}\n")

    # Write transcripts.
    write_transcript(transcript, TRANSCRIPTS_DIR / "improve_full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "improve_summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Apply and verify documentation improvements",
    )
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model for improver and fact verifier (default: sonnet)")
    parser.add_argument("--check-model", type=str, default="haiku",
                        help="Model for style/quality checks (default: haiku)")
    parser.add_argument("--max-rounds", type=int, default=10,
                        help="Maximum revision rounds (default: 10)")
    args = parser.parse_args()

    summary = asyncio.run(run(args))

    if summary.get("approved"):
        print(f"  Approved changes at: {DOCS_WORKING}")
    else:
        print(f"  Changes not fully approved after {len(summary.get('rounds', []))} rounds.")
    print(f"  Summary: {IMPROVE_DIR / 'improve_summary.json'}")


if __name__ == "__main__":
    main()
