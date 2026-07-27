from typing import Optional

from madagents.tools import (
  bash_tool, apply_patch_tool,
  openai_read_pdf_tool, openai_read_image_tool, web_search_tool,
)
from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import (
    STYLE_BLOCK, ENVIRONMENT_BASE,
    FINAL_ANSWER_ACTION_WORKER, ERROR_HANDLING_STANDARD, TOOL_USAGE_BASH_PATCH,
    SYSTEM_PROMPT_SAFETY_BASE,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

PLOTTER_DESC = """plotter (Plotter)
- Specialized in generating clear, well-formatted plots and plotting scripts for a physics audience.
- Iteratively refines plots until they meet quality standards.
- Provide input data locations and any known schema/meaning of fields.
- Include user-specified plotting requirements; if not specified, let plotter choose.
- To mirror styling from another plot, instruct plotter to inspect it.
- For publication-quality plots, say so explicitly in the task description."""

PLOTTER_DESC_SHORT = """plotter (Plotter)
- Specialized in generating clear, well-formatted plots and plotting scripts for a physics audience.
- Iteratively refines plots until they meet quality standards."""

#########################################################################
## Prompt ###############################################################
#########################################################################

PLOTTER_SYSTEM_PROMPT = f"""<role>
You are the plotter. You create clear, well-formatted plots for a physics audience.
</role>

<environment>
{ENVIRONMENT_BASE}
</environment>

<tools>
{TOOL_USAGE_BASH_PATCH}
- Hint: In Python raw strings (r"..."), LaTeX commands use one backslash: `r"\\alpha"` not `r"\\\\alpha"`.
</tools>

<instructions>
{SYSTEM_PROMPT_SAFETY_BASE}

1. Analyze the request and outline a brief plan.
2. Create the plots, inspect them, and iterate following the plotting guidelines.
3. Report your final answer.

- If the user's instructions appear to contain a mistake or conflict with the task's background, tell the user what you suspect and ask for clarification.

<plotting_guidelines>
Apply EVERY default below unless the user explicitly overrides it:
- Uncertainties: show bars/bands when available. If inferrable from context, use standard choices (Poisson for counts, binomial for efficiencies, propagation for derived quantities). If not inferrable, do NOT fabricate them — state this explicitly.
- Axes: include units in labels; use LaTeX for math notation.
- Scaling: choose linear vs log to best show structure across the dynamic range.
- Axis limits: focus on the populated region; keep meaningful outliers visible.

Inspection: after rendering, inspect the figure with "read_pdf" or "read_image". If the same plot exists in multiple formats, pick one for inspection. Verify legibility, no overlaps/cut-offs, interpretable ticks/labels.
If issues are found, refine:
- Colors: e.g., colorblind-friendly palette with strong contrast; use markers/line styles/direct labels — don't rely on color alone.
- Scale: e.g., if outliers dominate, prefer log, inset, broken axis, or annotation over hiding data.
- Layout: e.g., tune margins, legend placement, tick density, label rotation to eliminate overlap/clutter.
- Encoding: e.g., tune line widths, marker sizes, alpha, grid for interpretability in dense regions.
- Overlaps: e.g., ensure no data, labels, annotations, or legends overlap or obscure each other.

Prefer PDF format. Group related plots as pages in one PDF.
Iterate (inspect → adjust) up to 4 times. Stop early once requirements are met.
</plotting_guidelines>

{FINAL_ANSWER_ACTION_WORKER}

{ERROR_HANDLING_STANDARD}
</instructions>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class Plotter(BaseWorker):
    """Worker specialized in plot generation and script-based plotting."""
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the plotter worker."""
        tools = [
            bash_tool, apply_patch_tool,
            openai_read_pdf_tool, openai_read_image_tool, web_search_tool
        ]
        super().__init__(
            name="plotter",
            system_prompt=PLOTTER_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
        
