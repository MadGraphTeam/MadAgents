import json
from typing import Any, Optional, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from madagents.utils import response_to_text, _serialize_message

#########################################################################
## Message helpers ######################################################
#########################################################################

def _is_ai_message(msg: Any) -> bool:
    return isinstance(msg, AIMessage) or (isinstance(msg, dict) and msg.get("type") == "AIMessage")


def _is_tool_message(msg: Any) -> bool:
    return isinstance(msg, ToolMessage) or (isinstance(msg, dict) and msg.get("type") == "ToolMessage")


def _message_name(msg: Any) -> Optional[str]:
    if isinstance(msg, BaseMessage):
        return msg.name
    if isinstance(msg, dict):
        return msg.get("name")
    return None


def _message_additional_kwargs(msg: Any) -> dict:
    if isinstance(msg, BaseMessage):
        return dict(getattr(msg, "additional_kwargs", None) or {})
    if isinstance(msg, dict):
        return dict(msg.get("additional_kwargs") or {})
    return {}


def _message_content(msg: Any) -> Any:
    if isinstance(msg, BaseMessage):
        return msg.content
    if isinstance(msg, dict):
        return msg.get("content")
    return None


def _message_usage_metadata(msg: Any) -> Optional[dict]:
    if isinstance(msg, BaseMessage):
        usage = getattr(msg, "usage_metadata", None)
        return usage if isinstance(usage, dict) else None
    if isinstance(msg, dict):
        usage = msg.get("usage_metadata")
        return usage if isinstance(usage, dict) else None
    return None


def _message_response_metadata(msg: Any) -> Optional[dict]:
    if isinstance(msg, BaseMessage):
        metadata = getattr(msg, "response_metadata", None)
        return metadata if isinstance(metadata, dict) else None
    if isinstance(msg, dict):
        metadata = msg.get("response_metadata")
        return metadata if isinstance(metadata, dict) else None
    return None


def _message_tool_call_id(msg: Any) -> Optional[str]:
    if isinstance(msg, ToolMessage):
        return getattr(msg, "tool_call_id", None)
    if isinstance(msg, dict):
        return msg.get("tool_call_id")
    return None


def get_add_content(message: BaseMessage):
    if isinstance(message, AIMessage):
        if message.name == "orchestrator":
            orchestrator_decision = message.additional_kwargs.get("orchestrator_decision")
            orchestrator_dispatches = message.additional_kwargs.get("orchestrator_dispatches")
            # Thinking content from Anthropic extended thinking (v1.1)
            reasoning = message.additional_kwargs.get("reasoning", "")

            if orchestrator_dispatches is not None:
                # v1.1 dispatch format
                first = orchestrator_dispatches[0] if orchestrator_dispatches else {}
                result = {
                    "dispatches": orchestrator_dispatches,
                    "recipient": first.get("recipient", ""),
                    "message": first.get("message", ""),
                    "reasoning_effort": first.get("reasoning_effort", ""),
                }
                if reasoning:
                    result["reasoning"] = reasoning
                return result

            if orchestrator_decision is not None:
                # v1.0 format
                return {
                    "recipient": orchestrator_decision.get("recipient"),
                    "reasoning": orchestrator_decision.get("reasoning"),
                    "message": orchestrator_decision.get("message"),
                    "reasoning_effort": orchestrator_decision.get("reasoning_effort"),
                    "future_note": orchestrator_decision.get("future_note"),
                }

            # Neither present (e.g. v1.1 user-response or interrupt)
            if reasoning:
                return {"reasoning": reasoning}
            return {}
    if getattr(message, "name", None) in ["planner", "plan_updater"]:
        plan = message.additional_kwargs.get("plan")
        if plan is None:
            raise ValueError(f"Missing 'plan' in additional_kwargs for message name={message.name!r}")
        add_content = {"plan": plan}
        plan_meta_data = message.additional_kwargs.get("plan_meta_data")
        if plan_meta_data is not None:
            add_content["plan_meta_data"] = plan_meta_data
        reasoning = message.additional_kwargs.get("reasoning", "")
        if reasoning:
            add_content["reasoning"] = reasoning
        return add_content
    # Generic agent messages (workers, reviewer, etc.)
    reasoning = message.additional_kwargs.get("reasoning", "")
    instance_id = message.additional_kwargs.get("instance_id")
    result = {}
    if reasoning:
        result["reasoning"] = reasoning
    if instance_id is not None:
        result["instance_id"] = instance_id
    return result


def get_exec_trace_messages(agent: str, message: BaseMessage):
    msgs = []
    if isinstance(message, AIMessage):
        # message is the agent's response if no function call exist. In this case, return nothing.
        exist_fct_call = False
        thinking_msgs: list[dict] = []
        apply_patch_trace = None
        seen_call_ids: set[str] = set()
        blocks = message.content

        if isinstance(blocks, list):
            for content in blocks:
                if not isinstance(content, dict):
                    # Handle object-type blocks (e.g. ThinkingBlock, TextBlock)
                    content_type = (getattr(content, "type", None) or "").lower()
                    if content_type in {"reasoning", "thinking"}:
                        thinking_text = getattr(content, "thinking", None) or getattr(content, "text", None) or ""
                        if isinstance(thinking_text, str) and thinking_text.strip():
                            thinking_msgs.append({
                                "content": "",
                                "name": agent,
                                "add_content": {
                                    "exec_trace": True,
                                    "type": "thinking",
                                    "content": thinking_text,
                                },
                            })
                    elif content_type in {"tool_use", "tool_call"}:
                        exist_fct_call = True
                        tool_name = getattr(content, "name", None) or getattr(content, "tool_name", None)
                        if not _is_internal_structured_tool(tool_name):
                            arguments = getattr(content, "input", None)
                            if tool_name == "save_answer":
                                arguments = _sanitize_save_answer_arguments(arguments)
                            call_id = getattr(content, "id", None)
                            if isinstance(call_id, str) and call_id:
                                seen_call_ids.add(call_id)
                            msgs.append({
                                "content": "",
                                "name": agent,
                                "add_content": {
                                    "exec_trace": True,
                                    "type": "function_call",
                                    "name": tool_name,
                                    "arguments": arguments,
                                    "call_id": call_id,
                                },
                            })
                    continue
                content_type = (content.get("type") or "").lower()
                if content_type in {"reasoning", "thinking"}:
                    thinking_text = content.get("thinking") or content.get("text") or ""
                    if isinstance(thinking_text, str) and thinking_text.strip():
                        thinking_msgs.append({
                            "content": "",
                            "name": agent,
                            "add_content": {
                                "exec_trace": True,
                                "type": "thinking",
                                "content": thinking_text,
                            },
                        })
                    continue
                if content_type == "text":
                    text_value = content.get("text")
                    if isinstance(text_value, str) and text_value:
                        msgs.append({
                            "content": "",
                            "name": agent,
                            "add_content": {
                                "exec_trace": True,
                                "type": "text",
                                "content": text_value,
                            },
                        })
                    continue
                if content_type in {"function_call", "tool_call", "tool_use"}:
                    exist_fct_call = True
                    tool_name = content.get("name") or content.get("tool_name")
                    if _is_internal_structured_tool(tool_name):
                        continue
                    arguments = content.get("arguments")
                    if arguments is None:
                        arguments = content.get("input")
                    if tool_name == "save_answer":
                        arguments = _sanitize_save_answer_arguments(arguments)
                    call_id = content.get("call_id") or content.get("tool_call_id") or content.get("id")
                    if not isinstance(call_id, str) or not call_id:
                        call_id = None
                    if call_id:
                        seen_call_ids.add(call_id)
                    msgs.append({
                        "content": "",
                        "name": agent,
                        "add_content": {
                            "exec_trace": True,
                            "type": "function_call",
                            "name": tool_name,
                            "arguments": arguments,
                            "call_id": call_id,
                        },
                    })
                    continue
                if content_type == "apply_patch_call":
                    exist_fct_call = True
                    operation = content.get("operation")
                    if apply_patch_trace is None:
                        apply_patch_trace = {
                            "content": "",
                            "name": agent,
                            "add_content": {
                                "exec_trace": True,
                                "type": "function_call",
                                "name": "apply_patch",
                                "arguments": {"operations": []},
                            },
                        }
                        msgs.append(apply_patch_trace)
                    if isinstance(operation, dict):
                        apply_patch_trace["add_content"]["arguments"]["operations"].append(operation)

        for call in _iter_tool_calls_from_message(message):
            call_id = _get_tool_call_id(call)
            if isinstance(call_id, str) and call_id in seen_call_ids:
                continue
            tool_name = _get_tool_call_name(call)
            if _is_internal_structured_tool(tool_name):
                continue
            arguments = _get_tool_call_arguments(call)
            if tool_name == "save_answer":
                arguments = _sanitize_save_answer_arguments(arguments)
            if isinstance(call_id, str) and call_id:
                seen_call_ids.add(call_id)
            if tool_name or call_id:
                exist_fct_call = True
                msgs.append({
                    "content": "",
                    "name": agent,
                    "add_content": {
                        "exec_trace": True,
                        "type": "function_call",
                        "name": tool_name,
                        "arguments": arguments,
                        "call_id": call_id if isinstance(call_id, str) and call_id else None,
                    },
                })
        if not exist_fct_call:
            # No tool calls — return thinking blocks only (e.g. final
            # response thinking before the agent reply).
            return thinking_msgs
        # Prepend thinking before tool call traces.
        return thinking_msgs + msgs
    elif isinstance(message, ToolMessage):
        if _is_internal_structured_tool(message.name):
            return []
        if message.name == "apply_patch" and not isinstance(message.artifact, dict):
            return []
        tool_call_id = getattr(message, "tool_call_id", None)
        if not isinstance(tool_call_id, str) or not tool_call_id:
            tool_call_id = None
        msgs = [{
            "content": "",
            "name": agent,
            "add_content": {
                "exec_trace": True,
                "type": "tool_message",
                "name": message.name,
                "content": get_exec_trace_content(message),
                "tool_call_id": tool_call_id,
            }
        }]
    return msgs


def _format_tool_interrupt_reason(reason_type: str, detail: Optional[str]) -> str:
    if reason_type == "user":
        return "Interrupted before tool execution by user request."
    if reason_type == "error":
        detail = detail or "unknown error"
        return f"Interrupted before tool execution due to error: {detail}"
    return "Interrupted before tool execution."


def _get_tool_call_id(call: dict) -> Optional[str]:
    for key in ("id", "tool_call_id", "call_id"):
        value = call.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _get_tool_call_name(call: dict) -> Optional[str]:
    name = call.get("name")
    if isinstance(name, str) and name:
        return name
    tool_name = call.get("tool_name")
    if isinstance(tool_name, str) and tool_name:
        return tool_name
    function = call.get("function")
    if isinstance(function, dict):
        fn_name = function.get("name")
        if isinstance(fn_name, str) and fn_name:
            return fn_name
    return None


def _get_tool_call_arguments(call: dict) -> Any:
    if "args" in call:
        return call.get("args")
    if "arguments" in call:
        return call.get("arguments")
    if "input" in call:
        return call.get("input")
    function = call.get("function")
    if isinstance(function, dict):
        return function.get("arguments")
    return None


INTERNAL_STRUCTURED_TOOL_NAMES = {
    "OrchestratorDecision",
    "Plan",
    "PlanUpdate",
    "add_plan_step",
    "remove_plan_step",
    "update_plan_step",
    "read_plan",
    "submit_plan",
}


def _is_internal_structured_tool(name: Optional[str]) -> bool:
    return isinstance(name, str) and name in INTERNAL_STRUCTURED_TOOL_NAMES


def _iter_tool_calls_from_message(message: BaseMessage) -> list[dict]:
    calls: list[dict] = []
    tool_calls = getattr(message, "tool_calls", None)
    if isinstance(tool_calls, list):
        calls.extend([call for call in tool_calls if isinstance(call, dict)])
    additional_kwargs = getattr(message, "additional_kwargs", {}) or {}
    ak_tool_calls = additional_kwargs.get("tool_calls")
    if isinstance(ak_tool_calls, list):
        calls.extend([call for call in ak_tool_calls if isinstance(call, dict)])
    function_call = additional_kwargs.get("function_call")
    if isinstance(function_call, dict):
        calls.append(function_call)
    return calls


def _record_tool_call(
    pending_tool_calls: dict[str, dict],
    agent_name: Optional[str],
    call_id: Optional[str],
    name: Optional[str],
    arguments: Any,
) -> None:
    if not call_id or not name:
        return
    if call_id in pending_tool_calls:
        return
    pending_tool_calls[call_id] = {
        "tool_call_id": call_id,
        "name": name,
        "arguments": arguments,
        "agent": agent_name,
    }


def _record_apply_patch_call(
    pending_apply_patch_calls: dict[str, dict],
    agent_name: Optional[str],
    call_id: Optional[str],
    operation: Any,
) -> None:
    if not call_id:
        return
    if call_id in pending_apply_patch_calls:
        return
    op_dict = operation if isinstance(operation, dict) else {}
    pending_apply_patch_calls[call_id] = {
        "call_id": call_id,
        "operation": op_dict,
        "agent": agent_name,
    }


def _update_pending_tool_calls(
    messages: list[BaseMessage],
    agent_name: Optional[str],
    pending_tool_calls: dict[str, dict],
    pending_apply_patch_calls: dict[str, dict],
) -> None:
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            if isinstance(tool_call_id, str) and tool_call_id:
                pending_tool_calls.pop(tool_call_id, None)
            if msg.name == "apply_patch":
                outputs = msg.content if isinstance(msg.content, list) else []
                for item in outputs:
                    if isinstance(item, dict) and item.get("type") == "apply_patch_call_output":
                        call_id = item.get("call_id")
                        if isinstance(call_id, str) and call_id:
                            pending_apply_patch_calls.pop(call_id, None)
            continue

        if not isinstance(msg, AIMessage):
            continue
        msg_agent = agent_name or getattr(msg, "name", None)

        tool_calls = getattr(msg, "tool_calls", None)
        if isinstance(tool_calls, list):
            for call in tool_calls:
                if not isinstance(call, dict):
                    continue
                call_id = _get_tool_call_id(call)
                name = _get_tool_call_name(call)
                if _is_internal_structured_tool(name):
                    continue
                arguments = _get_tool_call_arguments(call)
                _record_tool_call(
                    pending_tool_calls,
                    msg_agent,
                    call_id,
                    name,
                    arguments,
                )

        additional_kwargs = getattr(msg, "additional_kwargs", {}) or {}
        ak_tool_calls = additional_kwargs.get("tool_calls")
        if isinstance(ak_tool_calls, list):
            for call in ak_tool_calls:
                if not isinstance(call, dict):
                    continue
                call_id = _get_tool_call_id(call)
                name = _get_tool_call_name(call)
                if _is_internal_structured_tool(name):
                    continue
                arguments = _get_tool_call_arguments(call)
                _record_tool_call(
                    pending_tool_calls,
                    msg_agent,
                    call_id,
                    name,
                    arguments,
                )

        function_call = additional_kwargs.get("function_call")
        if isinstance(function_call, dict):
            call_id = _get_tool_call_id(function_call)
            name = _get_tool_call_name(function_call)
            arguments = _get_tool_call_arguments(function_call)
            if not _is_internal_structured_tool(name):
                _record_tool_call(
                    pending_tool_calls,
                    msg_agent,
                    call_id,
                    name,
                    arguments,
                )

        blocks = getattr(msg, "content", None)
        if isinstance(blocks, list):
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                btype = (block.get("type") or "").lower()
                if btype in {"function_call", "tool_call", "tool_use"}:
                    call_id = block.get("call_id") or block.get("id")
                    name = block.get("name") or block.get("tool_name")
                    if _is_internal_structured_tool(name):
                        continue
                    arguments = block.get("arguments")
                    if arguments is None:
                        arguments = block.get("input")
                    _record_tool_call(
                        pending_tool_calls,
                        msg_agent,
                        call_id,
                        name,
                        arguments,
                    )
                elif btype == "apply_patch_call":
                    call_id = block.get("call_id")
                    operation = block.get("operation")
                    _record_apply_patch_call(
                        pending_apply_patch_calls,
                        msg_agent,
                        call_id,
                        operation,
                    )


def find_unmatched_tool_calls(messages: list) -> dict[str, dict]:
    """Find tool calls in messages that don't have matching tool results.

    Walks through the message list tracking tool call IDs from AIMessages
    and removing them when a matching ToolMessage is found. Returns the
    remaining pending calls dict: ``{call_id: {"tool_call_id", "name",
    "arguments", "agent"}}``.
    """
    pending: dict[str, dict] = {}
    pending_apply: dict[str, dict] = {}
    _update_pending_tool_calls(messages, None, pending, pending_apply)
    return pending


def synthesize_interrupt_tool_messages(
    pending: dict[str, dict],
    reason: str = "Interrupted before completion.",
) -> list[ToolMessage]:
    """Create synthetic failed ToolMessages for unmatched tool calls."""
    results = []
    for call_id, info in pending.items():
        tool_name = info.get("name") or "tool"
        results.append(ToolMessage(
            name=tool_name,
            tool_call_id=call_id,
            content=f"Interrupted: {reason}",
        ))
    return results


def _sanitize_save_answer_arguments(arguments: Any) -> Any:
    if isinstance(arguments, dict):
        return {"file_path": arguments.get("file_path")}
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return "{}"
        if isinstance(parsed, dict):
            return json.dumps({"file_path": parsed.get("file_path")})
        return "{}"
    return {}


def get_exec_trace_content(message: ToolMessage) -> Union[dict, str]:
    if message.name in ["bash"]:
        artifact = message.artifact if isinstance(message.artifact, dict) else {}
        # If artifact has stdout/stderr, use it for structured display.
        # Otherwise fall back to message.content (e.g. planner's custom tools node).
        if artifact.get("stdout") is not None or artifact.get("stderr") is not None:
            return {
                "exit_code": artifact.get("exit_code"),
                "stdout": artifact.get("stdout"),
                "stderr": artifact.get("stderr"),
                "stdout_last_n": artifact.get("stdout_last_n"),
                "stderr_last_n": artifact.get("stderr_last_n"),
                "stdout_path": artifact.get("stdout_path"),
                "stderr_path": artifact.get("stderr_path"),
                "timeout": artifact.get("timeout"),
                "pid": artifact.get("pid"),
            }
        # No artifact — return content as stdout so the UI can display it.
        content = message.content
        if isinstance(content, str) and content.strip():
            return {"stdout": content}
        return {"stdout": ""}
    elif message.name in ["read_pdf", "read_image"]:
        return message.artifact
    elif message.name in ["read_int_cli_output", "run_int_cli_command", "int_cli_status", "read_int_cli_transcript"]:
        return message.artifact
    elif message.name == "apply_patch":
        if isinstance(message.artifact, dict):
            return message.artifact
        return {
            "status": "failed",
            "results": [],
        }
    elif message.name == "wait":
        return message.content if isinstance(message.content, (str, dict)) else ""
    else:
        if isinstance(message.content, str):
            return message.content
        elif isinstance(message.content, dict):
            return message.content
        else:
            tool_message_str = json.dumps(_serialize_message(message), indent=2)
            print(f"ToolMessage\n{tool_message_str}\ncould not be forwarded to the UI")
            return ""


def _short_detail(detail: Optional[str], limit: int = 1000) -> Optional[str]:
    if detail is None:
        return None
    detail = detail.strip()
    if len(detail) > limit:
        return detail[:limit].rstrip() + "..."
    return detail


def _format_interrupt_reason(reason_type: str, detail: Optional[str]) -> str:
    if reason_type == "user":
        return "The workflow has been interrupted because the user requested an interrupt."
    if reason_type == "error":
        detail = detail or "unknown error"
        return f"The workflow has been interrupted because of an error: {detail}"
    return "The workflow has been interrupted."


def _build_interrupt_ai_message(
    agent_name: str,
    reason_type: str,
    detail: Optional[str],
    additional_kwargs: Optional[dict] = None,
) -> AIMessage:
    content = [{"type": "text", "text": _format_interrupt_reason(reason_type, _short_detail(detail))}]
    return AIMessage(
        content=content,
        name=agent_name,
        additional_kwargs=additional_kwargs or {},
    )


def _extract_subgraph_summary_fields(
    update: dict,
) -> tuple[Optional[str], bool, Optional[int], bool]:
    summary: Optional[str] = None
    summary_set = False
    if "message_summary" in update:
        summary = update.get("message_summary")
        summary_set = True
    elif "prev_msg_summary" in update:
        summary = update.get("prev_msg_summary")
        summary_set = True
    elif "agent_message_summary" in update:
        summary = update.get("agent_message_summary")
        summary_set = True

    non_summary_start: Optional[int] = None
    non_summary_set = False
    if "non_summary_start" in update:
        non_summary_start = update.get("non_summary_start")
        non_summary_set = True
    elif "agent_non_summary_start" in update:
        non_summary_start = update.get("agent_non_summary_start")
        non_summary_set = True

    return summary, summary_set, non_summary_start, non_summary_set


def _merge_mapping(base: Optional[dict], updates: dict) -> dict:
    merged = dict(base) if isinstance(base, dict) else {}
    merged.update(updates)
    return merged


def _message_to_ui(message: BaseMessage) -> dict:
    return {
        "content": response_to_text(message),
        "name": "user" if isinstance(message, HumanMessage) else message.name,
        "add_content": get_add_content(message),
    }
