---
name: ma-wiki-lint
description: Periodic tidy pass on the wiki/MEMORY tree at `.madagents/wiki/` — structural checks, merge near-duplicates, split overgrown pages, balance the MEMORY/wiki tiers, prune; plus a frontmatter scan sub-operation. Reorganizes already-recorded content; it does not source-walk, run MadGraph, or author new principles. User-invoked; do not auto-invoke at session start or end.
---

# `/ma-wiki-lint [targets]`

A periodic **tidy** of the learned tier — the wiki at `.madagents/wiki/` and each owner's MEMORY.md. It keeps what is already recorded well-formed, deduplicated, and balanced across the two tiers (MEMORY.md slate and wiki bodies). It **reorganizes existing, already-cited content** — it never source-walks, runs MadGraph, or authors a new principle.

Learning new content is a different job and lives elsewhere: `ma-wiki-write` records a finding on insight; **generalization** (lifting a deeper principle that catches more cases) fires on insight during `mg-study` / `ma-reflect` / mid-work via `ma-wiki-write`'s `generalize`, never here; correctness of cached content is held by grounding-at-write, `ma-reflect` on a surfaced mistake, and `/mg-deep-verify` at point-of-use.

User-invoked only. Do not auto-invoke at session start or end.

## Target

If the user did not name targets, ask: `lead`, named consultants, or `all`. Skip if `.madagents/wiki/` is empty. Each owner tidies its own subtree — the memory-carrying agents (consultants and the probe) dispatched in parallel, the lead concurrent on `lead/`; no owner reads another's subtree.

## Per-owner dispatch (tidy-mode)

> "Tidy-mode dispatch on `.madagents/wiki/consultants/<your-agent-name>/` (literal subtree path, suffix and all). Reorganize what is already recorded — **do not source-walk, do not run MadGraph, do not author a new principle.** Cheap fixes you apply via `ma-wiki-write`; findings beyond your reach you list.
>
> **Structural:**
> (a) every page has parseable `description:` frontmatter and only that field — flag/fix other keys;
> (b) descriptions ≥40 chars and not a trivial restatement of the filename;
> (c) no two pages share the same description (semantic duplicate → merge, below);
> (d) filenames not in blocklist (`notes.md`, `misc.md`, `general.md`, `temp.md`, `todo.md`, `wip.md`, dated filenames);
> (e) directory name exactly matches your agent's filename, suffix and all (e.g. `ma-…-consultant`, or `ma-probe`);
> (f) MEMORY.md exists and is within budget (≤80 lines target, ≤120 hard cap; if over, demote stale entries);
> (g) MEMORY.md's wiki page index matches the actual pages in your subtree (fix missing/stale entries).
>
> **Consolidate (reorganize existing content only — no new claims):**
> (h) **Merge** two pages with the same trigger + behaviour, differing only in examples → one page;
> (i) **Split** a page whose body cleanly separates into two scopes that shouldn't co-load on one query;
> (j) **Tier-balance** — promote a wiki page's distillation into MEMORY.md when its principle is operative on most recent dispatches; demote a MEMORY.md entry that is internalized or long-unused.
>
> Cross-subtree refs are not yours to update — flag them.
> Return: clean / N findings; one line per finding with the `ma-wiki-*` operation applied; cross-subtree refs flagged."

### Lead pass

The lead runs its own tidy on `lead/` directly, adding: flat tree (no subdirs); consultant directory list matches the real consultant agents.

**Routing pass.** Refine the `description` of each dispatched consultant whose boundary sharpened, and the index entry of each `lead/` page you touched. Then **sweep the whole roster** — not only what you refined: every description valid frontmatter, under the 800-character cap, and free of the two description bugs.

Refining a description needs input the lead does not hold, so ask for it: a consultant's tidy-mode return should say **which regimes and situations properly belong to it, and which it should hand off** — drawn from its own wiki and slate.

### Aggregate

Per owner: (1) clean / N findings; (2) one line per finding with the recommended `ma-wiki-*` operation; (3) cross-subtree refs flagged.

---

## Scan sub-operation

A frontmatter description scan over a wiki subtree: returns one line per page — `<path> description: <text>`. It is **read-only** — it returns descriptions and reorganizes nothing (tidying is owner-only); a reviewer or auditor uses it purely to orient on a subtree it does not own. This is the **fallback for when MEMORY.md is not auto-loaded** — for normal subagent dispatches the auto-loaded MEMORY.md already carries the index of pages in the agent's own subtree.

### When you actually need it

For memory-carrying agents (the consultants and the probe) and the lead, MEMORY.md auto-loads at every dispatch and already carries the index. Use the scan only when:

- You're a reviewer / `ma-blind-spot-auditor` / `ma-failure-mode-extractor` scanning **another** agent's subtree for orientation (those agents have no auto-memory of the consultant they verify).
- You need to refresh the index manually (rare; auto-memory does this automatically).
- The auto-memory loaded fewer entries than the wiki contains (overflow case; auto-memory caps at first-200-lines).

### Procedure

```bash
find <subtree> -maxdepth 2 -name '*.md' \
  -exec awk '/^description:/{print FILENAME ": " $0; nextfile}' {} +
```

Report verbatim. Empty subtree → `empty`.

### Read-scope discipline

- Lead scans `lead/` only. To get a consultant's content, dispatch the consultant.
- Consultant scans its own subtree only.
- Reviewers / auditors scan consultant subtrees per their cards.

---

## Boundaries

- **Tidy only.** Reorganize existing recorded content; never source-walk, never run MadGraph, never author a new principle. Generalization and re-verification are not this skill's job (see the header).
- **Single-writer-per-page.** Each owner tidies its own subtree; the lead tidies `lead/`. Cross-subtree refs are flagged, not edited.
- **Cheap by construction.** Reorganizing already-cited content needs no source access; invoking the pass is the go-ahead for these fixes — no further asks.
