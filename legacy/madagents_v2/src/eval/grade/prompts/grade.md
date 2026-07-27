You are grading an AI agent's answer to a MadGraph question.

## Question
{question}

## Verification Summary

The answer was split into {n_claims} individual claims and each was independently verified. Results:
- {n_correct} claims verified as correct
- {n_incorrect} claims verified as incorrect
- {n_inconclusive} claims inconclusive

The full verdicts file is at `{verdicts_path}`. Read it for details on which claims failed and why.

## Answer Transcript

The full transcript of the agent's answer session is at `{transcript_path}`. Read it to assess the agent's workflow and efficiency.

## Grades

Assign exactly one grade:

{grades}

## Tags

Assign zero or more tags:

{tags}

If no transcript is available, do not assign the `inefficient` tag.

## Output

Write your grade to `{output_path}`:

```
{
  "grade": "CORRECT, INCORRECT, or INCONCLUSIVE",
  "tags": ["list", "of", "applicable", "tags"],
  "explanation": "1-3 sentences explaining why this grade was assigned, referencing specific incorrect claims or inefficiencies if relevant."
}
```

Tags is an empty list if none apply.
