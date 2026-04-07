"""Deduplication of questions against prior eval runs."""
from __future__ import annotations

import json
from pathlib import Path


MAX_DEDUP_QUESTIONS = 300


def load_previous_run_questions(
    runs_dir: Path,
    mode: str,
    current_timestamp: str,
    *,
    max_questions: int = MAX_DEDUP_QUESTIONS,
) -> list[str]:
    """Collect question texts from previous runs for deduplication.

    Args:
        runs_dir: Directory containing timestamped run subdirectories.
        mode: ``"latest"`` (most recent run only) or ``"all"``.
        current_timestamp: Timestamp of the current run (excluded).
        max_questions: Cap on the number of texts returned.

    Returns:
        List of question text strings (up to *max_questions*).
    """
    if not runs_dir.exists():
        return []

    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name != current_timestamp],
        key=lambda d: d.name,
        reverse=True,
    )
    if not run_dirs:
        return []
    if mode == "latest":
        run_dirs = run_dirs[:1]

    texts: list[str] = []
    for rd in run_dirs:
        qfile = rd / "questions.jsonl"
        if not qfile.exists():
            continue
        for line in qfile.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
                text = q.get("text", "").strip()
                if text:
                    texts.append(text)
            except json.JSONDecodeError:
                continue
        if len(texts) >= max_questions:
            break
    return texts[:max_questions]
