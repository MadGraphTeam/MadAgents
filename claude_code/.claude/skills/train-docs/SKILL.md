---
name: train-docs
description: "Run one iteration of the doc improvement loop: generate or accept questions, answer them in parallel, verify, grade, diagnose, fix the docs, and re-evaluate until convergence."
---

# Train Documentation

Run one cycle of the documentation improvement loop with parallel question processing.

## Parameters

$ARGUMENTS

Parse `key=value` pairs from the input. All are optional — use defaults if not specified.

- **questions**: Comma-separated list of questions, or a path to a JSON file. If not given, generate questions.
- **count**: Number of questions to generate (default: 3). Ignored if questions are provided.
- **focus**: Topic focus for question generation. Example: `focus=NLO matching`
- **requirements**: Extra constraints for generation. Example: `requirements=must involve Pythia8`

## Workspace Setup

Answerers and verifiers must be spawned as **teammates** (via `TeamCreate`), NOT as subagents (via the `Agent` tool). Teammates run as independent Claude Code sessions that can dispatch their own subagents. Subagents cannot dispatch further subagents — so a verifier spawned as a subagent would be unable to delegate to madgraph-operator, script-operator, etc.

- **Answerers**: `agent_type: "orchestrator"` — full MadAgents orchestrator.
- **Verifiers**: `agent_type: "verifier"` — MadAgents orchestrator with built-in verification workflow and restricted subagent roster.

Teammates start in `/output` (the lead's working directory). Always specify absolute paths (e.g., `/output/train/q000/`) when telling a teammate where to write its output.

Create `./train/` with a subdirectory per question: `q000/`, `q001/`, etc. Each question directory gets: `answer/`, `verify/`, `grade/`, `diagnose/`.

## Workflow

Execute all steps in sequence without pausing for confirmation — the user will be consulted only where the skill explicitly says "Discuss with user."

### 1. Get questions

If questions were provided, use them. Otherwise invoke `/generate-questions` with the count, focus, and requirements parameters.

The generated questions include `reference_answer` fields. These are **unverified** and must not be visible to answerer subagents.

Write the full questions data (including `reference_answer` fields) to `./train/questions.json`. This file will be hidden from answerers and re-answerers via `hide_paths`.

Number each question: q000, q001, q002, ...

### 2. Answer all questions (parallel, teammates)

**Before answering**, call `hide_paths` to hide the questions file (which contains reference answers answerers must not see). Pass: `/output/train/questions.json`. Save the returned token.

Create a team for the answerers. For each question, add a teammate to this team with `agent_type: "orchestrator"`. Give it the question and its working directory. All teammates work in parallel.

> {question text}
>
> Work in `/output/train/q{N}/answer/`. Ensure your answer is complete and concrete before finishing — all steps, commands, and parameters should be fully specified.

After ALL teammates finish, shut down the team. **Before calling TeamDelete**, kill all tmux panes belonging to the team's teammates (they may linger after the teammate finishes). Then:
1. Call `show_paths` with the saved token to restore the questions file.
2. For each question, call `get_transcript` with `team_name`, `agent_name`, `output_path` set to `/output/train/q{N}/answer/transcript.json`, and `answer_path` set to `/output/train/q{N}/answer/response.md`. This extracts both the transcript and the answer in one call — no need to save the response manually.

### 3. Verify all answers (parallel, teammates)

Create a team for the verifiers. For each question, add a teammate to this team with `agent_type: "verifier"`. Tell each to work in its question directory:

> Work in `/output/train/q{N}/verify/`. Verify the factual claims in the answer at `/output/train/q{N}/answer/response.md`. Also check for user-facing written artifacts the answerer produced (answer files, scripts, code) in `/output/train/q{N}/answer/`.
>
> If a claim database exists at `/output/.eval/claim_db.json`, reuse the exact wording of known claims where the same fact appears. Use known claims as **context**, not automatic skips. Re-verify if there is any doubt. Do NOT generalize from known claims across contexts.
>
> **Output**: Write verdicts to `/output/train/q{N}/verify/verdicts.json` — a JSON array where each object has: `claim`, `correct` (true/false/null), `method` (execution/inspection/physics_reasoning/null), `evidence` (list), `explanation`.
>
> Also write remember selections to `/output/train/q{N}/verify/remember.json` — a flat array of 0-based indices marking which newly verified claims are genuinely new and worth caching. Skip inconclusive claims (correct=null).

After ALL verifier teammates finish, shut down the team. **Before calling TeamDelete**, kill all tmux panes belonging to the team's teammates.

**Consolidate claim database**: For each question, read `remember.json` to find which newly verified claims should be cached. Append them to `/output/.eval/claim_db.json` (load existing DB or start with `[]`, assign incremental IDs, add `claim`, `correct`, `method`, `evidence`, `explanation`, `count: 1` fields). **Deduplicate**: skip any claim whose text already exists in the DB (exact match). This is done sequentially to avoid race conditions.

### 4. Grade and diagnose all answers (parallel)

For each question **simultaneously**, invoke a subagent (no worktree isolation needed — grading and diagnosis only read files and write JSON). Tell each:

> Grade and diagnose this answer. Read the inputs, then:
>
> **Step 1 — Grade**: Assess the answer against the verification verdicts.
>
> **Inputs**:
> - Question: {question text}
> - Verification summary: {count correct, incorrect, inconclusive claims}
> - Verdicts: `/output/train/q{N}/verify/verdicts.json`
> - Answer: `/output/train/q{N}/answer/response.md`
> - Transcript: `/output/train/q{N}/answer/transcript.json` (for assessing workflow and efficiency)
>
> **Output**: Write to `/output/train/q{N}/grade/grade.json`:
> ```json
> {"grade": "CORRECT|INCORRECT|INCONCLUSIVE", "tags": [], "explanation": "..."}
> ```
>
> **Grades**:
> - **CORRECT**: The answer correctly answers the question. Errors in reasoning or wrong intermediate facts do not affect this — those are captured by tags.
> - **INCORRECT**: Wrong final answer, misleading conclusions, refusal, or no meaningful response.
> - **INCONCLUSIVE**: Verification results are insufficient to determine correctness. Use only when you genuinely cannot make the call.
>
> **Tags** (zero or more, independent of grade):
> - **has_mistakes**: Wrong facts, flawed reasoning, or incorrect intermediate steps that do not invalidate the final answer.
> - **inefficient**: The agent spent significant effort that better documentation would have prevented. Read the transcript to assess this. Web searches and source inspection for question-specific resources are expected — flag only when extra effort traces back to a documentation problem. If no transcript file is available, do not assign this tag.
> - **reviewer_corrections**: The agent's internal reviewers (verification-reviewer) caught mistakes during the answering process that required revision before the final answer was produced. Even if the final answer is correct, this indicates the docs were unclear or misleading enough to cause initial errors. Read the transcript to identify revision cycles where reviewers flagged issues. If no transcript file is available, do not assign this tag.
>
> **Step 2 — Diagnose** (only if grade is INCORRECT or any tag is present):
>
> Identify documentation issues that caused or contributed to the problems.
>
> - Read `/output/train/q{N}/verify/verdicts.json` for incorrect claims
> - Read `/output/train/q{N}/answer/response.md` and `/output/train/q{N}/answer/transcript.json` — look for revision cycles where reviewers flagged issues
> - Check whether `/madgraph_docs/` covers the topic correctly and clearly
> - If the docs are missing, wrong, or ambiguous — write a finding. If the docs already cover it correctly — skip (model error, not actionable).
> - If the `inefficient` tag is present, also look for unnecessary effort in the transcript caused by doc gaps: web searches for basic MadGraph operations, trial-and-error with commands, reading MG5 source code for info the docs should provide.
> - If the `reviewer_corrections` tag is present, identify what the reviewers flagged and trace it back to a documentation problem. What did the agent get wrong initially? Was the doc misleading, incomplete, or ambiguous on that point?
>
> **Rules**: Identify root causes, not symptoms. Findings must be generalizable. Recommendations should be practical, not sweeping rewrites. If no issues are documentation problems, write empty lists.
>
> **Output**: Write to `/output/train/q{N}/diagnose/diagnoses.json`:
> ```json
> {"doc_gap": [...], "doc_incorrect": [...], "doc_ambiguous": [...]}
> ```
> Each finding has `problem`, `correct_info`, and `recommendation` fields. Include all three categories. Empty lists are fine. If the answer is CORRECT with no tags, write empty lists for all categories.

After ALL agents finish, proceed.

### 5. Convergence check

Read each grade.

If ALL questions are `CORRECT` with empty tags → stop here. The docs supported clean correct answers for every question. Report the results to the user and skip to the Summary.

Collect the questions that need improvement: grade is `INCORRECT`, or any tag is present (`has_mistakes`, `inefficient`, or `reviewer_corrections`). `INCONCLUSIVE` with no tags does NOT need improvement.

### 6. Merge diagnoses

Read `diagnoses.json` files only from questions that need improvement (from step 5). Merge findings:
- Deduplicate: if multiple questions identified the same doc gap, keep the most specific recommendation
- Group by category: `doc_gap`, `doc_incorrect`, `doc_ambiguous`

Write merged findings to `./train/diagnoses_merged.json`.

### 7. Fix the docs

Read `./train/diagnoses_merged.json`. For each question that needed improvement, read its `reference_answer` from `./train/questions.json`. Reference answers are **unverified** — they may contain errors. Tell the doc-editor to use them as inspiration for understanding what the docs should cover, not as ground truth.

Tell the doc-editor to prefer minimal, topic-general changes over problem-specific patches. Write about the topic naturally — not about the failure that motivated the change. If more specificity is needed, the review cycle will ask for it.

Apply documentation improvements using the `/edit-docs` workflow, passing the merged diagnoses and reference answer context. The edit-docs workflow handles:
- Editing via **doc-editor**
- Parallel review via **doc-style-reviewer**, **doc-quality-reviewer**, and **verifier**
- Revision loop until all three checks pass — if ANY reviewer flags an issue, revision is mandatory before proceeding

Do NOT skip or short-circuit the edit-docs revision loop. All three reviewers must pass before applying. Once all pass, apply the changes so re-answerers see the updated docs.

**Unverified claims warning**: After the verifier finishes, read its verdicts file. If any claim has `correct: null` (inconclusive — verification failed to confirm or deny), STOP and print a warning to the user listing each unverified claim with its explanation. Ask the user how to proceed: keep the change as-is, drop the unverified claim, or rewrite the relevant section. Do NOT apply the changes until the user responds.

### 8. Re-evaluate failed questions (parallel, teammates)

Re-answer only the questions that failed (from step 5). The answerer teammates must not see previous evaluation artifacts (grades, verdicts, diagnoses, previous answers).

**Before re-answering**, call `hide_paths` to move all eval artifacts out of the container's view. Pass every relevant path for each failed question N (use absolute container paths for MCP tools):
- `/output/train/questions.json`
- `/output/train/q{N}/answer`
- `/output/train/q{N}/verify`
- `/output/train/q{N}/grade`
- `/output/train/q{N}/diagnose`
- `/output/train/diagnoses_merged.json`

Save the returned token.

**Answer**: Create a team for the re-answerers. For each failed question, add a teammate to this team with `agent_type: "orchestrator"` (fresh context — it will see the updated docs). Tell each the question and its working directory. All teammates work in parallel.

> {question text}
>
> Work in `/output/train/q{N}/answer/`. Ensure your answer is complete and concrete before finishing — all steps, commands, and parameters should be fully specified.

**After ALL teammates finish**, shut down the team. **Before calling TeamDelete**, kill all tmux panes belonging to the team's teammates. Then:
1. Call `show_paths` with the saved token to restore the hidden artifacts.
2. For each re-answered question, call `get_transcript` with `team_name`, `agent_name`, `output_path` set to `/output/train/q{N}/answer/transcript.json`, and `answer_path` set to `/output/train/q{N}/answer/response.md`.

Then re-run ALL three verification steps for each re-evaluated question (same as steps 3–4):
1. **Verify** (step 3): Create a new verifier team with `agent_type: "verifier"`. Dispatch one teammate per re-evaluated question with the same instructions as step 3.
2. **Consolidate claim database**: Same as step 3 — sequential, after all verifiers finish.
3. **Grade and diagnose** (step 4): Same as step 4, only for re-evaluated questions.

### 9. Convergence check

For each re-evaluated question, check its new grade:
- If `CORRECT` with no tags → mark as **converged** (exclude from further iterations)
- Otherwise → still needs work

**If ALL re-evaluated questions converged** → doc changes confirmed. Discuss results with user.

**If some questions still fail** → keep the applied doc changes (they may have partially helped) and repeat from step 6 with only the non-converged questions. Read diagnoses only from the latest iteration's non-converged questions — do not re-merge stale diagnoses from earlier iterations. Max 2 iterations total.

**If questions still fail after 2 iterations** → stop and report the remaining issues to the user. Doc changes from all iterations are kept.

## Summary

After completion, report:
- Number of questions tested
- Per-question results: question text, initial grade/tags, final grade/tags
- Number of doc files changed
- Claims database: number of verified claims added
- Iterations completed
