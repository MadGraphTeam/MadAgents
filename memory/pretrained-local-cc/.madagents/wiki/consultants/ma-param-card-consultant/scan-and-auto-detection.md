---
description: How scan parameters and Auto widths are detected in the card-read path — ParamCardIterator, the scan/Auto regexes, scan iteration semantics (eval'd lists, numbered-id lockstep vs bare-scan cartesian product), the both-cards-scanned precedence (param wins, no cross-card error = myth), and the scan output artefacts (summary table + per-run params.dat + per-point Auto-width capture).
---

# Scan & Auto detection in the card-read path

Detection lives in `static_check_param_card` in `$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py` L3740. (Width COMPUTATION and small-width TREATMENT are out of slice — madwidth / bw-window. This page covers only how the card-read path detects and dispatches them.)

## Two regexes — L3742-3743
- Scan: `^(decay)?[\s\d]*scan` (re.I+re.M) — matches any line whose value field starts `scan` (incl. a decay line).
- Auto width: `decay\s+(\+?\-?\d+)\s+auto(@NLO|)` (re.I) — captures pid and optional `@NLO` suffix.

## Scan dispatch — L3746-3755
If the scan regex hits:
- Web mode (`not CmdShell`) → raises `Scan are not allowed in web mode` (L3748-3749).
- Else: build `ParamCardIterator(text)` (L3751), store on `interface.param_card_iterator`, take the first card via `.next(autostart=True)`, **overwrite `path` with that first card** (L3754), recurse with `dependent=True`.

## Auto-width dispatch — L3757-3772
If the auto regex hits and `run=True`: collects pids, builds `compute_widths` line (`--nlo` if any `@NLO`), calls `static_compute_widths` (L3767). If `run=False`: just logs that widths are on Auto and will be computed after card editing.

## `ParamCardIterator(ParamCard)` — check_param_card.py L931
- `iterate()` L968 is the generator. Scan-value syntax parsed by `scan\s*(?P<id>\d*)\s*:\s*(?P<value>[^#]*)` (L971). `re.findall` returns the id as a **string** (`'1'`, `'2'`, …), used verbatim as the `all_iterators` dict key.
- A `scan:` with no id (`key==''`) gets a synthetic key `-1 * len(all_iterators)` (L982-983) → ints 0, -1, -2, … each **unique** → its own independent product axis. A numbered `scanN:` groups parameters sharing the SAME string id so they advance **in lockstep / same index** (L984-987; assignment L1006-1014 loops all params in the group and assigns `values[pos]` at the shared `pos`). Note the string-vs-int key domains never collide (bare→int, numbered→str), so `scan0:` and bare `scan:` are distinct axes.
- Value list is `eval`'d Python (L987) — ANY expression that evals to something indexable: `scan:[100,200,300]`, `scan:range(100,300,50)`, list comprehensions. Only a `SyntaxError` is caught → re-raised with the offending entry (a NameError/other from eval propagates uncaught).

## Correlated (lockstep) vs independent (product) — the load-bearing rule
- Two params both tagged `scan1:` → grouped under key `'1'` → **lockstep**: axis length = length of the group's FIRST value list only (L999 `all_iterators[key][0][1]`); every param in the group is assigned its own list's element at the shared index (L1008-1010). Unequal list lengths in a group are NOT validated — a shorter list would `IndexError` at the far end, a longer one is silently truncated to the first list's length.
- `scan1:` and `scan2:` (different ids) → different keys → independent **product** axes (L1002 `itertools.product`).
- Bare `scan:` everywhere → every param its own synthetic key → full cartesian product (each param an independent dimension).

## Both cards scanned simultaneously → NO error; param scan wins (claim-4 myth)
The claim "MG5 raises an error if `scan:` is present in both param_card and run_card" is a **doc myth** — no such cross-card guard exists. Mechanism (orchestration is ma-launch's `scanparamcardhandling` decorator, common_run_interface.py L7843; the param-detection half that gates it is mine):
- L7971 `check_card(obj)(...)` = `static_check_param_card` runs FIRST on the param_card and sets `obj.param_card_iterator` iff a param scan is detected.
- L7978 the run_card-scan branch (`if run_card_scan: scan_over_run_card(...)`, L7980-7982) is entered only `if not param_card_iterator`.
- So when BOTH cards carry `scan:`, the param_card_iterator is truthy → run_card branch is unreachable → the run_card scan is silently ignored and the param scan runs. `static_check_param_card` reads only the param_card, so it can raise no both-cards error. (Owner of the precedence/orchestration = ma-launch-consultant; the param-detection that pre-empts the run branch is the mechanism I own.) Downstream, the run_card's literal `scan:` value is left in place and would only surface if the run_card parser later chokes on it — not an intentional guard.
- Cartesian product over all grouped axes via `itertools.product` (L1002); `total` = product of axis lengths (L1001). Each iteration assigns values into a single shared `param_card` copy (L993) and yields it (L1018).
- `Auto` widths inside a scan card are collected separately into `self.autowidth` (L990-991) — resolved per scan point.
- `store_entry` L1021 / `write_summary` L1040 accumulate the cross-section per scan point for the scan summary table; `get_next_name` L1109 generates run names.

## Scan output artefacts — `store_entry` (L1021) + `write_summary` (L1040)
After each scan point integrates, the framework records results onto the iterator and emits two
artefacts. Source-described (the write calls are code-certain; exact on-disk layout not probed):
- `store_entry(run_name, cross, ...)` L1021 appends a dict `{'bench': self.itertag, 'run_name': ...,
  'cross(pb)': ...}` to `self.cross` (L1027-1032). **The resolved `Auto` width for this scan point is
  recorded too**: if `self.autowidth` is non-empty and a card path is given, it reloads that point's card
  and stores `width#<pid>` = `paramcard.get_value(block, lhacode)` (L1034-1037). So a scan over a
  parameter that also has `decay <pid> auto` captures the per-point computed width into the summary —
  the only place the scan ties the madwidth-computed value back to the scan table.
- `write_summary(path, ...)` L1040 writes the scan summary table (`scan_<name>.txt`-style): a header row
  of `run_name` + `self.param_order` (the scanned `block#lhacode` tags, built L997) + sorted result keys
  (`cross(pb)`/`error(pb)`/`width#*` pushed last, L1051-1063), then one `%-Ne`-formatted line per point
  (L1090-1099). `nbcol=20` column width default.
- **Per-run `params.dat` side-file (L1100-1103):** for every point it ALSO opens
  `<events_dir>/<run_name>/params.dat` and writes `<fortran_var> = <value>` lines — one per scanned
  param, mapping the scan value to its **ident-card Fortran variable name** (the `mdl_`-stripped var from
  `Cards/ident_card.dat`, parsed L1073-1082 into the `ident` dict keyed `block#pid`). This is a distinct
  artefact from the operative card: a flat Fortran-name→value file per scan run, not SLHA. `nbcol`/format
  does not apply — it is plain `name = value`.
- `get_next_name(run_name)` L1109 auto-increments the run-name suffix (`<name>_<NN>` → `+1`, else
  `<name>_scan_02`) so successive scan points get distinct run directories.

## Scan restore — the original card IS auto-restored (corrects a prior caution)
The framework restores the original `scan:` card after the scan completes, via a context manager.
`common_run_interface.py` L7892 `restore_iterator`: `__exit__` calls `self.iterator.write(self.path)`
(L7901-7902); the `with restore_iterator(param_card_iterator, card_path)` block (L7988) wraps the
whole scan loop, so on completion **or crash** the original card is written back over
`Cards/param_card.dat`. The iterator object is the ORIGINAL `ParamCardIterator(text)` (still holding
the unexpanded `scan:` lines) — `iterate()` mutates a *separate* `ParamCard(self)` copy (L993), never
the iterator itself, and `ParamCardIterator` inherits `ParamCard.write` with no override (L931). So
after a normal scan the operative card holds the original `scan:` syntax again, NOT the last point.
(Same pattern for run-card scans: `scan_over_run_card` L7904, `restore_iterator(orig_card, ...)` L7917.)

## Cautions
- Scan detection mutates the operative card on disk *during* the run: the first scan point is written
  over `Cards/param_card.dat` before integration (L3754), and each subsequent point overwrites it
  (`store_entry`/the loop body) — but the original is restored at the end by `restore_iterator` (above).
  A scan that is killed mid-loop without unwinding the `with` (e.g. SIGKILL) leaves the last-written
  point on disk; a clean exit or exception restores the original.
- The scan value list is `eval`'d — arbitrary Python; this is why scans are forbidden in web mode.
- Grouped scans (same integer id) require equal-length value lists implicitly; only `all_iterators[key][0][1]` length drives the axis (L999) — mismatched lengths in a group are not validated here.
