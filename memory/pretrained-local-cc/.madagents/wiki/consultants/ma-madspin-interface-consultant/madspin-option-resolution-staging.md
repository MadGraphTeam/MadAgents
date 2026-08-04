---
description: PRINCIPLE — MadSpin option sentinels resolve lazily at option-specific sites (banner-derived at do_import; seed/input_format at the launch dispatch target), and seed is further mutated during generation. Reading options['X'] gives different values pre-import / post-import / post-launch.
---

# Option-resolution staging — when a MadSpin option holds its real value

Deeper principle lifted from `madspin-options`, `madspin-import-resolution`,
`madspin-bridge-onshell-launch-io`, and `madspin-launch-and-decay`. Those pages each
document one resolution site; this page names the connecting rule and the sites they
do NOT individually cover.

## Principle
Every MadSpin **sentinel/auto** option resolves **lazily at its first point of need**, and
the **site is option-specific**. There is no single "resolve all defaults" step. Therefore
`madspin_cmd.options['X']` can hold three different values across an interface's lifetime:
the raw card/default value, the import-resolved value, and the launch/generation-mutated value.
A caller that reads an option must know *which stage* it is reading at.

Boundary: this is about the **interface-level option value** (what a caller reads off
`self.options[...]`), which is in slice. How decay.py *consumes* a resolved value
(BW off-shell sampling, max-weight estimation math) is MadSpin internals, out of slice.

## Stage 1 — `do_import`, banner-derived (interface_madspin.py:243-266)
Resolved ONCE from the input LHE run-card banner (or the no-banner fallback):
- `Nevents_for_max_weight` (:248 banner / :263 no-banner fallback)
- `nb_sigma` (:250 / :264 no-banner fallback)
- `BW_cut` (:252 from bwcutoff / :266 no-banner fallback)
- `frame_id` (:258 from run_card LO / :260 forced to the NLO frame id) — read all no-banner fallbacks fresh at their lines.

See `madspin-import-resolution` for the formulas and the NWA-threshold critical.

## Stage 2 — launch dispatch target, runtime-derived
Resolved at do_launch / run_bridge / run_onshell — NOT at import:
- `input_format='auto'` -> from **filename** (`.lhe`/`.hepmc`) in run_bridge/run_onshell (:855-861).
  Distinct from the do_import `.lhe`-tail check used only by the pure-decay shortcut (:217-218).
- `seed=0` (sentinel) -> a random seed within the seed-space bound (bound read fresh at its site), at **five** distinct derivation sites with
  subtly different mechanics. Three are the launch-dispatch entry points:
  - full/madspin path: `self.options['seed']` directly (:659)
  - run_bridge: `self.options['seed']` directly (:895)
  - run_onshell: uses attribute `self.seed`, set via `do_set` (:1434-1435), then mirrors
    into `self.options['seed']` at :1443 — the attribute is authoritative here, not the dict.
  ...and two more inside `generate_events` (Stage 3) that only fire if the seed is *still*
  falsy when a decay subprocess is built:
  - inline regime: `if not self.seed -> self.seed = random.randint(...)`, then `do_set`
    + history insert (:1330-1334) — same shape as run_bridge but on the attribute.
  - gridpack-driven (ME-mother) regime: `self.seed = <offset> + self.mother.run_card['iseed']`
    (:1356 — offset read fresh), falling back to random if no mother (:1358); wraps modulo the seed-space bound (:1360-1361).
    This is the only seed *derived from the production run-card* rather than picked fresh.

## Stage 3 — mutation DURING generation (the case no instance page covered)
- **seed is incremented per decay-generation call**: inside `generate_events`,
  `run_card["iseed"] = self.options['seed']` (:1276) then `self.options['seed'] += 1` (:1283-1284).
  So each decayed PDG's ME-generation subprocess gets a distinct seed offset, and
  `options['seed']` after launch is NOT the seed recorded in the madspin banner block
  (which captured the pre-increment value via `history.insert` at launch time).
- **run_onshell has its OWN Nevents_for_max_weight fallback** (:1450-1452): if it reads 0
  (e.g. a no-banner edge that import didn't resolve), it defaults to a hardcoded local value
  (:1450-1452 — read fresh) — a second safety net independent of the do_import resolution.

## Why this catches more than the instances
The instance pages document stage-1 (import-resolution) and the stage-2 input_format/seed
*entry* points. None document: the per-PDG seed increment (:1283), the run_onshell attribute-vs-dict
seed quirk (:1443), or the run_onshell local Nevents fallback (:1450). A caller asking
"what seed did decay sample N use?" or "why does options['seed'] differ from the banner?"
is answered only by this staging view.

## Caller-facing consequences
- Do not read a sentinel option's value before `do_import` and assume it is final.
- The seed in the output madspin banner block is the launch-time value; `options['seed']`
  read afterward is higher by the number of decayed PDGs.
- input_format may still be `'auto'` after import (it only resolves in the none/onshell launch
  target); the full/madspin path never resolves it because it does not go through run_bridge.

## Source-grounding note
All sites here are source-visible assignment/control-flow facts (interface_madspin.py @ 3.7.1),
not runtime predictions — verified by reading the assignment sites, no probe required.
