---
description: ControlSwitch multi-axis Q/A widget (extended_cmd.py 2437) — the engine behind AskRunNLO/AskRun; per-key customization hooks, switch dispatch, consistency, get_cardcmd.
---

# ControlSwitch widget (`extended_cmd.py` 2437)

Abstract multi-axis question widget. Subclassed by `madevent_interface.AskRun` (497) and the NLO `AskRunNLO`-style classes. Asks "which programs to run" — each axis (shower, analysis, detector, ...) is one switch key. Subclass of `SmartQuestion`.

## Customization hooks (per key XXXX), all optional (docstring 2441-2473)
- `set_default_XXXX()` — default value (superseded by `self.default_switch[key]` dict if present).
- `get_allowed_XXXX()` — list of legal values (default `['ON','OFF']`, line 2616).
- `check_value_XXXX(value)` — whether USER may set it (system can set others like "Not available").
- `switch_off_XXXX()` — special-mode off.
- `color_for_XXXX(value)` — screen representation.
- `get_cardcmd_for_XXXX(value)` — command(s) to run to make cards match the chosen status.
- `print_options_XXXX()` — text under "other options".
- `consistency_XX_YY(val_XX,val_YY)` → None or `"replace_YY"`; `consistency_XX(val_XX)` → dict of replacements.
- typing `NAME` → `self.ans_NAME(None)`; `NAME=XX` → `self.ans_NAME('XX')`.

## Construction (`__init__` 2478)
- `to_control` = list of `(KEY, prompt-text)`. `self.switch[key.lower()]` initialized 'temporary' then `set_default_switch()` (2500).
- builds `allowed_args` for completion: numeric `1;`..`N;`, `key=value;` for each allowed value, `ans_*` names, `0`/`done` (2504-2514).
- `self.options = mother_interface.options` (2516).
- `quit_on = ['0','done','EOF','','auto']` (2476); `case_sensitive=False` (2475).

## Dispatch (`default` 2618) — the parser
Handles `;`-joined lines recursively. Forms:
- `key=value` / numeric `N=value` (N→to_control name) / `key value` / bare `ans_NAME` / bare number N (cycles to next allowed value for that axis) / bare key (cycles allowed values).
- `''`/`done`/`EOF`/`0` → finish, return `self.answer`.
- `auto` → sets `switch['dynamical']=True`.
- routes to `ans_<base>(value)` if defined, else `set_switch(base,value)`.
- unknown → `logger.warning('unknow command')`, `self.value='reask'`.
- `set ...` with no `do_set` → `NotValidInput`.

## answer / consistency
- `answer` property (2713): coerces any key failing `check_value` to 'OFF'; merges `inconsistent_keys` overrides.
- `inconsistent_keys`/`inconsistent_details`/`last_changed` track cross-axis conflicts; resolution order from modification order.
- `special_check_answer_in_input_file` (2518): for script-mode, validates `key=value` where check_value is False but the axis exists (allows setting even if a module is missing). A bare `set ...` line is stored for the mother and default returned.
- `get_cardcmd` (2598): aggregates `get_cardcmd_for_*` over chosen switch values — this is how the widget translates UI choices into card-customization commands.
- `onecmd` (2707) re-runs `create_question()` after each command so the displayed menu refreshes.

CAUTION: `check_value` returning False silently maps a key to 'OFF' in `answer` — a chosen program whose backing tool is missing disappears from the returned switch dict rather than erroring.

## Script-mode form (a `launch` switches block inside a `.mg5`): keyword vs number
Both forms parse — `allowed_args` (2504-2514) registers numeric `1;`..`N;`, `key=value;`, `ans_*` names, and `0`/`done`, and `special_check_answer_in_input_file` (2518) matches script lines against that set. But they are NOT equivalent in a script:
- `key=value` (e.g. `shower=PYTHIA8`, `detector=Delphes`) sets that axis to a NAMED value deterministically via `set_switch` — the form scripts should use.
- a bare number `N` (or bare key) CYCLES the axis to its next allowed value (`default` dispatcher 2618), which depends on the axis's CURRENT state — non-deterministic in a script, so avoid it there even though it is accepted.
The block ends with `done` / `0` / (interactively) empty-Enter — all in `quit_on=['0','done','EOF','','auto']` (2476), finishing and returning `self.answer`. In a `.mg5` script the block MUST be terminated with an explicit `done`/`0` line (there is no blank-Enter); the enclosing `import_command_file` feed then continues past it. (do_launch itself + which switches exist = launch/amcatnlo slices; this is only the widget's parse of the block.)

## Is a `key=value` value case-normalized at the prompt? (verified)
Question: does `shower=PYTHIA8` vs `shower=pythia8`, or `analysis=MadAnalysis5` vs `madanalysis5`, matter?
- **`default` parse (2628-2631):** `if '=' in line` → `base, value = line.split('=',1)`, both `.strip()`ed. `1=OFF` numeric-base form supported (2633-2637: digit base → `to_control[N-1][0]`). Then base is `.lower()`ed (2685) and routed: `ans_<base>` hook if defined (2686-2689), else `set_switch(base,value)` (2690-2691).
- **Value normalization is CASE-INSENSITIVE by default, done in `set_switch` (2759-2766):** `case_sensitive = False` class attr (2475); `is_case_sensitive(key)` (2699-2705) returns that unless a `case_<key>` attr overrides. When not case-sensitive AND `value not in get_allowed(key)` exactly, it builds `lower=[t.lower() for t in get_allowed(key)]`, finds `lower.index(value.lower())`, and REMAPS `value` back to the **canonically-cased** allowed string `get_allowed(key)[ind]` (2766). So `PYTHIA8`/`pythia8`/`Pythia8`, `MadAnalysis5`/`madanalysis5`/`MADANALYSIS5` all resolve to whatever exact casing the axis's `get_allowed_<key>()` registers — the input casing does NOT matter for matching. On no-match the input case is kept (2763-2764 `pass`) so `check_value` still gets a shot.
- For an `ans_<key>` hook the value is lowercased before the call (2687-2688 in `default`, 2755-2756 in `set_switch`) — same case-insensitivity, but lowercased (not canonical-remapped) since the hook owns interpretation.
- **`case_sensitive=False` is inherited unchanged by the LO launch dialogue** (`madevent_interface.AskRun`): no `case_shower`/`case_detector`/`case_analysis` overrides and no `ans_shower/detector/analysis` hooks exist there (grep 560/643/742 = only `get_allowed_*`), so all three go through the canonical-remap `set_switch` path. Value casing at the launch prompt is therefore irrelevant for these three axes. (The concrete allowed strings for `analysis` + their MA5 parton/hadron mapping = ma-madanalysis5-interface-consultant; the launch orchestration = ma-launch-consultant.)

## Unknown / unavailable value handling (verified)
- **Unknown value** (not in `get_allowed`, and no case-fold match): `check_value(key,value)` is the gate (2768). If it returns falsy → `logger.warning('"%s" not valid option for "%s"', value, key)` and `set_switch` returns WITHOUT mutating (2769-2771). `self.value` stays `'reask'` (set at 2684), so `postcmd` (2744-2746) re-runs `create_question()` + `reask(True)` — the user is re-shown the menu, NOT dropped. No exception in the normal interactive path.
- **Unavailable module** (value is a legal name but the backing tool is missing): same `check_value`-False → warning + no mutation. Additionally, even a value that WAS set can be coerced to `'OFF'` at read time — the `answer` property (2717-2719) loops `to_control` and forces any key whose current value fails `check_value` to `'OFF'`. So a chosen-but-unavailable program silently disappears from the returned switch dict (CAUTION below).
- A `check_value` that returns a STRING rewrites the value (2772-2773) — a "reject" can instead be a "corrected to X".

## The mutation + consistency engine (`set_switch` 2749 → `check_consistency` 2795)
The actual axis-mutation path (the `default` dispatcher routes here for any key with no `ans_<key>` hook):
- `set_switch(key, value, user=True)` (2749): `assert key in self.switch`. If an `ans_<key>` method exists, defers to it (with case-fold) and returns. Else case-folds `value` against `get_allowed(key)`, calls `check_value(key,value)` — False → `logger.warning('"%s" not valid option for "%s"')` and returns WITHOUT mutating; a STRING return from `check_value` replaces the value (a check can rewrite, not just accept/reject). Sets `self.switch[key]=value`; if `user` → `check_consistency(key,value)`.
- `check_consistency(key,value)` (2795): pushes `key` to the end of `last_changed` (modification order = resolution order). Builds a `rules` dict `{key2: None|replacement}`: if a `consistency_<key>` method exists it returns the whole dict at once (`consistency_KEY(value, self.switch)`); ELSE it probes each pair via `consistency_<key>_<key2>(value, value2)`. A per-pair rule whose suggested replacement itself fails `check_value` is DROPPED to None (unless it was 'OFF') with a debug log — so a consistency fix that needs a missing tool is silently abandoned. Records surviving conflicts into `inconsistent_details`/`inconsistent_keys` (the {orig_value, changed_key, new_changed_key_val, replacement} record at 2840).
- `remove_inconsistency(keys=[])` (2780): empty → wipe all conflict state; else delete the named key's conflict record (run for the newly-set key first, so re-setting a key clears its prior conflict before re-evaluating).
- THE FIXPOINT ENGINE (2868-2919): recording conflicts is only the first half. `check_consistency` then runs an ITERATIVE resolution loop — seeds `tmp_switch=dict(self.switch)`, builds a `to_check` worklist of `(changed_key, new_val)` pairs from all `inconsistent_details` (sorted by `last_changed` index, so modification order = resolution order; the just-set `(key,value)` prepended at 2880), and pops/propagates: for each it re-derives `rules` (whole-dict `consistency_KEY` OR `check_consistency_with_all`, 2887-2891), applies any replacement into `tmp_switch` AND re-appends it to `to_check` (2893-2896) so a replacement can cascade into further conflicts. A dedup keeps only the LAST queued change per key (2900-2907, the `to_check=[('fixed_order','ON'),('fixed_order','OFF')]` comment case). Bounded by an `nstep` cap (read at 2908); on overflow → `logger.critical('Failed to find a consistent set of switch values.')` (2908-2909) [runtime string source-grounded, not probe-confirmed — needs a model with circular consistency rules]. The converged `tmp_switch` then rebuilds `self.inconsistent_keys` (2913-2919), skipping a key whose enforced value is 'OFF' for a missing tool (2917-2918). So the on-screen `value < replacement` arrows reflect a TRANSITIVELY-consistent set, not just the single pair that triggered — a switch the user never touched can show a replacement because a chain of consistency rules forced it.
CAUTION (`consistency_*` two forms): a `consistency_KEY` whole-dict method and per-pair `consistency_KEY_KEY2` methods are mutually exclusive per key — if the whole-dict form exists, the per-pair methods for that key are NOT consulted (2815-2830). The displayed `value < replacement` arrow in the menu comes from `inconsistent_keys`, not from `switch` — the chosen value and the enforced value can differ on screen.

## Menu rendering (`create_question` 3192, `question_formatting` 3021, `print_options` 2957)
`onecmd` re-calls `create_question()` after every command — this is the render path:
- `create_question(help_text=True)` (3192): reads live terminal size via `os.popen('stty size')` (fallback size hardcoded at 3192), then computes max column widths over all `to_control` rows (description / switch / name / add_info / potential-switch / nb-key-digits via `1+log10(len(to_control))`). Delegates the border/format strings to `question_formatting` (3021), then emits the bordered table. Each row's switch cell is colored by `color_for_value(key, switch[key])`; `add_info` from `print_options(key)` (2957, the per-key "other options" text); an inconsistent key shows `value < replacement` (3219). `hide_line` keys are SKIPPED under `-O` and shown green-highlighted with a strikethrough variant in a dev tree (3247-3264) — this is the same `__debug__` site catalogued on optimize-mode-debug-divergence.md (site 7).
- `do_help(line, list_command=False)` (2975) / `print_help_for_switch` (2998): bare `help` prints the how-to-change-a-switch legend + the list of `ans_*` special keywords; `help <NAME>` defers to `help_<NAME>()` if defined, else dumps the switch's allowed values + any `help_text_<NAME>` lines. So a ControlSwitch question is self-documenting per axis.

## Is a forced consistency override ANNOUNCED or SILENT? (verified)
Question: when setting one switch forces a dependent switch to change, does the widget PRINT a warning?
- **No warning/info is printed at override time.** `set_switch` (2749) → `check_consistency` (2795). Across 2795-2919 the ONLY log emissions are `logger.debug` (2827, an invalid *suggestion* was dropped) and `logger.critical` (2909, fired when the fixpoint loop exceeds its `nstep` cap — cap read fresh at the `if nstep >=…` guard, extended_cmd.py:2908, not cached here). Neither is a "your switch was changed" message. The normal forced-change path emits nothing — it only records the replacement into `self.inconsistent_keys` (2919).
- **The override value is NOT written into `self.switch`.** `self.switch[key2]` keeps the user's chosen value; the replacement lives only in `inconsistent_keys`. The EFFECTIVE value surfaces in two places: `answer` property (2713) does `out.update(self.inconsistent_keys)` (2725), and `get_cardcmd` (2598) reads `self.answer` (2602) — so the FORCED value, not the requested one, drives the card-customization commands.
- **Interactive vs scripted visibility differs.** Interactively, `postcmd` (2728) re-runs `create_question()`+`reask` after each non-quit command, and the redrawn menu shows the forced axis as a `chosen < replacement` arrow (create_question 3219, from `inconsistent_keys`). So the user DOES see the change on the next prompt — no warning, but a visible arrow. In non-interactive/`-f`/script-fed mode the menu is not re-displayed, so the correction is applied through `answer`→`get_cardcmd` with NO surfaced indication at all.
- **Net: a forced consistency override is un-announced but not invisible.** The override path emits NO `logger.warning`/`print` (across `check_consistency` 2795-2919 the only emissions are `logger.debug` 2827 and `logger.critical` 2909, neither a "your switch was changed" message), so the forcing is genuinely un-announced. BUT the next interactive menu redraw renders the forced axis as a `chosen < replacement` arrow (`create_question` 3219, from `inconsistent_keys`), so an interactive user sees the change on the following prompt. It is truly silent — effective config differing from requested with nothing surfaced — only under scripted / `launch -f` execution, where the menu is never re-displayed and the correction flows through `answer`→`get_cardcmd` unshown.

## The concrete shower/detector coupling lives OUTSIDE my slice (extended_cmd is mechanism-only)
No `consistency_*` methods exist in extended_cmd.py — the ControlSwitch base only PROVIDES the hook-dispatch. The concrete shower↔detector rules are the `AskRun` subclass in `madevent_interface.py` (sibling slice — launch / madevent-interface owns the Delphes/PGS semantics):
- `consistency_shower_detector(vshower,vdetector)` (madevent_interface.py:623): if `vshower=='OFF'` and detector is valid and ≠'OFF' → returns `'OFF'` (forces detector off). Also `Pythia8`+`PGS` → detector 'OFF'.
- `consistency_detector_shower(vdetector,vshower)` (madevent_interface.py:720): `Delphes` + shower∉{Pythia6,Pythia8} → returns `'Pythia8'` (if PY8 avail, else Pythia6, else raise); `PGS` + shower≠Pythia6 → `'Pythia6'`.
So BOTH directions are real and symmetric (set detector=Delphes on shower=OFF → shower forced Pythia8; set shower=OFF on detector=Delphes → detector forced OFF). **Precedence = whichever axis the user set LAST is the trigger and forces the other** (the mechanism keys resolution off `last_changed`, 2799-2801/2877). Which of the two competing symmetric rules applies is therefore determined by the user's last action, not a fixed shower>detector priority. The exact rule content + `available_module` gating are the sibling slice's to own.
