# 37 — Save as you go, and phase the work

> Write durable output to disk incrementally, phase a long task with checkpoints, and catch drift early — because framing sets the ceiling on everything downstream.

Append intermediate output to a file as it is produced, not all at the end, and detect current
state at the start so an interrupted run resumes from the breakpoint rather than restarting — and
write to files, not chat, since chat vanishes at session end. Phase a long task and verify before
the next phase: the cost of correcting directional drift rises the later it is caught
(finding the outline broken after five chapters is far worse than after one). And
framing is load-bearing — "how well discovery is done sets the ceiling on the whole loop's
quality"; a flawlessly executed run of the *wrong* thing is wasted.

**In a harness like this.** Durability matters for autonomous campaigns (multi-step simulation
work) and for wiki writes — an interrupted long run picks up from the last persisted phase, and a
consultant's incremental wiki note survives a dropped session. Phase the work with an early
reviewer/verification gate: a spec error caught at framing is cheap, the same error caught after a
cluster run is not. Framing/spec correctness gates everything downstream — getting the physics
question right early is the highest-leverage check.

## Where the books say it

- **Skills** — ch7/ch9. Save as you go rather than saving everything at the end; detect state and resume from the breakpoint; catch drift early — phase with checkpoints, because the earlier directional drift is caught the cheaper it is to correct.
- **CC-Guide** — §12. Durable output to disk, not chat — write findings to files and save incrementally so a mid-task compaction doesn't lose the work.
- **Codex** — App C. Write decisions to disk — after every milestone record the summary, key decisions and todo in NOTES.md, so that even if the app wipes history the next session starts caught up.
- **Loop** — §03/§04. Framing sets the ceiling on the whole loop's quality — otherwise you do useless work, carefully; memory on disk, read back when needed.
- **Harness** — §10. The constrained four-stage workflow — plan-and-discover, build, verify, fix — the explicit shape for the deep path.
