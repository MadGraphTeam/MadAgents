---
description: FKSHelas* objects and the async_generate_real/born/finalize hooks driven by ncores_for_proc_gen; serial vs parallel ME generation paths.
---

# FKS Helas ME generation (serial and async)

`fks_helas_objects.py` turns the FKSMultiProcess (amplitudes) into Helas matrix
elements. `FKSHelasMultiProcess.__init__` (`:255`) branches on
`fksmulti['ncores_for_proc_gen']`.

**Logger silencing during generation:** `__init__` raises `madgraph.diagram_generation`
and `madgraph.helas_objects` to WARNING for the whole build (`:258-263`), restoring
their levels at the end (`:485-486`). So during FKS ME generation those two modules'
INFO/DEBUG records are suppressed — only the FKS driver's own INFO (the "Processing/
Reusing color information for …", "Generating real …", "Collecting infos …", "Done")
appears. If you expect diagram-generation INFO during NLO ME building and see none,
this is why (it is NOT a sign nothing ran).

## Serial path (ncores == 0, fks_helas_objects.py:274-288)
- Generates real MEs via `generate_matrix_elements(combine_matrix_elements=False)`
  if `real_amplitudes` present, else empty list.
- `generate_matrix_elements_fks` (`:564`) builds the born/virtual FKSHelasProcesses.
- `initial_states=[]`; `has_loops` = any virtual MEs.

## Serial combination engine — generate_matrix_elements_fks (:564-664)
This is the serial-mode analogue of `async_finalize_matrix_elements` (combination)
+ the color-recycling the async path does per-worker. Per born `FKSProcess`:
- Builds ONE `FKSHelasProcess(proc, self['real_matrix_elements'], [diagram-bearing
  real_amplitudes], gen_color=False)` (`:595-600`). Note reals are pre-filtered to
  `amp['diagrams']` before being handed in.
- `matrix_elements.index(matrix_element)` (FKSHelasProcess.`__eq__`, up to color
  links) — **found** → `other.add_process(matrix_element)` (`:660`, the 1-to-1
  real merge on born/virtual/real pdg lists, see add_process section). **Not
  found** (ValueError) → append the ME **only if** `born_me.get('processes') and
  born_me.get('diagrams')` (`:615-617`). A born with no diagrams is silently
  dropped here — a SIXTH config-shrink site beyond the five on
  silent-real-config-drops.md, at the born (not real) level, no log.
- **Color recycling** (`:622-656`): builds the colorize dict-list of the born ME;
  `list_colorize.index(colorize_obj)` reuses an existing `ColorBasis`/`ColorMatrix`
  (INFO "Reusing existing color information for …") else builds fresh (INFO
  "Processing color information for …"). So the INFO color logs come from THIS
  serial driver, keyed on born color structure, not on the full FKS process.
- After the loop, `set_color_links()` on every kept ME (`:662-663`).

## FKSHelasProcess.__init__ real loops (:684-764)
Two real-combination loops select on `fksproc.ncores_for_proc_gen`:
- **async mode** (`:703-715`): zips `real_me_list` with `fksproc.real_amps`.
- **old mode** (`:716-729`): iterates `fksproc.real_amps`, generating each
  `FKSHelasRealProcess` from the (real_me_list, real_amp_list) pair, but only for
  reals whose `amplitude['diagrams']` is non-empty (`:719`).
Both loops dedup within the born via `self.real_processes.index(fksreal_me)`
(FKSHelasRealProcess.`__eq__`) — a match **extends** the existing real's
`matrix_element['processes']` (`:709-710,723-724`) rather than appending; a miss
appends only if the real ME has processes AND diagrams (`:712-714,726-728`).
- **Side effect** (`:731`): `fksproc.real_amps = real_amps_new` — the FKSProcess's
  real_amps list is REWRITTEN to only the reals that survived (had diagrams and
  weren't merged away). Mutates the upstream FKSProcess.
- Also builds `extra_cnt_me_list` from `fksproc.extra_cnt_amp_list` (`:699-700`),
  the virtual `LoopHelasMatrixElement` if `fksproc.virt_amp` (`:732-735`), and the
  per-amp `sudakov_matrix_elements` dict list (`:739-749`, one HelasMatrixElement
  per sudakov amp, keys copied except `'amplitude'`).

## Sizing for the exporter — max_configs / max_particles
The NLO Fortran exporter needs the max diagram-config count and max external-leg
count across the whole multiprocess (`nexternal.inc`, configs sizing). Stored as
dict keys `max_configs`/`max_particles`, both init to **-1** (`:271-272`).
- **Serial / lazy getters** (`get_max_configs` `:528-540`, `get_max_particles`
  `:543-550`): computed on first call when still < 0. `get_max_configs` =
  `max( max(real ME get_num_configs), max(born_me get_num_configs) )` — the real
  max is wrapped in try/except (ValueError / PhysicsObjectError → skip reals, fall
  back to borns). `get_max_particles` = max born `get_nexternal_ninitial()[0]`.
- **Async / eager set** (`:471-477`): `max_configs`/`max_particles` are set
  directly from the worker returns — `meout[1]` (real `get_num_configs`) and
  `meout[2]` (real nexternal) from `async_generate_real`; the lists were
  pre-seeded with born infos after `async_generate_born` (comment `:468-470`).
- **Asymmetry:** the async path takes max over reals only (born configs already
  folded into `configs_list`), whereas the serial getter explicitly takes
  `max(reals, borns)`. Same final value in practice, but the serial getter is the
  one to read for "where does the exporter's config bound come from".

## Async path (ncores != 0, fks_helas_objects.py:290+)
Three module-level worker functions (picklable, run in a pool):

- `async_generate_real(args)` (`:52`): generates the real amplitude; if no
  diagrams returns `[]` (debug log). Builds the real HelasMatrixElement, processes
  color, pickles `[amplitude, helasreal]` to a temp file. Returns
  `[tmpfile, num_configs, nexternal]`.
- `async_generate_born(args)` (`:98`): reloads real data from temp files (drops
  reals whose pdgs were removed), calls `born.link_born_reals()` and
  `find_fks_j_from_i`. Generates the VIRTUAL here (`:138-151`) when
  NLO_mode=='all' and OLP=='MadLoop' (LoopAmplitude, InvalidCmd→no loops). Builds
  the FKSHelasProcess, pickles it. Returns
  `[tmpfile, metag, has_loops, processes, num_configs, nexternal]`.
- `async_finalize_matrix_elements(args)` (`:173`): reloads a born ME, sets uid,
  builds the color basis + color matrix, then compares against the duplist of
  full MEs (born/real/virtual). `add_process` if equal, else `cannot_combine`.
  Calls `set_color_links()`. Collects initial_states. Returns
  `[tmpfile, initial_states, used_lorentz, used_couplings, has_virtual, cannot_combine]`.

The metag from async_generate_born identifies candidate-equal borns; finalize does
the full-ME equality and color-link insertion.

## Parent-side two-stage combination + retry loop (fks_helas_objects.py:371-422)
The async ME combination is **two-stage**, unlike the serial path which does the
full `__eq__` in one shot:
- **Stage A — cheap candidate grouping (parent, `:380-396`):** the parent's
  `while bornmapout` loop groups born outputs by `metag == metag2` only (the
  `IdentifyMETag` from `async_generate_born`, `:389`). The FIRST born with a given
  metag becomes the `unique_me_list` representative; the rest go into that rep's
  `duplicate_me_lists`. This is purely the born topology pre-filter — no real/
  virtual comparison yet.
- **Stage B — authoritative full compare (worker, `async_finalize_matrix_elements`
  `:202-212`):** finalize reloads the rep ME, then for each member of its duplist
  does the FULL `otherme == me` (`:209`, born metag + virtual metag + real multiset,
  the whole `FKSHelasProcess.__eq__`). Comment `:206-208`: "before entering this
  function, only the born processes were compared. Now compare the full ME
  (born/real/virtual)." A member that passes → `me.add_process(otherme)` (`:210`); a
  member that FAILS → `cannot_combine.append(othermefile)` (`:212`), returned to the
  parent as `meout[5]` (`:235`).
- **Retry loop (`:415-420`):** the parent removes only the temp files NOT in
  `not_combined`; borns in `not_combined` stay in `bornmapout`, so the
  `while bornmapout` loop **iterates again**, re-grouping the leftovers into fresh
  unique-me/duplist sets. So a metag COLLISION that is not a true full-ME match is
  reprocessed — eventually becoming its own ME. metag is a *candidate* (cheap, can
  false-positive); the full `__eq__` is the *authority*.
- The pool is a `fork` context, `maxtasksperchild=1` (`:319-323`); worker
  `sys.path` is augmented with the model paths via `misc.TMP_variable` (`:332-334`).
  uid = position in the unique-me list (`async_finalize`, `:184`).

So the serial path's single `matrix_elements.index(matrix_element)` (one
`__eq__` that internally computes the metag, `:854-856`) is split, in async mode,
into a parent-side metag pre-filter + a worker-side full `__eq__` with a retry
loop. Both paths key the topology match on the SAME `IdentifyMETag`.

## FKSHelasProcess equality (fks_helas_objects.py:850)
`__eq__` is "up to color links". Compares born IdentifyMETag, then reals/virtuals.
**EW Sudakov: if `self.ewsudakov`, never combine** (`:859-863`) — quoted as "not
100% ideal … safest option". The short-circuit is NOT silent: it emits
`logger.warning('With --ewsudakov, matrix elements will not be combined')` (`:862`)
on every comparison before `return False`. So ewsudakov runs produce more
(uncombined) MEs and a stream of this warning. (Minor: both `IdentifyMETag`s are
computed at `:854-857` BEFORE the ewsudakov short-circuit, so they are computed and
discarded under ewsudakov — the inefficiency the comment acknowledges.)
**Compare order/shape (`:854-892`):** born metag → (if both have virtuals) virtual
metag → reals. The real compare (`:881-892`) is a **symmetric multiset** test: copy
other's `real_processes`, `.remove(real)` (FKSHelasRealProcess.`__eq__`) each of
self's reals, then require the remainder EMPTY — so the two borns must have the SAME
COUNT of reals AND each self-real must match one of other's (not a subset/superset).
A real-count mismatch alone makes the borns unequal.

## add_process — the actual ME combination (fks_helas_objects.py:900-938)
When two FKSHelasProcesses are `==` (up to color links), `add_process` folds
`other` into `self`:
- **Born** (`:907-913`): appends each of other's born processes whose pdg list is
  not already present. Identity is the **leg-id list**, NOT the process object —
  comment `:906` notes this keeps MIRROR processes distinct (mirrored initial
  states have the same ME but different pdg order).
- **Virtual** (`:916-918`): extends the virtual ME's process list only if both
  sides have a virtual ME.
- **Real** (`:920-937`): for each of other's real_processes, finds the matching
  self real via `self.real_processes.index(oth_real)` (FKSHelasRealProcess
  `__eq__`); a missing match RAISES `FKSProcessError('add_process: error in
  combination of real MEs')`. Then merges that real's process pdg lists the same
  way as borns. So combination assumes a **1-to-1 real correspondence** between
  the two equal borns.

This is the merge that `async_finalize_matrix_elements` (or the serial
`combine_matrix_elements`) performs after `__eq__` declares two borns equal; the
1-to-1 real requirement is why ewsudakov's "never combine" (`__eq__` short-circuit)
sidesteps it entirely.

## get_fks_info_list (fks_helas_objects.py:781)
Flattens reals into `{n_me, pdgs, fks_info}` records — the per-config info the
NLO exporter consumes. `n_me` = `n+1` (1-indexed position in `real_processes`);
`pdgs` come from `real.matrix_element.get_base_amplitude()['process']['legs']`,
NOT from `FKSRealProcess.pdgs`.

## Lorentz/coupling/process/nexternal aggregation (and the extra_cnt OMISSION)
The exporter pulls used-Lorentz/couplings/processes/sizing through these accessors;
two non-obvious facts:
- **`FKSHelasProcess.get_used_lorentz`/`get_used_couplings` (`:814-838`)** aggregate
  born + reals + virtual + **sudakov** MEs — but NOT the `extra_cnt_me_list`. The
  extra-cnt ME is built with `gen_color=True` (`:700`) yet its Lorentz/couplings are
  reached only indirectly (via the reals it shares). A code-visible omission: don't
  assume extra-cnt structures are independently registered here.
- **Per-process vs multiprocess coupling shape asymmetry:** `FKSHelasProcess.
  get_used_couplings` (`:827-839`) keeps the list-of-lists shape (extends with
  `[c for c in real.matrix_element.get_used_couplings()]`, each element a list),
  whereas `FKSHelasMultiProcess.get_used_couplings` (`:502-512`) **flattens**
  (`[c for l in me.get_used_couplings() for c in l]`, `:509`). The async aggregation at the
  multiprocess level (`:475-477`) flattens identically. So the multiprocess returns
  scalar coupling names; the per-process returns lists. **Probe-verified (v3.7.1,
  `u u~ > u u~ [QCD]`):** per-process `get_used_couplings` elements are `list`;
  multiprocess elements are `str`. Same probe: `multiproc.get_processes()` returned
  1 (born-only) and `me0.get_nexternal_ninitial()` = `(5,2)` (the real-emission
  count: born has 4 externals, accessor reports born+1).
- **`FKSHelasMultiProcess.get_processes` (`:515-525`)** extends only with
  `me.born_me.get('processes')` (`:522`) — the **born** process list, NOT reals/virtuals.
  So `multiproc['processes']` is the born-process set.
- **`FKSHelasProcess.get_nexternal_ninitial` (`:840-848`)** returns the FIRST real's
  nexternal if reals exist; otherwise the **born nexternal + 1** (`:846-847`) — it
  reports the real-emission external count even with zero reals. `get_max_particles`
  (multiproc `:543-550`) takes the max of this across MEs → the real-emission leg
  count, correctly sizing `nexternal.inc`.

## Cautions
- Async path computes virtuals inside `async_generate_born`, bypassing
  `FKSMultiProcess.generate_virtuals`. Two code paths to keep in sync mentally.
- Temp files (NamedTemporaryFile delete=False) are left for the parent to read;
  the return values carry only filenames + small objects.
- ewsudakov disabling of ME combination inflates subprocess count vs the same
  process without sudakov mode.
