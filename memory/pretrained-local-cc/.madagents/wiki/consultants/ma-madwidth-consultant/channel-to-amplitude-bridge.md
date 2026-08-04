---
description: How enumerated decay channels become DecayAmplitude subprocesses for the MadEvent survey — get_amplitudes per body-level, same-final-state grouping, ON-SHELL-only selection, and amplitude-level min_br pruning.
---

# Channel → amplitude → subprocess bridge (v3.7.1)

The link between channel ENUMERATION (channel-enumeration-bodydecay page) and the MadEvent SURVEY (compute-widths-flow page). After channels are enumerated they are grouped into `DecayAmplitude` objects (one per distinct final state = one MadEvent subprocess), collected into `self._curr_amps`, then output as `madevent` and surveyed.

## do_decay_diagram drives the collection (madgraph/interface/madgraph_interface.py:10130)
Per requested pid (skip if `width.lower()=='zero'`, 10191-10192):
- **Integer body_decay** (10195-10206): `find_channels(part, level, min_br)` enumerates ALL levels up front, then `part.get_amplitudes(l)` for l=2..level, each `extend`-ed into `self._curr_amps`.
- **Float body_decay** (10207-10234): `model.find_all_channels(2, generate_abstract=False)` once (first pid), collect `get_amplitudes(2)`; then the precision `while` loop — each iteration `find_channels_nextlevel(model, min_br)`, `get_amplitudes(clevel)`, `extend` `_curr_amps`, `update_decay_attributes`.
- `_generate_info` is set from `_curr_amps[0]['process'].nice_string()[9:]` (10239-10241). If `_curr_amps` empty → "No decay is found" (10246).

## get_amplitudes(partnum) (decay_objects.py:706)
Returns `self.get('decay_amplitudes')[partnum]` — a `DecayAmplitudeList` keyed by body-count. Missing key → `[]` (a body-level with no channels contributes nothing). So `decay_amplitudes` is a dict {n_body → list of amplitudes}; the per-level lists are built by `group_channels_2_amplitudes`.

## group_channels_2_amplitudes (decay_objects.py:1138) — the grouping rule
- **ONLY on-shell channels become amplitudes**: iterates `get_channels(clevel, True)` (1159) — the `(clevel, True)` ChannelList. Off-shell channels `(clevel, False)` are NOT turned into survey subprocesses (they exist only as scaffolding for building higher on-shell levels and for the apx error estimate). This is a key selection: a decay that is only ever off-shell at a given level produces no MadEvent subprocess there.
- **Same-final-state grouping** (1162-1177): channels are bucketed by `sorted([leg.id for final legs])`. A channel whose sorted final PIDs match an existing amplitude's final legs is folded in via `add_std_diagram` for each symmetric channel (1172-1173); otherwise a NEW `DecayAmplitude(channel, model)` is started (1182-1183). So one amplitude = one distinct final state = one MadEvent subprocess, possibly multiple Feynman diagrams.
- "NO CALCULATION of branching ratio at this stage" (docstring 1141) — apx_br is computed only for the min_br cut.

## Amplitude-level min_br pruning (decay_objects.py:1184-1197)
If `min_br` is nonzero: for each amplitude, `br = amp.apx_decaywidth / part.apx_decaywidth` (1192); if `br.real < min_br` the amplitude is REMOVED from `decay_amplitudes[clevel]` (1196). So min_br prunes whole final-state subprocesses whose estimated BR is below threshold BEFORE the survey — they never get integrated. (Integer body_decay path: min_br defaults to 0, so no pruning; float default min_br = (body_decay%1)/5 — see channel-enumeration page, noting the help-text ÷4 vs code ÷5 discrepancy.)

## Cautions
- **Off-shell channels never become subprocesses.** Only `(clevel, True)` on-shell channels group into amplitudes. If you expect a numerically-integrated contribution from an off-shell intermediate, it is captured at a LOWER on-shell multiplicity (cf. gauge-dependence drop), not as its own subprocess.
- min_br pruning is on the ESTIMATED br (apx_decaywidth ratio), not the surveyed one — a channel whose crude estimate undershoots min_br is dropped and never integrated, even if its true BR would exceed min_br. The estimator's accuracy (apx-matrixelement-estimator page) thus bounds completeness.
- `generate_abstract=False` is passed on the float path (10213): the abstract-model amplitude machinery (AbstractModel / Ab2RealDict, decay_objects.py 4999/5962) is bypassed here; the concrete per-pid DecayAmplitudes drive the survey. The abstract path is a separate optimization, not the default compute_widths route.
- **The AbstractModel cluster is DEAD in production compute_widths.** `generate_abstract=True` and `generate_abstract_model()` / `generate_abstract_amplitudes()` appear ONLY in `tests/unit_tests/various/test_decay.py` (e.g. 4203 `find_all_channels(3, generate_abstract=True)`); the live `do_decay_diagram` calls `find_all_channels(2, generate_abstract=False)` (madgraph_interface.py:10213) exclusively, and the integer body_decay path uses `find_channels` which never touches the abstract model at all. So the ~1000-line AbstractModel / Ab2RealDict / AbstractHelasMatrixElement cluster (decay_objects.py classes 4999, 5962, 6020, 6032, 6059) is a test-exercised-only optimization scaffold (group amplitudes sharing Lorentz+color structure into reusable abstract matrix elements) that NEVER runs in a real compute_widths/calculate_decay_widths invocation. Don't reason about width behavior through it — the concrete per-pid DecayAmplitude → MadEvent-subprocess path is the only production route. (Confirmed: tree-wide grep for `generate_abstract=True` / `generate_abstract_model` outside decay_objects.py returns only test_decay.py.)
