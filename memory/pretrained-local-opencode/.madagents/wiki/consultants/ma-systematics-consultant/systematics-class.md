---
description: Systematics class (systematics.py) — constructor params, regime/beam/EVA detection, LO vs NLO weight algorithms, get_all_fct argument grid, weight-group banner emission.
---

# Systematics class

`$MADGRAPH_INSTALL/madgraph/various/systematics.py`, v3.7.1.
Post-hoc scale/PDF/alphaS reweighting on an existing LHE file. NOT the integrator-side weight emission (that's amcatnlo's slice).

## Constructor defaults (`__init__`, sys.py:52-69)
- The `mur`/`muf` scale-multiplier lists, `alps`, `pdf`, and `dyn` (list of dynamical-scale codes) variation defaults are set here — read the default assignments at sys.py:52-69 for the current grids (`pdf` defaults to the `'errorset'` string; `dyn` enumerates the dyn codes whose meanings are on `systematics-weight-kernels`).
- `together` default groups mur/muf/dyn as one product block (varied together), not the full separate Cartesian product.
- `remove_wgts`/`keep_wgts` default empty, `start_id=None`, `ion_scaling=True`, `weight_format`/`weight_info=None` (non-numeric structural defaults).

## Regime detection (sys.py:96-183)
- LO vs NLO from `banner.run_card.LO`. LO uses `scalefact`; NLO uses `mur_over_ref`/`muf_over_ref`. If any of those != 1, `orig_dyn` is forced to -1 (sys.py:96-104).
- `orig_pdf = banner.run_card.get_lhapdf_id()`; `matching_mode = ickkw` (sys.py:106-107).
- **LO requires `use_syst=True`** in run_card or raises SystematicsError (sys.py:172-173).
- **NLO requires `store_rwgt_info=True`** or raises SystematicsError (sys.py:182-183).
- Ion PDF detected from `nb_neutron*`/`nb_proton*` != default — but **LO-ONLY**: `orig_ion_pdf=True` is set only inside the `RunCardLO` branch (sys.py:175-179); the NLO branch (sys.py:180-183) never sets it, so ion-PDF scaling in `get_pdfQ2` is inert for NLO systematics. (Kernel detail in `systematics-weight-kernels`.)

## Beam detection (sys.py:109-165)
- `b1`,`b2` = beam_pdg//2212 for protons. **Non-proton both beams → `pdf` forced to `'central'`** (sys.py:111-114).
- EVA (`pdlabel=='eva'`): e/mu beams, sets `pdf='0'`, `isEVA=True` (sys.py:130-146).
- EVA-on-DIS hybrid: `pdlabel1=='eva'` & `pdlabel2=='lhapdf'` (or swapped), LO only, sets `isEVAxDIS` (sys.py:148-162).
- **`pdlabel` in {none, chff, edff} → SystematicsError "Systematics not supported"** (sys.py:164-165).

## dyn-list adjustments (sys.py:201-206)
- FxFx (`matching_mode==3`) → `self.dyn=[-1]` only.
- `4` (sqrts) removed from dyn if both beams hadronic AND NLO (`if 4 in self.dyn and self.b1 and self.b2 and not self.is_lo`).

## LHAPDF (sys.py:222-227)
- Loads python lhapdf via `misc.import_python_lhapdf`. If load fails and not EVA → logs 'fail to load lhapdf' and **returns early** (no systematics). `pdf` strings: `errorset`→`<orig_pdf>` (full set), `central`→`<orig_pdf>@0` (member 0 only), `NAME@N` individual member, bare set name → all members via `mkPDFs()`.

## Argument grid (`get_all_fct`, sys.py:798-832)
- `default = [1.,1.,1.,-1, orig_pdf]` (mur,muf,alps,dyn,pdf); always `args[0]`.
- `together` blocks expanded via `itertools.product`; remaining axes scanned one-at-a-time off default.
- Inserts an extra copy of `default` before the PDF scan (member orig+1) for full weight-group grouping (sys.py:824-829).
- Logs "# Will compute N weights per event" = `len(args)-1`.

## Weight computation
- `run()` (sys.py:391-463): per event, `wgts=[get_lo_wgt|get_nlo_wgt(event,*arg) for arg in args]`; reported weight = `event.wgt*wgts[i]/wgts[0]` (ratio to nominal). Cross sums into `all_cross`. Writes `<rwgt>` entries keyed by ids from `get_wgt_name`.
- `get_lo_wgt` (sys.py:931-1034): recomputes αs^n_qcd at Dmur*mur and PDF at Dmuf*muf from stored `<mgrwt>` LO info (`parse_lo_weight`). dyn -1 uses stored scales; **dyn=1 = Σ E_T (transverse energy `get_et_scale`, NOT sum-pt despite the `'sum pt'` label string)**, 2=HT, 3=HT/2, 4=√ŝ. Full kernel (EVA branch, ion-scaling, asrwt/ALS loops, dyn formulas) in `systematics-weight-kernels`.
- `get_nlo_wgt` (sys.py:1036-1103): uses `<mgrwgt>` partial-weight info; reconstructs via `pwgt[0] + pwgt[1]*log(mur2/Q2) + pwgt[2]*log(muf2/Q2)`, Q2=Ellis-Sexton scale, times αs^qcdpower and PDFs. Under `-O` (`not __debug__`) the nominal arg short-circuits to stored `ref_wgt`; under `__debug__` (default) the nominal arg recomputes and **asserts `misc.equal(tmp, ref_wgt, sig_fig=…)` (sig-fig tolerance read at sys.py:1095-1101) — mismatch raises 'not enough agreement between stored value and computed one'** (sys.py:1095-1101), a hard error only in debug mode.

## Banner weight-groups (`write_banner`, sys.py:603-738)
- Emits `<weightgroup name="Central scale variation" combine="envelope">`, `"Emission scale variation"` (ALPS), and per-PDFSET groups with `combine=errorType`.
- dyn description map: `{1:'sum pt',2:'HT',3:'HT/2',4:'sqrts'}` (sys.py:679,761).
- Each weight: `<weight id="NAME" MUR=.. MUF=.. [DYN_SCALE=..] PDF=..> info </weight>`.

## Constructor params beyond the variation grid (sys.py:52-69)
Also accepts `start_event=0`, `stop_event=sys.maxsize` (event-range slicing, used by multicore split), `write_banner=False`, `only_beam=False`, `lhapdf_config=misc.which('lhapdf-config')`, `ion_scaling=True`.

## only_beam — asymmetric-beam PDF gating (sys.py:169, 846-847; parse_argument sys.py:1339)
- `get_pdfQ` (sys.py:846): `if self.only_beam and self.only_beam!=beam and pdf.lhapdfID != self.orig_pdf: return self.getpdfQ(self.pdfsets[self.orig_pdf], pdg, x, scale, beam)`. I.e. when `only_beam` is set, PDF *variations* are applied only to the named beam; the other beam keeps the original PDF. Useful for asymmetric (e.g. e-p / ion) setups.
- **LATENT BUG (probe-confirmed)**: that line calls `self.getpdfQ` (no underscore) — a method that does NOT exist on the class (`hasattr(Systematics,'getpdfQ')` is False; only `get_pdfQ`/`get_pdfQ2` exist). So the `only_beam` PDF-variation branch raises **AttributeError** at runtime, not a graceful fallback to the original PDF. Narrow path (only_beam is API/subprocess-only) but a live bug. See `systematics-weight-kernels`.
- Parsed by `Systematics.parse_argument` as an int key (sys.py:1339), alongside `start_event`/`stop_event`.
- **Whitelist trap:** `--only_beam=` and `--ion_scaling=` appear in `do_systematics`'s help text (cri.py:1721-1722) and ARE parsed by systematics.py, but are NOT in `do_systematics`'s option-validation whitelist (cri.py:1813-1817). Passing `--only_beam=` to the `systematics` command raises `InvalidCmd`. They reach the class only via direct API call or the per-job `bin/internal/systematics.py` subprocess (multicore path).

## Cautions
- LO without `use_syst` / NLO without `store_rwgt_info` → hard error, not a warning. Those run_card flags must have been set at generation time.
- `pdf='central'` silently forced for non-proton beams — a requested PDF error set will not be computed.
- dyn=4 silently dropped for hadronic NLO.
- `--only_beam=`/`--ion_scaling=` advertised in help but rejected by the command whitelist — only usable via API/subprocess, not the interactive `systematics` command.

## Boundary note — reweight.f is matching-Sudakov, not mine
`$MADGRAPH_INSTALL/Template/LO/SubProcesses/reweight.f` (listed in my card's source areas) is the **CKKW/MLM matching-Sudakov** scaffolding: `gamma`/`sud`/`sudwgt` branching-probability functions, clustering tracing (`ipartupdate`), `alpsfact`-driven αs, dynamic clustering scales (reweight.f:19-557). This is matching-slice territory (jet-merging Sudakov), distinct from both my scale/PDF Systematics and the EW-Sudakov ME reweight. The ME-reweight Fortran (`rw_me/`) is generated dynamically via the standalone exporter (`export_v4`/`export_fks`), not a static template. Route reweight.f matching-Sudakov questions to the matching slice.
