---
description: PRINCIPLE — MG resolves a detector card's identity (delphes_card/delphes_trigger/pgs_card) by substring match at two distinct routers keyed on DIFFERENT things — detect_card_type on CONTENT, Banner.add on FILENAME — neither uses exact filename or declared type, so a rename or token-strip mis-routes at one or the other.
---

# Card identity is resolved by substring — at two routers, on two different keys

## Principle
MadGraph never tracks a card by an exact filename or a declared type. It re-derives a card's
identity by **substring matching** every time it needs to know what a card IS, and it does this
at TWO distinct lifecycle points that key on DIFFERENT things:

- **`detect_card_type`** (common_run_interface.py:1230) — keys on file **CONTENT**. Builds a
  regex over a tag list and `re.findall`s it against `fulltext` (the file body), then classifies
  by which tokens appeared. Used when a user uploads/edits a card and MG must decide what it is.
- **`Banner.add`** (banner.py:457, inference at 460-485) — keys on **FILENAME**. Infers the
  banner tag from `os.path.basename(path)` by substring. Used when a card is written into the run
  banner.

Both are substring strategies, neither uses an exact match or a stored type. So a card's identity
can be broken at EITHER router independently:
- strip the identifying **content tokens** → `detect_card_type` mis/under-classifies it;
- strip the identifying **filename token** → `Banner.add` mis-tags or drops it.
This is why "rename my delphes card" and "edit a card's header" are two different risks, not one.

## The two routers, source-confirmed (v3.7.1)
### CONTENT router — detect_card_type (classification 1232-1258)
My slice's cards route by these CONTENT tokens (case-insensitive, matched in file body):
- `delphes_card.dat` ← `executionpath` OR `treewriter` OR `cen_max_tracker` (1234-1237).
  `particlepropagator` is INTENDED but DEAD (missing-comma concatenation bug — see
  card-type-recognition page; probe-confirmed dead there).
- `delphes_trigger.dat` ← `#trigger card` (1249-1250).
- `pgs_card.dat` ← `parameter set name` OR `muon eta coverage` (1251-1254).
A file whose body lacks ALL of a card-type's live tokens is NOT recognized as that card.

### FILENAME router — Banner.add (inference 470-475)
Tag inferred from basename substring, checked in order:
- `'pgs_card' in name` → MGPGSCard (470-471)
- `'delphes_card' in name` → MGDelphesCard (472-473)
- `'delphes_trigger' in name` → MGDelphesTrigger (474-475)
The three substrings are mutually exclusive (`delphes_trigger.dat` does NOT contain the substring
`delphes_card`), so the check order is benign — no card collides with an earlier branch.
Probe: `infer('delphes_card_ATLAS.dat')→MGDelphesCard`,
`infer('delphes_trigger_ATLAS.dat')→MGDelphesTrigger` (the `_ATLAS`/`_CMS` variants keep the
token, so they tag correctly), but `infer('my_detector.dat')→None`, `infer('CMS.dat')→None`
(token stripped → falls through, mis-tagged/dropped in the real add()).

## What this catches beyond the two instance pages
1. A delphes card **renamed** to drop `delphes_card`/`delphes_trigger` from its basename: tags
   fine on upload IF its content tokens survive (detect_card_type is content-keyed) but is
   MIS-TAGGED when written to the banner (Banner.add is filename-keyed). The two routers disagree
   on the same file — a class of bug neither page alone predicts.
2. A card whose **content header** was edited away (e.g. trigger card stripped of its
   `#TRIGGER CARD` first line): unrecognized by detect_card_type on re-upload even though its
   filename is canonical. (This is exactly why the trigger template's line 1 is
   `#TRIGGER CARD  # DO NOT REMOVE THIS IS A TAG!`.)
3. Any **future card family** added to MG that follows the same substring approach inherits both
   fragilities — the principle predicts the failure mode without re-deriving per card.

## Boundary
- This is card IDENTITY resolution. It is NOT the operative-card EXISTENCE gate (whether Delphes
  RUNS) — that is the `operative-card-existence-is-the-detector-switch` principle. A card can be
  correctly identified yet never trigger a run, and vice versa.
- Delphes-internal parsing of the card's module/parameter content is OUT OF SLICE (Delphes
  internals). This principle stops at "which MG slot does this file map to".

## Instance pages (kept)
- `card-type-recognition` — the CONTENT router in full (tag list, the dead-tag missing-comma bug,
  banner-vs-delphes_card disambiguation).
- `delphes-card-banner-lifecycle` §2 — the FILENAME router in full (Banner.add, the registry
  tables, write order, recover_banner stripping).
