---
description: How the run banner becomes the LHE <header> block — Banner class ordered-tag write (banner.py), banner_header.txt template, the double write (standalone _banner.txt + inline LHE header via unweight->banner.write close_tag=False), init-block/lha-strategy mutation at unweight time.
---

# LHE header / banner assembly (the `<header>` block)

Cites `$MADGRAPH_INSTALL/madgraph/various/banner.py`, `.../lhe_parser.py`, `.../interface/madevent_interface.py`, `Template/LO/Source/banner_header.txt` (v3.7.1). The banner write itself is a launch-owned step of `do_combine_events`; the combine flow that calls it is on combine-store-compile-stages. This page is the "what is in the LHE `<header>`, and how it gets there" reference.

## The Banner object (banner.py:66-89)
`class Banner(dict)` — an ordered dict keyed by lower-case tag, value = the raw text of that card/section. Key structural members:
- `ordered_items` (70-72): write order = `mgversion, mg5proccard, mgproccard, mgruncard, slha, initrwgt, mggenerationinfo, mgpythiacard, mgpgscard, mgdelphescard, mgdelphestrigger, mgshowercard, foanalyse, ma5card_parton, ma5card_hadron, run_settings`.
- `capitalized_items` (74-88): lower key -> LHE tag name. `mgversion`->`MGVersion`, `mg5proccard`->`MG5ProcCard`, `mgruncard`->`MGRunCard`, `slha`->`slha` (param_card content), `mggenerationinfo`->`MGGenerationInfo`, etc.
- `forbid_cdata = ['initrwgt']` (89): every other tag whose text contains `<` or `@` gets CDATA-wrapped; `initrwgt` never is.
- `tag_to_file` (~275): tag -> Cards filename, used by `split()` (banner->Cards) not by write. `slha`->`param_card.dat`, `mgruncard`->`run_card.dat`, `mg5proccard`->`proc_card_mg5.dat`, etc.
- On init (100-109): `mgversion` is set from `Source/MGMEVersion.txt` (MADEVENT side) or `misc.get_pkg_info()` — this is the MG5 version stamp.

So "run_card, param_card, model info, MG5 version" map to concrete tags: run_card=`MGRunCard`, param_card=`slha`, model info=carried inside the proc_card tags (`MG5ProcCard`/`MGProcCard` = `proc_card_mg5.dat`, which contains the `import model` line — there is NO dedicated "model" tag), MG5 version=`mgversion`/`MGVersion`. Doc claim (claim 2) is CORRECT in substance.

## What populates the banner before write (do_combine_events, madevent_interface.py:3784-3797)
- `self.banner = banner_mod.recover_banner(self.results, 'parton')` if not already set (3785-3786).
- `self.banner.load_basic(self.me_dir)` (3787) -> `load_basic` (banner.py:251-260) `add`s `Cards/param_card.dat` + `Cards/run_card.dat` + (`SubProcesses/procdef_mg5.dat`+`proc_card_mg5.dat`) or `proc_card.dat`. This is where param/run/proc content enters the banner dict.
- `self.banner.add_generation_info(cross, nevents)` (3788) -> sets `MGGenerationInfo` (banner.py:269-276) to a two-line block: `#  Number of Events : <nb>` / `#  Integrated weight (pb) : <cross>`. NOTE: the arg is `run_card['nevents']` (the REQUEST), not the actual generated count.
- `self.banner.change_seed(self.random_orig)` (3790) -> regex-rewrites the `= iseed` line inside the stored `mgruncard` text (banner.py:263-267) so the banner records the actual seed offset used.

## The write method (banner.py:387-455)
`write(output_path, close_tag=True, exclude=[])`:
1. Reads header template `Source/banner_header.txt` (MADEVENT) or `Template/LO/Source/banner_header.txt` (395-398) and emits it with `%(version).1f` filled from `run_card['lhe_version']` (forced to 1.0 if <3, 404-407). The template IS `<LesHouchesEvents version="X.0">` + `<header>` + a comment block that literally reads *"This file contains all the information necessary to reproduce the events generated"* then lists software version / proc_card / param_card / run_card / pythia / pgs / delphes. The **"reproduce the events" reproducibility language is a verbatim source string in `banner_header.txt`**, not paraphrase.
2. For each tag in `ordered_items` present, then any extra keys (411-427): emit `<CapitalizedTag>\n<text>\n</CapitalizedTag>\n`. If the text contains `<` or `@` and the tag is not in `forbid_cdata`, wrap the body in `<![CDATA[ ... ]]>` (418-422). `init` tag is skipped in this loop.
3. Unless `/header` in exclude: emit `</header>\n` (429-430).
4. If `init` key present and not excluded: emit `<init>\n<text>\n</init>\n` (433-441) — the LHE `<init>` block (beam/process xsec lines).
5. If `close_tag`: emit `</LesHouchesEvents>\n` (443-450).

## The DOUBLE write — two destinations for the same banner
The banner is written twice per run:

**(a) Standalone banner file** — `do_combine_events` (madevent_interface.py:3796): `self.banner.write(Events/<run>/<run>_<tag>_banner.txt)` with default `close_tag=True`. This is a self-contained banner (no events), the `banner_<run>_banner.txt`-style artefact. Written at COMBINE time (see combine-store-compile-stages caution: no banner if the run dies before combine).

**(b) Inline LHE header** — `lhe_parser.py` `MultiEventFile.unweight` (441-559). `do_combine_events` sets `AllEvent.banner = self.banner` (3806) then calls `AllEvent.unweight(unweighted_events.lhe, ...)`. Inside unweight:
- The banner is mutated for the final file (508-526): `modify_init_cross(cross, allow_zero=True)` updates the `<init>` block cross-section to the unweighted value; `banner["unweight"] = "unweighted by <name>"` adds an `unweight` tag; `set_lha_strategy(±3)` if normalization is unit/sum else `±4` (sign preserves the existing sign) — the LHA weighting-strategy code in `<init>`.
- `banner.write(outfile, close_tag=False)` (559): emits the FULL header block (`<LesHouchesEvents>` ... `</header>` ... `<init>`) as the head of `unweighted_events.lhe`, deliberately WITHOUT the closing `</LesHouchesEvents>` because events follow.
- After the event loop, `outfile.write("</LesHouchesEvents>\n")` (lhe_parser.py:590/597/606) closes the file.

So the `<header>` block of `unweighted_events.lhe` and the standalone `_banner.txt` are the SAME banner object rendered twice; the LHE copy additionally carries the unweight-time init/strategy/unweight mutations.

## Cautions
- **`MGGenerationInfo` "Number of Events" is `run_card['nevents']` (the request), not the produced count** — it is set before unweighting knows the actual yield (madevent_interface.py:3788). The actual count lives in `results` / shell output, not this banner line.
- **No dedicated "model" tag.** Model identity is inside the proc_card tags (`MG5ProcCard` = `proc_card_mg5.dat` `import model ...`). A reader looking for a `<model>` block will not find one.
- **The LHE `<init>` cross-section is the unweight-time value** (`modify_init_cross`), which can differ from the `MGGenerationInfo` integrated weight and from the raw survey/refine banner if few events survived (`allow_zero=True` guards the missing-input case).
- **lha_strategy in the final LHE is ±3 (unit/sum norm) or ±4 (average norm)** and is set at unweight time, not from the run_card directly (lhe_parser.py:519-526).
- CDATA wrapping is content-triggered (`<` or `@` in the tag text), not tag-fixed, except `initrwgt` which is never wrapped — relevant if parsing the header back.
