---
description: ALOHA's self.tag list is the single routing channel — one per-routine string list assembled at compute_all/compute_routine that steers propagator flavor (P*), loop path (L*), conjugate flow (C*), and output precision (MP) across BOTH the kernel (create_aloha.py) and the writer (aloha_writers.py).
---

# Tag-routing channel (self.tag)

Generalization over the four ALOHA tag consumers. Cites `$MADGRAPH_INSTALL/aloha/create_aloha.py` and `aloha_writers.py`, v3.7.1 (source-walked).

## The principle
Every ALOHA routine carries ONE `self.tag` list (a list of short strings). This single list is the entire routing surface that selects what a routine *is* — its propagator numerator, its loop vs flat form, its fermion-flow conjugation, and its output precision. The same list object is read by the KERNEL (which symbolic objects to multiply) and is passed verbatim to the WRITER factory (which target/precision to emit). There is no second routing channel: change behavior = change a tag.

This catches more than any single instance page: a NEW tag family (or reasoning about an unfamiliar one) flows the same way — assembled in `compute_all`/`compute_aloha`, read by the kernel branches, then handed to `WriterFactory`. To predict a routine's nature, enumerate its tags.

## Tag assembly (where tags are born)
- `self.tag = []` default (`create_aloha.py:74`, `:140`); `compute_routine(mode, tag=[])` sets `self.tag = tag` (`:162`).
- `compute_aloha` builds the per-routine tag: conjugate tags `['C%s' % i for i in builder.conjg]` (`:1111`), or appended to an existing propagator tag (`:1113-1114`); routine real-name = `name + ''.join(tag)` (`:1120`).
- `custom_propa` block constructs the `P*` variants per particle (`compute_all`, `:912-930`): `P1N` default (hel recycling), `P<propagator.name>` / `P0` (zero-mass), vector `P1L/P1T/P1A` + `P1PS` (massless phase-space gauge), fermion `P1P/P1M`.
- `mp_precision` appends `MP` if absent (`AbstractRoutine.write`, `:102-103`).

## Tag consumption — KERNEL side (create_aloha.py)
- Propagator selection: `propa = [t[1:] for t in self.tag if t.startswith('P')]` (`:313`); branches `['0']`→massless, `[]`/`['1D']`→standard, else `get_custom_propa` (`:314-331`); `1D` BW-cutoff multiplier (`:326-329`, `:380-382`).
- Loop path: `if any(tag.startswith('L') for tag in self.tag if len(tag)>1)` → `compute_loop_coefficient` returning a `SplitCoefficient` (`:418-419`); `l_in` recovered from the `L<n>` tag (`:596`).
- Conjugate flow: `C*` tags drive the per-leg `_conjugate_gap` index shift (`:340`,`:355`,`:390`,`:399`) and the output tag is recomputed C-stripped + re-added (`:251-252`).

## Tag consumption — WRITER side (aloha_writers.py)
- The kernel passes the list straight through: `WriterFactory(self, language, output_dir, self.tag, options)` (`create_aloha.py:93`).
- `WriterFactory.__new__` dispatches on it: `SplitCoefficient` expr → loop writer (`:2569`), `'MP' in tags` → `*QP` writer (`:2571`,`:2576`); plain fortran/python/cpp/gpu otherwise (`:2575-2585`).
- `'MP' in self.tag` toggles quad-precision emission inside the writer (`:538`,`:1143`); `combine_name`/`get_routine_name` strip/encode `MP` into the emitted name (`:1336-1338`).
- `C*` surfaces in the call args: `make_call_list` reads `[2*(int(c[1:])-1) for c in self.tag if c[0]=='C']` and swaps the adjacent leg name (`:412`,`:418-424`).

## Boundary
- This is a STATIC code-flow fact (which code reads `self.tag`), fully source-grounded.
- It does NOT by itself predict a routine's emitted FILENAME or the set of files in `<PROC_DIR>/Source/DHELAS/` for a given model — that is a runtime consequence. `combine_name` may hash long combined names (`aloha_writers.py:1351-1354`), so a tag set does not map 1:1 to a predictable filename. Any "tags X produce routine/file Y" claim is a runtime prediction — mark hypothesis and probe before asserting.
- Gauge/loop-mode also steer behavior via the `aloha.<flag>` GLOBALS, not via `self.tag` (see propagators-and-gauge-flags.md). The tag channel and the global-flag channel are distinct: tags are per-routine, globals are module-wide for the whole `compute_all` pass.

## Instance pages (kept — carry the per-consumer detail)
- high-kernel-algorithm.md — the P*/L* kernel branches in `compute_aloha_high_kernel`.
- build-pipeline.md — `custom_propa` tag construction + C* conjugate-builder setup.
- propagators-and-gauge-flags.md — custom-propagator tag catalogue + the global-flag (non-tag) channel.
- writer-hierarchy.md — MP/SplitCoefficient factory dispatch + C* call-arg swap.
