---
description: How delphes_card.dat / delphes_trigger.dat live in the run banner — Banner registry tags, substring add() routing (twin of detect_card_type), recover_banner level-stripping of prior detector cards, do_delphes appending the operative card to the pythia-level banner
---

# Delphes/PGS card lifecycle through the run banner

Complements `card-type-recognition` (the UPLOAD-side `detect_card_type`) and `do_delphes-flow`
step 6 (the banner write). This page is the BANNER-side lifecycle of my detector cards:
how they are tagged, ordered, stored, stripped, and recovered. All in
`$MADGRAPH_INSTALL/madgraph/various/banner.py` (class `Banner(dict)`, def line 66) unless noted.

## 1. The card↔tag registry (3 parallel tables, all source-confirmed v3.7.1)
The `Banner` dict keys its sections by lowercase tag; my cards appear in every table (exact
lines, v3.7.1):
- `ordered_items` (banner.py:69-73, detector entries at 71): `...,'mgpgscard','mgdelphescard',
  'mgdelphestrigger','mgshowercard',...` — detector cards sit AFTER pgs, BEFORE shower card.
  This list fixes the WRITE ORDER (see §4).
- `capitalized_items` (def 82; detector entries 83-85): `'mgpgscard':'MGPGSCard'`,
  `'mgdelphescard':'MGDelphesCard'`, `'mgdelphestrigger':'MGDelphesTrigger'`. These are the
  XML tag names emitted into the banner.
- `tag_to_file` (def 120; detector entries 122-124): `'mgpgscard':'pgs_card.dat'`,
  `'mgdelphescard':'delphes_card.dat'`, `'mgdelphestrigger':'delphes_trigger.dat'` — used when
  a banner is split back out to disk.

## 2. `Banner.add()` routing — substring-based, the banner twin of detect_card_type (472-475)
`add(self, path, tag=None)` (def line 457) with no explicit tag infers the tag from
`os.path.basename(path)` by substring:
```
elif 'delphes_card' in card_name:   tag = 'MGDelphesCard'   # 472-473
elif 'delphes_trigger' in card_name: tag = 'MGDelphesTrigger' # 474-475
elif 'pgs_card' in card_name:        tag = 'MGPGSCard'        # 470-471
```
Same substring philosophy as `detect_card_type` (filename, not content here), so a renamed
delphes card passed to `add()` without keeping `delphes_card`/`delphes_trigger` in its name is
mis-tagged. `do_delphes` calls `self.banner.add(.../delphes_card.dat)` (common_run_interface.py
~3422) WITHOUT an explicit tag, so it relies on this inference — but it always passes the
canonical filename, so the inference is correct in the normal flow.

## 3. `recover_banner` STRIPS prior detector cards at pythia/pgs/delphes level (706-768)
`recover_banner(results_object, level, run, tag)` (706) reads the existing
`<run>_<tag>_banner.txt`, then for cleanup (764-767):
```
if level in ['pythia','pgs','delphes']:
    for tag in ['mgpgscard','mgdelphescard','mgdelphestrigger']:
        if tag in banner: del banner[tag]
```
So whenever a banner is recovered for the pythia/pgs/delphes level, ALL prior detector cards
(pgs + delphes + trigger) are deleted from the in-memory banner. (`'pythia'` level additionally
deletes `mgpythiacard`, 761-763.)
- **do_pythia8** rebuilds `self.banner = recover_banner(self.results, 'pythia')`
  (madevent_interface.py:4617) when its banner is empty — so a delphes card from a PREVIOUS
  tag's run is wiped before the new shower's banner is written (5260). The Pythia6 `do_pythia`
  does the same (madevent_interface.py:5355). This is why a fresh shower's banner never carries a
  stale detector card — it is re-added only when do_delphes runs for THIS tag.

## 4. `do_delphes` appends the operative card to the pythia-level banner (do_delphes-flow §6)
After the shower tail-calls `delphes --no_default`, `do_delphes` (common_run_interface.py:3367)
does, only if `Source/banner_header.txt` exists:
- `self.banner.add(Cards/delphes_card.dat)` — appends MGDelphesCard to the banner the shower
  just built (which already holds run_card/param_card/proc_card/pythia_card).
- for delphes2 only: also `self.banner.add(Cards/delphes_trigger.dat)` (MGDelphesTrigger).
- `self.banner.write(<run>_<tag>_banner.txt)` — rewrites that banner file with the detector card
  now included.
`Banner.write` (387) emits sections in `ordered_items` order then any extras, so the delphes
card lands after the pgs slot / before the shower-card slot in the written banner.

## 5. Where the banner is CONSUMED back as the LHCO header (run_delphes3, commented out)
The delphes banner that §4 writes is the intended header of the LHCO output — but the block that
prepends it is COMMENTED OUT in `Template/LO/bin/internal/run_delphes3` (tail of script):
`sed -e "s/^/#/g" ${run}/${run}_${tag}_banner.txt > ...lhco` then appends the cross-section
comment and the lhco body. Since root2lhco is off by default (see run-delphes-scripts), this
banner-to-LHCO path does not fire on a default delphes3 run; the `<run>_<tag>_banner.txt` is
still written by do_delphes regardless.

## Cautions
- The stripping in §3 means you CANNOT recover a prior run's delphes card from a freshly
  recovered pythia-level banner — it was deleted in-memory. To read back a stored delphes card,
  parse the on-disk `<run>_<tag>_banner.txt` directly (the file still contains the
  `<MGDelphesCard>` block from when do_delphes wrote it; the deletion is only in the recovered
  in-memory object for the NEW run).
- `Banner.add()` tag inference is filename-substring, not content — a card that lost its
  `delphes_card`/`delphes_trigger` basename token before being added is mis-tagged (mirrors the
  detect_card_type renamed-card caveat). do_delphes itself always passes canonical names.
- `split_banner` (700) / the `tag_to_file` table (§1) are the inverse path (banner → on-disk
  card files); `mgdelphescard`→`delphes_card.dat`, `mgdelphestrigger`→`delphes_trigger.dat`.
