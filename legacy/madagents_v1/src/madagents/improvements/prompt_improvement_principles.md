# Prompt Engineering Principles for Multi-Agent Systems

Principles for writing effective agent prompts, extracted from improving the MadAgents orchestrator, planner, and worker prompts. Applicable to any multi-agent system using GPT-5.x, Claude 4.x, or similar reasoning models.

---

## 1. Structure

### 1.1 Flatten and merge related sections

If two sections share a topic, merge them. Models don't need bureaucratic separation — they need clear, scannable information.

**Before:** `<environment_description>`, `<environment_guidance>`, `<context>`, `<allowed_assumptions>` as four nested blocks.
**After:** One flat `<environment>` block with bullet points.

Separate sections only when they serve genuinely distinct purposes (e.g., "what tools exist" vs. "when to use which tool").

### 1.2 Minimize prompt slots

Use one prompt string unless the API semantically requires two. Splitting into system + developer prompts forces the author to decide where each rule goes and creates risk of contradictions.

### 1.3 Use action-oriented section names

Name sections by what the agent needs to *do*: `<routing>`, `<reviewing>`, `<workflow>`. Avoid generic names like `<guidelines>` or `<output>`. Drop the suffix "guidelines" when the tag already implies guidance.

### 1.4 Compress stable rules

Once rules are well-understood and stable, convert bullet lists to concise prose. Bullets are good for drafting; dense prose is better for production where token count matters.

**Before (11 lines):**
```
Whenever you are invoked, follow the steps:
1. Infer from the conversation
  - What the user ultimately wants.
  - What has already been done by the agents.
  - Which agent execution was interrupted.
  - What is still missing or unclear.
2. You must decide whether
  - you should instruct an agent to act next or,
  - to talk to the user directly.
3. Send a message to the recipient.
```

**After (1 line):**
```
On each turn, assess the current state — what the user wants, what has been done, whether any agent execution was interrupted, and what is still missing — then either invoke the appropriate tool or respond directly to the user.
```

---

## 2. Content: What to Include

### 2.1 Only add rules for observed failure modes

Every rule should be traceable to a concrete problem. Avoid speculative rules — they add length without value. If you can't point to a specific failure that a rule prevents, don't add it.

### 2.2 State the desired behavior, not just prohibitions

Positive instructions are stronger than prohibitions. State what to do first, then add the boundary.

**Before:** "Do not fabricate results. Do not simulate agent execution." (two negatives)
**After:** "Delegate ALL substantive work to agents — never answer HEP software or physics questions from your own knowledge." (positive rule with boundary)

### 2.3 Scope information to the agent's role

Each agent should only see information it can act on:
- A planner doesn't need directory management guidance (workers handle files).
- A reviewer doesn't need routing rules (the orchestrator handles routing).
- Downstream workflow info ("after you create the plan, the reviewer will judge it") is not actionable and adds length without value.

### 2.4 State each fact once, in the most relevant location

If a fact appears in `<environment>`, don't restate it in `<workflow>`. Common offenders: trace paths, permission rules, CLI access constraints. When information is needed across sections, use a cross-reference rather than duplication.

### 2.5 Make override authority explicit

State who can override workflow rules and how. Without this, the model may rigidly follow rules when the user wants something different.

**Example:** "The user may override any part of this workflow — in particular reviewing frequency, quality/expense trade-offs, and iteration limits."

---

## 3. Content: What to Remove

### 3.1 Remove rules the model already follows

GPT-5.x and Claude 4.x have trained-in behaviors for safety, anti-hallucination, structured output, and tool calling. Test by removing rules one at a time and checking for regressions.

**Commonly redundant:**
- "Do not fabricate results" — trained-in via RLHF/safe-completion
- "Think step by step" — built into reasoning models, can *degrade* performance
- "Return valid JSON" — use structured output modes instead
- "Don't help with illegal activity" — core safety training
- Generic safety refusals — focus on *application-specific* policies instead

**Still needed:**
- Application-specific behavioral constraints
- Scope constraints ("only answer about X")
- Tool usage preferences (when to use which — models know *how* but not your preferred *when*)
- Domain-specific accuracy requirements

### 3.2 Don't explain constraints the architecture enforces

If the graph mechanics prevent a behavior (e.g., a model can't call tools and produce structured output simultaneously), don't tell the model not to do it. Prompt rules should only cover behaviors the model could actually choose.

### 3.3 Don't duplicate tool schemas in the prompt

Both OpenAI and Anthropic inject tool definitions from the `tools` API parameter into the model's context automatically. Duplicating the schema in the system prompt wastes tokens and measurably hurts performance (OpenAI measured a 2% decrease on SWE-bench when manually injecting schemas vs. using the API parameter).

### 3.4 Drop examples for obvious rules

Include examples only when the rule is genuinely ambiguous or counterintuitive. If the instruction is clear without the example, omit it.

---

## 4. Tool Descriptions

### 4.1 Separate schema from behavioral guidance

Tool descriptions should be split between two locations:

| Content | Where it belongs |
|---|---|
| Parameter names, types, required/optional | Pydantic schema (sent via `bind_tools()` / API `tools` param) |
| What the tool does (1-2 sentences) | Tool `description` field in the schema |
| When to use / when NOT to use | System prompt — behavioral guidance |
| Usage tips, caveats, limitations | System prompt — `*_DESC` blocks |
| Response format details | Omit — the model learns from actual responses |
| Usage examples (for complex tools) | System prompt — dedicated section |

### 4.2 Don't include return message shapes

Models learn response formats from seeing actual tool responses. Documenting the exact return format wastes tokens and becomes a maintenance burden when the format changes. The one exception: custom formats the model has never seen (e.g., the V4A diff syntax for `apply_patch`).

### 4.3 Front-load critical rules in tool descriptions

For reasoning models (o3, GPT-5), critical rules placed at the beginning of tool descriptions score higher on tool-calling accuracy evals. Put the most important constraint first.

### 4.4 Keep tool descriptions in the prompt concise

For tools bound via `bind_tools()`, the system prompt should contain only behavioral guidance that goes beyond the schema. The schema itself (parameter names, types, descriptions) is already visible to the model via the API.

**Before (36 lines):** Full bash description with return message shapes, encoding details, spill-to-file mechanics.
**After (6 lines):** Non-interactive, stdin disabled, 600s background feature, large output spill.

---

## 5. Multi-Agent Descriptions

### 5.1 Maintain two tiers of agent descriptions

When an agent is described for different consumers:
- **`_DESC`** (full): capabilities + calling tips. Used by agents that *dispatch* this agent (e.g., orchestrator instructing workers).
- **`_DESC_SHORT`** (capabilities only): what the agent can do, no calling tips. Used by agents that *reason about* what's possible (e.g., planner creating feasible steps).

Calling tips ("specify the absolute path", "make sub-questions explicit") are noise for agents that don't compose instructions.

### 5.2 Single source of truth

Define each description constant in the agent's own file and import it where needed. Never inline descriptions — this causes drift when one copy is updated but not another.

### 5.3 Match description detail to the consumer

The orchestrator needs routing rules and calling conventions. The planner needs capability summaries. The reviewer needs to know what workers can verify. Each consumer gets the description tier that matches its needs.

---

## 6. Compression Techniques

### 6.1 Em-dashes and parentheticals over sub-bullets

**Before:** Multi-level bullet nesting (3-4 levels deep).
**After:** Single-level bullets with em-dashes: "`/output` — user's directory for final deliverables. Persistent, shared across sessions."

### 6.2 Merge conditional chains into single sentences

**Before:** "If a specific choice/decision is needed, decide whether it can be easily changed later on: If so, let the specialized agents make the choice. Otherwise, ask the user."
**After:** "Act autonomously for decisions that are easy to revise. Involve the user for irreversible or high-impact decisions."

### 6.3 Use compact formats for reference data

Lookup tables, parameter defaults, and routing rules should use the most compact readable format.

**Example:**
```
Reasoning effort:
- Planner: high (new), medium (revision), low (specified changes).
- Reviewer: high.
- Workers: medium default. low trivial. high complex/retries.
```

---

## 7. Architectural Principles

### 7.1 Replace agents with tools for mechanical tasks

If an "agent" performs a deterministic, mechanical task (e.g., updating plan step statuses), replace it with a programmatic tool call. This saves tokens, reduces latency, and eliminates errors.

### 7.2 Prefer tool-calling over structured output for multi-action agents

Tool-calling enables parallel dispatch, plain-text responses, and batched operations. Structured output is appropriate only when there is exactly one action type with a fixed schema (e.g., the planner producing a plan).

### 7.3 Use explicit read/write tools for persistent state

When an agent needs persistent state (scratchpad, plan), use explicit tools (`ReadPlan`, `UpdateScratchpad`) rather than implicit fields carried forward. This makes the state lifecycle visible and controllable.

### 7.4 Handle errors in the infrastructure, not the prompt

GPT-5.x and Claude 4.x are increasingly capable of autonomous error recovery. Rather than scripting recovery procedures in the prompt ("inspect logs, then try fix A, then try fix B"), return errors as tool results and let the model reason about recovery itself. The prompt should only specify *application-specific constraints* — retry caps, escalation patterns, when to stop and report — not the recovery procedure.

**Before (7 lines):** Step-by-step error recovery procedure with nested bullets.
**After (1 line):** "On failure, inspect errors/logs and try 2-3 fixes. If still stuck, stop and report: the error, what you tried, and root-cause hypotheses."

### 7.5 Provide split and merged versions of shared blocks

When multiple agents share a prompt block (e.g., environment description) but some agents need to append agent-specific lines, provide both:
- **Sub-parts** (`ENVIRONMENT_DESCRIPTION_BASE`, `ENVIRONMENT_GUIDANCE_BASE`) for agents that insert custom lines between them.
- **Merged convenience constant** (`ENVIRONMENT_BASE`) for agents with no customization.

This avoids duplication while preserving flexibility. Define the merged version as a composition of the sub-parts so they stay in sync.

---

## 8. Checklist for Improving an Agent Prompt

Apply these in order when reviewing any agent prompt:

1. **Audit for redundancy.** Search for rules that say the same thing in different words or sections.
2. **Remove trained-in behaviors.** Safety refusals, anti-hallucination, "think step by step" — remove unless you've observed failures without them.
3. **Remove architecture-enforced constraints.** If the graph prevents it, the prompt doesn't need to say it.
4. **Scope to the agent's role.** Remove information the agent can't act on.
5. **Merge sections that share a topic.** If you cross-reference two sections, they should be one.
6. **Flatten nesting.** Replace nested sub-sections with flat bullet lists.
7. **Convert negatives to positives.** "Don't X" → "Do Y (not X)."
8. **Compress stable rules.** Bullets → prose for well-understood rules.
9. **Drop obvious examples.** Keep only for ambiguous or counterintuitive rules.
10. **Verify tool descriptions.** Schema in API, behavioral guidance in prompt. No return message shapes.
11. **Match description tiers to consumers.** `_DESC` for dispatchers, `_DESC_SHORT` for planners.
12. **State override authority.** Make clear when the user can override defaults.
13. **Add rules only for observed failures.** Every rule traceable to a specific problem.
14. **State each fact once.** In the most relevant location.

---

## 9. Rubric-Based Verification (VERA)

Based on: *Unified Plan Verification with Static Rubrics and Dynamic Policies for Reliable LLM Planning* (ICLR 2025, [OpenReview](https://openreview.net/forum?id=qDFegAnCin)).

### 9.1 Use structured rubrics instead of free-form critique

Replace "review this plan" with a binary PASS/FAIL checklist per dimension. Structured rubrics outperform free-form critique because they force the critic to check each dimension explicitly (nothing gets skipped), binary decisions are easier for LLMs than nuanced judgments, and failures pinpoint exactly what is wrong — making revision loops converge faster.

### 9.2 Separate general taxonomy from instance-specific checks

The **system prompt** defines the general taxonomy (the dimensions to check). The **user prompt** instantiates task-specific binary questions from the taxonomy using the user's actual goal and constraints.

Example: A general "Completeness" dimension becomes "Does the plan include lodging for every night within the requested dates and budget?" for a travel task, or "Does the plan address the 13 TeV beam energy specified by the user?" for an HEP task.

### 9.3 VERA's three core dimensions

VERA's general taxonomy uses three dimensions:

1. **Completeness**: All required elements are included.
2. **Correctness**: Logical/factual soundness — constraint satisfaction, step-to-goal alignment, internal consistency, no hallucinations.
3. **Executability**: The plan can actually run in the target environment.

These can be extended with domain-specific dimensions (e.g., parallelizability, step clarity) as needed.

### 9.4 Support domain-specific hard rules

VERA allows optional hard rules that the generic taxonomy may not cover (e.g., "never exceed $500 total airfare"). In practice, these encode constraints that are always true for the domain — such as "no meta-steps about planning or reviewing" in an orchestrated multi-agent system.

### 9.5 Complement pre-execution rubrics with runtime verification

VERA's second component, Dynamic Verification Policy (DVP), monitors execution at runtime. The combination of pre-execution static rubrics and runtime dynamic policies consistently outperforms either alone. Consider both when designing verification for multi-step workflows.
