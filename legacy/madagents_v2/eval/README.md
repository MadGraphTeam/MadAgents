# Eval Pipeline

Automated evaluation and documentation improvement pipeline for MadAgents. The pipeline generates questions, runs MadAgents to answer them, verifies the answers, identifies documentation gaps, edits the docs, and re-evaluates — iterating until the agent answers correctly.

## Quick Start

```bash
# 1. Build the container image (once).
./image/examples/create_image.sh

# 2. Run the full pipeline with the default config.
./eval/run.sh

# 3. Apply the doc improvements to the repository.
./eval/apply_docs.sh eval/runs/<run_dir>
```

## What the Pipeline Does

```
generate → answer → verify → grade → diagnose → improve
                                                    │
                                              ┌─────┘
                                              ▼
                                    ┌─── reeval ◄──┐
                                    │              │
                                    └── diagnose ──┤
                                    └── improve ───┘
                                       (iteration loop)
```

1. **Generate** — create evaluation questions about MadGraph.
2. **Answer** — MadAgents answers each question inside a container.
3. **Verify** — extract factual claims from the answer and check each one.
4. **Grade** — assign `CORRECT` / `INCORRECT` plus tags (e.g. `has_errors`, `inefficient`, `reviewer_corrections`).
5. **Diagnose** — identify documentation gaps that caused errors.
6. **Improve** — edit docs and check the changes (factual + style + quality).
7. **Reeval** — re-answer failed questions with the improved docs.
8. **Iterate** — repeat diagnose → improve → reeval until questions converge or `max_iterations` is reached.

## Running the Pipeline

```bash
./eval/run.sh                                      # default config
./eval/run.sh --config eval/config/pipeline.yaml   # custom config
./eval/run.sh --run-dir eval/runs/my_experiment    # custom run dir
./eval/run.sh --apply-docs                         # apply changes after the run
```

The pipeline runs on the host (requires the `MadAgents` conda environment). Each Claude invocation runs inside an Apptainer container.

To run a single phase on its own, see [examples/](examples/).

## Configuration

The pipeline is configured via a YAML file (default: `eval/config/pipeline.yaml`).

### Questions

```yaml
questions:
  mode: generate          # "generate" or "file"
  file: null              # path to existing questions.json (when mode=file)
  count: 2                # number of questions to generate
  focus: ""               # topic focus (e.g. "jet matching and merging")
  requirements: "..."     # additional requirements (e.g. difficulty level)
```

| Field | Default | Description |
|-------|---------|-------------|
| `mode` | `generate` | `generate` creates new questions; `file` loads from an existing JSON file |
| `file` | `null` | Path to a questions JSON file (only used when `mode: file`) |
| `count` | `2` | Number of questions to generate |
| `focus` | `""` | Topic guidance for the question generator |
| `requirements` | `""` | Additional constraints (e.g. difficulty, question style) |

### Models

```yaml
models:
  # Expensive tasks (sonnet)
  answerer: sonnet
  verifier: sonnet
  diagnoser: sonnet
  improver: sonnet
  fact_verifier: sonnet

  # Cheap tasks (haiku)
  supervisor: haiku
  extractor: haiku
  triage: haiku
  remember: haiku
  grader: haiku
  style_checker: haiku
  quality_checker: haiku
```

Each role uses its own model. Expensive tasks default to `sonnet`; cheap text-analysis tasks default to `haiku`.

### Parallelism

```yaml
parallel:
  max_questions: 3            # concurrent questions
  max_api_calls: 5            # concurrent API calls (rate-limit safety)
```

| Field | Default | Description |
|-------|---------|-------------|
| `max_questions` | `3` | Maximum questions processed concurrently |
| `max_api_calls` | `5` | Global cap on concurrent API calls |

### Phase Settings

```yaml
answer:
  max_turns: 3                # max answer ↔ supervise turns per question

verify:
  max_extract_retries: 3      # claim extraction retry attempts
  max_verify_retries: 2       # claim verification retry attempts

improve:
  max_rounds: 10              # max improve → check → revise rounds

iterate:
  max_iterations: 10          # max diagnose → improve → reeval cycles
```

| Field | Default | Description |
|-------|---------|-------------|
| `answer.max_turns` | `3` | Answer-supervisor loop turns before accepting |
| `verify.max_extract_retries` | `3` | Retries for claim extraction validation |
| `verify.max_verify_retries` | `2` | Retries for claim verification validation |
| `improve.max_rounds` | `10` | Revision rounds within a single improve phase |
| `iterate.max_iterations` | `10` | Outer loop: diagnose → improve → reeval cycles |

### Container

```yaml
container:
  image: image/examples/clean/image.sif
  overlay_size_mb: 4096
```

| Field | Default | Description |
|-------|---------|-------------|
| `image` | `image/examples/clean/image.sif` | Path to the Apptainer SIF image (relative to repo root) |
| `overlay_size_mb` | `4096` | Size of the writable overlay (used for MadGraph installs) |

### Paths

```yaml
paths:
  docs: src/madagents/software_instructions/madgraph
  docs_overview: src/madagents/software_instructions/madgraph.md
  src: src
  claude_code: src/claude_code
  prompts_dir: null           # null = use built-in defaults
```

| Field | Default | Description |
|-------|---------|-------------|
| `docs` | `src/madagents/.../madgraph` | MadGraph documentation directory |
| `docs_overview` | `src/madagents/.../madgraph.md` | Documentation overview file |
| `src` | `src` | Source directory (mounted as `/src` in containers) |
| `claude_code` | `src/claude_code` | Claude Code config directory (agents, rules, settings) |
| `prompts_dir` | `null` | Custom prompts directory; `null` uses built-in defaults |

## Run Directory

Each run creates a timestamped directory under `eval/runs/`:

```
eval/runs/250401_120000/
  config.yaml                  # copy of the config used
  state.json                   # pipeline progress (for resumability)
  questions.json               # generated or loaded questions
  docs_working/                # improved documentation (final output)
  db/claim_db.json             # claim database (grows across runs)
  questions/q000/              # per-question results
    answer/        verify/        grade/        diagnose/
  improve_0/                   # initial improvement pass
    docs.diff
    improve_summary.json
  iter_1/                      # iteration 1
    reeval/q000/  diagnose/
  improve_1/                   # iteration 1 improvement
  iter_2/
    ...
```

After a run, the most useful artifacts are:

- `docs_working/` — the improved documentation
- `improve_*/docs.diff` — unified diffs for each improvement pass
- `questions/q*/grade/grade.json` — per-question grades
- `iter_*/reeval/q*/grade/grade.json` — per-iteration regrade results

## Resumability

If a run is interrupted, re-running with the same `--run-dir` resumes from the last completed phase:

```bash
./eval/run.sh --run-dir eval/runs/250401_120000
```

Each step skips work whose output already exists.

## Applying Doc Changes

After a successful run, apply the improved documentation to the repository:

```bash
# Show the diff and ask for confirmation.
./eval/apply_docs.sh eval/runs/250401_120000

# Apply without confirmation.
./eval/apply_docs.sh eval/runs/250401_120000 --yes
```

This copies the files from `docs_working/` to `src/madagents/software_instructions/madgraph/` and updates the overview file.

## Convergence

A question **converges** when its grade is `CORRECT` with no improvement-triggering tags. The iteration loop stops when all questions converge or `max_iterations` is reached.

## Prerequisites

1. **Conda environment**: `conda activate MadAgents`
2. **Container image**: `./image/examples/create_image.sh`
3. **Claude authentication**: run `claude` once on the host to create credentials
4. **Apptainer**: set `APPTAINER_DIR` in `config.env` if `apptainer` is not on `$PATH`

## Examples

See [examples/](examples/) for running individual phases step by step. Each example has its own README with usage, options, and output.
