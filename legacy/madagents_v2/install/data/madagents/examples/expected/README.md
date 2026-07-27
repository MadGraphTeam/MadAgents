# Golden example setups

Committed reference renders of the neutral MadAgents schema, one per provider:

- `claude_code/` — the `.claude/` payload (`CLAUDE.block.md`, `rules/`, `agents/*.md`,
  `system-prompt-append.md`, `start_madagents.sh`).
- `codex/` — the Codex payload (`AGENTS.block.md`, `agents/*.toml`, `config.toml`,
  `start_madagents.sh`).

They show exactly what each adapter assembles, and back the regression check
(`check_expected.sh` re-renders and diffs against these; `regen_expected.sh` refreshes them).

## Sanitized — no private information

These are generated with **no real paths or secrets**:

- rendered with the docs path as the literal token **`<DOCS>`** (a real install substitutes the
  user's `<repo>/.madagents/madgraph_docs`), so no filesystem paths appear;
- the copied `madgraph_docs/` tree is **excluded** (it is a verbatim copy of
  `src/madagents/software_instructions/madgraph` — no need to duplicate it here);
- no auth, keys, hostnames, or user data.

If you change the schema or an adapter, run `regen_expected.sh` and commit the result.
