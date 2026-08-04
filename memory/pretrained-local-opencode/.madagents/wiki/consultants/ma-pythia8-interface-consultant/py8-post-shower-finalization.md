---
description: do_pythia8 post-shower finalization — djr/pts renaming, merging plots, merged_xsecs.txt, banner MGGenerationInfo injection, deferred HepMC store_result consumption (compress/remove/move queue) + the hepmc@<dir> UnboundLocalError hazard, and the version-consistency warning mechanism.
---

# PY8 post-shower finalization + deferred HepMC store + version-consistency warning

The handoff's *tail end*: after PY8 finishes, before `do_pythia8` returns, MG renames PY8's
raw output files, generates merging plots, writes a merged-xsec table, injects the matched
xsec into the banner, and *queues* the HepMC compress/move/remove for later. The actual HepMC
file ops happen in a **separate** `store_result()` call, not in `do_pythia8`. All citations
`madevent_interface.py` v3.7.1 unless noted.

## DJR / pts output renaming (`:5145-5153`)
PY8 writes bare `Events/<run>/djrs.dat` and `pts.dat`. do_pythia8 renames them to
`<tag>_djrs.dat` / `<tag>_pts.dat` (shutil.move, only if present). This is the source for the
`<tag>_djrs.dat` filename that py8-result-extraction.md's DJR parse consumes — pinned here.

## Merging plots (`:5160-5163`)
`create_plot('Pythia8')` produces the DJR merging plots; failure => `logger.warning('Failed to
produce Pythia8 merging plots.')` (non-fatal, continues). Runs after the success check, before
the merged-xsec block.

## merged_xsecs.txt table (`:5235-5246`, inside the merged block)
Writes `Events/<run>/<tag>_merged_xsecs.txt`: a 3-col table (Merging scale / Cross-section [pb] /
MC uncertainty [pb]) over all `cross_sections` keys from the DJR. If the DJR yielded nothing
(`cross_sections` empty) it instead writes the literal line "Cross-sections could not be read from
the XML node 'xsection' of the .dat file produced by Pythia8." — so an empty-but-present
merged_xsecs.txt is the on-disk signature of a DJR-read failure.

## Banner update + matched-xsec injection (`:5248-5260`)
- `self.banner.add(pythia_cmd_card)` (`:5251`) — the full PY8 command card is appended to the banner.
- **if `int(run_card['ickkw'])`** (`:5253`, i.e. ANY nonzero ickkw — MLM at LO is 1): injects
  `'#  Matched Integrated weight (pb)  :  <cross_pythia>\n'` into `MGGenerationInfo` (create or
  append, `:5255-5258`). NB this reads `self.results.current['cross_pythia']` (the inclusive
  showered xsec from the log), NOT `cross_pythia8` (the DJR central-scale value). So the banner's
  "Matched Integrated weight" is the log-derived number. On the use_syst+old-interface path
  `cross_pythia` was overwritten to -1 (py8-result-extraction.md CAUTION) — the banner then
  records -1 as the matched weight.
- Banner written to `<run>_<tag>_banner.txt` (`:5259-5260`).
- Then `print_results_in_shell` (`:5265`) and, if `delphes_path` set, `delphes --no_default`
  (`:5263-5264`) — the in-do_pythia8 Delphes chaining (distinct from the generate_events chain).

## Deferred HepMC ops: queued in setup, consumed in store_result
The HepMC compress/move/remove are NOT done in do_pythia8 — they are appended to `self.to_store`
during `setup_Pythia8RunAndCard` and executed later in `store_result()` (`:5783`). This is a
queue/consume split across two methods.

### Queue side (`setup_Pythia8RunAndCard:4334-4359`)
For a `hepmc...@<path>` value (`len(hepmc_specs)>1`, `:4334`): two sub-branches by whether the
custom path is absolute.
- **absolute path** (`:4335-4338`): guarded by `if os.path.exists(hepmc_specs[1])` (`:4336`) — the
  *parent* custom dir must already exist; then `os.mkdir(<path>/<run_name>)` (`:4337`) **then**
  append `"moveHEPMC@<path>/<run_name>"` (`:4338`). If the parent doesn't exist: warning + fall
  back to default path, no move queued (`:4339-4340`).
- **relative path** (`:4341-4343`, the `else`): append `"moveHEPMC@.../Events/<rel>/<run_name>"`
  (`:4342`) **then** `os.mkdir(.../Events/<rel>/<run_name>)` (`:4343`) — NO existence check at all
  on parent or subdir (note the append/mkdir order is reversed vs the abs branch).

`.gz` suffix => append `'compressHEPMC'` (`:4346-4348`); absent => *remove* any
queued compressHEPMC (`:4349-4351`). `remove` suffix => append `'removeHEPMC'` (`:4354-4356`);
absent => remove it (`:4357-4359`).

### Consume side (`store_result:5813-5836`)
`if 'pythia8' in self.to_store` (queued at `:5165`):
- `file_path = Events/<run>/<tag>_pythia8_events.hepmc`.
- if `removeHEPMC` in to_store => `os.remove(file_path)` (`:5820-5821`) — the Delphes/no-keep case.
- else: if `compressHEPMC` => `misc.gzip(file_path, stdout=file_path)`, set `hepmc_fileformat='.gz'`
  (`:5824-5826`); then if a `moveHEPMC@<dir>` is queued, `os.system("mv " + file_path +
  hepmc_fileformat + " " + move_hepmc_path)` (`:5828-5835`).
- The legacy Pythia6 leg of store_result (`:5804-5811`) gzips `pythia_events.hep` ->
  `<tag>_pythia_events.hep` — StdHEP, no HepMC machinery (consistent with do-pythia6 page).

`store_result()` is called from the generate_events chain (`:2671`), do_pythia6 (`:5657`), the LO
shower path (`:5738`), and the run-config flow (`:6421`).

## CAUTION: `hepmc@<dir>` (uncompressed custom path) => UnboundLocalError
`grep hepmc_fileformat` over madevent_interface.py returns exactly TWO lines: assignment at `:5826`
(inside `if 'compressHEPMC' in self.to_store`) and read at `:5835` (`os.system("mv "+file_path+
hepmc_fileformat+...)`). It is a bare local — not `self.`, not a module global, no default — so when
the assignment branch is skipped the read is an unbound local. A user setting
`HEPMCoutput:file = hepmc@<dir>` (custom path WITHOUT `.gz`) queues `moveHEPMC@` (`:4338`/`:4342`)
but NOT `compressHEPMC` (`:4346` endswith('.gz') is false), and not removeHEPMC. In store_result the
`os.path.isfile(file_path)` guard (`:5819`) is True (the .hepmc exists after a good shower) and
`removeHEPMC` absent (`:5820`), so control reaches the move with `compressHEPMC` absent =>
`hepmc_fileformat` never assigned => `:5835` raises **`UnboundLocalError`** (source-traceable by
variable scoping; full LHE->PY8->store path not yet probe-confirmed — expensive probe candidate).
The safe custom-path form is `hepmc.gz@<dir>` (compresses first, sets `.gz`). A bare `hepmc.gz`
(no `@`) or bare `hepmc` (no `@`, no move) is unaffected (move branch not entered).

## CAUTION: re-run with same custom HepMC path => FileExistsError
Both branches `os.mkdir(<path>/<run_name>)` on the run-named subdir without checking *that subdir's*
existence: abs branch `:4337` (only the *parent* is checked, `:4336`), rel branch `:4343` (no check
at all). Re-launching the same run_name into the same custom `@<dir>` => `FileExistsError` on the
run-named subdir (source-visible; expensive probe candidate). Precondition: same explicit run_name
into same custom dir — MadEvent's default run-name incrementing avoids it unless the name is reused.

## Version-consistency warning mechanism (`mg5amc_py8_interface_consistency_warning`, `:4236-4305`)
Static method; my other pages reference it but here is the mechanism. Only meaningful when a
PY8 path is set (`:4241` returns None otherwise). Two-stage:
1. `mg5amc_py8_interface_path` unset but `pythia8_path` set => returns the "PY8 cannot be used for
   LO with MadEvent; install mg5amc_py8_interface" warning string (`:4244-4252`).
2. Reads `MG5AMC_VERSION_ON_INSTALL` + `PYTHIA8_VERSION_ON_INSTALL` files from the interface dir
   (`:4263-4270`; `'UNSPECIFIED'` => None). Current PY8 version via shelling out
   `./get_pythia8_version.py <py8_path>` in the interface dir and `float()`-casting the output
   (`:4272-4283`; any exception => None). Returns a "version differs, refresh the interface"
   warning string if either on-install version != current (`:4285-4303`), else None.

Caller: do_pythia8 invokes this only on the `--old_interface` path (`:4646`); the returned string
(if any) is logged as a warning. On the default main164 path it is not called — so a stale
interface install is silently fine when steering via main164.

## Boundary
In slice: the MG-side finalization control flow, file renaming/queuing, banner injection, the
version-check mechanism. Out of slice: what PY8 wrote into djrs.dat/the HepMC physics, and PY8's
own version semantics.
