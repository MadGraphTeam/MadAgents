"""Persistent claim database for caching verification results.

Designed for concurrent use: the main database file (``claim_db.json``)
is read-only during parallel verification runs.  Each run writes its
results to separate staging files (``new_claims_<run_id>.json``,
``bumps_<run_id>.json``).  After all runs complete, :func:`merge_db`
consolidates staging files into the database.

This avoids file locking issues on NFS filesystems.

Typical usage::

    # At the start of a run (read-only snapshot).
    db = load_db(db_path)
    simplified = simplify_for_triage(db)

    # During the run — write to staging files.
    write_bumps(staging_dir, run_id, bumped_ids)
    write_new_claims(staging_dir, run_id, new_claims)

    # After ALL parallel runs complete — single merge.
    merge_db(db_path, staging_dir)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════
#  Read operations (safe for concurrent access)
# ═══════════════════════════════════════════════════════════════════════

def load_db(path: Path) -> list[dict]:
    """Load the claim database from a JSON file.

    Returns an empty list if the file doesn't exist.
    """
    if not path.exists():
        return []
    return json.loads(path.read_text())


def simplify_for_triage(entries: list[dict]) -> list[dict]:
    """Create a simplified view for the triage session.

    Returns only ``id``, ``claim``, and ``correct`` fields.
    """
    return [
        {"id": e["id"], "claim": e["claim"], "correct": e["correct"]}
        for e in entries
        if "id" in e and "claim" in e and "correct" in e
    ]


def get_entries_by_ids(entries: list[dict], ids: set[int]) -> list[dict]:
    """Return full entries for the given IDs."""
    return [e for e in entries if e.get("id") in ids]


# ═══════════════════════════════════════════════════════════════════════
#  Staging operations (per-run, no shared state)
# ═══════════════════════════════════════════════════════════════════════

def write_bumps(staging_dir: Path, run_id: str, ids: set[int]) -> None:
    """Write bumped IDs to a staging file for later merge."""
    if not ids:
        return
    staging_dir.mkdir(parents=True, exist_ok=True)
    path = staging_dir / f"bumps_{run_id}.json"
    path.write_text(json.dumps(sorted(ids)))


def write_new_claims(staging_dir: Path, run_id: str, claims: list[dict]) -> None:
    """Write new claims to a staging file for later merge."""
    if not claims:
        return
    staging_dir.mkdir(parents=True, exist_ok=True)
    path = staging_dir / f"new_claims_{run_id}.json"
    path.write_text(json.dumps(claims, indent=2))


# ═══════════════════════════════════════════════════════════════════════
#  Merge (single-writer, after all parallel runs)
# ═══════════════════════════════════════════════════════════════════════

def _next_id(entries: list[dict]) -> int:
    """Return the next available ID."""
    if not entries:
        return 1
    return max(e.get("id", 0) for e in entries) + 1


def _sort_db(entries: list[dict]) -> None:
    """Sort in place by (count desc, date desc)."""
    entries.sort(key=lambda e: (-e.get("count", 0), e.get("date", "")))


def merge_db(db_path: Path, staging_dir: Path) -> list[dict]:
    """Merge all staging files into the database.

    Reads all ``bumps_*.json`` and ``new_claims_*.json`` from
    *staging_dir*, applies them to the database, saves, and cleans
    up staging files.

    Args:
        db_path: Path to the main database file.
        staging_dir: Directory containing staging files.

    Returns:
        The updated database entries.
    """
    db = load_db(db_path)

    # Aggregate bump counts per ID (one bump per run that selected it).
    bump_counts: dict[int, int] = {}
    for bump_file in staging_dir.glob("bumps_*.json"):
        ids = json.loads(bump_file.read_text())
        for id_ in ids:
            bump_counts[id_] = bump_counts.get(id_, 0) + 1
        bump_file.unlink()

    # Apply bumps.
    if bump_counts:
        for e in db:
            eid = e.get("id")
            if eid in bump_counts:
                e["count"] = e.get("count", 0) + bump_counts[eid]

    # Aggregate all new claims.
    all_new: list[dict] = []
    for claims_file in sorted(staging_dir.glob("new_claims_*.json")):
        claims = json.loads(claims_file.read_text())
        all_new.extend(claims)
        claims_file.unlink()

    # Append new claims with IDs, skipping exact duplicates.
    if all_new:
        existing_claims = {e.get("claim", "").strip() for e in db}
        nid = _next_id(db)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        n_skipped = 0

        for c in all_new:
            claim_text = c.get("claim", "").strip()
            if claim_text in existing_claims:
                n_skipped += 1
                continue
            existing_claims.add(claim_text)
            db.append({
                "id": nid,
                "claim": claim_text,
                "correct": c.get("correct"),
                "method": c.get("method", ""),
                "evidence": c.get("evidence", []),
                "explanation": c.get("explanation", ""),
                "count": 0,
                "date": today,
            })
            nid += 1

        if n_skipped:
            print(f"  Skipped {n_skipped} duplicate claims.")

    # Sort and save.
    _sort_db(db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text(json.dumps(db, indent=2))

    # Clean up empty staging dir.
    try:
        staging_dir.rmdir()
    except OSError:
        pass  # Not empty — other files present.

    return db
