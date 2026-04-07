"""Configuration, path constants, and CLI argument parsing for the eval harness."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass, fields
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]       # AgentFitterDev/
EVAL_DIR = REPO_ROOT / "claude_code" / "eval"         # data lives here
DOCS_DIR = REPO_ROOT / "src/madagents/software_instructions/madgraph"
CLAUDE_CODE_DIR = REPO_ROOT / "claude_code"
IMAGE_PATH = EVAL_DIR / "base/madagents.sif"
BASE_OVERLAY = EVAL_DIR / "base/mad_overlay.img"
PROMPTS_DIR = EVAL_DIR / "prompts"

# Isolated working directory for headless SDK calls.
# A .git marker prevents Claude from walking up and loading the project CLAUDE.md.
# The directory is created lazily by ensure_tmp_dir() rather than at import time,
# so that importing config.py for its constants doesn't cause filesystem side effects.
EVAL_TMP_DIR = EVAL_DIR / ".tmp"


def ensure_tmp_dir() -> Path:
    """Create EVAL_TMP_DIR and its .git marker if they don't already exist.

    Called automatically before any SDK/subprocess call that uses EVAL_TMP_DIR.
    Safe to call multiple times (idempotent).
    """
    EVAL_TMP_DIR.mkdir(exist_ok=True)
    (EVAL_TMP_DIR / ".git").touch(exist_ok=True)
    return EVAL_TMP_DIR


# ── Outcome categories ─────────────────────────────────────────────────
CATEGORIES = [
    "SUCCESS",
    "SUCCESS_INEFFICIENT",
    "DOC_GAP",
    "DOC_CONFUSION",
    "PROMPT_ISSUE",
    "ORCHESTRATION_ISSUE",
    "SOFTWARE_ERROR",
    "QUESTION_AMBIGUITY",
    "UNVERIFIABLE",
    "GRADING_ERROR",
]


# ── RunConfig ──────────────────────────────────────────────────────────
@dataclass
class RunConfig:
    timestamp: str
    mode: str = "all"            # "all" | "new_only" | "failed_from:TIMESTAMP"
    max_parallel: int = 2        # concurrent evaluation containers
    delay_between: int = 10      # seconds between launches
    max_questions: int = 0       # 0 = all questions, >0 = limit to first N
    max_doc_revisions: int = 10  # max revision attempts per doc draft
    max_confirm_rounds: int = 3  # max effectiveness re-eval rounds per topic
    num_questions: int = 12      # total questions to generate (0=skip generation)
    include_manual_questions: bool = False
    question_focus: str = ""     # optional guidance for question generation
    dedup_from: str = ""         # "latest", "all", or empty


def load_config(run_dir: Path) -> RunConfig:
    """Load RunConfig from a run directory's config.json."""
    config_path = run_dir / "config.json"
    data = json.loads(config_path.read_text())
    valid_fields = {f.name for f in fields(RunConfig)}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return RunConfig(**filtered)


# ── Apptainer ──────────────────────────────────────────────────────────
def find_apptainer_bin() -> str:
    """Locate the apptainer binary using config.env or PATH."""
    config_path = REPO_ROOT / "config.env"
    apptainer_dir = ""
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("APPTAINER_DIR="):
                apptainer_dir = line.split("=", 1)[1].strip('"').strip("'")
                break

    if apptainer_dir:
        candidate = os.path.join(apptainer_dir.rstrip("/"), "apptainer")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    env_dir = os.environ.get("APPTAINER_DIR", "")
    if env_dir:
        candidate = os.path.join(env_dir.rstrip("/"), "apptainer")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    found = shutil.which("apptainer")
    if found:
        return found

    raise FileNotFoundError(
        "apptainer not found. Set APPTAINER_DIR in config.env or add apptainer to PATH."
    )


# ── CLI argument parsing ──────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments (replaces eval.sh argument parsing)."""
    parser = argparse.ArgumentParser(
        description="MadAgents self-evaluation pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python -m eval                                  # 12 questions (default)
  python -m eval -n 20                            # 20 questions
  python -m eval -n 20 --focus "NLO and matching" # 20 questions with focus
  python -m eval -n 0 --include-manual             # manual questions only
  python -m eval --parallel 4 --limit 10          # fast run
  python -m eval --continue 2026-03-01_120000     # resume
""",
    )

    g = parser.add_argument_group("Question generation")
    g.add_argument("-n", "--questions", type=int, default=None,
                   help="Total questions to generate (default: 12)")
    g.add_argument("--focus", type=str, default="",
                   help="Guidance string for question generation")
    g.add_argument("--include-manual", action="store_true",
                   help="Include the manually authored questions from the question bank")

    g = parser.add_argument_group("Evaluation")
    g.add_argument("--mode", type=str, default="all",
                   help="all | new_only | failed_from:TIMESTAMP")
    g.add_argument("--parallel", type=int, default=2,
                   help="Concurrent Apptainer containers (default: 2)")
    g.add_argument("--delay", type=int, default=10,
                   help="Seconds between container launches (default: 10)")
    g.add_argument("--limit", type=int, default=0,
                   help="Only evaluate first N questions (default: 0 = all)")

    g = parser.add_argument_group("Doc improvement")
    g.add_argument("--max-revisions", type=int, default=10,
                   help="Max revision attempts per doc draft (default: 10)")
    g.add_argument("--max-confirm-rounds", type=int, default=3,
                   help="Max effectiveness re-eval rounds (default: 3)")

    g = parser.add_argument_group("Deduplication & reuse")
    g.add_argument("--dedup-from", type=str, default="",
                   help="latest | all — avoid repeating old questions")
    g.add_argument("--reuse-from", type=str, action="append", default=[],
                   help="Reuse questions from previous run (TS or TS:q001,q003)")

    g = parser.add_argument_group("Resumption")
    g.add_argument("--continue", dest="continue_from", type=str, default="",
                   help="Continue an interrupted run from TIMESTAMP")
    g.add_argument("--auto-retry", type=int, default=6,
                   help="Auto-retry on transient errors (0=off, -1=unlimited)")

    return parser.parse_args(argv)


def create_run_config(args: argparse.Namespace, timestamp: str) -> RunConfig:
    """Create a RunConfig from parsed CLI args and a timestamp."""
    num_questions = args.questions if args.questions is not None else 12
    return RunConfig(
        timestamp=timestamp,
        mode=args.mode,
        max_parallel=args.parallel,
        delay_between=args.delay,
        max_questions=args.limit,
        max_doc_revisions=args.max_revisions,
        max_confirm_rounds=args.max_confirm_rounds,
        num_questions=num_questions,
        include_manual_questions=args.include_manual,
        question_focus=args.focus,
        dedup_from=args.dedup_from,
    )


def save_config(config: RunConfig, run_dir: Path) -> None:
    """Save RunConfig as config.json in the run directory."""
    config_path = run_dir / "config.json"
    data = {f.name: getattr(config, f.name) for f in fields(RunConfig)}
    config_path.write_text(json.dumps(data, indent=2))
