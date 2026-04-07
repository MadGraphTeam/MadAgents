# lib/ -- Shared Container Setup

`container.sh` is sourced by every example's `run.sh`. It provides:

- **`REPO_ROOT`** -- absolute path to the repository root
- **`APPTAINER_BIN`** -- path to the `apptainer` binary
- **`CONTAINER_FLAGS`** -- common `apptainer exec` flags (`--fakeroot`, `--cleanenv`, `--writable-tmpfs`, `--no-mount home,cwd`)
- **`CONTAINER_ENV`** -- `--env` flags for `CLAUDE_CONFIG_DIR`, `PATH`, `TERM`, etc.
- **`CONTAINER_BINDS`** -- common `-B` mounts: `/src` (eval harness), `/claude_code`, `/madgraph_docs`
- **`CLAUDE_BIND_ARGS`** -- bind mount for the Claude CLI installation (auto-detected)

## Helper Functions

- **`init_claude_config DIR`** -- creates a fresh config directory with credentials and settings copied from the host
- **`build_example_claude_dir DIR [--type bare|madagents]`** -- builds a `.claude/` directory using `scripts/build_claude_dir.py`

## Configuration

Reads `config.env` from the repo root. Key variables:

- `APPTAINER_DIR` -- directory containing the `apptainer` binary
- `CLAUDE_CONFIG_DIR` -- host path to Claude credentials (default: `~/.config/.claude`)

## Usage

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/container.sh"

"$APPTAINER_BIN" exec \
  "${CONTAINER_FLAGS[@]}" \
  "${CONTAINER_ENV[@]}" \
  "${CONTAINER_BINDS[@]}" \
  "${CLAUDE_BIND_ARGS[@]}" \
  "$SIF_PATH" \
  python3 /my_script.py
```
