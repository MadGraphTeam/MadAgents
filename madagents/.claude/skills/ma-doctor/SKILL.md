---
name: ma-doctor
description: "Audit this agent system's own harness — its agents, skills, rules, and learned memory — against your past sessions and a corpus of agent-design principles, then recommend structural changes (add / remove / adjust a consultant, skill, or rule). Human-gated: recommends and discusses first, snapshots before editing, applies only on explicit approval, and runs a reviewer panel on the change. Use when asked to audit, doctor, tune, or improve the setup itself — not for a physics or MadGraph task."
---

# ma-doctor — audit and improve this agent system's harness

Run this when the user asks to audit / doctor / tune / improve the **setup itself** — its agents, skills, rules, memory — never for a physics or MadGraph task.

This reshapes the **harness**. Hardening behavior from a specific past mistake into memory is `/ma-reflect`'s job; this is the structural sibling — it changes the agents, skills, and rules themselves. It is **human-gated**: recommend first, change only on the user's explicit approval.

Everything the workflow needs is in this skill's folder:

- `analyst.md` — the analysis brief.
- `lessons/` — agent-design principles (`lessons/INDEX.md` is the list).
- `cc-mechanics.md` — what Claude Code can and cannot do, so a recommendation is buildable.
- `use-case.md` — the product goals every change must serve.
- `reviewers/` — the five panel briefs.

## 1. Snapshot

Before anything else, archive the current harness so the whole operation is revertable to the exact pre-doctor state:

    root="${CLAUDE_PROJECT_DIR:-$PWD}"
    ts=$(date -u +%Y-%m-%dT%H-%M-%SZ)
    mkdir -p "$root/.madagents/harness-archive/$ts"
    cp -r "$root/.claude" "$root/.madagents/harness-archive/$ts/"

## 2. Analyze

Dispatch a general-purpose agent with the full text of `analyst.md` as its instructions. It returns prioritized, evidence-cited recommendations. It is read-only — it analyzes and reports, it never edits.

## 3. Present and discuss

Relay the recommendations to the user. Each names the weakness and its evidence, the proposed change, the principle it follows, and the risk. **Make no change yet.** Discuss until the user decides.

## 4. Approve

Apply only the changes the user explicitly approves. If the user is unsure, stay in discussion.

## 5. Apply

Apply the approved change to `.claude/`. When editing an existing agent card, edit its **body** in place — do not overwrite its `description`, which may carry a learned routing refinement.

**Edit by targeted substitution — never normalise.** A change that spans many files (a discipline across the roster, a slate, the wiki) is **surgical**: write an exact-string or tightly-anchored replacement for the one thing you are changing. Never add a "cleanup" pass — collapsing whitespace, tidying punctuation, stripping empty parens. Each looks harmless alone; together they silently rewrite content that had nothing to do with the change, and the result still *parses*, so nothing errors.

**Tripwire: count the files you changed, and sanity-check the number before you trust it.** A job that should touch ~12 files reporting 632 is not a success message — it is an alarm, and it means your pattern matched more than you meant.

**Verify against the step-1 snapshot, not against your own output.** Diff `.claude/` against `.madagents/harness-archive/<ts>/.claude/` and assert: *every file I changed contained the thing I was changing, and no file changed for any other reason.* That one assertion catches this entire class. This is why step 1 archives before anything else — treat the archive as read-only, always.

**A fix in one tier is not a fix.** If the discipline you changed is also stated in the learned tier (`agent-memory/<name>/MEMORY.md`, `lead-memory/MEMORY.md`, `.madagents/wiki/`), that tier now contradicts the surface **in the same reader's context**. Correct it in the same pass — through the owning agent, per single-writer — or tell the user plainly that you did not.

## 6. Panel review

Dispatch the `reviewers/` briefs as general-purpose agents on the applied change — route by relevance (a CC-mechanics-neutral prose tweak need not pay `cc-alignment`), with the full panel as the minimum gate for anything non-trivial. Each returns a verdict. (Keep dispatch with you, the main session — the panel is a flat fan-out the lead drives.)

**Name the defect classes you want checked.** A reviewer reports what it was asked about and *nothing else*: a class you do not name will not appear in any verdict, and the panel's silence will read as a pass. Before dispatching, ask what you are **not** asking about. `surface-discipline` carries the classes the other four are blind to — wrong reader, wrong addressee, content the reader already has, a hardcoded environment — so it is not optional on any change that moves content between surfaces.

## 7. Finalize or revert

- All clear → keep the change; tell the user what changed and where the snapshot is.
- A blocking or needs-revision verdict → surface it; revise, or revert by restoring the archived `.claude/` from the snapshot. The user decides.
- If no change was applied, the snapshot can be removed.
