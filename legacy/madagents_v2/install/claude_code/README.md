# MadAgents installer (Claude Code)

Run Claude Code **here** and ask it to install MadAgents into your repo:

```bash
cd install/claude_code
claude
# then, in the session:
#   /install-madagents     set MadAgents up in a target repo (Claude Code or Codex)
#   /update-madagents      update an existing install (3-way merge, preserves your edits)
```

The agent picks up its job from `.claude/CLAUDE.md` and the install/update **skills** from
`.claude/skills/`. It can install MadAgents for **either provider** (Claude Code or Codex) —
it will ask which.

The schema, adapters, and examples those skills operate on live in
[`../data/madagents/`](../data/madagents/).

> This directory's `.claude/` is **assembled** from the neutral installer source
> (`../data/installer/`) by `build_installers.sh`. Edit the source, not this copy.
> The Codex installer is the sibling [`../codex/`](../codex/).
