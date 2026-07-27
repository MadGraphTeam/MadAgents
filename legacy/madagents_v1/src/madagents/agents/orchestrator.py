from __future__ import annotations

import json
import uuid
import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Literal, Callable

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage

from madagents.agents.workers.user_cli_operator import USER_CLI_OPERATOR_DESC
from madagents.agents.workers.madgraph_operator import MADGRAPH_OPERATOR_DESC
from madagents.agents.workers.script_operator import SCRIPT_OPERATOR_DESC
from madagents.agents.workers.pdf_reader import PDF_READER_DESC
from madagents.agents.workers.researcher import RESEARCHER_DESC
from madagents.agents.workers.plotter import PLOTTER_DESC
from madagents.agents.workers.physics_expert import PHYSICS_EXPERT_DESC
from madagents.agents.planner import PLANNER_DESC
from madagents.agents.reviewer import (
    PLAN_REVIEWER_DESC,
    VERIFICATION_REVIEWER_DESC,
    PRESENTATION_REVIEWER_DESC,
)
from madagents.agents.prompts_common import STYLE_BLOCK
from madagents.agents.planner import Plan, PlanMetaData, PlanUpdate, PlanStepUpdate, update_plan
from madagents.agents.summarizer import Summarizer
from madagents.llm import LLMRuntime, get_default_runtime
from madagents.config import ANTHROPIC_MODEL_TIERS, OPENAI_MODEL_TIERS, WORKER_AGENTS
from madagents.utils import (
    response_to_text,
    extract_thinking,
    extract_token_kwargs,
    make_summary_fingerprint,
)

if TYPE_CHECKING:
    from madagents.graph import MadAgentsState

logger = logging.getLogger(__name__)


#########################################################################
## Tool schemas (Pydantic, schema-only, not executed) ###################
#########################################################################

WORKER_NAMES = Literal[
    "script_operator",
    "madgraph_operator",
    "user_cli_operator",
    "researcher",
    "pdf_reader",
    "plotter",
    "physics_expert",
]


class InvokePlanner(BaseModel):
    """Delegate to the planner agent to create or revise a multi-step plan."""
    instruction: str = Field(
        ...,
        description="The objective to plan for. Do not specify plan structure, workers, or implementation details. For revisions: state what to change.",
    )
    instance_id: Optional[int] = Field(
        default=None,
        description=(
            "Instance ID for planner resumption. Omit to create a new instance "
            "(auto-assigned). Specify an existing ID to resume that instance "
            "with its prior research context."
        ),
    )


REVIEWER_NAMES_LITERAL = Literal["plan_reviewer", "verification_reviewer", "presentation_reviewer"]


class InvokeReviewer(BaseModel):
    """Delegate to a specialized reviewer agent."""
    reviewer_name: REVIEWER_NAMES_LITERAL = Field(
        ...,
        description="Name of the reviewer to invoke.",
    )
    instruction: str = Field(
        ...,
        description="Instruction for the reviewer describing what to review.",
    )
    instance_id: Optional[int] = Field(
        default=None,
        description=(
            "Instance ID for multi-instance reviewers. Omit to create a new instance "
            "(auto-assigned). Specify an existing ID to resume that instance "
            "with its prior context."
        ),
    )


class InvokeWorker(BaseModel):
    """Delegate to a specialized worker agent."""
    worker_name: WORKER_NAMES = Field(
        ...,
        description="Name of the worker to invoke.",
    )
    instruction: str = Field(
        ...,
        description=(
            "Full instruction for the worker. For new instances: workers have no prior "
            "context — include all relevant details (objective, constraints, deliverables). "
            "For resumed instances (explicit instance_id): the worker retains its execution "
            "trace, so a follow-up instruction suffices."
        ),
    )
    reasoning_effort: Literal["low", "medium", "high"] = Field(
        "medium",
        description=(
            "Reasoning effort for the worker. "
            "low: straightforward task. "
            "medium: default. "
            "high: complex/ambiguous tasks or after previous failures."
        ),
    )
    step_id: Optional[int] = Field(
        default=None,
        description=(
            "Plan step ID this worker is executing. When set, the worker receives "
            "plan context (this step and its completed dependencies). "
            "When null, no plan context is injected."
        ),
    )
    instance_id: Optional[int] = Field(
        default=None,
        description=(
            "Instance ID for multi-instance workers. Omit to create a new instance "
            "(auto-assigned). Specify an existing ID to resume that instance "
            "with its prior execution trace."
        ),
    )


class StepUpdateItem(BaseModel):
    """A single plan step status update."""
    id: int = Field(..., description="ID of the plan step to update.")
    status: Literal["pending", "in_progress", "done", "failed", "skipped"] = Field(
        ..., description="New status for the step."
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Outcome description (required for done/failed/skipped).",
    )


class UpdatePlan(BaseModel):
    """Programmatically update plan step statuses. No LLM is involved. Always batch ALL step updates into a single call per turn."""
    step_updates: List[StepUpdateItem] = Field(
        ...,
        description="List of step updates to apply.",
    )


class UpdateScratchpad(BaseModel):
    """Update the orchestrator's persistent scratchpad notes."""
    content: str = Field(
        ..., description="New scratchpad content. Replaces previous content entirely.",
    )


class ReadPlan(BaseModel):
    """Read the full current execution plan with step statuses."""
    pass


class ReadScratchpad(BaseModel):
    """Read the current scratchpad notes."""
    pass


DELEGATION_TOOLS = [InvokePlanner, InvokeReviewer, InvokeWorker, UpdatePlan, UpdateScratchpad, ReadPlan, ReadScratchpad]


#########################################################################
## Tool building ########################################################
#########################################################################


def _make_invoke_worker_with_model(
    available_models: list[str],
    default_model: str,
) -> type[BaseModel]:
    """Create an InvokeWorker variant that includes a ``model`` field.

    The model field lets the orchestrator dynamically select which LLM a
    worker should use on a per-call basis.
    """
    all_tiers = {**ANTHROPIC_MODEL_TIERS, **OPENAI_MODEL_TIERS}
    model_lines = []
    for model in available_models:
        tier, description = all_tiers.get(model, ("unknown", ""))
        marker = " (default)" if model == default_model else ""
        model_lines.append(f"{model} [{tier}]{marker}: {description}")
    models_catalog = "; ".join(model_lines)

    class _InvokeWorker(BaseModel):
        """Delegate to a specialized worker agent."""

        worker_name: WORKER_NAMES = Field(
            ...,
            description="Name of the worker to invoke.",
        )
        instruction: str = Field(
            ...,
            description=(
                "Full instruction for the worker. For new instances: workers have no prior "
                "context — include all relevant details (objective, constraints, deliverables). "
                "For resumed instances (explicit instance_id): the worker retains its execution "
                "trace, so a follow-up instruction suffices."
            ),
        )
        reasoning_effort: Literal["low", "medium", "high"] = Field(
            "medium",
            description=(
                "Reasoning effort for the worker. "
                "low: straightforward task. "
                "medium: default. "
                "high: complex/ambiguous tasks or after previous failures."
            ),
        )
        step_id: Optional[int] = Field(
            default=None,
            description=(
                "Plan step ID this worker is executing. When set, the worker receives "
                "plan context (this step and its completed dependencies). "
                "When null, no plan context is injected."
            ),
        )
        model: Optional[str] = Field(
            default=None,
            description=(
                f"Override the worker's default LLM model. "
                f"Default (when not specified or null): {default_model}. "
                f"Available models: {models_catalog}."
            ),
        )
        instance_id: Optional[int] = Field(
            default=None,
            description=(
                "Instance ID for multi-instance workers. Omit to create a new instance "
                "(auto-assigned). Specify an existing ID to resume that instance "
                "with its prior execution trace."
            ),
        )

    # Use the canonical name so the tool schema matches the expected tool name.
    _InvokeWorker.__name__ = "InvokeWorker"
    _InvokeWorker.__qualname__ = "InvokeWorker"
    return _InvokeWorker


def build_delegation_tools(
    enable_model_routing: bool,
    available_models: list[str] | None = None,
    default_model: str | None = None,
) -> list:
    """Build the orchestrator's tool list, optionally including model routing."""
    if enable_model_routing and available_models and default_model:
        invoke_worker_cls = _make_invoke_worker_with_model(
            available_models, default_model,
        )
        return [
            InvokePlanner, InvokeReviewer, invoke_worker_cls,
            UpdatePlan, UpdateScratchpad, ReadPlan, ReadScratchpad,
        ]
    return DELEGATION_TOOLS


#########################################################################
## Constants ############################################################
#########################################################################

MAX_CONSECUTIVE_SELF_LOOPS = 15


#########################################################################
## Prompt ###############################################################
#########################################################################

ORCHESTRATOR_SYSTEM_PROMPT = f"""<role>
You are the orchestrator of MadAgents, a system of specialized agents. You manage the workflow, delegate work to agents, and ensure quality via reviewers; you do not solve tasks yourself.
</role>

<environment>
- You run in a container with a persistent filesystem. Three key directories:
  - `/output` — user's directory for final deliverables. Persistent, shared across sessions. No destructive actions without user request.
  - `/workspace` — your scratch space. Recreated empty each session. Fully managed by you and the planner.
  - `/opt` — persistent installations, shared across sessions. No destructive actions without user request. Default Python env: `/opt/envs/MAD`; create per-project envs under `/opt/envs/<project>` when needed.
- Avoid writing outside these three directories.
- The user works in `/output` via a CLI session shared with user_cli_operator. CLI inspection is always allowed; executing commands requires explicit user permission.
- Default assumptions: the user wants MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin) for event generation/simulations, and the latest software versions.
</environment>

<orchestration>
<tools>
- Persist important findings, decisions, and key results in the scratchpad. Keep under ~500 words.
- Batch step status changes into a single UpdatePlan call. Only include steps that change; blocked → pending resolves automatically.
- Prefer parallel tool calls when possible (e.g., dispatching independent workers, combining UpdatePlan with agent invocations).
__MODEL_ROUTING_PLACEHOLDER__</tools>

<recipients>
All agents see your instruction. Additional context varies:
- Planner: also sees recent user↔orchestrator exchanges (+ summary of older ones), the current plan, and its own instance-scoped research history. Does not see worker responses — relay key outcomes in your instruction.
- Reviewers: also see recent user↔orchestrator exchanges, the current plan, and their own instance-scoped conversation history. They do not see worker responses — relay key outcomes in your instruction.
- Workers: also see their own instance-scoped execution trace. Each instance maintains separate conversation history. When `step_id` is set, they receive a `<plan_context>` block with that step's details and completed dependencies.
- All agents can read traces at `/workspace/.agent_traces/{{agent_name}}/{{instance_id}}.md` via bash. Reference trace paths from `[Trace: ...]` footers when relevant.
- Agent names in parentheses are the display names visible to the user.

# user
- You may assume the user is a particle physicist.
- Keep your messages concise while including all relevant information. The user may only read your message, so don't rely on other agents' messages.

# {PLANNER_DESC}

# reviewers (select by reviewer_name in InvokeReviewer)
- Do NOT use any reviewer to solve tasks or execute plan steps — only to assess outputs.
- When calling: state what to review, the plan step if applicable, and which agents were involved. Reference trace paths when relevant. You may point out specific concerns if you have any. Do not instruct how to review.
- Reviewers assess quality (pass/fail) — do not ask them to propose improvements or alternatives.

## {PLAN_REVIEWER_DESC}

## {VERIFICATION_REVIEWER_DESC}

## {PRESENTATION_REVIEWER_DESC}

# specialized workers
- All workers share a base toolset: bash, apply_patch, read_pdf, read_image, web_search. Additional tools are noted per worker.
- State the objective and key constraints. Workers are expert agents that determine how to achieve it.
- For research-type workers (researcher, pdf_reader, physics_expert): if instructing them to save output to a file, specify the absolute path.

## {SCRIPT_OPERATOR_DESC}

## {MADGRAPH_OPERATOR_DESC}

## {PHYSICS_EXPERT_DESC}

## {PLOTTER_DESC}

## {RESEARCHER_DESC}

## {PDF_READER_DESC}

## {USER_CLI_OPERATOR_DESC}
</recipients>

<invocation_guidance>
When invoking workers:
- Start with a "Background:" section (2-8 sentences) with big-picture context.
- Tell agents where to write their outputs. Prefer descriptive subdirectories over writing to `/workspace/` or `/output/` root. Parallel agents may conflict on shared filesystem paths — manage this proactively (e.g., assign separate output directories).
- Focus on what to do, not how — workers are expert agents that determine implementation details.
- Be specific only where ambiguity would cause wrong results (e.g., output paths, parameter values, physics settings).

When invoking the planner or reviewers, follow the guidance in their descriptions above.

Reasoning effort:
- Planner: `high` (new plan), `medium` (unspecified revision), `low` (specified changes).
- Reviewers: `high`.
- Workers: `medium` by default. `low` for trivial tasks. `high` for complex/ambiguous tasks, retries, or when previous attempts failed. Always `high` for plotter (new plots) and physics_expert (complex derivations).

Parallel execution:
- You may dispatch multiple agents in parallel, including multiple instances of the same type. Each instance gets an auto-assigned instance_id and maintains its own conversation history.
- Use parallel dispatch when tasks are genuinely independent (e.g., MadGraph runs with different configurations, parallel research queries, independent analysis scripts).
- Dispatching multiple reviewer instances on specific aspects improves review depth, but may miss cross-cutting consistency issues.

Instance resumption:
- To follow up on a specific instance's context, set instance_id explicitly (e.g., asking a worker to retry with adjusted parameters, asking a reviewer to check if previously flagged issues were fixed, or asking the planner to revise based on its prior research).
- Prefer a new instance when most of the previous context is not needed — this reduces token cost.
</invocation_guidance>
</orchestration>

<instructions>
Your objective: fulfill the user's request — completely, but nothing beyond what was asked. Do not add deliverables or features the user did not request.

The user may override any part of this workflow — in particular reviewing frequency, quality/expense trade-offs, and iteration limits. Follow user instructions when they conflict with these defaults.

On each turn:
1. **Assess** the current state — what the user wants, what has been done, whether any agent execution was interrupted, and what is still missing.
2. **Act** — invoke tools, message the user, or both.
Keep the user informed throughout (see <user_updates>).

<workflow>
- If a `<previous_conversation_summary>` is present and the plan / scratchpad content is not visible in recent messages, call ReadPlan / ReadScratchpad before making workflow decisions.

General principles:
- Delegate ALL substantive work to agents. Only respond directly for conversational purposes (e.g., status updates, summaries, clarifications, workflow decisions). Delegate all domain questions (e.g., HEP software, physics) to the appropriate specialist — never answer them from your own knowledge.
- Review substantial agent work before building on it or presenting it to the user (see <reviewing>). Everything presented to the user must be correct and pass reviewer checks.
- If a decision is needed, act autonomously if it can be easily changed or extended later — but report the choice to the user. Otherwise, ask the user.
<user_updates>
Keep the user informed throughout the workflow.
- Start with a brief outline of what you are going to do.
- Send updates as text alongside your tool calls, not only via tool calls.
- Send a short update (1-2 sentences) after completing a plan step or when there are meaningful changes.
- If you expect a longer stretch without updates, post a brief note explaining why.
</user_updates>

Task sizing:
- Simple tasks (1-2 steps): execute immediately with the appropriate worker.
- Complex tasks (>2 steps): invoke planner first, then review the plan.

Plan execution:
- Set steps to `in_progress` via UpdatePlan before dispatching workers. You may run independent steps in parallel.
- All plan steps MUST be executed by workers — never by you or the reviewer, even for "verification" or "review" steps.
- After a step succeeds, mark it `done`.
- Failed steps: retry 2-3 times (escalate reasoning effort to `high`), then mark `failed` and report the error to the user with details, warnings, and hypotheses.
- Steps can be skipped if irrelevant. Plans can be revised via planner (re-review after revision).
- Before presenting final results: ensure no step is `in_progress` and all steps are `done`/`failed`/`skipped`/`blocked`.

Filesystem:
- Keep `/workspace/` and `/output/` organized — move scattered files into dedicated directories, and clean up intermediate files when they are no longer needed.
</workflow>

<reviewing>
Invoke reviewers:
1. plan_reviewer: After every new or revised plan.
2. verification_reviewer: Review agent work to ensure correctness.
   - Skip for trivial, mechanical work (e.g., finding files, simple file operations).
   - Related outputs may be grouped into a single review.
   - Consider dispatching reviews during execution to catch errors early.
   - Dispatch reviews in parallel with ongoing work if downstream work can be easily adjusted.
   - Quick check for intermediate results; thorough for:
     - Final or user-facing results (e.g., physics explanations, HEP software claims presented to the user)
     - Work where errors would propagate downstream and be costly to undo (e.g., findings or conclusions that future work builds on)
     - Surprising or unintuitive results
3. presentation_reviewer: For user-facing deliverables (e.g., plots, documents, reports).

Worker self-validation does not replace independent review by reviewers.

You may invoke multiple reviewers in parallel. A single deliverable may need both verification and presentation review.

If a reviewer flags issues, revise and retry (typically up to 2 iterations; adapt to user expectations).

Handling reviewer feedback:
- Consider whether flagged issues matter for the user's goal — skip or override those that don't.
- Instead of fixing a failing deliverable, consider whether the user actually asked for it. If not, consider skipping the plan step, asking the planner to reduce its scope, stripping the problematic parts, or noting the limitation in the step outcome.
- Fix remaining FAILs. You have override authority if you disagree (state justification).
- Choose the simplest revision path — re-invoke existing scripts or patch a single artifact rather than rebuilding entire steps.
</reviewing>

<worker_routing>
- Default worker: script_operator (bash, Python, file manipulation, general software, quick web lookups).
- MadGraph & related tools: ALWAYS dispatch madgraph_operator for anything involving MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin) or HEP event generation/simulation. Use researcher as fallback only.
- Plots: ALWAYS use plotter for user-facing plots. Other agents may create intermediate/diagnostic plots directly.
- User's CLI: use user_cli_operator only when the task requires the user's interactive session. Inspect the CLI whenever the request is underspecified or the user refers to terminal output. Default to inspecting rather than asking the user to paste content.
- Physics reasoning: ALWAYS use physics_expert for physics explanations, derivations, and validation. Pair with other workers for implementation.
- Research: reserve researcher for deep multi-source research. For quick lookups, use script_operator.
- PDFs: use pdf_reader for extracting information from long or complex PDFs — it returns only the relevant parts, keeping downstream context clean. Workers may read short PDFs or look up specific details directly.
- Prefer multiple specialists over one generalist when quality improves (e.g., script_operator for analysis + plotter for visualization).
</worker_routing>
</instructions>

<style>
{STYLE_BLOCK}
- Be educational when reasonable: include enough explanation for the user to repeat the approach, and instruct workers to present solutions in an educational way.
- When communicating results to the user, prefer equations and formulas over descriptive text.
- When asking for details/choices/..., include 1-2 proposals if reasonable.
</style>"""


#########################################################################
## Helpers ##############################################################
#########################################################################


def get_last_tool_call_id(state: MadAgentsState) -> str | None:
    """Extract tool_call_id from the orchestrator's last AIMessage."""
    orchestrator_messages = state.get("orchestrator_messages", [])
    for msg in reversed(orchestrator_messages):
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            if tool_calls:
                last_tc = tool_calls[-1]
                if isinstance(last_tc, dict):
                    return last_tc.get("id")
            break
    return None


def get_parallel_ready_steps(plan: list | dict | None) -> list[int]:
    """Return IDs of pending steps whose dependencies are all resolved."""
    if not plan:
        return []
    steps = plan.get("steps", []) if isinstance(plan, dict) else plan
    if not isinstance(steps, list):
        return []
    done_ids = {s["id"] for s in steps if s.get("status") in ("done", "skipped")}
    return [s["id"] for s in steps
            if s.get("status") == "pending"
            and all(d in done_ids for d in s.get("depends_on", []))]


def compact_plan_summary(plan: dict | list | None) -> str:
    """Build a one-line plan status for ToolMessage footers.

    Actionable statuses (in_progress, pending, blocked, failed) include step
    titles so the orchestrator knows *what* each step is without calling
    ReadPlan.  Completed statuses (done, skipped) show bare IDs only.
    """
    if not plan:
        return ""
    steps = plan.get("steps", []) if isinstance(plan, dict) else plan
    if not steps:
        return ""
    # Group steps by status
    by_status: dict[str, list[dict]] = {}
    for s in steps:
        by_status.setdefault(s.get("status", "pending"), []).append(s)
    # Statuses where titles add value (orchestrator needs to reason about these)
    _actionable = {"in_progress", "pending", "blocked", "failed"}
    parts = [f"Plan: {len(steps)} steps"]
    for status in ("done", "skipped", "in_progress", "pending", "blocked", "failed"):
        group = by_status.get(status, [])
        if not group:
            continue
        if status in _actionable:
            items = ", ".join(f"{s['id']}: {s.get('title', '')}" for s in group)
            parts.append(f"{status}: [{items}]")
        else:
            parts.append(f"{status}: {[s['id'] for s in group]}")
    parallel = get_parallel_ready_steps(plan)
    if len(parallel) > 1:
        parts.append(f"parallel-ready: {parallel}")
    return " | ".join(parts)


def _format_plan_update_result(
    plan: dict | None,
    updated_step_ids: list[int],
) -> str:
    """Format a compact UpdatePlan result showing status of all steps and
    full details of updated steps only."""
    if not plan:
        return "No plan exists."
    steps = plan.get("steps", []) if isinstance(plan, dict) else []
    if not steps:
        return "Plan has no steps."

    # Status overview: one line per step (id, title, status)
    overview_lines = []
    for s in steps:
        sid = s.get("id", "?")
        title = s.get("title", "")
        status = s.get("status", "?")
        marker = " *" if sid in updated_step_ids else ""
        overview_lines.append(f"  [{sid}] {title} — {status}{marker}")
    overview = "Plan status (* = updated):\n" + "\n".join(overview_lines)

    # Full details for updated steps
    updated_steps = [s for s in steps if s.get("id") in updated_step_ids]
    if updated_steps:
        detail = "\n\nUpdated step details:\n" + json.dumps(updated_steps, indent=2)
    else:
        detail = ""

    return overview + detail


def build_worker_context(plan: dict | None, message: str, step_id: int | None = None) -> str:
    """Prepend plan step context to a worker instruction message.

    Only inserts context when *step_id* is provided — showing that step
    and its completed dependencies.  Without a step_id, returns *message*
    unchanged.
    """
    if step_id is None or not plan or not isinstance(plan, dict):
        return message
    steps = plan.get("steps", [])

    target = [s for s in steps if s["id"] == step_id]
    if not target:
        return message

    dep_ids = set()
    for s in target:
        dep_ids.update(s.get("depends_on", []))
    completed_deps = [
        {"id": s["id"], "title": s.get("title", ""), "outcome": s.get("outcome", "")}
        for s in steps
        if s["id"] in dep_ids and s.get("status") in ("done", "skipped") and s.get("outcome")
    ]
    parts = ["<plan_context>"]
    parts.append("<current_step>\n" + json.dumps(
        [{"id": s["id"], "title": s.get("title", ""), "description": s.get("description", "")}
         for s in target], indent=2) + "\n</current_step>")
    if completed_deps:
        parts.append("<completed_dependencies>\n" + json.dumps(completed_deps, indent=2)
                     + "\n</completed_dependencies>")
    parts.append("</plan_context>")
    return "\n".join(parts) + "\n\n" + message


def _parse_tool_call_to_decision(tool_call: dict) -> dict:
    """Convert a LangChain tool_call dict to an orchestrator dispatch dict."""
    name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if name == "InvokePlanner":
        dispatch = {
            "recipient": "planner",
            "message": args.get("instruction", ""),
            "reasoning_effort": "high",
        }
        instance_id = args.get("instance_id")
        if instance_id is not None:
            dispatch["instance_id"] = instance_id
        return dispatch
    elif name == "InvokeReviewer":
        dispatch = {
            "recipient": args.get("reviewer_name", "verification_reviewer"),
            "message": args.get("instruction", ""),
            "reasoning_effort": "high",
        }
        instance_id = args.get("instance_id")
        if instance_id is not None:
            dispatch["instance_id"] = instance_id
        return dispatch
    elif name == "InvokeWorker":
        dispatch = {
            "recipient": args.get("worker_name", "script_operator"),
            "message": args.get("instruction", ""),
            "reasoning_effort": args.get("reasoning_effort", "medium"),
        }
        model = args.get("model")
        if model:
            dispatch["model"] = model
        step_id = args.get("step_id")
        if step_id is not None:
            dispatch["step_id"] = step_id
        instance_id = args.get("instance_id")
        if instance_id is not None:
            dispatch["instance_id"] = instance_id
        return dispatch
    elif name == "UpdatePlan":
        return {
            "recipient": "plan_updater",
            "message": json.dumps(args, ensure_ascii=False),
            "reasoning_effort": "low",
        }
    elif name == "UpdateScratchpad":
        return {
            "recipient": "scratchpad",
            "message": json.dumps(args, ensure_ascii=False),
            "reasoning_effort": "low",
        }
    elif name == "ReadPlan":
        return {"recipient": "read_plan", "message": "", "reasoning_effort": "low"}
    elif name == "ReadScratchpad":
        return {"recipient": "read_scratchpad", "message": "", "reasoning_effort": "low"}
    else:
        # Unknown tool call — surface it to the user instead of silently dropping
        return {
            "recipient": "user",
            "message": f"Unexpected orchestrator tool call '{name}' with args: {json.dumps(args, ensure_ascii=False, default=str)}",
            "reasoning_effort": "high",
        }


MODEL_ROUTING_GUIDANCE = (
    "- Match model strength to task complexity. Escalate to a stronger model "
    "on retries. Model controls capability; reasoning_effort controls depth "
    "of thinking — use both.\n"
)


def _build_orchestrator_prompt(
    *,
    message_summary: str | None = None,
    enable_model_routing: bool = False,
) -> str:
    """Build the merged orchestrator prompt with optional summary."""
    guidance = MODEL_ROUTING_GUIDANCE if enable_model_routing else ""
    base = ORCHESTRATOR_SYSTEM_PROMPT.replace("__MODEL_ROUTING_PLACEHOLDER__", guidance)
    if message_summary and message_summary.strip():
        base += f"\n\n<previous_conversation_summary>\n{message_summary}\n</previous_conversation_summary>"
    return base


#########################################################################
## Orchestrator node ####################################################
#########################################################################


def get_orchestrator_node(
    orchestrator: Orchestrator,
    summarizer: Summarizer,
    delegation_tools: list | None = None,
    enable_model_routing: bool = False,
    default_worker_model: str | None = None,
) -> Callable[[MadAgentsState], dict]:
    """Create a state-graph node that runs the tool-calling orchestrator."""
    _delegation_tools = delegation_tools or DELEGATION_TOOLS
    _enable_model_routing = enable_model_routing
    _default_worker_model = default_worker_model
    _self_loop_count = 0

    def orchestrator_node(state: MadAgentsState) -> dict:
        nonlocal _self_loop_count
        """Run orchestrator with tool-bound LLM and return graph updates."""
        runtime: LLMRuntime = orchestrator.runtime

        # 1. Read orchestrator_messages (private context)
        orch_msgs = list(state.get("orchestrator_messages", []))

        # 2. Sync: if last message in `messages` is a HumanMessage not yet in
        #    orchestrator_messages, add it. This handles new user input.
        #    Track what we synced so we can include it in the return value.
        display_messages = state.get("messages", [])
        synced_human_msg = None
        if display_messages:
            last_display = display_messages[-1]
            if isinstance(last_display, HumanMessage):
                needs_sync = True
                if orch_msgs:
                    last_orch = orch_msgs[-1]
                    if (
                        isinstance(last_orch, HumanMessage)
                        and last_orch.content == last_display.content
                    ):
                        needs_sync = False
                if needs_sync:
                    orch_msgs.append(last_display)
                    synced_human_msg = last_display

        # 3. Summarize orchestrator_messages if needed
        message_summary = state.get("message_summary", None)
        non_summary_start = state.get("non_summary_start", 0)

        message_summary, non_summary_start = summarizer.summarize(
            message_summary, non_summary_start, orch_msgs
        )
        context_msgs = orch_msgs[non_summary_start:]

        # 4. Build prompt
        plan = state.get("plan", None)
        prompt = _build_orchestrator_prompt(
            message_summary=message_summary,
            enable_model_routing=_enable_model_routing,
        )

        # 5. Invoke orchestrator LLM with tools bound
        # NOTE: bind_tools() via __getattr__ delegates to the inner
        # ChatModel, which drops any prior .bind(thinking=...) kwargs.
        # Re-apply thinking via bind_reasoning() after binding tools.
        llm_with_tools = orchestrator.llm.bind_tools(_delegation_tools)
        llm_with_tools = runtime.bind_reasoning_trace(llm_with_tools)
        llm_with_tools = runtime.bind_reasoning(
            llm_with_tools, reasoning_effort=orchestrator.reasoning_effort,
            adaptive=True,
        )

        messages = [
            *runtime.build_preamble(prompt=prompt),
            *context_msgs,
        ]

        response: AIMessage = runtime.invoke(llm_with_tools, messages)
        response.name = "orchestrator"

        # 6a. Extract thinking content (Anthropic extended thinking)
        thinking_text = extract_thinking(response)

        # 6b. Parse tool calls — build dispatches for ALL tool calls
        tool_calls = getattr(response, "tool_calls", None) or []

        orchestrator_dispatches: list[dict] = []
        if tool_calls:
            for tc in tool_calls:
                dispatch = _parse_tool_call_to_decision(tc)
                dispatch["tool_call_id"] = tc.get("id")
                orchestrator_dispatches.append(dispatch)

        # 6c. Inline plan updates — separate plan_updater dispatches
        plan_update_dispatches = [
            d for d in orchestrator_dispatches if d.get("recipient") == "plan_updater"
        ]
        remaining_dispatches = [
            d for d in orchestrator_dispatches if d.get("recipient") != "plan_updater"
        ]

        inline_orch_msgs: list[BaseMessage] = []
        inline_display_msgs: list[BaseMessage] = []
        updated_plan = state.get("plan", None)
        updated_plan_meta_data = state.get("plan_meta_data", None)

        for pu_dispatch in plan_update_dispatches:
            # Parse step_updates from tool args
            try:
                args = json.loads(pu_dispatch.get("message", ""))
                step_updates_raw = args.get("step_updates", [])
            except (json.JSONDecodeError, AttributeError) as exc:
                logger.warning("Failed to parse plan update args: %s — raw: %s", exc, pu_dispatch.get("message", ""))
                step_updates_raw = []

            step_updates = []
            for su in step_updates_raw:
                step_updates.append(PlanStepUpdate(
                    id=su.get("id", 0),
                    status=su.get("status", "pending"),
                    outcome=su.get("outcome"),
                ))
            plan_update_obj = PlanUpdate(step_updates=step_updates)

            # Apply updates to current plan
            plan_obj = Plan.model_validate(updated_plan if updated_plan else {"steps": []})
            plan_meta_obj = PlanMetaData.model_validate(
                updated_plan_meta_data if updated_plan_meta_data else {"steps": []}
            )
            plan_obj, plan_meta_obj = update_plan(plan_obj, plan_meta_obj, plan_update_obj)
            updated_plan = plan_obj.model_dump(mode="json")
            updated_plan_meta_data = plan_meta_obj.model_dump(mode="json")

            # ToolMessage for orchestrator_messages (one per call for correct tool_call_id matching)
            pu_tool_call_id = pu_dispatch.get("tool_call_id") or "unknown"
            updated_step_ids = [su.id for su in plan_update_obj.step_updates]
            pu_result = _format_plan_update_result(updated_plan, updated_step_ids)
            pu_tool_msg = ToolMessage(
                content=f"Plan updated.\n\n{pu_result}",
                tool_call_id=pu_tool_call_id,
                name="UpdatePlan",
            )
            inline_orch_msgs.append(pu_tool_msg)

        # Emit a single merged display message for all plan updates (avoids noisy
        # consecutive plan_updater cards in the UI)
        if plan_update_dispatches and updated_plan is not None:
            pu_message_id = uuid.uuid4().hex
            pu_display = AIMessage(
                content=f"The updated plan is:\n{json.dumps(updated_plan, indent=2)}",
                name="plan_updater",
                additional_kwargs={
                    "plan": updated_plan,
                    "plan_meta_data": updated_plan_meta_data,
                    "message_id": pu_message_id,
                },
            )
            inline_display_msgs.append(pu_display)

        # Replace dispatches: only non-plan ones remain
        orchestrator_dispatches = remaining_dispatches

        # 6d. Inline scratchpad updates
        scratchpad_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") == "scratchpad"]
        remaining_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") != "scratchpad"]

        updated_scratchpad = state.get("scratchpad")
        for sp_dispatch in scratchpad_dispatches:
            try:
                args = json.loads(sp_dispatch.get("message", ""))
                updated_scratchpad = args.get("content", "")
            except (json.JSONDecodeError, AttributeError) as exc:
                logger.warning("Failed to parse scratchpad update args: %s", exc)
            inline_orch_msgs.append(ToolMessage(
                content=f"Scratchpad updated.\n\nCurrent content:\n{updated_scratchpad}",
                tool_call_id=sp_dispatch.get("tool_call_id") or "unknown",
                name="UpdateScratchpad",
            ))

        orchestrator_dispatches = remaining_dispatches

        # 6f. Inline ReadPlan
        read_plan_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") == "read_plan"]
        remaining_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") != "read_plan"]
        for rp in read_plan_dispatches:
            plan_json = json.dumps(updated_plan, indent=2) if updated_plan else "No plan exists yet."
            extras = []
            parallel = get_parallel_ready_steps(plan)
            if len(parallel) > 1:
                extras.append(f"Parallel-ready steps: {parallel}")
            content = f"Current plan:\n{plan_json}"
            if extras:
                content += "\n\n" + "\n".join(extras)
            inline_orch_msgs.append(ToolMessage(
                content=content,
                tool_call_id=rp.get("tool_call_id") or "unknown",
                name="ReadPlan",
            ))
        orchestrator_dispatches = remaining_dispatches

        # 6g. Inline ReadScratchpad
        read_scratch_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") == "read_scratchpad"]
        remaining_dispatches = [d for d in orchestrator_dispatches if d.get("recipient") != "read_scratchpad"]
        for rs in read_scratch_dispatches:
            sp_content = updated_scratchpad or "Scratchpad is empty."
            inline_orch_msgs.append(ToolMessage(
                content=f"Current scratchpad:\n{sp_content}",
                tool_call_id=rs.get("tool_call_id") or "unknown",
                name="ReadScratchpad",
            ))
        orchestrator_dispatches = remaining_dispatches

        # If ONLY plan+scratchpad+read updates were requested (no external dispatches),
        # signal self-loop back to orchestrator
        if (plan_update_dispatches or scratchpad_dispatches or read_plan_dispatches or read_scratch_dispatches) and not orchestrator_dispatches:
            _self_loop_count += 1
            if _self_loop_count > MAX_CONSECUTIVE_SELF_LOOPS:
                logger.warning(
                    "Orchestrator exceeded %d consecutive self-loops (plan/scratchpad only). "
                    "Breaking out to user.", MAX_CONSECUTIVE_SELF_LOOPS
                )
                orchestrator_dispatches = [{"recipient": "user"}]
            else:
                orchestrator_dispatches = [{"recipient": "orchestrator"}]
        else:
            _self_loop_count = 0

        # 6h. Assign instance IDs for worker/reviewer dispatches
        _non_agent_recipients = {
            "user", "plan_updater", "orchestrator",
            "scratchpad", "read_plan", "read_scratchpad",
        }
        agent_instance_counter = dict(state.get("agent_instance_counter") or {})

        for dispatch in orchestrator_dispatches:
            recipient = dispatch.get("recipient", "")
            if recipient in _non_agent_recipients:
                continue

            if "instance_id" in dispatch:
                # Follow-up on existing instance: ensure counter stays ahead
                current = agent_instance_counter.get(recipient, 0)
                agent_instance_counter[recipient] = max(current, dispatch["instance_id"] + 1)
            else:
                # Auto-assign a fresh instance (always auto-increment)
                current = agent_instance_counter.get(recipient, 0)
                dispatch["instance_id"] = current
                agent_instance_counter[recipient] = current + 1

        # 6i. Fill in default model for worker dispatches when model routing is active
        if _enable_model_routing and _default_worker_model:
            _worker_names = set(WORKER_AGENTS)
            for dispatch in orchestrator_dispatches:
                if dispatch.get("recipient") in _worker_names and "model" not in dispatch:
                    dispatch["model"] = _default_worker_model

        # 6j. Pre-compute conversation summary if a planner or reviewer is dispatched.
        #     This avoids redundant summarizer LLM calls when multiple agents
        #     are dispatched in parallel (each would independently call
        #     _build_conversation_context and produce the same summary).
        _conv_summary_recipients = {
            "planner", "plan_reviewer", "verification_reviewer", "presentation_reviewer",
        }
        _needs_conv_summary = any(
            d.get("recipient") in _conv_summary_recipients
            for d in orchestrator_dispatches
        )
        conv_summary = state.get("conversation_summary", None)
        conv_non_summary_start = state.get("conversation_non_summary_start", 0)
        if _needs_conv_summary:
            all_display = list(state.get("messages", []))
            user_orch_msgs = [
                msg for msg in all_display
                if isinstance(msg, HumanMessage)
                or (isinstance(msg, AIMessage) and getattr(msg, "name", None) == "orchestrator")
            ]
            conv_summary, conv_non_summary_start = summarizer.summarize(
                conv_summary, conv_non_summary_start, user_orch_msgs
            )

        # 7. Build display AIMessage for `messages`
        message_id = uuid.uuid4().hex
        summary_fingerprint = make_summary_fingerprint(message_summary, non_summary_start)
        token_kwargs = extract_token_kwargs(response)

        display_content = response_to_text(response)

        display_additional: dict[str, Any] = {
            "message_id": message_id,
            "summary_fingerprint": summary_fingerprint,
            **token_kwargs,
        }
        if orchestrator_dispatches:
            display_additional["orchestrator_dispatches"] = orchestrator_dispatches
        if thinking_text:
            display_additional["reasoning"] = thinking_text

        display_response = AIMessage(
            content=display_content,
            name="orchestrator",
            additional_kwargs=display_additional,
        )

        # 8. Build full response for exec trace
        full_response = response
        full_additional = dict(full_response.additional_kwargs or {})
        full_additional["message_id"] = message_id
        full_additional["summary_fingerprint"] = summary_fingerprint
        full_additional.update(token_kwargs)
        full_response.additional_kwargs = full_additional

        # 9. Return: raw AIMessage -> orchestrator_messages,
        #    display AIMessage -> messages
        new_orch_msgs = []
        if synced_human_msg is not None:
            new_orch_msgs.append(synced_human_msg)
        new_orch_msgs.append(response)
        # Append inline plan update ToolMessages for orchestrator context
        new_orch_msgs.extend(inline_orch_msgs)

        display_msgs = [display_response]
        # Append inline plan update display messages for UI
        display_msgs.extend(inline_display_msgs)

        result: dict[str, Any] = {
            "messages": display_msgs,
            "orchestrator_messages": new_orch_msgs,
            "orchestrator_full_messages": {message_id: full_response},
            "message_summary": message_summary,
            "non_summary_start": non_summary_start,
            "conversation_summary": conv_summary,
            "conversation_non_summary_start": conv_non_summary_start,
        }
        if updated_plan is not None and plan_update_dispatches:
            result["plan"] = updated_plan
            result["plan_meta_data"] = updated_plan_meta_data
        if scratchpad_dispatches:
            result["scratchpad"] = updated_scratchpad
        # Always set dispatches to avoid stale state from previous orchestrator
        # call persisting (LangGraph merges state, doesn't replace).
        result["orchestrator_dispatches"] = orchestrator_dispatches
        result["current_dispatch"] = (
            orchestrator_dispatches[0] if orchestrator_dispatches else None
        )
        # Always include instance counter so parallel sends merge correctly
        result["agent_instance_counter"] = agent_instance_counter
        return result

    return orchestrator_node


#########################################################################
## Agent ################################################################
#########################################################################

class Orchestrator:
    """Container for the orchestrator LLM and runtime.

    The orchestrator is driven by tool-calling in graph.py via
    get_orchestrator_node() rather than an internal subgraph with
    structured output.
    """
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        runtime: LLMRuntime | None = None,
        **kwargs,
    ):
        """Initialize the orchestrator model."""
        self.reasoning_effort = reasoning_effort
        self.runtime = runtime or get_default_runtime()
        self.llm = self.runtime.create_chat_model(
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            max_tokens=1_000_000,
        )
