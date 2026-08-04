---
description: MadAnalysis5Card class in banner.py — fields, the @MG5aMC escape-tag mini-language, validity raises (InvalidMadAnalysis5Card), and the shipped default templates.
---

# MadAnalysis5Card (banner.py, v3.7.1)

Class `MadAnalysis5Card(dict)` — `$MADGRAPH_INSTALL/madgraph/various/banner.py:5149`.
`InvalidMadAnalysis5Card(InvalidCmd)` — `:5146`.

## Shipped default templates (both modes)
`$MADGRAPH_INSTALL/Template/LO/Cards/madanalysis5_{parton,hadron}_card_default.dat` — the shipped skip-only fallback (read the file for exact text; the load-bearing sentinel `@MG5aMC skip_analysis` is stable):
```
# This card is used only if MA5 failed to create a default for this run
# We therefore use as default: do nothing
@MG5aMC skip_analysis
```
PROBE-CONFIRMED (parse): parsing either default gives `_skip_analysis=True`. So out-of-the-box (no MA5-generated card) the analysis step is a NO-OP. Header comment says MA5 normally auto-creates a real default per run; this template is only the fallback if that creation failed.

## Class-level fields (:5153-5157)
- `_MG5aMC_escape_tag = '@MG5aMC'` — every MG-directive line starts with this.
- `_default_hadron_inputs = ['*.hepmc','*.hep','*.stdhep','*.lhco','*.root']`
- `_default_parton_inputs = ['*.lhe']`
- `_skip_analysis = False` — CLASS attribute. CAUTION: `read()` calls `self.__init__()` (:5247) which runs `default_setup()` but does NOT reset `_skip_analysis`; it is only ever flipped True by a `skip_analysis` tag (:5269-5270). A given card object only sets it True, never back to False within read.

## default_setup() (:5177) keys
`mode`='parton', `inputs`=[], `stdout_lvl`=None, `analyses`={}, `recasting`={'commands':[],'card':[]}, `reconstruction`={'lhco_input':...,'root_input':...}, `order`=[]. Analyses/reconstructions hold `{'commands':[],'reconstructions':[]}` / `{'commands':[],'reco_output':'lhe'}`.

## read() — the @MG5aMC mini-language (:5225-5386)
Lines starting `#` skipped; blank skipped. `@MG5aMC option=value` (or bare option) parsed into:
- `inputs` -> extend self['inputs'] (comma-split).
- `skip_analysis` -> `_skip_analysis=True`.
- `stdout_lvl` -> int, else eval, else `logging.<NAME>`; else raise.
- `analysis_name=NAME` -> new analysis (dup name raises).
- `set_reconstructions=[...]` -> must be a list, attached to current analysis.
- `reconstruction_name=NAME` -> new reconstruction (dup raises).
- `reco_output=lhe|root` -> only inside a reconstruction, else raise; only 'lhe'/'root' allowed.
- `recasting_<card|commands>` -> recasting block; only one recasting allowed.
- anything else -> `InvalidMadAnalysis5Card("Unreckognized MG5aMC instruction ...")`.
Non-tag lines are appended as commands to the current analysis/reconstruction/recasting block. A bare default analysis is auto-created if commands appear before any analysis_name (:5349).

## Mode inference & validity (:5361-5386)
- If a reconstruction-in-analyses or a recasting card is present AND mode=='parton' -> raise "A parton MadAnalysis5 card cannot specify a recombination or recasting." Otherwise such a card forces `card_mode='hadron'`.
- `mode is None` defaults to 'parton'.
- Empty `inputs` filled from `_default_{hadron,parton}_inputs` per resolved mode.
- HADRON validity: every hadron-level analysis MUST name >=1 reconstruction, and each named reconstruction must be defined — else `InvalidMadAnalysis5Card` ("not specified any reconstruction(s)" / "is not defined").

## write() (:5388)
Emits `@MG5aMC skip_analysis` (if set), then `@MG5aMC inputs = ...`, optional `stdout_lvl`, then each ordered block. Used to fold the operative card into the run banner (run_madanalysis5:3353).
