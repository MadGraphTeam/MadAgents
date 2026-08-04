---
description: You must read, parse, predict, or hand off the event file itself. Its records, its weights, its normalization.
---

# LHE event output format — fan-out

The "explain / parse / predict the LHE event file" question class spans the write path end-to-end. Route by which piece of the record the question is about. MadGraph facts live in `../consultants/<name>/`; confirm one cited `file:line` before adopting a page as evidence. Column facts are settled against `Source/rw_events.f` (LO writer) and `SubProcesses/unwgt.f` (LO record assembler).

## Owner map (by sub-question)

- **Record columns / format / where written** → `ma-output-consultant` — the LO writer templates `do_output` copies into `<PROC_DIR>`: `unwgt.f:write_leshouche` (assembles `jpart(7,nexternal)`) and `Source/rw_events.f:write_event` (formats the row, `format 51 = i11,5i5,5e19.11,f3.0,f4.0`; cols = IDUP, ISTUP=`ic(6)`, MOTHUP1-2, ICOLUP1-2, px,py,pz,E, mass, VTIMUP=hardcoded `0.`, SPINUP). Also owns `leshouche.inc`/ICOLUP generation (`export_v4.py:947 get_leshouche_lines`; colorless ME → all-zero ICOLUP, `:970-974` — no format axis drops color). Page: `lhe-event-output-and-leshouche.md`.
- **event_norm / XWGTUP normalization / weighted-vs-unweighted / nevents=0** → `ma-mc-integration-consultant` (LO) — default `event_norm=average` (`banner.py:4298`); per-mode weight in `lhe_parser.py:1224-1239` (average→each |wgt|=σ, lha_strategy ±4; sum→Σ=σ strat ±3; unity→±1 strat ±3). `nevents=0` → channel events discarded at combine (`madevent_interface.py:3909-3911`), no `unweighted_events.lhe`, σ still reported. Page: `lhe-event-writing-and-normalization.md`.
- **SPINUP value semantics** → `ma-mc-integration-consultant` owns the writer's three-source account: external legs → MC-selected helicity `nhel` (`unwgt.f:609`, ±1 for spin-½); reconstructed status-2 resonance records → `9` (`addmothers.f:332` "No helicity info for intermediate states"); Python `lhe_parser.Particle` default → `9` (`:94/117`). Route the letter→helicity *meaning* (esp. **`0` on a vector = longitudinal, not "averaged"**; `{L}`→-1; `{0}` for longitudinal) → `ma-polarization-consultant` `pol-spinup-lhe-seam.md`.
- **status-2 intermediate record (ISTUP=2)** → `ma-chain-decay-consultant` `lhe-status2-intermediate-resonance.md` owns the status *decision* (`addmothers.f:253`); the write is **runtime-gated by the `OnBW` test, NOT by decay-chain syntax**. The BW-window test + bwcutoff → `ma-bw-window-consultant` `bw-lhe-istup2-gating.md` (`myamp.f:136-147`; window is `bwcutoff×Γ_eff` with a Γ/M<0.1 narrow gate unless gForceBW=1). Which config's s-channel `sprop` is selected → `ma-phase-space-consultant` (configs.inc).
- **`<header>` (banner) block** → `ma-launch-consultant` `lhe-header-banner-assembly.md` — banner = run_card(`MGRunCard`)/param_card(`slha`)/MG5 version(`mgversion`)/proc info; written twice (standalone `_banner.txt` + inline LHE header via `lhe_parser.py:559`), unweight-time `modify_init_cross`+`set_lha_strategy`.
- **`<init>` block xsec / IDWTUP / NPRUP** → `ma-mc-integration-consultant` (LO, `banner.py:322-326/379-380`) / `ma-amcatnlo-consultant` (NLO).
- **`<rwgt>` / `<initrwgt>` reweighting weights** → `ma-systematics-consultant` `lhe-weight-indexing.md` — ids are **sequential from 1** (`sys.py:795`), scale/PDF combo lives in the `<weight>` **tag attributes** (MUR/MUF/PDF), not the numeric id. `use_syst=True` is a precondition (stores per-event info), not the reweighting engine (`systematics_arguments`+`do_systematics`).
- **NLO events.lhe.gz / signed weights / S-vs-H events** → `ma-amcatnlo-consultant` `nlo-lhe-event-format.md` — NLO file is `events.lhe.gz` (not `unweighted_events`); `event_norm`→IDWTUP (`driver_mintMC.f:669-688`: average→**-4** signed, sum/unity→**-3**); NLO events inherently signed/weighted; extra `#aMCatNLO` metadata line; S-events (nexternal-1, Born-projected) and H-events (nexternal) coexist in one file.
- **MadSpin's SPINUP/status rewrite** → `ma-madspin-interface-consultant` `madspin-lhe-record-rewrite.md` — decayed particle → status=2 always; its SPINUP is **spinmode-dependent** (`none`→**0** via `add_decay`; `onshell`/`full`/`madspin`→**9** via `add_decays`). Undecayed finals keep their production SPINUP; the ±1 magnitudes are decay.py-internal (out-of-slice GAP).
- **Pythia8 SPINUP handoff** → `ma-pythia8-interface-consultant` `spinup-tau-decay-handoff.md` — MG ships/writes **no** tau/SPINUP/`mayDecay` key; `15:mayDecay=no` is a user card edit; LHE→PY8 wired by `do_pythia8`→`setup_Pythia8RunAndCard` (`Beams:LHEF`), not `Pythia8Launcher` (that's standalone `output pythia8`). Pythia8's `TauDecays:mode`/`iTopCopyId` are Pythia8-internal — a GAP, not this slice.

## Doc-myth traps (this class reliably hits these)

Common LHE write-ups are frequently stale on exactly these points — do not ship them without routing to the owning page:

1. **"SPINUP=9 for most particles by default"** — WRONG. Externals carry the MC-selected helicity; `9` appears on reconstructed status-2 resonance records and as a parser default (three distinct sources above).
2. **"SPINUP 0.0 = averaged / 9.0 = no info"** — the `0` on a **vector** external is helicity-0 (longitudinal), a physical value, not "averaged."
3. **"intermediate written only with decay-chain syntax; interfering Z/γ has no unique intermediate → none written"** — WRONG. Runtime OnBW-gated: inclusive `e+ e- > mu+ mu-` at √s=M_Z (default bwcutoff) writes a status-2 Z in ~99% of events; off-window events omit it.
4. **"rwgt id=1001 encodes a scale/PDF index"** — WRONG for the systematics.py path (ids sequential from 1; scale/PDF in tag attributes). `1001` is the NLO-integrator convention (amcatnlo), not systematics.
5. **"use_syst=True does the reweighting"** — precondition only; the engine is `systematics_arguments`+`do_systematics`.
6. **"set 15:mayDecay=no (a MadGraph default)"** — it is a user edit; MG writes no tau-related pythia8_card key.
7. **"MadSpin assigns SPINUP=±1 to all finals; decayed→status2/SPINUP9"** — spinmode-dependent (`none`→SPINUP 0); undecayed finals keep production helicity.
8. **event_norm token trap** — the run_card accepts `unity` but the consumer compares against `unit` (`lhe_parser.py:519,1232`); whether `unity` silently no-ops/crashes is an open probe-candidate (`probe-backlog.md`). Prefer `unit` if a caller means ±1.
9. **NLO ≠ LO** — file name (`events.lhe.gz` vs `unweighted_events.lhe.gz`), signed weights, and S/H multiplicity coexistence all differ; never assume LO-unweighted semantics for an NLO LHE.

## Dispatch ordering

For a general "explain/predict the LHE" ask: core = **output** (format/columns) + **mc-integration** (SPINUP + event_norm weights), dispatched first; then branch by sub-question (status-2 → chain-decay+bw-window; header → launch; rwgt → systematics; NLO → amcatnlo; MadSpin/PY8 → the two interface slices). Pin **LO vs NLO first** — the file name, weight convention, and event-record structure all fork on it (mirrors `runcard-lo-nlo-value-divergence.md`).
