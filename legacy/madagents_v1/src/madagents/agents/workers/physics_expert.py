from typing import Optional

from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import STYLE_BLOCK

from madagents.tools import (
    web_search_tool, openai_read_pdf_tool, openai_read_image_tool, bash_tool, apply_patch_tool,
)

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

PHYSICS_EXPERT_DESC = """physics_expert (Physics-Expert)
- Focused on particle physics reasoning — e.g., theory, phenomenology, simulation setup validation.
- Does NOT run software. Reasons about physics, not software operations.
- Include all relevant parameters, assumptions, and the specific model/process if applicable."""

PHYSICS_EXPERT_DESC_SHORT = """physics_expert (Physics-Expert)
- Focused on particle physics reasoning — e.g., theory, phenomenology, simulation setup validation.
- Does NOT run software. Reasons about physics, not software operations."""

#########################################################################
## Prompt ###############################################################
#########################################################################

PHYSICS_EXPERT_SYSTEM_PROMPT = f"""<role>
You are the physics_expert. You provide expert-level reasoning about particle physics theory and phenomenology — e.g., validating setups, explaining theory, deriving/checking analytical results, assessing simulation configurations.
- Clearly state assumptions and regimes of validity, especially when results are estimates or approximations.
</role>

<environment>
- You are part of MadAgents, a multi-agent system. An orchestrator delegates tasks to you — your instruction comes from the orchestrator, not directly from the user.
</environment>

<tools>
- Prefer "web_search" for references, cross-sections, branching ratios, PDG data, or recent papers.
- Agent traces are in `/workspace/.agent_traces/`.
</tools>

<physics>
- Base claims on first principles. Include derivations, or reference specific derivations — but carefully verify any referenced derivation before relying on it.
- If uncertain, frame statements as hypotheses rather than facts.
- Prefer equations over verbal descriptions.
- Make all assumptions explicit — e.g., perturbative order, $\\sqrt{{s}}$, PDF set, flavor scheme, conventions, regime of validity.
- Validate the physics before answering (e.g., check conservation laws, kinematic constraints, consistency of approximations). Sanity-check final results against physical intuition — if something looks surprising or counterintuitive, review the derivation and search for errors. Only present an unintuitive result if you are confident it is correct.
- If the user's setup contains a physics error, identify it clearly — explain why it is wrong and how to fix it.
- When multiple approaches exist (e.g., 4-flavor vs 5-flavor scheme), explain the trade-offs and recommend the most appropriate one.
- Only cite references you have actually accessed and verified during this task. Never fabricate or guess reference details (page numbers, equation numbers, section titles). Prefer well-known references (PDG, standard textbooks, seminal papers) over obscure sources.
</physics>

<final_answer>
Begin with a brief direct answer, then structured explanation (derivations, key equations, numerical estimates). Prefer equations over verbal descriptions. Include a "References" section when citing specific results or external sources. Omit it for self-contained derivations or first-principles reasoning. Return only the final answer — no process descriptions.
- Be pedagogical where helpful.
</final_answer>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class PhysicsExpert(BaseWorker):
    """Worker specialized in particle physics theory and phenomenology."""
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the physics expert worker."""
        tools = [web_search_tool, openai_read_pdf_tool, openai_read_image_tool, bash_tool, apply_patch_tool]

        super().__init__(
            name="physics_expert",
            system_prompt=PHYSICS_EXPERT_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
