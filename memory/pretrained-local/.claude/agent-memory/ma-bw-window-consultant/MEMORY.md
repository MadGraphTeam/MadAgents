## Slice
I own: bwcutoff / small_width_treatment / cut_decays run-card knobs (banner.py), the
cut_bw on-shell test in myamp.f (bwcutoff×Γ_eff window + Γ/M narrow gate + gForceBW flag +
lbw require/exclude encoding), the cut_decays↔BW interaction in setcuts.f, and consume
gForceBW (decayBW.inc, static) + lbw (runtime DeCode, NOT decayBW.inc) read-only.
Out of slice: WRITING decayBW.inc / chain-decay choice (chain-decay), phase-space channel
decomposition (phase-space), kinematic cut values pt/eta/dr (kinematic-cuts), MadSpin
BW_cut/spinmode (MadSpin), width computation (madwidth), NLO/FKS BW (amcatnlo/fks).

## Core operating principles
- Source is truth; verify against $MADGRAPH_INSTALL for THIS input every time. Adopt a
  scope-matching cached page per ma-wiki-as-evidence (sanity-check one file:line); else walk.
- Return shape: ## Source-walked facts (file:line cites) then ## Implications
  (DIRECT/INFERRED/HYPOTHESIS labels). Reject unmarked out-of-slice claims explicitly.
- bwcutoff is NEVER inert regardless of gForceBW value (0, 1, or 2) — repeated mistake is
  "gForceBW=0 makes bwcutoff inert." LO myamp.f has TWO regimes (bw-bwcutoff-scaling-regimes.md):
  Regime A UNCONDITIONAL (Les-Houches tag myamp.f:137 + s-hat transform gate myamp.f:575 —
  scales the window for ALL legs/poles) vs Regime B forced-only (cut_bw enforcement onshell,
  set_peaks grid, impossible-onshell guard — bwcutoff when gForceBW=1, else hardcoded 5σ).
  Changing bwcutoff always changes the Regime A sites; "bwcutoff doesn't widen ordinary
  s-channel resonances" is true for Regime B ONLY — classify the stage first. Trigger: ANY
  sub-threshold or off-shell chain-decay → derive bwcutoff, NEVER propose default.
- Two LO layers (bw-param-layer-map.md): window/classification (myamp.f+run.inc) vs
  sampling/jacobian (transpole.f+dsample.f). bwcutoff is window-layer ONLY → can NEVER touch
  the jacobian/sampled-peak; small_width_treatment spans both (floor+gate in window vs
  floor+NWA σ-reweight in sampling). Place the stage in a layer before answering reach.
- Γ_eff = max(prwidth, prmass*small_width_treatment); prmass/prwidth come from the
  operative param-card via coupl.inc — a wrong-template param_card gives surprising widths
  even when bwcutoff machinery is correct.
- Runtime predictions (warnings, null-channel stops, σ) are hypotheses until probed; mark
  inline if written without a probe.

## Recent lessons (FIFO, max 5)
- smallwidth-zero-vs-tiny: small_width_treatment (default at banner.py:4452, hidden, NWA
  comment) rescues tiny-NONZERO widths ONLY. Sampling floor+NWA jac (transpole.f:44-47) is
  gated by swidth>0 (dsample.f:1393); swidth=prwidth REAL (set_peaks keeps real width
  myamp.f:411/417). Exactly-zero s-channel width → swidth=0 → transpole SKIPPED → setgrid
  power-law fallback (myamp.f:450-456 "no BW radiation") → NO NWA correction, NO error/warning
  → unregulated 1/(s−M²) pole, fluctuating σ. Window layer floors independently (prwidth_tmp=
  max(prwidth,prmass*swt) myamp.f:132/330/398 IS >0) but that floor never reaches sampling jac.
  Width is NOT replaced in the ME propagator denom (coupl.inc fixed Γ) — only sampling+window;
  σ reconciled by jac*=width/width1. CMS(complex mass in propagator) is model-loader, not mine.
  Trigger: any zero/tiny-width s-channel or "does swt fix my delta-pole" claim.
- lhe-istup2-is-bwcutoff-gated: bwcutoff is NOT confined to PS mapping/SPROP classification —
  it write-gates the LHE ISTUP=2 intermediate record (LO ickkw=0). Trigger: any "does bwcutoff
  affect the LHE / status-2 / resonant-mother record" claim. Correct: myamp.f:129-140 FIRST
  "LesHouches" onshell (bwcutoff×Γ_eff + Γ/M<0.1 gate + idenpart de-dup) sets OnBW → addmothers.f:253
  jpart(6,i)=2 else 3; status-3 dropped(:346/:362). SECOND onshell (:186-193, 5σ/bwcutoff) is a
  SEPARATE var feeding the cut_bw event-cut via lbw — don't conflate. Matched ickkw>0 → isbw/clustering.
- lbw-not-in-decaybw-inc: a built decayBW.inc has ONLY GFORCEBW data lines; lbw is set at
  RUNTIME in madevent_driver.f:347 (base-3 DeCode of dconfig), NOT written to the .inc.
  Trigger: claiming an array's PROVENANCE. Correct: read a built artefact (find -name
  decayBW.inc) before asserting what a generated .inc carries — gForceBW (static) and lbw
  (runtime) share to_BW-style consumption but have different origins.
- onbw-seam-grep-membership: unwgt.f has ZERO to_BWEvents/OnBW refs; common/to_BWEvents/ is
  shared by myamp.f/cluster.f/addmothers.f only. unwgt.f reaches OnBW INDIRECTLY (calls
  cut_bw then addmothers, which reads OnBW). Trigger: asserting a common-block SEAM. Correct:
  grep -rln the block name for actual membership; "calls X which shares the block" ≠ "shares it."
  (bwcutoff-derivation lesson retired to FIFO → see bw-cutoff-sizing-derivation.md in index.)

## Wiki page index
- bw-runcard-knobs: Registration/defaults/Fortran wiring of bwcutoff(default@banner.py:4305)/small_width_treatment(default@:4452,hidden,NWA)/cut_decays(@:4306); wrong-key typo→silent fallback-to-registered-default (banner.py:2906 lower() match).
- bw-onshell-test-cutbw: cut_bw on-shell test in myamp.f — bwcutoff×Γ_eff window, Γ/M<0.1 narrow gate, gForceBW flag, lbw 1=require/2=exclude, zero-vs-tiny-width consumption gate.
- bw-cutdecays-interaction: cut_decays gates kinematic cuts on decay legs via from_decay (setcuts.f, check_decay:993 ← gForceBW=1); default False drops them. DY σ arrow 1131 / comma 2840 / +cut_decays=True 1123.
- bw-setpeaks-psgrid: set_peaks PS-grid bwcutoff/5σ windows, impossible-onshell write_null_results+stop, s-hat 1/s-vs-BW transform gate using small_width_treatment.
- bw-bwcutoff-scaling-regimes: 6 bwcutoff sites in LO myamp.f → Regime A (unconditional: L137 tag + L575 s-hat gate) vs Regime B (gForceBW=1-only, else 5σ); per-page "forced-only" caution omits Regime A.
- bw-margin-constants-map: the four LO BW constants (bwcutoff / 5σ / 3σ@symmetry:381 / 0.1d0 Γ/M gate) mapped to (stage × leg-class) cells across myamp.f+madevent_symmetry.f; cross-stage window answers.
- bw-cutoff-sizing-derivation: SIZE bwcutoff for off-shell/sub-threshold forced leg — DERIVE bwcutoff ≥ (m_pole−virtuality_floor)/Γ_eff per-leg (floor xm myamp.f:403, guard :417-427); no universal value (canonical 50/75 NOT reusable — leptonic-tuned under-covers off-shell top); silent-vs-loud (:599-603); W→τν floor=m_τ NOT (m_H−m_W); widen-don't-forbid; excluded-tail 1/(4n²+1)≈1/900 at n=15 (NOT 1/226) justifies the default for on-pole narrow resonances.
- bw-transpole-nwa-jacobian: BW sampling transform transpole/untranspole (transpole.f, driven by dsample.f:1396) — small_width floor + NWA σ-correction jac*=width/width1; bwcutoff absent here. Floor protects tiny-NONZERO only (swidth>0 gate dsample.f:1393); exactly-zero→setgrid fallback (myamp.f:450-456) no warning; width NOT replaced in ME propagator (coupl.inc), sampling+window only.
- bw-param-layer-map: two-layer axis — window/classification (myamp.f+run.inc) vs sampling/jacobian (transpole.f+dsample.f); bwcutoff Layer-1 ONLY (grep=0 in L2), small_width spans BOTH.
- bw-nlo-window-sites: NLO BW sites (cluster.f:692, add_write_info.f:808) use plain bwcutoff×real-width — no Γ_eff/small_width/Regime A-B/5σ/gForceBW consumer; granny flag override; export_fks.py:3966 emits (not consumed).
- bw-smallwidth-python-warnings: Python small_width warning surface (common_run_interface.py) — FAQ-3053 WARNING (:6527/:7332) + 1e-12 ERROR (:3790) + 1e-11 CRITICAL; NLO sets knob 0 so never fires; small_width_treatment default (@:4452) = floor AND warn-threshold.
- bw-symmetry-failconfig: THIRD bwcutoff/gForceBW consumer — BW_Conflict(:286, 3σ) + failConfig(:434, gForceBW=1→bwcutoff else 5σ, DROPS configs) in madevent_symmetry.f at symfact.dat time; forced-only; NLO has none.
- bw-gforcebw-lbw-provenance: gForceBW STATIC in decayBW.inc from onshell flag (export_v4.py:5884 →0/1/2); lbw RUNTIME base-3 DeCode (madevent_driver.f:347), NOT in .inc. Single-$ KEEPS diagram→gForceBW=2 (diagram_generation.py:792); $$ REMOVES (:742-775).
- bw-cutbw-callers: cut_bw's 3 LO callers + dual nature — cuts.f:509 (only return-as-cut) vs cluster.f:423 + unwgt.f:737 (bare, populate OnBW); to_BWEvents shared by myamp/cluster/addmothers ONLY (unwgt reaches OnBW via addmothers); no LO BW_cut token.
- bw-lhe-istup2-gating: LHE intermediate ISTUP=2 IS write-gated by bwcutoff (LO ickkw=0) — myamp.f:129-140 "LesHouches" onshell (bwcutoff×Γ_eff + Γ/M<0.1 gate) → OnBW → addmothers.f:253 status2/3, status3 dropped(:346,:362); matched ickkw>0 uses isbw/clustering not this window. Doc "within M±bwcutoff·Γ" incomplete (Γ_eff/narrow-gate/idenpart).
- bw-madspin-bwcut-inheritance: MadSpin BW_cut default=-1 sentinel (interface_madspin.py:64) → inherits run_card bwcutoff (:251-252) if banner has run_card, else hardcoded fallback (:265-266); bwcutoff default @banner.py:4305/5713. MadSpin's ±BW_cut·Γ mass window (decay.py:534-535, RAW width, floor 0.5) is DISTINCT from myamp.f cut_bw. >25 critical warn (:254), >100 raise (:653). MadSpinOptions parsing = madspin-interface.
