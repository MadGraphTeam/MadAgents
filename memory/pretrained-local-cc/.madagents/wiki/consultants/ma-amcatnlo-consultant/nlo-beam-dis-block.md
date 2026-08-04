---
description: RunCardNLO.check_validity DIS/beam block (banner.py:5775-5777) — proton-paired-with-non-proton forbidden at NLO; exact boolean, blocked/passes classification, timing (card-read via consistency), LO-vs-NLO class split, EPA-EPA supported.
---

# NLO beam-config block — the "Deep Inelastic scattering" DIS raise

`$MADGRAPH_INSTALL/madgraph/various/banner.py`, `RunCardNLO.check_validity` (class at 5594, method at 5761). The DIS raise is 5775-5777; it is the ONLY beam-topology rejection in the NLO run_card. `RunCardLO` (4187) has NO analog → all beam configs pass LO.

## The exact boolean (5775-5777)
```python
if abs(self['lpp1'])!=1 or abs(self['lpp2'])!=1:      # (a) at least one beam NOT ±1 (not proton/antiproton)
    if self['lpp1'] == 1 or self['lpp2']==1:          # (b) at least one beam IS exactly a proton (==1, NOT -1)
        raise InvalidRunCard('Process like Deep Inelastic scattering not supported at NLO accuracy.')
```
Fires iff **(a) AND (b)**: one beam is non-standard (`abs(lpp)!=1`) AND one beam is specifically a **proton** (`lpp==1`).

Key asymmetries the boolean creates:
- **Antiproton `lpp=-1` is "standard" for (a)** (`abs(-1)==1`) but **NOT a proton for (b)** (`-1!=1`). So antiproton can neither trigger (a) nor satisfy (b).
- **lepton-antiproton `0,-1` PASSES** the DIS check: (a) True via `abs(0)!=1`; (b) False (neither beam ==1). Only a proton (`==1`), not an antiproton (`-1`), is blocked when paired with a non-standard beam.

## Blocked list (both conditions true) — all confirmed
- lepton-proton `0,1` / proton-lepton `1,0`
- EPA-proton `2,1` / proton-EPA `1,2`
- dressed-lepton-proton `±3,1`,`±4,1` and reverses `1,±3`,`1,±4`
Pattern: **proton (`lpp==1`) paired with anything whose `abs(lpp)!=1`** (i.e. 0, 2, ±3, ±4). Proton+antiproton is NOT this — see passes.

## Passes list — all confirmed
- **pp `1,1`, p-pbar `1,-1`, pbar-p `-1,1`**: fail (a) entirely (`abs=1` both) → whole block skipped.
- **lepton-lepton `0,0`, dressed-dressed `±3,±3`/`±4,±4`, EPA-EPA `2,2`, lepton-EPA `0,2`, lepton-antiproton `0,-1`, antiproton-lepton `-1,0`**: pass (a) but fail (b) (neither beam is `==1`) → fall through to the lepton/EPA PDF-coercion branches (5779-5795), not raised.

## Timing — card-READ, via `consistency` (default True)
`check_validity` is invoked at `banner.py:2915` inside RunCard read (`if consistency: self.check_validity()`), NOT at write. So the DIS raise fires whenever a RunCardNLO is instantiated from a file with `consistency` truthy (default). In the NLO launch flow this happens at LAUNCH: `aMCatNLOCmd` reads `Cards/run_card.dat` (e.g. amcatnlo_run_interface.py:941 `banner_mod.RunCard(...run_card.dat)` default consistency=True; do_treatcards:1712→base 923→960 write path also holds a live run_card). It does NOT fire at `generate`/`output` — those write the card from a template, no consistency read against user beam values.
- With `consistency='warning'` (2917) the InvalidRunCard is downgraded to a `logger.warning`, not raised — e.g. the banner-reload path at common_run_interface.py:5192 uses `consistency='warning'`. So the "raise" is launch-context specific; a warning-mode read of the same card only warns.

## LO-vs-NLO class split — driven by `req_acc_FO`
`RunCard.__new__` (2720) is a factory: `if 'req_acc_FO' in finput → RunCardNLO else RunCardLO` (2734-2737). `req_acc_FO` is an NLO-only run_card parameter, present only in run_cards shipped by NLO output dirs. So an NLO `[QCD]`/`[QED]` process dir → RunCardNLO → DIS check reachable; a LO dir → RunCardLO → check absent. This is the RunCardLO/RunCardNLO divergence for beams. Confirmed.

## EPA-EPA at NLO is a SUPPORTED mode
Source does NOT support "EPA-EPA passes validation but fails later." The opposite: EPA-EPA (`lpp1==lpp2==2`) has DEDICATED NLO handling —
- validation: `if self['lpp1']==self['lpp2']==2:` (5892) forces `rw_fscale=[1.0]` with warning "Factorisation scale cannot be varied for elastic photon collisions."
- runtime: `elif self.run_card['lpp1']==2==self.run_card['lpp2']:` (amcatnlo_run_interface.py:5524) — a live EPA-EPA code path.
So EPA-EPA is an intended-accommodated config, not one flagged for failure. Whether a given EPA/lepton NLO run actually converges at integration is a RUNTIME question source can't settle here → probe-candidate, not cached as fact. Boundary: lpp/pdlabel coherence + EVA/EPA density modes are scales-pdf's slice.

## Sibling checks in the same method (context, not the DIS block)
- heavy-ion (5766-5772): `lpp not in [1,2]` + `nb_proton!=1 or nb_neutron!=0` → "Heavy ion mode is only supported for lpp1=1/2". Fires BEFORE the DIS check.
- dressed-lepton pdlabel (5783-5784): `abs(lpp1)==abs(lpp2) in [3,4]` + pdlabel not a lep-density → "pdlabel %s not allowed for dressed-lepton collisions".
- lepton/EPA PDF coercion (5786-5795): silently rewrites pdlabel→nn23nlo, reweight_pdf→[False] for lepton beams (info log, not raise).

## Relation to [[nlo-card-validation-is-a-soft-net]]
That page catalogs what check_validity does NOT catch. The DIS/beam block is the COMPLEMENT: a case check_validity DOES enforce (hard raise at launch-context card read). Beam topology is caught; massless-cut / bad-parton_shower-name / FxFx-PY8-plugin are not.
