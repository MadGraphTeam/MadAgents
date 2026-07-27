---
description: Delphes/PGS card + trigger template inventory in v3.7.1; default==CMS (delphes card+trigger) / default==LHC (pgs); what detector an unedited run silently uses; delphes_path config default
---

# Card templates, defaults, and config (v3.7.1)

## Cross-family default-equals-a-named-variant principle
For every detector-card family the MG-shipped *default* file is byte-identical to one named
variant (verified `diff -q`, v3.7.1):
- delphes card:    `delphes_card_default.dat`    == `delphes_card_CMS.dat`
- delphes trigger: `delphes_trigger_default.dat` == `delphes_trigger_CMS.dat`
- pgs card:        `pgs_card_default.dat`         == `pgs_card_LHC.dat`

`do_delphes`/`do_pgs` copy the **default** file (not the named variant) when no operative
card exists (do_delphes 3404, do_pgs 2342). Net effect: **an unedited run silently uses
CMS-style Delphes geometry (+ CMS trigger for delphes2) / LHC-style PGS geometry.** ATLAS is
the genuine differ in all three families — to get it the user must select/copy the variant.

SCOPE: the *mechanism* (copy `_default`, never a named variant) is version-stable and
general. WHICH named variant `_default` equals — the "CMS geometry" / "LHC geometry" label —
is card-CONTENT and version-specific: re-derive it per install with the `diff -q` recipe
below, never lift the label as universal. (Re-confirmed this install: delphes-card &
trigger default==CMS, pgs default==LHC, ATLAS differs everywhere.)

## Delphes cards — `$MADGRAPH_INSTALL/Template/Common/Cards/`
Recipe to re-verify identity/difference: `diff -q` each variant against `_default` in that dir
(don't trust a cached byte size — read the files).
- `delphes_card_default.dat`
- `delphes_card_CMS.dat` — byte-identical to default (see principle above).
- `delphes_card_ATLAS.dat` — differs. ExecutionPath module-list diff vs default is
  small at the listing level: default includes `FatJetFinder`, ATLAS does not (+ leading
  whitespace on `ParticlePropagator`). Per-module parameter differences (resolutions, b-tag,
  isolation) are Delphes internals — OUT OF SLICE.
- No LHC-specific delphes card present in this install (card set drifts across versions;
  re-list per install).

`do_delphes` copies `delphes_card_default.dat` → `delphes_card.dat` when none exists
(common_run_interface.py:3404). To get ATLAS/CMS the user must select/copy the variant
(via the card-edit menu or manually); there is no auto-ATLAS/auto-CMS branch in do_delphes.

NB: no bare `delphes_card.dat` is shipped in any Template (only `_default`/`_CMS`/
`_ATLAS`). The operative card is created LAZILY — by `keep_cards` (scripted/auto path),
by do_delphes copy-if-missing (3404), or by the user via the card-edit menu — NOT at
`output` time. See delphes-availability-and-card-provisioning page for the full chain.

## Trigger cards — `$MADGRAPH_INSTALL/Template/LO/Cards/`
- `delphes_trigger_default.dat`, `delphes_trigger.dat`, `delphes_trigger_CMS.dat` — all
  **byte-identical** (`diff -q` IDENTICAL, v3.7.1). The shipped default trigger card
  IS the CMS trigger card.
- `delphes_trigger_ATLAS.dat` — the only genuine differ (different PT thresholds;
  ATLAS uses isolated-lepton trigger objects IElec/IMuon).
- Format: PGS-style `trigger_name >> OBJ_PT: 'thresh' && …`. Consumed ONLY by the delphes2
  wrapper (run_delphes). delphes3 ignores them.

## PGS cards — `$MADGRAPH_INSTALL/Template/Common/Cards/` (legacy)
- `pgs_card_default.dat` — first line `LHC ! parameter set name`.
- `pgs_card_LHC.dat` — **byte-identical to default** (default PGS card = LHC set; `diff -q`).
- `pgs_card_ATLAS.dat` (`ATLAS`), `pgs_card_CMS.dat` (`CMS`) — differ.
- `pgs_card_TEV.dat` — `CDF ! parameter set name`; Tevatron/CDF geometry (smaller, lower-field
  cal + tracker than the LHC set). The specific cal-cell / B-field / tracker-radius / eta
  numbers are PGS detector parameters — read them fresh from the card if needed; per-module
  values are PGS internals, near/over the slice boundary. `do_pgs` copies `pgs_card_default.dat`
  (=LHC) when none exists (common_run_interface.py:2342).

## `set delphes_card <value>` — preset-only command (do_set)
In the launch/card-edit `set` handler (common_run_interface.py `do_set`, the second one at
5868), `delphes_card` accepts ONLY three preset tokens; it is NOT a structured card and
takes NO arbitrary Delphes parameters:
- `atlas` → copies `delphes_card_ATLAS.dat` → `delphes_card.dat`, returns (6010-6014).
- `cms`   → copies `delphes_card_CMS.dat`   → `delphes_card.dat`, returns (6015-6019).
- `default` → handled by the shared card block (6021-6033): copies `..._default.dat`.
Gate: `if not self.has_delphes` → "Invalid Command: No Delphes card defined." + return (6007).
Tokens are case-sensitive exact lowercase (`args[1]=='atlas'`/`'cms'`, 6010/6015) — `ATLAS`
would miss and fall through.

ANY other value (e.g. a Delphes parameter name, or `lhc`): sets `card='delphes_card'`,
start=1 (6035-6039), then matches NONE of the structured-card param branches (run_card 6080,
param_card 6117, shower 6253, PY8 6305, rivet 6325 all require their own card in the guard;
there is no `self.delphes_card` object with `.keys()`), so it lands in the INVALID else
(6358): `logger.warning('invalid set command %s')` + return — a silent no-op on the card.
Tab-completion confirms the surface: `opts = ['default','atlas','cms']` (5779).

CORRECTED/CONFIRMED nuances vs the seed claim: preset list is EXACTLY {default, atlas, cms}
— there is NO `lhc` delphes preset (LHC is PGS-only) and NO trigger-variant selection through
this command. Per-parameter Delphes edits are impossible via `set`; the user edits the raw
`delphes_card.dat` in the editor instead. NB `default` and `cms` copy byte-identical files
(default==CMS, see top principle), so they yield the same geometry from different tokens.

## delphes_path config
- `$MADGRAPH_INSTALL/input/mg5_configuration.txt:172` ships COMMENTED: `# delphes_path = ./Delphes`.
- In-code default in common_run_interface.py:653 is `'delphes_path':'./Delphes'` (relative to
  MG main dir). If unset, check_delphes re-reads config then raises InvalidCmd (335-350).
