---
description: Registration, defaults, and Fortran wiring of bwcutoff / small_width_treatment / cut_decays run-card knobs (banner.py, run.inc), v3.7.1; plus wrong-key typo → silent fallback to the registered bwcutoff default (case-insensitive lower() match at banner.py:2906, so bwCutoff/BWcutoff MATCH but bw_cutoff/bw_cut/BW_cut fall through)
---

# BW-window run-card knobs (registration + defaults)

All cites `$MADGRAPH_INSTALL/madgraph/various/banner.py` (LO `RunCard`) and the NLO
re-registration, v3.7.1.

## bwcutoff
- `banner.py:4305`: `self.add_param("bwcutoff", <default>)` — LO registration (visible,
  not hidden), in the `#cut` block. Read the default at that line (or `display run_card
  bwcutoff` / the rendered `run_card.dat` bwcutoff line).
- `banner.py:5713`: `self.add_param('bwcutoff', <default>)` — re-registered for `RunCardNLO`,
  same default; read it at that line.
- Meaning: half-width of the mass window (in units of effective width Γ_eff) used by the
  on-shell test. See bw-onshell-test-cutbw.md.

## small_width_treatment
- `banner.py:4452`: `self.add_param('small_width_treatment', <default>, hidden=True,
  comment="generation where the width is below VALUE times mass will be replace by VALUE
  times mass for the computation. The cross-section will be corrected assuming NWA. Not
  used for loop-induced process")`. Read the default at that line.
- **hidden** (not written to a default run_card unless surfaced).
- **LO-only knob.** Registered for the LO `RunCard` only; NOT re-registered for `RunCardNLO`.
  `grep -rl small_width_treatment Template/` returns only LO files (run.inc, transpole.f,
  myamp.f); **zero hits in any `Template/NLO/` file** (verified). So the Γ_eff floor
  and NWA σ-correction it drives exist only in the LO path — NLO BW windows use the real width
  with no floor (see bw-nlo-window-sites.md).
- NWA-correction comment is explicit in source: widths below `VALUE*mass` are floored to
  `VALUE*mass` for the computation, and σ is corrected assuming NWA.
- Used to floor Γ_eff: in `cut_bw` `prwidth_tmp = max(prwidth, prmass*small_width_treatment)`
  (myamp.f:132). Also appears in the s-hat 1/s-vs-BW transform gate (myamp.f:575).

## small_width_treatment has NO sentinel (do not confuse with BW_cut −1)
`small_width_treatment` is a **floor MULTIPLIER**, not a sentinel param. There is no
zero/negative-triggered branch; `add_param('small_width_treatment', <default>, hidden=True)`
(banner.py:4452) registers a plain float. The `−1` sentinel belongs to MadSpin's `BW_cut`
(interface_madspin.py:64), a DIFFERENT parameter (bw-madspin-bwcut-inheritance.md).
- Value 0 (or ≤0): `Γ_eff = max(prwidth, prmass*small_width_treatment)` (myamp.f:132) →
  `max(prwidth, 0) = prwidth` → the floor is DISABLED, raw width used in both window and the
  s-hat gate (`spole(i)*small_width_treatment`→0 at myamp.f:575). No error/branch fires from a
  zero value; it simply removes the tiny-width protection. (Setting it to a small positive value
  is the floor; setting it to 0 turns the floor off — the numeric knob IS the semantics.)

## cut_decays
- `banner.py:4306`: `self.add_param("cut_decays", False, cut='d')` — LO default **False**.
- The `cut='d'` annotation ties it to decay-product kinematic cuts. When False (default),
  kinematic cuts are NOT applied to particles flagged as coming from decays. See
  bw-cutdecays-interaction.md.
- Not re-registered in the NLO RunCard region scanned (no `cut_decays` near 5713).

## sde_strategy (referenced by the on-shell test, not owned here)
- `banner.py:4458`: `self.add_param('SDE_strategy', <default>, allowed=[1,2],
  fortran_name="sde_strat", comment=...)`. Read the default at that line (allowed set [1,2]).
- Relevant because `cut_bw` only hard-cuts on-shell-forbidden s-channels (gForceBW=2) when
  `sde_strat.eq.1` (myamp.f:142). Channel-strategy ownership is the phase-space slice; we
  note it only as a gate condition.

## User-facing run_card.dat default-template text
`$MADGRAPH_INSTALL/Template/LO/Cards/run_card.dat`, v3.7.1. NOTE: this template carries
Jinja-style placeholders, not literal values — the numbers below are what the rendered
run_card a user reads shows, filled from the registered defaults (4305/4306):
- Line 97 header: `# BW cutoff (M+/-bwcutoff*Gamma) ! Define on/off-shell for "$$" and decay`.
- Line 99 (template): `%(bwcutoff)s  = bwcutoff      ! (M+/-bwcutoff*Gamma)` → renders the
  registered bwcutoff default (banner.py:4305).
- Line 104 (template): `%(cut_decays)s  = cut_decays    ! Cut decay products` → renders the
  registered cut_decays default (banner.py:4306).
- The header comment ties bwcutoff explicitly to `"$$"` and `decay` (decay-chain).
  CAUTION — the header's `"$$"` attribution is imprecise for v3.7.1: source-walk
  (bw-gforcebw-lbw-provenance.md) shows the operator that KEEPS a diagram and makes its
  propagator consume bwcutoff (onshell=False → gForceBW=2 + ALOHA P1D routine) is the
  SINGLE-`$` (`forbidden_onsh_s_channels`, diagram_generation.py:792). Double-`$$`
  (`forbidden_s_channels`, diagram_generation.py:742-775) REMOVES the diagram entirely — it
  does NOT consume bwcutoff. (Required-s-channel syntax is `> >`, a third thing.) So the
  run_card comment's "$$" is at best loose colloquial "$/$$ dollar syntax"; the bwcutoff
  consumer is `$` + `decay`, not `$$`. The `decay` (decay-chain) part IS the gForceBW=1
  forced legs. This is the user-facing confirmation of the forced-leg coupling that
  bw-bwcutoff-scaling-regimes.md derives from the Fortran: bwcutoff's *enforcement/grid*
  effect is on forced legs (Regime B). The
  comment does NOT advertise the unconditional Regime-A uses (Les-Houches tag line 137,
  s-hat transform gate line 575) — so reading the run_card alone undersells where bwcutoff
  bites. small_width_treatment is hidden, so it has no run_card line at all by default.

## Fortran wiring
- `$MADGRAPH_INSTALL/Template/LO/Source/run.inc:36-37`: `bwcutoff` in
  `common/to_bwcutoff/`.
- `run.inc:106-107`: `small_width_treatment` in `common/narrow_width/`.
- `run.inc:110-112`: `sde_strat` in `common/TO_CHANNEL_STRAT/` (with `tmin_for_channel`).
- `cut_decays` is wired via `cuts.inc` / `run.inc` and consumed in `setcuts.f` (see
  bw-cutdecays-interaction.md).

## Wrong-key typo → silent fallback to the registered bwcutoff default (parser mechanics)
A run_card line whose key does NOT match the registered token `bwcutoff` (4305) does NOT set
bwcutoff; the parser then takes the registered default. Two log lines result, then a run at
the registered default:
- `RunCard.read` (banner.py:2898-2910) splits each line on `=`, then **`name = name.lower().strip()`**
  (banner.py:2906) and tests `if name not in self`. **The key match is CASE-INSENSITIVE
  (lowercased), not byte-exact.**
- Unregistered key → `add_unknown_entry` (banner.py:2909→2921) emits
  `logger.warning("Found unexpected entry in run_card: \"%s\" with value \"%s\"...")`
  (banner.py:2961-2967) and registers the stray name as a NEW param (does not touch bwcutoff).
- bwcutoff is now absent from the card → `get_default('bwcutoff')` (banner.py:3251) logs
  `'%s missed argument %s. Takes default: %s%s'` (banner.py:3305) → `Takes default: <default>`
  (the registered default, sourced from run_card_default.dat per banner.py:3294-3300).
- Run proceeds at the registered bwcutoff default → for a sub-threshold forced chain, same
  `Impossible BW configuration` / `Zero result detected: No Phase Space` as explicitly
  setting bwcutoff to that default (bw-cutoff-sizing-derivation.md). Substituting `BW_cut = 0` for the
  bwcutoff line reproduces BOTH log lines + the Zero-result abort.

CORRECTION to the typo enumeration: because of the `.lower()` at banner.py:2906, only keys
that differ from `bwcutoff` AFTER lowercasing are unregistered:
- `bw_cutoff`, `BW_cut`, `bw_cut` → lowercase to `bw_cutoff` / `bw_cut` (≠ `bwcutoff`) →
  **unexpected-entry + fallback-to-default** (the failure mode).
- `bwCutoff`, `BWcutoff` → lowercase to `bwcutoff` → **MATCH the registered key → set correctly,
  NO fallback.** (Only `bwcutoff` is registered; banner.py:4305/5713. No `bw_cut*` token is
  registered anywhere — grep=0.) Case is the only forgiving axis; underscores/different tokens
  are not. (Generic run_card-parser ownership lies outside this slice; the `bwcutoff`-KEY exact
  match + its registered-default fallback are this slice.)

## Caution
- `small_width_treatment` is hidden (default registered at banner.py:4452 — read it there);
  a user lowering a real width below `mass*small_width_treatment` silently gets the floored
  Γ_eff (NWA-corrected σ), not the literal width. This is a source-visible default, not a
  runtime claim.
- Do NOT list `bwCutoff`/`BWcutoff` as fallback-triggering typos — they lowercase to the
  registered key and set bwcutoff correctly (banner.py:2906). Only non-case differences
  (underscore, truncation) are unregistered.
