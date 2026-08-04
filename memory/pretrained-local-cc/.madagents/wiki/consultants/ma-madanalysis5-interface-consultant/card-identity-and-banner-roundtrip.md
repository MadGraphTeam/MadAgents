---
description: How MG identifies an MA5 card by content (detect_card_type) and persists/restores the operative MA5 card via the run banner — incl. the skip_analysis->'unknown' trap and the missing charge_card path.
---

# MA5 card identity (content-recognition) + banner roundtrip (v3.7.1)

Two interface-boundary facts about how MG handles the MA5 card AS A FILE — recognizing its type from content, and persisting it into / restoring it from the run banner. Complements ma5-card-structure (the in-memory class) and config-and-install (the Cards/ lifecycle).

## detect_card_type — content-based MA5 recognition (common_run_interface.py:1238-1248)
`@staticmethod detect_card_type(path)` recognizes a card by scanning its content (regex list 1197-1227). MA5 branch:
- ANY line matching `@MG5aMC` (case-insensitive) routes into the MA5 sub-classifier (1238).
- `ma5_flag = [f[7:].strip() for f in matched-@mg5amc-lines]` — strips the `@MG5aMC` prefix.
- If any flag starts with `reconstruction_name` -> `madanalysis5_hadron_card.dat` (1240-1241).
- Else keep only flags containing `*.` and take the extension (`f.split('*.')[1]`): `lhe` -> parton (1243), `hepmc|hep|stdhep|lhco` -> hadron (1245-1246).
- Else -> `'unknown'` (1248).

### TRAP (PROBE-CONFIRMED): the shipped skip_analysis default detects as 'unknown'
The shipped default card is only `@MG5aMC skip_analysis` (no `inputs=`, no `reconstruction_name`). It matches `@MG5aMC`, so it enters the MA5 branch, but `ma5_flag=['skip_analysis']`: not reconstruction_name, and after the `*.`-filter the list is empty -> falls to `else: return 'unknown'`.
Probe (parse-time, `CommonRunCmd.detect_card_type(path)`):
- `@MG5aMC skip_analysis` only -> `'unknown'`
- `@MG5aMC inputs = *.lhe` (+ analysis) -> `madanalysis5_parton_card.dat`
- `@MG5aMC inputs = *.hepmc` + `@MG5aMC reconstruction_name = ...` -> `madanalysis5_hadron_card.dat`
So a no-op MA5 card is NOT identified as an MA5 card by content alone — only a card that names inputs or a reconstruction is. Filename-based handling (e.g. the keep_cards / banner.add paths, which key off the literal `madanalysis5_*_card.dat` name) does not have this hole; only content-detection does.

## Banner roundtrip — write/restore works, re-charge does NOT
MA5 cards are first-class banner tags (banner.py):
- `Banner.ordered_items` includes `'ma5card_parton','ma5card_hadron'` (:72); `capitalized_items` maps them to `MA5Card_parton`/`MA5Card_hadron` (:79-80); `tag_to_file` maps `ma5card_parton`->`madanalysis5_parton_card.dat`, `ma5card_hadron`->`madanalysis5_hadron_card.dat` (:136-137).

### Write side (into the banner)
- `run_madanalysis5` after all runtags: `self.banner.add(Cards/madanalysis5_<mode>_card.dat)` then `self.banner.write(<run>_<tag>_banner.txt)` (common_run_interface.py:3352-3356).
- `Banner.add` (banner.py:457) dispatches by filename -> `'madanalysis5_parton_card' in card_name` => tag `MA5Card_parton` (:490-491), hadron => `MA5Card_hadron` (:492-493) -> `add_text(tag.lower(), open(path).read())` (:497). So the operative card's RAW TEXT is stored under dict key `ma5card_parton`/`ma5card_hadron`.

### Restore side (banner -> disk)
- `Banner.split(me_dir)` (banner.py:281-295) iterates all tags; any tag with a non-empty `tag_to_file` entry is written to `Cards/<tag_to_file[tag]>`. So recovering a run from its banner REWRITES the operative MA5 cards back to `Cards/madanalysis5_{parton,hadron}_card.dat`. Full text roundtrip.

### The asymmetry: no charge_card path for MA5
`Banner.charge_card(tag)` (banner.py:516-565) rebuilds a python card OBJECT from banner text, but it only handles `slha / mgruncard / mg5proccard / mgshowercard / foanalyse` — guarded by `assert tag in [...]` (:530). MA5 tags are NOT in that list, so `charge_card('ma5card_parton')` (or any MA5 alias) would hit the assert. CONSEQUENCE: the MA5 card survives the banner as raw text (and round-trips to disk via split), but cannot be re-instantiated into a `MadAnalysis5Card` directly from the banner — to get an object you must read the on-disk card MA5Card(path) as run_madanalysis5 does (3156). This is unlike run_card/param_card which both persist AND re-charge.

## Caution
Content-detection ('unknown' for a skip_analysis card) is a real edge for any tooling that classifies a Cards/ file by content rather than name. The operative interface paths (keep_cards, banner.add, run_madanalysis5) all key off the literal filename, so they are unaffected — but a generic "what card is this?" content probe on the shipped default will not say "MA5".
