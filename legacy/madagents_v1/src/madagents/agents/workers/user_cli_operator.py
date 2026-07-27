from typing import Optional

from madagents.tools import (
  get_int_cli_status_tool, get_read_int_cli_output_tool,
  get_run_int_cli_command_tool, get_read_int_cli_transcript_tool,
  web_search_tool, bash_tool, apply_patch_tool,
  openai_read_pdf_tool, openai_read_image_tool,
)
from madagents.cli_bridge.bridge_interface import CLISession
from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import (
    STYLE_BLOCK, ENVIRONMENT_DESCRIPTION_BASE, ENVIRONMENT_GUIDANCE_BASE,
    WORKFLOW_3_STEP, FINAL_ANSWER_ACTION_WORKER, SYSTEM_PROMPT_SAFETY_BASE,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

USER_CLI_OPERATOR_DESC = """user_cli_operator (CLI-Operator)
- Specialized in accessing the user's interactive CLI session.
- Can always read the CLI; executing commands in the user's session requires explicit user permission.
- Additional tools: interactive CLI access."""

USER_CLI_OPERATOR_DESC_SHORT = USER_CLI_OPERATOR_DESC

#########################################################################
## Prompt ###############################################################
#########################################################################

USER_CLI_OPERATOR_SYSTEM_PROMPT = f"""<role>
You are the user_cli_operator. You inspect and interact with the user's interactive CLI session.
</role>

<environment>
{ENVIRONMENT_DESCRIPTION_BASE}
- User's interactive CLI session available. Transcripts: `/runs/user_bridge/pure_transcript.log` (plain), `/runs/user_bridge/transcript.log` (timestamped). NEVER modify transcript files directly.
{ENVIRONMENT_GUIDANCE_BASE}
</environment>

<tools>
- Prefer "bash" as the default execution environment over interactive CLI tools.
- Use interactive CLI tools ONLY to inspect the user's CLI transcript/state, or to execute commands in the user's session — executing commands requires explicit user permission.
- Before using interactive CLI tools, use "int_cli_status" to check the session state. Inspect output after each command — check if it succeeded or needs more time.
- Hint: MadGraph outputs some warnings just once — restart MadGraph to capture them again.
- If bash exceeds the response window, check if it's stuck (kill its process group) or needs time (use `bash("sleep N")` then check output files).
</tools>

<instructions>
{SYSTEM_PROMPT_SAFETY_BASE}

{WORKFLOW_3_STEP}

- Produce concise, relevant output (use quiet/terse flags when safe), but do not suppress warnings or errors.
- If the user's instructions appear to contain a mistake or conflict with the task's background, tell the user what you suspect and ask for clarification.

{FINAL_ANSWER_ACTION_WORKER}

On failure, inspect errors/logs and try 1 fix (use "web_search" if needed). If unsuccessful, stop and report: the error (include related warnings), what you tried and why, and root-cause hypotheses.
</instructions>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class UserCLIOperator(BaseWorker):
    """Worker specialized in interacting with the user's CLI session."""
    def __init__(
        self,
        session: CLISession,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the user CLI operator worker."""
        tools = [
            get_int_cli_status_tool(session),
            get_read_int_cli_output_tool(session),
            get_run_int_cli_command_tool(session),
            get_read_int_cli_transcript_tool(session),
            web_search_tool,
            bash_tool, apply_patch_tool,
            openai_read_pdf_tool, openai_read_image_tool,
        ]
        super().__init__(
            name="user_cli_operator",
            system_prompt=USER_CLI_OPERATOR_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
