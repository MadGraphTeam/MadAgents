#########################################################################
## Backend constants ####################################################
#########################################################################

BASE_WORKER_AGENTS = {
    "script_operator",
    "researcher",
    "pdf_reader",
    "madgraph_operator",
    "plotter",
    "user_cli_operator",
    "physics_expert",
}

REVIEWER_AGENTS = {"plan_reviewer", "verification_reviewer", "presentation_reviewer"}

KNOWN_AGENT_NAMES = BASE_WORKER_AGENTS | {
    "planner",
    "plan_updater",
    "orchestrator",
} | REVIEWER_AGENTS

INTERRUPT_USER_MESSAGE = "I interrupt the workflow."

APP_CONFIG_KEY = "global"

RUNS_DB_PATH = "/runs/runs.sqlite"
CHECKPOINTS_DB_PATH = "/runs/checkpoints.sqlite"
