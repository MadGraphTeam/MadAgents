# Phase 6: Improve

Applies documentation improvements based on the diagnoses, then runs three parallel checks (factual verification, style, quality). If any check fails, feedback is collected and the improver revises. Loops up to `--max-rounds` rounds.

## Usage

```bash
./eval/examples/6_improve/run.sh                              # default (sonnet + haiku)
./eval/examples/6_improve/run.sh --model sonnet --max-rounds 5
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | sonnet | Model for the improver and fact verifier |
| `--check-model MODEL` | haiku | Model for the style and quality checks |
| `--max-rounds N` | 10 | Maximum revision rounds |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/2_answer/run.sh
./eval/examples/3_verify/run.sh
./eval/examples/5_diagnose/run.sh
```

## Output

```
output/
  improve/
    improve_summary.json   # rounds, changed files, approval status
    docs.diff              # unified diff of all changes
    round_1/               # per-round artifacts (claims, verdicts, style, quality)
    round_2/
    staging/               # new claims for DB merge
  diagnose/                # copied from phase 5
  verification/            # copied from phase 3
  transcripts/
  logs/
docs_working/              # the improved documentation files
```
