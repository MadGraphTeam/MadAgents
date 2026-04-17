# MadAgents

[![arXiv](https://img.shields.io/badge/arXiv-2601.21015-b31b1b.svg)](https://arxiv.org/abs/2601.21015)

This is the **official implementation** of **MadAgents**.

- 📄 Paper: [arXiv:2601.21015](https://arxiv.org/abs/2601.21015)
- 📦 Supplementary material: `supplementary/`

---

## Changelog 🔥

- **[26/04/07]** **Self-improving docs** — MadAgents evaluates itself and refines the MadGraph documentation. See [Self-improving docs](#self-improving-docs). 🔥
- **[26/03/20]** Released **Claude Code implementation** — run MadAgents as a multi-agent system directly from the terminal, works with a Claude subscription, no API credits needed! See [Quick start (Claude Code)](#quick-start-claude-code). 🔥
- **[26/03/20]** Added **Anthropic model support** (Claude Opus 4.6, Sonnet 4.6, Haiku 4.5) — switch between OpenAI and Anthropic directly from the UI!
- **[26/03/20]** New **physics expert** worker for HEP theory and phenomenology, plus **three specialized reviewers** (plan, verification, presentation) for higher-quality answers!
- **[26/03/20]** **Parallel worker dispatch** — the orchestrator now runs multiple workers concurrently, with full agent traces and an expanded MadGraph documentation library.

---

## What can I do with MadAgents?

MadAgents is a set of **communicative agents** that support **MadGraph-centered HEP workflows**, including:

- **Install & configure** complex HEP toolchains
- **Teach & guide** users with step-by-step, executable instructions
- **Answer physics + implementation questions** and translate them into runnable workflows  
- **Run autonomous multi-step campaigns** and organize outputs + logs

---

## Two ways to run MadAgents

MadAgents can be used in two modes. Both run inside an Apptainer container.

| | Claude Code | API version |
| --- | --- | --- |
| **Interface** | Terminal (CLI) | Web UI (browser) |
| **Backend** | Claude Code multi-agent system | LangGraph + FastAPI |
| **Setup** | Claude Code CLI + Apptainer | API keys + Apptainer |
| **Authentication** | Claude subscription or API credits | OpenAI / Anthropic API keys |
| **Session management** | `--resume` / `--continue` flags | Browser-based |

---

## Quick start (Claude Code)

### 0) Requirements

- **Linux host** (or a Linux VM on Windows/macOS, see [Install Apptainer](#install-apptainer))
- **[Apptainer](https://apptainer.org/)** installed on the host (see [Install Apptainer](#install-apptainer))
- **[Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)** installed and authenticated (works with a Claude subscription or API credits)

### 1) Get the code

Clone or download this repository.

### 2) Build image + overlay

```bash
# Preinstalled MadGraph stack (ROOT, Pythia8, Delphes)
./image/create_image.sh --type preinstall
```

See [Build image](#build-image) for more options.

### 3) Run

```bash
./madrun_code.sh
```

To resume or continue a previous session:

```bash
./madrun_code.sh --resume              # Pick from past sessions
./madrun_code.sh --continue            # Continue most recent session
```

> Tip: any `config.env` value can be overridden for a single run via an environment variable, e.g. `ENABLE_DOC_EDITING=1 ./madrun_code.sh`. See [Temporary overrides](#temporary-overrides-environment-variables).

---

## Self-improving docs

MadAgents can improve its own MadGraph documentation. Enable doc-editing mode and ask the instance to guide you through it:

```bash
ENABLE_DOC_EDITING=1 ./madrun_code.sh
```

```
> How can I improve the MadGraph documentation?
```

> **Host requirements:** doc-editing mode launches an MCP server (`claude_code/mcp/docs_server.py`) on the **host**, not inside the container. The host Python environment must therefore have the dependencies from [`requirements-agent.txt`](requirements-agent.txt) installed. Set up a venv or conda env, install them, and activate it before running `madrun_code.sh`, e.g.:
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> pip install -r requirements-agent.txt
> ENABLE_DOC_EDITING=1 ./madrun_code.sh
> ```
>
> **Port:** the MCP server listens on **TCP 8089** on the host by default. Override with `MCP_PORT` (in `config.env` or as a one-shot env var) if that port is taken:
> ```bash
> MCP_PORT=9089 ENABLE_DOC_EDITING=1 ./madrun_code.sh
> ```
> If the chosen port is in use, the MCP server will fail to start — check `run_dir/workdirs/<stamp>/logs/mcp_docs_server.log`.

See [`claude_code/README.md`](claude_code/README.md) for the doc-editing skills the instance has access to.

For automated, batch-style runs (e.g. CI, overnight evaluations), use the host-side Python pipeline at [`eval/`](eval/) instead.

---

## Quick start (API version)

### 0) Requirements

- **Linux host** (or a Linux VM on Windows/macOS, see [Install Apptainer](#install-apptainer))
- **[Apptainer](https://apptainer.org/)** installed on the host (see [Install Apptainer](#install-apptainer))
- **OpenAI or Anthropic API key**
- **Network access** to OpenAI/Anthropic endpoints

### 1) Get the code

Clone or download this repository.

### 2) Configure

Copy `config.env.example` to `config.env` in the repo root, then edit:

```dotenv
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
LLM_API_KEY=""
APPTAINER_DIR="/path/to/apptainer/bin"
```

> **WARNING:** Do **not** commit real keys. Keep `config.env` local and git-ignored.

### 3) Build image + overlay

```bash
# Preinstalled MadGraph stack (ROOT, Pythia8, Delphes)
./image/create_image.sh --type preinstall

# Minimal MadGraph stack (ROOT only, no Pythia8/Delphes/HEPTools)
./image/create_image.sh --type minimal

# Clean base image (no preinstalled tools)
./image/create_image.sh --type clean
```

Creates:
- `image/madagents.sif` (Apptainer image)
- `image/mad_overlay.img` (overlay; persists container-side changes across runs)

### 4) Run

```bash
./madrun_api.sh
```

By default, the output is written to `./output` in the repository root.

Both `madrun_api.sh` and `madrun_code.sh` handle cleanup on exit. `cleanup_madrun.sh` is an optional cleanup helper that works for both and can be run at any time, but it is usually unnecessary unless a run is stuck or your terminal died:

```bash
./cleanup_madrun.sh
```

> Tip: any `config.env` value can be overridden for a single run via an environment variable, e.g. `FRONTEND_PORT=6000 ./madrun_api.sh`. See [Temporary overrides](#temporary-overrides-environment-variables).

---

## Startup output — API version (what you should see)

When you run `./madrun_api.sh` (from the repo root), the CLI should look like:

```
Starting MadAgents ...
Backend: http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
Apptainer>
```

If you don’t see this output, check out [Troubleshooting](#troubleshooting).

---

## Install Apptainer

We use **Apptainer** because it can *often* be installed and used **without sudo** (rootless / unprivileged), which is especially convenient on **HPC / computing clusters** where users typically do not have administrator rights.

Please follow the official documentation:
- **Official installation guide (all methods):** https://apptainer.org/docs/admin/main/installation.html
- **No-sudo (unprivileged) installation:** https://apptainer.org/docs/admin/main/installation.html#install-unprivileged-from-pre-built-binaries

On **Windows** and **macOS**, Apptainer does not run natively; you’ll need a **Linux VM** (recommended: **WSL2** on Windows, **Lima** on macOS):
- https://apptainer.org/docs/admin/main/installation.html#installation-on-windows-or-mac

If installation is **not possible in your environment** (e.g., required kernel features are disabled or local policy restricts installs), please contact your **cluster/system administrator** and request a site-wide Apptainer installation or the required system features.

---

## Configuration

Both modes read `config.env` from the repo root. Relative paths are resolved from the repo root.
Use `config.env.example` as the template if `config.env` is missing.

### Global settings (both modes)

- `APPTAINER_DIR` — directory containing the `apptainer` binary (required by `image/create_image.sh`).
- `APPTAINER_IMAGE` — path to the Apptainer `.sif` image (`image/madagents.sif`). Useful when sharing a prebuilt image from a common location instead of the per-clone default.
- `APPTAINER_OVERLAY` — path to the writable overlay image (`image/mad_overlay.img`).
- `OUTPUT_DIR` — outputs folder (`output`)
- `RUN_DIR` — runtime folder for logs, locks, sockets (`run_dir`)

> Relative paths for `APPTAINER_IMAGE` / `APPTAINER_OVERLAY` resolve against the repo root; absolute paths are used as-is.

### API version

#### Required

Provide at least one API key; provider-specific keys take precedence over `LLM_API_KEY`.

- `OPENAI_API_KEY` — OpenAI API key (preferred for OpenAI models if set).
- `ANTHROPIC_API_KEY` — Anthropic API key (preferred for Anthropic models if set).
- `LLM_API_KEY` — fallback API key when provider-specific keys are not set.

#### Optional (defaults shown)

- `FRONTEND_PORT` — UI port (`5173`)
- `BACKEND_PORT` — API port (`8000`)
- `APPTAINER_CACHEDIR` — Apptainer cache (`.apptainer/cache`)
- `APPTAINER_CONFIGDIR` — Apptainer config (`.apptainer`)
- `NPM_CONFIG_CACHE` — npm cache (`.npm`)

#### Model defaults

- Agents use GPT‑5.1 models by default, except the Plan‑Updater which uses GPT‑5‑mini.
- You can change all model selections from the UI; provider is inferred from the model name (`gpt-*` → OpenAI, `claude-*` → Anthropic).

#### Minimal example

```dotenv
OPENAI_API_KEY="your-openai-key-here"
ANTHROPIC_API_KEY=""
LLM_API_KEY=""
APPTAINER_DIR="/path/to/apptainer"
```

### Claude Code version

Claude Code handles its own authentication; API keys from `config.env` are not used.

- `CLAUDE_CONFIG_DIR` — Claude Code configuration directory (`claude_code/.config/.claude`)
- `ENABLE_VERIFY` — enable the verify-claims skill (`0`)
- `ENABLE_DOC_EDITING` — enable documentation editing skills and agent teams, implies verify (`0`)

See [claude_code/README.md](claude_code/README.md) for details on the available modes, skills, and documentation improvement workflows.

### Temporary overrides (environment variables)

Any value in `config.env` can be overridden for a single run by setting the variable in the caller environment. This works for both `madrun_api.sh` and `madrun_code.sh`. Precedence: **caller env > config.env > script defaults**.

```bash
FRONTEND_PORT=6000 BACKEND_PORT=9000 ./madrun_api.sh
OUTPUT_DIR=/tmp/madagents_out ./madrun_code.sh
ENABLE_DOC_EDITING=1 ./madrun_code.sh
```

---

## Build image

All image definitions and build scripts live in `image/`.

```bash
./image/create_image.sh --type TYPE
```

Three image variants are supported:

- **`--type preinstall`** builds from `image/madagents_preinstall.def` and includes a **basic MadGraph stack**
  (ROOT, Pythia8, Delphes, FastJet, LHAPDF6). The build downloads two tarballs; if the upstream links change, you may need
  to update them in the definition file.
- **`--type minimal`** builds from `image/madagents_minimal.def` and includes a **minimal MadGraph installation**
  (MG5_aMC and ROOT only, **no** HEPTools — Pythia8, Delphes, FastJet, LHAPDF6 are skipped). Useful for tree-level
  matrix-element workflows where showering/detector simulation is not needed; builds faster and produces a smaller image.
- **`--type clean`** builds from `image/madagents_clean.def` and includes **no preinstalled tools**.

Both options create `image/madagents.sif` and `image/mad_overlay.img` (default size ~10GB), overwriting
any existing files with the same names.

**Notes**
- The build uses `apptainer build --fakeroot`. If your system disallows fakeroot, see
  [Troubleshooting](#troubleshooting).
- If you only need to rebuild the overlay, run:

```bash
./image/create_overlay.sh
```

---

## Stop / cleanup

Both `madrun_api.sh` and `madrun_code.sh` trap exit signals and stop the Apptainer instance automatically.
`cleanup_madrun.sh` is safe to run at any time for either variant, but it is usually unnecessary unless the process is wedged or your terminal died:

```bash
./cleanup_madrun.sh
```

Manual fallback:

```bash
apptainer instance list
apptainer instance stop INSTANCE_NAME
```

The `INSTANCE_NAME` is recorded in `run_dir/logs/instance_name.txt` (API version) or `run_dir/workdirs/<stamp>/logs/instance_name.txt` (Claude Code version) and is usually `madagents` or `madagents-cc`.

---

## Data, outputs, and persistence

- `OUTPUT_DIR` is where runtime outputs are written.
- `RUN_DIR` holds logs, locks, and instance metadata and can be deleted when you are done.
- The container is launched with an overlay (`image/mad_overlay.img`) so changes inside the container
  persist across runs until you rebuild or delete the overlay.

Want a “clean slate” run?
1. Stop the instance (`./cleanup_madrun.sh`)
2. Delete the overlay (`rm image/mad_overlay.img`)
3. Recreate it (`./image/create_overlay.sh`), and optionally rebuild the `.sif`

---

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `config.env not found` | Run commands from the repo root or copy `config.env.example` to `config.env`. |
| `apptainer not found` | Install Apptainer or set `APPTAINER_DIR` in `config.env`. |
| `port already in use` | Choose free ports via `FRONTEND_PORT` / `BACKEND_PORT` in `config.env` or as env var overrides. |
| Build fails | Ensure Apptainer supports `--fakeroot` and you have permissions to use it. |
| Preinstall build fails | The tarball download URLs in `image/madagents_preinstall.def` may have changed; update them and retry. |
| `cannot check port availability` | Install `ss`, `lsof`, or `python` so the script can test ports. |
| No UI link printed | Check `run_dir/logs/madagents_links.txt` and `run_dir/logs/madrun.log`. |
| UI not reachable from your browser | If running on a cluster or remote machine, you must **port‑forward** the backend and frontend ports (see `port_forward.sh`). |

### Multiple runs

MadAgents supports **one run per clone**. For multiple runs, **clone the repo multiple times** and
use **different ports** for each run. See [Temporary overrides (environment variables)](#temporary-overrides-environment-variables) for
how to set `FRONTEND_PORT` and `BACKEND_PORT`.

### Port forwarding (remote / cluster)

If you run MadAgents on a **remote machine or cluster**, the UI will not be reachable from your
local browser until you **port‑forward** the backend and frontend ports.

This repo includes a helper script: `port_forward.sh`.

1) Edit `port_forward.sh` and set `SSH_TARGET` to your SSH destination, e.g.:

```bash
SSH_TARGET="user@remote-host"
```

2) Run the script **from your local machine (the one with the browser)** and pass the ports you
need to forward:

```bash
./port_forward.sh --port 8000,5173
```

3) Open the UI locally in your browser:
`http://127.0.0.1:5173`

If you changed ports via `FRONTEND_PORT` / `BACKEND_PORT`, pass those same ports to
`port_forward.sh`.

### Cluster / HPC notes (build troubleshooting)

Apptainer is commonly used on clusters because **running containers does not require sudo** once installed.
Installation itself may still require admin help.

**If `--fakeroot` works**  
✅ Build normally with `./image/create_image.sh`.

**If `--fakeroot` is not allowed**  
Typical options:
1. **Use a prebuilt `.sif`**: build on a machine that supports fakeroot and distribute the image
   (e.g. GitHub Releases or a shared cluster filesystem).
2. Ask admins about enabling user namespaces / fakeroot (policy-dependent).

---

## Security

- `config.env` contains secrets (OpenAI API key). Treat it like a password.
- `config.env.example` is a safe template and can be committed.
- Do not commit real keys to version control.
- Logs may contain request metadata; store them appropriately.

---

## Citation

If you used MadAgents in your research, please cite us as follows:

```bibtex
@article{Plehn:2026gxv,
    author = "Plehn, Tilman and Schiller, Daniel and Schmal, Nikita",
    title = "{MadAgents}",
    eprint = "2601.21015",
    archivePrefix = "arXiv",
    primaryClass = "hep-ph",
    month = "1",
    year = "2026"
}
```
