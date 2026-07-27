---
description: Sizing bwcutoff for a sub-threshold/off-shell chain-decayed propagator — the (m_pole-virtuality_floor)/Gamma derivation, the m_tau floor for chained W→τν and the (m_H-m_W) TRAP-floor sharpening, silent-vs-loud default-window geometry, "widen don't forbid" correction, and the excluded-tail quantity (a bwcutoff of n widths excludes only <1/(4n²+1) of peak ≈ 1/900 at n=15, NOT 1/226) that justifies the registered default for narrow resonances (LO, v3.7.1)
---

# Sizing bwcutoff for an off-shell / sub-threshold chain-decayed propagator

Applies the LO BW-window mechanism (bw-onshell-test-cutbw.md, bw-setpeaks-psgrid.md,
bw-margin-constants-map.md) to the practical question: **how large must `bwcutoff` be so a
forced (decay-chain, gForceBW=1) intermediate that is pushed off its pole still gets
sampled?** Anchored on MG5_aMC v3.7.1 runs (default `sm`).

## Why the registered default suffices for an ordinary narrow resonance (the excluded-tail quantity)
This is the complement of the whole page: for an on-pole narrow resonance whose physics
lives AT the pole, the registered `bwcutoff` default (banner.py:4305) is wide enough — you
only derive a larger value when the physics lives IN the tail (sub-threshold /
forced-off-shell daughter, the cases below).

**Physics/numerics-grounded fact (NOT a source line — derived, tool-settled):** a `bwcutoff`
of `n` widths keeps the BW band `|m−M| ≤ nΓ` and excludes only the tail *below*
**`1/(4n²+1)` of the peak height**. At n=15 → **1/901 ≈ 1/900**.

Derivation (relativistic-s narrow-width propagator, the form MadGraph integrates):
`|D(s)|² ∝ 1/[(s−M²)² + M²Γ²]`. At `|m−M| = nΓ`, `s−M² ≈ 2M·nΓ`, so the ratio to the
peak (`s=M²`) is `M²Γ²/[(2MnΓ)² + M²Γ²] = 1/(4n²+1)`. The non-relativistic Lorentzian
written with **HWHM = Γ/2** — `1/[(nΓ)² + (Γ/2)²]` — gives the identical `1/(4n²+1)`.
(Exact relativistic, keeping the dropped `(m−M)²` term, is ≈ 1/1308 for the Z at n=15 —
same order, still the 1/900 family.)

**Convention trap — do NOT quote ~1/226.** `1/226 = 1/(n²+1)` is the Lorentzian written with
the FULL width Γ (not Γ/2) as the denominator scale; that is the non-physical convention for
this purpose and is a factor ~4 too shallow. The tail excluded at n=15 is ~1/900 of peak,
not ~1/226.

**Consequence for sizing:** because the excluded tail is `< 1/(4n²+1)` of peak, for a narrow
resonance sampled at its pole the default ±(default·Γ) window discards a negligible fraction —
that is why the registered default is sensible and why you do NOT raise it for ordinary
s-channel resonances.
You raise `bwcutoff` (or switch to the full off-shell ME) ONLY when the required physics
sits in that tail — a sub-threshold parent or a forced daughter pushed off its pole (every
case in the sizing table below), where the `1/(4n²+1)` suppression at the pole is irrelevant
because the leg is never near its pole to begin with.

## Critical: bwcutoff is never inert regardless of gForceBW value

**gForceBW=0, 1, or 2 — bwcutoff is NEVER inert.** This corrects the prior mistake
"class gForceBW=0 makes bwcutoff inert, so default is fine."

- **gForceBW=1** (decay-chain forced): Regime B uses `bwcutoff` for the window AND
  the grid/guard (myamp.f:189, 403, 419) — obviously bwcutoff matters. But it also
  matters in Regime A: the Les Houches on-shell tag at myamp.f:136-139 uses
  `bwcutoff*prwidth_tmp` for ALL legs regardless of gForceBW. The narrow-resonance
  gate (`Γ/M < 0.1`) is relaxed by gForceBW=1, but the window scale is always
  `bwcutoff*Γ_eff`.
- **gForceBW=0** (ordinary s-channel): Regime B uses hardcoded `5d0*Γ_eff` for the
  enforcement on-shell test (myamp.f:192-193) and the set_peaks grid (myamp.f:405-409).
  **BUT Regime A still uses bwcutoff**: the Les Houches tag (myamp.f:137) and the
  s-hat transform gate (myamp.f:575) are unconditional — bwcutoff scales the window
  for ALL legs, gForceBW=0 included.
- **gForceBW=2** (on-shell forbidden s-channel): Same Regime A applies. The
  gForceBW=2 only adds a hard cut at myamp.f:142-144 (`cut_bw=.true.` when on-shell);
  bwcutoff still governs the Les Houches tag window and the s-hat transform.

**Consequence for sub-threshold decay chains:** When `m_parent < m_daughter_sum`,
the off-shell tail is required. `gForceBW=1` forces the bwcutoff window onto that leg
(Regime B cut_bw enforcement + set_peaks grid lower bound), but **does NOT enlarge the
window**. The registered `bwcutoff` default (banner.py:4305) → a ±(default·Γ) window that
clips the off-shell tail. The fix
is always: **derive `bwcutoff ≥ (m_pole − virtuality_floor) / Γ_eff`**, regardless of
the gForceBW value. (For gForceBW=1 the sizing is mandatory — for gForceBW=0 it is
still relevant via Regime A, even though Regime B uses 5σ.)

## The window geometry (source-confirmed)
A forced (gForceBW=1) s-channel propagator's BW sampling window has lower edge
`m_pole - bwcutoff·Γ_eff` and upper edge `m_pole + bwcutoff·Γ_eff`:
- `$MADGRAPH_INSTALL/Template/LO/SubProcesses/myamp.f:403` (v3.7.1):
  `xm(i) = max(xm(i), prmass(i,iconfig)-bwcutoff*prwidth_tmp(i,iconfig))` — PS-grid lower bound,
  inside the `if (gforcebw(i,iconfig).eq.1)` branch (:402), `bwcut_for_PS(i)=bwcutoff` at :404.
  (The source line is :403, not :401.)
- `Γ_eff = prwidth_tmp = max(prwidth, prmass*small_width_treatment)` (myamp.f:131-135). For an
  ordinary-width resonance Γ_eff is just the real width; the floor only matters for tiny widths.
- `xm(i)` (before the BW widening) is the **kinematic minimum invariant mass** of the
  propagator = sum of its daughters' own mass thresholds. This is the `virtuality_floor`.

## The derivation
For the window's lower edge to reach down to the kinematically-required virtuality, you need
`m_pole - bwcutoff·Γ_eff ≤ virtuality_floor`, i.e.

  **bwcutoff ≥ (m_pole − virtuality_floor) / Γ_eff**   (plus margin)

where `virtuality_floor` = the off-shell daughter's own decay threshold:
- ≈ 0 for a leptonic W/Z (`W→ℓν`, `Z→ℓℓ`: lepton masses negligible).
- **m_τ ≈ 1.777 GeV for a chained `W→τν`** (the W's invariant mass can go as low as its
  own daughter sum m_τ + m_ν ≈ m_τ; SM `restrict_default.dat:22` `15 1.777e+00 # MTA`).
- m_W + m_b ≈ 85 GeV for `top → b W` (the top can only go as low as its own daughter sum).

### TRAP FLOOR: the partner's mass never enters the floor (central light-Higgs derivation trap)
When the chained off-shell propagator is a W (or Z) whose **partner** also has mass, an agent
is tempted to use `(m_parent − m_partner)` as the lower endpoint of the off-shell invariant
mass. **This is wrong** — that is the off-shell leg's mass *only in the special case its
partner sits exactly on its pole* (a BW-suppression heuristic, not a kinematic boundary). The
TRUE minimum of the off-shell propagator's invariant mass is its OWN daughter threshold,
reached when the partner carries most of the available invariant mass.
- **Rule (general):** `virtuality_floor` = the off-shell propagator's OWN daughter mass-sum,
  full stop — the partner's mass never enters the floor. Using `(m_parent − m_partner)` puts
  the window's lower edge ABOVE the kinematic floor and **silently under-counts** (partial
  coverage, no abort, no warning).
- **One marked example — chained `W→τν`:** floor = m_τ (the W's invariant mass can fall to its
  own daughter sum m_τ+m_ν ≈ m_τ), so the requirement is `bwcutoff ≥ (m_W − m_τ)/Γ_W`, NOT
  `(m_parent − m_W)/Γ_W`. (m_W is the SM *internal* parameter computed from aEWM1/Gf/MZ via
  coupl.inc — `models/sm/parameters.py` `MW = Parameter(...)`, not a param_card MASS line; read
  m_W and Γ_W fresh from the operative card, they are version/card-dependent numbers.)

This is the SAME quantity the impossible-onshell guard tests: myamp.f:417-427 fires
`write_null_results()` (:426) + `stop` (:427) when `prmass + bwcutoff·Γ_eff < xm(i)` for a gForceBW=1 leg —
i.e. when even the FULL window cannot reach the kinematic minimum. Widening bwcutoff until
`bwcutoff·Γ_eff ≥ m_pole − xm` is exactly what clears that guard.

## Applying the rule per-propagator (derivation, not a lookup table)
For each forced off-shell leg, compute `bwcutoff ≥ (m_pole − virtuality_floor)/Γ_eff` from the
operative card's m_pole and Γ (read fresh — a wrong-template param_card gives a wrong Γ and
therefore a wrong derived bwcutoff). The result is a per-leg quantity, NOT a fixed number
reusable across processes. The three `virtuality_floor` classes (symbolic, version-independent):
- leptonic off-shell W/Z (`virtuality_floor ≈ 0`): need ≈ m_pole/Γ.
- chained `W→τν` (`virtuality_floor = m_τ`): need ≈ (m_W − m_τ)/Γ_W (the trap-floor case above).
- off-shell top in `H→tt*` (`virtuality_floor = m_W + m_b`): need ≈ (m_t − m_W − m_b)/Γ_t.
Plug the operative m_pole/Γ into the formula to get the number; the formula is the durable
artefact, the number is not.

## Meta-trap: no single bwcutoff value is universal (highest-value caution)
A value chosen to cover one off-shell case is NOT reusable. A bwcutoff that fully contains a
light leptonic off-shell W/Z (its lower edge below 0) can still CLIP the allowed band of an
off-shell top — the top's narrower Γ and larger pole-to-floor distance push the required
bwcutoff higher, so a leptonic-tuned value biases the top σ **silently** low (partial
coverage, no warning). An agent who memorises a single "set bwcutoff=N" passes the case it was
tuned on and under-counts the others. The value MUST be derived per-propagator from
`(m_pole − virtuality_floor)/Γ`, never copied — and the registered default (banner.py:4305,
read it there) is sized for on-pole narrow resonances, not off-shell tails.

## Silent vs loud: how a too-narrow window fails (geometry, not announcement)
The window is `m_pole ± (bwcutoff·Γ)` (bwcutoff read at banner.py:4305). Whether an
insufficient bwcutoff produces a small nonzero σ (silent) or a hard stop (loud) is a pure
overlap question between the window and the kinematically-allowed region:
- **Window overlaps ANY sliver of the allowed region → small nonzero σ (SILENT).** A leptonic
  sub-threshold W/Z: the off-shell daughter can sit in the window's upper part while its
  partner is light, so a thin slice leaks through — a small-fraction-of-true σ, no warning.
- **Allowed region sits entirely outside the window → hard stop (LOUD).** When even the full
  window cannot reach the daughter floor (an off-shell leg far below its pole), the
  impossible-onshell guard (myamp.f:417-427) calls `write_null_results()` then `stop`.
  Source-literal message at myamp.f:599 is `'Impossible BW configuration'`; results.dat is
  written all-zero (myamp.f:600-603).

So "did the run give a small number or zero" is itself a fingerprint of which geometry you're
in — the failure does NOT reliably announce itself; a silent small-fraction σ looks like a
converged run.

RUNTIME-PREDICTION CAVEAT: the exact top-level user-facing wording (e.g.
`"Zero result detected: No Phase Space"`) is a Python-layer roll-up of the zero results.dat
(the literal `"No Phase Space"` string lives in madevent_symmetry.f:279, a different stage),
NOT a string emitted at myamp.f:426. The source-confirmed loud artefact is the
`Impossible BW configuration` print + all-zero results.dat + `stop`. Any specific fraction-of-
true σ for the silent case is a runtime prediction — treat as hypothesis for a NEW process
until probed.

## Mental-model correction: a sub-threshold chain is NOT forbidden, and NOT the NWA
A documented agent failure mode: an agent correctly notes m_parent < 2·m_daughter, then
WRONGLY concludes the chain forces both daughters on-shell with a narrow ~Γ spread,
declares the configuration "kinematically forbidden / impossible," and refuses to widen
bwcutoff (often proposing an off-shell ME-internal substitute amplitude that violates the
chain-decay spec). **This is wrong.** Chain decay wraps each intermediate in a BW-sampled
propagator (set_peaks builds a BW grid for the forced leg, myamp.f:399-449); its invariant
mass is bounded only by `bwcutoff·Γ_eff` from the pole, so it reaches arbitrarily far
off-shell once the window is opened. The impossible-onshell guard fires only because the
DEFAULT window is too narrow to reach the daughter floor — widening bwcutoff until
`bwcutoff·Γ ≥ m_pole − virtuality_floor` clears it and the off-shell region samples normally.

The fix for a sub-threshold chain is ALWAYS: **widen bwcutoff and keep the chain.** It is
never "the chain is forbidden" and never "substitute an off-shell ME." (Width computation /
the NWA σ-correction itself is a separate axis — the NWA reweight lives in the sampling
layer, bw-transpole-nwa-jacobian.md, and floors tiny widths; it does NOT collapse a forced
leg to its pole.)

## Boundaries
- LO only. bwcutoff is the forced-leg window at the grid/enforcement sites (Regime B,
  bw-bwcutoff-scaling-regimes.md). NLO uses a single `bwcutoff*real_width` with no Γ_eff
  floor (bw-nlo-window-sites.md) — this sizing logic does not transfer unchanged.
- m_pole and Γ come from the operative param_card via coupl.inc; a wrong-template param_card
  gives a wrong Γ and therefore a wrong derived bwcutoff even when this logic is applied
  correctly. Width computation is madwidth's slice.
- Which chain-decay SYNTAX produces gForceBW=1 (so this sizing even applies) is chain-decay's
  slice; here we assume the leg is already forced (gForceBW=1) and consume that.
