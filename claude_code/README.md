# Claude Code Configuration

This directory contains the Claude Code configuration for MadAgents: agent definitions, skills, rules, prompts, and the build system that assembles them into sessions.

---

## Modes

The Claude Code version of MadAgents supports two modes, controlled by environment variables.

### Base mode (default)

```bash
./madrun_code.sh
```

The standard interactive MadAgents session. You can ask questions, run MadGraph workflows, generate events, and get physics guidance. The agent has access to specialized workers (madgraph-operator, physics-expert, researcher, plotter, etc.) and reviewers that check its work.

### Doc editing mode

```bash
ENABLE_DOC_EDITING=1 ./madrun_code.sh
```

Adds the ability to inspect and improve the MadGraph documentation that the agent uses as reference. Enables agent teams so the main session can spawn parallel teammates, each a fresh MadAgents instance with its own context window.

Available skills:

| Skill | What it does |
|---|---|
| `/get-docs` | Copy the docs to a writable location for editing |
| `/edit-docs` | Edit docs with parallel review (style, quality, factual verification) |
| `/generate-questions` | Generate evaluation questions based on real-world MadGraph use cases |
| `/diagnose-docs` | Analyze a failed answer to identify documentation gaps |
| `/train-docs` | Run the full improvement loop: generate questions, answer, verify, grade, diagnose, and fix docs |

The `/train-docs` workflow uses Claude Code's agent teams feature. The main session acts as a team lead that:

1. Generates evaluation questions
2. Spawns **answerer teammates** — each is a full, independent MadAgents instance with its own context window, capable of delegating to specialist workers (madgraph-operator, physics-expert, etc.)
3. Spawns **verifier teammates** — each independently verifies the claims in an answer using execution, source inspection, and physics reasoning
4. **Grades and diagnoses** via subagents
5. Fixes the docs via the `/edit-docs` workflow
6. **Re-evaluates** failed questions with fresh teammates that see the updated docs

Each teammate has a fresh context window — no pollution between questions.

---

## Claim database

When doc editing is enabled, the `verifier` agent maintains a persistent database of verified claims at `/output/.eval/claim_db.json`. Each verified fact (with its evidence and method) is cached so that subsequent verification runs can skip known claims. The `/train-docs` workflow consolidates the database after each verification batch to avoid race conditions between concurrent verifiers.
