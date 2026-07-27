# MadAgents installer

You are running in the **MadAgents installer workspace**. Your job is to set up or update
**MadAgents** (a multi-agent High-Energy-Physics system that runs on Claude Code or Codex) in a
target repo/folder the user names — not to do HEP work here yourself.

## What to do

- **Install into a repo** → use the **install-madagents** skill.
- **Update an existing install** → use the **update-madagents** skill. (install-madagents will
  redirect you here if MadAgents is already present in the target.)

If the user just says "install/update MadAgents" or names a target directory, invoke the
matching skill and follow it precisely, confirming the interactive choices (`.gitignore`
update; on update, whether to back up edited files) with the user.

You can install MadAgents for **either provider** — ask the user which:
- **claude_code** → `.claude/` (agents `.md`, `CLAUDE.md`)
- **codex** → `AGENTS.md` + `.codex/agents/*.toml`

Both assemble from the same neutral schema. This ships **bare mode** only (the agent runs
directly in the user's repo); container mode is deferred — see
`install/data/madagents/adapters/claude_code/CONTAINER_DEFERRED.md`.

## Where things live

The data these skills operate on lives in the MadAgents source repo (located automatically via
`git rev-parse --show-toplevel`):

- `install/data/madagents/` — the **neutral schema**: `agents/`, `context.md`, `rules/`,
  `orchestrator.md` (provider-agnostic; `{{DOCS}}` placeholder + `container-only` blocks).
- `install/data/madagents/adapters/<provider>/render.sh` — assembles the schema for one CLI
  (`claude_code` or `codex`).
- `install/data/madagents/examples/` — `build_example.sh <provider>` (runnable reference),
  `verify_install.sh` (checks), and `expected/<provider>/` (golden reference to review against).

Do **not** modify these source templates as part of an install — only write into the user's
target directory.
