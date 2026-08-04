#!/usr/bin/env bash
# MadAgents against a self-hosted model — see local/README.md.
#
#   ./local/madrun.sh                 interactive: choose an existing run or
#                                     start a new one, then launch it
#   ./local/madrun.sh --list          list your runs and exit
#   ./local/madrun.sh --new --memory pretrained-local-opencode --name qwen-study
#   ./local/madrun.sh --fork run_dir/instances/qwen-study__<stamp>
#   ./local/madrun.sh --resume        forwarded to the CLI, as usual
#
# Same menu as the repo-root ./madrun.sh, and the same runs: instances live in
# run_dir/instances/ either way, and the BACKEND column says which start path a
# run was built for. A run's backend is fixed when it is built, so resuming one
# from here starts it however it was built — as does resuming it from there.
#
# Configure the endpoint in local/config.env (copy local/config.env.example).
# Everything else — image, overlay, run instances, memory packs — is shared
# with the normal ./madrun.sh in the repo root.
#
# This is a SEPARATE launcher on purpose. The root ./madrun.sh strips every API
# key and endpoint variable from the container, always; that guarantee is not
# weakened to support this case. The two paths share the container machinery
# and nothing about auth.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -f "${SCRIPT_DIR}/config.env" ]]; then
  echo "local/config.env not found." >&2
  echo "  cp local/config.env.example local/config.env   # then set LOCAL_MODEL_BASE_URL" >&2
  exit 2
fi

# Both the shared launcher package and this one need to be importable.
exec env PYTHONPATH="${REPO_ROOT}/src:${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}" \
     python3 -m launcher_local run "$@"
