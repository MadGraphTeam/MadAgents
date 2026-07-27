#!/usr/bin/env python3
"""Generate evaluation questions using Claude Code inside a container.

Designed to run inside an Apptainer container started by run.sh.
The container provides /output (with .git marker and settings.local.json)
and /src on PYTHONPATH.

Usage (via run.sh):
    ./eval/examples/1_generate/run.sh -n 3
    ./eval/examples/1_generate/run.sh -n 2 --focus "jet matching"
    ./eval/examples/1_generate/run.sh --model haiku -n 5
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure /src is on PYTHONPATH (for container use).
_src = Path("/src")
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from eval.generate import QUESTIONS_FILENAME, generate_questions
from eval.session import ClaudeCodeSession
from eval.transcript import write_summary, write_transcript, write_workflow

# run.sh sets --pwd /output and stages .git + settings.local.json there.
WORK_DIR = Path("/output")
OUTPUT_FILE = WORK_DIR / QUESTIONS_FILENAME
LOG_DIR = WORK_DIR / "logs"


async def run(args: argparse.Namespace) -> list[dict]:
    session = ClaudeCodeSession(
        cwd=str(WORK_DIR),
        name="generator",
        model=args.model,
        permission_mode="default",
        setting_sources=["local"],
        log_dir=str(LOG_DIR),
    )

    questions = await generate_questions(
        num_questions=args.n,
        session=session,
        output_path=OUTPUT_FILE,
        focus=args.focus,
        requirements=args.requirements,
        prompts_dir=args.prompts_dir,
    )

    # Write transcripts.
    write_transcript(session.transcript, WORK_DIR / "transcripts" / "full.json")
    write_summary(session.transcript, WORK_DIR / "transcripts" / "summary.txt")
    write_workflow(session.transcript, WORK_DIR / "transcripts" / "workflow")

    return questions


def main():
    parser = argparse.ArgumentParser(
        description="Generate evaluation questions via Claude Code",
    )
    parser.add_argument("-n", type=int, default=3, help="Number of questions (default: 3)")
    parser.add_argument("--focus", type=str, default="", help="Topic focus for generation")
    parser.add_argument("--requirements", type=str, default="",
                        help="Additional requirements (e.g. difficulty, question style)")
    parser.add_argument("--model", type=str, default="sonnet", help="Model override (default: sonnet)")
    parser.add_argument("--prompts-dir", type=str, default=None,
                        help="Custom prompts directory (initial.md, retry.md, etc.)")
    args = parser.parse_args()

    questions = asyncio.run(run(args))

    if questions:
        print(f"\n{'=' * 60}")
        print(f"  Output: {OUTPUT_FILE}")
        print(f"{'=' * 60}\n")
        for q in questions:
            print(f"  - {q['text']}")
            ref = q.get("reference_answer", "")
            if ref:
                preview = (ref[:80] + "...") if len(ref) > 80 else ref
                print(f"    -> {preview}")
            print()
    else:
        print("\nNo questions produced.")


if __name__ == "__main__":
    main()
