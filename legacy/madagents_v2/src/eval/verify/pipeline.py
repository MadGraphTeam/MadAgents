"""Full verification pipeline: extract → triage → verify → remember.

Composes all verification steps into a single async function.
Each step uses its own LangGraph internally.

Flow::

    1. extract_claims    — split answer into claims (haiku)
    2. triage            — match claims against known database (haiku)
    3. prepare           — programmatic: bump counts, write relevant_known_claims.json
    4. verify_claims     — verify each claim (MadAgents)
    5. remember          — ask verifier which claims to cache (follow-up call)
    6. update_db         — programmatic: append new claims to database
"""
from __future__ import annotations

import json
from pathlib import Path

from eval.session import QuerySession
from eval.verify.claim_db import (
    get_entries_by_ids,
    load_db,
    simplify_for_triage,
    write_bumps,
    write_new_claims,
)
from eval.verify.extractor import CLAIMS_FILENAME, extract_claims
from eval.verify.remember import REMEMBER_FILENAME, run_remember
from eval.verify.triage import TRIAGE_FILENAME, run_triage
from eval.verify.verifier import VERDICTS_FILENAME, verify_claims


KNOWN_CLAIMS_FILENAME = "known_claims.json"
RELEVANT_CLAIMS_FILENAME = "relevant_known_claims.json"


# ═══════════════════════════════════════════════════════════════════════
#  Full pipeline
# ═══════════════════════════════════════════════════════════════════════

async def run_verification(
    question_text: str,
    agent_response: str,
    extractor_session: QuerySession,
    triage_session: QuerySession,
    verifier_session: QuerySession,
    remember_session: QuerySession,
    output_dir: Path,
    *,
    run_id: str = "",
    db_path: Path | None = None,
    staging_dir: Path | None = None,
    prompts_dir: str | Path | None = None,
) -> tuple[list[dict], list[dict]]:
    """Run the full verification pipeline.

    Steps:
    1. Extract claims from the agent's answer (extractor, haiku).
    2. Triage: match claims against the known claims database (triage, haiku).
    3. Prepare: stage count bumps, write relevant known claims file.
    4. Verify: verify each claim with MadAgents (verifier, sonnet).
    5. Remember: select new claims worth caching (remember, haiku).
    6. Stage new claims for later merge.

    The database is **read-only** during this function.  Count bumps
    and new claims are written to *staging_dir* as separate files.
    Call :func:`eval.verify.claim_db.merge_db` after all parallel
    runs complete to consolidate.

    Args:
        question_text: The original question.
        agent_response: The agent's response to verify.
        extractor_session: Session for claim extraction (haiku).
        triage_session: Session for triage matching (haiku).
        verifier_session: Session for claim verification (MadAgents).
        remember_session: Session for selecting new claims (haiku).
        output_dir: Directory for output files.
        run_id: Unique identifier for this run (used for staging files).
        db_path: Path to the persistent claim database. If None,
            triage and remember steps are skipped.
        staging_dir: Directory for staging files (bumps, new claims).
            Defaults to ``output_dir / "staging"``.
        prompts_dir: Custom prompts directory.

    Returns:
        Tuple of ``(claims, verdicts)``.
    """
    _prompts_dir = Path(prompts_dir) if prompts_dir else None
    output_dir.mkdir(parents=True, exist_ok=True)

    if not run_id:
        import uuid
        run_id = uuid.uuid4().hex[:8]

    if staging_dir is None:
        staging_dir = output_dir / "staging"

    claims_path = output_dir / CLAIMS_FILENAME
    verdicts_path = output_dir / VERDICTS_FILENAME

    # ── Step 1: Extract claims ────────────────────────────────────────
    # Pass known claim texts so the extractor reuses wording for matching facts.
    _known_claim_texts = None
    if db_path is not None:
        db_snapshot = load_db(db_path)
        if db_snapshot:
            _known_claim_texts = [e["claim"] for e in db_snapshot if e.get("claim")]

    claims = await extract_claims(
        question_text=question_text,
        agent_response=agent_response,
        session=extractor_session,
        output_path=claims_path,
        known_claims=_known_claim_texts,
        prompts_dir=_prompts_dir,
    )

    if not claims:
        print("  No claims extracted — skipping verification.")
        return [], []

    # ── Step 2–3: Triage (if database exists) ─────────────────────────
    relevant_claims_path: Path | None = None

    if db_path is not None:
        db = load_db(db_path)

        if db:
            # Write simplified view for triage.
            known_claims_path = output_dir / KNOWN_CLAIMS_FILENAME
            known_claims_path.write_text(
                json.dumps(simplify_for_triage(db), indent=2)
            )

            valid_ids = {e["id"] for e in db}

            # Run triage — returns a flat list of relevant database IDs.
            triage_path = output_dir / TRIAGE_FILENAME
            selected_ids = await run_triage(
                claims_path=claims_path,
                known_claims_path=known_claims_path,
                output_path=triage_path,
                session=triage_session,
                valid_db_ids=valid_ids,
                prompts_dir=_prompts_dir,
            )

            if selected_ids:
                # Stage count bumps (don't write DB).
                write_bumps(staging_dir, run_id, set(selected_ids))

                # Write full entries for relevant claims.
                relevant = get_entries_by_ids(db, set(selected_ids))
                relevant_claims_path = output_dir / RELEVANT_CLAIMS_FILENAME
                relevant_claims_path.write_text(
                    json.dumps(relevant, indent=2)
                )
                print(f"  {len(relevant)} relevant known claims provided to verifier.")
        else:
            print("  Claim database is empty — skipping triage.")

    # ── Step 4: Verify claims ─────────────────────────────────────────
    verdicts = await verify_claims(
        question_text=question_text,
        claims=claims,
        session=verifier_session,
        verdicts_path=verdicts_path,
        known_claims_path=relevant_claims_path,
        prompts_dir=_prompts_dir,
    )

    # ── Step 5: Remember → stage new claims ─────────────────────────
    if db_path is not None and verdicts:
        # Ensure known_claims.json exists for the remember session
        # (may not exist if triage was skipped on first run).
        known_claims_path = output_dir / KNOWN_CLAIMS_FILENAME
        if not known_claims_path.exists():
            known_claims_path.write_text("[]")

        remember_path = output_dir / REMEMBER_FILENAME
        selected_indices = await run_remember(
            session=remember_session,
            verdicts_path=verdicts_path,
            known_claims_path=known_claims_path,
            output_path=remember_path,
            prompts_dir=_prompts_dir,
        )

        if selected_indices:
            # Extract full entries from verdicts for the selected indices.
            new_claims = [
                verdicts[i] for i in selected_indices
                if 0 <= i < len(verdicts)
            ]
            if new_claims:
                write_new_claims(staging_dir, run_id, new_claims)
                print(f"  Staged {len(new_claims)} new claims for merge.")

    return claims, verdicts
