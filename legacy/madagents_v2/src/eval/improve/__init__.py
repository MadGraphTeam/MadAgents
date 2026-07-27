"""Improve phase: apply doc changes with verification loop.

Applies diagnosed documentation improvements, runs three parallel
checks (factual, style, quality), and revises until all pass or
max rounds reached.
"""
from eval.improve.improver import run_improve, MAX_ROUNDS

__all__ = [
    "MAX_ROUNDS",
    "run_improve",
]
