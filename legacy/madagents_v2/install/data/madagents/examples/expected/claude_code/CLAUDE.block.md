# MadAgents — Environment & Context

## Environment

- Default assumptions: the user wants MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin) for event generation/simulations, and the latest software versions.

## Operational guidelines

Parallel execution:
- When tasks are independent, invoke multiple agents in parallel rather than sequentially.
- Parallel agents may conflict on shared filesystem paths — manage this proactively (e.g., assign separate output directories).
- Invoking multiple reviewer instances in parallel on specific aspects improves review depth, but may miss cross-cutting consistency issues.


## Style

- Format math with LaTeX (`$...$` inline, `$$...$$` display). Prefer `\\alpha` over Unicode. Use LaTeX only for math, not in plain text.
