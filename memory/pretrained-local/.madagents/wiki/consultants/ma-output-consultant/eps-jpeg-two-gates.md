---
description: Output diagram emission has TWO independent gates — EPS matrix*.ps via output_options['noeps'] in generate_subprocess_directory vs the 'nojpeg'-gated raster conversion in finalize (gen_jpeg-pl emits PNG, NOT jpg, despite the name); -nojpeg keeps .ps but skips the png, --noeps=True kills both (MG5_aMC v3.7.1)
---

# Diagram emission: EPS and JPEG are two independent gates

A madevent output writes Feynman-diagram pictures in two stages, each with its own
gate, its own command-line trigger, and its own location in the code. Answering "will
this output have diagrams?" requires checking BOTH. File:
`$MADGRAPH_INSTALL/madgraph/iolibs/export_v4.py`.

## Gate 1 — EPS `matrix*.ps` write (inside generate_subprocess_directory)
The `MultiEpsDiagramDrawer(...).draw()` call that writes the per-P-dir PostScript is guarded by:
```
if not 'noeps' in self.opt['output_options'] or self.opt['output_options']['noeps'] != 'True':
```
at `:2982` (SA), `:3780` (MW), `:4535` (ungrouped ME), `:6359` (MEGroup, the production path).
- Driven by `output_options['noeps']`, a STRING. It equals `'True'` exactly when `--noeps=True`
  was on the output line: `do_output` builds `line_options` by splitting `--k=v` (`madgraph_interface.py:9144-9145`),
  so `--noeps=True` -> `line_options['noeps'] == 'True'`. `line_options` is passed as `cmd_options`
  to `ExportV4Factory`, which sets `opt['output_options'] = cmd_options` (`export_v4.py:9870`); the
  exporter reads `self.opt['output_options']` (`self.cmd_options` at `:200`).
- So the EPS write is suppressed iff `--noeps=True`. **`-nojpeg` does NOT touch this gate** — it
  is not a `--k=v` arg, so it never enters `output_options`.

### Output filename differs by exporter path
- Ungrouped ME / SA / MW: `matrix.ps` (`:4536`, `:2983`, `:3781`).
- **MEGroup (production default)**: `"matrix%d.ps" % (ime+1)` -> `matrix1.ps`, `matrix2.ps`, …
  (`:6360`) — one per matrix element in the group. So a default `output madevent` P-dir carries
  `matrix1.ps`, not `matrix.ps`.

## Gate 2 — raster conversion (inside finalize) — emits PNG, not JPEG
ME finalize (`:4615`) sets `makejpg = 'nojpeg' not in flaglist` (`:4623-4626`), then at `:4699-4709`,
IF `makejpg` AND `misc.which('gs')` (ghostscript present), runs `bin/internal/gen_jpeg-pl` per P-dir
to rasterize the `.ps` files.
- **The output is PNG, not JPEG, despite the `jpeg`/`nojpeg` naming.** `gen_jpeg-pl` calls
  `gs -sDEVICE=pngmono -sOutputFile=matrix$imatrix%00d.png` (probe-read from the copied
  `bin/internal/gen_jpeg-pl`). For `generate u u~ > z`, gate 2 produced `matrix11.png` (= `matrix`
  + imatrix `1` + gs page `1`), NOT `matrix1.jpg`. It also removes/regenerates the per-P-dir
  `card.png`. The flag/var/script names are a historical misnomer; nothing named `.jpg` is written.
- `'nojpeg'` enters flaglist from `do_output`'s `nojpeg` var (`:9735-9736`), which is True for EITHER
  `-nojpeg` OR `--noeps=True` (`:9118-9120`).
- gs absent -> conversion silently skipped even with makejpg True.

## The trigger/effect matrix (probed v3.7.1, `generate u u~ > z`, MEGroup, gs present)
| output line          | `output_options['noeps']` | flaglist has `nojpeg` | `matrix1.ps` | `matrix11.png` |
|----------------------|---------------------------|-----------------------|--------------|----------------|
| (plain)              | absent                    | no                    | written      | written*       |
| `-nojpeg`            | absent                    | yes                   | **written**  | absent         |
| `--noeps=True`       | `'True'`                  | yes                   | **absent**   | absent         |

*png only if `gs` on PATH (the conversion is gs-driven). The raster file is `matrix11.png`
(`matrix` + imatrix=1 + gs-page=1), NOT a `.jpg`.
- Probed plain `output ... -f`: `matrix1.ps` PRESENT, `matrix11.png` PRESENT, `card.png` PRESENT (gs on PATH).
- Probed `output ... -nojpeg -f`: `matrix1.ps` PRESENT, NO `matrix11.png`, NO `card.png`.
- Probed `output ... --noeps=True -f`: NO `matrix1.ps`, NO `matrix11.png`.

So `-nojpeg` is "keep EPS, skip the raster conversion"; `--noeps=True` is the stronger "emit no
diagram pictures at all" (it implies nojpeg AND closes the EPS gate). The two are NOT synonyms.

## Why this catches more than the finalize page
finalize-and-model-conversion.md documents Gate 2 (`nojpeg`->makejpg, gen_jpeg-pl) and lists the
`MultiEpsDiagramDrawer` call sites, but treats EPS/raster as one suppression. It is two: the EPS
write lives in generate_subprocess_directory under `output_options['noeps']` (a string gate, set
only by `--noeps=True`), the raster (PNG) conversion lives in finalize under the `nojpeg` flaglist
(set by either flag). `-nojpeg` leaves the `.ps` on disk; only `--noeps=True` removes it.

## Cautions
- `gen_infohtml`'s `check_postcript` links `matrix<id>.ps` only if it exists; under `--noeps=True`
  the info page's postscript links are absent (no `.ps` written). See gen-infohtml-output-info-page.md.
- The EPS gate string-compares `!= 'True'`; a programmatic caller passing `output_options['noeps']=True`
  (bool) would NOT match `'True'` and would still write EPS. The gate is keyed on the CLI string form.
