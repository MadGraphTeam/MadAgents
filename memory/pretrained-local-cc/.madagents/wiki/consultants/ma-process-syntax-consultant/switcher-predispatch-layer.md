---
description: The master_interface Switcher front-end intercepts generate/add process/check, runs extract_process_type to classify LO vs NLO + route to MadGraph/aMC@NLO/MadLoop, and validates _valid_nlo_modes BEFORE MadGraphCmd's check_process_format/extract_process — the user-visible bad-NLO-mode error site.
---

# Switcher pre-dispatch layer (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/master_interface.py`, `class Switcher` at **56**.
The interactive interface is `MasterCmd(Switcher, LoopInterface, aMCatNLOInterface, ...)` (**655**) — MRO puts `Switcher` FIRST, so a user's `generate`/`add process`/`check` hits the Switcher method before any `MadGraphCmd` method. The orchestration/arrow/enum pages describe the `MadGraphCmd` layer that runs AFTER this one.

## What the Switcher does on each command
- `Switcher.do_generate` (**260**), `Switcher.do_add` (**200**), `Switcher.do_check` (**239**): each calls `extract_process_type(proc_line)` then, if `type=='NLO'`, validates `nlo_mode in self._valid_nlo_modes` and raises `'The NLO mode %s is not valid. Please chose one among: %s'` (do_generate **268-270**; do_add **211-213**, note do_add's message says "choose"/`InvalidCMD`; do_check **245-247**). On a valid mode it calls `change_principal_cmd('aMC@NLO'|'MadLoop'|'MadGraph')` to swap the active sub-interface, THEN delegates: `return self.cmd.do_generate(self, line, ...)`.

## extract_process_type (162) — independent bracket parse
- Does its OWN spacing normalisation (same `space_before` regex as extract_process) then `loopRE = re.compile(r"^(.*)(?P<loop>\[(\s*(?P<option>\w+)\s*=)?(?P<orders>.+)?\])(.*)$")` (**175**) on `re.split(r'\s\-\-', line, 1)[0]`.
- No bracket → `('tree', None, [])`. Bracket with `option=` → `('NLO', option, orders)` (or `('tree','tree',...)` if option is literally `tree`). Bracket, no option → `('NLO', None|'LOonly', ...)`.
- This is a SECOND, independent perturbation-bracket parser distinct from extract_process's `perturbation_couplings_pattern` (madgraph_interface.py 4852). Its job is interface ROUTING, not the final ProcessDefinition.

## Why this matters: message precedence
The bad-NLO-mode message the user sees comes from the **Switcher** (268/211/245), NOT from `extract_process` (madgraph_interface.py 4863 check / 4871-4872 raise). The Switcher runs before `MadGraphCmd.check_process_format` (the arrow-count guard) and before `extract_process`. So a line that is BOTH malformed (bad arrow count) AND has a bad NLO bracket yields the NLO message, because the Switcher pre-empts the arrow check.

## Probe-confirmed (v3.7.1, sm)
- `generate u u~ > z [badmode= QCD]` → `InvalidCmd : The NLO mode badmode is not valid. Please chose one among: all real virt sqrvirt tree noborn LOonly only`.
- `generate u u~ > z > z > z [badmode= QCD]` (3 arrows AND bad mode) → SAME NLO message, NOT the arrow-count "3 found" message. Confirmed via `bin/mg5_aMC` and via direct `MasterCmd().do_generate(...)`. Calling `MadGraphCmd.check_process_format` directly on the same string DOES raise the arrow message — proving the Switcher pre-empts it on the real path.

## CAUTION
- `_valid_nlo_modes` is therefore consumed at THREE sites: Switcher 211/245/268 (routing + user-visible reject) and extract_process 4863 (after routing). See valid-mode-enumerations.md and arrow-validation-two-checks.md.
- `MasterCmdWeb` (711) has its own `do_generate`/`do_add` (756/767) — Web override, not the interactive path.
