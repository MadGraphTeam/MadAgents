# MadAgents — Environment & Context

## Environment

- You run in a container with a persistent filesystem. Three key directories:
  - `/output` — user's directory for final deliverables. Persistent, shared across sessions.
  - `/workspace` — your scratch space. Recreated empty each session.
  - `/opt` — persistent installations, shared across sessions.
- Avoid writing outside these three directories.
- Default assumptions: the user wants MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin) for event generation/simulations, and the latest software versions.

## Operational guidelines

Parallel execution:
- When tasks are independent, invoke multiple agents in parallel rather than sequentially.
- Parallel agents may conflict on shared filesystem paths — manage this proactively (e.g., assign separate output directories).
- Invoking multiple reviewer instances in parallel on specific aspects improves review depth, but may miss cross-cutting consistency issues.

Filesystem:
- Keep `/workspace/` and `/output/` organized — move scattered files into dedicated directories, and clean up intermediate files when they are no longer needed.

## Style

- Format math with LaTeX (`$...$` inline, `$$...$$` display). Prefer `\\alpha` over Unicode. Use LaTeX only for math, not in plain text.
