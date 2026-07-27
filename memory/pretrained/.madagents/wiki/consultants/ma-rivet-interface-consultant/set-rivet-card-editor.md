---
description: The interactive `set rivet_card <var> <value>` editor command (do_set) — setRivet path, immediate write (not delayed), single-token value grab quirk vs PY8, has_rivet gate, fast_rivet macro's cross-card MPI entry.
---

# `set rivet_card ...` interactive editor (do_set path)

The OTHER way a user changes a Rivet card value: the MadGraph-prompt `set` command, distinct from (a) text-editing `rivet_card.dat` and (b) the on-disk-string `__setitem__` parse (analysis-list-parsing.md). This page is the do_set control flow for `rivet_card`. All in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py` unless noted.

## Registration / gate
- `to_init_card` includes `'rivet'` (4956) -> `init_rivet(cards)` runs (5338-5357). `init_rivet` sets `has_rivet`, builds `self.rivet_card = RivetCard(paths['rivet'])`, `self.rivet_card_default = RivetCard()` (no file -> default_setup values), and `self.rivet_vars = [k.lower() for k in self.rivet_card.keys()]` (5355).
- `self.paths['rivet'] = Cards/rivet_card.dat`, `self.paths['rivet_default'] = Cards/rivet_card_default.dat` (5019-5020).
- `do_set` early gate: `if args[0]=="rivet_card": if not self.has_rivet: warn 'Invalid Command: No Rivet card defined.'; return` (6000-6004). So `set rivet_card ...` with no rivet card managed in this session -> warning, no-op.

## `set rivet_card default` — copy file, NO in-memory reload (6021-6033)
- `rivet_card` is in the `['run_card','param_card',...,'rivet_card']` list at 6021-6022; `args[1]=='default'` -> `files.cp(paths['rivet_default'], paths['rivet'])` (6026). Logs "replace rivet_card by the default card".
- The per-card reload `if` chain (6027-6032) handles ONLY param_card/run_card/shower_card -> reloads the in-memory object. rivet_card is NOT in that chain (the `return` is at 6033). So `set rivet_card default` copies the default FILE onto rivet_card.dat but leaves the in-memory `self.rivet_card` STALE for the rest of the editor session. (Same gap as delphes; contrast run_card/param_card which reload.)

## `set rivet_card <var> <value>` — the Rivet Parameter block (6324-6339)
```
elif self.has_rivet and (card in ['', 'rivet_card']) \           # 6325-6326
     and args[start].lower() in [k.lower() for k in self.rivet_card.keys()]:
    if args[start] in self.conflict and card=='': warn 'ambiguous'; return  # 6328-6331
    if args[start+1] == 'default':                                # 6332
        value = self.rivet_card_default[args[start]]; default = True  # 6333-6334
    else:
        value = args[start+1]; default = False          # <-- SINGLE TOKEN, 6336
    self.setRivet(args[start], value, default=default)            # 6338
    self.rivet_card.write(self.paths['rivet'], self.paths['rivet_default'])  # 6339
```
- `card in ['','rivet_card']`: a bare `set <var> <value>` (no card prefix) reaches this block when `<var>` is a rivet key AND not claimed by an earlier elif (run_card/MadLoop/PY8 are checked first; ambiguous names go to run_card per the conflict logic).
- **Immediate write, NOT delayed.** run_card uses `self.modified_card.add('run')` (deferred write at editor exit); rivet writes the file RIGHT NOW via `self.rivet_card.write(...)` (6339). Every `set rivet_card` line re-serialises rivet_card.dat on the spot. (Same eager pattern as PY8/MadLoop/Delphes; opposite of run_card/param_card delayed.)

## setRivet (6433-6441)
- `self.rivet_card.set(name, value, user=True)` — `ConfigFile.set` (banner.py:1548) -> `__setitem__(name, value, change_userdefine=True)`, i.e. the SAME list-coercion / format_variable machinery as the on-disk parse (analysis-list-parsing.md). So `set rivet_card analysis [MC_JETS,MC_MET]` goes through bracket-strip + comma/space split + quote-strip.
- **Failure is non-fatal at the prompt.** setRivet wraps `.set` in try/except: any Exception -> `logger.warning("Fail to change parameter. Please Retry. Reason: %s.")` and `return` (6435-6438). So a bad value typed at the editor prompt warns and is dropped; it does NOT crash the editor. (Contrast: a bad value text-edited INTO the file surfaces later — at RivetCard.read / do_rivet time.)
- `user=True` marks the key in `self.rivet_card.user_set`; `set ... default` additionally REMOVES the key from user_set so future default-reset logic can touch it (6440-6441).

## Quirk: single-token value grab (6336 vs PY8 6317)
- Rivet: `value = args[start+1]` (6336) — ONLY the first whitespace token after the var name. (The adjacent `if args[start+1]=='default'` branch test is at 6332; the actual single-token assignment is in the `else` at 6336.)
- Pythia8: `value = ' '.join(args[start+1:])` (6317) — joins ALL remaining tokens.
- Consequence: at the prompt, `set rivet_card analysis [MC_JETS MC_MET]` (SPACE-separated) passes only `[MC_JETS` to setRivet -> `__setitem__` strips `[`, gets `["MC_JETS"]` (the closing `]` and `MC_MET` are lost). A COMMA-separated `[MC_JETS,MC_MET]` is one token -> survives. So multi-analysis selection via the `set` command MUST be comma-joined with no internal spaces (or quoted) — space-separation works when text-editing the FILE (the file read passes the whole bracketed string) but NOT via the `set` command. Non-obvious asymmetry between the two edit routes.
- Same single-token grab also affects any rivet value with embedded spaces (e.g. a latex `xaxis_label` like `mass_{Z'}` typed unquoted) — truncated to the first token via this command.

## fast_rivet macro is do_set lines, incl. a CROSS-CARD entry (5345-5347)
`special_shortcut['fast_rivet']` = `([], [ 'rivet_card run_rivet_later True', 'rivet_card draw_rivet_plots False', 'pythia8_card HEPMCoutput:file hepmc', 'partonlevel:mpi = off' ])`.
- The macro is a LIST OF `set` ARGUMENT STRINGS replayed through do_set. First two prefix `rivet_card`; third prefixes `pythia8_card`.
- The 4th entry `'partonlevel:mpi = off'` has NO card prefix. It reaches the **Pythia8 Parameter** block via `card=='' and args[start] in self.PY8Card` (6305-6306) — `partonlevel:mpi` IS a PY8Card key (probe-confirmed: `'partonlevel:mpi' in banner.PY8Card()` == True, case-insensitive `__contains__`), so it sets the Pythia8 card's MPI off. (The `= off` is parsed by do_set's arg-splitting; the bare-name PY8 block joins remaining tokens via `' '.join(args[start+1:])` at 6317.) So `fast_rivet` (a Rivet shortcut) edits the PYTHIA8 card to disable MPI — a cross-card side effect, the reason fast_rivet "speeds up" the shower as well as the Rivet handling.
- fast_rivet help (5349): "Fastest way to run multiple Rivet runs when scanning. Does NOT compress the HepMC files so enough storage should be guaranteed!" (HEPMCoutput:file = `hepmc`, uncompressed).

## complete / tab-completion (5649-5650, 5722-5723, 5765-5769)
- `has_rivet` gates `rivet_card` into the `set`-completion category list (5722-5723) and into `complete_set`'s `args==1` allowed dict (5649-5650).
- `set rivet_card <TAB>` completes from `self.rivet_vars` (5765-5769), with `'default'` appended when `allowed['rivet_card']=='default'`.

## Boundaries / cross-refs
- This is the EDITOR command. What the resulting card VALUES mean at run time -> do_rivet-flow.md (execution), analysis-selection.md (getAnalysisList), run-now-vs-defer.md (run_rivet_later).
- The string->list coercion invoked by setRivet is documented mechanism-side in analysis-list-parsing.md (shared banner.py infra).
- has_rivet itself (the gate that enables this whole block) is rivet-suppression-gates.md Gate 3 / install-and-config.md.
- A note on two config defaults seen while walking: `common_run_interface.py:656-657` defaults `rivet_path`/`yoda_path` to `None`, whereas `madgraph_interface.py:3050` defaults `rivet_path` to `'./HEPTools/rivet'`. Different default-config dicts in different interface classes; the validity check (madevent_interface.py:2159-2162) rejects either unless `<path>/bin/rivet` exists. (install-and-config.md.)
