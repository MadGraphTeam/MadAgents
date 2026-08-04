---
description: shower_card.py ShowerCard — supported showers, the Qcut->py8 qcut mapping (FxFx merging scale), njmax, and the per-shower names_dict write-out.
---

# ShowerCard (shower_card.dat)

Cites `$MADGRAPH_INSTALL/madgraph/various/shower_card.py`. `class ShowerCard(banner.RunCard)` @40.

## Supported showers / names_dict
- `add_param` @77 takes per-shower name kwargs `py8=`, `py6=`, `hw6=`, `hwpp=` (plus `all_sh=`/`sh_postfix=`). Populates `names_dict[name] = {'PYTHIA8':..., 'PYTHIA6':..., 'HERWIG6':..., 'HERWIGPP':...}`.
- `check_support(name, shower)` @112: True iff shower key present in that param's names_dict entry.
- `write_card(shower, ...)` @332: maps `PYTHIA6*` → 'PYTHIA6'; writes only params whose names_dict has the chosen shower (KeyError → skipped @398). So a param without a py8 name is simply not written for PYTHIA8.

## var-type lists (@42-54)
- `float_vars` @54: `['maxerrs','lambda_5','b_mass','qcut']` — `qcut` IS a float var.
- `logical_vars` @44, `string_vars` @50, `int_vars` @53 (`njmax` is here).

## Merging params (@178-182)
- `Qcut` @179: `add_param("Qcut", -1.0, comment="Merging scale", py8='qcut')`. Default `-1.0`. Maps ONLY to PYTHIA8 (py8='qcut'); no py6/hw6/hwpp name → not written for other showers. This is the FxFx merging scale (block header @178 "FxFx merging parameters").
- `njmax` @181: `add_param("njmax", -1, ..., py8='njmax')`. Default `-1` = "guessed from the process definition". PYTHIA8 only.

## No auto-detect (Qcut/njmax never filled from the process)
`ShowerCard.create_default_for_process` @329-330 is a no-op: `pass # will be usefull later on`. Unlike the run-card (whose `create_default_for_process` auto-sets ickkw/ptj/xqcut when matching is detected), the shower-card does NOT inspect the process. So `Qcut` stays `-1.0` and `njmax` stays `-1` (template defaults) until the user edits them. The "-1 = guessed from process" for njmax is resolved later in the MCatNLO shower driver (Scripts/`MCatNLO_MadFKS_PYTHIA8.Script` + `JetMatching.h`, pythia8-interface/amcatnlo boundary), NOT in shower_card.py.

## Float write format
`write_card` @384: floats written as `'%4.3f'`. So `Qcut` is emitted with 3 decimals.

## Cautions
- `Qcut` default `-1.0` means "not set" — for an FxFx (NLO ickkw=3) run the user MUST set a positive Qcut in shower_card; it is the merging scale and there is no run-card xqcut at NLO to fall back on.
- `Qcut`/`njmax` are PYTHIA8-only; selecting HERWIG for an FxFx run drops these params silently (KeyError skip @398).
- The run-card key for the LO MLM scale is `xqcut`; the shower-card key for the FxFx/PY8 merging scale is `Qcut`→`qcut`. Distinct knobs in distinct files.
