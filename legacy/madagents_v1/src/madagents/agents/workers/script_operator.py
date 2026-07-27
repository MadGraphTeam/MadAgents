from typing import Optional

from madagents.tools import (
  bash_tool, apply_patch_tool,
  openai_read_pdf_tool, openai_read_image_tool, web_search_tool,
)
from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import (
    STYLE_BLOCK, ENVIRONMENT_BASE,
    WORKFLOW_3_STEP, WORKFLOW_GUIDANCE_BASE,
    FINAL_ANSWER_ACTION_WORKER, ERROR_HANDLING_STANDARD, TOOL_USAGE_BASH_PATCH,
    SYSTEM_PROMPT_SAFETY_BASE,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

SCRIPT_OPERATOR_DESC = """script_operator (Script-Operator)
- Specialized in bash and Python. Can inspect/modify the environment and create/edit/execute scripts."""

SCRIPT_OPERATOR_DESC_SHORT = SCRIPT_OPERATOR_DESC

#########################################################################
## Prompt ###############################################################
#########################################################################

SCRIPT_OPERATOR_SYSTEM_PROMPT = f"""<role>
You are the script_operator. You accomplish tasks using bash and Python.
</role>

<environment>
{ENVIRONMENT_BASE}
</environment>

<tools>
{TOOL_USAGE_BASH_PATCH}
</tools>

<instructions>
{SYSTEM_PROMPT_SAFETY_BASE}

{WORKFLOW_3_STEP}

{WORKFLOW_GUIDANCE_BASE}

{FINAL_ANSWER_ACTION_WORKER}

{ERROR_HANDLING_STANDARD}
</instructions>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class ScriptOperator(BaseWorker):
    """Worker specialized in bash/Python scripting tasks."""
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the script operator worker."""
        tools = [
            bash_tool, apply_patch_tool,
            openai_read_pdf_tool, openai_read_image_tool, web_search_tool
        ]
        super().__init__(
            name="script_operator",
            system_prompt=SCRIPT_OPERATOR_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
        
