---
description: upstream of do_delphes — check_available_module gates Delphes on a shower; set_default_detector + auto-resolver pick detector; keep_cards creates operative delphes_card.dat from _default
---

# Delphes availability, detector selection, and operative-card creation

Covers the layer ABOVE `do_delphes` (see do_delphes-flow page) that decides
*whether* Delphes runs and *creates* the operative card. Lives mostly in
`$MADGRAPH_INSTALL/madgraph/interface/madevent_interface.py`, with the actual
card-copy in `common_run_interface.py`.

## 1. Availability gate — `check_available_module` (madevent_interface.py:516-540)
Builds `self.available_module` from configured paths:
- `delphes_path` set → adds `'Delphes'` ONLY if `PY6` or `PY8` is also available
  (530-532). Otherwise logs `warning("Delphes program installed but no parton shower
  module detected.\n    Please install pythia8")` (534) and does NOT add Delphes.
- `PY6`/`PGS` from `pythia-pgs_path` (519-521); `PY8` from `pythia8_path` (522-523).
- INFERRED consequence: Delphes with no shower installed is silently unavailable —
  the detector switch can't select it. (Source-confirmed gate; warning text quoted.)

## 2. Interactive detector default — `set_default_detector` (madevent_interface.py:660-673)
Sets `self.switch['detector']` for the interactive launch menu:
- PGS if `'PGS' in available_module` AND shower=='Pythia6' AND `Cards/pgs_card.dat`
  exists (664-666).
- elif Delphes if `'Delphes' in available_module` AND shower!='OFF' AND
  `Cards/delphes_card.dat` exists (667-669).
- elif `get_allowed_detector()` → 'OFF' (670-671), else 'Not Avail.' (672-673).
- **KEY:** the Delphes default branch requires `Cards/delphes_card.dat` to ALREADY
  exist. No bare operative card is shipped (see card-templates page; Template ships only
  `_default`/`_CMS`/`_ATLAS`). So on a fresh proc dir the interactive detector default is
  NOT Delphes — it falls through to OFF until a delphes_card.dat is present.

## 3. Scripted/auto detector resolver (madevent_interface.py:6843-6864)
For `--laststep=` / `generate_events` mode resolution:
- `mode=='auto'` → pgs if `pythia_version==6` AND `pgs_card.dat` exists (6846-6848);
  elif `delphes_card.dat` exists → 'delphes' (6849-6850); else `pythia<suffix>` (6851-2).
- Once mode=='delphes' it appends `'delphes_card.dat'` to `cards` (6860) and, for
  delphes2 (delphes_path has a `data/` dir, 6862), also `'delphes_trigger.dat'` (6864),
  then calls `keep_cards(cards, ...)` (6865).

## 4. Operative-card CREATION — `keep_cards` (common_run_interface.py:3997-4020)
The mechanism that actually materializes `Cards/delphes_card.dat`:
- For each card in the master `check_card` list (4000-4005, includes delphes_card.dat +
  delphes_trigger.dat): if it's NOT needed → hide it to `.<card>` (4012-4013); if it IS
  needed and absent → restore from `.<card>` if hidden (4016-4017), else
  `files.cp(<card>_default.dat → <card>.dat)` (4019-4020).
- **So `keep_cards` is where `delphes_card_default.dat` (== CMS, see card-templates
  page) becomes the operative `delphes_card.dat`.** This is the upstream twin of
  `do_delphes`'s own copy-if-missing (common_run_interface.py:3404): both copy the
  *default* template, so the "unedited run silently uses CMS geometry" effect can be
  triggered from either path.

## Caution
- No `delphes_card.dat` is shipped in any Template (find Template -name delphes_card.dat
  → empty). The operative card is created LAZILY — by keep_cards (scripted/auto path),
  by do_delphes copy-if-missing (line 3404), or by the user via the card-edit menu.
  Corrects the loose "copied at output" phrasing: it is created at run/keep-cards time,
  not at `output` time.
- Detector switch defaulting to Delphes is gated on the card pre-existing
  (set_default_detector 668) — a chicken/egg that makes OFF the fresh-proc default.
