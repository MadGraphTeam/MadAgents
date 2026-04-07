# Phase 8: Iterate

Combines diagnose, improve, and re-evaluate in one step. Each invocation performs **one** iteration. Run the script repeatedly to keep improving documentation until the grade converges.

## Usage

```bash
./eval/examples/8_iterate/run.sh --from-7        # first iteration (reads from 7_reeval)
./eval/examples/8_iterate/run.sh                 # subsequent iterations (reads from latest)
./eval/examples/8_iterate/run.sh --model sonnet
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--from-7` | | Read input from `7_reeval` (required for the first iteration) |
| `--model MODEL` | sonnet | Model for main tasks |
| `--check-model MODEL` | haiku | Model for cheap checks |
| `--max-improve-rounds N` | 10 | Max improve revision rounds |
| `--max-turns N` | 3 | Max answer turns |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/7_reeval/run.sh        # for the first iteration (--from-7)
```

## Output

```
8_iterate/
  latest -> iter_2          # symlink to the most recent iteration
  iter_1/
    output/
      iterate_summary.json  # grade comparison and stats
      diagnose/
      improve/
      reeval/
        results.json
        verification/
        grade/
      transcripts/
      logs/
    docs_working/           # improved docs (input for the next iteration)
    overlay.img
  iter_2/
    ...
```

### Iteration summary

```json
{
  "previous_grade": "INCORRECT",
  "previous_tags": [],
  "new_grade": "CORRECT",
  "new_tags": [],
  "improved": true,
  "findings": 3,
  "improve_approved": true,
  "improve_rounds": 2,
  "n_claims": 8,
  "n_incorrect": 0
}
```
