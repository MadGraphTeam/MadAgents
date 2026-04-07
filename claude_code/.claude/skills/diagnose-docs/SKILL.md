---
name: diagnose-docs
description: "Find documentation problems that caused agent mistakes — gaps, inaccuracies, or ambiguities. Uses grade context to guide diagnosis."
---

# Diagnose Documentation Issues

Find documentation issues that caused or contributed to problems. Your goal is to identify what needs to change in the docs to prevent similar issues.

## Input

$ARGUMENTS

If a description was given, use it as the problem to diagnose. If a file path was given (e.g. verdicts JSON), read it and extract entries where `correct` is `false`. If nothing was given, ask the user what went wrong.

If a grade file is available (e.g. `/workspace/train/grade/grade.json`), read it for context. When the `inefficient` tag is present, also look for unnecessary effort in the agent's workflow caused by doc gaps.

## Documentation Scope

The docs at `/madgraph_docs/` are operational reference for an expert LLM agent using MadGraph. They cover MadGraph-specific syntax, parameters, defaults, and behavior — not textbook physics. A topic is in scope if knowing it helps the agent correctly use MadGraph.

Some web search and code inspection is expected and healthy — looking up specifics about papers or model implementations is normal. Inefficiency means the agent had to search for *basic operational information* that the docs should provide (common commands, default values, parameter names, standard workflows).

## Task

1. **Get the docs**: Call `get_doc_draft("/workspace/docs_check")` to get a local copy you can read.

2. For each issue:
   1. Check whether the topic is in scope for the documentation (see above).
   2. If in scope, check whether the docs cover it correctly and clearly.
   3. If the docs are missing, wrong, or ambiguous — write a finding.
   4. If the docs already cover the topic correctly — skip it (not actionable).

## Rules

- Identify root causes, not symptoms. If multiple issues stem from the same gap, write one finding.
- Findings must be generalizable — not specific to this one question.
- Recommendations should be practical (e.g. "note that parameter X differs between LO and NLO"), not sweeping rewrites.
- If no issues are documentation problems, write empty lists.

## Categories

- **doc_gap**: The documentation does not cover this topic.
- **doc_incorrect**: The documentation contains wrong or outdated information.
- **doc_ambiguous**: The documentation is unclear or could be read multiple ways.

## Output

Write your findings to a file (e.g., `/workspace/diagnoses.json`):

```json
{
  "doc_gap": [
    {
      "problem": "What went wrong or what information was missing",
      "correct_info": "The correct information",
      "recommendation": "Specific documentation change to prevent this"
    }
  ],
  "doc_incorrect": [],
  "doc_ambiguous": []
}
```

Include all categories. Empty lists are fine.

## Self-Validation

After writing results, verify:
- All three category keys are present
- Each finding has `problem`, `correct_info`, and `recommendation`
- All three fields are non-empty strings
