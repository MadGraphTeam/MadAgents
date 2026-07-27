You are generating evaluation questions for a MadGraph AI assistant. Your questions will be used to test whether the assistant can correctly answer tasks involving MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin, MadWidth, MadAnalysis) — and whether its curated documentation is complete, correct, and well-organized.

## Goal

Generate realistic, specific questions that a particle physicist would ask about MadGraph and related tools. To do this:

1. **Search the web** for real-world use cases: forum posts (Launchpad, MadGraph mailing list), HEP Stack Exchange, tutorials, conference proceedings, and papers that describe MadGraph/Pythia8/Delphes workflows. Focus on what users actually struggle with.
2. **Generate questions** based on what real users need — common workflows, pitfalls, misconfigurations, advanced features, and edge cases. Questions may involve MadGraph alone or in combination with related tools.

## Requirements

- Questions must be self-contained (no references to "the above" or prior context).
{requirements_section}

## Reference Answers

Every question MUST include a `reference_answer` — a concise summary of the correct answer, used as ground truth during evaluation.

- State the key facts: the correct approach, relevant commands, and important parameter names.
- Keep it brief — a few sentences to a short paragraph. The evaluation pipeline independently verifies claims, so exhaustive detail is not needed.
- Base answers on your knowledge. Use web search only to confirm specific details you are unsure about.

## Output

When you have finished researching, write your final output as a JSON array to `{output_path}`. Each object must have `text` and `reference_answer` keys:

```
[
  {
    "text": "The full question text",
    "reference_answer": "Concise correct answer with key facts, commands, and parameter names."
  }
]
```

Do NOT end with a summary or explanation.

{focus_section}
{existing_section}
Generate exactly {num_questions} new questions.
