# Phase 4: Grade

Grades the answer based on the verification verdicts. Assigns a primary grade (`CORRECT` / `INCORRECT` / `INCONCLUSIVE`) plus optional tags such as `has_errors`, `inefficient`, and `reviewer_corrections`.

## Usage

```bash
./eval/examples/4_grade/run.sh                  # grade with haiku
./eval/examples/4_grade/run.sh --model sonnet   # grade with sonnet
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | haiku | Model for the grader |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/2_answer/run.sh
./eval/examples/3_verify/run.sh
```

## Output

```
output/
  grade/
    grade.json           # {"grade": "CORRECT", "tags": [...], "explanation": "..."}
  verification/          # copied from phase 3
  transcripts/
  logs/
```

### Grade schema

```json
{
  "grade": "CORRECT",
  "tags": ["has_errors"],
  "explanation": "The answer correctly describes..."
}
```

Grades and tags marked `"improve": true` in `categories.json` trigger the improve cycle (phases 5–8).
