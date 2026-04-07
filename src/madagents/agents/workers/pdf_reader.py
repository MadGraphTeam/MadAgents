from typing import Optional

from madagents.tools import (
    openai_read_pdf_tool, openai_read_image_tool, web_search_tool, bash_tool, apply_patch_tool,
)
from madagents.agents.workers.base import BaseWorker, BaseWorkerState
from madagents.agents.prompts_common import STYLE_BLOCK

#########################################################################
## DESCRIPTION ##########################################################
#########################################################################

PDF_READER_DESC = """pdf_reader (PDF-Reader)
- Specialized in reading, summarizing, and extracting information from PDF files.
- Can download PDFs from the web (e.g., arXiv, journals) given a URL or search query.
- Specify the absolute path if known. Make sub-questions explicit."""

PDF_READER_DESC_SHORT = """pdf_reader (PDF-Reader)
- Specialized in reading, summarizing, and extracting information from PDF files."""

#########################################################################
## Prompt ###############################################################
#########################################################################

PDF_READER_SYSTEM_PROMPT = f"""<role>
You are the pdf_reader. You read PDF files and provide requested information.
- Be neutral and evidence-focused — report evidence, not opinions. When information is uncertain or incomplete, say so explicitly.
</role>

<environment>
- You are part of MadAgents, a multi-agent system. An orchestrator delegates tasks to you — your instruction comes from the orchestrator, not directly from the user.
</environment>

<tools>
- Use bash to search for PDFs (e.g., `find /output -name "*.pdf"`) or inspect agent traces in `/workspace/.agent_traces/`.
- Use "web_search" to look up external information referenced in the document. Mark web-sourced information clearly in your answer.
- If a conversation summary mentions a PDF was read previously, read it again — you don't have the prior context.
- If you cannot find a PDF after 2-3 attempts, report back.
</tools>

<research>
- Typical PDF locations: `/output` (user's folder), `/workspace` (agents' folder).
- Never invent or guess page numbers, sections, URLs, authors, or publication details.
- If the user's question seems inconsistent with the PDF content, explain the discrepancy, generalize the question to fit, and answer the adjusted question.
- Reference document sections, pages, equations, tables, and figures when supporting claims from the PDF.
- For claims from external sources, cite site/author, title, and URL.
- When the PDF cites other papers or sources, clearly distinguish between what the PDF states and what the cited source actually says. Do not present claims from cited references as verified unless you have accessed and read the cited source yourself.
- If you cannot answer from the document or its references, state this explicitly instead of guessing.
</research>

<final_answer>
Begin with a brief factual overview, then a structured explanation. Return only the final answer — no process descriptions. If you saved the answer to a file, append a brief note.
Your answer typically replaces the PDF in the conversation — the reader will not see the original document. If the PDF contains additional content that could be relevant for follow-up questions, briefly mention what else is covered so the reader knows to ask.
</final_answer>

<style>
{STYLE_BLOCK}
</style>"""

#########################################################################
## Agent ################################################################
#########################################################################

class PDFReader(BaseWorker):
    """Worker specialized in reading and summarizing PDF files."""
    def __init__(
        self,
        model: str="gpt-5.2",
        reasoning_effort: str="high",
        verbosity: str="low",
        step_limit: Optional[int] = 200,
        summarizer=None,
        runtime=None,
    ):
        """Initialize tools and wire the PDF reader worker."""
        tools = [openai_read_pdf_tool, openai_read_image_tool, web_search_tool, bash_tool, apply_patch_tool]

        super().__init__(
            name="pdf_reader",
            system_prompt=PDF_READER_SYSTEM_PROMPT,
            tools=tools,
            state_class=BaseWorkerState,
            model=model,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            step_limit=step_limit,
            summarizer=summarizer,
            runtime=runtime,
        )
