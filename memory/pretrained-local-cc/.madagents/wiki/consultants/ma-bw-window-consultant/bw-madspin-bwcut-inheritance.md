---
description: MadSpin BW_cut sentinel (-1) inherits run_card bwcutoff (default registered at banner.py:4305) at banner-charge time; MadSpin's own ±n·Γ mass-sampling window in decay.py is a DISTINCT mechanism from the myamp.f cut_bw on-shell test.
---

# MadSpin BW_cut ↔ run_card bwcutoff

MG5_aMC v3.7.1. Slice boundary: the `BW_cut` sentinel and its resolution to `bwcutoff`
are MY slice (bw-window). The `MadSpinOptions` add_param / `do_set` string-parsing grammar
is ma-madspin-interface-consultant.

## Source-walked facts
- `MadSpin/interface_madspin.py:64`: `self.add_param('BW_cut', -1)` — default value is the
  sentinel **-1**, NOT a window size.
- Sentinel resolution has TWO branches, gated on whether the input LHE banner carries a run_card:
  - `interface_madspin.py:243` `if 'mgruncard' in self.banner:` → `:251-252`
    `if self.options['BW_cut'] == -1: self.options['BW_cut'] = float(self.banner.get_detail('run_card','bwcutoff'))`
    — **inherits the run_card bwcutoff value verbatim.**
  - `:261 else:` (no run_card in banner) → `:265-266`
    `if self.options['BW_cut'] == -1: self.options['BW_cut'] = <fallback>` — **hardcoded
    fallback; read the literal at interface_madspin.py:265-266.**
- run_card `bwcutoff` default: `banner.py:4305` (RunCardLO) and `banner.py:5713`
  (RunCardNLO), both `add_param("bwcutoff", <default>)` — read the default there. So the
  inherited value is the run_card default unless the user changed bwcutoff in the run_card.
  (The no-banner hardcoded fallback is set to match that default; if the two ever diverge in
  source, read each at its own coordinate.)
- Guard rails on the resolved value:
  - `:253-254`: if inherited bwcutoff `> 25` → `logger.critical(... "much too large value for
    Madspin and the validity of the Narrow-width-Approximation ... overwrite ... set BW_cut X
    ... like X=10")`. So the *inherited default* does NOT trip this (default < 25); only a
    user-raised bwcutoff>25 does.
  - `interface_madspin.py:653-654`: `if self.options['BW_cut'] > 100: raise Exception("BW_cut
    parameter is much too large (>100) for narrow width approximation...")`.

## MadSpin's window is a SEPARATE mechanism from myamp.f cut_bw
- MadSpin applies BW_cut in its OWN mass-sampling in `MadSpin/decay.py:534-535`:
  `m_min = max(mpole - BW_cut*w, 0.5)` ; `m_max = mpole + BW_cut*w` (with
  `m_max = min(m_max, 0.99*E_collider)` if E_collider>0 at :536). This is a **symmetric
  ±(BW_cut·Γ) half-width in the daughter INVARIANT MASS**, floored at 0.5 GeV, feeding an
  atan-mapped BW sampling (`:538-539` zmin/zmax). Here `w = pid2width(pid)` is the **raw
  particle width** (decay.py:531) — NO small_width_treatment / Γ_eff floor is applied
  (contrast myamp.f Γ_eff = max(prwidth, prmass·small_width_treatment)).
- `decay.py:521`: `if d>0 or not BW_cut:` — if BW_cut is falsy (0), the daughter mass is set
  to the pole mass (no BW smearing = effectively on-shell/NWA sampling).
- The myamp.f `cut_bw` on-shell test (bwcutoff×Γ_eff window + Γ/M narrow gate + gForceBW/lbw)
  runs at LO madevent integration/unweighting time; MadSpin's decay.py window runs
  post-generation on already-produced LHE events during the decay-attachment resampling. Two
  DISTINCT windows that merely SHARE the same numeric value (the inherited bwcutoff default)
  by the sentinel inheritance above.

## Claim reconciliation
1. BW_cut is MadSpin's on-shell-window param and the run_card equivalent is bwcutoff — CORRECT as a
   value correspondence (sentinel inheritance), but they are two distinct enforcement
   mechanisms, not one shared window. Treating them as "the same on-shell test" is WRONG.
2. "BW_cut=-1 inherits run_card bwcutoff." — CORRECT, but ONLY when the banner carries a
   run_card (`mgruncard`); with no run_card banner it hardcodes the fallback at :265-266. Both
   paths land on the same value for the default run_card.
3. "default BW_cut inherits the run_card bwcutoff default." — CORRECT numerically (BW_cut
   sentinel resolves to the bwcutoff default). A `set BW_cut <default>` equals the inherited
   default (harmless no-op). Note MadSpin's own guidance (:254) recommends a SMALLER value
   (~10) for NWA validity; the inherited bwcutoff default is already at the loose end.

## Cross-slice pointers
- `MadSpinOptions` field registration, the `do_set BW_cut X` command grammar, spinmode
  (full/madspin/none/onshell) selection → ma-madspin-interface-consultant.
- decay.py BW sampling internals / polarization-preservation algorithm → MadSpin internals
  (ma-madspin-interface-consultant redirects).
