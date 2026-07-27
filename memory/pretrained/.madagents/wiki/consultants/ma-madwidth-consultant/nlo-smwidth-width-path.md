---
description: The --nlo / auto@NLO compute_widths path routes to compute_widths_SMWidth — an external Fortran program (smwidth), EW-scheme-dependent, wholly distinct from the LO survey engine; early-return bypasses find_channels/survey entirely.
---

# NLO width via SMWidth (v3.7.1)

All citations `madgraph/interface/madgraph_interface.py` unless noted. This is the OTHER width engine: `--nlo` does NOT run the LO channel-enumeration + MadEvent survey at all. It shells out to a precompiled Fortran program `smwidth` shipped inside the model. Wholly separate code path from everything on compute-widths-flow / channel-enumeration / apx-* pages.

## How `auto@NLO` reaches `--nlo` (runtime)
`common_run_interface.py:7301` `do_compute_widths`: regex `decay\s+(\+?\-?\d+)\s+auto(@NLO|)` (case-insensitive) over the param_card text. `has_nlo = any("@nlo"==nlo.lower() for _, nlo in pdg_info)` (7304). If any decay line is `DECAY <pid> auto@NLO`, it appends `--nlo` to the forwarded line (`if has_nlo: line += ' --nlo'`, 7311-7312). So the per-particle `@NLO` suffix in the card is what selects the NLO engine — it is a card-level, not a command-level, choice in the runtime path. (The bare REPL caller must pass `--nlo` explicitly.)

## Dispatch — early return, LO engine bypassed (madgraph_interface.py:9839)
```
if '--nlo' in line:
    self.compute_widths_SMWidth(line, model=model)
    return
```
- The check is a raw substring test on `line` (9839), evaluated AFTER the decay-model import at 9833 (`import_ufo.import_model(modelname, decay=True)` still runs — the DecayModel is built even though NLO never uses it) but BEFORE `check_compute_widths` parses opts (9844). The `return` at 9842 means `find_channels`, `do_decay_diagram`, the survey, and ALL apx machinery are skipped. body_decay / precision_channel / min_br options are PARSED inside compute_widths_SMWidth (via its own check_compute_widths, 10034) but never used — SMWidth has no notion of body-level or channel pruning.

## compute_widths_SMWidth (10029)
1. **auto→1 dummy** (10036-10049): same as the LO path — any `param.value=="auto"` in the card is set to `1` (float) and the card rewritten (to `--output` if set, else overwrite `--path`). The unit dummy is just so the Fortran reads a numeric width; it is overwritten by the result.
2. **EW-scheme detection** (10063-10074): inspects the model's external parameters.
   - `('sminputs','aewm1')` present → `arg2="1"` (alpha(MZ) scheme).
   - `('sminputs','mdl_gf')` or `('sminputs','gf')` present → `arg2="2"` (Gmu scheme).
   - neither → `raise Exception("Do not know the EW scheme in the model %s")`. So a model lacking a recognizable EW input set cannot do NLO widths at all.
3. **Model-must-ship-SMWidth gate** (10060-10061): `if not os.path.exists(pjoin(model_path,'SMWidth')): raise InvalidCmd("Model %s is not valid for computing NLO width with SMWidth")`. The Fortran source tree lives inside the model dir; absent → hard fail.
4. **Compile-on-first-use** (10077-10088): if `SMWidth/smwidth` binary absent, logs "Compiling SMWidth. This has to be done only once and can take a couple of minutes." Recompiles `SMWidth`, `SMWidth/oneloop`, `SMWidth/hdecay` if the fortran_compiler differs from what the makefile_MW5 was built with, then `misc.compile`. So the FIRST `--nlo` call in a fresh install pays a multi-minute compile; subsequent calls reuse the binary.
5. **ident_card.dat** (10090-10094): if present in the card dir, passed as second arg; else a single space `" "`.
6. **Run** (10096-10099): `misc.Popen(['./smwidth', opts['path'], identpath, arg2], cwd=SMWidth_dir)` — three positional args: param_card path, ident_card path (or " "), EW-scheme code. The Fortran reads/writes via stdout.
7. **Parse output** (10100-10104): regex `  decay\s+(\+?\-?\d+)\s+(\+?\-?\d+\.\d+E\+?\-?\d+)` over smwidth's stdout → `width_dict[pid] = float(width)`. SMWidth emits its own `decay <pid> <width>` lines.

## Result write-back — different from the LO path
Per requested pid (10106-10119):
- **Unresolved pid → 0** (10107-10108): `if not pid in width_dict: width = 0`. A particle smwidth didn't report gets width ZERO, silently. (Contrast LO: an unreported pid means no channels / 0 too, but via the survey, and the LO path's small-width warnings fire downstream.)
- Sets `param.value = width`, `param.format='float'` directly on the in-memory ParamCard (10111-10113).
- **HDECAY citation for pid 25** (10114-10116): if Higgs (pid 25) is among the requested particles, logs in bold: "You are using program 'HDECAY', please cite refs: hep-ph/9704448, arXiv:1801.09506 [hep-ph]." So the Higgs NLO width comes from HDECAY bundled inside SMWidth — a different program than the EW one-loop for other particles.
- **BR-table RESET** (10117-10119): `if pid in param_card['decay'].decay_table: del param_card['decay'].decay_table[pid]`. The NLO path WIPES the per-pid BR sub-block — it writes ONLY a total width, NO branching-ratio decay lines. (The LO survey path, by contrast, writes BR sub-lines from `update_width_in_param_card`.) A param_card after `--nlo` has bare `DECAY <pid> <total>` with no `# BR  NDA  ID1 ID2` children for that pid.
8. **Write** (10120-10126): to `--output` if set, else overwrite `--path`; logs "Results are written in %s".

## Cautions
- **No BRs from the NLO path.** `--nlo` gives a total width only and deletes any existing BR table for that pid. If a downstream step (MadSpin, decay chain) needs branching ratios, the NLO width path does not supply them — only the total. Don't expect BR lines in a card computed with `auto@NLO`.
- **Model-gated.** Only models shipping a `SMWidth/` Fortran tree can do `--nlo`; otherwise `InvalidCmd`. Whether a given install's models ship it is install-dependent — do a live `ls models/*/SMWidth` rather than assuming. (In this install's bundled models the directory was absent at scan time; treat presence as a per-model, per-install live-scan fact.)
- **EW-scheme exception** is a hard fail for models without `aewm1`/`gf` in sminputs — a BSM model with a non-standard EW input block cannot use SMWidth even if it ships the tree.
- **Unresolved pid silently → 0** — no warning at the SMWidth parse stage; a typo'd or unsupported pid just gets zero width.
- **First-call compile cost** — the multi-minute SMWidth compile happens lazily on the first `--nlo` invocation per install; not a runtime bug, but a surprising first-call latency.

## Boundary
- The LO engine (survey, channels, apx) is everything else in this subtree; this page owns ONLY the `--nlo`/SMWidth branch.
- The `auto@NLO` card-line FORMAT (how the suffix is written/read in SLHA) is the param-card slice; this page owns only the regex that the width code uses to detect it.
- NLO width *physics* (one-loop EW, HDECAY internals) is out of scope — auto-width consultant owns the MG-side dispatch, not the Fortran physics.
