---
description: Custom-cut hooks (custom_fcts run_card param + dummy_cuts LO/NLO signatures via dummy_fct.f) and the no_parton_cut / set run_card nocut macro that zeroes every cut-tagged param
---

# Custom cuts (custom_fcts / dummy_cuts) and no_parton_cut

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`,
`$MADGRAPH_INSTALL/Template/{LO,NLO}/SubProcesses/dummy_fct.f`,
`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py`. v3.7.1.

## custom_fcts run_card parameter
- Registered LO `banner.py:4292` and NLO `banner.py:5741`:
  `add_param("custom_fcts", [], typelist="str", include=False, comment="list of files
  containing function that overwritte dummy function of the code (like adding cuts/...)")`.
  Default = empty list; a list of `.f` file paths.
- Present in the LO run_card template as `%(custom_fcts)s = custom_fcts ! List of files
  containing user hook function`.
- Consumed by `RunCard.edit_dummy_fct_from_file` (`banner.py:3320`), invoked at
  `banner.py:3604` (`self.edit_dummy_fct_from_file(self["custom_fcts"], os.path.dirname(output_dir))`).
  It splices the user file's function bodies over the template `dummy_fct.f` at card-write time.
- Version: the `custom_fcts` hook is live in v3.7.1. The introduction version cannot be
  confirmed from source (no version stamp in the code path), so any "since 3.5.0" claim is
  unverified.

## dummy_fct.f hook functions and the two dummy_cuts signatures
`Template/LO/SubProcesses/dummy_fct.f` overrideable functions:
`dummy_cuts(P)` (:1), `get_dummy_x1` (:42), `get_dummy_x1_x2` (:67),
`dummy_boostframe()` (:93), `user_dynamical_scale(P)` (:102), `bias_wgt_custom` (:123).
- **LO** `dummy_cuts` signature: `logical FUNCTION dummy_cuts(P)` (LO dummy_fct.f:1);
  body returns `dummy_cuts=.true.` (:37) — pass everything by default.
- **NLO** `dummy_cuts` signature: `logical function dummy_cuts(p,istatus,ipdg)`
  (NLO dummy_fct.f:4); returns `.true.` (:37). NLO passes particle status + PDG arrays so a
  custom NLO cut can be IR-safe / flavour-aware.
- The two signatures differ — a custom `dummy_cuts.f` written for LO will NOT compile as an
  NLO override and vice versa. Doc claim CONFIRMED.
- dummy_cuts is called from `cuts.f` (`PASSCUTS`) as the user extension hook; see
  cuts-f-filter.md for where it sits in the filter sequence.

## no_parton_cut / set run_card nocut
- `no_parton_cut` is a `set`-command macro, NOT a run_card parameter.
  `common_run_interface.py:5220`: `'no_parton_cut':([],['run_card nocut T'])` — it expands
  to `set run_card nocut T`. Help string `:5239`: `'no_parton_cut': 'remove all cut (but BW_cutoff)'`.
- Handler `common_run_interface.py:6111-6114`: when `card=='run_card'` and the key is
  `'nocut'`/`'no_cut'`, logs "Going to remove all cuts from the run_card" and calls
  `self.run_card.remove_all_cut()`.
- `remove_all_cut` (`banner.py:3858`): loops over `self.cuts_parameter` (every param with a
  `cut=` tag) and zeroes it by type — bool→False, dict→'{}', name-contains-'min'→0,
  'max'→-1, 'eta'→-1, else→0.
- **"(but BW_cutoff)"**: `bwcutoff` carries NO `cut=` tag (banner.py:4305 is a plain
  add_param), so it is not in `cuts_parameter` and survives remove_all_cut. Same for
  non-cut-tagged knobs. Doc claim CONFIRMED: no_parton_cut zeroes all cut-tagged params,
  leaves bwcutoff (and other untagged params) intact.
- Because it iterates `cuts_parameter`, it also zeroes the `*_pdg` dict cuts (dict→'{}')
  and the ordered/HT/photon-iso params — genuinely ALL cuts, not just the pt/eta headline set.
