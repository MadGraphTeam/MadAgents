# 23 — Memory is an index of pointers

> The always-loaded layer is a capped index of one-line pointers; the bodies live elsewhere and are fetched on demand.

Progressive disclosure: load a name + one-line description first, the full body only when needed,
referenced files last — so hundreds of pages cost almost nothing day to day ("scan the spine
titles, pull the one you need onto your desk, then look up an appendix"). An index file "does 80%
of the work": without it the agent enters a folder, sees 50 files, and scans them one by one;
with it, it reads the index first and knows where to look in seconds. Each entry's description is
what drives recall, so it carries weight (lesson 20). The bodies live on disk, not in context.

## In a harness like this

This is the two-tier memory-plus-wiki design exactly: the always-loaded MEMORY carries the
description-only index of the slice's wiki pages, and the consultant Reads the one relevant page
body on demand. The index of descriptions is the standing surface; each description must be tight
and self-disambiguating. The token payoff — hundreds of pages, near-zero standing cost — is the
explicit point. When auditing memory, the warning sign is bodies that have crept into the
always-loaded layer (it should hold pointers, not content) or index entries too vague to drive the
right Read.

## Where the books say it

- **Src-Analysis** — ch6. Memory is a capped index of one-line pointers; bodies live elsewhere; each entry's description drives recall.
- **Obsidian** — §04.3/§06. An `index.md` does the bulk of the work; a global `wiki/INDEX.md` is read first — check the contents, then turn to the right page — and pages are pulled selectively after that.
- **Hermes** — §09. Three-tier progressive disclosure — name+description first, full body on demand, referenced files last.
- **Skills** — ch3. The origin of three-tier disclosure: L1 metadata-only index, L2 full body on demand, L3 bundled resources last.
- **Loop** — §04. Memory belongs on disk rather than in the context — read it back when needed.
- **CC-Guide** — §05/§09b/§12/App A. Load-bearing memory and rules live on disk, not transient context (compaction is lossy); breaking work into smaller single-responsibility pages keeps each context clean.
