# MadAgents — neutral schema + provider adapters

This directory defines **what MadAgents is**, independent of any coding-agent CLI, plus the
per-provider **adapters** that assemble it into a concrete install. It is the data the
installer skills operate on — the installer itself lives in [`../installer/`](../installer/),
and the runnable installer sessions are [`../../claude_code/`](../../claude_code/) and
[`../../codex/`](../../codex/).

> Scope: the **default** MadAgents setup (orchestrator + workers + reviewers). The
> verify / doc-editing / eval machinery from the top-level `claude_code/` setup is left out here.

## Layout

```
install/data/madagents/
  agents/*.md                  # provider-agnostic agent defs (name/description frontmatter + body)
                               #   incl. madgraph-operator.md (a header; the docs overview is appended at render)
  context.md                   # environment + style (becomes CLAUDE.md / top of AGENTS.md)
  rules/{correctness,mandatory-reviews}.md
  orchestrator.md              # the delegation role
  adapters/
    claude_code/
      render.sh                # schema -> .claude payload (CLAUDE.block.md, rules/, agents/*.md, …)
      launchers/start_madagents.{bare,container}.sh
      CONTAINER_DEFERRED.md    # container mode is built but not exposed yet
    codex/
      render.sh                # schema -> Codex payload (AGENTS.block.md, agents/*.toml, config.toml)
      agent_to_toml.py         # agent .md -> Codex subagent .toml
      config.toml  launchers/start_madagents.sh
  examples/
    build_example.sh <provider>   # runnable end-to-end install + verify
    verify_install.sh             # objective pass/fail checks for any install
    regen_expected.sh / check_expected.sh   # golden-example regen + regression check
    expected/{claude_code,codex}/ # committed, sanitized golden renders
```

Agents stay Markdown + `name`/`description` frontmatter (a neutral form both CLIs use). The
content carries one placeholder, `{{DOCS}}` (the read-only MadGraph docs location), plus
`<!-- container-only -->` blocks (and a `{{REPO}}` placeholder inside them) for a future
**container mode** — the bare renderer strips those blocks entirely. See
`adapters/claude_code/CONTAINER_DEFERRED.md`.

## How each adapter assembles the schema

| Schema element | **claude_code** | **codex** |
| --- | --- | --- |
| `agents/*.md` | → `.claude/agents/*.md` | → `.codex/agents/*.toml` (`name`/`description`/`developer_instructions`) |
| `context.md` | → `.claude/CLAUDE.md` block | → top of `AGENTS.md` |
| `rules/*` | → `.claude/rules/*` | → appended to `AGENTS.md` |
| `orchestrator.md` | → `--append-system-prompt` at launch | → appended to `AGENTS.md` |
| launcher | `start_madagents.sh` → `claude` | `start_madagents.sh` → `codex` |

The MadAgents content always lives in a `<!-- MadAgents:begin/end -->` block inside
`CLAUDE.md`/`AGENTS.md`, so an install merges into a user's existing instruction file.

## Produced at install time (not stored here)

1. **`madgraph-operator`** — the operator card/agent = its header + the MadGraph overview
   (`src/madagents/software_instructions/madgraph.md`, headings shifted +1).
2. **The MadGraph docs** — copied from `src/madagents/software_instructions/madgraph/` into
   `<repo>/.madagents/madgraph_docs`. Referenced from source, not duplicated here.
3. **A launcher** — `start_madagents.sh` runs `claude`/`codex` in the repo and **forwards args
   and env** (positional args pass through; `--env KEY=VALUE` sets env vars).
4. **A manifest** — `<repo>/.madagents/install.json` records the source **commit id** +
   `provider` + version label. No base snapshot is stored.

## Updating

`update-madagents` updates an install while preserving the user's edits via a **3-way merge**.
Because nothing pristine is stored in the target, the merge **base** (the original of the
installed version) is *reconstructed* by re-rendering the schema at the recorded commit
(`git archive <source_commit> -- install/data/madagents src/madagents/software_instructions`).
Per file: `current == base` → take new; user-edited only → keep theirs; both changed →
`git merge-file` (clean merge keeps both; overlap → conflict markers + `.orig` backup). This
applies to everything installed (agents, rules, the instruction block, docs, launcher) and is
provider-aware.

## Status

Bare install + update are implemented and validated for **both providers** (Claude Code and
Codex). Container mode is built but deferred (see
`adapters/claude_code/CONTAINER_DEFERRED.md`).
