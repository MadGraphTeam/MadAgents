# 21 — Curate the dispatch payload

> More context isn't better. Hand a consultant its slice and let it read the rest on demand — don't stuff the corpus into the prompt.

Too much context degrades the model; it gets lost in the noise, and long-context recall
measurably regresses (the books cite needle-in-haystack recall dropping sharply as the window
grows toward 1M tokens). The model's real strength on a large codebase "isn't context size, it's
knowing which files *not* to include." So fix the goal and let the agent read files on demand
rather than dumping everything in. This is *per-dispatch* curation — distinct from cutting the
standing scaffold.

**In a harness like this.** Hand a consultant its slice and let it source-walk the rest on
demand; scope memory/wiki reads to the task. This licenses curating *what a dispatch carries*,
not speculatively thinning the standing cards. Because a cached MG5 path/symbol is durable within
an install, read-on-demand of a known location is cheap and reliable here in a way the books'
fast-moving-application-code setting is not.

## Where the books say it

- **Claude Code: The Complete Guide** — §06/App A. More context isn't better — context engineering means giving the *right* scoped information for the task, not an encyclopedia.
- **Codex Complete Guide** — §10/App C. A million-token window is not a free lunch — surgical file selection beats feeding more, and files should be read on demand rather than stuffing in the whole repo (the long-context recall regression is documented in Anthropic's own system card, web-verifiable).
- **OpenClaw: The Complete Guide** — §30, on where the tokens go — the per-dispatch payload (what each consultant carries) is one of the two harness-controllable levers (the other is the standing description surface, lesson 20).
