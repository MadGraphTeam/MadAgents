---
description: do_compute_widths entry points and the full two-stage width computation flow (FeynRules 2-body formulas + MadEvent survey for N>2 body), with option defaults.
---

# compute_widths flow (v3.7.1)

## Interactive command surface (MG5 REPL)
- **Command name is `compute_widths`** (`do_compute_widths`, madgraph_interface.py:9801). `calculate_width` appears only in the help/example text (help_compute_widths:706, 729) — it is NOT a registered command (no `do_calculate_width`). `calculate_decay_widths` is a *different* command, available at the MadEvent/process-dir REPL only (`do_calculate_decay_widths`, madevent_interface.py:2925), not the MG5 REPL.
- **Syntax:** `compute_widths particle [other particles] [--options]` (docstring 9804). Particle = name, antiname, multiparticle label, pid, or `all`. ≥1 required (check 1796-1799).
- **Prerequisite: a model must be imported** (`import model X` first) — `check_compute_widths` resolves every arg through `self._curr_model` (1821/1830). It does NOT need an `output` process dir, a `generate`, or a user-supplied param_card. With `--path` omitted, the model's OWN built-in card is written and used (1859-1868). So `import model sm` → `compute_widths t` works standalone (probe-confirmed).
- **What it does with the list:** computes each requested pid's total + partial widths (2-body via FR formula if `decays.py` present, else all channels numeric — see Two stages below) and **WRITES them into a param_card**, replacing that card's DECAY blocks. It does NOT print a width table to the console. Probe (`compute_widths t --body_decay=2`, sm): console shows only the NWA warning, `INFO: Get two body decay from FeynRules formula`, and `Results written to $MADGRAPH_INSTALL/models/sm/param_card.dat`. So a doc calling it "compute and *display* widths" is wrong on the display half — it computes and **writes** (overwrites the target param_card's widths in place).
- **Where it writes (default):** with no `--path`/`--output`, the **model directory's `param_card.dat`** (1862-1863) — i.e. it overwrites the model's built-in card, not a process dir. Give `--path=<card>` to compute against a specific card and `--output=<card>` to redirect the result (else `output` defaults to `path`, 1869-1870).
- **Options (check_compute_widths defaults, 1802-1804 — read the literals fresh there, drift-prone):** `--body_decay` (a fractional default; integer part = body cap, fractional part = convergence target), `--precision_channel` (the MadEvent survey `accuracy`), `--min_br` (default = formula `(body_decay%1)/5`, 1872-1873), `--path=None`, `--output=None`, `--nlo` (flag → SMWidth path). A `--opt` without `=` (except `--nlo`) raises; an unknown `--opt` raises (1812-1816). Note: `--min_br` and `--precision_channel` are NOT in the compute_widths docstring (9804-9818) but ARE valid (present in the options dict + help_compute_widths:719-722).
- **Doc-myth corrections (verified 1802-1817, 10195-10233):**
  - The precision option is spelled **`--precision_channel`**, NOT `--precision`. `--precision=X` is not in the options dict → `arg[2:] not in options` at 1815 → `raise InvalidCmd('--precision not valid options')` (1816). A doc/example writing `--precision=0.01` is wrong; it errors out.
  - `--body_decay=2.0` **does** mean "2-body only" (CORRECT). 2.0 satisfies `level//1 == level and level>1` (10195) → the INTEGER branch with `level=int(2)` → `find_channels(part,2,...)` collects 2-body only. Any whole-number value takes this exhaustive branch; only a fractional value (e.g. the default at :1803) takes the precision-loop branch (integer part = body cap, fractional part = convergence stop).
  - The **default** `body_decay` (read at :1803) enumerates **up to its integer-part body cap** (max_level = int part; precision = fractional part) — its cap is >3, NOT "2-body and 3-body". A doc saying the default keeps only 2-and-3-body is wrong on the cap (it enumerates up to the int-part cap, subject to the apx-error convergence stop).

## Entry points
- `madgraph/interface/madgraph_interface.py:9801` `do_compute_widths(self, line, model=None, do2body=True, decaymodel=None)` — the real engine (MasterCmd/MadGraph principal).
- `madgraph/interface/common_run_interface.py:2428` `do_compute_widths` — MadEvent/aMC runtime wrapper: builds the `compute_widths` line and forwards to a child `MasterCmd` via `cmd.exec_cmd(line, model=opts['model'])` (2450).
- `madgraph/interface/common_run_interface.py:7292` `do_compute_widths` — MadSpin-side. Scans the param_card text with regex `decay\s+(\+?\-?\d+)\s+auto(@NLO|)` (7301, case-insensitive) for `DECAY <pid> auto[@NLO]`, appends those pids to the line, then calls `self.mother_interface.do_compute_widths(line)` (7315). After, warns on very-small widths: `total/mass < small_width_treatment` (run_card) or below a hardcoded critical floor (read at 7331-7336).
- `madgraph/interface/madevent_interface.py:2925` `do_calculate_decay_widths` — the standalone MadEvent command; runs `survey`/`combine_events`/`store_events` then `collect_decay_widths` (2961).

## Particle selection (check_compute_widths, madgraph_interface.py:1789)
- **MG5 REPL `compute_widths` requires ≥1 particle** (1796-1799): bare `compute_widths` raises InvalidCmd ("requires at least the name of one particle. If you want ... type 'compute_widths all'"). It does NOT auto-detect AUTO-flagged widths. (The runtime/MadSpin wrappers DO auto-scan — common_run 7301 regex; that distinction is real.)
- Args accepted: (anti)particle name, multiparticle label, or pid; collected as `abs(pid)` into a set (1818-1838).
- **`all`** (1835-1837): selects EVERY model particle's pid — not just AUTO-width ones. So `compute_widths all` recomputes all widths regardless of their card flag.
- `--path` resolution fallback chain (1843-1858): literal → `MG5DIR/<path>` → model_v4_path → `model.path`; if a dir, looks for `param_card.dat` inside; validated by `detect_card_type(...) == 'param_card.dat'`.
- **No `--path` given** (1859-1869): writes the current model's own param_card via `write_param_card()` to the model dir (or `--output`) and uses that. So widths are computed against the model's default card unless one is supplied.
- `min_br` default: see Option defaults below (1872-1873).

## Warning fired at every call
`madgraph_interface.py:9826-9828` (text 9826-9827, `logger.warning` at 9828; unless `--nlo`): "Please note that the automatic computation of the width is only valid in narrow-width approximation and at tree-level." This is the LO/NWA caveat.

## Option defaults — `check_compute_widths` (madgraph_interface.py:1789)
Defaults dict at 1802-1804 (read the literals fresh there — drift-prone):
- `body_decay` — a fractional default; integer part = body cap, fractional part = convergence target.
- `precision_channel` — the MadEvent survey `accuracy`.
- `path=None, output=None, min_br=None, nlo=False`
- `min_br` default (1872-1873): `(float(body_decay) % 1) / 5` — read the divisor at :1873. Integer body_decay → min_br = 0 (stable consequence of the formula).
- If `--nlo` present: routes to `compute_widths_SMWidth` (madgraph_interface.py:10029); LO engine skipped.

## Two stages inside do_compute_widths (madgraph_interface.py)
1. **2-body from FeynRules `partial_widths`** (9866-9920): if every requested particle has a `partial_widths` attribute (analytic formulas shipped in the UFO), evaluate each mode's expression at scale = particle mass. `do2body=True` and presence of `partial_widths` → `skip_2body=True` for the later MadEvent stage. If `body_decay == 2`, return after this (9919-9920).
   - **Per-particle card re-eval at scale=mass** (9878): `set_parameters_and_couplings(opts['path'], scale=mass)` is re-run for EACH particle, so the analytic formulas use couplings run to that particle's mass (parallel to the apx engine's running). The returned `data` dict is the eval namespace for the formula (9899).
   - **aS-zero warning** (9881-9882): if `aS == 0` (running undefined at low mass) and `color != 1`, warns "aS set to zero ... running is not defined for such low mass."
   - **Kinematic gate per mode** (9886-9895): subtract each final particle's mass from the mother mass; `if tmp_mass <= 0: continue` — closed 2-body channels are skipped.
   - **for/else write-back gating** (9869 loop, 9916 `else` → `update_width_in_param_card` 9917-9918): runs ONLY if the particle loop completes without `break`. If ANY requested particle lacks `partial_widths` (`if not hasattr` 9871 → `break` 9873), `skip_2body=False`, the FR write-back is skipped, and ALL widths (incl. 2-body) go numeric via MadEvent.
   - **What sets `partial_widths` — the `all_decays`/decays.py gate (BSM-critical).** `do_compute_widths` reloads the model with `import_ufo.import_model(modelname, decay=True)` (9833) when no model is passed (default `import_model` is `decay=False`, 243/328). The decay-load block is gated at `import_ufo.py:426` `if decay and hasattr(ufo_model, 'all_decays') and ufo_model.all_decays:` (loop 428-437) — i.e. it runs ONLY if the UFO ships a non-empty `decays.py` (`all_decays`). When it runs, every model particle `p = model['particles'].find_name(name)` gets `partial_widths` = the UFO dict if `ufo_part` has it (433-434), else `{}` (435-436, guarded `elif p and not hasattr(p,'partial_widths')` — so a ghost where `find_name` returns `None` gets nothing, comment "might be None for ghost" 437). Since `model.get_particle(pid)` returns the SAME objects from `particle_dict` (base_objects.py:1303-1307) that the import block mutated, every real (non-ghost) particle then has the attr → the `break` at 9873 does NOT fire for a requested pid → the FR shortcut runs (a particle with `{}` iterates zero modes at 9885, contributes total 0). When the UFO has NO `decays.py` (the common new-physics case) the block is skipped, NO particle has `partial_widths`, the `break` fires on the first requested pid → `skip_2body=False` → ALL widths via MadEvent. So whether the analytic 2-body shortcut runs is a per-MODEL property (decays.py presence), not per-particle — and whether a UFO ships `decays.py` is a UFO-slice fact (boundary: ufo).
   - QCD-scale zeroing (9909-9912): for colored particles, a positive partial width below the GeV-scale floor (read the literal at :9909-9912) is set to 0 with a warning. Same threshold reapplied to the survey results at 10011-10015.
   - Negative partial widths (tiered clamp at 9900-9908 — read the two cut-off literals there): a tiny-negative width → 0 silently; a larger-negative → 0 + warning; more negative still → Exception.
2. **N>2-body via MadEvent** (9928-10020): `do_decay_diagram` builds amplitudes (see channel-enumeration page); if `self._curr_amps` non-empty, `output madevent` into a TMP dir, then `survey decay` with `accuracy=precision_channel` plus fixed points/iterations (read the literals at 9976-9981), `combine_events`, `store_events`, `collect_decay_widths` (9988). Final widths/BRs read back from the survey param_card (9993) and merged via `update_width_in_param_card` (10019).
   - run_card with `ickkw` is zeroed and cuts removed for the decay run (9949-9953).
   - MSSM models get `convert_to_slha1` on the param_card before/after (9960-9961, 10022-10023).

## Standalone `calculate_decay_widths` (madevent_interface.py:2925)
Separate MadEvent command (used by a process dir output in `width` mode), NOT the compute_widths engine. Runs `survey <run> --accuracy=<acc> --points=<..> --iterations=<..>` (2944-2954; read the acc default + point/iter literals there), sets `refine_mode="old"`, then `combine_events`/`store_events`/`collect_decay_widths` (2956-2961). Same survey opts as the compute_widths N-body stage.

## Result write-back
`madevent_interface.py:2998` `update_width_in_param_card(decay_info, initial, output)` (staticmethod) — strips existing DECAY blocks from the card text and rewrites total widths + BR sub-lines from `decay_info` (pid → list of `[decay_products, partial_width]`). `collect_decay_widths` (2968) reads each subprocess `<run>_results.dat` first value as the partial width and divides by a grouping factor `nb_output = len(ids)/len(set(initial pids))` (2982).
- **Path caution (standalone path):** `collect_decay_widths` (2991-2994) reads initial=`Cards/param_card.dat` but writes output to `Events/<run_name>/param_card.dat` — it does NOT overwrite the operative `Cards/param_card.dat` in place. (The REPL compute_widths path, by contrast, writes back to the card it was pointed at via `update_width_in_param_card`.)

## Stale width after a MASS edit (no warning) — width is a DERIVED quantity
A particle width is a quantity DERIVED from the model at the current masses/couplings; it is NOT auto-derived when an input it depends on changes. Editing `Block mass` for a PDG leaves the stored `DECAY <pid>` width **verbatim**, with no recompute and **no warning**.
- **Nothing in the mass-edit path couples to width recompute.** The only card-edit-time width machinery is `static_check_param_card` (`common_run_interface.py:3740`). Its sole recompute trigger is the regex `decay\s+(\+?\-?\d+)\s+auto(@NLO|)` (`:3743`/`:3756`) — it fires ONLY when the DECAY line literally says `auto`. A NUMERIC `DECAY 25 6.38e-03` is never recomputed regardless of the mass.
- **No mass↔width consistency check exists.** The post-detection loop over `card['decay']` (`:3779`+) only flags a too-small `width/mass` (below the s-channel-resonance floor literal — read at `:3788`) and `not mass and width` (massive width on a massless particle). There is NO check that the stored width is *consistent* with the current mass. A 125-GeV width (`6.38e-03`) under `mass 25 = 400` passes silently (`width/mass ≈ 1.6e-5`, comfortably above that floor).
- **`update_dependent` does not touch it.** Mass edits run `param_card.update_dependent(model, restrict_card, ...)` (`:7045`), which recomputes only *internal/dependent* (formula-defined) parameters + `param_card_rule.dat` constraints. The Higgs width `WH` is `nature = 'external'`, `lhablock = 'DECAY'`, `lhacode = [25]` (`models/sm/parameters.py:213-219`) — an external param is never recomputed by `update_dependent`. So no path feeds an edited mass back into the stored width.
- **MG5 uses whatever number is in `DECAY <pid>` verbatim.** The width slot is read as-is; the only LO caveat ever emitted is the NWA/tree-level warning at `:9826-9828` (fires only WHEN `compute_widths` runs), not a staleness warning.

### The fix: regenerate. Three equivalent paths, all → the SAME engine at the CURRENT card masses
`do_compute_widths` re-evaluates parameters at `set_parameters_and_couplings(opts['path'], scale=mass)` (`madgraph_interface.py:9862`/`9878`) using the masses **in the card it is pointed at** — so the regen must be issued AFTER the mass edit.
- **(a) `compute_widths 25`** — REPL → `madgraph_interface.py:9801` engine directly; at the launch card-edit prompt → `common_run_interface.py:2428 do_compute_widths` → child MasterCmd → same `:9801` engine. Fires at compute-widths time (immediately).
- **(b) `DECAY 25 Auto` in the param_card** — at end-of-card-edit, `static_check_param_card:3743` regex-detects it → `static_compute_widths:3805` → `do_compute_widths`. Fires at launch / end-of-edit (deferred).
- **(c) `set WH Auto`** (card editor) — `setP:6450` translates the value to the string `'Auto'` and writes it into the DECAY block (`block != 'decay'` would warn-and-reject; DECAY is allowed), reducing to path (b) at the same end-of-edit check. Fires at end-of-edit (deferred).
- A hand-set numeric is correct ONLY if it equals the model-computed width at the new mass; otherwise it is stale. There is no in-MG5 validation of a hand-set number.

### Anchored example (probe-confirmed; `compute_widths 25 --body_decay=2`, default `sm`)
Hypothetical 400-GeV SM-like Higgs: shipped `DECAY 25 6.382339e-03` is the total width of a **125-GeV** Higgs (≈ H→bb̄-dominated). At `mass 25 = 400` the WW/ZZ/tt channels open and the model-computed total is **Γ_H ≈ 27.2 GeV** (~3.5 orders larger). `compute_widths 25` (issued AFTER the mass edit) regenerates:
```
DECAY 25 2.720001e+01    # total = 27.20 GeV
  6.065e-01  2  -24 24    # H->WW  = 16.498 GeV
  2.833e-01  2   23 23    # H->ZZ  =  7.706 GeV
  1.095e-01  2    6 -6    # H->tt  =  2.978 GeV
  6.39e-04   2    5 -5    # H->bb  =  0.0174 GeV
```
(At `mass 25 = 100` the consistent total is ≈ `4.499e-03` GeV.) `--body_decay=2` keeps only 2-body modes; the default `body_decay` (`:1803`) surveys higher multiplicities too. Note this 400-GeV table uses the FR analytic 2-body path because `sm` ships `decays.py` (`all_decays`); a BSM model without `decays.py` would integrate every channel numerically (see the `all_decays` gate above).

## Consumer seam: MadSpin BR>1 warning (denominator is MY slice, computation is NOT)
MadSpin's "Branching ratio larger than one for %s" is emitted from **MadSpin internals, not compute_widths** (`MadSpin/interface_madspin.py:969/980/986` as `logger.critical`; a hard `raise MadSpinError('BR is larger than one.')` at `MadSpin/decay.py:4008` when `max_br > 1.0001`). The comparison there (`interface_madspin.py:964-970`) is:
- **denominator `totwidth`** = `float(self.banner.get('param','decay',abs(pdg)).value)` (:964) — the **total width read from the param_card `DECAY <pid>` block**. This is the value MY slice's `compute_widths`/`update_width_in_param_card` writes.
- **numerator `pwidth`** = `sum(event_files[k].cross ...)` (:967) — the cross-section of MadSpin's OWN decay-event generation (`generate_events` → `decay.py`), i.e. MadSpin's internally-computed partial width. This is **out-of-slice (madspin-interface)** — it is NOT a compute_widths partial width.
- BR>1 fires (`if pwidth > 1.01 * totwidth`, :968) when the stored total width in the card is **too small / inconsistent** relative to MadSpin's partial-width estimate. `br *= pwidth/totwidth` (:970) is the chain σ ∝ Γ_partial/Γ_total factorization — no clamp to 1 in that multiply.
- **The fix IS in-slice:** running `compute_widths <pid>` rewrites a consistent total width into the `DECAY` block (overwrites in place, no printed table — see above), so the denominator matches the model's actual total width and BR ≤ 1. The ratio semantics (partial width divided by the stated total width) is correct, but the partial-width computation and the warning both live in MadSpin, not madwidth.
- Contrast the ZeroResult path (:941-943): MadSpin generating a decay with cross 0 → "Branching ratio is zero for this particle" and drops it — the BR≈0 (silent-fail) fingerprint, also MadSpin-side.
- Shipped `sm` Higgs total width: every `restrict_*.dat` except `no_widths` carries a `DECAY 25 <width>` line — read the shipped value fresh at `models/sm/restrict_default.dat:33` (drift-prone source card default). For orientation only, the SM theory/PDG prediction is ~4.1 MeV (literature); the shipped card default differs from it.

## Gaps / cautions
- The `do2body` FeynRules path needs the UFO to ship a non-empty `decays.py` (`all_decays`), which is what gates the `partial_widths`-attribute import (`import_ufo.py:426`); whether a given model ships it is a UFO-slice fact. Without it, ALL widths (incl. 2-body) go through MadEvent numerically. **Most BSM/EFT new-physics UFOs do NOT ship `decays.py`** — so for typical BSM auto-width requests the FR shortcut is bypassed and every channel is integrated numerically (model-agnostic; the end-to-end "slower" timing effect is probe-gated, not asserted here).
  - Shipped-model evidence (`$MADGRAPH_INSTALL/models`; re-inspect with `grep -l all_decays models/*/decays.py`): models that ship `decays.py` include `sm`, `2HDM`, `2HDM5F_NLO`, `2HDMtII_NLO`, `2HDMtypeII`, `MSSM_SLHA2`; the EFT/NP ones that DON'T include `dim6top_LO_UFO`, `SMEFTatNLO`, `loop_sm`, `hgg_plugin`, `taudecay_UFO`. So the BSM/EFT models this gate matters for carry no `decays.py` and integrate every channel numerically. (File presence/content is a UFO-slice fact; this is shipped-model grounding, not a runtime prediction.)
- `precision_channel` (survey accuracy) is distinct from `body_decay` precision (channel-enumeration stop criterion). Don't conflate.
- QCD-scale zeroing silently drops sub-floor positive partial widths (threshold at :9909-9912, read there) for colored particles — a light colored state can get an under-counted total width.
