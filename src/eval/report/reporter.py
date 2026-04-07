"""Generate summary report and doc diffs for an evaluation run.

Reads grades, verification verdicts, and documentation state to produce
a Markdown summary (``summary.md``) and a unified diff of doc changes.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from eval.config import CATEGORIES, DOCS_DIR
from eval.models import load_grades, load_questions, load_verification


def find_previous_run(run_dir: Path) -> Path | None:
    """Find the most recent run directory preceding *run_dir*."""
    runs_dir = run_dir.parent
    current_name = run_dir.name
    prev_runs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name < current_name],
        reverse=True,
    )
    return prev_runs[0] if prev_runs else None


def generate_report(run_dir: Path):
    """Generate summary.md and doc_changes.diff."""
    report_dir = run_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    questions = load_questions(run_dir / "questions.jsonl")
    grades = load_grades(run_dir)

    q_map = {q.id: q for q in questions}
    counts = Counter(g.category for g in grades)
    total = len(grades)
    total_questions = len(questions)

    successes = counts.get("SUCCESS", 0) + counts.get("SUCCESS_INEFFICIENT", 0)
    success_rate = (successes / total * 100) if total > 0 else 0

    docs_before = run_dir / "docs_before"
    diff_text = ""
    if docs_before.exists():
        try:
            proc = subprocess.run(
                ["diff", "-ru", str(docs_before), str(DOCS_DIR)],
                capture_output=True, text=True,
            )
            diff_text = proc.stdout
        except Exception:
            diff_text = "[diff command failed]"

    (report_dir / "doc_changes.diff").write_text(diff_text)

    docs_after = run_dir / "docs_after"
    if docs_after.exists():
        shutil.rmtree(docs_after)
    shutil.copytree(DOCS_DIR, docs_after)

    verifications = {}
    for q in questions:
        q_dir = run_dir / "questions" / q.id
        v = load_verification(q_dir)
        if v:
            verifications[q.id] = v

    prompt_proposals_dir = report_dir / "proposals/prompt"
    doc_proposals_dir = report_dir / "proposals/doc"
    prompt_proposals = list(prompt_proposals_dir.glob("*.json")) if prompt_proposals_dir.exists() else []
    doc_proposals = list(doc_proposals_dir.glob("*.json")) if doc_proposals_dir.exists() else []

    comparison_section = ""
    prev_run = find_previous_run(run_dir)
    if prev_run:
        prev_grades = load_grades(prev_run)
        prev_counts = Counter(g.category for g in prev_grades)
        prev_successes = prev_counts.get("SUCCESS", 0) + prev_counts.get("SUCCESS_INEFFICIENT", 0)
        prev_total = len(prev_grades)
        prev_rate = (prev_successes / prev_total * 100) if prev_total > 0 else 0

        comparison_section = f"""
## Comparison with Previous Run

| Metric | Previous ({prev_run.name}) | Current |
|--------|---------------------------|---------|
| Total questions | {prev_total} | {total} |
| Success rate | {prev_rate:.1f}% | {success_rate:.1f}% |
| DOC_GAP | {prev_counts.get("DOC_GAP", 0)} | {counts.get("DOC_GAP", 0)} |
| DOC_CONFUSION | {prev_counts.get("DOC_CONFUSION", 0)} | {counts.get("DOC_CONFUSION", 0)} |
"""

    per_question_rows = []
    total_duration_ms = 0
    for g in grades:
        q = q_map.get(g.question_id)
        q_text = q.text if q else "?"
        tm = g.trace_metrics
        duration_s = tm.duration_ms / 1000 if tm.duration_ms else 0
        total_duration_ms += tm.duration_ms
        row = f"| {g.question_id} | {q_text} | {g.category} | {g.confidence:.2f} | {duration_s:.0f}s |"
        per_question_rows.append(row)

    per_question_table = "\n".join(per_question_rows) if per_question_rows else "| (no results) | | | | |"

    doc_changes_count = diff_text.count("\n+") - diff_text.count("\n+++")
    doc_changes_summary = (
        f"{doc_changes_count} lines added across documentation files."
        if doc_changes_count > 0
        else "No documentation changes applied."
    )

    seed_count = sum(1 for q in questions if q.source == "seed")
    generated_count = sum(1 for q in questions if q.source == "generated")

    summary = f"""# Evaluation Run Summary

**Run**: {run_dir.name}
**Date**: {run_dir.name.replace("_", " ", 1).replace("_", ":")}
**Questions evaluated**: {total} / {total_questions}
**Success rate**: {success_rate:.1f}%

## Questions

| Source | Count |
|--------|-------|
| Seed (pre-curated) | {seed_count} |
| Generated | {generated_count} |
| **Total** | **{total_questions}** |

## Category Breakdown

| Category | Count | Percentage |
|----------|-------|------------|
"""
    for cat in CATEGORIES:
        c = counts.get(cat, 0)
        pct = (c / total * 100) if total > 0 else 0
        if c > 0:
            summary += f"| {cat} | {c} | {pct:.1f}% |\n"

    if verifications:
        has_ref = sum(1 for q in questions if q.reference_answer)
        exec_verified = sum(1 for v in verifications.values() if v.agent_verified is True)
        unverifiable_count = counts.get("UNVERIFIABLE", 0)

        summary += f"""
## Verification Statistics

| Metric | Count |
|--------|-------|
| Questions with reference answers (unverified) | {has_ref} / {total_questions} |
| Execution-verified agent answers | {exec_verified} / {len(verifications)} |
| UNVERIFIABLE | {unverifiable_count} |
"""

    total_duration_s = total_duration_ms / 1000
    avg_duration_s = total_duration_s / total if total > 0 else 0
    totals_row = f"| | **Total / Avg** | | | **{total_duration_s:.0f}s / {avg_duration_s:.0f}s** |"

    summary += f"""
## Per-Question Results

| ID | Question | Category | Confidence | Duration |
|----|----------|----------|------------|----------|
{per_question_table}
{totals_row}
"""

    summary += f"""## Documentation Changes

{doc_changes_summary}

See `doc_changes.diff` for full diff.

## Prompt Proposals

{len(prompt_proposals)} prompt change(s) pending review in `report/proposals/prompt/`.
"""

    if prompt_proposals:
        summary += "\n| File | Category | Prompt Fix |\n|------|----------|------------|\n"
        for p in sorted(prompt_proposals):
            data = json.loads(p.read_text())
            prompt_fix = data.get("prompt_suggested_fix", "")
            summary += f"| {p.name} | {data.get('category', '?')} | {prompt_fix} |\n"

    summary += f"""
## Doc Proposals

{len(doc_proposals)} doc change(s) pending review in `report/proposals/doc/`.
"""

    if doc_proposals:
        summary += "\n| File | Category | Status | Suggested Fix |\n|------|----------|--------|---------------|\n"
        for p in sorted(doc_proposals):
            data = json.loads(p.read_text())
            fix = data.get("suggested_fix", data.get("draft", {}).get("action", ""))
            summary += f"| {p.name} | {data.get('category', '?')} | {data.get('status', '?')} | {fix} |\n"

    doc_changes_manifest = run_dir / "doc_changes.json"
    if doc_changes_manifest.exists():
        manifest_data = json.loads(doc_changes_manifest.read_text())
        manifest_changes = manifest_data.get("changes", [])
        if manifest_changes:
            summary += "\n## Applied Changes Detail\n\n"
            summary += "| Question | File(s) | Action | Revisions | Effectiveness | Outcome | Merged With |\n"
            summary += "|----------|---------|--------|-----------|---------------|---------|-------------|\n"

            regular = [ch for ch in manifest_changes
                       if not ch.get("question_id", "").startswith(("incidental:", "claim:"))]
            incidental = [ch for ch in manifest_changes if ch.get("question_id", "").startswith("incidental:")]
            claim_fixes = [ch for ch in manifest_changes if ch.get("question_id", "").startswith("claim:")]

            for ch in regular:
                qid = ch.get("question_id", "?")
                file_path = ch.get("file_path", "?")
                if isinstance(file_path, list):
                    file_path = ", ".join(file_path)
                eff_rounds = ch.get("effectiveness_rounds", 0)
                eff_outcome = ch.get("effectiveness_outcome", "n/a")
                merged_with = ", ".join(ch.get("merged_with", []))
                summary += (
                    f"| {qid} | {file_path} | {ch.get('action', '?')} "
                    f"| {ch.get('revision_attempts', 0)} | {eff_rounds} round(s) "
                    f"| {eff_outcome} | {merged_with} |\n"
                )

            if incidental:
                summary += f"\n### Incidental Corrections ({len(incidental)})\n\n"
                summary += "Pre-existing documentation errors found and fixed during verification.\n\n"
                summary += "| Source | File | Description |\n|--------|------|-------------|\n"
                for ch in incidental:
                    source_q = ch.get("question_id", "?").replace("incidental:", "")
                    file_path = ch.get("file_path", "?")
                    desc = ch.get("description", "")
                    summary += f"| {source_q} | {file_path} | {desc} |\n"

            if claim_fixes:
                summary += f"\n### Claim-Based Fixes ({len(claim_fixes)})\n\n"
                summary += "Documentation improvements derived from failed verification claims.\n\n"
                summary += "| Source Question | File | Action | Claim |\n|----------------|------|--------|-------|\n"
                for ch in claim_fixes:
                    source_q = ch.get("question_id", "?").replace("claim:", "")
                    file_path = ch.get("file_path", "?")
                    action = ch.get("action", "?")
                    desc = ch.get("claim_description", "")
                    summary += f"| {source_q} | {file_path} | {action} | {desc} |\n"

    summary += comparison_section

    (report_dir / "summary.md").write_text(summary)
    print(f"Report written to {report_dir / 'summary.md'}")
    print(f"Doc diff written to {report_dir / 'doc_changes.diff'}")
