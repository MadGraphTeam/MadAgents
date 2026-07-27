#!/usr/bin/env python3
"""Run the answer evaluation loop using Claude Code inside a container.

Designed to run inside an Apptainer container started by run.sh.
The container provides /output for results, /src on PYTHONPATH, and
/input/questions.json.  Each session type creates its own .claude/
directory from the assets in /src/claude_code/.

Usage (via run.sh):
    ./eval/examples/2_answer/run.sh
    ./eval/examples/2_answer/run.sh --model haiku --max-turns 2
    ./eval/examples/2_answer/run.sh --questions path/to/questions.json
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

from eval.answer import run_answer_loop
from eval.session import ClaudeCodeSession, MadAgentsSession
from eval.transcript import write_summary, write_transcript, write_workflow

WORK_DIR = Path("/output")
QUESTIONS_FILE = Path("/input/questions.json")
OUTPUT_FILE = WORK_DIR / "results.json"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
LOG_DIR = WORK_DIR / "logs"

# Grader gets its own workdir so its bare .claude/ doesn't conflict
# with the MadAgents .claude/ (CLAUDE.md + agents) at /output.
SUPERVISOR_DIR = Path("/session_supervisor")


async def run(args: argparse.Namespace) -> dict:
    # Load and select question.
    if not QUESTIONS_FILE.exists():
        print(f"ERROR: Questions file not found: {QUESTIONS_FILE}")
        print("Generate questions first:  ./eval/examples/1_generate/run.sh")
        sys.exit(1)

    questions = json.loads(QUESTIONS_FILE.read_text())
    idx = args.index

    if idx < 0 or idx >= len(questions):
        print(f"ERROR: Question index {idx} out of range "
              f"(file has {len(questions)} questions, indices 0-{len(questions) - 1}).")
        print(f"Try:  ./eval/examples/2_answer/run.sh --index <0-{len(questions) - 1}>")
        sys.exit(1)

    q = questions[idx]
    text = q["text"]
    print(f"\n{'=' * 60}")
    print(f"  Question {idx}: {text[:80]}...")
    print(f"{'=' * 60}\n")

    transcript = []

    # Answerer: full MadAgents orchestrator (the system under test).
    session = MadAgentsSession(
        cwd=str(WORK_DIR),
        name="answerer",
        model=args.model,
        permission_mode="default",
        setting_sources=["project", "local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )
    # Supervisor: bare Claude Code, writes verdict files.
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
        question_text=text,
        session=session,
        supervisor=supervisor,
        output_dir=supervision_dir,
        max_turns=args.max_turns,
    )

    result = {
        "question": text,
        "question_index": idx,
        "final_response": answer.final_response,
        "final_category": answer.final_category,
        "num_turns": len(answer.turns),
        "all_messages": session.messages,  # all user-facing text from the answerer
        "turns": [
            {
                "user_prompt": t.user_prompt,
                "response": t.response,
                "category": t.category,
            }
            for t in answer.turns
        ],
    }

    print(f"\n  -> Category: {answer.final_category} ({len(answer.turns)} turn(s))")
    preview = answer.final_response[:120].replace("\n", " ")
    print(f"  -> Response: {preview}...")

    # Write result and transcript.
    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run answer evaluation loop via Claude Code",
    )
    parser.add_argument("--index", "-i", type=int, default=0,
                        help="Question index to answer (default: 0)")
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model override for the answerer (default: sonnet)")
    parser.add_argument("--supervisor-model", type=str, default="haiku",
                        help="Model for the supervisor (default: haiku)")
    parser.add_argument("--max-turns", type=int, default=3,
                        help="Max answer+supervise turns per question (default: 3)")
    args = parser.parse_args()

    result = asyncio.run(run(args))

    print(f"\n{'=' * 60}")
    print(f"  Results: {OUTPUT_FILE}")
    print(f"{'=' * 60}\n")
    cat = result["final_category"]
    turns = result["num_turns"]
    q = result["question"][:70]
    print(f"  [{cat}] ({turns}t) {q}...")


if __name__ == "__main__":
    main()
