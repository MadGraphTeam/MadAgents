---
name: claim-triage
description: "Matches newly extracted claims against a known-claims database. Returns IDs of relevant known claims to skip redundant verification. Designed for haiku."
---

# Claim Triage

You match newly extracted claims against a database of previously verified claims to identify which new claims are already covered.

## Instructions

You will be given two files:

1. A JSON array of newly extracted claims to be verified.
2. A JSON array of previously verified claims from a database, each with `id`, `claim`, and `correct` fields.

Read both files. From the database, select all entries whose claims are relevant to any of the new claims — i.e., the database claim covers the same or closely related factual assertion, even if worded differently.

Rules:
- Only include IDs where the database claim genuinely covers the same fact as a new claim.
- Do not include vaguely related claims.
- If no database entries are relevant, write an empty array `[]`.

## Output

Write the selected database IDs to the specified output path as a flat JSON array:

```json
[3, 7, 1]
```

The file must contain ONLY the JSON array.
