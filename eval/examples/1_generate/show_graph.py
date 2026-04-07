#!/usr/bin/env python3
"""Save a PNG visualization of the question generation graph."""
from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parents[2] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from eval.generate import build_generate_graph


def main():
    graph = build_generate_graph()  # no session → visualization mode
    png_bytes = graph.get_graph().draw_mermaid_png()
    out = Path(__file__).resolve().parent / "generate_graph.png"
    out.write_bytes(png_bytes)
    print(f"Saved: {out}  ({len(png_bytes)} bytes)")


if __name__ == "__main__":
    main()
