#!/usr/bin/env python3
"""Verify an agent's answer by extracting and checking claims.

Designed to run inside an Apptainer container started by run.sh.
The container provides:
- /output — copy of the answer phase output (read-write, with overlay)
- /workspace — fresh scratch space
- /src on PYTHONPATH
- /input/results.json — the answer phase result
- /db/claim_db.json — persistent claim database (read-write)

Three sessions run in the same container:
- Extractor (ClaudeCodeSession) — splits the answer into claims
- Triage (ClaudeCodeSession) — matches claims against known database
- Verifier (MadAgentsSession) — verifies each claim using tools
- Remember (ClaudeCodeSession) — selects new claims to cache

Usage (via run.sh):
    ./eval/examples/3_verify/run.sh
    ./eval/examples/3_verify/run.sh --model sonnet
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

from eval.session import ClaudeCodeSession, MadAgentsSession
from eval.transcript import write_summary, write_transcript, write_workflow
from eval.verify import run_verification

WORK_DIR = Path("/output")
RESULTS_FILE = Path("/input/results.json")
VERIFICATION_DIR = WORK_DIR / "verification"
TRANSCRIPTS_DIR = WORK_DIR / "transcripts"
LOG_DIR = WORK_DIR / "logs"
DB_PATH = Path("/db/claim_db.json")

# Each session gets its own workdir for .claude/ isolation.
EXTRACTOR_DIR = Path("/session_extractor")
TRIAGE_DIR = Path("/session_triage")
VERIFIER_DIR = Path("/session_verifier")
REMEMBER_DIR = Path("/session_remember")


async def run(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    if not RESULTS_FILE.exists():
        print(f"ERROR: Results file not found: {RESULTS_FILE}")
        print("Run the answer phase first:  ./eval/examples/2_answer/run.sh")
        sys.exit(1)

    result = json.loads(RESULTS_FILE.read_text())
    question_text = result["question"]

    # Use all user-facing messages if available, otherwise fall back to final_response.
    all_messages = result.get("all_messages", [])
    if all_messages:
        agent_response = "\n\n".join(all_messages)
    else:
        agent_response = result["final_response"]

    print(f"\n{'=' * 60}")
    print(f"  Verifying: {question_text[:80]}...")
    print(f"{'=' * 60}\n")

    transcript = []

    # Extractor: bare Claude Code — just text analysis.
    extractor = ClaudeCodeSession(
        cwd=str(EXTRACTOR_DIR),
        name="extractor",
        model=args.extractor_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    # Triage: bare Claude Code — reads files, outputs mapping.
    triage = ClaudeCodeSession(
        cwd=str(TRIAGE_DIR),
        name="triage",
        model=args.triage_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    # Verifier: full MadAgents — needs agents for code execution,
    # source inspection, physics reasoning.
    verifier = MadAgentsSession(
        cwd=str(VERIFIER_DIR),
        name="verifier",
        model=args.model,
        permission_mode="default",
        setting_sources=["project", "local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    # Remember: bare Claude Code — selects new claims to cache.
    remember = ClaudeCodeSession(
        cwd=str(REMEMBER_DIR),
        name="remember",
        model=args.remember_model,
        permission_mode="default",
        setting_sources=["local"],
        transcript=transcript,
        log_dir=str(LOG_DIR),
    )

    claims, verdicts = await run_verification(
        question_text=question_text,
        agent_response=agent_response,
        extractor_session=extractor,
        triage_session=triage,
        verifier_session=verifier,
        remember_session=remember,
        output_dir=VERIFICATION_DIR,
        db_path=DB_PATH,
    )

    # Summary.
    n_correct = sum(1 for v in verdicts if v.get("correct") is True)
    n_incorrect = sum(1 for v in verdicts if v.get("correct") is False)
    n_inconclusive = sum(1 for v in verdicts if v.get("correct") is None)

    print(f"\n{'=' * 60}")
    print(f"  Claims: {len(claims)}")
    print(f"  Verdicts: {n_correct} correct, {n_incorrect} incorrect, "
          f"{n_inconclusive} inconclusive")
    print(f"{'=' * 60}\n")

    for v in verdicts:
        status = "+" if v.get("correct") is True else ("-" if v.get("correct") is False else "?")
        claim = v.get("claim", "")[:70]
        print(f"  {status} {claim}...")

    # Write transcripts.
    write_transcript(transcript, TRANSCRIPTS_DIR / "full.json")
    write_summary(transcript, TRANSCRIPTS_DIR / "summary.txt")
    write_workflow(transcript, TRANSCRIPTS_DIR / "workflow")

    return claims, verdicts


def main():
    parser = argparse.ArgumentParser(
        description="Verify an agent's answer by extracting and checking claims",
    )
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Model for the verifier (default: sonnet)")
    parser.add_argument("--extractor-model", type=str, default="haiku",
                        help="Model for claim extraction (default: haiku)")
    parser.add_argument("--triage-model", type=str, default="haiku",
                        help="Model for triage matching (default: haiku)")
    parser.add_argument("--remember-model", type=str, default="haiku",
                        help="Model for remember selection (default: haiku)")
    args = parser.parse_args()

    claims, verdicts = asyncio.run(run(args))

    if verdicts:
        print(f"\n  Output: {VERIFICATION_DIR}")
    else:
        print("\nNo verdicts produced.")


if __name__ == "__main__":
    main()
