---
description: OUTPUT-time MA5 default-card creation at code-export — create_MA5_cards / create_default_madanalysis5_cards (export_v4.py + export_fks.py), the LO parton+hadron vs NLO hadron-only split, and the copy-to-operative step that "turns MA5 on by default".
---

# Output-time MA5 card creation (v3.7.1)

The earlier pages all start at RUN time (run_madanalysis5 and the switch layer). This page maps the EARLIER half of the interface lifecycle: where the operative `Cards/madanalysis5_{parton,hadron}_card.dat` files come from in the first place — they are generated during `output <dir>` (code export), not at launch. This is why a fresh process directory already has MA5 cards before the user ever runs anything.

## Entry: create_MA5_cards, called from process-dir finalisation
- `ProcessExporterFortran.create_MA5_cards(self, matrix_elements, history)` — `$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py:560`.
- Invoked right after `create_run_card` during output finalisation: `self.create_MA5_cards(matrix_elements, history)` (export_v4.py:558).
- It is a thin wrapper "so that it can be bypassed by daughter classes (i.e. in standalone)" (docstring :561-562).
- **StandAlone bypass**: `ProcessExporterFortranSA.create_MA5_cards(self,*args,**opts): pass` (export_v4.py:2853-2855 — `def` at :2853, `pass` at :2855; "Overload the function of the mother so as to bypass this in StandAlone"). => StandAlone output (`output standalone ...`) gets NO MA5 cards at all.

## The output-time gate (export_v4.py:563-565)
```
if 'madanalysis5_path' in self.opt and not \
        self.opt['madanalysis5_path'] is None and not self.proc_defs is None:
```
Three conjuncts — ALL must hold or no MA5 cards are written:
1. `'madanalysis5_path' in self.opt`
2. `self.opt['madanalysis5_path'] is not None`
3. `self.proc_defs is not None`
- THE `opt` DICT: `ExportV4Factory` builds `opt = dict(cmd.options)` (export_v4.py:9869), so `opt['madanalysis5_path']` is simply `cmd.options['madanalysis5_path']`. (A SEPARATE line `opt['madanalysis5'] = cmd.options['madanalysis5_path']` for `format in ['madevent']` at export_v4.py:10007-10008 sets a DIFFERENT key `'madanalysis5'` with no `_path` — that key is NOT what the :563 gate reads; the gate is satisfied via the `dict(cmd.options)` copy, making :10008 effectively a redundant/legacy key for this gate.)
- THIS INSTALL (PROBE-CONFIRMED): `cmd.options['madanalysis5_path']` resolves to python `None`, NOT the literal string. The config-load validation (madgraph_interface.py:7441-7448) sets `self.options['madanalysis5_path']=None` when `<path>/bin/ma5` is absent (also nulls + warns when `is_MA5_compatible_with_this_MG5` returns a reason). `mg5_configuration.txt:180`'s `$MADGRAPH_INSTALL/None` value has no `bin/ma5`, so it is nulled. Probe: `MasterCmd().options['madanalysis5_path']` -> `None`. So conjunct 2 (`is not None`) is FALSE here -> the OUTPUT-time gate is CLOSED in this install; NO MA5 cards are generated/copied at output time. (Corrects the earlier hypothesis that the value stays a truthy string.)
- Caution: the OUTPUT-time gate and the RUN-time path-truthy gate (three-gate page Gate 1) are DIFFERENT checks at different stages, but BOTH read the SAME nulled `cmd.options['madanalysis5_path']` in this install — both closed for the same root cause (no installed MA5).
- conjunct 3 (`proc_defs is not None`): a directory built by some non-standard path that left `proc_defs` unset would silently skip MA5-card creation.

## LO vs NLO levels split — INDEPENDENT corroboration of "hadron-only at NLO"
- **LO** (`export_v4.py:573-576`): `create_default_madanalysis5_cards(..., levels=['hadron','parton'])` — BOTH levels.
- **NLO/FKS** (`export_fks.py:1047-1067`): the SAME inline gate (:1047-1048), then `create_default_madanalysis5_cards(..., levels=['hadron'])` (call :1064-1067, `levels =['hadron']` at :1067) — HADRON ONLY.
  - FKS does NOT route through the `create_MA5_cards` wrapper; it inlines the gate + call directly in its source-writing finalisation (export_fks.py:1046-1067).
  - Process list at NLO: `processes = sum([me.get('processes') ... for me in matrix_elements.get('matrix_elements')],[])`; falls back to `self.born_processes`; if still empty, a WARNING ("MG5aMC could not provide to Madanalysis5 the list of processes generated ... low_mem_multicore_nlo_generation") and the card won't be process-tailored (export_fks.py:1052-1061).
- This is a SECOND, independent confirmation (from the exporter, not the run-interface switch) of the nlo-amcatnlo-ma5-interface page's "no parton MA5 at NLO" finding: NLO never even WRITES a parton card.

## create_default_madanalysis5_cards — the generator (export_v4.py:444)
`create_default_madanalysis5_cards(self, history, proc_defs, processes, ma5_path, output_dir, levels=['parton','hadron'])`:
- `if len(levels)==0: return` (:448-449).
- Logs INFO "Generating MadAnalysis5 default cards tailored to this process" (:451).
- Constructs an MA5 interpreter via `common_run_interface.CommonRunCmd.get_MadAnalysis5_interpreter(MG5DIR, ma5_path, loglevel=100)` (export_v4.py:454-455) — the SAME interpreter-construction helper used at run time (common_run_interface.py:2651), but called HERE at output time with NO `mg5_interface` arg and `loglevel=100`. This is the SECOND caller of get_MadAnalysis5_interpreter (the only other is run_madanalysis5:3203).
- On interpreter failure: `except (Exception, SystemExit)` -> WARNING "Fail to create a MadAnalysis5 instance. Therefore the default analysis with MadAnalysis5 will be empty" + return (:456-458); `if MA5_interpreter is None: return` (:459-460). => if MA5 can't start, NO `_default.dat` is written by this function, so the only card present is the shipped skip-only fallback template.
- Per requested level: `text = MA5_main.madgraph.generate_card(history, proc_defs, processes, lvl)` (export_v4.py:467) — the actual card TEXT generation is MA5-INTERNAL (`MA5_interpreter.main.madgraph.generate_card`), OUT OF SLICE. On its failure: WARNING "MadAnalysis5 failed to write a %s-level default analysis card ... will be empty" + keep the skip-only default (:468-478, comment "keep the default card (skip only)").
- Success: `open(card_to_generate,'w').write(text)` where `card_to_generate = pjoin(output_dir,'madanalysis5_%s_card_default.dat'%lvl)` (:464, :480). So the OUTPUT is the `_default.dat` file (the same name as the shipped fallback template), now tailored.

## The "turn MA5 on by default" copy step (export_v4.py:577-582) — load-bearing
After generation, for each level the wrapper copies the `_default.dat` to the OPERATIVE card name:
```
for level in ['hadron','parton']:
    # Copying these cards turn on the use of MadAnalysis5 by default.
    if os.path.isfile(.../madanalysis5_%s_card_default.dat):
        shutil.copy(.../madanalysis5_%s_card_default.dat,
                    .../madanalysis5_%s_card.dat)
```
- This is WHERE the operative `Cards/madanalysis5_{parton,hadron}_card.dat` come from: a copy of the generated `_default.dat`.
- The code comment is explicit: **copying these turns MA5 ON by default.** This is the mechanism behind three-gate Gate 2 (card exists) and Gate 3 (card non-default): if MA5 generated a REAL default, the operative card is real (Gate 3 open); if generation failed and only the shipped `@MG5aMC skip_analysis` template was present, the copied operative card is skip-only (Gate 3 closed / no-op).
- Note the copy loop is over `['hadron','parton']` regardless of the `levels` passed — but it is `os.path.isfile`-guarded, so at NLO (only the hadron `_default.dat` was generated) only the hadron operative card is copied; the parton branch finds no file and is skipped. Consistent with hadron-only NLO.

## Where the shipped fallback template fits
- `Template/LO/Cards/madanalysis5_{parton,hadron}_card_default.dat` (ma5-card-structure page) is the `@MG5aMC skip_analysis` 3-line fallback. Its header comment "This card is used only if MA5 failed to create a default for this run" now has a precise meaning: it is the `_default.dat` that ships in the Template, OVERWRITTEN by create_default_madanalysis5_cards when MA5 successfully generates a tailored one; if generation/interpreter fails, the skip-only template remains and gets copied to the operative card -> a no-op analysis (Gate 3 closed).

## Cautions
- The OUTPUT-time gate (export, 3 conjuncts incl. proc_defs) is distinct from the RUN-time path-truthy gate (three-gate Gate 1). A directory can lack MA5 cards because output-time creation was gated off (standalone / proc_defs None / path None at OUTPUT time), independent of run-time path state.
- StandAlone exports never get MA5 cards (bypass override, export_v4.py:2853-2855: `def create_MA5_cards(self,*args,**opts): pass`).
- The card TEXT content (generate_card) is MA5-internal; this page owns only the WHEN/WHERE/HOW-COPIED, not what the analysis card says.
- The CLOSED direction is probe-confirmed here (path nulled -> gate closed -> no cards at output time). The OPEN direction — "a fresh `output` dir carries non-skip operative MA5 cards when MA5 IS installed+functional at output time, parton+hadron for LO and hadron-only for NLO" — is HYPOTHESIS (NOT probe-verified): cannot drive it because MA5 is not installed here. Probe: install MadAnalysis5, `output` a simple LO proc, confirm `Cards/madanalysis5_{parton,hadron}_card.dat` exist and are non-skip; repeat for `output standalone` (expect none) and an NLO output (expect hadron only).
