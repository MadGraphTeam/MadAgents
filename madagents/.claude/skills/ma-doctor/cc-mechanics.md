# What Claude Code can and cannot do

The mechanics a structural change must respect. A recommendation that assumes a behavior not listed here is not buildable on the Claude Code CLI — check it against this file before proposing it. (Established by observing Claude Code 2.1.x behaviour against its published docs; version-specific, so re-confirm after a version bump.)

## Two effective levels — one dispatcher

There is one lead (the main session) and a flat set of subagents — a design choice, not a Claude Code limit. A subagent inherits the Agent tool (unless its card sets `tools:`) and **can** dispatch any named subagent type, built-in or custom (nested subagents, Claude Code v2.1.172+, depth cap 5). It **receives the full roster**, but reactively — the "available agent types" menu is injected after the subagent's first `Agent` call, not pre-loaded — so a nester bootstraps with one dispatch (any known type), then sees the whole menu. A middle tier of "group-leader" agents is fully buildable; this harness keeps dispatch with the lead by choice.

## What loads, and where

- **`CLAUDE.md` + every `rules/*.md`** auto-load into **every** agent — the lead and all subagents. This is the only channel that puts the same content, in full, into every agent at startup. **This layer deliberately uses neither, and ships neither.** Both are *project*-scoped surfaces: they load into a host project's own, non-MadAgents agents too, so a discipline placed there ("MadGraph source is your truth") would bind agents that have nothing to do with MadGraph, and a shipped `CLAUDE.md` would clobber or fight the host's. The layer is therefore behavior-isolated: it ships only `agents/`, `skills/`, and the lead's system-prompt append. **Do not recommend re-introducing a rule or a `CLAUDE.md`** — a cross-cutting discipline goes into every card that needs it (duplicated across cards, which is the accepted cost of isolation), and a lead-only discipline goes into `prompts/lead-discipline.md`.
- **Skill *descriptions*** reach every agent that has the Skill tool (lead and subagents), injected passively at startup. **Skill *bodies* (`SKILL.md`) load only when an agent invokes that skill** — never at startup, unless a card's `skills:` preload field names it. Mechanics buried in a skill body reach a subagent only if it invokes the skill; anything a subagent must always have in full cannot live in a skill body.
- **The lead's system-prompt append** (`append_system_prompt_file`) and **the lead's slate** reach the lead only. Subagents never see them.
- **Each subagent** gets its **card body** as its system prompt, plus **its own slate** when its card carries `memory: project`.

## Memory

- Per-subagent slate: `memory: project` on the card makes Claude Code auto-load `.claude/agent-memory/<name>/MEMORY.md` into that subagent (first ~200 lines / 25 KB). Only that subagent sees it.
- Lead slate: declared via `autoMemoryDirectory` in `settings.local.json`, auto-loading `.claude/lead-memory/MEMORY.md` into the lead.
- The wiki is **read on demand**, never auto-loaded.
- A slate's write path must be the absolute auto-load path. A slate written anywhere else (e.g. under the wiki tree) never auto-loads.

## Dispatch

Each dispatch starts a **fresh, isolated** context — the subagent sees neither the lead's conversation nor its own prior dispatches. A custom subagent can be **resumed** (it then retains its prior history). "Verify in clean context" means a fresh dispatch, not a resume.

## What this means for a structural change

- A new always-on discipline → the **card body of every agent it binds** (and `lead-discipline.md` if it binds the lead), not a skill body — a skill body never auto-loads, so a subagent gets it only if it invokes the skill. Not a rule and not `CLAUDE.md`: those are project-scoped and would bind the host's own agents too. Scope the discipline per role, and expect to write it more than once; that duplication is the cost of an additive layer.
- A new agent is reachable only through the lead's routing — it needs a clear `description` (the router) and a reason the lead would dispatch it.
- Removing an agent removes a routing target the lead may rely on; changing a discipline that lives in N card bodies means changing all N, or the roster silently disagrees with itself.
- A subagent can dispatch any named subagent type, built-in or custom (nested, depth cap 5); it receives the full roster, but reactively (injected after its first `Agent` call, not pre-loaded). Skill bodies never auto-load.
