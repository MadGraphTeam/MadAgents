# v1.0 → v1.1 Architectural Changes: Analysis

This document evaluates each architectural change introduced in v1.1 compared to v1.0,
assessing whether it improves the agent system. Verdicts are supported by literature
references where available, and evidence gaps are noted explicitly.

---

## 1. Orchestrator: Structured Output → Tool Calling

### What changed

**v1.0:** The orchestrator is a standalone LangGraph subgraph (`Orchestrator.graph`) with an internal
`StateGraph(OrchestratorState)` containing a single "agent" node. It uses `runtime.with_structured_output(OrchestratorDecision, include_raw=True)` to produce exactly one `OrchestratorDecision` per turn — a Pydantic model with fields `recipient`, `reasoning`, `message`, `reasoning_effort`, and `future_note`. The outer graph reads `state["orchestrator_decision"]["recipient"]` to route to one of the other nodes (planner, plan_updater, reviewer, worker, or user/END). Validation failures are caught by `invoke_with_validation_retry()` which retries up to 3 times on Pydantic `ValidationError`.

**v1.1:** The orchestrator class is a plain container (no internal graph) storing `self.llm`, `self.runtime`, and `self.reasoning_effort`. All orchestration logic lives in `graph.py`'s `get_orchestrator_node()`. The LLM is invoked with 7 tools bound (`InvokePlanner`, `InvokeReviewer`, `InvokeWorker`, `UpdatePlan`, `UpdateScratchpad`, `ReadPlan`, `ReadScratchpad`). The response's `.tool_calls` attribute is parsed into dispatch dicts via `_parse_tool_call_to_decision()`. Multiple tool calls in a single response are supported, enabling parallel dispatch. When no tool is called, the text content is treated as a direct user response. There is no validation retry loop.

### Why it matters

- **Multi-action turns.** v1.0 required two full graph cycles (orchestrator → plan_updater → orchestrator → worker) for a common pattern like "update plan then dispatch worker." v1.1 handles both in one LLM invocation.
- **Native LLM affordance.** Tool calling is a first-class feature of modern LLMs. Structured output forces the entire response into a rigid schema, preventing the LLM from mixing free-form text (for the user) with structured actions.
- **Simpler error surface.** The `invoke_with_validation_retry` mechanism in v1.0 implies that structured output failures were a real concern. Tool calling leverages provider-native formats which are more reliable.

### Trade-off

v1.0's structured output **forced** every field to be present. The LLM couldn't "forget" to specify a recipient. With tool calling, the LLM could respond with plain text when it should have invoked a tool. The v1.1 prompt mitigates this with explicit guidance.

### Verdict: Improvement

### Evidence

- **Tam et al. (2024), "StructEval: Benchmarking LLMs' Capabilities to Generate Structural Outputs"**: Requiring JSON output reduced accuracy on GSM8K by **27.3 percentage points** compared to natural language. Structured formats force models to simultaneously handle format constraints, query understanding, and tool selection. [arXiv:2505.20139](https://arxiv.org/html/2505.20139v1)
- **Vellum Blog, "When should I use function calling, structured outputs or JSON mode?"**: Function calling offloads parsing responsibility to model providers. Structured output with strict mode guarantees schema adherence via logit biasing, but constrains the model's output space. [Vellum](https://www.vellum.ai/blog/when-should-i-use-function-calling-structured-outputs-or-json-mode)
- **Evidence gap:** No paper directly benchmarks tool-calling vs structured-output for multi-agent orchestration. The StructEval results apply to JSON output generally, not tool-calling schemas specifically. The move from structured output to tool calling is well-supported by industry practice (OpenAI's Responses API, LangChain's default agent patterns) but lacks a controlled academic comparison.

---

## 2. Parallel Agent Dispatch

### What changed

**v1.0:** `route_from_orchestrator()` returns a single `Literal` string — exactly one recipient per orchestrator turn. No parallel execution is possible.

**v1.1:** `route_from_orchestrator()` returns either a string (single dispatch) or a `list[Send]` for multiple dispatches. Each `Send` object carries the full state with a per-dispatch `current_dispatch` dict. LangGraph executes all `Send` targets in parallel within a single "superstep." State merging upon return is handled by custom reducer functions (`merge_agent_messages`, `merge_full_messages`, `merge_dict`) that merge by unique keys (message IDs via `uuid.uuid4().hex`) to avoid collisions.

### Why it matters

- A 20-step plan with several independent steps can execute them concurrently, reducing wall-clock time proportionally.
- The orchestrator prompt explicitly guides this: "May work on multiple independent plan steps in parallel when their dependencies are all resolved."
- `_get_parallel_ready_steps()` identifies parallel-eligible steps by checking that all dependencies are `done` or `skipped`. This information is surfaced in the compact plan summary.

### Trade-off

- LangGraph supersteps are transactional — a slow sibling branch blocks downstream progress of fast branches ([LangGraph Issue #6320](https://github.com/langchain-ai/langgraph/issues/6320)).
- Parallel execution increases instantaneous resource usage (concurrent API calls).

### Verdict: Improvement (latency reduction for independent steps)

### Evidence

- **LangGraph Documentation — Branching**: LangGraph natively supports fan-out/fan-in using `Send()`. Multiple edges from a single node automatically trigger parallel execution in a superstep. State merging uses reducer operations. [LangGraph Docs](https://www.baihezi.com/mirrors/langgraph/how-tos/branching/index.html)
- **"Scaling LangGraph Agents: Parallelization, Subgraphs, and Map-Reduce Trade-Offs"**: Parallel execution reduces latency but increases instantaneous resource usage. Supersteps are transactional — checkpointing saves results from successful nodes, so only failing branches retry. [AI Practitioner Substack](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)
- **Evidence gap:** No benchmark quantifying the actual latency improvement from parallel dispatch in this specific system. The benefit depends on how often truly independent steps occur and on API call latency.

---

## 3. Inline Plan Updates (LLM Agent → Deterministic Processing)

### What changed

**v1.0:** Plan updates require a dedicated LLM call. The orchestrator routes to a `plan_updater` node, which invokes a separate LLM (`plan_updater_llm`) with `PLAN_UPDATER_SYSTEM_PROMPT` and a developer prompt containing the full current plan. The LLM produces structured output (`PlanUpdate`), which is validated and applied via `update_plan()`. The system prompt contains 10 constraint lines: "Do not fabricate results or outcomes," "Do not split updates for a single step," "Do not create step updates for nonexistent step IDs," etc.

**v1.1:** Plan updates are deterministic and LLM-free. The `UpdatePlan` tool call carries structured `step_updates` in its arguments (step ID, status, outcome). The orchestrator node parses them into `PlanStepUpdate` objects and calls `update_plan()` inline. No separate graph node, no LLM invocation. Invalid step IDs are silently skipped (same behavior as v1.0's `get_plan_step()` returning None).

### Why it matters

- Saves one LLM call per plan update. For a 10-step plan, that's ~20 eliminated LLM calls (in_progress + done for each step).
- The 10 constraint lines in v1.0's prompt are evidence that the LLM-based approach had real failure modes. v1.1 makes all of these impossible by construction.
- Eliminates latency: each plan update in v1.0 required a full LLM round-trip (seconds); v1.1 does it in microseconds.

### Verdict: Strictly better (no trade-offs identified)

### Evidence

- **Qiu et al. (2025), "Blueprint First, Model Second: A Framework for Deterministic LLM Workflow"**: Proposes separating deterministic workflow execution from LLM-driven decisions. Pre-defined blueprints reduce non-deterministic behavior and enable reusability across models. [arXiv:2508.02721](https://arxiv.org/pdf/2508.02721)
- **"Get Experience from Practice: LLM Agents with Record & Replay" (2025)**: Since most task steps can be executed by replaying a pre-derived plan, the number of LLM calls is "drastically decreased." [arXiv:2505.17716](https://arxiv.org/html/2505.17716v1)
- **Optimization Techniques for Agent Performance (apxml.com)**: "Analyze the agent's decision-making process. Can certain choices be made heuristically or with a simpler rule-based system instead of a full LLM call?" [apxml.com](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-6-evaluation-optimization-agentic-systems/optimization-techniques-agent-performance)
- These sources consistently support the principle: use LLMs for genuinely non-deterministic decisions; use deterministic code for mechanical operations.

---

## 4. Dual Message Streams (Private Orchestrator Context)

### What changed

**v1.0:** Single `messages` stream shared between all agents and the UI. The orchestrator sees the same messages as the user.

**v1.1:** Two parallel streams:
- `messages` (display/UI): Contains `AIMessage` objects with display-friendly content for the frontend.
- `orchestrator_messages` (private): Contains the orchestrator's raw `AIMessage` (with `tool_calls` and reasoning tokens intact) and `ToolMessage` responses with truncated agent results.

The raw LLM response — including encrypted reasoning tokens (OpenAI) or extended thinking blocks (Anthropic) — goes directly into `orchestrator_messages`. This means **reasoning tokens are preserved across turns**. In v1.0, `response_to_text()` was applied to create the display content (extracting only `type == "text"` blocks), which stripped reasoning tokens.

### Why it matters

- **Protocol alignment.** Tool-calling LLMs expect AIMessage(tool_calls) → ToolMessage alternation. v1.0's flat stream of named AIMessages didn't match this protocol.
- **Reasoning token reinsertion.** The orchestrator's chain-of-thought persists across turns, enabling better multi-step reasoning. OpenAI's `include=["reasoning.encrypted_content"]` and Anthropic's extended thinking both benefit from this.
- **Context efficiency.** Agent outputs are truncated to 3000 chars in `orchestrator_messages` via `_save_artifact_if_needed()`, while the UI stream gets full outputs.

### Trade-off

- State synchronization complexity: HumanMessages must be synced from `messages` to `orchestrator_messages` (graph.py lines 650-668).
- Two message streams are harder to debug than one.

### Verdict: Significant improvement

### Evidence

- **OpenAI Responses API Cookbook, "Better performance from reasoning models"**: Persisting encrypted reasoning items across tool calls yields ~**3% improvement on SWE-bench**. Cache utilization jumps from 40% to 80%. "Reasoning persistence boosts intelligence, reduces token usage, and increases cache hit rates." [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/responses_api/reasoning_items/)
- **Anthropic Extended Thinking Documentation**: For Claude Opus 4.5+, thinking blocks are preserved by default across turns. Preserved thinking blocks enable prompt cache hits. "Thinking blocks must be passed back unmodified during tool use loops to maintain reasoning continuity." [Anthropic Docs](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
- These are direct evidence from the two major LLM providers that reasoning token reinsertion improves performance.

---

## 5. Context Filtering for Planner and Reviewer

### What changed

**v1.0:** Both planner and reviewer receive the full `messages` list (after summarization). They see all agent responses, plan updates, worker tool outputs, and user messages in one stream.

**v1.1:** `_extract_user_orchestrator_messages()` filters the `messages` stream to only `HumanMessage`s and orchestrator `AIMessage`s. These filtered messages are then summarized (older exchanges compressed, recent ones kept intact) and delivered to both planner and reviewer in the same format: a `<conversation_context>` block appended to the developer prompt, containing:
- `<summarized_history>`: Condensed summary of older user↔orchestrator exchanges (may be absent for short sessions).
- `<recent_exchanges>`: Recent user↔orchestrator dialogue formatted as `[User]`/`[Orchestrator]` text lines.
- `<current_plan>`: The current plan state as JSON (if one exists).

Neither planner nor reviewer sees worker responses, tool call details, or other agents' outputs. Both receive their context as formatted text in the developer prompt, cleanly separated from their own tool-calling conversation.

Additionally, v1.1 uses a shared `conversation_summary` / `conversation_non_summary_start` state pair that tracks only user/orchestrator exchanges, separate from the orchestrator's own summarization state.

### Why it matters

- **Noise reduction.** For a 20-step plan, the full stream might contain 60+ messages of worker execution details irrelevant to planning or reviewing.
- **Token savings.** Worker responses can be enormous (bash outputs, analysis results). Filtering them out reduces token consumption significantly.
- **Structured format.** The reviewer gets a cleanly structured context block instead of a raw message dump.

### Trade-off

The orchestrator must relay all relevant worker outcomes in its instruction. If it forgets, the planner/reviewer operates on incomplete information.

### Verdict: Improvement

### Evidence

- **Lindenbauer, Slinko, Felder, Bogomolov, Zharov (NeurIPS 2025 DL4Code Workshop), "The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management"**: Observation masking (targeting only environment observations while preserving action/reasoning history) **halves cost** relative to unmanaged context while matching or slightly exceeding the solve rate of LLM summarization. LLM summarization caused agents to run **15% longer** (52 turns vs 45) because summaries masked stopping signals. [arXiv:2508.21433](https://arxiv.org/abs/2508.21433)
- **Adobe Research (2025), "NoLiMa: Long-Context Evaluation Beyond Literal Matching"**: At 32K tokens, 10 of 12 LLMs achieve only **half** of their short-context performance. Performance declines start at just 2K-8K tokens. [arXiv:2502.05167](https://arxiv.org/abs/2502.05167)
- These papers establish that (a) reducing context length improves LLM performance, and (b) simple masking/filtering is as effective as expensive LLM summarization.

---

## 6. Worker Context Enrichment (Plan Injection + Masked History)

### What changed

**v1.0:** Workers receive only the orchestrator's `message` field and their accumulated execution history (with summarization but no masking).

**v1.1:** Three changes:
1. `_build_worker_context()` automatically prepends a `<plan_context>` block containing the current in-progress step(s) and completed dependency outcomes. An optional `step_id` parameter enables targeted context: when set, only the specified step and its dependencies are shown (recommended for parallel dispatch).
2. `mask_tool_observations()` (2000 char limit, head+tail) truncates verbose tool results in worker history. Applied both in `graph.py` when persisting results and in `base.py` as defense-in-depth.
3. The `InvokeWorker` tool exposes an optional `step_id` field. When the orchestrator dispatches multiple workers in parallel, each worker receives only its own step's context rather than all in-progress steps.

### Why it matters

- Plan context injection gives workers situational awareness that the orchestrator might forget to include manually.
- Without history masking, a worker invoked 5+ times could accumulate 100K+ tokens of old tool outputs.

### Verdict: Strictly better (no trade-offs)

### Evidence

- **"The Complexity Trap" (NeurIPS 2025)**: Observation masking with a window of the **latest 10 turns** provided the best balance between performance and efficiency. [arXiv:2508.21433](https://arxiv.org/abs/2508.21433)
- **LangChain, "Context Management for Deep Agents" (Jan 2026)**: Deep Agents offload large tool results at 20,000 tokens and truncate at 85% context window capacity. [LangChain blog](https://blog.langchain.com/context-management-for-deepagents/)
- **Liu et al. (TACL 2024), "Lost in the Middle: How Language Models Use Long Contexts"**: Performance is highest when relevant information is at the beginning or end of context, and "significantly degrades when models must access relevant information in the middle." [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
- The head+tail masking strategy in v1.1 directly addresses the "lost in the middle" effect by preserving the beginning and end of each tool output.

---

## 7. Scratchpad: `future_note` → Dedicated Tools

### What changed

**v1.0:** `future_note` is a field on `OrchestratorDecision` — a string in the structured output. It is stored in the AIMessage's `additional_kwargs` (inside the `orchestrator_decision` dict), NOT in the message `content` field. The prompt guidance says "2-5 turns" and "keep it concise."

**v1.1:** Persistent `scratchpad: Optional[str]` field in `MadAgentsState`, managed via `UpdateScratchpad` (replace entire content) and `ReadScratchpad` (retrieve current content) tools. The prompt guidance says "under ~500 words" and "update it when context shifts significantly."

### Why v1.0's approach was flawed

1. `response_to_text()` only extracts `type == "text"` blocks, so `future_note` was NOT in the message `content`.
2. The summarizer processes `content`, not `additional_kwargs`. When messages were summarized, `future_note` was permanently lost.
3. LLMs typically see only the `content` field of messages. A `future_note` from N turns ago was likely invisible even before summarization.

### Why v1.1's approach is better

1. The scratchpad is a graph state field, not a message field. It survives summarization.
2. Explicit read/write via tool calls. The orchestrator knows exactly when it wrote and can explicitly read.
3. The prompt explicitly addresses recovery: "After a conversation summary occurs, the plan and scratchpad may no longer appear in your recent messages. Use the read tools to refresh your state."

### Verdict: Strictly better

### Evidence

- **Packer et al. (2023), "MemGPT: Towards LLMs as Operating Systems"**: Introduces virtual context management inspired by OS memory hierarchies. Working context serves as a scratchpad. Demonstrated ability to analyze documents exceeding context windows and maintain multi-session conversational memory. [arXiv:2310.08560](https://arxiv.org/abs/2310.08560)
- **Xu, Liang et al. (NeurIPS 2025), "A-MEM: Agentic Memory for LLM Agents"**: Dynamic memory organization with explicit read/write operations. Shows "superior improvement against existing SOTA baselines" on long-term conversational benchmarks. [arXiv:2502.12110](https://arxiv.org/abs/2502.12110)
- **Letta Blog, "Memory Blocks: The Key to Agentic Context Management"**: Explicit memory blocks serve as structured scratchpads that persist across turns, with the agent deciding what to write, update, and delete. [Letta blog](https://www.letta.com/blog/memory-blocks)
- Strong consensus: explicit, persistent memory outperforms implicit in-context memory for long-horizon tasks.

---

## 8. Planner: Single-Phase → Two-Phase (Research + Plan)

### What changed

**v1.0:** Planner is a single-node graph (`START → agent → END`). One LLM call with structured output (`Plan`). Only `web_search_tool` available.

**v1.1:** Two-phase graph (`START → research → [tools | plan → END]`). The research phase is a tool-calling loop with `bash_tool`, `read_pdf_tool`, `read_image_tool`, `web_search_tool`. The research LLM has its own system/developer prompts (`RESEARCH_SYSTEM_PROMPT`, `RESEARCH_DEVELOPER_PROMPT`) that enforce read-only behavior and provide full environment context (directory layout, worker capabilities, domain assumptions, trace access). When the research LLM stops calling tools, it flows to the plan node which produces structured output. The plan phase has no tools — it uses only structured output (`Plan` schema), relying entirely on research findings in the message history.

### Why it matters

- The planner can inspect the filesystem, read PDFs, search the web, and run read-only bash commands **before** creating the plan. This enables environment-aware planning (e.g., checking what software is installed, what files exist).
- v1.0's planner could only do web search. Any environment inspection had to be planned as a step, executed, and then the plan revised.
- The plan phase has no tools, enforcing a clean separation: research gathers information, planning synthesizes it. This prevents the planner from making tool calls during structured output generation, which would be unsupported by the graph topology.

### Trade-off

- Adds latency to plan creation (research phase may make multiple tool calls before producing a plan).
- Additional prompt engineering surface (research system/developer prompts, now full-quality prompts matching the standard of other agents).

### Verdict: Improvement

### Evidence

- This is an application of the general principle that planning benefits from information gathering. No specific paper benchmarks "research before planning" in LLM agents, but the benefit is self-evident: a plan that accounts for existing files and installed software is more likely to be correct than one based on assumptions. This is analogous to the standard software engineering practice of gathering requirements before design.
- **Evidence gap:** No controlled study comparing single-phase vs two-phase planning in LLM agents.

---

## 9. Summarizer Improvements

### What changed

**v1.0:** Free-form summary output. The summarizer prompt says "Only output the summary." Messages are passed directly to the LLM without preprocessing.

**v1.1:** Multiple improvements:
1. **Structured output format.** Summary must be in `<summary>` tags with 5 sections: "Task Overview", "Current State", "Important Discoveries", "Plan", "Environment". A regex parser (`_extract_summary_tags()`) extracts the content.
2. **Pre-summarization processing.** Before invoking the summarizer LLM: (a) `strip_inline_base64()` removes binary payloads, (b) `_truncate_tool_results_for_summary()` truncates tool results to 500 chars. This reduces summarizer input size.
3. **Stronger recall guidance.** "Your summary replaces the messages you see. Any unmentioned information is permanently lost. Prioritize recall: it is far better to include something unnecessary than to lose something critical."

### Why it matters

- Structured summaries are more consistently formatted and easier for downstream agents to parse.
- Pre-processing prevents the summarizer from being overwhelmed by huge tool outputs or base64 payloads.
- Explicit recall priority reduces the risk of losing critical information during summarization.

### Verdict: Improvement

### Evidence

- **"The Complexity Trap" (NeurIPS 2025)**: LLM summarization caused agents to run **15% longer** because summaries masked stopping signals. This highlights the risk of information loss during summarization and supports the "prioritize recall" guidance. [arXiv:2508.21433](https://arxiv.org/abs/2508.21433)
- **LangChain, "Context Management for Deep Agents"**: Summarization produces structured summaries (session intent, artifacts, next steps) while preserving original messages on disk. Structured summarization is industry standard practice for long-running agents. [LangChain blog](https://blog.langchain.com/context-management-for-deepagents/)

---

## 10. Reasoning Token Reinsertion

### What changed

**v1.0:** The display stream stored `response_to_text(result["messages"][-1])` — only `type == "text"` blocks. Reasoning tokens (OpenAI encrypted reasoning, Anthropic extended thinking) were stripped. The orchestrator consumed the same display stream, so it **lost its own chain-of-thought between turns**.

**v1.1:** The raw `AIMessage` response goes into `orchestrator_messages` (line 908). For OpenAI, `bind_reasoning_trace()` does `llm.bind(include=["reasoning.encrypted_content"])`, requesting encrypted reasoning tokens that are decrypted by the provider when sent back. For Anthropic, extended thinking blocks are part of the AIMessage content natively. The orchestrator's chain-of-thought is preserved across turns.

### Why it matters

Multi-step orchestration is inherently a reasoning-heavy task. The orchestrator must track goals, infer what has been accomplished, and decide the next action. Losing chain-of-thought between turns forces it to re-derive this reasoning from the conversation each time.

### Verdict: Significant improvement

### Evidence

- **OpenAI Responses API Cookbook**: Persisting encrypted reasoning items across tool calls yields ~**3% improvement on SWE-bench**. Cache utilization jumps from 40% to 80%. [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/responses_api/reasoning_items/)
- **OpenAI Reasoning Models Guide**: "Reasoning persistence boosts intelligence, reduces token usage, and increases cache hit rates." [OpenAI Guide](https://developers.openai.com/api/docs/guides/reasoning/)
- **Anthropic Extended Thinking Documentation**: Thinking blocks must be passed back unmodified during tool use loops to maintain reasoning continuity. Preserved thinking blocks enable prompt cache hits. [Anthropic Docs](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
- This is one of the strongest evidence-backed improvements: both major LLM providers document measurable benefits from reasoning token persistence.

---

## 11. Review Intensity Signaling

### What changed

**v1.0:** No review intensity concept. Every reviewer invocation receives the same treatment.

**v1.1:** The orchestrator signals "quick check" or "thorough review" in its instruction. The reviewer prompt includes a `<review_intensity>` section:
- **Quick check:** Structural assessment, no tool calls unless something looks wrong. Default for plan reviews and low-risk intermediate steps.
- **Thorough review:** Use tools to verify outputs in detail. Default for final deliverables, plots, and high-stakes/foundational steps.

Additionally, v1.1 adds plan review permissiveness ("plans are high-level outlines that will be refined during execution"), issue classification (operational / substantive / unverifiable), and revision thresholds ("recommend revise only if structural flaw").

### Why it matters

Verification phases consume disproportionate resources. Applying the same thoroughness to a plan review as to a final deliverable check wastes tokens and time.

### Verdict: Improvement

### Evidence

- **Hong et al. (ICLR 2024), "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework"**: In MetaGPT's development experiments, **72% of tokens are used for verification**. Despite the overhead, verification achieved 100% task completion rate — suggesting review is valuable but its cost should be managed. [arXiv:2308.00352](https://arxiv.org/abs/2308.00352)
- **"On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents" (ICLR 2025 Workshop)**: Review mechanisms recover up to **96.4% of errors** made by faulty agents. This confirms review value but doesn't address intensity calibration. [OpenReview](https://openreview.net/forum?id=bkiM54QftZ)
- **Evidence gap:** No paper directly benchmarks adaptive review intensity (more/less thorough depending on stakes). The MetaGPT 72% overhead figure is the strongest indirect evidence that review intensity should be calibrated. The improvement is supported by the general principle that allocating resources proportionally to risk is more efficient than uniform allocation.

---

## 12. Worker History Management (`clear_history`)

### What changed

**v1.0:** No way to clear a worker's accumulated conversation history. History only grows (with summarization).

**v1.1:** `InvokeWorker` has a `clear_history: bool` field (default `False`). When `True`, the worker executor discards all prior `prev_msgs` and sets `agent_message_summary = None`. The orchestrator prompt includes detailed guidance on when to use it:
- **Use when:** New task is unrelated, prior context is stale/misleading, worker accumulated a long irrelevant trace.
- **Don't use when:** Worker needs to build on prior work, continuity matters, retrying a failed step where error context is valuable.

### Why it matters

Over a long plan, a worker invoked for unrelated tasks accumulates irrelevant history that wastes tokens and may mislead the LLM.

### Verdict: Improvement

### Evidence

- **Moveworks, "Context Window Management"**: Without reset mechanisms, agents suffer from "context pollution" — token waste, hallucinations/bias from carried-over constraints, and memory overflow. [Moveworks Docs](https://docs.moveworks.com/agent-studio/agentic-ai/assistant-behavior-framework/context-window-management)
- **mem0, "LLM Chat History Summarization Guide" (2025)**: Periodically compressing older conversation segments into summaries while keeping recent ones intact is the standard approach. An explicit reset is the extreme case of this. [mem0 blog](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)
- The `clear_history` flag is the explicit version of what these sources recommend — giving the orchestrator control over when to reset vs. continue.

---

## 13. Output Truncation and Artifact Saving

### What changed

**v1.0:** Full agent responses are stored in the shared `messages` stream. The summarizer handles context management.

**v1.1:** Two-tier truncation:
1. **For orchestrator context:** `_save_artifact_if_needed()` truncates agent outputs at 3000 chars in ToolMessages using **head+tail** truncation (first 1500 chars + last 1500 chars). Full output is saved to `/workspace/.agent_artifacts/` with a file reference in the truncated version. The head+tail strategy ensures the orchestrator sees both the setup context (typically at the beginning) and conclusions/results (typically at the end).
2. **For worker history:** `mask_tool_observations()` keeps head+tail (2000 chars each half) of verbose tool results, preserving the beginning and end while masking the middle.

### Why it matters

In v1.1, agent responses go into ToolMessages in `orchestrator_messages`. Without truncation, a worker producing a 50K-char response would bloat the orchestrator's context. The head+tail masking strategy directly addresses the "lost in the middle" effect by preserving the two positions where LLMs pay the most attention.

### Verdict: Improvement

### Evidence

- **Liu et al. (TACL 2024), "Lost in the Middle: How Language Models Use Long Contexts"**: Performance is **highest when relevant information is at the beginning or end** of context, and "significantly degrades when models must access relevant information in the middle." Tested on multi-document QA and key-value retrieval. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
- **"The Complexity Trap" (NeurIPS 2025)**: Simple observation masking at 52% cost reduction matches LLM summarization solve rates, providing a practical compression strategy. [arXiv:2508.21433](https://arxiv.org/abs/2508.21433)
- **LangChain, "Context Management for Deep Agents"**: Tool outputs >20K tokens are offloaded; context truncation triggers at 85% of window capacity; summarization is a last resort. [LangChain blog](https://blog.langchain.com/context-management-for-deepagents/)
- The head+tail strategy is directly supported by the "lost in the middle" finding: preserving the positions where LLMs pay the most attention.

---

## 14. Self-Loop Guard

### What changed

**v1.0:** Not needed. Every orchestrator decision routes to a different graph node or END.

**v1.1:** When the orchestrator's turn produces only inline operations (UpdatePlan, UpdateScratchpad, ReadPlan, ReadScratchpad) and no external dispatches, it self-loops. `MAX_CONSECUTIVE_SELF_LOOPS = 15` prevents infinite loops — after 15 consecutive self-loops, it forces a break-out to the user.

### Verdict: Necessary safety mechanism (no trade-offs)

### Evidence

Self-evident: the tool-calling architecture creates a self-loop possibility that didn't exist in v1.0. The guard prevents runaway resource consumption. This is standard practice in agentic systems.

---

## 15. New Agent: physics_expert

### What changed

**v1.0:** 6 workers. Physics questions go through the researcher (web search) or the orchestrator itself.

**v1.1:** 7 workers. Adds `physics_expert` specialized in analytical derivations, cross-checks, and assessment of simulation configurations.

### Verdict: Improvement (fills a clear gap)

### Evidence

Domain-specific: the system is designed for particle physics workflows. A dedicated physics expert avoids the orchestrator answering from its own potentially outdated knowledge (which the prompt explicitly forbids for MadGraph-related topics). No external evidence needed; this is a domain requirement.

---

## 16. Model Routing

### What changed

**v1.0:** All workers use the model they were initialized with. No per-invocation model selection.

**v1.1:** When `enable_worker_model_routing=True` (default: `False`), the `InvokeWorker` tool gains a `model` parameter. `_make_invoke_worker_with_model()` dynamically creates an InvokeWorker schema listing available models. Model routing guidelines are injected into the orchestrator prompt. The worker executor passes `model_override` to the worker's graph, which creates a new LLM with the specified model.

### Trade-off

- Adds cognitive load to the orchestrator (another dimension of decision-making).
- Additional prompt complexity (model tier descriptions consume context).
- Default-off status suggests the developers aren't fully confident in the benefit.

### Verdict: Marginal improvement, questionable complexity

### Evidence

- **Evidence gap:** No paper benchmarks per-invocation model routing in multi-agent systems. The concept is intuitively sound (use cheaper models for simple tasks), but the added orchestrator complexity may outweigh cost savings if the orchestrator makes poor routing decisions. The default-off status is appropriate.

---

## 17. `require_madgraph_evidence` Removal

### What changed

**v1.0:** Both orchestrator and reviewer accept `require_madgraph_evidence: bool`. When True, injects detailed MadGraph evidence verification rules: the orchestrator must label claims as VERIFIED/UNVERIFIED, cite evidence types (documentation excerpts, CLI output, source code), and the reviewer enforces a two-stage rule with anti-loophole checks.

**v1.1:** Feature removed entirely. Replaced by a blanket rule in the orchestrator prompt: "CRITICAL: Never write MadGraph commands, scripts, configurations, or technical HEP software instructions yourself. Always dispatch the appropriate worker agent."

### Why it matters

v1.0's approach tried to make the orchestrator reliable for MadGraph claims by adding verification overhead. v1.1 takes a simpler approach: the orchestrator never makes MadGraph claims at all; it always delegates to `madgraph_operator` which has access to curated documentation.

### Verdict: Simplification (improvement)

### Evidence

This is an application of the principle of least authority: rather than verifying the orchestrator's MadGraph claims (complex, error-prone), prevent the orchestrator from making them at all (simple, reliable). No external evidence needed; the architectural argument is self-evident.

---

## 18. Compact Plan Summaries

### What changed

**v1.0:** No plan summaries in agent responses. The orchestrator must read the full plan from the message stream.

**v1.1:** `_compact_plan_summary()` generates a one-line status overview appended as a footer to every worker and reviewer ToolMessage. Actionable statuses (in_progress, pending, blocked, failed) include step titles so the orchestrator knows *what* each step is without calling ReadPlan; completed statuses (done, skipped) show bare IDs only. Example: `Plan: 5 steps | done: [1,2] | in_progress: [3: Run simulation] | pending: [4: Analyze output, 5: Plot results] | parallel-ready: [4,5]`.

### Why it matters

The orchestrator gets a lightweight status update with every agent response, without needing to call `ReadPlan`. This is especially useful when the full plan is large.

### Verdict: Improvement (no trade-offs)

### Evidence

Token-efficient status reporting is a standard pattern. The plan summary consumes ~50 tokens per message, far less than the full plan. No external evidence needed.

---

## 19. `adaptive` Reasoning Flag

### What changed

**v1.0:** `runtime.bind_reasoning(llm, reasoning_effort=...)` without `adaptive`.

**v1.1:** `runtime.bind_reasoning(llm, reasoning_effort=..., adaptive=True)` on the orchestrator, reviewer, and planner research phase.

### Why it matters

The `adaptive` flag allows the LLM provider to dynamically adjust reasoning depth based on the task difficulty, rather than applying a fixed effort level. This is relevant for the orchestrator, which handles both trivial routing decisions and complex multi-step planning.

### Verdict: Likely improvement

### Evidence

- **Anthropic, "Adaptive Thinking"**: Extended thinking with adaptive budget allows the model to "think less for simpler tasks and more for harder tasks." [Anthropic Docs](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
- The benefit is provider-dependent and may not apply to all runtimes.

---

## 20. Abbreviated Worker Descriptions for Planner/Reviewer

### What changed

**v1.0:** Planner and reviewer import full `_DESC` constants from each worker module (detailed invocation instructions, constraints, expected outputs).

**v1.1:** Planner and reviewer import `_DESC_SHORT` variants (brief capability summaries).

### Why it matters

The planner and reviewer don't invoke workers directly — they only need to know what workers can do, not how to invoke them. Shorter descriptions save tokens in their context.

### Verdict: Improvement (no trade-offs)

### Evidence

Follows from the context filtering principle (change #5). Less irrelevant detail in the prompt means better performance on the actual task. Supported by the NoLiMa and "Complexity Trap" findings cited above.

---

## 21. Agent Trace Infrastructure (Shared Workspace)

### What changed

**v1.0:** No agent traces. The orchestrator manually relays worker outcomes to the reviewer and planner via instruction text. The reviewer and planner have no independent access to worker execution details.

**v1.1:** Full agent execution traces are saved to `/workspace/.agent_traces/` after every invocation of any agent (workers, reviewer, planner). Each agent has one trace file (e.g., `madgraph_operator.md`, `reviewer.md`) with invocations appended as `## [N]` sections. Each section contains:
- `### Instruction`: The HumanMessage that started the invocation.
- `### Response`: The final AIMessage text.
- `### Tool Log`: Interleaved tool calls (args truncated to 500 chars) and masked tool results (truncated to 1000 chars).

Trace paths appear in `[Trace: /workspace/.agent_traces/agent.md | Invocation N]` footers on every ToolMessage visible to the orchestrator. The orchestrator prompt instructs it to reference trace paths when invoking the reviewer or planner. The reviewer and planner prompts describe the trace directory and provide guidance on when to inspect traces (thorough review: inspect traces; quick check: skip unless something looks wrong).

### Why it matters

- **Eliminates relay bottleneck.** In v1.0, the orchestrator must summarize and relay every worker outcome to the reviewer/planner — inevitably losing detail and consuming tokens. With traces on disk, the orchestrator summarizes key outcomes and points to the trace; the reviewer/planner reads details independently.
- **Independent verification.** The reviewer can now inspect how a worker actually worked (tool calls, intermediate results, reasoning) rather than relying solely on the orchestrator's summary.
- **Token savings.** The orchestrator no longer needs to copy-paste large worker outputs into reviewer/planner instructions. A trace path reference costs ~20 tokens vs. hundreds or thousands for relayed content.
- **Auditability.** Every agent invocation is recorded with full context, enabling post-hoc analysis of agent behavior.

### Architecture

This implements a **hybrid hierarchical + blackboard** architecture:
- **Hierarchical**: The orchestrator controls delegation (who does what, when).
- **Blackboard**: Agents share information through traces on disk (shared workspace), reducing the need for the orchestrator to relay every detail.

### Verdict: Significant improvement

### Evidence

- **Hong et al. (ICLR 2024), "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework"**: Introduces a "shared message pool" where agents publish structured outputs that other agents can selectively consume. This eliminates cascading errors from information loss during relay. MetaGPT achieved 100% task completion rate on HumanEval vs 85.7% for ChatDev, attributed partly to the shared message pool reducing information distortion. [arXiv:2308.00352](https://arxiv.org/abs/2308.00352)
- **Han et al. (2025), "LbMAS: Language-based Multi-Agent Systems"**: Implements a centralized blackboard for inter-agent communication. Achieved **3.5x token savings** compared to direct agent-to-agent communication by avoiding redundant information relay. The blackboard pattern decouples information production from consumption, allowing agents to read what they need. [IET Digital Library](https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/cdt2.12128)
- **Yuen, Yau, Chan (2025), "Intrinsic Memory Agents"**: Agents store execution artifacts and intermediate results to persistent storage, enabling future agents to access them without orchestrator relay. Demonstrated improved task completion and reduced token consumption on multi-step reasoning tasks. [arXiv:2504.06898](https://arxiv.org/abs/2504.06898)
- **OPTIMA (ACL 2025)**: Shows that communication topology significantly affects multi-agent performance. Reducing unnecessary message passing while maintaining information access yields both efficiency and accuracy gains. [arXiv:2410.08115](https://arxiv.org/abs/2410.08115)
- Strong consensus across multiple independent papers: shared workspace / blackboard patterns reduce token costs and information loss compared to relay-based communication.

---

## 22. Universal Bash Access for Workers

### What changed

**v1.0:** Only `madgraph_operator`, `script_operator`, `user_cli_operator`, and `plotter` had `bash_tool`. The `researcher`, `physics_expert`, and `pdf_reader` used specialized tools: `save_answer` (write text to file), `list_pdfs` (glob for PDFs).

**v1.1:** All workers have `bash_tool`. The `save_answer` and `list_pdfs` tools are removed from worker tool lists (the tool definitions remain in `tools.py` for backwards compatibility). Workers that previously lacked bash (`researcher`, `physics_expert`, `pdf_reader`) can now:
- Save answers to files via bash (replaces `save_answer`).
- Search the filesystem via bash (replaces `list_pdfs`).
- Read agent traces in `/workspace/.agent_traces/` (enables the shared workspace from change #21).

### Why it matters

- **Enables the trace infrastructure.** Without bash, `researcher`, `physics_expert`, and `pdf_reader` cannot read agent traces. With bash, ALL agents can read traces from the shared workspace — no orchestrator differentiation needed.
- **Eliminates redundant tools.** `save_answer` is a subset of bash (`echo "..." > file`). `list_pdfs` is a subset of bash (`find /pdf_files -name "*.pdf"`). Removing them simplifies the tool surface without losing functionality.
- **Uniform architecture.** The orchestrator no longer needs to distinguish between "bash workers" and "non-bash workers" in its instruction style. All workers have the same basic capabilities.

### Verdict: Improvement

### Evidence

- **OpenAI, "A Practical Guide to Building Agents" (2025)**: Recommends giving agents a small set of powerful, composable tools rather than many specialized ones. "Fewer, well-designed tools reduce confusion and improve tool selection accuracy." [OpenAI Guide](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- **Anthropic, "Tool Use Best Practices"**: Minimize the number of tools, use clear naming, and prefer general-purpose tools when they cover the use case. Redundant tools increase the chance of the LLM selecting the wrong one. [Anthropic Docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview)
- **Evidence gap:** No paper directly benchmarks "fewer general tools vs many specialized tools" in multi-agent systems. The improvement is supported by practitioner consensus and the enabling effect on the trace infrastructure.

---

## 23. Targeted Worker Plan Context (`step_id`)

### What changed

**v1.0:** Workers receive no plan context.

**v1.1 (before):** `_build_worker_context()` prepends a `<plan_context>` block to the worker instruction, but it includes ALL in-progress steps and the union of all their dependencies. When multiple workers are dispatched in parallel (e.g., steps 3 and 5), every worker sees both steps in `<current_step>` — even though each worker is only responsible for one.

**v1.1 (after):** `InvokeWorker` exposes an optional `step_id: int` field. When set, `_build_worker_context(plan, message, step_id=N)` filters to only step N and its completed dependencies. When omitted, the old behavior (all in-progress steps) is preserved for backward compatibility.

### Why it matters

- During parallel dispatch, each worker receives clean, targeted context about exactly the step it's executing — no noise from sibling steps.
- Reduces token waste: for a plan with 3 parallel steps, each worker sees 1 step instead of 3 in its `<plan_context>`.
- The orchestrator's instruction text remains the authoritative task assignment; `step_id` ensures the automatic plan context is equally precise.

### Verdict: Improvement (minor, but clean)

### Evidence

- This is a direct refinement of change #6 (worker context enrichment). The same evidence applies: targeted context reduces noise, aligned with the "Complexity Trap" finding that narrower context improves performance.
- **Evidence gap:** No paper directly benchmarks "targeted vs broadcast plan context" for parallel worker dispatch.

---

## 24. Research Prompt Overhaul + Plan Phase Tool Removal

### What changed

**v1.1 (before):** The research phase had minimal prompts — a 4-line system prompt and a 10-line developer prompt with no environment description, no worker context, no domain knowledge. The plan phase had `web_search_tool` bound, even though the plan node produces structured output and has no tool-calling loop.

**v1.1 (after):** Two changes:
1. **Research prompt overhaul.** `RESEARCH_SYSTEM_PROMPT` and `RESEARCH_DEVELOPER_PROMPT` are now full-quality prompts matching the standard of the planner and reviewer. The research developer prompt includes: `<environment>` (with `environment_description`, `environment_guidance`, `workers`, `context`, `allowed_assumptions`), `<tools>`, and `<instructions>` (with `research_guidance` and `workflow`). The research LLM now knows the directory layout, worker capabilities, domain context (particle physics, MadGraph), trace access patterns, and how to structure its findings.
2. **Plan phase tool removal.** `web_search_tool` removed from the plan node. `get_planner_node()` no longer accepts a `tools` parameter. `with_structured_output()` is called without `tools`, producing pure structured output. The planner developer prompt's `<tools>` section now states that the plan phase has no tool access.

### Why it matters

- The research LLM was operating without environment context — it didn't know which directories exist, what workers are available, or what domain the user works in. Without this, research was unfocused and missed high-value inspections.
- Removing `web_search` from the plan phase enforces clean separation: research gathers information, planning synthesizes it. Previously, the LLM could theoretically call `web_search` during structured output generation, producing unexpected behavior.

### Verdict: Improvement

### Evidence

- **Prompt engineering best practices (OpenAI, Anthropic):** Providing relevant context in system/developer prompts improves task performance. The research phase was the only agent in the system without environment context — an inconsistency now corrected.
- The "Complexity Trap" (NeurIPS 2025) finding applies inversely: while excessive context hurts, missing context also hurts. The research LLM needs enough context to know what to investigate.
- **Evidence gap:** No controlled study comparing minimal vs detailed prompts for research phases in multi-agent planning systems.

---

## Summary Table

| # | Change | Verdict | Evidence Strength |
|---|--------|---------|-------------------|
| 1 | Structured output → tool calling | Improvement | Moderate (StructEval, industry practice) |
| 2 | Parallel agent dispatch | Improvement | Moderate (LangGraph docs, latency principle) |
| 3 | LLM plan_updater → inline deterministic | Strictly better | Strong (multiple sources on deterministic vs LLM) |
| 4 | Dual message streams (private orchestrator context) | Significant improvement | Strong (OpenAI +3% SWE-bench, Anthropic docs) |
| 5 | Context filtering for planner/reviewer | Improvement | Strong (Complexity Trap, NoLiMa) |
| 6 | Worker context enrichment (plan injection + masking) | Strictly better | Strong (Lost in the Middle, Complexity Trap) |
| 7 | `future_note` → scratchpad tools | Strictly better | Strong (MemGPT, A-MEM, Letta) |
| 8 | Planner research phase | Improvement | Weak (no direct study; self-evident) |
| 9 | Summarizer improvements | Improvement | Moderate (Complexity Trap, LangChain) |
| 10 | Reasoning token reinsertion | Significant improvement | Strong (OpenAI cookbook, Anthropic docs) |
| 11 | Review intensity signaling | Improvement | Moderate (MetaGPT 72% overhead) |
| 12 | Worker `clear_history` flag | Improvement | Moderate (context pollution literature) |
| 13 | Output truncation + artifact saving (head+tail) | Improvement | Strong (Lost in the Middle) |
| 14 | Self-loop guard | Necessary | Self-evident |
| 15 | New physics_expert agent | Improvement | Domain-specific |
| 16 | Per-invocation model routing | Marginal | Weak (no benchmarks) |
| 17 | `require_madgraph_evidence` removal | Simplification | Self-evident (principle of least authority) |
| 18 | Compact plan summaries | Improvement | Self-evident |
| 19 | `adaptive` reasoning flag | Likely improvement | Moderate (Anthropic docs) |
| 20 | Abbreviated worker descriptions | Improvement | Supported by #5 evidence |
| 21 | Agent trace infrastructure (shared workspace) | Significant improvement | Strong (MetaGPT, LbMAS 3.5x savings, IMA, OPTIMA) |
| 22 | Universal bash access for workers | Improvement | Moderate (OpenAI/Anthropic tool design guides) |
| 23 | Targeted worker plan context (`step_id`) | Improvement | Supported by #6 evidence (Complexity Trap) |
| 24 | Research prompt overhaul + plan phase tool removal | Improvement | Moderate (prompt engineering best practices) |

### Overall Assessment

All 24 changes are at least marginally positive. The strongest evidence-backed improvements are:
- **#3 (inline plan updates)**: Eliminates unnecessary LLM calls — supported by multiple sources on deterministic vs LLM execution.
- **#4 (dual message streams) + #10 (reasoning reinsertion)**: Reasoning token persistence yields measurable improvements — documented by both OpenAI (+3% SWE-bench) and Anthropic.
- **#5 (context filtering) + #6 (worker masking) + #13 (output truncation)**: Context management cluster — strongly supported by the "Lost in the Middle" paper, the "Complexity Trap" paper, and the NoLiMa benchmark.
- **#7 (scratchpad)**: Explicit persistent memory outperforms implicit in-context memory — supported by MemGPT, A-MEM, and Letta.
- **#21 (agent trace infrastructure)**: Shared workspace / blackboard architecture — supported by MetaGPT (shared message pool, 100% vs 85.7% task completion), LbMAS (3.5x token savings), and Intrinsic Memory Agents. This is the strongest new addition, addressing a fundamental information flow bottleneck.

The only change flagged as questionable is **#16 (model routing)**, which lacks benchmarks and adds orchestrator complexity. Its default-off status is appropriate.

### Evidence Gaps

For full transparency, these topics lack strong peer-reviewed evidence:
1. **Tool calling vs structured output** (#1): The StructEval accuracy drop applies to JSON output generally, not tool-calling specifically.
2. **Retry escalation** (#12): No paper benchmarks "increase reasoning effort on failure retries" as a standalone strategy.
3. **Adaptive review intensity** (#11): No paper directly compares fixed vs adaptive review intensity. The MetaGPT 72% overhead is indirect evidence.
4. **Planner research phase** (#8): No controlled study comparing single-phase vs two-phase planning in LLM agents.
5. **Model routing** (#16): No benchmarks for per-invocation model routing in multi-agent systems.
6. **Universal bash vs specialized tools** (#22): No paper directly benchmarks "fewer general tools vs many specialized tools" in multi-agent systems.
