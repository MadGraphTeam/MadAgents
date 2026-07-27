---
description: The ask() flow, timed_input timeout (SIGALRM), SmartQuestion/OneLinePathCompletion/AskforCustomize (do_customize_model) widgets, and check_answer_in_input_file (script-mode answer matching).
---

# ask() / question widgets / timeout (`extended_cmd.py`)

## `Cmd.ask` (1089)
Central question entry. Signature: `ask(question, default, choices=[], path_msg=None, timeout=True, fct_timeout=None, ask_class=None, alias={}, first_cmd=None, text_format='4', force=False, return_instance=False, **opt)`.
- `timeout is True` → pulls `self.options['timeout']` (1102-1106).
- Builds the bracketed `[default, choice, ...]` prompt; default rendered in ANSI color `text_format` (default `'4'`=blue). Truncates the displayed choice list + appends `...` (cap read at 1118).
- Widget class: explicit `ask_class`, else `OneLinePathCompletion` if `path_msg`, else `SmartQuestion` (1123-1128).
- `force=True` → returns `default` without prompting.
- Non-interactive: calls `check_answer_in_input_file` FIRST (1152); if it returns non-None, uses that (with `alias` remap).
- Interactive: `Cmd.timed_input(question, default, timeout, fct=question_instance, fct_timeout=...)` (1173).

## ask() alias remap, ask_class return, return_instance (1130-1193)
- `alias` is a `{user_word: canonical}` dict. Its KEYS are appended to `choices` (1130-1131) so they tab-complete and match. The remap fires on BOTH paths: non-interactive (1154-1155, after `check_answer_in_input_file`) and interactive (1179-1182, wrapped in `try/except TypeError` so a non-hashable widget answer — e.g. a ControlSwitch dict — is left alone).
- `ask_class` set (a ControlSwitch/AskRun-style widget) changes the RETURN: when a script answer is found, `ask()` runs `question_instance.default(line)` + `postcmd(answer, line)` and returns `question_instance.answer` — the multi-axis switch dict, NOT the raw line (1156-1163). Same on the interactive `value==default` path (1184-1187: `value = question_instance.default(default)` then `.answer`). So an `AskRun`/`AskRunNLO` invoked via `ask(..., ask_class=...)` returns its assembled switch dict even when answered from `-f`/script.
- `return_instance=True` returns `(answer, question_instance)` so the caller can inspect post-answer widget state (e.g. `inconsistent_keys`, `get_cardcmd`) (1160-1169, 1190-1193).
- `check_answer_consistency` hook: if the widget defines it, it runs on a matched script answer (1164-1165).
- `fct_timeout` default (1138): `lambda x: question_instance.postcmd(x, default) if x and default else False` — on timeout with a non-empty answer AND a default, the answer is run through `postcmd` (validated) rather than blindly used; `timed_input` calls `fct_timeout(True)`.
- `first_cmd` (1139-1144): a string or list of lines run through `question_instance.onecmd` BEFORE the prompt — pre-seeds the widget (e.g. set a switch before asking).

## `timed_input` (1770, staticmethod)
- Installs `SIGALRM` handler raising `TimeOutError` (1774-1777).
- `signal.alarm(timeout)`; appends `[Ns to answer]` to prompt (1783-1784).
- On `TimeOutError` with `noerror` (default): logs `use <default>`, calls `fct_timeout(True)`, returns default. `finally: signal.alarm(0)`.
- `timeout=0`/falsy → no alarm (no time limit). Config key `timeout` default read fresh in `options_configuration` (config-system.md) / template.

## SmartQuestion (2125, `BasicCmd` subclass)
Interactive Q/A with default + validation. `smart_input(text, allow_arg, default)` (2343) is the procedural shortcut.
- `__init__` (2139): stores `question`, `allow_arg` (stringified), `default_value`, `mother_interface`. `case`/`casesensitive` opt.
- `postcmd` (2293) is the validator: accepts if value in `allow_arg`; `EOF`→default; bare command (`do_X`) or `repeat`/`reask`→`reask()`; if `allow_arg` empty accept anything (2305). `=` normalization. Invalid → warn "not valid argument. Valid argument are in (...)", retry. After the `wrong_answer` cap is hit → forces default (limit at 2334).
- `default`/`emptyline` (2278/2286): empty line → `default_value`.
- `completenames` (2171) cancels any pending timer via `signal.alarm(0)` and prints `[timer stopped]` — tab completion stops the countdown.
- `reask` (2227): re-prints question, re-arms timer if `[Ns to answer]` present.

## OneLinePathCompletion (2351, SmartQuestion subclass)
Path-completion variant; `allowpath=True`. `postcmd` (2403) accepts a value that `os.path.isfile` → returns relpath, or `http`/`www` URL. `precmd` cancels timer. `raw_path_input` (2430) is its procedural shortcut.

## AskforCustomize (madgraph_interface.py 10303, SmartQuestion subclass)
The widget behind `do_customize_model`. NOT in extended_cmd — lives in madgraph_interface but is a question-widget in this slice.
- `__init__` (10307): loads the UFO model's `build_restrict.all_categories`; builds `name2options` mapping numeric index AND despaced option-name → the restriction option object; `allow_arg = ['0'] + indices + ['done']`.
- `get_question` (10382): renders each category and `i: name [status]`; footer "Enter a number to change its status or press enter to validate" + "For scripting ... type 'help'".
- `default` (10333): a bare number/name toggles `option.status` and sets `self.value='repeat'` (re-asks with updated menu); empty → default_value; `do_X` line → dispatches.
- `do_set NAME VALUE` (10359): scripting hook — sets a named option's status True/False (accepts True/1/.true./T..., False/0/.false./F...). `complete_set` (10399) completes option names then True/False. This is how a script non-interactively drives model customization.
CAUTION: toggles mutate the in-memory UFO option objects; the actual restricted model is produced downstream by the model-loader (out of slice) from these statuses.

## The editor-return timing guard ("Are you really that fast?")
`common_run_interface.py:7780-7801` (`AskforEditCard`-side, the `open`/reload-card flow behind `edit_cards`): after `exec_cmd('open <card>')` returns, if `time.time() - start < .5` (the OS `open` returned in under half a second — an editor that forks/returns immediately, or a headless env with no blocking editor), it fires
`self.mother_interface.ask("Are you really that fast? If you are using an editor that returns directly. Please confirm that you have finised to edit the file", 'y', timeout=False)` [note the source typo "finised"], THEN `reload_card(path)`.
- `timeout=False` → no SIGALRM arm (`timed_input` skips the alarm, ask-flow above); it blocks indefinitely for a real `y`. Default answer `'y'`.
- In script/`-f` mode this resolves through `check_answer_in_input_file` (allow_arg from the y/n `ask`) — an unmatched next line falls to default `'y'` per Layer-3 (script-mode-answer-resolution.md), so a non-interactive run does not hang here.
CAUTION: the prompt only appears when the editor call returns fast; it is a race-guard against reloading a card the user never actually edited, NOT a SmartQuestion/CmdFile timing check. The `ask` mechanism is in-slice; the surrounding card-reload flow is the edit-cards/card slice.

## check_answer_in_input_file (1220) — script-mode answer matching
Only active when `self.inputfile` set (non-interactive). Reads next line, strips comments, and matches against `question_instance.allow_arg`:
- exact / `line;` / case-insensitive match → returns it.
- if line is a `do_X` command → executes it and recurses to next line (1256).
- path mode → accepts existing file / URL.
- `special_check_answer_in_input_file` hook (used by ControlSwitch).
- If no match and piping → stores line for parent, returns None (prints question, falls to pipe). Else logs warning, stores line for next question, uses `default` (1298-1302). KEY: an unmatched answer is NOT consumed — it is kept for the *next* question.

CAUTION: in `bin/mg5_aMC` script mode (`run_cmd('import file')`) `use_rawinput=False` and `haspiping=False` are set explicitly (mg5_aMC:214-215), so the inputfile path is the one taken.
