The agent has responded to your follow-up. Here is its updated response:

## Response

{response}

## Categories

{categories}

Classify this response into exactly one category, considering the full conversation so far. If the category's action is "continue", write a specific follow-up instruction tailored to the response's remaining shortcomings.

Your follow-up must NOT contain any information beyond what is already in the original question. Do not reveal the answer, hint at the solution, point out specific gaps, or simplify the task. The agent must figure everything out on its own.

Write your verdict as a JSON object to `{output_path}`:

```
{
  "category": "the category name (exactly as listed above)",
  "follow_up": "if action is continue, a specific follow-up instruction. Otherwise empty string."
}
```
