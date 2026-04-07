from pathlib import Path
from typing import Optional

from madagents.tools import (
  bash_tool, apply_patch_tool,
  get_int_cli_status_tool, get_read_int_cli_output_tool,
  get_run_int_cli_command_tool, get_read_int_cli_transcript_tool,
  openai_read_pdf_tool, openai_read_image_tool, web_search_tool,
)
from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import (
    STYLE_BLOCK, ENVIRONMENT_DESCRIPTION_BASE, ENVIRONMENT_GUIDANCE_BASE,
    WORKFLOW_3_STEP, WORKFLOW_GUIDANCE_BASE,
    FINAL_ANSWER_ACTION_WORKER, ERROR_HANDLING_STANDARD,
    SYSTEM_PROMPT_SAFETY_BASE,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

MADGRAPH_OPERATOR_DESC = """madgraph_operator (MadGraph-Operator)
- The primary expert on MadGraph and related tools (e.g. Pythia8, Delphes, MadSpin), with access to authoritative local documentation.
- Specialized in MadGraph5_aMC@NLO: process definition, event generation, shower/hadronisation, detector simulation setup, generation/prediction-level studies.
- Additional tools: interactive CLI access."""

MADGRAPH_OPERATOR_DESC_SHORT = MADGRAPH_OPERATOR_DESC

#########################################################################
## Prompt ###############################################################
#########################################################################

_here = Path(__file__).resolve()
# _here = .../madagents/agents/workers/madgraph_operator.py → .parent.parent.parent = .../madagents/
_sw_instr_dir = _here.parent.parent.parent / "software_instructions"
_madgraph_instr_path = _sw_instr_dir / "madgraph.md"
if not _madgraph_instr_path.is_file():
  raise FileNotFoundError(f"madgraph.md not found at: {_madgraph_instr_path}")
madgraph_instr = _madgraph_instr_path.read_text(encoding="utf-8").strip()

MADGRAPH_OPERATOR_SYSTEM_PROMPT = f"""<role>
You are the madgraph_operator. You accomplish tasks using MadGraph and associated tools.
</role>

<environment>
{ENVIRONMENT_DESCRIPTION_BASE}
- Interactive CLI session available. Transcripts: `$WORKDIR/madgraph_bridge/pure_transcript.log` (plain), `$WORKDIR/madgraph_bridge/transcript.log` (timestamped). NEVER modify transcript files directly.
- `/madgraph_docs/`: read-only curated documentation for MadGraph and associated tools (e.g. Pythia8, Delphes, MadSpin).
{ENVIRONMENT_GUIDANCE_BASE}
</environment>

<tools>
- Prefer "apply_patch" for creating/updating/deleting non-binary files (up to ~20 lines for new files; use "bash" for larger).
- Use bash/Python scripts for general tasks. For MadGraph commands, ALWAYS prefer scripted `.mg5` files (e.g., `<MG5_DIR>/bin/mg5_aMC script.mg5`) over interactive mode.
- Use the interactive CLI ONLY for quick inspection/debugging or user-requested interactive mode.
- Hint: MadGraph outputs some warnings just once — restart MadGraph to capture them again.
- Before using interactive CLI tools, use "int_cli_status" to check the session state. When using the interactive CLI, inspect output after each command — check if it succeeded or needs more time.
- If bash exceeds the response window, check if it's stuck (kill its process group) or needs time (use `bash("sleep N")` then check output files).
</tools>

<information_trust>
For MadGraph syntax, parameters, and configuration:
1. Consult `/madgraph_docs/` first.
2. Trust code outputs, error messages, config files, and MadGraph source code. Inspect source files directly when docs don't cover a detail.
3. "web_search" as last resort — be skeptical, cross-check against local docs, prefer official MadGraph/Launchpad sources.
If sources disagree, trust MadGraph source code over local docs, and local docs over web sources.

**Do not rely on your own knowledge** for MadGraph-specific facts (parameter names, default values, syntax, software behavior). Your training data may be outdated or incorrect. Always verify against the sources above before making claims. Use your knowledge for orientation — knowing where to look and what to try — not as a source of truth.
</information_trust>

<instructions>
{SYSTEM_PROMPT_SAFETY_BASE}

{WORKFLOW_3_STEP}

{WORKFLOW_GUIDANCE_BASE}

{FINAL_ANSWER_ACTION_WORKER}

{ERROR_HANDLING_STANDARD}
</instructions>

<style>
{STYLE_BLOCK}
</style>

<madgraph_instructions>
{madgraph_instr}
</madgraph_instructions>"""

#########################################################################
## Agent ################################################################
#########################################################################

class MadGraphOperator(BaseWorker):
    """Worker specialized in MadGraph workflows and tooling."""
    def __init__(
        self,
        session,  # CLISession or CLISessionManager (duck-typed)
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the MadGraph operator worker."""
        tools = [
            bash_tool, apply_patch_tool,
            get_int_cli_status_tool(session),
            get_read_int_cli_output_tool(session),
            get_run_int_cli_command_tool(session),
            get_read_int_cli_transcript_tool(session),
            openai_read_pdf_tool, openai_read_image_tool, web_search_tool,
        ]

        super().__init__(
            name="madgraph_operator",
            system_prompt=MADGRAPH_OPERATOR_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
