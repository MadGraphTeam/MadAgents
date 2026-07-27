# Install examples & reference scripts

Runnable references that make the agent-driven `install-madagents` skill more reliable:
the agent can read them as ground truth and execute them to confirm the mechanics work.

| Script | What it does |
|---|---|
| `build_example.sh [target]` | Performs a full **bare** install into a demo target (default: a temp dir) using the exact render/assemble/copy/launcher mechanics, then runs `verify_install.sh`. The canonical mechanical reference + smoke test. |
| `verify_install.sh <target> <bare\|container>` | Objective pass/fail check of a finished install: structure, all 8 agents, nothing left unrendered, operator card, docs, launcher (incl. `bash -n`), and mode-specific paths. Exit 0 = all pass. Used by the skill's verify step. |

## Quick use

```bash
# Render a reference bare install and verify it (no container/Apptainer needed):
./build_example.sh /tmp/madagents_demo

# Check an existing install:
./verify_install.sh /path/to/repo bare
./verify_install.sh /path/to/repo container
```

`build_example.sh` covers bare mode end-to-end (fully runnable without Apptainer).
Container mode adds the Apptainer prerequisites (image build/reuse, overlay) described in
the skill; `verify_install.sh container` validates the resulting files either way.

> These scripts mirror the skill's steps exactly. If you change the templates or the skill's
> mechanics, re-run `build_example.sh` — it is the smoke test that keeps them honest.
