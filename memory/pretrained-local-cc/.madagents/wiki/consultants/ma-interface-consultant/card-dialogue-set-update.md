---
description: Card-dialogue `set`/`update` dispatch in AskforEditCard (common_run_interface.py:5868) — key=val parse, per-card set routing table, special-shortcut macros, `update <block>`/`to_full` hidden-param reveal via banner.py RunBlock, and the config-vs-card do_set split.
---

# Card-dialogue `set` / `update` + run_card hidden-block reveal

Scope: the `AskforEditCard` widget in `common_run_interface.py` — the `set`/`update` command dispatch during the launch card-editing dialogue, and the run_card hidden-parameter reveal mechanism (banner.py `RunBlock`). This is the CARD-editing `do_set` (`common_run_interface.py:5868`), NOT the config `do_set` (`common_run_interface.py:3536` CommonRunCmd / `madgraph_interface do_set@8941`). Different objects: card `set run_card X` edits `self.run_card`; config `set` edits `self.options`. See config-system.md for the split.

## `set` command parse (`do_set` @ common_run_interface.py:5868)
- `common_run_interface.py:5878-5882`: `key=val` glued form split; standalone `=` removed. So `set run_card ebeam1=6500` and `set run_card ebeam1 6500` both parse.
- `:5884`: `args[:-1]` lowercased (targets case-insensitive; the VALUE keeps case). So `set PbPb` → token `pbpb`.
- `:5888-5939`: **special-shortcut branch** (macros) checked FIRST — see below.
- `:5941-5944`: needs ≥2 args otherwise "Invalid set command (need two arguments)".
- `:5975-6077`: leading card-name token (`run_card`/`param_card`/`pythia8_card`/`madloop_card`/`delphes_card`/`shower_card`/`rivet_card`/`madweight_card`/`madspin_card`) sets `start=1` and gates on the card existing (`has_PY8`, `has_ml`, etc.). `set <card> default` resets that card to default template. `set madspin_card ...` is REFUSED (6075-6076: use `decay` instead). `set delphes_card atlas|cms` copies the ATLAS/CMS template.

## Per-card `set` routing table (verified do_set @5975-6370)
- **madspin_card**: ONLY `set madspin_card default` accepted (6069-6073 → `files.cp(MS_default, madspin)`). Any other `set madspin_card <p> <v>` → `else` at 6074-6077 emits verbatim `"Command set not allowed for modifying the madspin_card. \n Check the command \"decay\" instead."` and returns. So no per-param editing of madspin via `set`. Parameters instead reach it via `add madspin_card ...` or the `spinmode`/`nodecay` macros (below).
- **delphes_card**: PRESETS ONLY. `atlas`→cp `delphes_card_ATLAS.dat` (6010-14); `cms`→cp `delphes_card_CMS.dat` (6015-19); `default`→cp default template (6024-26). Any other `set delphes_card <param> <val>`: no delphes-param dispatch branch exists downstream, so it falls to the INVALID branch (6357-6370). No arbitrary-parameter editing. (No `lhc` preset here — that template exists but `set` does not wire it.)
- **pythia8_card**: `set pythia8_card X Y` → PY8 branch 6304-6322 → `setPY8(X, Y)` then `PY8Card.write(..., print_only_visible=True)`. setPY8 SETS/ADDS the directive in `self.PY8Card` (adds it if not already present) — effectively appends/overrides a Pythia8 directive. `set pythia8_card default` restores template (6054-61).
- **run_card / param_card / shower_card / MadLoop_card / rivet_card / fo_card / MadWeight_card**: full `set <card> <param> <val>` per-param editing, each its own dispatch branch (run 6080, param 6117/6187, MW 6206+, shower 6253, ML 6286, PY8 6304, rivet 6324, fo 6341). `set <card> default` supported per branch.
- **INVALID fall-through (6357-6370)**: any `set <token> <val>` that matches no card-name and no card's param dict → `logger.warning('invalid set command %s ' % line)` (note trailing space in format string) + a "Did you mean" hint scanning PY8Card / run_card names, then returns (drops the command).

## Bare `set <param>` (no card prefix) routing
Bare `set <param> <val>` (start=0) is disambiguated by matching `args[0]` against each card's key set in dispatch order, gated on `card in ['', ...]`:
- Matches a run_card key (`args[0] in run_card.keys()`, 6080) → run_card. Matches `pname2block`/param_card → param_card. Matches `PY8Card` → pythia8. Etc.
- **`spinmode` is NOT dispatched as a bare param** — it is a `special_shortcut` (registered `init_madspin` @5364-65: `'spinmode':([str], ['add madspin_card --before_line="launch" set spinmode %(0)s'])`). The special_shortcut branch (5888) fires FIRST, before all card routing, so bare `set spinmode full` expands to `add madspin_card --before_line="launch" set spinmode full` → `do_add` appends that line into the madspin_card. That is why spinmode reaches the madspin_card while direct `set madspin_card ...` is refused.
- **`BW_cut`, `seed`, etc.** are neither special_shortcuts nor keys of any present card (run_card's seed key is `iseed`, not `seed`; `BW_cut` is a MadSpin/param concept, not a card dict key) → they fall to INVALID (6357), warned + dropped. So bare `set BW_cut 15` in a launch dialogue silently does nothing but warn.

## Bare file-path in launch block: auto-detected + copied
Handled by `AskforEditCard.default()` (7202), NOT do_set. When a dialogue line is not a recognized command/keyword: `elif os.path.isfile(line): self.copy_file(line); self.value='repeat'` (7220-22), and a me_dir-relative path variant (7223-24), plus an http(s)/www URL fetch-to-tempfile variant (7226-40). `copy_file` (7693): `.lhco[.gz]`→MadWeight inputfile; else `detect_card_type(path)` (7710) classifies by CONTENT — `detect_card_type` (static, 1168) reads `open(path).read(50000)` and pattern-matches sentinel strings (`<MGVersion>`=banner, `ParticlePropagator`=delphes, `MSTP`=pythia, `req_acc_FO`, etc., 1197+). Then `files.cp(path, self.paths[card_name.rsplit('_',1)[0]])` copies to the correct Cards/ slot and `reload_card`s it (7714-17). `banner`→`split_banner` decomposes into constituent cards (7718-24). `unknown`→`"Fail to determine the type of the file. Not copied"` (7712-13). So dropping a raw `/path/to/foo.dat` line does content-based auto-detect + copy-to-right-location.
- `:6080` RUN CARD dispatch: `args[start] in [l.lower() for l in self.run_card.keys()]` → `setR`.
- `:6117` PARAM_CARD with block name: `set param_card <block> <pdg...> <value>`, key = `tuple(int(i) for args[start+1:-1])` (6150); `all` and `scale`/`scan`/`auto` special-cased.
- `:6187` PARAM_CARD no block name: bare `set <pname> <value>` resolved via `self.pname2block`.
- The syntax `set <card> <block_or_param> [index] <value>` works; bare form (no card token) also works, disambiguated by `self.conflict` (ambiguous name → assumed run_card w/ warning, 6087).

## `set` works on hidden params without revealing
`run_card.keys()` includes hidden params (`hidden_param` is derived FROM keys at banner.py:2049, params stay in the dict). `run_set` = `run_card_def.keys() + hidden_param` (common_run:5203). So the `:6080` membership test matches a hidden param, and `setR` (6401) stores it. NO reveal needed. Reveal (`update <block>`) only affects whether the param is WRITTEN VISIBLY to the card file, not settability.

## Process-aware hiding (mechanism is banner's; scales-pdf/run_card slice owns semantics)
run_card blocks are `RunBlock` objects (banner.py:2581). `RunBlock.status(card)` (2646-2658): returns True (write full `template_on`) iff `self.name in card.display_block` OR a user set an `on_field`; else `template_off` (minimal/hidden). `create_default_for_process` per-block appends to `display_block` based on the process (e.g. beam_pol/ecut/mlm/ckkw revealed by process characteristics, banner.py:4804-5103). So blocks irrelevant to the process write as `template_off`. The full per-param hidden list is `hidden_param`.

## `update to_full` reveals ALL hidden run_card params
`do_update` (6890) → `update_to_full` (6902) → `self.run_card.write(..., write_hidden=True)`. banner.py:3161-3167: `write_hidden` unions `to_write` with `set(self.hidden_param)` → every hidden param printed. `update to_full run_card` is the documented form (help @6827/6838); arg after to_full is passed but the LO path writes the run_card regardless.

## `update <block>` valid names = run_card block names (LO ≠ NLO)
Dispatch: `do_update` @6892 `elif args[0] in self.update_block:` → `self.run_card.display_block.append(args[0])` + delayed write. `update_block` = `[b.name for b in self.run_card.blocks]` (common_run:5246).
**Actual LO block names** (banner.py:4190-4192 `RunCardLO.blocks`, names = RunBlock 1st arg):
`ion_pdf, beam_pol, syscalc, ecut, frame, eva_pdf, mlm, ckkw, psoptim, pdlabel, fixed_fact_scale, RUNNING`.
- The full LO block set is the names above (count read fresh at banner.py:4190-4192); note in particular `eva_pdf`, `pdlabel`, `fixed_fact_scale`, `RUNNING` alongside the more familiar beam_pol/ecut/ion_pdf/psoptim/mlm/ckkw/frame/syscalc.
- **NLO run_card** (banner.py:5599 `RunCardNLO.blocks`) is DIFFERENT: only `[heavy_ion (ion_pdf), RUNNING]`. So `update mlm`/`update beam_pol` are LO-only; invalid at an NLO run_card dialogue.

## `update dependent|missing|to_slha1|to_slha2` target PARAM_CARD
`do_update` @6848-6889: `dependent`→`update_dependent` (recomputes non-free masses/widths, calls `do_compute_widths` if auto), `missing`→`update_missing` (fill missing param_card blocks), `to_slha1`→`convert_to_slha1`, `to_slha2`→`convert_to_mg5card`. All operate on `self.paths['param']` / `self.param_card`. Command DISPATCH is this slice; param_card SEMANTICS (SLHA conversion, dependent-param formulas) belong to param-card / madwidth consultants.

## Silent no-validation at do_set layer (interface passes through; validation is banner's, deferred)
`setR` (6401-6409): interactive path calls `run_card.set(name, value, user=True)` with raiseerror DEFAULT False (only `inputfile`/script-mode passes `raiseerror=True`). So `set pdlabel nn31nlo` interactively is STORED, no error at set-time. Auto-correction / fallback for pdlabel is `PDLabelBlock`/`check_validity` at write/consistency time (scales-pdf slice owns pdlabel coherence). Interface layer = pass-through; the silent fallback is downstream. In script mode (`import ... /path` with inputfile) the same set CAN raise.

## `set no_parton_cut` and `set PbPb` macros — both real special_shortcuts
`special_shortcut` populated in `init_run_card` (common_run:5212-5225), gated on `self.run_set`:
- `no_parton_cut` → `['run_card nocut T']` → recursion hits do_set @6112 `elif card=='run_card' and args[start] in ['nocut','no_cut']:` → `self.run_card.remove_all_cut()`. Help: "remove all cut (but BW_cutoff)".
- `pbpb` → 7-command lead-lead heavy-ion setup (lpp1/2=1, nb_proton/nb_neutron/mass_ion for both beams to Pb). `set PbPb` works via the 5884 lowercase.
- Also: `pbp` (lead-proton), `pp` (reset to proton-proton), `ebeam`, `lpp`, `lhc`, `lep`/`ilc`, `lcc`, `fixed_scale`, `cm_velocity` (calls `set_CM_velocity` lambda).
- More special_shortcuts registered per-card-init: `simplepy8`, `mpi` (init_pythia8, 5317); `fast_rivet` (init_rivet, 5346); `spinmode`, `nodecay` (init_madspin, 5364). So the macro set is dynamic — depends which cards are present.

## Macro execution (5916-5938)
Each command string in the shortcut: if `do_<split[0]>` exists call it, else recurse into `do_set`. Non-string entries (lambdas like `set_CM_velocity`) are called with the parsed values. `format_variable` (5903) type-coerces macro args; `scan` args pass through.
