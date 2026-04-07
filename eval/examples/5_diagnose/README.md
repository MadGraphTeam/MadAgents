# Phase 5: Diagnose

Examines verification failures and reviewer-caught errors to identify documentation gaps, inaccuracies, and ambiguities.

## Usage

```bash
./eval/examples/5_diagnose/run.sh                  # diagnose with sonnet
./eval/examples/5_diagnose/run.sh --model haiku    # diagnose with haiku
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | sonnet | Model for the diagnoser |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/2_answer/run.sh
./eval/examples/3_verify/run.sh
./eval/examples/4_grade/run.sh      # optional, but recommended (provides grade context)
```

## Output

```
output/
  diagnose/
    diagnoses.json       # categorized findings with problems and recommendations
  verification/          # copied from phase 3
  grade/                 # copied from phase 4
  transcripts/
  logs/
```

### Diagnoses schema

```json
{
  "doc_gap":      [{"problem": "...", "correct_info": "...", "recommendation": "..."}],
  "doc_incorrect": [...],
  "doc_ambiguous": [...]
}
```
