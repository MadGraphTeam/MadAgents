# Phase 1: Generate Questions

Generates evaluation questions about MadGraph.

## Usage

```bash
./eval/examples/1_generate/run.sh                              # 3 questions (default)
./eval/examples/1_generate/run.sh -n 5                         # 5 questions
./eval/examples/1_generate/run.sh -n 2 --focus "jet matching"  # topic focus
./eval/examples/1_generate/run.sh --model haiku -n 3           # model override
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-n NUM` | 3 | Number of questions to generate |
| `--focus TEXT` | | Topic focus for the LLM |
| `--requirements TEXT` | | Additional requirements (e.g. difficulty) |
| `--model MODEL` | sonnet | Model override |
| `--prompts-dir DIR` | | Custom prompts directory |

## Prerequisites

```bash
./image/examples/create_image.sh    # build the container image
```

## Output

```
output/
  questions.json         # generated questions with reference answers
  transcripts/           # session transcripts and per-session workflow logs
  logs/                  # raw Claude CLI logs
```

The generated `questions.json` is the input to phase 2.
