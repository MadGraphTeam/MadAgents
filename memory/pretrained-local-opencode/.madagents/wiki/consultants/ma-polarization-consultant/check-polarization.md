---
description: check_polarization algorithm (Process.check_polarization) and its do_add caller — detection of ambiguous polarised/unpolarised mixes like p p > Z{T} Z and the abort prompt
---

# `check_polarization` — ambiguous polarised/unpolarised mix detection

## Method: `ProcessDefinition.check_polarization`
`$MADGRAPH_INSTALL/madgraph/core/base_objects.py:3869-3900` (v3.7.1). Defined on
**`ProcessDefinition`** (class at 3823, which subclasses `Process` at 2942) — `do_add`
calls it on `myprocdef`, a `ProcessDefinition`. Note the source has a typo `def  check_polarization` (two spaces) — greps for `def check_polarization` (single
space) miss it.
Docstring: "raise a critical information if someone tries something like
p p > Z{T} Z / return True if no issue and False if some issue is found".

Algorithm — builds dict `pol` keyed by final-state PID (initial-state legs skipped,
`if not leg.get('state'): continue`, 3877-3878). For each final-state leg:

- **Polarized leg** (`leg.get('polarization')` truthy, 3879-3890): for each PID in
  the leg's ids:
  - PID unseen → `pol[pid] = [leg.polarization]` (3881-3882).
  - this exact polarization list already recorded for the PID → skip, no issue
    (3883-3885).
  - else, for each helicity value `p` in this leg's polarization: if `p` appears in
    ANY already-recorded list `o` for that PID (`any(p in o for o in pol[pid])`) →
    **return False** (3887-3889). Otherwise append the new list (3890).
- **Unpolarized leg** (else, 3891-3898): for each PID:
  - PID unseen → record the placeholder full range `pol[pid] = [list(range(-3,4))]`
    i.e. `[[-3,-2,-1,0,1,2,3]]` (3893-3894).
  - already exactly that full-range placeholder → skip (3895-3896).
  - else (PID already had a *polarized* entry) → **return False** (3897-3898).

Returns True if no conflict (3900).

### What this means
- `p p > Z{T} Z` → False: same PID 23, first leg polarized [1,-1], second leg
  unpolarized → unpolarized branch sees PID already polarized → False.
- Two **identical** polarizations on the same PID (`Z{T} Z{T}`) → no issue (the
  "already present" skip).
- Two **disjoint** polarizations on the same PID → recorded, allowed only if helicity
  values don't overlap; overlapping values → False.
- Different PIDs never conflict with each other.

## Caller: `do_add` in madgraph_interface.py (3323-3333)
`if not myprocdef.check_polarization():` → `logger.critical(...)` with the message
(3325-3329, verbatim across concatenated strings):
"Not Supported syntax:\n   Syntax like p p  > Z{T} Z are ambiguious   Behavior is
not guarantee to be stable within future version of the code.   Furthemore, you can
have issue with symmetry factor (we do not guarantee [differential] cross-section.
We suggest you to abort this computation"

Then `ans = self.ask('Do you want to continue', 'no', ['yes','no'])` (3330) — default
'no'. If `ans == 'no'` → `InvalidCmd("Not supported syntax of type p p  > Z{T} Z")`
(3331-3332). 'yes' continues.

## Caution
- The prompt defaults to abort ('no'); a non-interactive/script run takes the default
  unless `yes`/answer is supplied — so an ambiguous-mix process aborts by default.
- Detection is **per-PID, helicity-value overlap based** — not a blanket "any
  polarized + any unpolarized". A polarized leg and an unpolarized leg for
  *different* PIDs do not trip it.
- The "symmetry factor" the warning text cites is concrete: `identical_particle_factor`
  (base_objects.py:3742-3755, key at 3750) keys identical legs on `(id, tuple(polarization))`, so a
  polarized + unpolarized copy of one PID are NOT treated as identical → no 1/n!
  factor → ambiguous differential cross-section. That is the mechanism this gate
  guards against — see `pol-symmetry-factor.md`.
