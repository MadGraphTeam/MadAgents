#!/usr/bin/env python3
"""Save a PNG visualization of the answer evaluation graph."""
from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parents[2] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from eval.answer import build_answer_graph


def main():
    graph = build_answer_graph()  # no session/supervisor → visualization mode
    png_bytes = graph.get_graph().draw_mermaid_png()
    out = Path(__file__).resolve().parent / "answer_graph.png"
    out.write_bytes(png_bytes)
    print(f"Saved: {out}  ({len(png_bytes)} bytes)")


if __name__ == "__main__":
    main()
