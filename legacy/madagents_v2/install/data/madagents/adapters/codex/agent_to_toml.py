#!/usr/bin/env python3
"""Convert a neutral MadAgents agent file (Markdown + frontmatter) to a Codex agent TOML.

Reads an already-rendered agent `.md` (container-only blocks stripped, {{DOCS}} substituted)
and writes a Codex `.codex/agents/<name>.toml` to stdout with:
    name, description           -> from the YAML frontmatter
    developer_instructions      -> the Markdown body

`developer_instructions` uses a TOML multiline *literal* string (''' ... ''') so backslashes
in the body (LaTeX like \\alpha, \\sqrt) are kept verbatim. A basic string ("...") would
treat them as escapes and break parsing.
"""
import json
import re
import sys

text = open(sys.argv[1]).read()
m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
if not m:
    sys.exit(f"agent_to_toml: no frontmatter in {sys.argv[1]}")
front, body = m.group(1), m.group(2).strip("\n")

name_m = re.search(r"^name:\s*(.+?)\s*$", front, re.M)
desc_m = re.search(r"^description:\s*(.+?)\s*$", front, re.M)
if not name_m or not desc_m:
    sys.exit(f"agent_to_toml: missing name/description in {sys.argv[1]}")

name = name_m.group(1).strip().strip('"')
desc = desc_m.group(1).strip()
if desc.startswith('"') and desc.endswith('"'):
    desc = desc[1:-1]

if "'''" in body:
    sys.exit(f"agent_to_toml: body of {sys.argv[1]} contains ''' — cannot use a literal string")

# json.dumps yields a valid TOML basic string for plain text (same \\" / \\n / \\uXXXX escapes).
out = (
    f"name = {json.dumps(name)}\n"
    f"description = {json.dumps(desc)}\n"
    "developer_instructions = '''\n"
    f"{body}\n"
    "'''\n"
)
sys.stdout.write(out)
