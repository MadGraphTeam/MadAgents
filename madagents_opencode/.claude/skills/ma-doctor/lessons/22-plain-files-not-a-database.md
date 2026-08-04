# 22 — Plain files, not a database

> Plain Markdown, read directly. At bounded scale you need no vector database and no RAG.

Plain-file memory is near-zero-maintenance, user-editable, version-controllable, and survives a
context reset — no DB, no vector store. Markdown is the native language of LLMs and uses 30-50%
fewer tokens than JSON or XML. At bounded scale, an agent reading structured Markdown directly
(steered by an index) beats a vector DB on latency, cost, readability, and portability; a vector
layer earns its place only past roughly a million characters. Three independent billion-dollar
agents converged on Markdown as the memory layer.

## In a harness like this

This harness uses **no** vector DB / RAG — consultants Read wiki page bodies directly, steered by
the memory index (lesson 23). The per-consultant MadGraph surface is finite and bounded (a slice
of a versioned, static codebase), squarely in the direct-read regime, and the large context
window holds it. The source is fixed and walkable once, so plain files are the right substrate —
not a gap to close. When auditing such a harness, a proposal to add a vector store or RAG layer is
almost always premature at this scale; the bar is the million-character threshold above.

## Where the books say it

- **Src-Analysis** — ch6/ch8. Plain Markdown, near-zero maintenance, user-editable, no DB or vector store — plain files beat a database.
- **Harness** — §04/§08/§16. Plain-file memory plus structured notes that survive a context reset (the Pokémon step-count example).
- **Obsidian** — §06/§02. Below roughly 400,000 characters a knowledge base needs no vector database at all; one earns its place only past ~1M chars; Markdown beats vector-DB on latency, cost, readability, version-control, and portability.
- **OpenClaw** — §07/§09. Everything-is-plain-text design; the surface-size ↔ tokens ↔ latency cost relationship.
