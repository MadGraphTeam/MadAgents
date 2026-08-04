---
description: How rivet_card `analysis = [...]` string becomes a Python list BEFORE getAnalysisList — ConfigFile list-coercion via list_parameter registration; edge cases (empty list, space-separated, quotes).
---

# Analysis-list parsing: `[...]` string -> Python list (the step BEFORE getAnalysisList)

`analysis-selection.md` covers `getAnalysisList` — what fires once `self["analysis"]` is a list. This page covers the step UPSTREAM: how the on-disk card string `analysis = [default]` becomes the Python list `["default"]` so that `len(self["analysis"])==1` and `self["analysis"][0]=="default"` (the sentinel test at banner.py:1662-1665). Non-obvious because `RivetCard.read` just does `self[key]=value.strip()` with `value` still the raw bracketed STRING — the list-building is entirely in `ConfigFile.__setitem__`.

## Why `analysis` routes through list-coercion
- `RivetCard.default_setup` (banner.py:1567): `self.add_param('analysis', [], typelist=str)`.
- `add_param` (banner.py:1328-1336): value `[]` is a list; `len(value)==0` so `targettype=typelist` (=str) via the `assert typelist` branch (1331-1333); registers `analysis` in `self.list_parameter` (1336). THIS registration is what makes `__setitem__` take the list branch.

## The coercion (`ConfigFile.__setitem__`, banner.py:1140-1211)
`RivetCard.read` (1610-1618) reaches `self["analysis"] = "[default]"` (the bracketed string; `analysis` is NOT in read's lowercase/blank list at 1612-1614, so the raw string passes through). Then in `__setitem__`:
- 1140: `analysis` in `self.list_parameter` -> list branch, `targettype=str`.
- 1145-1147: strip; if starts `[` and ends `]` -> drop the brackets. `"[default]"` -> `"default"`.
- 1149-1163: regex split on comma OR unescaped whitespace, preserving quoted blocks. `"default"` -> `["default"]`.
- 1172-1173: each element through `format_variable(v, str)` (1413). For str (1456-1460) leading/trailing matching `'…'` or `"…"` quotes are STRIPPED.
- 1211: `dict.__setitem__(self, 'analysis', values)` — the list is stored.

## Edge cases (parse-time reproduced, not a runtime claim)
Reproduced the 1145-1163 split + 1456-1460 quote-strip directly in Python:
| card text | resulting list | len | getAnalysisList branch |
|---|---|---|---|
| `[default]` | `["default"]` | 1 | sentinel (1665) -> curated MC set / Contur |
| `default` (no brackets) | `["default"]` | 1 | sentinel — brackets are OPTIONAL |
| `[  default  ]` | `["default"]` | 1 | sentinel (inner whitespace trimmed) |
| `[]` | `[]` | 0 | **falls to else (1690-1692) -> EMPTY analysis_list -> do_rivet IndexError at 2985 (see point 3)** |
| `[MC_GENERIC, MC_JETS, CMS_2019_I1753680]` | 3 names | 3 | each verbatim (1690-1692) |
| `[MC_JETS MC_MET]` | `["MC_JETS","MC_MET"]` | 2 | split on SPACE too — space-separated works |
| `['MC_JETS']` | `["MC_JETS"]` | 1 | single real name (1687-1688); quotes stripped by format_variable |

KEY non-obvious points:
1. **Brackets are optional and inner whitespace is trimmed** — `default`, `[default]`, `[ default ]` all collapse to the 1-element sentinel.
2. **Separator is comma OR whitespace** — `[MC_JETS MC_MET]` yields TWO analyses, not one mis-parsed token. Easy user surprise.
3. **`analysis = []` (empty) is NOT the sentinel — it CRASHES do_rivet** — len 0 skips the `len==1` sentinel branch (1662) entirely and hits the `else` loop (1690-1692), which iterates over nothing and returns `[]`. The sentinel is specifically a ONE-element `default`/None/"" — an empty list is a DIFFERENT, degenerate case. The empty list does NOT yield a benign "`-a ` with no analysis". With `analysis_list==[]` the `for analysis in analysis_list` loop (common_run_interface.py:2981-2984) never runs, so `run_analysis=""`, and the very next line `run_analysis = run_analysis.split(",", 1)[1]` (2985) does `"".split(",",1)[1]` -> **IndexError: list index out of range**. do_rivet raises THERE, before any `$CONTUR_` check, weight-name, env, HepMC fetch, or wrapper emission. This is pure control flow (reachable without a Rivet install): verified by reproducing `"".split(",",1)[1]` in Python. So `analysis = []` is a hard crash, not a silent empty run.
4. Quote-stripping is in `format_variable` (1456-1460), NOT the split — the regex split alone preserves quotes; the per-element format pass removes them.

## Boundary
- This is the STRING->list parse. What the resulting list MEANS (sentinel -> MC_* set, Contur beam gating, multi-element verbatim) is `analysis-selection.md`.
- The `ConfigFile.__setitem__`/`add_param`/`format_variable` machinery is generic banner.py infrastructure shared by all cards; cited here only as it governs the `analysis` typelist=str param.
