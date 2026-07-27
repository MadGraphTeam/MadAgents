#!/usr/bin/env bash
# MadAgents against a self-hosted model — see local/README.md.
#
#   ./local/madrun.sh                 start a session on your own endpoint
#   ./local/madrun.sh --resume        forwarded to claude, as usual
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
