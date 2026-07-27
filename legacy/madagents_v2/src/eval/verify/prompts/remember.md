You have two files:

1. `{verdicts_path}` — a JSON array of verified claims, each with `claim`, `correct`, `method`, `evidence`, and `explanation` fields.
2. `{known_claims_path}` — a JSON array of previously saved claims from the database, each with `id`, `claim`, and `correct` fields.

Read both files. Select the indices (0-based) from the verdicts file that represent genuinely new verified facts — not already covered by any known claim in the database.

Write the selected indices to `{output_path}` as a flat JSON array:

```
[0, 2, 5]
```

Rules:
- Skip claims where `correct` is null (inconclusive — not worth caching).
- Only select claims that are genuinely new — not already covered by a known claim, even if worded differently.
- Do NOT generalize — a known claim about one context does not cover a new claim in a different context.
- If all claims are already known or inconclusive, write an empty array `[]`.
