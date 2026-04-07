"""Reuse questions from previous eval runs."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def reuse_questions(
    run_dir: Path,
    reuse_specs: list[str],
    *,
    runs_dir: Path | None = None,
) -> None:
    """Append reused questions from previous runs to ``questions.jsonl``.

    Each entry in *reuse_specs* is either a bare timestamp (reuse all
    questions from that run) or ``TIMESTAMP:q001,q003`` (cherry-pick).

    Args:
        run_dir: Current run directory containing ``questions.jsonl``.
        reuse_specs: List of reuse specifications.
        runs_dir: Base directory containing all timestamped runs.
            Defaults to ``run_dir.parent``.
    """
    if runs_dir is None:
        runs_dir = run_dir.parent

    out = run_dir / "questions.jsonl"
    existing: list[dict] = []
    if out.exists():
        for line in out.read_text().splitlines():
            line = line.strip()
            if line:
                existing.append(json.loads(line))

    reused: list[dict] = []
    for spec in reuse_specs:
        if ":" in spec:
            ts, ids_str = spec.split(":", 1)
            pick_ids = set(ids_str.split(","))
        else:
            ts = spec
            pick_ids = None

        qfile = runs_dir / ts / "questions.jsonl"
        if not qfile.exists():
            print(f"ERROR: {qfile} not found.", file=sys.stderr)
            raise FileNotFoundError(str(qfile))

        count = 0
        for line in qfile.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)
            if pick_ids is None or q.get("id") in pick_ids:
                reused.append(q)
                count += 1

        if pick_ids:
            found = {q["id"] for q in reused}
            missing = pick_ids - found
            if missing:
                print(f"WARNING: question(s) {','.join(sorted(missing))} not found in run {ts}")
            print(f"Picked {count} question(s) from run {ts}")
        else:
            print(f"Reused {count} question(s) from run {ts}")

    if not existing and not reused:
        raise RuntimeError("No questions from generation or --reuse-from.")

    all_questions = existing + reused
    for i, q in enumerate(all_questions, start=1):
        q["id"] = f"q{i:03d}"

    with open(out, "w") as f:
        for q in all_questions:
            f.write(json.dumps(q) + "\n")

    print(f"Total: {len(all_questions)} question(s) ({len(existing)} generated + {len(reused)} reused)")
