---
name: get-docs
description: "Get a writable copy of the MadGraph documentation."
---

# Get MadGraph Docs

The MadGraph documentation is mounted read-only at `/madgraph_docs/`. To get a writable copy you can browse or edit, use the `get_doc_draft` MCP tool:

```
get_doc_draft("$ARGUMENTS")
```

If no path was given, use `/workspace/docs` as default. The path must be under `/workspace` or `/output`.

If you want to make changes and apply them back, use `/edit-docs` instead.
