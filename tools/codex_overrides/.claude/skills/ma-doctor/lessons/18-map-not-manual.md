# 18 — Map, not manual

> The always-loaded surface is a thin map of the non-inferable, not an encyclopedia. Only write what the agent cannot infer from the source.

The criterion for the always-loaded surface (CLAUDE.md, lead prompt, rules, cards): "if it can be
inferred from the source, don't write it; if it can't be guessed, you must." Too many rules
equals no rules — redundant rules dilute the load-bearing ones and can actively hurt. The most
valuable content is the non-inferable, source-specific gotcha, not generic best-practice filler
the model already knows. There is a sweet spot in length (the books cite ~100-200 lines /
~100-150 instructions, ~500-2,000 words per skill): too long buries the load-bearing parts, too
short says nothing. Control comes from sharper contracts, not longer prose.

**In a harness like this.** The lead prompt and the role cards stay lean and route to the
wiki and consultants; anything readable from the MadGraph source does not belong in the harness
surface. Cut "write clean code"; keep "this MG5 behavior is surprising and bites here." Apply the
lean side *conservatively*: cut only the clearly-inferable, never thin a working card
speculatively to hit a token target — a wrongly-cut piece of scaffolding surfaces as a failure on
a fresh first-use system that is hard to detect or recover from.

## Where the books say it

- **Harness Engineering** — §05/§06/§14. Give a map rather than a manual; too many rules amount to no rules; redundant rules can actively hurt (ETH Zurich); only write what cannot be inferred from the source.
- **Claude Code: The Complete Guide** — §05/App G. Guardrails rather than manuals; anything inferable from the source should not be written down; documented gotchas beat best-practice filler; ~200 lines / 100-150 instructions.
- **Claude Code Source-Code Analysis** — ch7 (durable rules in the always-loaded surface), ch8/ch12 (subtract before adding — "good enough"), ch4 (sharpen contracts, not prose).
- **Claude Code Source-Code Analysis** — ch11. Quantitative length anchors measurably outperform vague ones — a stated word cap beats an instruction to be concise; apply to lead prose with care, since the interactive product may need fuller hedges.
- **Agent Skills** — ch3. The Goldilocks Zone — the more content packed in, the less weight each piece carries; 500-2,000 words; the 5,000-word skill performed *worse*.
- **Codex Complete Guide** — §05. AGENTS.md restates it: leave out whatever the model can work out from the code, and write down whatever it cannot guess.
