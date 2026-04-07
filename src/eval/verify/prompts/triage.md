You have two files:

1. `{claims_path}` — a JSON array of newly extracted claims to be verified.
2. `{known_claims_path}` — a JSON array of previously verified claims from a database, each with `id`, `claim`, and `correct` fields.

Read both files. From the database, select all entries whose claims are relevant to any of the new claims — i.e., the database claim covers the same or closely related factual assertion, even if worded differently.

Write the selected database IDs to `{output_path}` as a flat JSON array:

```
[3, 7, 1]
```

Rules:
- Only include IDs where the database claim genuinely covers the same fact as a new claim.
- Do not include vaguely related claims.
- If no database entries are relevant, write an empty array `[]`.
