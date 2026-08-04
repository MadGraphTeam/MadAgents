# What opencode can and cannot do

The mechanics a structural change must respect. A recommendation that assumes a behavior not listed here is not buildable on the opencode CLI — check it against this file before proposing it. (Established by running opencode 1.18.11 and reading its resolved config with `opencode debug`; version-specific, so re-confirm after a version bump. `opencode debug skill` also prints opencode's own built-in `customize-opencode` skill, which is the authoritative config reference.)

## Two effective levels — one dispatcher

There is one lead (the primary agent) and a flat set of subagents — a design choice, not an opencode limit. Every consultant here is declared `mode: "subagent"`; opencode also ships `build`, `plan`, `general` and `explore`. Subagents are reached through the `task` tool, and `task` is a permission key like any other, so it can be allowed, asked or denied per agent. **Whether a subagent may itself dispatch is not established here** — treat a nested-dispatch design as UNVERIFIED and check it against the binary before recommending one. This harness keeps dispatch with the lead by choice.

## What loads, and where

- **`AGENTS.md`** at the project root auto-loads as project context. opencode reads `AGENTS.md` first and falls back to `CLAUDE.md` only when there is none — the first match wins, so the two are alternatives, not layers. Here it is the *environment description* (what the image installed, where MadGraph is), seeded once and then owned by the session. It is a project-global surface: in a host project it would reach that project's own agents too, which is why no discipline belongs in it.
- **`instructions`** in `.opencode/opencode.json` is the lead's channel: a list of files loaded as session context. It carries `prompts/lead-discipline.md` and the lead's slate. **Verified: it does not appear in a subagent's prompt** — it is the opencode equivalent of Claude Code's system-prompt append, in both reach and effect.
- **Skill *descriptions*** are surfaced to agents through the `skill` tool; **bodies (`SKILL.md`) load only when a skill is invoked.** Mechanics buried in a skill body reach a subagent only if it invokes the skill; anything a subagent must always have in full cannot live there.
- **Each subagent** gets its **`prompt`** — declared in `.opencode/opencode.json` and assembled by `{file:}` interpolation from its card body plus its own slate. Nothing else. Not `instructions`, not the lead's context.

**Two relative bases in one file, and this catches people.** `{file:...}` resolves against **the config file's directory** (`.opencode/`); `instructions` resolves against **the project root**. Spelling an instructions path `../prompts/lead-discipline.md` loads nothing, and says nothing — the lead simply starts without its discipline.

## Memory

- Per-subagent slate: a plain `.claude/agent-memory/<name>/MEMORY.md` — the same file and the same path Claude Code auto-loads — pulled into that agent's prompt by `{file:../.claude/agent-memory/<name>/MEMORY.md}`. Only that subagent sees it.
- Lead slate: `.claude/lead-memory/MEMORY.md`, listed in `instructions`.
- The wiki is **read on demand**, never auto-loaded.
- Interpolation happens **when config is loaded**, and config is loaded once at startup and never hot-reloaded. So a slate an agent rewrites is live from the **next** session — the same semantics as Claude Code's auto-memory, for the same reason. It also means **any** config-time edit needs a restart to take effect.

**A `{file:}` target that does not exist is fatal.** opencode rejects the whole config — *"Configuration is invalid … bad file reference"* — and the entire roster disappears. Every slate a prompt names must exist, which is why the shipped tree carries an empty skeleton for each and why the harness re-creates any a memory pack did not supply. "This agent has learned nothing yet" must be spelled as an empty file, never as an absent one. (`instructions` is the opposite: a missing file there is skipped silently.)

## Permissions

opencode's default is **allow everything** (only `doom_loop` and `external_directory` ask). The shipped `permission` block in `.opencode/opencode.json` is therefore what makes this system pre-approve nothing — it is load-bearing, not decoration. Removing or thinning it does not "use the defaults", it grants everything. Within a permission, **the last matching rule wins**, so order broad-to-narrow.

## Dispatch

Each dispatch starts a **fresh, isolated** context — the subagent sees neither the lead's conversation nor its own prior dispatches. "Verify in clean context" means a fresh dispatch.

## Where the harness actually lives

Three trees, not one:

- `.opencode/opencode.json` — the roster: every agent's `description`, `mode` and `prompt`, plus `instructions` and `permission`. **This file is JSON and opencode hard-fails on invalid config**, so a malformed edit does not degrade the system, it removes all 46 consultants at once.
- `.opencode/cards/<name>.md` — the card *bodies*, referenced by those prompts.
- `.claude/skills/` — the workflows, read by opencode natively; and `.claude/agent-memory/`, `.claude/lead-memory/` — the learned tier.

A card's **body** and its **description** are therefore in *different files*: the body in `cards/<name>.md`, the description in `opencode.json`. On Claude Code they are two halves of one file.

## What this means for a structural change

- A new always-on discipline → the **card body of every agent it binds** (`.opencode/cards/<name>.md`), and `prompts/lead-discipline.md` if it binds the lead. Not a skill body — a skill body never auto-loads. Not `AGENTS.md`: that is project-scoped and would bind a host project's own agents. Scope the discipline per role and expect to write it more than once; that duplication is the cost of an additive layer.
- A new agent is reachable only through the lead's routing — it needs a clear `description` (the router) in `opencode.json`, and a reason the lead would dispatch it. It also needs a slate file if its prompt names one.
- Removing an agent means removing its entry from `opencode.json` **and** its card body **and** its slate reference — leave the reference with the file gone and the whole roster fails to load.
- Editing `opencode.json` by hand is the highest-risk edit in this harness. Change it, then run `opencode debug agent <name>` and confirm the roster still resolves before you trust the change.
