#!/usr/bin/env bash
# MadAgents — pick a run and start it.
#
#   ./madrun.sh                 interactive: choose an existing run or start a
#                               new one (memory + name), then launch the session
#   ./madrun.sh --resume        same, and forward --resume to claude
#   ./madrun.sh --list          list your runs and exit
#
# Anything this script does not recognise is forwarded verbatim to claude, so
# --resume / --continue / --model all work.
#
# Permissions are yours to choose: the shipped agent system pre-approves
# nothing, so a plain run asks before each tool use. The container runs as your
# own user (no fakeroot) with your home directory mounted, so bypassing those
# checks is a real decision — make it explicitly, per run:
#
#   ./madrun.sh --dangerously-skip-permissions      # unattended, no prompts
#
# Non-interactive shortcuts (skip the menu):
#
#   ./madrun.sh --new --name ttbar-study --memory pretrained
#   ./madrun.sh --fork run_dir/instances/ttbar-study__<stamp>
#   ./madrun.sh --instance run_dir/instances/ttbar-study__<stamp>
#   ./madrun.sh --new --setup-only          build it, do not start a session
#
# Memory packs (see memory/README.md): pretrained (default, Anthropic models),
# pretrained-local (+ Claude Code know-how, self-hosted models), bare-local, none.
# A pack is COPIED into the run, so the session extends its own copy and
# memory/<pack>/ in this repo stays fixed.
#
# Each run is a self-contained folder under run_dir/instances/ with its own
# memory, its own sparse overlay and its own lock: different runs work
# concurrently, the same run cannot be started twice.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec env PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
     python3 -m launcher run "$@"
