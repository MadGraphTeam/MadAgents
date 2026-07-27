# MadAgents installer (Codex)

Run Codex **here** and ask it to install MadAgents into your repo:

```bash
cd install/codex
codex
# then, in the session:
#   /skills                 list skills, or type $install-madagents / $update-madagents
#   install MadAgents       (describe the task; Codex selects the install-madagents skill)
```

The agent picks up its job from `AGENTS.md` and the install/update **skills** from
`.agents/skills/` in this directory. It can install MadAgents for **either provider**
(Claude Code or Codex) — it will ask which.

The schema, adapters, and examples those skills operate on live in
[`../data/madagents/`](../data/madagents/).

> This directory is **assembled** from the neutral installer source
> (`../data/installer/`) by `build_installers.sh`. Edit the source, not this copy.
> The Claude Code installer is the sibling [`../claude_code/`](../claude_code/).
