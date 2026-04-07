#!/usr/bin/env python3
"""Grade an agent's answer based on verification verdicts.

Designed to run inside an Apptainer container started by run.sh.
The container provides:
- /output — copy of the verify phase output
- /src on PYTHONPATH
- /input/results.json — the answer phase result

One session:
- Grader (ClaudeCodeSession) — classifies the answer quality

Usage (via run.sh):
    ./eval/examples/4_grade/run.sh
    ./eval/examples/4_grade/run.sh --model haiku
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

from eval.grade import GRADE_FILENAME, run_grading
from eval.session import ClaudeCodeSession
from eval.transcript import write_summary, write_transcript, write_workflow

WORK_DIR = Path("/output")
RESULTS_FILE = Path("/input/results.json")
VERDICTS_PATH = WORK_DIR / "verification" / "verdicts.json"
WORKFLOW_DIR = WORK_DIR / "transcripts" / "workflow"
GRADE_DIR = WORK_DIR / "grade"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
LOG_DIR = WORK_DIR / "logs"

GRADER_DIR = Path("/session_grader")


def _find_workflow() -> Path | None:
    """Find the answerer workflow file."""
    if not WORKFLOW_DIR.is_dir():
        return None
    # Prefer 'answerer.json', fall back to first file found.
    answerer = WORKFLOW_DIR / "answerer.json"
    if answerer.exists():
        return answerer
    files = sorted(WORKFLOW_DIR.glob("*.json"))
    return files[0] if files else None


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
    verdicts = json.loads(VERDICTS_PATH.read_text())
    question_text = result["question"]

    n_correct = sum(1 for v in verdicts if v.get("correct") is True)
    n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)

    print(f"\n{'=' * 60}")
    print(f"  Grading: {question_text[:80]}...")
    print(f"  Verdicts: {n_correct} correct, {n_incorrect} incorrect "
          f"({len(verdicts)} total)")
    print(f"{'=' * 60}\n")

    transcript = []

    grader = ClaudeCodeSession(
        cwd=str(GRADER_DIR),
        name="grader",
        model=args.model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    GRADE_DIR.mkdir(parents=True, exist_ok=True)
    grade_path = GRADE_DIR / GRADE_FILENAME

    grade = await run_grading(
        question_text=question_text,
        verdicts=verdicts,
        session=grader,
        verdicts_path=VERDICTS_PATH,
        output_path=grade_path,
        transcript_path=_find_workflow(),
    )

    grade_name = grade.get("grade", "?")
    tags = grade.get("tags", [])
    tags_str = f" [{', '.join(tags)}]" if tags else ""

    print(f"\n{'=' * 60}")
    print(f"  Grade: {grade_name}{tags_str}")
    print(f"  {grade.get('explanation', '')}")
    print(f"{'=' * 60}\n")

    # Write transcripts.
    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return grade


def main():
    parser = argparse.ArgumentParser(
        description="Grade an agent's answer based on verification verdicts",
    )
    parser.add_argument("--model", type=str, default="haiku",
                        help="Model for the grader (default: haiku)")
    args = parser.parse_args()

    grade = asyncio.run(run(args))

    if grade:
        print(f"  Output: {GRADE_DIR / GRADE_FILENAME}")
    else:
        print("\nNo grade produced.")


if __name__ == "__main__":
    main()
