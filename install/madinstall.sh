#!/usr/bin/env bash
# MadAgents installer — a Claude Code session that installs the agent system into
# a folder of your choice, to be run without a container.
#
#   ./install/madinstall.sh             start the installer session
#   ./install/madinstall.sh --resume    anything unrecognised is forwarded to claude
#
# Host-side: no Apptainer, no image, no container. It reads this repository and
# writes the folder you name.
#
# It drives a plain script, so you can skip the conversation entirely:
#   python3 install/installer.py --list-memory
#   python3 install/installer.py ~/my-study --memory pretrained
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$SCRIPT_DIR"
exec claude "$@"
