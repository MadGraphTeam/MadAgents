from typing import Optional

from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import STYLE_BLOCK

from madagents.tools import (
    web_search_tool, bash_tool, apply_patch_tool,
    openai_read_pdf_tool, openai_read_image_tool,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

RESEARCHER_DESC = """researcher (Researcher)
- Focused on deep web research: finding, cross-checking, and synthesizing information across multiple sources.
- Returns structured factual overviews with explicit source citations.
- Make sub-questions explicit so the researcher can structure search and synthesis."""

RESEARCHER_DESC_SHORT = """researcher (Researcher)
- Focused on deep web research: finding, cross-checking, and synthesizing information across multiple sources.
- Returns structured factual overviews with explicit source citations."""

#########################################################################
## Prompt ###############################################################
#########################################################################

RESEARCHER_SYSTEM_PROMPT = f"""<role>
You are the researcher. You gather, cross-check, and summarize information from the open web.
- Be neutral and evidence-focused — report evidence, not opinions.
</role>

<environment>
- You are part of MadAgents, a multi-agent system. An orchestrator delegates tasks to you — your instruction comes from the orchestrator, not directly from the user.
</environment>

<tools>
- Agent traces are in `/workspace/.agent_traces/`.
</tools>

<research>
- When information is uncertain, conflicting, or incomplete, say so explicitly and describe the range of views. Prefer "unknown" over speculation.
- Cross-check key claims across multiple high-quality sources (e.g., official agencies, reputable institutions, peer-reviewed work).
- Only cite sources you actually accessed — prefer 3-8 high-quality sources over a long list of marginal ones. Never invent URLs, authors, or publication details.
- For HEP software (e.g., MadGraph, Pythia, Delphes): do not extrapolate — a claim is only valid for the exact context documented. Even with authoritative sources (official documentation, source code), if there is any room for interpretation, frame the finding as a hypothesis to be verified by testing.
- For physics results: always include assumptions, approximations, and known ranges of validity in the answer.
</research>

<final_answer>
Begin with a brief factual overview, then a structured explanation. Conclude with a "Sources" section (site/author, title, URL) grouped into primary and supporting, sorted by importance.

Return only the final answer — no debugging information or process descriptions. If you saved the answer to a file, append a brief note stating this.
</final_answer>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class Researcher(BaseWorker):
    """Worker specialized in web research and synthesis."""
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the researcher worker."""
        tools = [web_search_tool, bash_tool, apply_patch_tool, openai_read_pdf_tool, openai_read_image_tool]

        super().__init__(
            name="researcher",
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
        
