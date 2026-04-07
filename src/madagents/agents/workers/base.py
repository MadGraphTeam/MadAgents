import logging
from typing import Optional, Annotated, Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from madagents.agents.summarizer import Summarizer
from madagents.llm import LLMRuntime, get_default_runtime
from madagents.utils import annotate_output_token_counts

logger = logging.getLogger(__name__)

#########################################################################
## State ################################################################
#########################################################################

class BaseWorkerState(TypedDict):
    """State carried through a worker subgraph."""
    reasoning_effort: Optional[str]
    model_override: Optional[str]

    non_summary_start: Optional[int]
    prev_msg_summary: Optional[str]

    prev_msgs: list[BaseMessage]
    user_msg: HumanMessage

    messages: Annotated[list[BaseMessage], add_messages]

#########################################################################
## Nodes ################################################################
#########################################################################

def get_worker_node(
    llm: BaseChatModel,
    system_prompt: str,
    name: str,
    runtime: LLMRuntime,
    summarizer: Optional[Summarizer] = None,
    llm_tools: list | None = None,
) -> Callable[[BaseWorkerState], dict]:
    """Create a state-graph node that runs a worker LLM."""
    def worker_node(state: BaseWorkerState) -> dict:
        """Assemble prompts, invoke the worker, and return graph updates."""
        reasoning_effort = state.get("reasoning_effort", "high")
        model_override = state.get("model_override")

        if model_override and llm_tools is not None:
            # Create a new LLM with the overridden model and bind tools.
            override_llm = runtime.create_chat_model(
                model=model_override,
                reasoning_effort=reasoning_effort,
                verbosity="low",
                max_tokens=1_000_000,
            )
            override_llm_with_tools = runtime.bind_reasoning_trace(
                override_llm.bind_tools(llm_tools)
            )
            _llm = runtime.bind_reasoning(
                override_llm_with_tools, reasoning_effort=reasoning_effort,
            )
        elif model_override and llm_tools is None:
            logger.warning(
                "model_override=%r requested for worker %r but llm_tools is "
                "None; falling back to default LLM.",
                model_override, name,
            )
            _llm = runtime.bind_reasoning(llm, reasoning_effort=reasoning_effort)
        else:
            _llm = runtime.bind_reasoning(llm, reasoning_effort=reasoning_effort)

        prev_msgs_summary = state.get("prev_msg_summary", None)
        non_summary_start = state.get("non_summary_start", 0) or 0

        # On first pass, worker state may already be trimmed by the caller.
        # Reset local index so we don't double-skip messages.
        if not state.get("messages"):
            # Avoid double-skipping when the caller already trimmed messages.
            non_summary_start = 0

        prev_msgs = list(state["prev_msgs"])

        context_msgs = [
            *prev_msgs,
            state["user_msg"],
            *state["messages"],
        ]

        if summarizer is not None:
            # Summarize older context to stay within token limits.
            prev_msgs_summary, non_summary_start = summarizer.summarize(
                prev_msgs_summary,
                non_summary_start,
                context_msgs,
            )
            context_msgs = context_msgs[non_summary_start:]

        _prompt = system_prompt
        if prev_msgs_summary is not None and prev_msgs_summary.strip() != "":
            _prompt = f"""{system_prompt}

<previous_conversation_summary>
{prev_msgs_summary}
</previous_conversation_summary>"""

        messages = [
            *runtime.build_preamble(
                prompt=_prompt,
            ),
            *context_msgs,
        ]
        response = runtime.invoke(_llm, messages, reasoning_effort=reasoning_effort)
        response.name = name
        # Persist token counts for downstream accounting.
        annotate_output_token_counts(response, include_reasoning=True, include_total=True)
        
        return {
            "messages": [response],
            "prev_msg_summary": prev_msgs_summary,
            "non_summary_start": non_summary_start,
        }
    return worker_node

#########################################################################
## Agent ################################################################
#########################################################################

class BaseWorker:
    """Base class for workers that run tools under a state graph."""
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list,
        state_class: type[BaseWorkerState] = BaseWorkerState,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer: Optional[Summarizer] = None,
        worker_node_const: Callable[[BaseWorkerState], dict] = get_worker_node,
        runtime: LLMRuntime | None = None,
        **kwargs
    ):
        """Initialize the worker LLM, tools, and state graph."""
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.state_class = state_class
        self.summarizer = summarizer
        self.runtime = runtime or get_default_runtime()

        self.llm = self.runtime.create_chat_model(
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            max_tokens=1_000_000,
        )

        llm_tools, node_tools = self.runtime.prepare_tools(self.tools)

        # Bind tools to the LLM, including encrypted reasoning when available.
        self.llm_with_tools = self.runtime.bind_reasoning_trace(
            self.llm.bind_tools(llm_tools)
        )

        graph = StateGraph(self.state_class)

        graph.add_node(
            "agent",
            worker_node_const(
                self.llm_with_tools,
                self.system_prompt,
                self.name,
                runtime=self.runtime,
                summarizer=self.summarizer,
                llm_tools=llm_tools,
            ),
        )
        graph.add_node("tools", ToolNode(node_tools))

        graph.set_entry_point("agent")

        graph.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                END: END
            }
        )

        graph.add_edge("tools", "agent")

        limit = step_limit if isinstance(step_limit, int) and step_limit > 0 else 200
        # Cap the recursion limit to avoid runaway tool loops.
        self.graph = graph.compile().with_config({"recursion_limit": limit})
