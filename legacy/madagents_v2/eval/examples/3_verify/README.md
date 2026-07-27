# Phase 3: Verify

Extracts factual claims from the answer and verifies each one. Newly verified claims are appended to a persistent claim database that grows across runs and lets future verifications skip claims that have already been checked.

## Usage

```bash
./eval/examples/3_verify/run.sh                  # verify with sonnet
./eval/examples/3_verify/run.sh --model haiku    # use haiku for verification
./eval/examples/3_verify/run.sh --reset-db       # clear the claim database first
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--reset-db` | | Delete the claim database before running |
| `--model MODEL` | sonnet | Model for the verifier |
| `--extractor-model M` | haiku | Model for claim extraction |
| `--triage-model M` | haiku | Model for triage matching |
| `--remember-model M` | haiku | Model for remember selection |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/2_answer/run.sh
```

## Output

```
output/
  verification/
    claims.json          # extracted claims
    verdicts.json        # verification verdicts (correct / incorrect / inconclusive)
    staging/             # new claims to merge into the database
  transcripts/
  logs/
db/
  claim_db.json          # persistent claim database (grows across runs)
```
