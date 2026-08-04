---
description: Gauge-bit selection and auto-switch logic at model import — loop_qcd_qed_sm Feynman force, LoopModel perturbation gauge switch, gauge=[0,1] bit semantics, do_set gauge mapping.
---

# Gauge selection & auto-switch at import (v3.7.1)

All in `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` unless noted.

## Gauge bits on the model object
The UFO model `__init__.py` sets `gauge = [...]` consumed via `self._curr_model.get('gauge')`.
Bit semantics (from the consuming checks below + `set2_gauge`):
- `0` in gauge → unitary gauge allowed.
- `1` in gauge → Feynman gauge allowed.
- FD/axial map onto these bits too (FD needs `1`; axial needs `0`).

## What makes a model a LoopModel — the `perturbative_expansion>0` predicate (`models/import_ufo.py:498-510`)
`perturbation_couplings` is NOT a literal in the UFO `__init__.py`; it's COMPUTED at load:
`UFOMG5Converter` iterates `model.all_orders` and collects every order whose
`order.perturbative_expansion > 0` into `self.perturbation_couplings[name]=...` (`:500-502`).
If the dict is non-empty → `self.model = loop_base_objects.LoopModel({'perturbation_couplings': list(keys)})` (`:506-508`); else a plain `base_objects.Model()` (`:510`).
- The predicate is the CONSUMER's own test `> 0` (`:501`) — NOT a literal `==1` grep. `loop_qcd_qed_sm`-style models use `perturbative_expansion=99`; a convenience `=1` grep misses them.
- `CouplingOrder.__init__` (UFO `object_library.py`) defaults `perturbative_expansion=0` and ALWAYS assigns the attribute, so the `except AttributeError` at `:503` is effectively dead for FeynRules-generated `coupling_orders.py` (every order has the attr) — orders just default to 0 and are skipped.
- **SMEFTatNLO** (`models/SMEFTatNLO/coupling_orders.py`): `NP`(exp_order 2, no pert), `QCD`(pert_exp=1), `QED`(no pert). Only QCD>0 → `perturbation_couplings=['QCD']` → it IS a LoopModel, but with the QCD-only perturbation set. Probe (`import_model('SMEFTatNLO-NLO')` under default unitary): class `RestrictModel`, `isinstance LoopModel`=True, `perturbation_couplings=['QCD']`, name `SMEFTatNLO-NLO`, 22 particles.
- **dim6top_LO_UFO** (`coupling_orders.py`): QCD/QED/DIM6/FCNC, NONE set `perturbative_expansion` → all default 0 → `perturbation_couplings={}` → plain `base_objects.Model()`, NOT a LoopModel. An LO EFT model; no LoopModel branch at all.
- **2HDM5F_NLO / 2HDMtII_NLO / 2HDMtypeII** (BSM-NLO/2HDM, installed): all three `coupling_orders.py` set `perturbative_expansion=1` on **QCD ONLY** (QED order has no `perturbative_expansion` attr → defaults 0; `2HDMtypeII/coupling_orders.py:9-12` QCD pert=1, QED no attr). So `perturbation_couplings=['QCD']` → all ARE LoopModels, QCD-loop-only — same class as `loop_sm`/`SMEFTatNLO`. `gauge=[0,1]` (`2HDMtypeII/__init__.py:45`). Probes (under default unitary): `2HDM5F_NLO` → `LoopModel`, `2HDMtII_NLO` → `LoopModel`, `2HDMtypeII` → `LoopModel`, all `pert=['QCD']`, `gauge=[0,1]`, all stay `gauge=unitary`/`aloha.unitary_gauge=True`, 25 particles each. So a 2HDM-NLO BSM import does **NOT** force Feynman and does **NOT** warn — it can do tree + QCD loops in unitary gauge, exactly like loop_sm.
  - **Bare-name restriction varies by which restrict card each ships** (auto-pick gated SOLELY on `restrict_default.dat`, `get_path_restrict:228`). `2HDM5F_NLO` ships only `restrict_noL.dat` → bare `import model 2HDM5F_NLO` is a PLAIN `LoopModel` (unrestricted); `import model 2HDM5F_NLO-noL` → `RestrictModel`. `2HDMtypeII` ships only `restrict_nobmass.dat` → bare is a PLAIN `LoopModel` (unrestricted), 25 parts (probe-confirmed); needs `-nobmass` suffix to restrict. `2HDMtII_NLO` ships NO restrict cards at all → ALWAYS unrestricted (`LoopModel`). Contrast `SMEFTatNLO-NLO` / `loop_sm` which load as `RestrictModel` via their `restrict_*.dat`.

## Installed loop/BSM-NLO models all stay unitary — the load-bearing MECHANISM (membership = live-scan, never memorized)
The load-bearing FACT is a mechanism, not a count: a LoopModel whose `perturbation_couplings`
is `['QCD']` (QCD as its SOLE perturbative order) lands in the `[[],['QCD']]` auto-switch
exclusion (`do_import:5814`) → does **NOT** force Feynman under default unitary; it does
tree + QCD loops in unitary. Only a LoopModel with a NON-QCD perturbative order
(QED/EW), or the `loop_qcd_qed_sm*` name-prefix case, forces/warns. Which installed models
are QCD-only LoopModels is INSTALL-DEPENDENT and volatile — **derive it, never quote a count
or membership list from memory.** Re-scan with the CONSUMER's own predicate
(`perturbative_expansion>0`, `import_ufo.py:501` — NOT a literal `=1` grep, which misses the
`=99` of `loop_qcd_qed_sm`):
```bash
# QCD-only LoopModels on THIS install (the auto-switch-exclusion set):
for d in "$MADGRAPH_INSTALL"/models/*/; do f="$d/coupling_orders.py"; [ -f "$f" ] || continue
  python3 - "$f" "$(basename "$d")" <<'PY'
import sys,re; txt=open(sys.argv[1]).read()
pe=[re.search(r"name\s*=\s*'([^']+)'",b).group(1) for b in re.findall(r"CouplingOrder\((.*?)\)",txt,re.S)
    if (m:=re.search(r"perturbative_expansion\s*=\s*(\d+)",b)) and int(m.group(1))>0]
if pe: print(f"{sys.argv[2]:18s} perturbation={pe}  ->",
            "QCD-only LoopModel, stays unitary" if pe==['QCD'] else "NON-QCD pert -> forces/warns Feynman")
PY
done
```
As of the last scan (sanity-check, NOT a memorized fact): the QCD-only-LoopModel set was
`loop_sm, SMEFTatNLO, 2HDM5F_NLO, 2HDMtII_NLO, 2HDMtypeII` (all `['QCD']`, `gauge=[0,1]`, stay
unitary); `dim6top_LO_UFO` and `2HDM`/`MSSM_SLHA2`/`sm`/etc. set NO `perturbative_expansion>0`
→ plain `Model`, not LoopModels. (`2HDMtII_NLO` and `2HDMtypeII` are DISTINCT dirs.) Treat that
list as last-scan evidence to re-confirm, not a standing claim — run the scan for the actual input.
The ONLY model that forces Feynman at import is **`loop_qcd_qed_sm`** (and `*_Gmu`), and it is
**NOT installed locally** — `ls models/loop_qcd_qed_sm` is absent (online-only on this build).
It forces Feynman via the NAME-prefix test at `do_import:5774`, BEFORE load, not via the
post-load LoopModel auto-switch. So on a stock install you will essentially never see the
post-load LoopModel→Feynman auto-switch (`:5819-5824`) fire from a bundled model: it requires
a LoopModel whose `perturbation_couplings` includes a NON-QCD order (e.g. QED/EW loops), and
no bundled model has one. (To observe the force/warn you'd import an online QED-loop model or
`loop_qcd_qed_sm`.)

## SMEFT EFT-loop gauge consequence (the topic's load-bearing non-obvious fact)
SMEFTatNLO's `perturbation_couplings==['QCD']` lands in the auto-switch EXCLUSION set
`[[], ['QCD']]` — the literal is at `do_import:5814` (the `not in` predicate is on `:5813`,
the list `[[],['QCD']]` on `:5814`); the LoopModel sub-branch `if` opens at `:5811`. The
mirror manual-set test is `set2_gauge:8134`. So under the
DEFAULT unitary gauge a `SMEFTatNLO-NLO` import does NOT auto-switch to Feynman and does NOT
warn — it behaves like `loop_sm` (QCD-loop-only): stays unitary, W/Z keep unitary
propagators, can do tree + QCD-loop. The famous "force Feynman" case is
`loop_qcd_qed_sm*` (a NAME prefix test at `do_import:5774`, fires BEFORE load) and the
generic LoopModel-with-non-QCD-perturbation auto-switch — neither applies to SMEFTatNLO,
whose ONLY perturbative order is QCD. `gauge=[0,1]` (both allowed) for SMEFTatNLO AND
dim6top, so neither model forces a gauge by the `0 not in gauge`/`1 not in gauge` arms either.

## `do_set gauge` → `aloha.unitary_gauge` mapping (`set2_gauge`, :8067)
No model loaded (`:8078-8089`): unitary→`True`, axial→`2`, FD→`3`, else(feynman)→`False`.
With a model, the chosen gauge is gated on the model's gauge bits:
- unitary: needs `0 in gauge` → `aloha.unitary_gauge=True`, else `able_to_mod=False` + warning (`:8094-8100`).
- axial: needs `0 in gauge` → `=2` (`:8101-8107`).
- FD: emits "NOT ALL MODEL ARE SUPPORTING THIS GAUGE ... 2203.10440 and 2405.01256" warning; needs `1 in gauge` → `=3` (`:8108-8115`).
- feynman: needs `1 in gauge` → `=False` (`:8116-8122`).
`aloha.complex_mass = self.options[args[0]]` is set in the CMS setter (`:8037`); module defaults `complex_mass=False`, `unitary_gauge=True` at `$MADGRAPH_INSTALL/aloha/__init__.py:1-2`.

**Manual unitary downgrade re-warning** (`:8131-8137`): symmetric to the import-time auto-switch — when a user does `set gauge unitary` (`able_to_mod and log`) and the loaded model is a `LoopModel` with `perturbation_couplings not in [[],['QCD']]`, `set2_gauge` logs `'You will only be able to do tree level and QCD corrections in the unitary gauge.'` before re-importing. So a QED/EW loop model is not blocked from unitary gauge, just warned it loses its non-QCD loop capability. (The early `return` when `self.options['gauge']==args[1]` is at `:8125-8126` — note `:8129` is instead the `self.options[args[0]]=args[1]` assignment — so a no-op gauge set never reaches the re-import tail at `:8159`.)

`aloha.unitary_gauge` selects the pickle filename in import_full_model:
`1`→`model.pkl`, `3`→`model_FDG.pkl`, else→`model_Feynman.pkl` (`models/import_ufo.py:355-360`).
**The gauge bit also drives the converter interior** (Goldstone drop/keep, propagator
element selection, the `py3_`/`dec_` pickle-name prefixing, the prefix-mismatch reload, and
the `_import_once` modified-on-disk guard) — see `gauge-dependent-model-loading.md`.

## loop_qcd_qed_sm Feynman force (`do_import`, :5774-5780)
If `args[1]` (or its basename) startswith `'loop_qcd_qed_sm'` AND `self.options['gauge']!='Feynman'`:
`logger.info('Switching to Feynman gauge because it is the only one supported by the model ...')`, set `self._curr_model=None`, then `self.do_set('gauge Feynman', log=False)`. Fires BEFORE the UFO load.

## Post-load gauge check (`do_import`, :5810-5837)
Runs after `import_ufo.import_model` returns. Two regimes by `self.options['gauge']`:

**gauge in `['unitary','axial']`** (`:5810`):
- LoopModel sub-branch (`:5811-5824`): if `not force` AND model is `loop_base_objects.LoopModel` AND `perturbation_couplings not in [[], ['QCD']]`:
  - if `1 not in gauge` → `logger_stderr.warning('This model does not allow Feynman gauge. You will only be able to do tree level and QCD loop computations with it.')` (`:5815-5818`).
  - else → `logger.info('Change to the gauge to Feynman because this loop model allows for more than just tree level and QCD perturbations.')`, `do_set('gauge Feynman', log=False)`, **return** (`:5819-5824`).
- Then (any model): if `0 not in gauge` → warning "Change the gauge to Feynman since the model does not allow unitary gauge", `do_set('gauge Feynman')`, return (`:5825-5829`).

**gauge == else (Feynman/FD)** (`:5830-5837`):
- if `1 not in gauge` → `logger_stderr.warning('Change the gauge to unitary since the model does not allow Feynman gauge. Please re-import the model')`, `self._curr_model=None`, `do_set('gauge unitary')`, return.

## sm → loop_sm model auto-upgrade at NLO (NOT a do_import mechanism)
Importing plain `sm` then issuing an NLO process (`generate p p > t t~ [QCD]`) DOES auto-swap
the loaded model to `loop_sm` — but this happens in `loop_interface.validate_model`
(`$MADGRAPH_INSTALL/madgraph/interface/loop_interface.py:297`, "Upgrade the model sm to
loop_sm if needed"), fired when master_interface switches to MadLoop/aMC@NLO on seeing the
`[...]` bracket — NOT in `do_import`.
- If the current model is not a LoopModel (or lacks the requested pert order) AND the model
  name base is `sm` (`:331`): `[QCD]` → `add_on=''` → `exec_cmd('import model loop_sm')`
  (`:338-352`); `[QED]` or `[QCD QED]` → `add_on='qcd_qed_'` → `import model loop_qcd_qed_sm`
  AND (if not already Feynman) forces Feynman gauge first (`:333-345`).
- A non-`sm` model that is not loop-capable → `raise InvalidCmd("The model %s cannot handle
  loop processes")` (`:354-356`); NO auto-upgrade.
- WITHOUT the interface switch (i.e. asking for a loop pert order while the model is still
  plain `sm` and no upgrade fired), `extract_process` raises `InvalidCmd("The current model
  does not allow for loop computations.")` (`madgraph_interface.py:5280-5283`).
- **`loop_qcd_qed_sm`/`_Gmu` are NOT bundled on a minimal install** — so the `[QED]`/`[QCD QED]`
  auto-upgrade path on `sm` triggers an online fetch (or fails) here; the `[QCD]`→`loop_sm`
  path works because `loop_sm` ships. (Whether `loop_qcd_qed_sm_Gmu` uses the Gmu EW input
  scheme vs `loop_sm`'s alpha(MZ) scheme is a UFO fact — ufo/nlo-model slice.)
- Boundary: my slice owns the `do_import`/`import model` re-invocation that validate_model
  fires; the TRIGGER + upgrade DECISION live in loop_interface/master_interface (amcatnlo /
  nlo-syntax territory).

## Installed model set is INSTALL-VOLATILE — scan, never assume
A minimal MG5_aMC install ships only a handful of UFO dirs under `$MADGRAPH_INSTALL/models/`.
Observed minimal set: `sm`, `loop_sm`, `MSSM_SLHA2`, plus the plugin/aux dirs `hgg_plugin`,
`taudecay_UFO`. `heft` does NOT ship; `sm-no_b_mass` is a RESTRICTION of `sm` (loaded via
`get_path_restrict`'s name-split, not a separate dir). BSM/NLO models (`2HDM*`, `SMEFTatNLO`,
`dim6top_LO_UFO`, `loop_qcd_qed_sm*`) are FETCHED on demand (online DB) and may be ABSENT on a
given install — do NOT assume they are present. This page's per-model probe claims (2HDM/
SMEFTatNLO LoopModel classes etc.) hold ONLY where those models are actually installed; on a
minimal install they must be imported (which triggers the online fetch, `-`-free names only)
before any of it applies. Scan the actual install: `for d in "$MADGRAPH_INSTALL"/models/*/; do
[ -f "$d/particles.py" ] && basename "$d"; done`.

## Boundary: model-import switches GAUGE only, never the INTERFACE
The only auto-switches inside `do_import`'s model branch (`:5772-5837`) are GAUGE switches:
the `loop_qcd_qed_sm` Feynman force (`:5774-5780`) and the post-load gauge check
(`:5810-5837`). There is **NO interface switch at model-import time** — importing a LoopModel
(loop_sm, SMEFTatNLO, 2HDM*_NLO) does NOT flip the command interface to aMC@NLO/MadLoop. The
interface switch (`Switcher.change_principal_cmd('aMC@NLO'/'MadLoop'/...)`,
`madgraph/interface/master_interface.py:215-227`) fires at the PROCESS-SPECIFICATION stage,
triggered by a `[QCD]`/`[real=...]` bracket in `generate`/`add process` — that is NLO-syntax /
process-syntax slice territory, not model loading. So "what auto-switches when a loop model is
imported" = gauge only; the interface stays on whatever it was until a perturbation bracket
appears in a process line.

## Caution
- The auto-switch returns (`:5824` LoopModel→Feynman, `:5829` no-unitary→Feynman, `:5837` no-Feynman→unitary) do NOT leave a half-loaded model. They each call `self.do_set('gauge <X>', ...)` (`:5823`/`:5828`/`:5836`) FIRST, and `set2_gauge`'s tail itself re-enters `do_import` with `force=True` (`set2_gauge:8159`: `MadGraphCmd.do_import(self,'model %s %s'%(model_name,opts),force=True)`) — that recursive import runs the FULL tail (`pass_particles_name`, `process_model` at `:5845`). The outer bare `return` (`:5824` etc.) just avoids double-processing after the recursion already completed the load. Recursion terminates because `force=True` skips the LoopModel sub-branch (`:5811 if not force`). Probe (`import model sm; set gauge Feynman`): the gauge switch re-fired "Change particles name to pass to MG5 convention" + "Kept definitions of multiparticles p / j / ..." and `all` gained Goldstones `g0 g+ g-` — confirming a full re-import+process_model under the new gauge, not a caller-driven one. (`:5837` additionally sets `self._curr_model=None` before the `do_set`, so set2_gauge re-imports from `modelpath+restriction`.)
- The auto-switch sub-branch only fires for loop models whose `perturbation_couplings` is NOT in `[[],['QCD']]` (i.e. QED/EW loops). The common installed `loop_sm` is QCD-loop-only, so under default unitary gauge it does NOT auto-switch: probe (`import model loop_sm` under unitary) left `gauge='unitary'`, `aloha.unitary_gauge=True`, and multiparticles populated (process_model ran). Don't assume "any loop model under unitary auto-switches."
- `force=True` bypasses the LoopModel sub-branch entirely (`:5811`).
