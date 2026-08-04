---
description: hepmc_parser.py — HepMC2 IO_GenEvent ASCII parsing (E/V/P/N/U/C/H/F lines), EventFile gz handling, event/vertex/particle classes. v3.7.1.
---

# HepMC parser — hepmc_parser.py (v3.7.1)

File: `$MADGRAPH_INSTALL/madgraph/various/hepmc_parser.py` (426 lines). Parses **HepMC2 IO_GenEvent ASCII** format (the text format Pythia8 writes via MG). This slice owns the *parsing only* — analysis on top is downstream-tool territory.

## Format / line types
Event listing bracketed by `HepMC::IO_GenEvent-START_EVENT_LISTING` / `...-END_EVENT_LISTING`. Header (everything before START) stored as `self.header`. Line first-char dispatch (HEPMC_Event.parse, 189):
- `E` (215): event header — `event_id nb_interaction scale alphas alphaew process_id barcode_vertex nb_vertex barcode_beam1 barcode_beam2 nb_random_state <randoms...> nb_weight <weights...>`. `wgt` property = `weights[0]` (177).
- `V` (120): vertex — `barcode id x y z ctau nb_orphan nb_outgoing nb_weight <weights...>`. Sets `event.curr_vertex`.
- `P` (62): particle — `barcode pdg px py pz E mass status pol_theta pol_phi vertex_barcode nb_flow_list <flow pairs...>`. On parse, added as outgoing to `event.curr_vertex` (83).
- `N/U/C/H/F` (235-245): stored verbatim as strings, not parsed (N=weight names, U=units, etc.).
- Incoming particles wired up post-parse via `vertex_barcode` (206-213); `vertex_barcode==0` skipped.

## HEPMC_EventFile (260)
- Open: handles `.gz` (gzip.GzipFile, `zip_mode=True`) and falls back to the non-gz path if a `.gz` request finds only the plain file (273-275). On gz failure can gunzip then reopen.
- On read-open, consumes header up to START_EVENT_LISTING (296-305).
- `next_event` (362): accumulates lines until next `E` line (which becomes `start_event` for the following call) or END marker; returns `HEPMC_Event(text)`.
- `__len__` (330): full pass counting events (caches in `self.len`); sets `parsing=False` during count.
- `__iter__`/`next`/`__next__` standard; `tell`/`seek`/`getfilesize` handle gz peculiarities (gz tell falls back to `self.size`; getfilesize reads gz trailer ISIZE via struct).
- `write` (400) encodes for gz/binary modes; supports `to_zip` re-zip on close.

## Cautions / known quirks (source-visible)
- `HEPMC_Particle.helicity` is **hardcoded to 9** (unknown, 58-60) — the parser does not read true helicity from HepMC2.
- `HEPMC_Vertex.id` and particle `vertex_barcode` are parsed as **float** (125, 77) despite being integer barcodes — comparisons rely on float equality.
- `__main__` block (417) references a hardcoded macOS path and uses `self.comment` which is never initialized in `HEPMC_Event.__init__` (line 204 appends to `self.comment` → AttributeError on any unrecognized line). The comment attribute is a latent bug for non-standard lines.
- HepMC **3** (the newer format) is not handled here — this is HepMC2 only.
