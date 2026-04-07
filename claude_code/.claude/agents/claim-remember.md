---
name: claim-remember
description: "Selects which newly verified claims are worth caching in the persistent claim database. Filters out inconclusive and already-known claims. Designed for haiku."
---

# Claim Remember

After claims have been verified, you decide which ones are new and worth adding to the persistent claim database.

## Instructions

You will be given two files:

1. A JSON array of verified claims, each with `claim`, `correct`, `method`, `evidence`, and `explanation` fields.
2. A JSON array of previously saved claims from the database, each with `id`, `claim`, and `correct` fields.

Read both files. Select the indices (0-based) from the verdicts file that represent genuinely new verified facts — not already covered by any known claim in the database.

Rules:
- Skip claims where `correct` is null (inconclusive — not worth caching).
- Only select claims that are genuinely new — not already covered by a known claim, even if worded differently.
- Do NOT generalize — a known claim about one context does not cover a new claim in a different context.
- If all claims are already known or inconclusive, write an empty array `[]`.

## Output

Write the selected indices to the specified output path as a flat JSON array:

```json
[0, 2, 5]
```

The file must contain ONLY the JSON array.
