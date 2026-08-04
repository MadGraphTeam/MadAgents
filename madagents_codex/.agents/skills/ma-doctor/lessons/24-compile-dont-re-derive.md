# 24 — Compile, don't re-derive

> Read the source once, compile it into a kept structured wiki, and answer later questions from the wiki — not by re-deriving from source every time.

Karpathy's distinction: a *retriever* searches the raw material and stitches an answer every
time, discarding it after use (an intern who wakes with amnesia every morning); a *compiler*
reads the raw material once, writes a structured article that is kept, iterated on, and
cross-referenced, and answers later from it. "A retriever does redundant work every time. A
compiler does the work once and produces reusable output." Each session then stops being a
one-time consumable and becomes an incremental update that raises the starting point of the next
— a positive feedback loop.

## In a harness like this

This is the wiki / learned-state design: a consultant source-walks the MadGraph internals once,
writes the wiki page, and the accumulated state inherits it — later questions read the compiled
page instead of re-walking the source. It names cleanly why a system whose memory and wiki have
filled in beats a fresh one: the fresh system is the retriever (re-derives on the spot), the
filled-in system is the compiler's output consumed. This is the self-improving requirement and the
"warm and well trained at start" goal. Compiling once is safe because MG5 source is byte-static
within an install, so a compiled page does not silently go stale.

The value is **conditional on wiki quality**. An uncurated wiki can be *worse* than re-deriving
fresh — it caches wrong or trap-laden derivations that then ride along into every later answer.
Curation (the reflect and lint passes) is what makes the compiled page an asset rather than a
liability — this is lesson 25's source-vs-derived risk made concrete, and it is why the curation
disciplines (lessons 27-28) earn their keep. When auditing such a harness, the compile loop is only
a win if a quality gate stands between "a page was written" and "the page is trusted and shipped";
a promote/ship step with no quality check would carry a bad wiki as readily as a good one.

## Where the books say it

- **Obsidian** — §06 (compiler rather than retriever — read once, write a kept structured wiki, answer from it), §07.3 (incremental accumulation: each research session adds an increment, raising the starting point for the next — a positive feedback loop).
