---
description: Process-driven cut auto-setting at card creation/write time — create_default_for_process (1->N remove_all_cut, multiplicity matching auto-enable, maxjetflavor auto-set), cut_class classification, writer hid_lines display logic hiding cuts for absent particle classes
---

# Process-driven cut layer (card creation + write time)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py`, class `RunCardLO`. MG5_aMC v3.7.1.
This layer runs at `output`/card-CREATION time, UPSTREAM of `check_validity` (runcard-cut-validity.md)
and of the Fortran enforcement (cuts-f-filter.md). It decides which cut DEFAULTS the freshly
written `run_card.dat` carries and which cut LINES are even shown. Three mechanisms:
`create_default_for_process` (value defaults), `cut_class` (particle inventory), writer `hid_lines`
(line visibility).

## create_default_for_process (:4767)
Docstring (:4768) states the rules verbatim:
"process 1->N all cut set on off / loop_induced -> MC over helicity / e+ e- beam -> lpp:0 ebeam:500
/ p p beam -> set maxjetflavor automatically / more than one multiplicity: ickkw=1 xqcut=30 use_syst=F
/ if $ used in syntax force sde_strategy to 1".

Cut-relevant actions:
- :4778 first runs each `block.create_default_for_process(...)` (RunBlock layer).
- :4780 `if proc_characteristic['loop_induced']:` => :4781 `nhel=1` (MC over helicity).
- :4782 `pdgs_for_merging_cut = proc_characteristic['colored_pdgs']` (overrides the [21,1..6] default).
- :4784 `if proc_characteristic['ninitial'] == 1:` (decay / 1->N) => :4786 `self.remove_all_cut()`
  and :4787 `use_syst=False`. So a pure decay process ships with EVERY cut zeroed/off.
  (SDE_strategy also set to 1 at :5045.)
- :4807-4810 **`maxjetflavor` auto-set from beam IDs**: if any quark/gluon/photon in beams
  (`any(i in beam_id for i in [1..5,21,22]` at :4807), `maxjetflavor = max([FLOOR] + [|i| for i in
  beam_id if -7<i<7])` (:4808 — read the floor literal there; e.g. a b in beam raises it one).
  `asrwgtflavor` set the same. This runs BEFORE cut_class, so jet/b classification below uses
  the auto-set value, not the registered default (banner.py:4424).

## Multiplicity-driven matching auto-enable (:4924-:4966)
Detects multi-jet multiplicity samples (e.g. `p p > j, p p > j j`):
- :4925-:4960 if min!=max final-state multiplicity AND the extra legs of the highest-mult process
  are all jets (`[1..5,21]`), set `matching=True`.
- :4953 `matching=True`; :4957 `ickkw=1`; :4958 `xqcut` set to the matching default (read at :4958);
  then `drjj=0`, `drjl=0`, `sys_alpsfact`/`--alps` set, display blocks `mlm`+`ckkw`,
  `dynamical_scale_choice=-1`.
  => The default run_card for a multi-jet sample arrives with matching ON (xqcut>0) and drjj/drjl
  already zeroed. This is WHY check_validity's xqcut>0 branch (runcard-cut-validity.md) then fires
  on a default card. The cut auto-disable chain often originates HERE, not from user edits.
- :5050 contrast: if model carries `MLM` limitation, `ickkw=0` forced (matching incompatible).

## cut_class — particle inventory (:5070-:5098)
Builds `cut_class` (defaultdict(int)) by scanning every process's final-state PDGs
(`oneproc.get_final_ids_after_decay()` :5074):
- :5075 `decay_chains` present => :5076 `cut_class['d']=1`.
- :5078 `if pdg == 22:` => :5079 `'a'`.
- :5080 `|pdg| <= maxjetflavor or pdg==21` => :5081 `'j'` and :5082 `'J'`.
- :5083 `|pdg| <= 5` (not already a jet) => :5084 `'b'` and :5085 `'J'`.
- :5086 `|pdg| in [11,13,15]` => :5087 `'l'` and :5088 `'L'`.
- :5089 `|pdg| in [12,14,16]` => :5090 `'n'` and :5091 `'L'`.
- :5092 else if particle mass != 'ZERO' => `'H'` (massive non-light).
- :5096 `cut_class[key] = max(over processes, count)`; :5098 `cut_class['']=True` (avoid empty).
The VALUE is the max multiplicity of that class across the process(es) — drives how many ordered/
pair cut lines get shown.

## Writer hid_lines (display visibility) (:5127-:5142)
In `RunCardLO.write`, only when writing the DEFAULT card (output_file name contains 'default'):
- :5127 `hid_lines = {'default': True}`.
- :5131 if `self.cut_class`: `hid_lines['default'] = False` (cuts hidden by default), then for each
  class `key` with count `nb`, set `hid_lines[key*i]=True` (:5135) for i in 1..nb (so `'j'`,`'jj'`,...
  shown up to the present multiplicity).
- :5137-5138 cross-pair lines (`'bj','bl','al','jl','ab','aj'`) shown only if BOTH constituent classes
  present in cut_class.
- :5142 passes `hid_lines` as `template_options` to the base writer.

How `cut=` tag connects (cross-ref runcard-cut-params.md): each cut param's `cut=` value (stored in
`cuts_parameter[name]` at :2870) is looked up in `valid_line` (:2987) as `cond = cuts_parameter[param]`,
then the line is shown iff `template_options.get(cond, default)` is truthy OR `cond is True` (the
bare-`cut=True` global cuts like dsqrt_shat/xqcut/pdg-dicts always show). So `cut=` is precisely the
KEY into hid_lines — that is the mechanism behind "cut= is layout metadata": it selects line visibility.
`remove_all_cut` (:3858) also iterates `cuts_parameter` (bool->False, dict->'{}', name~min->0,
name~max->-1, name~eta->-1, else->0).

## Cautions
- A default run_card is process-tailored: cut lines for absent particle classes are HIDDEN, not just
  defaulted. Absence of a `ptb`/`drbb` line in a written card means no b in the final state, NOT that
  the cut is unavailable — it still exists and can be added.
- maxjetflavor auto-set (floor at :4808, raised by quark beams) changes which PDGs count as 'j' vs 'b' in
  cut_class AND in the Fortran is_a_j/is_a_b split (setcuts.f, cuts-f-filter.md). A b-initiated process
  gets maxjetflavor=5 -> b treated as a light jet for cuts.
- Multi-jet samples arrive matched-by-default (xqcut>0, value at :4958); the drjj/drjl=0 and
  ptj/mmjj=xqcut you see are auto-set, not user choices. Don't read them as deliberate.
- These are CREATION-time defaults; a user can override any of them by editing run_card.dat. Re-running
  check_validity on the edited card re-applies the validity corrections but NOT remove_all_cut /
  cut_class (those fire only at creation).
