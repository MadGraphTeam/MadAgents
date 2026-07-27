from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver

from madagents.cli_bridge.bridge_handle import InstanceHandle
from madagents.cli_bridge.bridge_interface import CLISession, CLISessionManager

from madagents.config import (
    infer_provider_from_model,
    models_for_routing,
    _strongest_model_for_provider,
    MadAgentsConfig,
    default_config,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
)
from madagents.llm import LLMRuntime, get_runtime_for_provider

#########################################################################
## Config ###############################################################
#########################################################################

DEFAULT_WORKFLOW_STEP_LIMIT = 1_000
DEFAULT_REASONING_EFFORT = "high"
SUMMARIZER_REASONING_EFFORT = "low"
ORCHESTRATOR_REASONING_EFFORT = "high"

#########################################################################
## Agent ################################################################
#########################################################################

class MadAgents:
    """Main entry point that wires agents and runs the workflow graph."""
    def __init__(
        self,
        madgraph_bridge_dir: str,
        user_handle: InstanceHandle,
        checkpointer: BaseCheckpointSaver,
        config: Optional[MadAgentsConfig] = None,
    ):
        """Initialize LLM agents, workers, and the state graph."""
        if config is None:
            config = default_config()

        self.config = config
        self.runtime_registry: dict[str, LLMRuntime] = {}

        def _runtime_for(agent_cfg) -> LLMRuntime:
            provider = agent_cfg.provider or infer_provider_from_model(agent_cfg.model)
            if not provider:
                provider = "openai"
            cached = self.runtime_registry.get(provider)
            if cached is not None:
                return cached
            runtime_instance = get_runtime_for_provider(provider)
            self.runtime_registry[provider] = runtime_instance
            return runtime_instance

        self._init(config, _runtime_for, madgraph_bridge_dir, user_handle, checkpointer)

    def _init(self, config, _runtime_for, madgraph_bridge_dir, user_handle, checkpointer):
        """Set up agents and graph."""
        from madagents.agents.planner import Planner
        from madagents.agents.reviewer import Reviewer, REVIEWER_CONFIGS
        from madagents.agents.orchestrator import Orchestrator
        from madagents.agents.summarizer import Summarizer
        from madagents.agents.workers.script_operator import ScriptOperator
        from madagents.agents.workers.researcher import Researcher
        from madagents.agents.workers.pdf_reader import PDFReader
        from madagents.agents.workers.madgraph_operator import MadGraphOperator
        from madagents.agents.workers.user_cli_operator import UserCLIOperator
        from madagents.agents.workers.plotter import Plotter
        from madagents.agents.workers.physics_expert import PhysicsExpert
        from madagents.graph import build_graph

        orchestrator_cfg = config.agents["orchestrator"]
        planner_cfg = config.agents["planner"]

        orchestrator_runtime = _runtime_for(orchestrator_cfg)
        self.orchestrator = Orchestrator(
            model=orchestrator_cfg.model,
            reasoning_effort=ORCHESTRATOR_REASONING_EFFORT,
            verbosity=orchestrator_cfg.verbosity,
            runtime=orchestrator_runtime,
        )

        summarizer_cfg = config.agents["summarizer"]
        summarizer_effort = (
            summarizer_cfg.reasoning_effort
            if isinstance(summarizer_cfg.reasoning_effort, str)
            else SUMMARIZER_REASONING_EFFORT
        )
        summarizer_runtime = _runtime_for(summarizer_cfg)
        self.summarizer = Summarizer(
            model=summarizer_cfg.model,
            reasoning_effort=summarizer_effort,
            verbosity=summarizer_cfg.verbosity,
            token_threshold=summarizer_cfg.token_threshold or 150_000,
            keep_last_messages=summarizer_cfg.keep_last_messages or 10,
            min_tail_tokens=summarizer_cfg.min_tail_tokens or 10_000,
            runtime=summarizer_runtime,
        )

        planner_runtime = _runtime_for(planner_cfg)
        self.planner = Planner(
            model=planner_cfg.model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=planner_cfg.verbosity,
            step_limit=planner_cfg.step_limit,
            runtime=planner_runtime,
            summarizer=self.summarizer,
        )

        self.reviewers: dict[str, Reviewer] = {}
        for rev_name, rev_data in REVIEWER_CONFIGS.items():
            rev_cfg = config.agents[rev_name]
            rev_runtime = _runtime_for(rev_cfg)
            self.reviewers[rev_name] = Reviewer(
                name=rev_name,
                system_prompt=rev_data["system_prompt"],
                model=rev_cfg.model,
                reasoning_effort=DEFAULT_REASONING_EFFORT,
                verbosity=rev_cfg.verbosity,
                step_limit=rev_cfg.step_limit,
                summarizer=self.summarizer,
                runtime=rev_runtime,
            )

        worker_model = planner_cfg.model
        worker_verbosity = planner_cfg.verbosity

        script_cfg = config.agents["script_operator"]
        self.script_operator = ScriptOperator(
            model=script_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=script_cfg.verbosity or worker_verbosity,
            step_limit=script_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(script_cfg),
        )
        researcher_cfg = config.agents["researcher"]
        self.researcher = Researcher(
            model=researcher_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=researcher_cfg.verbosity or worker_verbosity,
            step_limit=researcher_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(researcher_cfg),
        )
        pdf_cfg = config.agents["pdf_reader"]
        self.pdf_reader = PDFReader(
            model=pdf_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=pdf_cfg.verbosity or worker_verbosity,
            step_limit=pdf_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(pdf_cfg),
        )
        plotter_cfg = config.agents["plotter"]
        self.plotter = Plotter(
            model=plotter_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=plotter_cfg.verbosity or worker_verbosity,
            step_limit=plotter_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(plotter_cfg),
        )

        physics_expert_cfg = config.agents["physics_expert"]
        self.physics_expert = PhysicsExpert(
            model=physics_expert_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=physics_expert_cfg.verbosity or worker_verbosity,
            step_limit=physics_expert_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(physics_expert_cfg),
        )

        self.cli_session_manager = CLISessionManager(
            base_dir=madgraph_bridge_dir,
            cli_cmd="bash",
            name_prefix="madgraph_cli",
        )
        madgraph_cfg = config.agents["madgraph_operator"]
        self.madgraph_operator = MadGraphOperator(
            session=self.cli_session_manager,
            model=madgraph_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=madgraph_cfg.verbosity or worker_verbosity,
            step_limit=madgraph_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(madgraph_cfg),
        )
        self.user_cli_session = CLISession(handle=user_handle)
        user_cli_cfg = config.agents["user_cli_operator"]
        self.user_cli_operator = UserCLIOperator(
            session=self.user_cli_session,
            model=user_cli_cfg.model or worker_model,
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            verbosity=user_cli_cfg.verbosity or worker_verbosity,
            step_limit=user_cli_cfg.step_limit,
            summarizer=self.summarizer,
            runtime=_runtime_for(user_cli_cfg),
        )

        self._closed = False

        workers = {
            "script_operator": self.script_operator,
            "researcher": self.researcher,
            "pdf_reader": self.pdf_reader,
            "plotter": self.plotter,
            "physics_expert": self.physics_expert,
            "madgraph_operator": self.madgraph_operator,
            "user_cli_operator": self.user_cli_operator,
        }

        workflow_limit = (
            config.workflow_step_limit
            if isinstance(config.workflow_step_limit, int) and config.workflow_step_limit > 0
            else DEFAULT_WORKFLOW_STEP_LIMIT
        )

        # Determine available models for worker model routing.
        # The "strongest" tier representative comes from the orchestrator's
        # model (which is typically the strongest).  If the orchestrator is
        # not on a strongest-tier model, we fall back to a sensible default.
        # The worker default (what you get when model=null) is the worker's
        # own configured model.
        enable_model_routing = bool(config.enable_worker_model_routing)
        available_worker_models = None
        default_worker_model = None
        if enable_model_routing:
            default_worker_model = script_cfg.model or worker_model
            provider = infer_provider_from_model(default_worker_model)
            all_provider_models = ANTHROPIC_MODELS if provider == "anthropic" else OPENAI_MODELS
            strongest = _strongest_model_for_provider(orchestrator_cfg.model, provider or "openai")
            available_worker_models = models_for_routing(all_provider_models, strongest)

        self.graph = build_graph(
            orchestrator=self.orchestrator,
            planner=self.planner,
            reviewers=self.reviewers,
            summarizer=self.summarizer,
            workers=workers,
            checkpointer=checkpointer,
            workflow_limit=workflow_limit,
            enable_worker_model_routing=enable_model_routing,
            available_worker_models=available_worker_models,
            default_worker_model=default_worker_model,
        )

    def close(self) -> None:
        """Attempt to terminate any active subprocesses and close resources."""
        if self._closed:
            return
        try:
            # Best-effort cleanup for any lingering subprocesses.
            from madagents.tools import terminate_processes_for_current_logs
            terminate_processes_for_current_logs()
        finally:
            if hasattr(self, 'cli_session_manager'):
                self.cli_session_manager.close_all()
            self._closed = True

    def __del__(self) -> None:
        """Best-effort cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass
