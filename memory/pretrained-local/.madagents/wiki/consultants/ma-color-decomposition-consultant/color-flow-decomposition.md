---
description: color_flow_decomposition / get_color_flow_string — leading-N color-flow extraction (T-with-2-indices form) used downstream for LHE color tags; supported reps, the fake-index offset scheme, and error conditions.
---

# Color-flow decomposition (leading-N)

`$MADGRAPH_INSTALL/madgraph/core/color_amp.py:379-529`. This is the algebra that
PRODUCES the per-diagram color-flow data; the actual LHE color-tag emission and
`leshouche.inc` generation are output-slice territory.

## get_color_flow_string (`:379-440`, staticmethod)
Takes a color string + a list of external octet/sextet index descriptors;
returns the **leading-N** color-flow string (only T's with exactly 2 indices,
plus Epsilon/EpsilonBar). Algorithm:
- adds one T per external octet (contracts octet → triplet/antitriplet pair),
  K6 per antisextet, K6Bar per sextet (`:388-407`).
- `full_simplify` with `Epsilon.rule_eps_aeps_nosum` forced **False** via
  `misc.TMP_variable` (`:409-410`) — the nosum rule is incompatible with LC.
- keeps strings with the **max Nc_power** (`:418-420`) = leading-N. If more than
  one leading string and they are not `near_equivalent`, raises ColorBasisError
  (`:423-425`).
- validates result contains only 2-index T's / Epsilon (`:431-438`), else error.

## color_flow_decomposition (`:442-529`)
For each color-basis key, returns a dict {external leg number → [c1, c2]} flow
tags: (0,0) singlet, (X,0) triplet, (0,X) antitriplet, (X,Y) octet.
- Supported reps only: `abs(leg_repr) in [1,3,6,8]` (`:471-472`), else
  ColorBasisError "unsupported color representation".
- Fake-index offset scheme for octets/sextets: offset1=1000, offset2=2000,
  offset3=3000 (`:452-454`), used to introduce fake quark indices; flow offset
  starts 500 (`:489`). Sextets encoded with negative triplet numbers
  (`:512-518`).
- Initial-state legs (`key <= ninitial`) have their [c1,c2] **reversed**
  to match the Les Houches convention (`:520-525`).

CAUTION: this is a LEADING-N (large-Nc color-flow) decomposition only — it
discards subleading-color strings. Correct for color-tag assignment, not for
the full squared ME (that is the ColorMatrix). Reps outside {1,3,6,8} are
unsupported and hard-error.
