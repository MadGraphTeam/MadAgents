---
description: maxjetflavor run_card param — controls jet-vs-b-jet cut classification (setcuts.f), the matching >6 guard, and beam-driven auto-set; flavor-scheme link is model-side
---

# maxjetflavor (RunCardLO + RunCardNLO)

Source: `$MADGRAPH_INSTALL/madgraph/various/banner.py` + `Template/LO/SubProcesses/{setcuts.f,cuts.f}`. MG5_aMC v3.7.1.

## Registration / default (read the value at the cited line)
- LO: `banner.py:4424` `self.add_param("maxjetflavor", ...)` — NOT hidden (visible in LO run_card), include=True (reaches run.inc / Fortran). Read the default literal at :4424.
- NLO: `banner.py:5736` `self.add_param('maxjetflavor', ..., hidden=True)` — hidden in NLO card, separate class (RunCardNLO). Read the default at :5736.

## What it controls (runtime, Fortran)
maxjetflavor is the runtime decider of whether a quark leg is cut as a **light jet** (ptj/etaj/drjj) or as a **b-jet** (ptb/etab/drbb). It does NOT set masses — masses are model-side (model-loader slice).
- `setcuts.f:217` `if (abs(idup(i,1,iproc)).le.min(maxjetflavor,6)) is_a_j(i)=.true.` — pdg ≤ maxjetflavor → light jet.
- `setcuts.f:220` `else if abs(pdg) .ge. maxjetflavor+1 .and. .le.5 → is_a_b(i)=.true.` — pdg in (maxjetflavor, 5] → b-jet.
- `setcuts.f:225` gluon (21) always `is_a_j`.
- Mechanism (value-threshold): a b quark (pdg 5) is `is_a_b` (b-jet cuts) when maxjetflavor < 5, and `is_a_j` (light-jet cuts) when maxjetflavor ≥ 5. Which side the registered default (:4424) lands on: read the default there.
- `cuts.f:1107` comment: "From the run_card.dat, maxjetflavor defines if b quark should be considered here (via the logical variable 'is_a_jet')" — feeds `is_a_j`-based jet-clustering array `pQCD` (`cuts.f:1112-1118`).
- Card-creation classification mirror: `banner.py:5080` cut_class uses `abs(pdg) <= maxjetflavor or pdg==21 → 'j'` else `<=5 → 'b'` (decides which cut block to display). `banner.py:4994` jet_id = `[21]+range(1, maxjetflavor+1)` for sde_strategy.
- Also consumed in reweighting: `reweight.f:194,216` `if irfl.gt.maxjetflavor .and. irfl.ne.21: isjet=.false.` (asrwgtflavor is the matching-reweight analog).

## Flavor-scheme link (mostly model-side; run_card only reflects it)
"maxjetflavor=4 ⇒ 4-flavor scheme, =5 ⇒ 5-flavor" is a physics convention. The run_card param itself only sets the jet/b-jet cut split. Whether b is massless and in the p/j multiparticle (the actual scheme choice) is model-loader's slice. PDF flavor-scheme consistency is scales-pdf.

## Beam-driven auto-set at card creation
`banner.py:4807-4810` (create_default_for_process): if beam content includes any of [±1..±5,21,22], `maxjetflavor = max([FLOOR] + [abs(i) for i in beam_id if -7<i<7])` (read the floor literal at :4808); also sets `asrwgtflavor`. So a beam quark of flavour f raises maxjetflavor to at least |f| — e.g. a 5-flavor proton (b in beam_id) pushes it up automatically, above the registered default (:4424). This is the card-creation layer (see cut-value-layer-precedence).

## Validity guards (check_validity)
- `banner.py:4507-4508` `if int(maxjetflavor) > 6: raise InvalidRunCard('maxjetflavor should be lower than 5! (6 is partly supported)')`. QUIRK: the check is `> 6`, so **5 and 6 are accepted** despite the message text saying "lower than 5". 7+ rejected.
- `banner.py:4556-4557` (inside `if ickkw>0`, matching active): `if maxjetflavor == 6: raise InvalidRunCard('maxjetflavor at 6 is NOT supported for matching!')`. So 6 is allowed unmatched but forbidden with MLM/CKKW matching.

## Cross-slice
- b-mass / p,j membership / flavor-scheme model side → model-loader.
- PDF flavor-scheme consistency (nf active in PDF) → scales-pdf.
- what matching does with the jet flavors → matching (I own only the run_card guard).
