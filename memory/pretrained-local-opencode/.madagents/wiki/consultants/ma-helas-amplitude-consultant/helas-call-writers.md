---
description: helas_call_writers.py structure — lambda-dict call dispatch, get_call_key, Fortran/UFO/GPU writer hierarchy, zerowidth_tchannel, hel_sum/format_helas_object, GPU multi_channel_map interleave.
---

# HELAS call writers (helas_call_writers.py)

Cites `$MADGRAPH_INSTALL/madgraph/iolibs/helas_call_writers.py` and `.../core/helas_objects.py` (v3.7.1). This file emits the per-wf/per-amp CALL lines into `matrix_*.f`; the ALOHA routines those CALLs target are the aloha slice.

## Class hierarchy
- `HelasCallWriter(base_objects.PhysicsObject)` @38 — base. Holds two dicts `'wavefunctions'`/`'amplitudes'` mapping a call-key → a lambda(wf|amp)→string. `mother_dict` @48 = spin-state→letter for EXTERNAL legs: `{1:'S', 2:'O', -2:'I', 3:'V', 5:'T', 4:'OR', -4:'IR', ...}`.
- `FortranHelasCallWriter(HelasCallWriter)` @357 — legacy FR-model special calls (UVVAXX/JVTAXX/GGGGXX/JGGGXX hard-coded @383-446). `self_dict` @367 = spin→internal-letter `{1:'H',2:'F',-2:'F',3:'J',5:'U'}`; `sort_wf`/`sort_amp` @369-370 order mother letters.
- `UFOHelasCallWriter(HelasCallWriter)` @967 — UFO-model base (ALOHA-named routines).
- `FortranUFOHelasCallWriter(UFOHelasCallWriter)` @1020 — **production tree-level Fortran writer**. `__init__(argument, hel_sum=False, options)` @1030.
- `FortranUFOHelasCallWriterOptimized(FortranUFOHelasCallWriter)` @1348 — loop/MadLoop output (madloop slice); get_coef_construction_calls / get_loop_CT_calls.
- `CPPUFOHelasCallWriter` @1608 / `GPUFOHelasCallWriter(CPPUFOHelasCallWriter)` @1742 — C++/CUDA (MadGraph4GPU). `PythonUFOHelasCallWriter` @2045 — Python output.

## Dispatch mechanism — lambda dictionary keyed by get_call_key
- `get_wavefunction_call(wf)` @276 / `get_amplitude_call(amp)` @295: `self["wavefunctions"][wf.get_call_key()]` → lambda → string. **KeyError → returns "" silently** @282-283 (no error; an unregistered Lorentz structure emits nothing). Auto-gen via `generate_helas_call` caches the lambda so the next wf with the same structure reuses it (docstring @668-671).
- `get_call_key` (helas_objects.py @1719): `(tuple(sorted mother spin-state numbers + own spin-state + outgoing-number [+ loop index/is_part] + tuple(polarization) + onshell [+ conjugate_indices if hermitian]), tuple(lorentz))`. So the key folds together mother spins, own spin, vertex outgoing position, polarization, onshell, and the lorentz-name list — wfs differing only in those reuse the same emitted-call lambda.
- An amplitude with `interaction_id == 0` (the trivial/identity amp) emits a comment `#` line @681-687.

## get_matrix_element_calls @219 (base path)
1. Loop ME → delegates to `get_loop_matrix_element_calls` @228 (loop wfs are NOT recycled — see wavefunction-recycling page).
2. `matrix_element.reuse_outdated_wavefunctions(me)` @232 — assigns `me_id` memory slots (see wavefunction-recycling page) BEFORE emitting.
3. Per diagram: emit each wf's call, a `# Amplitude(s) for diagram number N` comment, then each amp's call.
- me_id is the W() slot in every Fortran template (`wf.get('me_id')`); amp templates use `amp.get('number')` for AMP().

## External legs (generate_helas_call @652/@1105)
No-mother wf → `IXXXXX/OXXXXX/VXXXXX/SXXXXX(P(0,n), [mass,NHEL(n),] sign*IC(n), W(1,me_id))` @691-725. Scalar: no mass/hel slot. Boson sign = `(-1)**(state=='initial')`; fermion sign = `-(-1)**get_with_flow('is_part')` (particle/antiparticle, flow-aware). Internal wfs use `self_dict`+sorted mother letters+lorentz name; WWWW/WWVV vertices special-case the mother letters to `WWWW`/`W3W3` @739-745. A hermitian-conjugate flag is appended when `needs_hermitian_conjugate()` @750 (Majorana/charge-conj — fermion-flow-clash-majorana page).

## zerowidth_tchannel — default-True width rewrite at emission
`get_wavefunction_call` @288-292: when `self.options['zerowidth_tchannel']` (default True, set in __init__ @343) AND `wf.is_t_channel()`, the emitted call string is regex-rewritten `, fk_<width> ,` → `, ZERO ,` (skips `fk_ZERO`), and `width_tchannel_set_tozero` is flagged. So t-channel propagator widths are forced to zero IN THE EMITTED CALL regardless of the param_card width — a source-visible default that changes the Fortran. (Width semantics/BW are the bw-window/mc-integration slices; this is only the emission rewrite.)

## hel_sum / format_helas_object — the W(1,i,H) form for helicity recycling
`FortranUFOHelasCallWriter.__init__(hel_sum=False)` @1030. `format_helas_object(prefix, number)` @1038: if `hel_sum` → `"{prefix}{number},H)"` else `"{prefix}{number})"`. So with hel_sum the W/AMP arrays carry an extra helicity index `H` — this is the indexed-array layout that helicity recycling (hel_recycle.py, see helicity-recycling-output page) reads/writes. Default False emits the plain per-call layout.

## set_octet_majorana_coupling_sign at emit time
`UFOHelasCallWriter.get_wavefunction_call` @986 calls `wf.set_octet_majorana_coupling_sign()` before building the call (extra minus on FVI/FSI for octet Majorana in UFO models). `FortranUFOHelasCallWriter.get_amplitude_call` @1047 does the same for LoopHelasAmplitude wfs; the *Optimized* subclass deliberately skips it (@1352-1359, calls grandparent). Connects to fermion-flow-clash-majorana page (sign lives on the wf, applied at emission).

## GPU writer — interleaved jamp/amp2/multi_channel
`GPUFOHelasCallWriter.get_matrix_element_calls(me, color_amplitudes, multi_channel_map=False)` @1974: after `reuse_outdated_wavefunctions`, walks diagrams and, per amplitude, sets `amp.number=1` (single amp register), emits the call, then:
- if the amp's id is the first amp of a config in `multi_channel_map`: emits `if(channel_id==i){multi_chanel_num += conj(amp[0])*amp[0];}` and always `multi_chanel_denom += ...` @2030-2032 — the single-diagram-enhanced multichannel weight (config ↔ first-amp mapping built @2010-2015).
- accumulates `jamp[njamp] += coeff*amp[0]` from the color_amplitudes coeff list @2034-2036.
GPU external (`get_external_line` @1803) uses **0-indexed** `me_id-1`/`number_external-1` (C arrays) and special-cases massless external fermions into `pzxxxx/mzxxxx/xzxxxx` momentum-direction routines @1850-1867.

## Cautions
- KeyError-on-missing-call → silent empty string @282-283: a Lorentz structure with no registered/auto-generated lambda drops its line with no diagnostic.
- `misc.sprint(...)` debug lines are live in the GPU path @2002/@2016 and get_external_line @1828-1834 — emit to stderr at output time (cosmetic, but visible).
- hel_sum and zerowidth_tchannel both change the emitted Fortran from the "naive" form; the actual matrix_*.f content depends on which writer + flags the exporter chose — confirm by reading the generated file, not by assuming defaults.
