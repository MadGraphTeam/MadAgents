---
description: A chain-decayed intermediate cannot reach its pole. The parent mass forbids both daughters on-shell.
---

# Off-shell decay windows — bwcutoff must be derived, not defaulted or memorised

This trap family spans several off-shell-decay scenarios — H→WW* and H→ZZ* at m_H=125, ZH with a 4τ chain, heavy-H→tt* off-shell, and W in a **light-Higgs** scenario m_H=100. All turn on the **same** load-bearing run-card value (`bwcutoff`) being set from kinematic reasoning. This is the single most reproducible "off-shell window" trap family. An instance of the broader `derived-quantity-staleness.md` discipline (a per-process value that must be derived, never defaulted/memorised).

## When it applies (the regime trigger)

A `generate` line **chain-decays an intermediate resonance** (`(h > z z, z > ...)`, `(h > w+ w-, ...)`, `(h > t t~, (t > b w+), ...)`) AND the parent mass forces the kinematic constraint

  m(daughter₁) + m(daughter₂) ≤ m(parent)

to push at least one daughter **off its pole by many widths**. Classify into one of:

- **Sub-threshold parent** — m(parent) < 2·m(daughter). The two daughters cannot both be on-shell; one sits near pole, the other runs deep off-shell down to *its own* decay floor.
  - `H→W⁺W⁻*` at m_H=125 (< 2m_W=160): off-shell W → ~0 (leptonic floor).
  - `H→ZZ*` at m_H=125 (< 2m_Z=182): off-shell Z → ~0 (leptonic floor).
- **Heavy-parent → heavy-daughter with a *massive* decay floor** — both daughters off-shell but bounded below by a non-zero decay threshold.
  - `H→t t̄*` at m_H=250: each top must reach ≥ m_W+m_b ≈ 85 GeV to decay to bW on-shell → both tops confined to [85, 165] GeV. The floor is **85, not 0**.

Surface keywords that should fire this playbook: "off-shell", "sub-threshold", "below threshold", "H→WW/ZZ/tt at LO", "heavy Higgs", "decay through ... chain", "the rate came out tiny / zero", "Zero result detected: No Phase Space" on a decay chain.

## The load-bearing derivation (physics; the bw-window consultant authors the source side)

The kinematics is textbook; the mapping to the knob is the consultant's. Required:

  **bwcutoff ≥ (m_pole − virtuality_floor) / Γ**   (then add margin)

where `virtuality_floor` is the *minimum invariant mass the off-shell daughter can take* = its own decay threshold (≈ 0 for leptonic W/Z; m_W+m_b ≈ 85 for top→bW). `bwcutoff` opens the BW sampling window to `m_pole ± bwcutoff·Γ` (MadGraph-fact — route to bw-window). The registered run-card **default is not near any of these** (read it fresh at its registration site via bw-window — it is a small O(10) value tuned for on-shell resonances, NOT an off-shell window), which is why an off-shell chain must set it explicitly.

**Worked once — illustrative, recompute `(m_pole − virtuality_floor)/Γ` per propagator, never lift a number:** a heavy-parent→massive-floor case such as `H→t t̄*` at m_H=250 has each top at m_pole≈173, Γ≈1.49 and a *massive* floor m_W+m_b≈85, giving (173−85)/1.49 ≈ **59** — the window must exceed ~59Γ (then add margin). Contrast the leptonic-floor sub-threshold cases (H→ZZ*/WW* at 125): floor≈0 gives (m−floor)/Γ ≈ 37–39, so ~40Γ suffices. The two differ by the floor, not by any tabulated recipe — **derive both, cache neither.** (m_W is an *internal* SM parameter computed from G_F/α/M_Z — read it in the generated `param_card.dat`, NOT a card MASS line; so a light-Higgs m_H edit does not move m_W, and the floor for a leptonic W* stays ≈m_τ regardless.)

### The floor is the daughter's OWN decay threshold — not (m_parent − m_partner-on-pole)
W→τν case. The `virtuality_floor` of a chained off-shell propagator is the mass-sum of *its* daughters (m_τ≈1.78 for W→τν; ≈0 for W→eν/μν), reached *regardless of where the partner propagator sits*. The seductive wrong floor is **(m_H − m_W) ≈ 19.6 GeV** — the off-shell W's mass *when its partner is exactly on pole* — a BW-suppression heuristic, not a kinematic boundary. Using it gives bwcutoff ≈ (80.42−19.6)/2.05 ≈ 29.7 → an agent lands between the default and the ~38 correct minimum, which **does not abort** — it opens a non-zero window that silently clips the low-m_W* tail (~80–90 % of canonical σ just above the default, no warning). Correct floor m_τ gives min bwcutoff = (80.42−1.78)/2.05 ≈ 38.4. Grounded `myamp.f:403` (window lower edge `xm(i)=max(xm(i), prmass−bwcutoff*prwidth_tmp)` inside the `gforcebw.eq.1` branch) — `../consultants/ma-bw-window-consultant/bw-cutoff-sizing-derivation.md`.

### gForceBW=0 (the 4-body / non-chain form) ⇒ bwcutoff is INERT
The off-shell daughters are BW-windowed by `bwcutoff` **only when they are gForceBW=1 chain-decay resonances**. The valid *alternative* setup — a 4-body H-decay matrix element (`h > ta+ vt ta- vt~ / ta+ z`) instead of a W-chain — leaves the W's as ordinary internal propagators with `gForceBW=0`; the `cut_bw` window check (`myamp.f:179`, guarded on `gForceBW.eq.1`) never fires for them and they get a hardcoded 5σ window, so **`bwcutoff` has no effect**. The off-shell-W coverage skill is then REPLACED by a Γ_H-normalisation skill (the H resonance becomes the only forced-BW propagator; its rate ∝ 1/Γ_H — see `decay-widths-lifecycle.md` BR-denominator + `derived-quantity-staleness.md`). So the two valid paths exercise *different* derived quantities: chain → bwcutoff; 4-body → Γ_H. Grounded `../consultants/ma-bw-window-consultant/bw-gforcebw-lbw-provenance.md`.

### The meta-trap: **the canonical 50 is NOT universal**
50 covers the Z (37Γ) and W (39Γ) cases because both happen to land near 40 — so an agent who *memorises* "set bwcutoff=50" passes both. The heavy-Higgs top case needs **59Γ → 50 is demonstrably insufficient** (opens to [98,248], still clips the [85,98] slice; σ biased low). **The only robust move is to derive bwcutoff freshly from (m_pole, Γ, floor) for the specific propagator.** Treat any answer that cites "50" without a derivation as a memorisation suspect, even when 50 happens to be right.

### The default fails SILENTLY or LOUDLY — and which one depends on window overlap
The default window `m ± bwcutoff·Γ` (at the default bwcutoff) either admits a sliver of the kinematic region (→ small nonzero σ, **silent**) or none of it (→ `Zero result detected: No Phase Space`, **loud**):
- leptonic-floor sub-threshold (W/Z → ~0): default window's *upper* part still overlaps where the off-shell daughter sits when its partner is light → **small nonzero σ** (~1–3 % of true), no warning. **Silent — the dangerous mode.**
- massive-floor, kinematic region sits *below* the default window: heavy-H→tt default [150.6,195.4] vs kinematic [85,165] overlaps only the [150.6,165] sliver → essentially no weight → **Zero result (loud)**.

So "did the default give zero or a small number" is itself a fingerprint of floor-vs-window geometry — do not assume the failure announces itself.

## Dispatch sequence

1. **Classify the regime first** (sub-threshold vs heavy-parent off-shell) — ma-physics-consultant if the kinematic window is non-obvious; otherwise the lead classifies from the masses.
2. **ma-bw-window-consultant authors the `bwcutoff` value** — give it (m_parent, daughter masses+widths, daughter decay floor) as inputs and ask it to derive bwcutoff from the kinematic floor. Do NOT hand it a candidate number to validate (marked-premise discipline would make it bless a memorised 50). The derivation + meta-trap + window geometry + chain-BW-≠-NWA correction live in `../consultants/ma-bw-window-consultant/bw-cutoff-sizing-derivation.md` (window lower edge `m_pole − bwcutoff·Γ_eff` at `myamp.f:403`, Γ_eff = max(Γ, m·small_width_treatment); the impossible-onshell kinematic guard at `:417-427`, `write_null_results`+`stop`, literal `'Impossible BW configuration'` at `:599` — line numbers drift, consultant page is authoritative). Note: the user-facing "Zero result detected: No Phase Space" wording is a Python roll-up. Related: `bw-param-layer-map.md`, `bw-gforcebw-lbw-provenance.md`.
3. **ma-chain-decay-consultant for the topology** — the chain syntax that makes the off-shell daughters *resonant intermediates* (so the BW window is the operative effect), and the parenthesisation grammar (see `process-line-scope-traps.md` case 3 + `decay-chain-seams.md`). Nested sub-decays (top→bW inside H→tt) need their own parens.
4. **ma-param-card-consultant if the parent mass is non-default** — a heavy-Higgs (m_H=250) needs a `param_card.dat` MH edit. Forgetting it silently computes for m_H=125, where the chain may be *kinematically forbidden* → `Zero result` (same surface symptom as default-bwcutoff, different cause — disambiguate via the agent's reported edits, not σ alone).

## Anticipated traps (named by behavioural shape)

- **Default bwcutoff left in place** — silent (~1–3 % σ) or loud (Zero result). The headline trap. → bw-window.
- **Memorised bwcutoff=50** — passes Z/W, fails heavy-top (59Γ). Derive per-process. → bw-window.
- **Insufficient bump (20–30)** — recognised the issue, undershot the floor. σ biased low. → bw-window.
- **Wrong floor (m_parent − m_partner) → bwcutoff between the default and the ~38 minimum** — derived the formula correctly but used the BW-suppression heuristic (m_H−m_W) as the floor instead of the daughter threshold m_τ. **Does not abort**; silently clips ~10–30 % of σ. → bw-window (see floor sharpening above).
- **Wrong-parameter-name typo → silent fallback to the default** — agent intends to set bwcutoff but writes an underscore/truncation variant (`BW_cut`, `bw_cut`, `bw_cutoff`); the parser prints `Found unexpected entry in run_card` then `run_card missed argument bwcutoff. Takes default: <value>` (the default echoed back) and runs at the default → same Zero result as leaving it default. **CAVEAT:** `banner.py:2906` lowercases the key *before* matching, so camelCase variants `bwCutoff`/`BWcutoff` actually MATCH and set correctly — only underscore/truncation forms fall through. So a textual "answer says bwcutoff=50" can hide either a real set (camelCase) or a silent fallback (underscore). → bw-window `bw-runcard-knobs.md`.
- **Honest-refusal misdiagnosis** — the agent correctly notes m_parent < 2·m_daughter, then **wrongly concludes the chain decay is "impossible"** and refuses to widen bwcutoff (or substitutes a non-chain inclusive amplitude). The mental-model error: *confusing chain-decay BW sampling with the narrow-width approximation*. **Chain decay does NOT force daughters on-shell** — it wraps each in a BW-sampled propagator whose invariant mass is bounded only by bwcutoff·Γ from the pole, so it can reach far off-shell once the window is opened. The fix is *widen bwcutoff and keep the chain*, never "refuse / substitute". If a consultant or draft frames a sub-threshold chain as forbidden, this is the error — re-dispatch bw-window with the NWA-vs-chain-BW distinction stated. → bw-window (mental model).
- **Inclusive / s-channel-filter amplitude to dodge the issue** — `h > l+ vl l- vl~` or `h > z > 4τ` instead of the explicit `WW`/`ZZ` chain. Loses topology restriction (admits Yukawa / ZZ contamination) — a *different* trap family, see `process-line-scope-traps.md`. Watch for an agent reaching for these to "sidestep bwcutoff".
- **Forgotten param-card mass edit** (heavy-parent) → Zero result for a different reason. → param-card.

## Setup-only tasks close the σ-feedback loop on purpose
When the user asks only for the setup ("don't run MG5"), the natural way to find the right bwcutoff — launch, see σ collapse, and fix — is foreclosed. The bwcutoff value must then come from the kinematic derivation, not from iteration. Do not let a setup-only answer ship without the derived bwcutoff and a one-line kinematic justification.

## Connection to silent run-card defaults
`bwcutoff` left at its default is the canonical **silent regime-wrong default**: a run-card default whose value silently changes the physics for the regime the user is in, producing a clean-running plausible-but-wrong σ. Its sibling instance is `cut_decays=False` (see `fiducial-cuts-fanout.md`). This is the *inverse direction* of `config-value-lifecycle-layers.md` ("I set X but the run did Y") — here it is "I never touched X and the default was wrong for my regime." Diagnostic discipline for both: **when a result is suspiciously small/large/zero, suspect a regime-wrong default before suspecting the amplitude** — and on a decay chain, suspect bwcutoff first.
