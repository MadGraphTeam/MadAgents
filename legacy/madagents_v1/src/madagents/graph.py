import os
import uuid
import json
import datetime
import logging
from typing import TypedDict, List, Dict, Any, Optional, Callable
from typing import Annotated

logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send

from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage

from madagents.agents.planner import (
    Plan, PlanMetaData,
    PlanUpdate, PlanStepUpdate, update_plan,
    Planner, PlannerState,
)
from madagents.agents.orchestrator import (
    Orchestrator,
    get_orchestrator_node,
    build_delegation_tools,
    get_last_tool_call_id,
    get_parallel_ready_steps,
    compact_plan_summary,
    build_worker_context,
)
from madagents.agents.reviewer import Reviewer, ReviewerState, REVIEWER_NAMES
from madagents.agents.workers.base import BaseWorker
from madagents.agents.summarizer import Summarizer, approx_tokens_in_messages

from madagents.llm import LLMRuntime

from madagents.utils import (
    response_to_text,
    extract_non_reasoning_output_tokens,
    extract_output_token_counts,
    extract_thinking,
    extract_token_kwargs,
    make_summary_fingerprint,
    add_messages_with_token_imputation,
)

#########################################################################
## Helper functions #####################################################
#########################################################################


def merge_agent_messages(
    existing: dict[str, dict[str, list[BaseMessage]]],
    incoming: dict[str, dict[str, list[BaseMessage]]],
) -> dict[str, dict[str, list[BaseMessage]]]:
    """Merge per-agent message batches for graph state updates."""
    merged = dict(existing) if isinstance(existing, dict) else {}
    if isinstance(incoming, dict):
        for agent, batches in incoming.items():
            if not isinstance(batches, dict):
                continue
            existing_batches = merged.get(agent)
            if isinstance(existing_batches, dict):
                merged[agent] = {**existing_batches, **batches}
            else:
                merged[agent] = dict(batches)
    return merged


def merge_dict(existing: dict, incoming: dict) -> dict:
    """Merge two flat dicts (used for per-agent summary/offset maps in parallel)."""
    merged = dict(existing) if isinstance(existing, dict) else {}
    if isinstance(incoming, dict) and incoming:
        merged.update(incoming)
    return merged


def merge_max_dict(existing: dict, incoming: dict) -> dict:
    """Merge two dicts by taking the max value for each key."""
    merged = dict(existing) if isinstance(existing, dict) else {}
    if isinstance(incoming, dict):
        for k, v in incoming.items():
            if isinstance(v, (int, float)):
                merged[k] = max(merged.get(k, 0), v)
    return merged


def last_non_none(existing: str | None, incoming: str | None) -> str | None:
    """Reducer for conversation_summary: keep the latest non-None value."""
    return incoming if incoming is not None else existing


def max_int(existing: int, incoming: int) -> int:
    """Reducer for conversation_non_summary_start: take the max (furthest progress)."""
    a = existing if isinstance(existing, int) else 0
    b = incoming if isinstance(incoming, int) else 0
    return max(a, b)


def merge_instance_map(
    existing: dict[str, dict[str, list[str]]],
    incoming: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, list[str]]]:
    """Deep merge: agent_name -> str(instance_id) -> [message_ids]."""
    merged = {}
    for d in (existing, incoming):
        if not isinstance(d, dict):
            continue
        for agent, instances in d.items():
            if not isinstance(instances, dict):
                continue
            if agent not in merged:
                merged[agent] = {}
            for iid, mids in instances.items():
                if not isinstance(mids, list):
                    continue
                existing_mids = merged[agent].get(iid, [])
                seen = set(existing_mids)
                merged[agent][iid] = existing_mids + [m for m in mids if m not in seen]
    return merged


#########################################################################
## State ################################################################
#########################################################################


class MadAgentsState(TypedDict, total=False):
    # Display / UI messages (v1.0 compatible)
    messages: Annotated[list[BaseMessage], add_messages_with_token_imputation]

    # Orchestrator's private context (clean AIMessage+ToolMessage alternation)
    orchestrator_messages: Annotated[list[BaseMessage], add_messages]

    # Full messages for exec trace
    orchestrator_full_messages: Annotated[dict[str, BaseMessage], merge_dict]
    planner_full_messages: Annotated[dict[str, BaseMessage], merge_dict]
    reviewer_full_messages: Annotated[dict[str, BaseMessage], merge_dict]

    # Orchestrator-level summarization
    message_summary: Optional[str]
    non_summary_start: int

    # Planning / execution state
    plan: List[Dict[str, Any]]
    plan_meta_data: List[Dict[str, Any]]

    # v1.1 multi-dispatch: list of dispatch dicts from orchestrator
    orchestrator_dispatches: List[Dict[str, Any]]

    # Orchestrator scratchpad
    scratchpad: Optional[str]

    # Per-Send dispatch context (set by Send(), read by executor nodes)
    current_dispatch: Optional[Dict[str, Any]]

    # Shared user↔orchestrator conversation summary (used by reviewer & planner)
    conversation_summary: Annotated[Optional[str], last_non_none]
    conversation_non_summary_start: Annotated[int, max_int]

    # Per-agent messages
    agents_messages: Annotated[
        dict[str, dict[str, list[BaseMessage]]],
        merge_agent_messages,
    ]
    agents_message_summary: Annotated[Dict[str, Optional[str]], merge_dict]
    agents_non_summary_start: Annotated[Dict[str, int], merge_dict]

    # Next available instance ID per agent type. Merge takes max for parallel safety.
    agent_instance_counter: Annotated[Dict[str, int], merge_max_dict]

    # Maps agent_name -> {str(instance_id) -> [message_id, ...]}
    agent_instance_map: Annotated[Dict[str, Dict[str, list[str]]], merge_instance_map]


#########################################################################
## Shared trace utils ###################################################
#########################################################################



TRACE_DIR = "/workspace/.agent_traces"

# Per-agent invocation counters (reset each session, like /workspace itself)
_trace_counters: dict[str, int] = {}


def _next_trace_counter(agent_name: str) -> int:
    """Return the next invocation number for this agent (1-based)."""
    _trace_counters[agent_name] = _trace_counters.get(agent_name, 0) + 1
    return _trace_counters[agent_name]


def _save_trace(
    messages: list,
    agent_name: str,
    plan: dict | None,
    instance_id: int = 0,
) -> tuple[str | None, int]:
    """Append one invocation's trace to the agent's trace file.

    Returns (trace_path, invocation_number) on success, (None, 0) on failure.
    """
    try:
        trace_dir = f"{TRACE_DIR}/{agent_name}"
        os.makedirs(trace_dir, exist_ok=True)
        trace_path = f"{trace_dir}/{instance_id}.md"
        counter_key = f"{agent_name}#{instance_id}"
        counter = _next_trace_counter(counter_key)

        # Build header
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step_info = ""
        if plan and isinstance(plan, dict):
            in_progress = [
                s for s in plan.get("steps", [])
                if s.get("status") == "in_progress"
            ]
            if in_progress:
                step_ids = ", ".join(str(s["id"]) for s in in_progress)
                step_info = f" Step {step_ids} —"

        header = f"## [{counter}]{step_info} {agent_name} | {timestamp}"

        # Extract instruction (first HumanMessage)
        instruction_text = ""
        for m in messages:
            if hasattr(m, "type") and m.type == "human":
                content = getattr(m, "content", "")
                if isinstance(content, str):
                    instruction_text = content
                elif isinstance(content, list):
                    instruction_text = "\n".join(
                        b if isinstance(b, str) else b.get("text", "")
                        for b in content
                    )
                break

        # Extract final response (last AIMessage)
        response_text = ""
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "ai":
                response_text = response_to_text(m)
                break

        # Extract tool log (tool calls + tool results, interleaved)
        tool_log_parts = []
        for m in messages:
            msg_type = getattr(m, "type", "")
            if msg_type == "ai" and hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    args_str = json.dumps(tc.get("args", {}), ensure_ascii=False)
                    if len(args_str) > 500:
                        args_str = args_str[:250] + " ... " + args_str[-250:]
                    tool_log_parts.append(
                        f"**Tool call**: `{tc.get('name', '?')}`\n```\n{args_str}\n```"
                    )
            elif msg_type == "tool":
                tool_name = getattr(m, "name", "tool")
                content = getattr(m, "content", "")
                if isinstance(content, str) and len(content) > 1000:
                    content = content[:500] + f"\n[... {len(content) - 1000} chars ...]\n" + content[-500:]
                elif isinstance(content, list):
                    content = str(content)[:1000]
                tool_log_parts.append(
                    f"**Result** (`{tool_name}`):\n```\n{content}\n```"
                )

        tool_log = "\n\n".join(tool_log_parts) if tool_log_parts else "_No tool calls._"

        # Assemble and append
        entry = f"""{header}

### Instruction
{instruction_text}

### Response
{response_text}

### Tool Log
{tool_log}

---
"""
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(entry)

        return trace_path, counter

    except Exception:
        logger.warning("Failed to save trace for %s", agent_name, exc_info=True)
        return None, 0


#########################################################################
## Executor context utils ###############################################
#########################################################################


def _extract_user_orchestrator_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Extract only HumanMessages and orchestrator AIMessages from the shared stream."""
    return [
        msg for msg in messages
        if isinstance(msg, HumanMessage)
        or (isinstance(msg, AIMessage) and getattr(msg, "name", None) == "orchestrator")
    ]


def _format_conversation_exchanges(messages: list[BaseMessage]) -> str:
    """Format a list of user/orchestrator messages as readable text lines."""
    parts = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            parts.append(f"[User] {content}")
        elif isinstance(msg, AIMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content.strip():
                parts.append(f"[Orchestrator] {content}")
    return "\n\n".join(parts)


def _build_conversation_context(
    state: MadAgentsState,
) -> str:
    """Build conversation context string from pre-computed summary in state."""
    all_messages = list(state.get("messages", []))
    user_orch_msgs = _extract_user_orchestrator_messages(all_messages)

    conv_summary = state.get("conversation_summary", None)
    conv_non_summary_start = state.get("conversation_non_summary_start", 0)

    recent_msgs = user_orch_msgs[conv_non_summary_start:]
    recent_exchanges = _format_conversation_exchanges(recent_msgs)

    context_parts = []
    if conv_summary and conv_summary.strip():
        context_parts.append(f"<summarized_history>\n{conv_summary}\n</summarized_history>")
    if recent_exchanges.strip():
        context_parts.append(f"<recent_exchanges>\n{recent_exchanges}\n</recent_exchanges>")
    plan = state.get("plan")
    if plan:
        context_parts.append(f"<current_plan>\n{json.dumps(plan, indent=2)}\n</current_plan>")

    return "\n\n".join(context_parts)


def _prepend_conversation_context(context: str, message: str) -> str:
    """Prepend conversation context to an instruction message."""
    if not context or not context.strip():
        return message
    return f"<conversation_context>\n{context}\n</conversation_context>\n\n---\n\n{message}"


#########################################################################
## Executor nodes #######################################################
#########################################################################


def get_planner_executor_node(
    planner: Planner,
    summarizer: Summarizer,
) -> Callable[[MadAgentsState], dict]:
    """Create a node that invokes the planner and returns plan + ToolMessage."""

    def planner_executor_node(state: MadAgentsState) -> dict:
        dispatch = state.get("current_dispatch") or {}
        instance_id = dispatch.get("instance_id", 0)

        # Per-instance context (mirrors worker/reviewer pattern)
        summary_key = f"planner#{instance_id}"

        agents_message_summary = state.get("agents_message_summary", {})
        agent_message_summary = agents_message_summary.get(summary_key, None)
        agents_non_summary_start = state.get("agents_non_summary_start", {})
        agent_non_summary_start = agents_non_summary_start.get(summary_key, 0)

        instance_map = state.get("agent_instance_map") or {}
        agent_instances = instance_map.get("planner", {})
        instance_msg_ids = set(agent_instances.get(str(instance_id), []))

        agents_messages = state.get("agents_messages", {})
        agent_messages = agents_messages.get("planner", {})

        if instance_msg_ids:
            instance_messages = {k: v for k, v in agent_messages.items() if k in instance_msg_ids}
        else:
            instance_messages = {}

        all_prev_msgs = [
            msg for msg_list in instance_messages.values() for msg in msg_list
        ]

        agent_message_summary, agent_non_summary_start = summarizer.summarize(
            agent_message_summary, agent_non_summary_start, all_prev_msgs
        )
        prev_msgs = all_prev_msgs[agent_non_summary_start:]

        instruction = dispatch.get("message", "")
        conversation_context = _build_conversation_context(state)
        enriched_instruction = _prepend_conversation_context(conversation_context, instruction)

        result: PlannerState = planner.graph.invoke({
            "reasoning_effort": dispatch.get("reasoning_effort", "high"),
            "non_summary_start": 0,
            "prev_msg_summary": agent_message_summary,
            "prev_msgs": prev_msgs,
            "messages": [HumanMessage(content=enriched_instruction)],
            "plan": state.get("plan"),
        })

        plan = result.get("plan")
        plan_meta_data = result.get("plan_meta_data")
        if plan is None:
            plan = {"steps": []}
            plan_meta_data = {"steps": []}

        # Find last AIMessage for token counts and thinking (skip ToolMessages)
        last_ai = None
        for m in reversed(result["messages"]):
            if isinstance(m, AIMessage):
                last_ai = m
                break

        message_id = uuid.uuid4().hex
        summary_fingerprint = make_summary_fingerprint(agent_message_summary, agent_non_summary_start)
        non_reasoning_output_tokens = extract_non_reasoning_output_tokens(last_ai) if last_ai else None

        planner_thinking = extract_thinking(last_ai) if last_ai else None

        # Save planner trace
        planner_trace_msgs = result["messages"]
        plan_for_trace = state.get("plan")  # old plan (before this invocation)
        trace_path, trace_counter = _save_trace(planner_trace_msgs, "planner", plan_for_trace, instance_id=instance_id)

        # Display AIMessage for `messages` (v1.0-compatible)
        display_additional = {
            "plan": plan,
            "plan_meta_data": plan_meta_data,
            "message_id": message_id,
            "instance_id": instance_id,
            "summary_fingerprint": summary_fingerprint,
        }
        if non_reasoning_output_tokens is not None:
            display_additional["non_reasoning_output_tokens"] = non_reasoning_output_tokens
        if planner_thinking:
            display_additional["reasoning"] = planner_thinking
        display_response = AIMessage(
            content=f"I have created the following plan:\n{json.dumps(plan, indent=2)}",
            name="planner",
            additional_kwargs=display_additional,
        )

        # Full response for exec trace
        full_response = last_ai if last_ai else result["messages"][-1]
        full_response.name = "planner"
        full_additional = dict(full_response.additional_kwargs or {})
        full_additional["message_id"] = message_id
        full_additional["summary_fingerprint"] = summary_fingerprint
        if non_reasoning_output_tokens is not None:
            full_additional["non_reasoning_output_tokens"] = non_reasoning_output_tokens
        full_response.additional_kwargs = full_additional

        # ToolMessage for orchestrator_messages
        tool_call_id = dispatch.get("tool_call_id") or get_last_tool_call_id(state)
        steps = plan.get("steps", []) if isinstance(plan, dict) else []
        extras = []
        parallel = get_parallel_ready_steps(plan)
        if len(parallel) > 1:
            extras.append(f"Parallel-ready steps: {parallel}")
        extra_str = ("\n\n" + "\n".join(extras)) if extras else ""
        instance_label = f" (instance {instance_id})" if instance_id != 0 else ""
        tool_msg_content = f"Planner{instance_label} completed. Plan created with {len(steps)} steps.\n\nPlan:\n{json.dumps(plan, indent=2)}{extra_str}"
        if trace_path:
            tool_msg_content += f"\n[Trace: {trace_path} | Invocation {trace_counter}]"
        tool_msg = ToolMessage(
            content=tool_msg_content,
            tool_call_id=tool_call_id or "unknown",
            name="InvokePlanner",
        )

        return {
            "messages": [display_response],
            "orchestrator_messages": [tool_msg],
            "planner_full_messages": {message_id: full_response},
            "agents_messages": {"planner": {message_id: planner_trace_msgs}},
            "agent_instance_map": {"planner": {str(instance_id): [message_id]}},
            "plan": plan,
            "plan_meta_data": plan_meta_data,
            "agents_message_summary": {summary_key: agent_message_summary},
            "agents_non_summary_start": {summary_key: agent_non_summary_start},
        }

    return planner_executor_node


def get_reviewer_executor_node(
    reviewer: Reviewer,
    reviewer_name: str,
    summarizer: Summarizer,
) -> Callable[[MadAgentsState], dict]:
    """Create a node that invokes a reviewer and returns a ToolMessage."""

    def reviewer_executor_node(state: MadAgentsState) -> dict:
        dispatch = state.get("current_dispatch") or {}
        instance_id = dispatch.get("instance_id", 0)

        # Per-instance context (mirrors worker pattern)
        summary_key = f"{reviewer_name}#{instance_id}"

        agents_message_summary = state.get("agents_message_summary", {})
        agent_message_summary = agents_message_summary.get(summary_key, None)
        agents_non_summary_start = state.get("agents_non_summary_start", {})
        agent_non_summary_start = agents_non_summary_start.get(summary_key, 0)

        # Look up this instance's message_ids
        instance_map = state.get("agent_instance_map") or {}
        agent_instances = instance_map.get(reviewer_name, {})
        instance_msg_ids = set(agent_instances.get(str(instance_id), []))

        agents_messages = state.get("agents_messages", {})
        agent_messages = agents_messages.get(reviewer_name, {})

        # Filter to this instance's message batches only
        if instance_msg_ids:
            instance_messages = {k: v for k, v in agent_messages.items() if k in instance_msg_ids}
        else:
            instance_messages = {}

        all_prev_msgs = [
            msg for msg_list in instance_messages.values() for msg in msg_list
        ]

        agent_message_summary, agent_non_summary_start = summarizer.summarize(
            agent_message_summary, agent_non_summary_start, all_prev_msgs
        )
        prev_msgs = all_prev_msgs[agent_non_summary_start:]

        conversation_context = _build_conversation_context(state)
        plan = state.get("plan")

        instruction = dispatch.get("message", "")
        enriched_instruction = _prepend_conversation_context(conversation_context, instruction)

        result: ReviewerState = reviewer.graph.invoke({
            "reasoning_effort": dispatch.get("reasoning_effort", "high"),
            "non_summary_start": 0,
            "prev_msg_summary": agent_message_summary,
            "prev_msgs": prev_msgs,
            "messages": [HumanMessage(content=enriched_instruction)],
        })

        message_id = uuid.uuid4().hex
        non_reasoning_output_tokens = extract_non_reasoning_output_tokens(result["messages"][-1])
        summary_fingerprint = make_summary_fingerprint(agent_message_summary, agent_non_summary_start)

        full_response = result["messages"][-1]
        full_response.name = reviewer_name
        full_additional = dict(full_response.additional_kwargs or {})
        full_additional["message_id"] = message_id
        full_additional["summary_fingerprint"] = summary_fingerprint
        if non_reasoning_output_tokens is not None:
            full_additional["non_reasoning_output_tokens"] = non_reasoning_output_tokens
        full_response.additional_kwargs = full_additional

        reviewer_text = response_to_text(result["messages"][-1])
        reviewer_thinking = extract_thinking(result["messages"][-1])

        # Save reviewer trace
        reviewer_trace_msgs = result["messages"]
        trace_path, trace_counter = _save_trace(reviewer_trace_msgs, reviewer_name, plan, instance_id=instance_id)

        # Display AIMessage for `messages`
        display_additional = {
            "message_id": message_id,
            "instance_id": instance_id,
            "summary_fingerprint": summary_fingerprint,
        }
        if non_reasoning_output_tokens is not None:
            display_additional["non_reasoning_output_tokens"] = non_reasoning_output_tokens
        if reviewer_thinking:
            display_additional["reasoning"] = reviewer_thinking
        display_response = AIMessage(
            content=reviewer_text,
            name=reviewer_name,
            additional_kwargs=display_additional,
        )

        # ToolMessage for orchestrator_messages
        tool_call_id = dispatch.get("tool_call_id") or get_last_tool_call_id(state)
        # Summarize reviewer output for orchestrator context
        plan_footer = compact_plan_summary(plan)
        instance_label = f" (instance {instance_id})" if instance_id != 0 else ""
        tool_content = f"{reviewer_name}{instance_label} response:\n{reviewer_text}"
        if plan_footer:
            tool_content += f"\n\n[{plan_footer}]"
        if trace_path:
            tool_content += f"\n[Trace: {trace_path} | Invocation {trace_counter}]"
        tool_msg = ToolMessage(
            content=tool_content,
            tool_call_id=tool_call_id or "unknown",
            name="InvokeReviewer",
        )

        return {
            "messages": [display_response],
            "orchestrator_messages": [tool_msg],
            "reviewer_full_messages": {message_id: full_response},
            "agents_messages": {reviewer_name: {message_id: reviewer_trace_msgs}},
            "agent_instance_map": {reviewer_name: {str(instance_id): [message_id]}},
            "agents_message_summary": {summary_key: agent_message_summary},
            "agents_non_summary_start": {summary_key: agent_non_summary_start},
        }

    return reviewer_executor_node


def get_worker_executor_node(
    worker: BaseWorker,
    agent_name: str,
    summarizer: Summarizer,
) -> Callable[[MadAgentsState], dict]:
    """Create a node that invokes a worker and returns a ToolMessage."""

    def worker_executor_node(state: MadAgentsState) -> dict:
        dispatch = state.get("current_dispatch") or {}
        instance_id = dispatch.get("instance_id", 0)

        # Composite key for per-instance summarization
        summary_key = f"{agent_name}#{instance_id}"

        # Per-agent context from agents_messages, scoped to this instance
        agents_message_summary = state.get("agents_message_summary", {})
        agent_message_summary = agents_message_summary.get(summary_key, None)
        agents_non_summary_start = state.get("agents_non_summary_start", {})
        agent_non_summary_start = agents_non_summary_start.get(summary_key, 0)

        # Look up this instance's message_ids
        instance_map = state.get("agent_instance_map") or {}
        agent_instances = instance_map.get(agent_name, {})
        instance_msg_ids = set(agent_instances.get(str(instance_id), []))

        agents_messages = state.get("agents_messages", {})
        agent_messages = agents_messages.get(agent_name, {})

        # Filter to this instance's message batches only
        if instance_msg_ids:
            instance_messages = {k: v for k, v in agent_messages.items() if k in instance_msg_ids}
        else:
            instance_messages = {}  # first invocation of this instance — no prior context

        all_prev_msgs = [
            msg
            for msg_list in instance_messages.values()
            for msg in msg_list
        ]

        agent_message_summary, agent_non_summary_start = summarizer.summarize(
            agent_message_summary, agent_non_summary_start, all_prev_msgs
        )
        prev_msgs = all_prev_msgs[agent_non_summary_start:]

        summary_fingerprint = make_summary_fingerprint(
            agent_message_summary, agent_non_summary_start
        )

        plan = state.get("plan")
        reasoning_effort = dispatch.get("reasoning_effort", "medium")

        # Build enriched worker message with plan step context (no conversation history)
        worker_message = build_worker_context(plan, dispatch.get("message", ""), step_id=dispatch.get("step_id"))

        worker_invoke_state = {
            "reasoning_effort": reasoning_effort,
            "non_summary_start": 0,
            "prev_msg_summary": agent_message_summary,
            "prev_msgs": prev_msgs,
            "messages": [],
            "user_msg": HumanMessage(content=worker_message),
        }
        model_override = dispatch.get("model")
        if model_override:
            worker_invoke_state["model_override"] = model_override

        # Set per-instance CLI bridge context variable before invoking worker
        from madagents.cli_bridge.bridge_interface import _current_cli_instance_id
        token = _current_cli_instance_id.set(instance_id)
        try:
            result = worker.graph.invoke(worker_invoke_state)
        finally:
            _current_cli_instance_id.reset(token)

        message_id = uuid.uuid4().hex
        token_kwargs = extract_token_kwargs(result["messages"][-1])

        worker_text = response_to_text(result["messages"][-1])
        worker_thinking = extract_thinking(result["messages"][-1])

        # Display AIMessage for `messages` (v1.0-compatible)
        display_additional = {
            "message_id": message_id,
            "instance_id": instance_id,
            "summary_fingerprint": summary_fingerprint,
            **token_kwargs,
        }
        if worker_thinking:
            display_additional["reasoning"] = worker_thinking
        display_response = AIMessage(
            content=worker_text,
            name=agent_name,
            additional_kwargs=display_additional,
        )

        # ToolMessage for orchestrator_messages
        tool_call_id = dispatch.get("tool_call_id") or get_last_tool_call_id(state)
        plan = state.get("plan")
        plan_footer = compact_plan_summary(plan)

        worker_trace_msgs = [result["user_msg"], *result["messages"]]

        # Save agent trace to disk
        trace_path, trace_counter = _save_trace(worker_trace_msgs, agent_name, plan, instance_id=instance_id)

        # Include instance in ToolMessage content for orchestrator
        instance_label = f" (instance {instance_id})" if instance_id != 0 else ""
        tool_content = f"{agent_name}{instance_label} response:\n{worker_text}"
        if plan_footer:
            tool_content += f"\n\n[{plan_footer}]"
        ctx_tokens = approx_tokens_in_messages(prev_msgs)
        if ctx_tokens > 5_000:
            tool_content += f"\n[Worker context: ~{ctx_tokens // 1000}K tokens]"
        if trace_path:
            tool_content += f"\n[Trace: {trace_path} | Invocation {trace_counter}]"
        tool_msg = ToolMessage(
            content=tool_content,
            tool_call_id=tool_call_id or "unknown",
            name="InvokeWorker",
        )

        return {
            "agents_messages": {
                agent_name: {message_id: worker_trace_msgs}
            },
            "agent_instance_map": {agent_name: {str(instance_id): [message_id]}},
            "messages": [display_response],
            "orchestrator_messages": [tool_msg],
            "agents_message_summary": {summary_key: agent_message_summary},
            "agents_non_summary_start": {summary_key: agent_non_summary_start},
        }

    return worker_executor_node


#########################################################################
## Routing ##############################################################
#########################################################################


def route_from_orchestrator(
    state: MadAgentsState,
) -> str | list[Send]:
    """Map the orchestrator decision to the next graph edge.

    Single dispatch: return a string (unchanged behavior).
    Multiple dispatches: return Send() objects for parallel fan-out.
    """
    dispatches = state.get("orchestrator_dispatches") or []

    if len(dispatches) <= 1:
        # Single dispatch or no tool call (user response)
        recipient = dispatches[0].get("recipient", "user") if dispatches else "user"
        return recipient

    # Multiple dispatches: fan-out via Send
    sends = []
    for d in dispatches:
        if d.get("recipient") == "user":
            continue
        sends.append(Send(d["recipient"], {**state, "current_dispatch": d}))
    return sends if sends else "user"


#########################################################################
## Graph builder ########################################################
#########################################################################

def build_graph(
    orchestrator: Orchestrator,
    planner: Planner,
    reviewers: dict[str, Reviewer],
    summarizer: Summarizer,
    workers: dict[str, BaseWorker],
    checkpointer,
    workflow_limit: int,
    enable_worker_model_routing: bool = False,
    available_worker_models: list[str] | None = None,
    default_worker_model: str | None = None,
) -> CompiledStateGraph:
    """Build and compile the v1.1 LangGraph state machine."""
    # Build delegation tools and optional model routing guidelines.
    delegation_tools = build_delegation_tools(
        enable_worker_model_routing, available_worker_models, default_worker_model,
    )
    graph = StateGraph(MadAgentsState)

    graph.add_node("orchestrator", get_orchestrator_node(
        orchestrator, summarizer,
        delegation_tools=delegation_tools,
        enable_model_routing=enable_worker_model_routing,
        default_worker_model=default_worker_model,
    ))
    graph.add_node("planner", get_planner_executor_node(planner, summarizer))

    for reviewer_name, reviewer in reviewers.items():
        graph.add_node(
            reviewer_name,
            get_reviewer_executor_node(reviewer, reviewer_name, summarizer),
        )

    for worker_name, worker in workers.items():
        graph.add_node(
            worker_name,
            get_worker_executor_node(worker, worker_name, summarizer),
        )

    graph.add_edge(START, "orchestrator")
    graph.add_edge("planner", "orchestrator")

    for reviewer_name in reviewers:
        graph.add_edge(reviewer_name, "orchestrator")

    for worker_name in workers:
        graph.add_edge(worker_name, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "orchestrator": "orchestrator",
            "planner": "planner",
            **{name: name for name in reviewers},
            **{name: name for name in workers},
            "user": END,
        },
    )

    return graph.compile(
        checkpointer=checkpointer
    ).with_config({"recursion_limit": workflow_limit})
