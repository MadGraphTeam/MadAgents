# Legacy releases

Superseded MadAgents releases, kept here so they stay readable and runnable without
digging through git history.

> **These are frozen and unmaintained.** They are preserved as a record of the
> published system, not as a supported way to run MadAgents. Their pinned
> dependencies will stop resolving over time. For current MadAgents, see the
> repository root.

Each folder mirrors the repository layout it was written against, so paths resolve
from the folder itself and the code runs unmodified. What *did* shift: defaults that
used to resolve at the repository root — `config.env`, `output/`, `run_dir/`,
`image/`, `.apptainer/` — now resolve **inside** the release folder. Each folder
therefore carries its own `config.env.example`, `requirements-agent.txt`,
`cleanup_madrun.sh` and `image/` build tooling.

---

## `madagents_v1/` — the API version

The original MadAgents: a LangGraph + FastAPI backend with a browser UI, driven by
OpenAI or Anthropic API keys. **This is the system described in
[arXiv:2601.21015](https://arxiv.org/abs/2601.21015)** — its agent roster
(Orchestrator, Planner, Plan-Updater, Reviewer, Summarizer, Researcher, PDF-Reader,
Plotter, Script-Operator, CLI-Operator, MadGraph-Operator) is the one whose prompts
are reproduced in `supplementary/prompts/`.

```bash
cd legacy/madagents_v1
cp config.env.example config.env       # set APPTAINER_DIR + an OpenAI/Anthropic key
./image/create_image.sh --type preinstall
./madrun_api.sh                        # backend :8000, frontend :5173
```

`port_forward.sh` forwards those ports when running on a remote host or cluster.
Configuration keys, model defaults and troubleshooting are documented in the
repository README as it stood at the time — see git history prior to the `legacy/`
reorganisation.

Contents: `src/madagents/` (agents, backend, frontend UI, LLM runtimes, CLI bridge,
and the MadGraph documentation corpus at `src/madagents/software_instructions/`),
`madrun_api.sh`, `port_forward.sh`.

---

## `madagents_v2/` — the first Claude Code version

MadAgents as a Claude Code multi-agent system: the CLI orchestrating subagents inside
the same Apptainer container, authenticated by a Claude subscription rather than API
keys. Includes the two optional modes and the automated evaluation pipeline that
drove them.

```bash
cd legacy/madagents_v2
cp config.env.example config.env       # set APPTAINER_DIR
./image/create_image.sh --type preinstall
./madrun_code.sh                       # all arguments are forwarded to `claude`
```

`madrun_code.sh` has no flags of its own; it is configured by environment variables,
which select one of three agent configurations (assembled by
`claude_code/scripts/build_claude_dir.py`):

| Mode | What it deploys |
| --- | --- |
| default | 8 workers — `madgraph-operator`, `script-operator`, `plotter`, `researcher`, `pdf-reader`, `physics-expert`, `presentation-reviewer`, `verification-reviewer`; rules `correctness`, `mandatory-reviews`. The orchestrator lives in the system prompt. |
| `ENABLE_VERIFY=1` | adds the `claim-extractor` and `verifier` agents |
| `ENABLE_DOC_EDITING=1` | implies `ENABLE_VERIFY`; adds the `doc-editor`, `doc-style-reviewer`, `doc-quality-reviewer`, `grader`, `claim-triage`, `claim-remember` and `orchestrator` agents, the `docs-editing` rule, the `edit-docs` / `get-docs` / `train-docs` / `diagnose-docs` / `generate-questions` skills, and agent teams |

Doc-editing mode additionally needs a **host** Python environment with
`requirements-agent.txt` installed (it starts `claude_code/mcp/docs_server.py` on TCP
8089, overridable via `MCP_PORT`) and `tmux` inside the container.

### `eval/` — the automated evaluation and doc-improvement pipeline

The batch counterpart to doc-editing mode: generate questions → answer them in a
container → verify each extracted claim → grade → diagnose which documentation gaps
caused the errors → improve the docs → re-evaluate, iterating until questions
converge.

```bash
./image/examples/create_image.sh       # the pipeline uses its own image tooling
./eval/run.sh                          # --config / --run-dir / --apply-docs
./eval/apply_docs.sh eval/runs/<run>   # write improved docs back into the corpus
```

Runs on the host and needs the `MadAgents` conda environment; each Claude invocation
goes into an Apptainer container. Configuration is `eval/config/pipeline.yaml`.
`eval/examples/` holds eight standalone single-phase examples (`1_generate` …
`8_iterate`), each with its own README and `run.sh`. Per-example run artifacts
(`output/`, `db/`, `claude_config/`, `workspace/`) are git-ignored — they carry
session credentials and host-specific paths — so an example ships its driver and
documentation only, and produces the artifacts its own README describes when run.

### `install/` — the native installers (Claude Code and Codex)

The agent-driven way to set v2 up in an arbitrary repo, without the container. An
installer session — run under either Claude Code or Codex — reads a provider-neutral
schema and assembles a concrete setup for whichever CLI will *run* MadAgents, leaving
a `start_madagents.sh` launcher behind. This is the origin of Codex support.

```bash
cd legacy/madagents_v2/install/claude_code && claude    # or install/codex && codex
```

It deploys v2's **default mode** — the same 8 workers and `correctness` /
`mandatory-reviews` rules in the table above; the verify, doc-editing and eval
machinery is deliberately left out. `data/madagents/` holds the neutral schema
(`agents/`, `context.md`, `rules/`, `orchestrator.md`) plus a `render.sh` adapter per
provider; `data/installer/` holds the installer logic, from which the two session
directories are generated by `build_installers.sh` so they cannot drift.

Superseded by the v3 installer at the repository root (`install/`), which targets the
v3 agent system and memory packs, and by `tools/render_codex.py` for the Codex half.
The v2 approach — a provider-neutral schema plus a `render.sh` per adapter — did not
carry over: v3 keeps `madagents/` canonical and *generates* `madagents_codex/` from it,
because the v3 system is edited by its own agents (`/ma-doctor`) and a rendered
canonical tree would have broken that.

Contents: `claude_code/` (agent configs, doc MCP server, build scripts),
`install/` (native installers + provider adapters),
`madrun_code.sh`, `eval/` (pipeline driver, config, examples), `src/eval/` (pipeline
library), `src/claude_code/` (the config the pipeline evaluates), and its own copy of
the MadGraph documentation corpus at `src/madagents/software_instructions/` — the
corpus is what doc-editing mode and the pipeline write to.
