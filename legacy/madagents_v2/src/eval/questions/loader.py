"""Load questions from JSONL files."""
from __future__ import annotations

import json
from pathlib import Path


def load_questions_jsonl(path: Path) -> list[dict]:
    """Load questions from a JSONL file.

    Each line should be a JSON object with at least a ``text`` key.
    Returns an empty list if the file does not exist.
    """
    if not path.exists():
        return []
    questions = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            questions.append(json.loads(line))
    return questions
