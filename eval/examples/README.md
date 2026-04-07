# Eval Pipeline Examples

Step-by-step examples for the MadAgents evaluation pipeline. Each phase runs as a standalone script that reads input from the previous phase's output. Use these to inspect, debug, or run a single phase outside the full pipeline.

For the full automated pipeline, see [`../README.md`](../README.md).

## Phases

```
1_generate  →  2_answer  →  3_verify  →  4_grade  →  5_diagnose  →  6_improve
                                                                         │
                                                                   7_reeval
                                                                         │
                                                                   8_iterate (loop)
```

| Phase | Purpose |
|-------|---------|
| [1_generate](1_generate/) | Generate evaluation questions |
| [2_answer](2_answer/) | Answer a question with MadAgents |
| [3_verify](3_verify/) | Extract and verify factual claims from the answer |
| [4_grade](4_grade/) | Grade the answer (`CORRECT` / `INCORRECT` + tags) |
| [5_diagnose](5_diagnose/) | Diagnose documentation gaps from the failures |
| [6_improve](6_improve/) | Edit docs and check the changes |
| [7_reeval](7_reeval/) | Re-answer with improved docs and regrade |
| [8_iterate](8_iterate/) | One full diagnose → improve → reeval cycle |

## Prerequisites

1. Build the container image:
   ```bash
   ./image/examples/create_image.sh
   ```
2. Authenticate Claude Code (run `claude` once on the host).
3. Set `APPTAINER_DIR` in `config.env` if `apptainer` is not on `$PATH`.

## Quick Start

Run the phases sequentially:

```bash
./eval/examples/1_generate/run.sh -n 3
./eval/examples/2_answer/run.sh
./eval/examples/3_verify/run.sh
./eval/examples/4_grade/run.sh
./eval/examples/5_diagnose/run.sh
./eval/examples/6_improve/run.sh
./eval/examples/7_reeval/run.sh
./eval/examples/8_iterate/run.sh --from-7
./eval/examples/8_iterate/run.sh          # repeat for further iterations
```

Each phase has its own README with usage, options, and output details.
