---
description: Where parton-level fiducial cuts bite LO integration — passcuts gate in the sampler (dsample.f:181), cut-fail stores a zero-weight point into the VEGAS grid, CUTSDONE caching, cut-derived smin vs GENCMS TAUMIN=0 (smin NOT a tau lower bound in standard pp), nb_pass_cuts/none_pass efficiency abort, dead pass_point path.
---

# The cut <-> phase-space seam (where fiducial cuts bite the integration)

Scope: the integration-side seam only. The cut PARAMETER definitions and the body of
`passcuts`/`cuts.f` (what each cut tests) belong to **ma-kinematic-cuts-consultant**; this page owns
*where in the integrator the cut is invoked and what that does to the sampling*.

## 1. The live cut gate is in the sampler, before the matrix element
`$MADGRAPH_INSTALL/Template/LO/Source/dsample.f`, `sample_full` (dsample.f:1):
- `x_to_f_arg(...)` builds the momenta `p` for the sampled point (dsample.f:178).
- `CUTSDONE=.FALSE.; CUTSPASSED=.FALSE.` (dsample.f:179-180), then `if (passcuts(p,VECSIZE_USED))`
  (**dsample.f:181**) gates the point.
- **Pass:** the point is appended to the vector batch (`all_p`, `all_wgt`, `all_x`, ...,
  dsample.f:189-195); the matrix-element integrand (`dsig`/`dsig_vec`) is evaluated only for the
  accumulated batch (dsample.f:206 / 231). So `passcuts` is upstream of the ME — **a cut-failed point
  never costs a matrix-element evaluation.**
- **Fail:** the `else` (dsample.f:264-268): `fx=0d0; wgt=0d0; call sample_put_point(wgt,x(1),...)`.
  The failed point is **stored into the VEGAS grid with weight zero** — NOT silently dropped. VEGAS
  sees it as a zero-weight sample, so cut efficiency enters the integral estimate directly and the
  grid adapts around the cut boundary (the importance-sampling grid learns to avoid the cut-out
  region across iterations).

`passcuts` is called with the per-point momenta in the rest frame (cuts.f:30 header); the
**integration-side hook** `pass_point(p)` (cuts.f:1) is a SEPARATE trivial wrapper: it returns
`.true.` by default with `pass_point = passcuts(p)` commented out (cuts.f:20-21).

## 2. CUTSDONE caching — the cut is evaluated exactly once per point
`common/TO_CUTSDONE/ cutsdone,cutspassed`. `passcuts` short-circuits on it:
`IF (CUTSDONE) THEN PASSCUTS=CUTSPASSED; RETURN; ENDIF` (cuts.f:282-285), else sets `CUTSDONE=.TRUE.`
(cuts.f:286). The sampler primes the cache: after a point passes, dsample.f:218-219 sets
`CUTSDONE=.TRUE.; CUTSPASSED=.TRUE.` before the grouped `prepare_grouping_choice`/`dsig` path. This is
why the grouped driver's own cut check is dead: `super_auto_dsig_group_v4.inc:835`
`c IF (.not.PASSCUTS(P1))` is commented out with `c not needed anymore ... set for debugging only`
(:834) — the cut moved upstream into the sampler, and the cache makes any re-call free.

## 3. Cut-derived `smin` vs the s-hat (tau) sampling bound — the surprise
`setcuts.f` computes a minimum partonic `s` FROM the cut values (pt / E / m_inv / HT cuts) into
`common/to_smin/ Smin` (setcuts.f:44, computed setcuts.f:528-571+; `smin = smin + max(smin_p**2,...)`).
`genps.f` reads it (`common/to_smin/ smin`, genps.f:159-160). **BUT in the standard pp regime it does
NOT truncate the tau range:**
- Standard two-beam pp path is the `else` at genps.f:330 -> `CALL GENCMS(STOT,...,SMIN,SJAC)`
  (genps.f:342).
- Inside `GENCMS` (genps.f:1621): **`TAUMIN = 0d0 !SMIN/S !keep scale fix`** (genps.f:1659) — the
  smin-based lower bound is explicitly commented out. TAU is sampled in `[0, TAUMAX]` (genps.f:1665);
  TAUMAX = `dsqrt_shatmax**2/S` only if the run_card `dsqrt_shat` cap is set, else `1d0`
  (genps.f:1660-1664). `SMIN` is used in GENCMS ONLY for the `S .LT. SMIN` sanity-error (genps.f:1648).
- So in standard pp: **cuts do NOT shrink the s-hat integration range from below; `dsqrt_shat`
  (run_card) is the only s-hat range modifier, and it caps from ABOVE (TAUMAX).** Cuts bite entirely
  through `passcuts` rejection (section 1), not through range truncation.
- The cut-derived `smin/stot` IS used as a real tau lower bound only on the non-pp regimes:
  dressed-ee `ee_picked==2` (`sample_get_x(...,smin/stot,1d0)`, genps.f:274) and the ee x1/x2
  generation (`generate_x_ee(x, smin/stot, ...)`, genps.f:297-298). Don't generalize "smin bounds tau"
  to pp.

(Upper cap, already on beam-shat-rapidity-flux-genmom + genps-momentum-generation pages:
`dsqrt_shatmax` caps TAUMAX in GENCMS and smax in `gen_s` — same run_card value, two sites.)

## 4. Cut efficiency at integration time — `nb_pass_cuts` and `none_pass`
`common/cut_efficiency/ nb_pass_cuts` (genps.inc:48-49). Incremented per cut-passing point in the
grouped driver (`super_auto_dsig_group_v4.inc:848-850`, `:1002-1003`, capped at a hardwired max — read
`super_auto_dsig_group_v4.inc:848-850`), reset to 0 at `sample_full` entry (dsample.f:844, 2744).
Consumed in `sample_put_point` (dsample.f):
- iteration 1, `nb_pass_cuts` past a hardwired threshold with `non_zero.eq.0` -> `call none_pass(<that
  threshold>)` (read the threshold at dsample.f:1931).
- `kn.ge.max_events .and. non_zero .le. <hardwired small count>` -> `call none_pass(max_events)` (read
  the count at dsample.f:1927).

`none_pass` (dsample.f:2424) sets the channel contribution to zero and emits the runtime symptom:
- above that threshold: `<n> points passed the cut but all returned zero ... considering this
  contribution as zero` (dsample.f:2452-2455).
- `0 < nb_pass_cuts < threshold`: `only <n> points passed the cut and they all returned zero ... Loosen
  cuts or increase max_events if you believe this is not zero` (dsample.f:2459-2463).
- else: `No points passed cuts! ... Loosen cuts or increase max_events` (dsample.f:2464-2466).
This is the source-visible "my cut is too tight for this channel's phase space" diagnostic.

## 5. RAMBO + cuts (standalone) — no cuts on that path
RAMBO (`rambo.py`) is the `mg5> check` generator, NOT on the integration/event-gen path
(see rambo-flat-phasespace.md). `rambo.py` has NO cut handling (grep-confirmed: no passcuts/pass_point
/cut), and its caller `process_checks.py` tests the matrix element at the RAMBO point WITHOUT applying
fiducial cuts. So "RAMBO + cuts" is a non-interaction: the standalone check ignores run_card cuts.

## Cautions
- **`pass_point` (dsample.f:433) is DEAD on the live path.** It sits in a second `sample_full` main
  loop (dsample.f:411-455) reached only via `goto 200` (dsample.f:385) — which jumps to label 200 at
  dsample.f:459 (that loop's STATS block), SKIPPING the loop body; and a `stop 1` (dsample.f:387) sits
  before any fall-through. The live cut gate is `passcuts` at dsample.f:181, not `pass_point` at :433.
  (And `pass_point` in cuts.f is the trivial `.true.` wrapper anyway, section 1.) Don't cite the :433
  `pass_point`/`dsig(p,wgt,0)` scalar path as the integration loop.
- The cut does NOT feed ICONFIG channel selection or the x->p mapping shape: channels are chosen by
  the DiscreteSampler grids (driver-and-channel-selection-sampling.md) and the propagator structure;
  cuts only zero-weight the resulting points. A tight cut can therefore make a whole channel return
  `none_pass`-zero without changing which channels are sampled — so cut/channel mismatch shows up as a
  zero channel, not as re-weighted channel selection.
- Mapping vs enforcement, again: a cut that lands ON a propagator peak (e.g. an m_inv cut slicing a
  BW-mapped s-channel resonance) does not change the BW change-of-variable
  (propagator-mappings-gen_s-transpole.md) — it just rejects points post-mapping, so the BW mapping
  wastes its importance-sampling density on the cut-out region (efficiency loss, not bias). This is the
  classic "generation cut interacts badly with a propagator mapping" hazard; the mapping is still
  correct, the efficiency just drops.
