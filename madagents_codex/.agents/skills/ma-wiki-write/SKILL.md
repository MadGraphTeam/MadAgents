---
name: ma-wiki-write
description: '''Record a finding into your own wiki/slate, or consolidate your notes. Invoke to cache something you source-walked for THIS input that is non-obvious and worth a future dispatch (signal = genuine learning, NOT "might be useful"); or to create / extend / supersede a page, merge / split / generalize across pages, or move a lesson between your slate and the wiki. Writes your OWN subtree only (per-agent: consultants/<your-name>/; lead: lead/).'''
---

# `/ma-wiki-write`

One skill to write your learned tier. You invoke it, then **pick the operation by judgment** — there is no menu to pre-select from. Carry the shared write discipline below into whichever operation fits.

**Single-writer-per-page.** Write only your own subtree. You never write another agent's subtree; cross-subtree refs you can only *flag* in your return for the lead.

## Your write paths

| | Wiki subtree | Slate |
|---|---|---|
| **Consultant / probe** | `.madagents/wiki/consultants/<your-agent-name>/` | the marked region of `.codex/agents/<your-agent-name>.toml` |
| **Lead** | `.madagents/wiki/lead/` (flat, no subdirs) | `.madagents/memory/lead/MEMORY.md` |

`<your-agent-name>` is your literal agent name (e.g. `ma-chain-decay-consultant`), suffix and all.

**A consultant's slate is not a file you write.** It lives inside your own role file, between `<!-- MADAGENTS-SLATE:BEGIN -->` and `<!-- MADAGENTS-SLATE:END -->`, because a role file's `developer_instructions` is what gets auto-loaded into every dispatch of you. Read it and write it only through the bundled script:

```bash
python3 .agents/skills/ma-wiki-write/scripts/write_slate.py --agent <your-agent-name> --show
python3 .agents/skills/ma-wiki-write/scripts/write_slate.py --agent <your-agent-name> --file <path>
```

**Never hand-edit the role file.** It is TOML, and a malformed edit removes you from the roster outright — card and slate together — with no error the session will notice. The script replaces only the marked region, re-parses the whole file, and leaves the original untouched if the result would not load. A slate written as a loose `MEMORY.md` somewhere in the tree is never loaded and is silently inert.

## Step 0 — should this be written at all? (the gates)

Two gates run before any operation. They are about *whether* to write, not *which* operation.

**Signal gate (recording a finding).** *"Did I source-walk something non-obvious for THIS input — where a surprising default lives and how it behaves, a multi-step mechanism, a behavior pretraining wouldn't predict — such that a future dispatch will plausibly act better because of this page?"* If yes, write — the source-walk is genuine learning worth caching. (Cache where the default lives and why it surprises, not the number — see discipline 4.) **Don't pre-judge on "might future-me need it"**; if it was non-obvious to walk, future-me benefits. Skip only when the walk was trivial restatement of something already loaded.

Record **confirmations too, not only surprises and pitfalls.** An approach you confirmed correct for THIS input — a path validated against source or probe that you'd otherwise only half-trust — earns a page, so the cache tells future-you what is safe to *repeat*, not only what to avoid. A tier holding only failures pushes the system toward over-caution.

**What-not-to-learn gate.** Do **not** cache session/instance state as a durable page or slate entry, even when the failure was real and reproduced. Three classes — surface them to the user, don't write them:

- **Environment / instance state** — a missing binary, an unset path / credential / config, a transient tool error. The state of this machine or run, not a rule of the task.
- **A "tool/feature is broken" claim** — writing it installs a standing self-refusal the system cites long after the real (often environmental) cause is fixed.
- **One-off specifics** — a single run's exact value, name, or error string; a one-time identifier. Re-derived when needed.

Criterion: **if the rule would only hold on this one run, machine, or input, it is not durable.** This is separate from "ground before writing" — a finding can be real and reproducible and still fail this gate.

## Which operation fits?

Decide by what you're holding and what the subtree already has. Your auto-loaded slate's `## Wiki page index` is the coverage map — consult it first.

| You have… | …and the subtree… | Operation |
|---|---|---|
| a non-obvious finding for THIS input | has **no** page covering this scope | **Add** — new page |
| a non-obvious finding for THIS input | has a page covering this scope, finding fits within it | **Update / extend** |
| a claim **contradicted** by source/probe | the contradicted claim lives on a page | **Update / supersede in-place** |
| two pages with the **same trigger + same behaviour**, differing only in examples | both exist, scope overlaps | **Merge** (backward dedup) |
| one page that grew **two distinct scopes** that shouldn't co-load | one page, two cohesion centres | **Split** |
| several instance pages and a **deeper principle that catches MORE cases than they do individually** | instances exist; principle is new | **Generalize** (forward-looking) — new page |
| a wiki page's principle now **operative on most dispatches** | page exists; earns the always-loaded slot | **Promote** → slate |
| a slate entry gone **stale / internalized / long-inoperative** | slate is at budget or the slot is better used | **Demote** → wiki |

Boundary cues:
- **Add vs Update:** a page already covering this scope → update, never a second page. New content genuinely *outside* every existing scope → add.
- **Merge vs Generalize:** merge is **pure backward-looking dedup** — the result covers exactly what the inputs covered together, no new principle. Generalize is **forward-looking** — a NEW page naming a deeper understanding that catches cases the instances individually never named. If your "generalization" body is just the union of the instance bodies, you wrote a merge — use Merge.
- **Merge vs Update:** one page a strict subset of another → extend the broader (Update), don't merge.
- **Split vs leave-alone:** split on *cohesion* (two scopes that shouldn't load on the same query), never on length alone.
- **Update-supersede vs a dated block:** supersede **in-place** — pages are current truth, git carries history. Never leave a `Superseded YYYY-MM-DD` section.

## Shared write discipline (every operation)

1. **Ground every claim before writing — source-walk for THIS input.** Memory and pretraining are *not* truth sources; pretrained recall is at best a hypothesis to verify. Open the source and confirm. **File:line citations are highly encouraged**; use `$MADGRAPH_INSTALL/...` in citations, not a hardcoded install path.
2. **Probe-verify runtime predictions.** Any claim that **predicts MadGraph runtime behavior** (a warning text, a diagram count, a subprocess directory, a σ value, an error message) is highly encouraged to be probe-verified — run MadGraph and observe. A runtime prediction written without a probe is a **hypothesis, not fact**: mark it inline (e.g. *"expected (not yet probe-verified)"*). If you meet an existing un-probed runtime claim on a page you're editing, mark it as hypothesis rather than leaving it as confident-fact.
3. **Agent-behavior claims** (consultant self-discipline, lead orchestration patterns) carry the **cite-the-incident** discipline instead of source-walk — name the dispatch/run where the behaviour showed.
4. **Cache the lookup, not the value.** A **version-dependent numeric answer** — a default value, an exact count — is **not** recorded on the page. Record where it is registered (a `$MADGRAPH_INSTALL/...:line` coordinate) and the one-line recipe to read it; the value is read fresh from source when it is load-bearing. The lookup coordinate itself *is* cached — it is how you look the value up, not the answer — and you supersede it in-place if a later walk finds it has moved. A version-stable mechanism around the value ("`X=Y` reads as `X<=Y` with a warning") stays cached; only the drift-prone number is excluded. A number that is stale reads exactly as valid as the current one, so it never earns a slot.
5. **One-citation sanity check on adopt.** When you adopt a scope-matching cached page as evidence instead of re-walking, verify **one** cited file:line still resolves.
6. **Supersede in-place.** Pages are the current truth; git carries history. No dated "superseded" sections.
7. **Single-writer-per-page.** Your subtree only.
8. **Keep the index current.** Every page add/delete/description-change updates the `## Wiki page index` in your slate.
9. **Prune as you grow.** Pair every install with apoptosis *in the same pass* — supersede the entry you replaced, merge pages whose scope now overlaps, demote slate entries pushed past budget — so the tier is pruned as it grows, not only appended.

### The slate shape

The marked region of your role file (above), **≤80-line budget**. Sections:

- `## Slice` — what you own (meta-discipline, always active).
- `## Core operating principles` — durable principles (cap ~5).
- `## Recent lessons` — **FIFO, max 5**; oldest demotes out when a 6th arrives.
- `## Wiki page index` — `<slug>: <description>` per page; your navigation surface, and the surface you **sweep against a task**. Every entry here names a *situation that should open the page*, so each one either fires on the task or it does not.
- `## Lead lookups — NOT part of the sweep` *(lead slate only)* — the few pages that answer a question you already have rather than telling you that you have one (a stage→owner table, a dispatch-ordering table, a deferred-probe ledger). They are opened deliberately, never matched during the sweep. **Keep them out of the index**: an entry that fires on every task is not routing, it only feels like it — and it crowds out the entries that would have fired on this one.

At budget cap, **Demote** a stale entry before promoting a new one.

**Rewriting the slate is a whole-region replace,** not an append: read the current slate (`--show`), edit it as a complete document, write it back in full. That is why prune-as-you-grow is cheap here — you are already holding the whole thing.

## Per-operation specifics

### Add — new page
1. **Check coverage** (index). A page already covers this scope → **Update** instead.
2. **Write the description** — one line, ≤120 chars, semantically matchable. *The description is the entire retrieval surface.*
3. **Choose a slug** — topic-named, no dates. Avoid `notes.md`, `misc.md`, `general.md`, `temp.md`, `todo.md`, `wip.md`.
4. Ground per shared discipline. Write the page:
   ```
   ---
   description: <your one-line description>
   ---
   ```
   Body: free-form markdown — plain relative-path cross-references (no `[[wikilinks]]`; they don't resolve as file refs), kept under ~200 lines.
5. Append `<slug>: <description>` to the `## Wiki page index`.
6. Return: `Added <slug>.md — "<description>"`.

### Update — extend or supersede in-place
1. **Read the page in full.**
2. Ground every new claim per shared discipline.
3. **Extend** the relevant section, or **supersede** (rewrite the contradicted section) in-place. No dated blocks.
4. **Rewrite the description** if scope shifted. If the new content is genuinely outside scope → **Add** (new page); if the page now covers two scopes → **Split**.
5. Update the index entry if the description changed.
6. Return: `Updated <slug>.md — extend | supersede — <one-line on what changed>`.

### Merge — fold overlapping pages (backward dedup)
*Gate:* same trigger + same correct behaviour, differing only in examples. Distinct triggers → keep separate. Strict subset → **Update** the broader instead.
1. **Read all pages** to be merged; identify the merged scope.
2. **Pick the primary** — usually the broader description / older slug.
3. **Apply via Update** on the primary; its description covers the union.
4. **Delete** the subsumed pages.
5. **Update inbound refs in your own subtree.** Cross-subtree refs → flag in the return.
6. **Collapse the index entries** — N become one.
7. Return: `Merged <subsumed-slugs> -> <primary-slug>. Cross-subtree refs to update: <list or none>.`

### Split — one page grew two scopes
*Gate:* two scopes that shouldn't co-load on the same query (cohesion, not length).
1. **Read the page in full;** find the natural boundary.
2. **Write two new pages** (Add procedure each), each with a sharper description.
3. **Delete the original.**
4. **Update inbound refs in your own subtree** to whichever new page each was about. Cross-subtree refs → flag.
5. Index: the two Add steps replace the original entry with two.
6. Return: `Split <original-slug>.md -> <slug-A>.md + <slug-B>.md.`

### Generalize — a deeper principle catching MORE cases (forward-looking)
*Gate:* a NEW page lifting a deeper understanding out of multiple existing pages that **catches cases the instances individually do not**. If you can't name the boundary, defer (no write).

*Example.* Instances: *"Answered restrict_LO.dat ctt1 default from memory; should have read the file."* / *"Gave run_card defaults from recall instead of `cat`-ing the generated card."* / *"Named param_card SLHA block from memory; actual block differed in this UFO."* → Generalization: *"Recall-from-memory trap on config/data files. Whenever a finding depends on the content of a file MadGraph reads (`restrict_*.dat`, run_card, param_card, UFO data files), the cached answer is a hypothesis — re-read for THIS input. Fires anywhere a cached file-content fact exists, including files not in the original instance set."* It catches future configs/UFOs the instances never named — that is what makes it a generalization.

1. **State the candidate** — principle, scope, boundary, the cases beyond the instances it catches.
2. **Verify the principle from primary source** — the instances are starting points, not verification.
3. **Write the new page** (Add procedure); description names the principle, body cites the instances briefly.
4. **Decide instance handling** — keep them (they carry specific examples) or **Merge** them in if the principle subsumes them. Default: keep.
5. Index entry added by the Add step.
6. Return: `Generalized: added <slug>.md — "<principle>". Instance pages: kept | merged.`

> If the new page's body is just the union of the instance bodies, it's a **Merge**, not a generalization — revert and use Merge.

### Promote — wiki page → slate working memory
*Gate:* a page's principle (or a recent failure-mode lesson) is **operative on most dispatches in this slice** and earns the always-loaded slot — e.g. a synthesis/failure-mode lesson adopted across many recent dispatches, or a fresh failure-mode page salient enough to keep in active memory until internalized.
1. **Read the wiki page.** Distill its principle into 1-3 lines (a `## Core operating principles` bullet) or 2-4 lines (a `## Recent lessons` entry).
2. **Read your slate.** If the target section is at its budget cap (5 principles / 5 lessons), **Demote** a stale entry first.
3. **Append** the distillation to the right section and write the slate back.
4. **The wiki page stays** — promotion surfaces the distillation, it does not delete the source.
5. Return: `Promoted <slug>.md to slate.<section>.`

### Demote — slate entry → back to a wiki page
*Gate:* a `## Recent lessons` entry past the FIFO budget (>5) and internalized; or a `## Core operating principles` bullet that hasn't fired recently and a sharper one should take its slot; or during a deep tier-balancing pass.
1. **Read the entry to demote** plus its originating wiki page (if any).
2. **Ensure a wiki page covers the lesson.** If none exists, **Add** it as a regular page first.
3. **Remove the entry from the slate** and write it back. The `## Wiki page index` entry stays, so the lesson is still findable on demand.
4. Return: `Demoted slate.<section>.<entry> -> <slug>.md.`
