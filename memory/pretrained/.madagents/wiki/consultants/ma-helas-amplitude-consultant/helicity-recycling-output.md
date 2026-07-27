---
description: Helicity recycling at output time — HelicityRecycler / DAG / MathsObject in hel_recycle.py, the good_helicity skip, matrix_orig→matrix_optim rewrite, and the gen_ximprove driver feeding good_hels/bad_amps.
---

# Helicity recycling at output time

Cites `$MADGRAPH_INSTALL/madgraph/madevent/hel_recycle.py`, `.../madevent/gen_ximprove.py`, `.../various/banner.py` (v3.7.1).

## What it does
Rewrites a per-helicity matrix routine so that wavefunctions/amplitudes shared across helicity combinations are computed once and recycled, and zero-contributing helicities are skipped. Runs at OUTPUT/optimization time (after a survey), NOT per-event MC over helicity (that is the mc-integration slice).

## Symbolic representation (hel_recycle.py)
- `DAG` @34 — dependency graph: `store_wav`, `add_branch`, `dependencies`, `find_path`, `kill_old`, `old_names`. external_wavs tracked.
- `MathsObject` @98 — base for symbolic amplitude nodes; `good_helicity` @137 decides whether a wav/amp's external dependency set is in an allowed `External.good_wav_combs` (@141), and for amps also drops `(hel_number, diag_number) in bad_hel_amp` @152.
- `External` @194 (good_hel/map_hel/hel_ranges), `Internal` @296, `Amplitude` @337 — `generate_wavfuncs`/`generate_amps` regenerate only good-helicity instances @307-311 / @352-363.

## HelicityRecycler @383
`__init__(good_elements, bad_amps=[], bad_amps_perhel=[], gauge='U')` @386 — resets External/Internal/Amplitude class counters. Defaults input/output `matrix_orig.f`, template `template_matrix.f`. `hel_filt=True` @429.
- `set_input` @432 **hard-exits** if filename contains `born_matrix` — recycler cannot handle born_matrix.f.
- `generate_output_file` @737 drives read_orig → read_template → write; `write_zero_matrix_element` @728 for the all-zero case.
- `good_elements`/`bad_amps`/`bad_amps_perhel` are the surviving helicity indices, zero amplitudes, and per-helicity zero amps respectively.

## Driver — gen_ximprove.py
```
recycler = hel_recycle.HelicityRecycler(good_hels, bad_amps, bad_amps_perhel, gauge=gauge)   # @306
recycler.hel_filt   = run_card['hel_filtering']   # @308
recycler.amp_splt   = run_card['hel_splitamp']    # @309
recycler.amp_filt   = run_card['hel_zeroamp']     # @310
```
- `good_hels` from a `madevent_forhel` survey: `all_good_hels` built @232-234, `good_hels = sorted(all_good_hels[me_index])` @288.
- `bad_amps`/`bad_amps_perhel` only when `run_card['hel_zeroamp']` (guard @289-295 region).
- If only ONE good helicity, skip optimization — just cp matrix_orig→matrix_optim (`len(good_hels)==1` @300).

## amp_splt — hel_splitamp amplitude splitting (split_amps @788)
The `hel_splitamp` knob (`recycler.amp_splt`, gen_ximprove @309) factorizes an amplitude CALL over the wavefunction column that appears in the MOST amplitudes, so a contracted wf is reused across helicities via a `CombineAmp` call.
- @792-809: counts wf occurrences per amplitude-argument column; the column with the max distinct wfs (`to_remove` @807) is factored out.
- @830-842: emits `<fct>P1N_<to_remove+1>(...)` (the partial-N HELAS variant) with the result slot replaced by `TMP(1)`, accumulating helicity/wf index lists.
- **Gauge-dependent CombineAmp suffix** @850-857: `spin=='F'` OR (`spin=='V'` AND gauge!='FD') → `CombineAmp` (no suffix); `spin=='S'` → `CombineAmpS`; `spin=='V'` AND gauge=='FD' → `CombineAmpFD`. **Spin-3/2 and spin-2 raise** `"split amp not supported for spin2, 3/2"` @857 — amplitude splitting is unavailable for those, the recycler aborts.
- gauge passed from `HelicityRecycler.__init__(gauge='U')` @386/@430 → `split_amps(..., gauge=self.gauge)` @616. 'FD' = Feynman-diagram gauge (goldstones present, vector propagator carries the extra term); 'U' (unitary, default) and others share the plain CombineAmp path for vectors.

## run_card knobs (banner.py)
- `limhel` — numeric threshold below which a helicity is deemed non-contributing (when not MC over helicity); default registered at `banner.py:4310`, read the current value fresh at that line (don't cache it).
- `hel_filtering` — pre-filter zero helicities during per-helicity optimization; default registered at `banner.py:4455`, read fresh at that line.
- `hel_splitamp` / `hel_zeroamp` — drive amp_splt / amp_filt above (read in gen_ximprove @309-310).

## Cautions
- born_matrix.f is explicitly unsupported by HelicityRecycler — NLO born routines do not get this output-time recycling.
- The good/bad helicity sets are RUNTIME survey products (madevent_forhel), so the optimized routine content cannot be predicted from source alone — requires a launch to observe.
