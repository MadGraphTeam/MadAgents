from __future__ import annotations

from typing import Optional, Dict, List

from pydantic import BaseModel, Field, field_validator, model_validator

SUPPORTED_MODELS: List[str] = [
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-5.1",
    "gpt-5.2",
    "gpt-5.4",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]

SUPPORTED_PROVIDERS: List[str] = ["openai", "anthropic"]

VERBOSITY_LEVELS: List[str] = ["low", "medium", "high"]
REASONING_EFFORT_LEVELS: List[str] = ["minimal", "low", "medium", "high"]

OPENAI_MODEL_PREFIXES: tuple[str, ...] = ("gpt-",)
ANTHROPIC_MODEL_PREFIXES: tuple[str, ...] = ("claude-",)

OPENAI_MODELS: List[str] = [m for m in SUPPORTED_MODELS if m.startswith(OPENAI_MODEL_PREFIXES)]
ANTHROPIC_MODELS: List[str] = [m for m in SUPPORTED_MODELS if m.startswith(ANTHROPIC_MODEL_PREFIXES)]

# Model capability tiers for orchestrator routing decisions.
ANTHROPIC_MODEL_TIERS: Dict[str, tuple[str, str]] = {
    "claude-opus-4-7": ("strongest", "Complex reasoning, physics, domain expertise, code generation, failed retries"),
    "claude-opus-4-6": ("strongest", "Complex reasoning, physics, domain expertise, code generation, failed retries"),
    "claude-sonnet-4-6": ("mid-tier", "Read-only research, formatting, scratch-space work"),
    "claude-haiku-4-5": ("lightest", "Simple extraction, formatting, lookups, straightforward file ops"),
}

OPENAI_MODEL_TIERS: Dict[str, tuple[str, str]] = {
    "gpt-5.4": ("strongest", "Complex reasoning, physics, domain expertise, code generation, failed retries"),
    "gpt-5.2": ("strongest", "Complex reasoning, physics, domain expertise, code generation, failed retries"),
    "gpt-5.1": ("strongest", "Complex reasoning, physics, domain expertise, code generation, failed retries"),
    "gpt-5.4-mini": ("mid-tier", "Read-only research, formatting, scratch-space work"),
    "gpt-5-mini": ("mid-tier", "Read-only research, formatting, scratch-space work"),
    "gpt-5.4-nano": ("lightest", "Simple extraction, formatting, lookups, straightforward file ops"),
    "gpt-5-nano": ("lightest", "Simple extraction, formatting, lookups, straightforward file ops"),
}

# Worker-only agents that can be routed to by the orchestrator.
WORKER_AGENTS: List[str] = [
    "script_operator",
    "researcher",
    "pdf_reader",
    "madgraph_operator",
    "plotter",
    "user_cli_operator",
    "physics_expert",
]

REVIEWER_AGENTS: List[str] = ["plan_reviewer", "verification_reviewer", "presentation_reviewer"]

LOOP_AGENTS: List[str] = [*REVIEWER_AGENTS, *WORKER_AGENTS]

AGENT_ORDER: List[str] = [
    "orchestrator",
    "planner",
    "plan_updater",
    "summarizer",
    *REVIEWER_AGENTS,
    *WORKER_AGENTS,
]


_ALL_MODEL_TIERS: Dict[str, tuple[str, str]] = {**ANTHROPIC_MODEL_TIERS, **OPENAI_MODEL_TIERS}


DEFAULT_STRONGEST_OPENAI_MODEL: str = "gpt-5.2"
DEFAULT_STRONGEST_ANTHROPIC_MODEL: str = "claude-opus-4-7"


def _strongest_model_for_provider(
    orchestrator_model: str,
    provider: str,
) -> str:
    """Pick the strongest-tier representative for routing.

    If the orchestrator's model is already in the "strongest" tier for the
    provider, use it.  Otherwise fall back to a sensible default.
    """
    tier = _ALL_MODEL_TIERS.get(orchestrator_model, ("unknown",))[0]
    if tier == "strongest":
        return orchestrator_model
    if provider == "anthropic":
        return DEFAULT_STRONGEST_ANTHROPIC_MODEL
    return DEFAULT_STRONGEST_OPENAI_MODEL


def models_for_routing(
    models: List[str],
    strongest_model: str,
) -> List[str]:
    """Return one model per capability tier for orchestrator routing.

    When multiple models share a tier (e.g. gpt-5.4/5.2/5.1 are all
    "strongest"), only *strongest_model* is kept for that tier.  For other
    tiers the first model in *models* order wins.
    """
    strongest_tier = _ALL_MODEL_TIERS.get(strongest_model, ("unknown",))[0]
    tier_representative: Dict[str, str] = {strongest_tier: strongest_model}

    for m in models:
        tier = _ALL_MODEL_TIERS.get(m, ("unknown",))[0]
        tier_representative.setdefault(tier, m)

    # Preserve original ordering, keeping only the representative per tier.
    return [m for m in models if tier_representative.get(
        _ALL_MODEL_TIERS.get(m, ("unknown",))[0]
    ) == m]


def infer_provider_from_model(model: Optional[str]) -> Optional[str]:
    """Infer provider from model naming conventions."""
    if not isinstance(model, str) or not model.strip():
        return None
    normalized = model.strip().lower()
    if normalized.startswith(OPENAI_MODEL_PREFIXES):
        return "openai"
    if normalized.startswith(ANTHROPIC_MODEL_PREFIXES):
        return "anthropic"
    return None


class AgentConfig(BaseModel):
    model: str = Field(default="gpt-5.2")
    provider: Optional[str] = Field(default=None)
    verbosity: str = Field(default="low")
    reasoning_effort: Optional[str] = Field(default=None)
    token_threshold: Optional[int] = Field(default=None)
    keep_last_messages: Optional[int] = Field(default=None)
    min_tail_tokens: Optional[int] = Field(default=None)
    step_limit: Optional[int] = Field(default=None)
    supports_step_limit: bool = Field(default=True)

    @field_validator("model")
    @classmethod
    def _validate_model(cls, value: str) -> str:
        """Ensure the model name is in the supported list."""
        if value not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {value}")
        return value

    @field_validator("verbosity")
    @classmethod
    def _validate_verbosity(cls, value: str) -> str:
        """Ensure verbosity is one of the supported levels."""
        if value not in VERBOSITY_LEVELS:
            raise ValueError(f"Unsupported verbosity: {value}")
        return value

    @field_validator("provider")
    @classmethod
    def _validate_provider(cls, value: Optional[str]) -> Optional[str]:
        """Ensure provider is one of the supported values."""
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {value}")
        return normalized

    @field_validator("step_limit")
    @classmethod
    def _validate_step_limit(cls, value: Optional[int]) -> Optional[int]:
        """Validate that the step limit is a positive integer when provided."""
        if value is None:
            return value
        if not isinstance(value, int) or value <= 0:
            raise ValueError("step_limit must be a positive integer")
        return value

    @field_validator("reasoning_effort")
    @classmethod
    def _validate_reasoning_effort(cls, value: Optional[str]) -> Optional[str]:
        """Ensure reasoning effort is one of the supported levels."""
        if value is None:
            return value
        if value not in REASONING_EFFORT_LEVELS:
            raise ValueError(f"Unsupported reasoning effort: {value}")
        return value

    @field_validator("token_threshold", "keep_last_messages", "min_tail_tokens")
    @classmethod
    def _validate_positive_int(cls, value: Optional[int]) -> Optional[int]:
        """Validate optional positive integer fields."""
        if value is None:
            return value
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Value must be a positive integer")
        return value

    @model_validator(mode="after")
    def _normalize_config(self) -> "AgentConfig":
        """Normalize provider inference and clear step limits when unsupported."""
        inferred = infer_provider_from_model(self.model)
        if self.provider is None:
            self.provider = inferred
        elif inferred is not None and self.provider != inferred:
            raise ValueError(
                f"Provider {self.provider} does not match model {self.model} (expected {inferred})."
            )
        if not self.supports_step_limit:
            self.step_limit = None
        return self


class MadAgentsConfig(BaseModel):
    workflow_step_limit: int = Field(default=1000)
    require_madgraph_evidence: bool = Field(default=False)
    enable_worker_model_routing: bool = Field(default=False)
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)

    @field_validator("workflow_step_limit")
    @classmethod
    def _validate_workflow_step_limit(cls, value: int) -> int:
        """Validate the workflow step limit is a positive integer."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError("workflow_step_limit must be a positive integer")
        return value


def _default_agents() -> Dict[str, AgentConfig]:
    """Return the default AgentConfig set for all agents."""
    agents: Dict[str, AgentConfig] = {
        "orchestrator": AgentConfig(step_limit=None, supports_step_limit=False),
        "planner": AgentConfig(step_limit=200, supports_step_limit=True),
        "plan_updater": AgentConfig(
            model="gpt-5-mini",
            verbosity="low",
            step_limit=None,
            supports_step_limit=False,
        ),
        "summarizer": AgentConfig(
            step_limit=None,
            supports_step_limit=False,
            reasoning_effort="low",
            token_threshold=150_000,
            keep_last_messages=10,
            min_tail_tokens=10_000,
        ),
    }
    for reviewer in REVIEWER_AGENTS:
        agents[reviewer] = AgentConfig(step_limit=200, supports_step_limit=True)
    for worker in WORKER_AGENTS:
        agents[worker] = AgentConfig(step_limit=200, supports_step_limit=True)
    return agents


def default_config() -> MadAgentsConfig:
    """Build the default MadAgentsConfig."""
    return MadAgentsConfig(workflow_step_limit=1000, agents=_default_agents())


def apply_global_overrides(
    config: MadAgentsConfig,
    *,
    base_model: Optional[str] = None,
    orchestrator_model: Optional[str] = None,
    verbosity: Optional[str] = None,
) -> MadAgentsConfig:
    """Apply optional global overrides to a base config."""
    data = config.model_dump(mode="json")
    if base_model:
        # Override all agent models except the plan updater, which is smaller.
        for name, agent in data.get("agents", {}).items():
            if name == "plan_updater":
                continue
            agent["model"] = base_model
            agent["provider"] = infer_provider_from_model(base_model)
    if orchestrator_model and "orchestrator" in data.get("agents", {}):
        data["agents"]["orchestrator"]["model"] = orchestrator_model
        data["agents"]["orchestrator"]["provider"] = infer_provider_from_model(orchestrator_model)
    if verbosity:
        # Set verbosity uniformly across all agents.
        for agent in data.get("agents", {}).values():
            agent["verbosity"] = verbosity
    return MadAgentsConfig.model_validate(data)


def coerce_config(payload: Optional[dict]) -> MadAgentsConfig:
    """Coerce a loose dict payload into a validated MadAgentsConfig."""
    base = default_config()
    if not isinstance(payload, dict):
        return base

    data = base.model_dump(mode="json")

    if "workflow_step_limit" in payload:
        data["workflow_step_limit"] = payload.get("workflow_step_limit")
    if "require_madgraph_evidence" in payload:
        data["require_madgraph_evidence"] = bool(payload.get("require_madgraph_evidence"))
    if "enable_worker_model_routing" in payload:
        data["enable_worker_model_routing"] = bool(payload.get("enable_worker_model_routing"))

    agents_payload = payload.get("agents")
    if isinstance(agents_payload, dict):
        for name, agent_payload in agents_payload.items():
            if name not in data["agents"]:
                continue
            if not isinstance(agent_payload, dict):
                continue
            # Only apply known per-agent fields.
            for key in (
                "model",
                "provider",
                "verbosity",
                "step_limit",
                "reasoning_effort",
                "token_threshold",
                "keep_last_messages",
                "min_tail_tokens",
            ):
                if key in agent_payload:
                    data["agents"][name][key] = agent_payload.get(key)
            if not data["agents"][name].get("supports_step_limit"):
                # Ensure step_limit is cleared for unsupported agents.
                data["agents"][name]["step_limit"] = None

    return MadAgentsConfig.model_validate(data)
