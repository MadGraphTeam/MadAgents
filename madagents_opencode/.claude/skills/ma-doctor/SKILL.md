---
name: ma-doctor
description: "Audit this agent system's own harness — its agents, skills, and learned memory — against your past sessions and a corpus of agent-design principles, then recommend structural changes (add / remove / adjust a consultant, skill, or rule). Human-gated: recommends and discusses first, snapshots before editing, applies only on explicit approval, and runs a reviewer panel on the change. Use when asked to audit, doctor, tune, or improve the setup itself — not for a physics or MadGraph task."
---

# ma-doctor — audit and improve this agent system's harness

Run this when the user asks to audit / doctor / tune / improve the **setup itself** — its agents, skills, memory — never for a physics or MadGraph task.

This reshapes the **harness**. Hardening behavior from a specific past mistake into memory is `/ma-reflect`'s job; this is the structural sibling — it changes the agents and skills themselves. It is **human-gated**: recommend first, change only on the user's explicit approval.

Everything the workflow needs is in this skill's folder:

- `analyst.md` — the analysis brief.
- `lessons/` — agent-design principles (`lessons/INDEX.md` is the list).
- `opencode-mechanics.md` — what opencode can and cannot do, so a recommendation is buildable.
- `use-case.md` — the product goals every change must serve.
- `reviewers/` — the five panel briefs.

## 1. Snapshot

Before anything else, archive the current harness so the whole operation is revertable to the exact pre-doctor state. This harness spans **three** trees, and a snapshot that takes only one cannot restore it:

    root="${OPENCODE_PROJECT_DIR:-$PWD}"
    ts=$(date -u +%Y-%m-%dT%H-%M-%SZ)
    mkdir -p "$root/.madagents/harness-archive/$ts"
    cp -r "$root/.opencode" "$root/.claude" "$root/prompts" "$root/.madagents/harness-archive/$ts/"

## 2. Analyze

Dispatch a general-purpose agent with the full text of `analyst.md` as its instructions. It returns prioritized, evidence-cited recommendations. It is read-only — it analyzes and reports, it never edits.

## 3. Present and discuss

Relay the recommendations to the user. Each names the weakness and its evidence, the proposed change, the principle it follows, and the risk. **Make no change yet.** Discuss until the user decides.

## 4. Approve

Apply only the changes the user explicitly approves. If the user is unsure, stay in discussion.

## 5. Apply

**A card is two files here.** Its body is `.opencode/cards/<name>.md`; its routing `description` is a field in `.opencode/opencode.json`. When editing a card, edit the **body** — do not overwrite its `description`, which may carry a learned routing refinement. When a change genuinely needs the description, edit that field alone and leave the body untouched.

**`.opencode/opencode.json` is the highest-risk file in this harness.** It is JSON, and opencode hard-fails on invalid config: a malformed edit does not degrade one consultant, it removes all 46 at once. After any edit to it, run `opencode agent list` and confirm the full roster still resolves — before moving on, not at the end.

**Every `{file:}` target must exist.** Adding an agent means adding its slate file; removing one means removing its reference. A reference to a missing file invalidates the whole config, with the same total effect.

**Edit by targeted substitution — never normalise.** A change that spans many files (a discipline across the roster, a slate, the wiki) is **surgical**: write an exact-string or tightly-anchored replacement for the one thing you are changing. Never add a "cleanup" pass — collapsing whitespace, tidying punctuation, stripping empty parens. Each looks harmless alone; together they silently rewrite content that had nothing to do with the change, and the result still *parses*, so nothing errors.

**Tripwire: count the files you changed, and sanity-check the number before you trust it.** A job that should touch ~12 files reporting 632 is not a success message — it is an alarm, and it means your pattern matched more than you meant.

**Verify against the step-1 snapshot, not against your own output.** Diff the three trees against `.madagents/harness-archive/<ts>/` and assert: *every file I changed contained the thing I was changing, and no file changed for any other reason.* That one assertion catches this entire class. This is why step 1 archives before anything else — treat the archive as read-only, always.

**A fix in one tier is not a fix.** If the discipline you changed is also stated in the learned tier (`.claude/agent-memory/<name>/MEMORY.md`, `.claude/lead-memory/MEMORY.md`, `.madagents/wiki/`), that tier now contradicts the surface **in the same reader's context** — and on this provider a card body and its slate are concatenated into one prompt, so the two sit side by side. Correct it in the same pass — through the owning agent, per single-writer — or tell the user plainly that you did not.

**Restart before judging the result.** opencode loads config once at startup and never reloads it. Nothing you changed is live in the running session; a change that looks inert may simply not have been read yet.

## 6. Panel review

Dispatch the `reviewers/` briefs as general-purpose agents on the applied change — route by relevance (a runtime-neutral prose tweak need not pay `opencode-alignment`), with the full panel as the minimum gate for anything non-trivial. Each returns a verdict. (Keep dispatch with you, the main session — the panel is a flat fan-out the lead drives.)

**Name the defect classes you want checked.** A reviewer reports what it was asked about and *nothing else*: a class you do not name will not appear in any verdict, and the panel's silence will read as a pass. Before dispatching, ask what you are **not** asking about. `surface-discipline` carries the classes the other four are blind to — wrong reader, wrong addressee, content the reader already has, a hardcoded environment — so it is not optional on any change that moves content between surfaces.

## 7. Finalize or revert

- All clear → keep the change; tell the user what changed and where the snapshot is.
- A blocking or needs-revision verdict → surface it; revise, or revert by restoring the archived trees from the snapshot. The user decides.
- If no change was applied, the snapshot can be removed.
