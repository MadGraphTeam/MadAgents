You are diagnosing why an AI agent had problems when answering a MadGraph question. Your goal is to find documentation issues that caused or contributed to the problems.

## Question
{question}

## Grade
{grade_summary}

## Inputs

- **Verification verdicts**: `{verdicts_path}` — look for entries where `correct` is `false`.
- **Answer transcript**: `{transcript_path}` — look for revision cycles where reviewers flagged issues.
- **Documentation**: `/madgraph_docs/`

## Documentation Scope

The docs at `/madgraph_docs/` are operational reference for an expert LLM agent using MadGraph. They cover MadGraph-specific syntax, parameters, defaults, and behavior — not textbook physics. A topic is in scope if knowing it helps the agent correctly use MadGraph.

Some web search and code inspection is expected and healthy — looking up specifics about papers or model implementations is normal. Inefficiency means the agent had to search for *basic operational information* that the docs should provide (common commands, default values, parameter names, standard workflows).

## Task

For each issue you find:
1. Check whether the topic is in scope for the documentation (see above).
2. If in scope, check whether `/madgraph_docs/` covers it correctly and clearly.
3. If the docs are missing, wrong, or ambiguous — write a finding.
4. If the docs already cover the topic correctly — skip it (model error, not actionable).

If the grade includes the `inefficient` tag, also look for unnecessary effort in the transcript caused by doc gaps: web searches for basic MadGraph operations, trial-and-error with commands, reading MG5 source code for info the docs should cover, or repeated searches with different terms for the same concept.

## Rules

- Identify root causes, not symptoms. If multiple issues stem from the same gap, write one finding.
- Findings must be generalizable — not specific to this one question.
- Recommendations should be practical (e.g. "note that parameter X differs between LO and NLO"), not sweeping rewrites.
- If no issues are documentation problems, write empty lists.

## Categories

{categories}

## Output

Write your findings to `{output_path}`:

```
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
