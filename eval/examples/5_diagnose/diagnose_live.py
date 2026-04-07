#!/usr/bin/env python3
"""Diagnose documentation issues from verification and reviewer errors.

Designed to run inside an Apptainer container started by run.sh.
The container provides:
- /output — copy of verify/grade phase output
- /src on PYTHONPATH
- /input/results.json — the answer phase result
- /madgraph_docs — MadGraph documentation (read-only)

One session:
- Diagnoser (ClaudeCodeSession) — reads verdicts, transcript, and docs

Usage (via run.sh):
    ./eval/examples/5_diagnose/run.sh
    ./eval/examples/5_diagnose/run.sh --model sonnet
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

from eval.diagnose import DIAGNOSE_FILENAME, run_diagnose
from eval.session import ClaudeCodeSession
from eval.transcript import write_summary, write_transcript, write_workflow

WORK_DIR = Path("/output")
RESULTS_FILE = Path("/input/results.json")
VERDICTS_PATH = WORK_DIR / "verification" / "verdicts.json"
GRADE_PATH = WORK_DIR / "grade" / "grade.json"
TRANSCRIPT_PATH = WORK_DIR / "transcripts" / "full.json"
WORKFLOW_DIR = WORK_DIR / "transcripts" / "workflow"
DIAGNOSE_DIR = WORK_DIR / "diagnose"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
LOG_DIR = WORK_DIR / "logs"

DIAGNOSER_DIR = Path("/session_diagnoser")


async def run(args: argparse.Namespace) -> dict:
    if not RESULTS_FILE.exists():
        print(f"ERROR: Results file not found: {RESULTS_FILE}")
        print("Run the answer phase first:  ./eval/examples/2_answer/run.sh")
        sys.exit(1)

    if not VERDICTS_PATH.exists():
        print(f"ERROR: Verdicts not found: {VERDICTS_PATH}")
        print("Run the verify phase first:  ./eval/examples/3_verify/run.sh")
        sys.exit(1)

    result = json.loads(RESULTS_FILE.read_text())
    question_text = result["question"]

    # Load grade if available (from phase 4).
    grade = None
    if GRADE_PATH.exists():
        grade = json.loads(GRADE_PATH.read_text())

    # Find best transcript: prefer workflow/answerer.json over full.json.
    transcript_path = TRANSCRIPT_PATH
    if WORKFLOW_DIR.is_dir():
        answerer_wf = WORKFLOW_DIR / "answerer.json"
        if answerer_wf.exists():
            transcript_path = answerer_wf

    # Count errors for display.
    verdicts = json.loads(VERDICTS_PATH.read_text())
    n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)

    grade_name = grade.get("grade", "?") if grade else "n/a"
    grade_tags = grade.get("tags", []) if grade else []
    tags_str = f" [{', '.join(grade_tags)}]" if grade_tags else ""

    print(f"\n{'=' * 60}")
    print(f"  Diagnosing: {question_text[:80]}...")
    print(f"  Incorrect claims: {n_incorrect}")
    print(f"  Grade: {grade_name}{tags_str}")
    print(f"{'=' * 60}\n")

    transcript = []

    diagnoser = ClaudeCodeSession(
        cwd=str(DIAGNOSER_DIR),
        name="diagnoser",
        model=args.model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    DIAGNOSE_DIR.mkdir(parents=True, exist_ok=True)
    diagnose_path = DIAGNOSE_DIR / DIAGNOSE_FILENAME

    diagnoses = await run_diagnose(
        question_text=question_text,
        session=diagnoser,
        verdicts_path=VERDICTS_PATH,
        transcript_path=transcript_path,
        output_path=diagnose_path,
        grade=grade,
    )

    # Summary.
    print(f"\n{'=' * 60}")
    total = sum(len(v) for v in diagnoses.values()) if diagnoses else 0
    print(f"  Findings: {total}")
    for cat, findings in (diagnoses or {}).items():
        if findings:
            print(f"\n  [{cat}]")
            for f in findings:
                print(f"    Problem: {f.get('problem', '')[:80]}")
                print(f"    Fix:   {f.get('recommendation', '')[:80]}")
    print(f"{'=' * 60}\n")

    # Write transcripts.
    write_transcript(transcript, TRANSCRIPTS_DIR / "diagnose_full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "diagnose_summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return diagnoses


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose documentation issues from verification errors",
    )
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model for the diagnoser (default: sonnet)")
    args = parser.parse_args()

    diagnoses = asyncio.run(run(args))

    if diagnoses:
        print(f"  Output: {DIAGNOSE_DIR / DIAGNOSE_FILENAME}")
    else:
        print("\nNo diagnoses produced.")


if __name__ == "__main__":
    main()
