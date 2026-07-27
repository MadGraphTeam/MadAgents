---
description: The readline completion engine in extended_cmd.py BasicCmd — complete(), the @@category@@ sentinel protocol (deal_multiple_categories/print_suggestions), libedit fallback, prefix-splitting for -/=/:/backslash-space, path_completion, the preloop display-hook wiring, and how SmartQuestion completenames reuses the category mechanism.
---

# Tab-completion machinery (`extended_cmd.py` BasicCmd)

File: `$MADGRAPH_INSTALL/madgraph/interface/extended_cmd.py`. The custom readline
completion that produces MG5's categorized tab-completion menus. All in `BasicCmd`
(486) plus the question-widget reuse in `SmartQuestion`.

## Wiring (who installs what, when)
- `__init__` (108) default `completekey='tab'`; `preloop` (148 region) binds
  `readline.parse_and_bind('tab: complete')` and `readline.set_completer(self.complete)`.
- TWO display-hook installs:
  - `BasicCmd.set_readline_completion_display_matches_hook` (489) → `preloop` (498):
    sets `readline.set_completion_display_matches_hook(self.print_suggestions)` UNLESS
    `'libedit' in readline.__doc__`, in which case it installs the EMPTY hook (496).
    Refactored out (491 docstring) so it can be re-installed after another tool (e.g.
    MadAnalysis5) clobbers the readline hook.
  - `Cmd.preloop` (946) re-installs the same hook (958) under the same libedit guard.
- So the custom categorized display is ACTIVE only on GNU readline; under libedit
  (old macOS) the hook is disabled and completion falls back to flat output.

## `complete(text, state)` (614) — the per-keystroke entry
readline calls this repeatedly with rising `state`; the real work runs only at `state==0`:
- reads `readline.get_line_buffer()`, computes `begidx`/`endidx` adjusted for leading whitespace.
- `;`-split (627): completes only the segment after the last `;` (re-bases begidx/endidx).
- chooses `compfunc`: `begidx==0` → `completenames` (complete the COMMAND); else
  `complete_<cmd>` via getattr, falling back to `completedefault` if absent (634-646).
- **prefix-splitting correction** — readline's word-split breaks on `-`, `=`, `:`, and `\ `;
  the code re-joins so completion works on the *real* token:
  - `\ ` escaped-space (649-656): rebuilds `completion_prefix` ending in `\ `, strips it
    off each match (`p[to_rm:]`).
  - `-` / `=` / `:` (658-669): same idea — `completion_prefix = token up to+including sep`,
    matches are returned with the prefix stripped, so `set gauge=uni<TAB>` completes the
    value not the whole `gauge=uni`.
  - else (670-672): no prefix, `compfunc(text,line,begidx,endidx)` directly.
- **suffix decoration** (674-676): every match gets a trailing space appended UNLESS it
  already ends in ` @ = /`, OR ends in literal `\$` (then the `\$` is stripped, no space) —
  the `\$` convention lets a completer emit a token that should NOT auto-advance.
- returns `self.completion_matches[state]`, `None` past the end (the `__debug__` error log
  at 681-684 is commented out).

## The `@@category@@` sentinel protocol (the non-obvious part)
MG5 groups completions under headers ("Options", "Recognized command", model names, ...).
readline has no native concept of this; MG5 fakes it with a sentinel string:
- `deal_multiple_categories(dico, formatting=True, forceCategory=False)` (502): input is a
  `{category_name: [options...]}` dict. Output is a FLAT list where each category emits a
  marker `opt[0].rstrip()+'@@'+name+'@@'` (531) followed by its (deduped, sorted) options.
  Special cases:
  - `formatting=False` → returns the dict unchanged (caller handles it).
  - libedit (509-514) → no parser available, returns `misc.make_unique` of ALL options flat
    (categories collapse). Matches the disabled display hook above.
  - all categories have ≤1 value and they coincide to a single value (517-520) → returns just
    that one value (no menu).
  - exactly one non-empty category (`valid==1`, 540-541) and not `forceCategory` → drops the
    leading `@@` marker (`out[1:]`), so a single-category result shows no header.
- `print_suggestions(substitution, matches, longest_match_length)` (546, `@debug()`-decorated)
  is the display hook that DECODES the markers: if any match ends in `@@` it walks
  `self.completion_matches`, and for each `...@@category@@` token writes
  `\n <category>:\n===\n`, then lays the following options out in N columns
  (`getTerminalSize()//(longest_match_length+1)`). Without markers it just column-formats.
  Re-prints `self.prompt + readline.get_line_buffer()` afterward (584) so the typed line
  survives the menu dump. CAUTION: `print_suggestions` is `@debug()`-wrapped — per
  optimize-mode-debug-divergence.md the decorator returns the function UNWRAPPED under `-O`,
  so the body still runs (the wrapper is a no-op, not a disable); only its internal
  `if __debug__: logger.error(error)` (587) is silenced in release.
- `getTerminalSize` (590): ioctl `TIOCGWINSZ` on fds 0/1/2, then ctermid, then `$LINES`/
  `$COLUMNS`, hardcoded fallback size (read at 590) → returns column count.

## `path_completion` (724, staticmethod) — file/dir completer
<!-- split_arg @687, list_completion @709 (v3.7.1) -->

- splits `text` into `prefix`/`text`, expands `~`/`$VARS` in `base_dir` (default cwd).
- `only_dirs=True` → only subdirs (each suffixed `os.path.sep`); else files THEN dirs.
- hides dotfiles unless the typed `text` itself starts with `.` (745).
- `relative=True` adds `./` `../` candidates (763-765).
- **escapes spaces**: `a.replace(' ', r'\ ')` (767) — this is the producer side of the `\ `
  prefix-split correction in `complete()`. `list_completion` (709) is the trivial
  `[t for t in list if t.startswith(text)]` helper.

## SmartQuestion / OneLinePathCompletion reuse (the widgets answer-completion)
- `SmartQuestion.completenames(text, line, *ignored)` (2171): FIRST cancels any pending
  SIGALRM (`signal.alarm(0)`) and prints `[timer stopped]` — tab-completing at a question
  STOPS the countdown (couples to ask-question-widgets.md timeout). Then builds
  `{' Options': list_completion(text, self.allow_arg), ' Recognized command': super().completenames(...)}`
  and runs it through `deal_multiple_categories` — so a question's tab menu shows the legal
  answers AND the interface's commands, in two categories, via the SAME sentinel protocol.
  `completedefault = completenames` (2187) — completing an argument behaves the same.
- `OneLinePathCompletion.completenames` (2357) adds path completion (`allowpath=True`).

## Gaps / cautions
- libedit path is hard to exercise in this Linux container (GNU readline only) — the flat-
  fallback behavior is source-grounded but not probe-confirmed here.
- The exact rendered menu (column count, category headers) depends on terminal width and is a
  runtime/display concern — a probe-candidate, not cached as fact.
- `do_open` (madgraph 9098) / `complete_*` per-command completers live in the workhorse
  slices; this page owns the engine, not the individual `complete_<cmd>` bodies.

See also: ask-question-widgets.md (SmartQuestion timeout / `[timer stopped]`),
command-loop-machinery.md (BasicCmd class position, split_arg),
optimize-mode-debug-divergence.md (`@debug()` decorator + `print_suggestions` error log).
