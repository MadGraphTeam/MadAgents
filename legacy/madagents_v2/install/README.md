# MadAgents installers

Set MadAgents up in any repo, using whichever coding agent you prefer as the **installer**,
and targeting whichever coding agent will **run** MadAgents.

## Two installer sessions (pick one to run)

| Run the installer with | Go here | How |
|---|---|---|
| **Claude Code** | [`claude_code/`](claude_code/) | `cd install/claude_code && claude` |
| **Codex** | [`codex/`](codex/) | `cd install/codex && codex` |

Either installer can install MadAgents for **either provider** — it asks `claude_code` or
`codex` and assembles the right setup in your target repo, with a `start_madagents.sh` launcher.

## Layout

```
install/
  claude_code/   codex/        # installer sessions (ASSEMBLED — don't edit directly)
  data/
    installer/                 # the installer itself, provider-agnostic
      orientation.md  skills/  build_installers.sh
    madagents/                 # what MadAgents IS — the neutral schema
      agents/ context.md rules/ orchestrator.md
      adapters/{claude_code,codex}/   # assemble the schema for each CLI
      examples/                # build_example.sh, verify_install.sh, expected/ (golden)
```

The session dirs are generated from `data/installer/` by `build_installers.sh` (so the two
installers never drift). Edit `data/installer/` (installer logic) or `data/madagents/`
(MadAgents content), then re-run the build.
