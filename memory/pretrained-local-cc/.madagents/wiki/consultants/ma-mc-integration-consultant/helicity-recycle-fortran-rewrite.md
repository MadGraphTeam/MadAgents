---
description: HelicityRecycler source-to-source write mechanism — read_orig line state-machine, reference-counting dead-call elimination, split_amps gauge-dependent CombineAmp emission, template substitution + 72-column continuation, symlink zero-ME path. v3.7.1.
---

# HelicityRecycler Fortran rewrite mechanism (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/madevent/hel_recycle.py` (943 lines). Complements `helicity-recycling.md` (which covers the gensym *discovery* of good helicities and the `MathsObject` DAG node taxonomy). This page is the **write side**: how `matrix*_optim.f` is actually produced from `matrix*_orig.f`. Driver: `generate_output_file` (737) → `read_orig` (667) → `read_template` (718).

## Driver and short-circuits (generate_output_file, 737)
- If `self.good_elements` is empty → `write_zero_matrix_element` (728): `os.remove(output)` then `os.symlink(orig.f, optim.f)` — the optim file is a **symlink to the orig**, NOT a copy (734). Distinct from the 1-good-helicity path in gensym (gen_ximprove.py:300-301) which `files.cp`s BOTH the `.f` and the `.o` and skips the recycler entirely.
- Otherwise `read_orig` (parse + transform into `template_dict`) then `read_template` (substitute into template, write output).
- `clean_up` (748) is a no-op; registered/unregistered via `atexit` around the read (743-746).

## read_orig — line-by-line state machine (667)
Iterates the orig file line by line (with `tqdm` progress, 673). Per-line handling:
- **line 0** cached, skipped (674-676).
- `'!SKIP'` lines dropped (678-679).
- **Continuation join**: if `line[5] == '$'` (Fortran continuation marker in col 6), `undo_multiline(line_cache, line)` (687) merges it into the cached line — collapses multi-line HELAS/AMP calls to ONE logical line before parsing. `undo_multiline` (879): strips first 6 chars of the continuation, concatenates.
- **One-line lookahead**: `line, line_cache = line_cache, line` (690) — always processes the *previous* physical line, so the continuation-merge can complete first.
- Dispatch chain per logical line (692-696): `get_old_name` (find FUNCTION/SUBROUTINE output var), `get_good_hel` (parse `DATA (NHEL...`), `get_amp_stuff` (track diagram/jamp/amp2 regions), `function_call` (classify external/internal/amplitude), `get_gwc` (trigger `External.get_gwc()` good-wav-comb computation at the external→non-external boundary).
- If `call_type in {external, internal, amplitude}`: `unfold_helicities` (563) returns the new DAG objects; appended to `template_dict['helas_calls']` (700).

### function_call classifier (449)
- No `'CALL'` → None. `CALL OXXXXX/IXXXXX/VXXXXX/SXXXXX` → `'external'`. Otherwise, if the called function name ends in `_0` → `'amplitude'`, else `'internal'` (478-481). So amplitude calls are recognized by the `_0` HELAS-vertex naming convention.

## Reference-counting dead-call elimination (704-716)
After parsing, a **reverse pass** over `helas_calls`: any object with `nb_used == 0` is blanked (`obj.line = ''`) and each of its DAG dependencies (`obj.linkdag`) has `nb_used` decremented (705-710). This is a transitive DCE: dropping an unused amplitude can cascade to drop the internal wavefunctions feeding only it. `nb_used` is incremented in `unfold_helicities` (587, 605) whenever a downstream object consumes a wavefunction. Surviving lines are emitted with a `! count <nb_used>` annotation (714). Result: zero-helicity / zero-amplitude HELAS calls never appear in `matrix_optim.f`, and so are never evaluated at integration time.

## get_good_hel — NHEL table rewrite (633)
- Accumulates every `DATA (NHEL...` row into `self.all_hel` (636-637).
- At the end of the NHEL block: if `hel_filt`, `External.good_hel = {all_hel[i-1]: i for i in good_elements}` — keeps only the surveyed-good combos (642); else keeps all (644).
- `nhel_string` (660) re-emits each kept combo as `DATA (NHEL(I,counter),I=0,nexternal) /old_id, h1,h2,.../` — **element 0 is the ORIGINAL helicity index** `old_id`, so the compiled code can recover the pre-filtering index. `ncomb` set to `len(good_hel)` (658).

## split_amps — gauge-dependent amplitude splitting (788, fires when amp_splt True)
Called from `apply_amps` (614) only if `self.amp_splt`; else plain `apply_args`. Restructures a set of amplitudes sharing wavefunctions into one shared HELAS call plus a `CombineAmp` reduction:
- Finds the wavefunction column that occurs the most across the amps and removes it from the product key (`to_remove`, 807-809); products over the remaining columns group amps (814-817).
- For a group >1, emits a single `<fct>P1N_<to_remove+1>(...)` call (842) computing the shared piece into `TMP`, then a `CombineAmp<suffix>` call (859-867) folding the per-helicity results back into `AMP(1,iamp)`.
- **suffix is spin/gauge-determined** (850-857): `F` or (`V` and gauge≠`FD`) → `''` (`CombineAmp`); `S` → `'S'` (`CombineAmpS`); `V` and gauge==`FD` → `'FD'` (`CombineAmpFD`). Spin 2 / 3/2 → `raise Exception("split amp not supported for spin2, 3/2")`. The spin char comes from the HELAS function name (`fct.split(None,1)[1][to_remove]`, 841). `gauge` is passed in from `proc_characteristics['gauge']` (gen_ximprove.py:305).

## read_template — substitution + 72-column reflow (718)
- Python `string.Template(line).safe_substitute(template_dict)` per template line (722-723) — fills `${helicity_lines}`, `${helas_calls}`, `${jamp_lines}`, `${amp2_lines}`, `${ncomb}`, `${nwavefuncs}` (defaults init'd in `__init__` 410-415; `nwavefuncs = max(num_externals, max_wav_num, External.max_wav_num)` set at 703).
- `do_multiline` (884) reflows any substituted line exceeding **72 chars** into Fortran continuation lines (`\n     $<indent>` joins, 900), preserving an inline `!` comment by splitting it off first (885-888). The `len(line) != 72` guard (891) skips exactly-72 lines.

## Recycler does NOT bypass line-wrapping — cannot be the >132 "Line truncated" locus (correction)
A cross-slice handoff suspected the HelicityRecycler emits verbatim Fortran (CALL/DATA lines) exceeding the 132-char fixed-form limit for a many-coupling model, bypassing the FortranWriter's 71-char wrap. SOURCE refutes: `read_template` (724) does `line = '\n'.join([do_multiline(sub_lines) for sub_lines in line.split('\n')])` — it splits the substituted block on `\n` and runs `do_multiline` (884) over **every** sub-line, including the injected `${helas_calls}` / `${jamp_lines}` / `${helicity_lines}` blocks AND the template scaffold lines. `do_multiline` reflows any line >72 chars into raw 72-char chunks joined with `\n     $<indent>` (char_limit=72, 889). Worst-case emitted physical line = 6 (`     $`) + indent + ≤72 ≈ under 90 chars for the single-digit indents in matrix files — never approaches 132. So the recycler's output cannot be the >132 truncation source; its 72-char reflow MATCHES (does not bypass) the writer discipline. The zero-ME path just symlinks `orig.f` (writer-wrapped). mc-integration side is CLEARED — a genuine >132 line is a writer-bypassing hardcoded/hand-`Template` `.f`/`.inc` (output slice), not the recycler. (`gen_ximprove` emits input_app/run scripts, not matrix Fortran.)

## Flag wiring (caution)
`__init__` (386) sets `self.hel_filt = True` (429) but does NOT initialize `self.amp_splt` or `self.amp_filt`. Those are set ONLY by the caller:
- gensym path (gen_ximprove.py:308-310): `hel_filt = run_card['hel_filtering']`, `amp_splt = run_card['hel_splitamp']`, `amp_filt = run_card['hel_zeroamp']`.
- CLI `main()` (917): `--hf-off`/`--as-off` flip `hel_filt`/`amp_splt` (default True); `amp_filt` never set in the CLI path.

**Caution:** calling `generate_output_file()` on a fresh `HelicityRecycler` without setting `amp_splt` first will `AttributeError` inside `apply_amps` (615 reads `self.amp_splt`). The recycler is not standalone-callable with defaults — it expects a configuring caller. (Source-visible; a runtime AttributeError of this exact shape is HYPOTHESIS until probed.)

## Other cautions
- `set_input` (432) hard-`exit(1)`s on any filename containing `born_matrix` — NLO Born matrix files are not handled by the recycler (433-436). LO-only mechanism.
- The recycler assumes the orig file's column-6 continuation marker is `$` (686) and that AMP-call functions end in `_0` (480). These are conventions of the MG-generated `matrix*_orig.f`; a hand-edited or differently-templated matrix file would mis-parse silently.
- `add_indices` (497): the `re.sub(r'\WAMP\(.*?\)', ...)` non-greedy match "Doesnt work if the AMP arguments contain brackets" (per the in-source docstring, 500) — a noted limitation, not currently triggered by standard output.
