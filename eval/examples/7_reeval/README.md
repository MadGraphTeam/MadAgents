# Phase 7: Re-evaluate

Re-answers the same question against the improved documentation, then verifies and grades the new answer. The result is compared to the original grade to measure whether the doc improvements actually helped.

The container only sees the question text and the improved docs — no previous grades, verdicts, or other evaluation artifacts.

## Usage

```bash
./eval/examples/7_reeval/run.sh                  # default
./eval/examples/7_reeval/run.sh --model sonnet
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | sonnet | Model for the answerer and verifier |
| `--supervisor-model M` | haiku | Model for the supervisor |
| `--extractor-model M` | haiku | Model for claim extraction |
| `--triage-model M` | haiku | Model for triage |
| `--remember-model M` | haiku | Model for remember selection |
| `--grader-model M` | haiku | Model for grading |
| `--max-turns N` | 3 | Max answer turns |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/2_answer/run.sh
./eval/examples/3_verify/run.sh
./eval/examples/4_grade/run.sh
./eval/examples/6_improve/run.sh
```

## Output

```
output/
  comparison.json         # original vs reeval grade comparison
  results.json            # new answer result
  supervision/
  verification/
    claims.json
    verdicts.json
    staging/
  grade/
    grade.json
  transcripts/
  logs/
```

### Comparison schema

```json
{
  "original_grade": "INCORRECT",
  "original_tags": [],
  "reeval_grade": "CORRECT",
  "reeval_tags": [],
  "improved": true,
  "reeval_explanation": "..."
}
```
