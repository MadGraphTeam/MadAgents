#!/usr/bin/env python3
"""Build madgraph-operator.md by concatenating the header with the
MadGraph software instructions (heading levels shifted by +1)."""

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

HEADER = SCRIPT_DIR.parent / "prompts" / "madgraph-operator.header.md"
MADGRAPH_MD = REPO_ROOT / "src" / "madagents" / "software_instructions" / "madgraph.md"
OUTPUT = SCRIPT_DIR.parent / ".claude" / "agents" / "madgraph-operator.md"


def shift_headings(text: str) -> str:
    """Shift Markdown headings by one level (# -> ##, ## -> ###, etc.)."""
    return re.sub(r"^(#+)", r"#\1", text, flags=re.MULTILINE)


def main():
    header = HEADER.read_text()
    madgraph = MADGRAPH_MD.read_text()

    # Ensure header ends with exactly one newline before appending
    header = header.rstrip("\n") + "\n"

    combined = header + "\n" + shift_headings(madgraph)
    OUTPUT.write_text(combined)
    print(f"Built {OUTPUT}")


if __name__ == "__main__":
    main()
