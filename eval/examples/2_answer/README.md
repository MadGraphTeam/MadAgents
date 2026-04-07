# Phase 2: Answer

Answers a generated question using MadAgents (the system under test). A supervisor reviews each answer turn and accepts or asks for corrections.

## Usage

```bash
./eval/examples/2_answer/run.sh                                     # answer question 0
./eval/examples/2_answer/run.sh --index 1                           # answer question 1
./eval/examples/2_answer/run.sh --questions path/to/questions.json  # custom input
./eval/examples/2_answer/run.sh --model haiku --max-turns 2
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--index N`, `-i N` | 0 | Question index to answer |
| `--questions FILE` | `1_generate/output/questions.json` | Path to questions JSON |
| `--model MODEL` | sonnet | Model for the answerer |
| `--supervisor-model M` | haiku | Model for the supervisor |
| `--max-turns N` | 3 | Max answer + supervise turns |

## Prerequisites

```bash
./image/examples/create_image.sh
./eval/examples/1_generate/run.sh
```

## Output

```
output/
  results.json           # answer result (question, response, turns, category)
  supervision/           # supervisor verdicts per turn
  transcripts/           # session transcripts and workflow logs
  logs/
overlay.img              # writable overlay (reused by phases 3, 6, 7)
```

The overlay file (`overlay.img`) is preserved on purpose — it contains software installed by the answerer (e.g. MadGraph), which the verify and reeval phases reuse.
