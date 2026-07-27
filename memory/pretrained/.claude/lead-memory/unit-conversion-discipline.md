---
name: unit-conversion-discipline
description: "When reporting MadGraph cross sections in non-pb units, verify the conversion with explicit arithmetic"
metadata: 
  node_type: memory
  type: feedback
  scope: "fires when user requests non-pb units (fb, ab, cm2)"
---

**When reporting a MadGraph cross section in units other than pb, verify the conversion by computing it — don't convert in your head.**

MadGraph's native output unit is picobarns (pb). Common conversions:
- 1 pb = 10³ fb
- 1 fb = 10³ ab
- 1 pb = 10⁶ ab

**Why:** Head-converting powers of ten between pb/fb/ab is a recurring error mode — a factor of 1000 mistake (reporting 0.358 fb instead of 3.58e-4 fb for a 3.576e-07 pb result) is the exact failure that happens.

**How to apply:** When the user asks for fb (or any non-pb unit), compute: `σ_fb = σ_pb × 1000`. Write the arithmetic out or use `python` — the point is the conversion is an explicit step, not a mental one. Report the result in the requested units, but show the original pb value in a parenthetical so the lead can trace it: `(3.58 ± 0.0003) × 10⁻⁴ fb (3.576e-07 pb)`.

Link: [[ma-numerics-consultant]] owns numerical evaluation; this is a lead-level post-processing check that fires before the number leaves the answer.