---
description: The task needs a tool or PDF set that may not be present here, or asks how to install or configure the stack.
---

# Installation & environment-setup fan-out

## When it applies
Any "how do I install / set up / configure MG5 or its tool chain" input: `install <tool>` commands, prerequisites, the install directory tree, `mg5_configuration.txt` keys, why an optional tool (Pythia8/Delphes/MA5/LHAPDF) is or isn't available, PDF-set selection, and the install smoke-test / verification launch. A single such question usually spans several of the owners below — fan out, don't answer from one.

## Owner map (route each sub-question to its slice)
- **Install commands** (`install pythia8|Delphes|MadAnalysis5|lhapdf6`), prerequisites (Python/`six`/compilers), install-target directory, the install directory tree → **ma-installation-consultant**.
- **`mg5_configuration.txt`** location + load-order/precedence, config-key spellings, the config-store vs card-store `set` distinction → **ma-interface-consultant**.
- **PDF-set management** (`pdlabel`/`lhaid`/`lhapdf` in run_card, bundled-grid vs LHAPDF linking, the "no-LHAPDF" behaviour) → **ma-scales-pdf-consultant**.
- **Per-tool path key + availability gate** — one owner each: `pythia8_path` + `shower=` → **ma-pythia8-interface-consultant**; `delphes_path` → **ma-delphes-interface-consultant**; `madanalysis5_path` → **ma-madanalysis5-interface-consultant**.
- **Install smoke-test / verification launch** (`bin/mg5_aMC` entry, `output`→`launch`→`Events/run_01/`, inline `set run_card` timing, `done` terminator) → **ma-launch-consultant**.

## Dispatch ordering
1. **ma-installation-consultant first** for anything about the `install` command surface, prereqs, or where files land — it owns the installer parse.
2. **ma-interface-consultant** for config-file/key questions (independent of #1).
3. **The per-tool interface consultant** for "why isn't tool X offered / did it run" — this is the downstream availability question, see `[[downstream-card-existence-gate]]`.
4. **ma-scales-pdf-consultant** for PDF questions (independent).
5. **ma-launch-consultant** for the verification-launch flow.
Waves 1–2 and 3–5 are largely parallel; cap the fan-out and drain before the next wave.

## Anticipated traps (pointers — mechanism lives in the consultant page)
- **Install tokens are case-sensitive** and the accepted set is narrow (`install delphes` lowercase and bare `install lhapdf` both fail; only `lhapdf6`/`lhapdf5` exist) → ma-installation-consultant.
- **Install target dir is not uniformly `HEPTools/`** — some tools land in `$MG5DIR/<name>` → ma-installation-consultant.
- **A commented config line does not mean "unset"** — the code's options-dict default fills the key (e.g. `delphes_path` defaults to a real path even when the template line is `#`-commented) → ma-interface-consultant / ma-delphes-interface-consultant. Related: `[[config-value-lifecycle-layers]]`.
- **`automatic_html_opening` default is `True`**, not the value older write-ups often show → ma-interface-consultant.
- **Three-gate downstream availability** (path-set → shower-present → operative-card-exists) governs whether Pythia8/Delphes/MA5 is offered and whether it silently no-ops → the per-tool interface consultant + `[[downstream-card-existence-gate]]`.
- **No runtime PDF fallback** — the default `pdlabel` is a bundled compiled-in grid (needs no LHAPDF); selecting `pdlabel=lhapdf` without a configured LHAPDF *errors* rather than degrading; `lhaid` is inert unless `pdlabel=lhapdf` → ma-scales-pdf-consultant.
- **Pythia8 showering does NOT require the `mg5amc_py8_interface`** in current versions — the default path uses a build-internal example driver; the interface is a legacy/fallback path only → ma-pythia8-interface-consultant.

## Return-interpretation hint
**Env STATE is a shell check, not a dispatch.** "Is Pythia8/Delphes/LHAPDF/MA5 actually built in this install" is a mechanical `ls`/`which` on `$MADGRAPH_INSTALL/HEPTools/` and `$MADGRAPH_INSTALL/Delphes/` (and `bin/ma5` for MA5) — settle it directly. Dispatch the consultant for the *source logic* (what the gate checks, what a value resolves to), then combine with the env fact you looked up. A consultant returning "install-blocked / cannot probe" usually means the tool is not built here — confirm with the `ls`, don't re-dispatch.

Related: `[[pipeline-stage-map]]`, `[[downstream-card-existence-gate]]`, `[[config-value-lifecycle-layers]]`, `[[probe-backlog]]`.
