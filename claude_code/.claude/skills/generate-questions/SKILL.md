---
name: generate-questions
description: "Generate evaluation questions about MadGraph and related tools with verified reference answers, using web research for real-world use cases."
---

# Generate Evaluation Questions

Generate realistic questions that a particle physicist would ask about MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin, MadWidth, MadAnalysis).

## Parameters

$ARGUMENTS

Parse `key=value` pairs from the input. All are optional — use defaults if not specified.

- **count**: Number of questions (default: 10). Example: `count=5`
- **focus**: Topic area. Example: `focus=NLO matching`
- **requirements**: Extra constraints. Example: `requirements=must include exact commands`
- **dedup**: Path to existing questions file to avoid duplicates. Example: `dedup=/workspace/existing.json`

## Goal

1. **Search the web** for real-world use cases: forum posts (Launchpad, MadGraph mailing list), HEP Stack Exchange, tutorials, conference proceedings, and papers that describe MadGraph/Pythia8/Delphes workflows. Focus on what users actually struggle with.
2. **Generate questions** based on what real users need — common workflows, pitfalls, misconfigurations, advanced features, and edge cases. Questions may involve MadGraph alone or in combination with related tools.

Do NOT tailor questions to any specific documentation. The goal is to capture what users genuinely need help with.

## Requirements

- Questions must be self-contained (no references to "the above" or prior context).
- If a dedup file was given, check each candidate question against existing ones and skip near-duplicates.

## Reference Answers

Every question MUST include a `reference_answer` — a concise summary of the correct answer, used as ground truth during evaluation.

- State the key facts: the correct approach, relevant commands, and important parameter names.
- Keep it brief — a few sentences to a short paragraph. The evaluation pipeline independently verifies claims, so exhaustive detail is not needed.
- Base answers on your knowledge. Use web search only to confirm specific details you are unsure about.

## Output

Write a JSON array (default: `questions.json`). The file must contain ONLY the JSON array — no markdown fences, no commentary, no explanation.

```
[
  {
    "text": "The full question text",
    "reference_answer": "Concise correct answer with key facts, commands, and parameter names."
  }
]
```

## Self-Validation

After writing, verify:
- Valid JSON array
- Non-empty
- Each object has non-empty `text` and `reference_answer` strings
- If dedup file was given, no new question is a near-duplicate
