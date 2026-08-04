---
description: Which UFO models actually ship under models/ (this install), the online model-DB fetch path (get_model_db / import_model_from_db), and hgg_plugin as the shipped effective-vertex plugin anchor (HIG/HIW orders). Model name != shipped != content.
---

# Shipped UFO models + the online model database

Covers the "model import and model database" question from the model-content side: what is on disk, how a not-on-disk model is fetched, and the concrete effective-vertex model that IS shipped. Refs under `$MADGRAPH_INSTALL/models/` (=$MADGRAPH_INSTALL/models).

## Shipped model roster (re-resolve per build — `ls $MADGRAPH_INSTALL/models/`)
The FIXED core shipped under `models/` (v3.7.1) — these are reliably present:
- `sm` — tree Standard Model.
- `loop_sm` — loop-capable SM (ships `CT_couplings.py`/`CT_parameters.py`/`CT_vertices.py`).
- `MSSM_SLHA2` — MSSM.
- `hgg_plugin` — effective Higgs-gluon/photon model (see below).
- `taudecay_UFO` — the ONLY shipped model carrying `propagators.py` + a `Propagator` class in its `object_library.py`.

Non-model support dirs also present: `template_files/`, `__pycache__/`, plus the loader `import_ufo.py` and `object_library.py`/`write_param_card.py` at the `models/` top level.

**Oscillating / not part of the fixed set** — `2HDM`, `EWdim6`, `heft`, and the EFT models `SMEFTsim*`, `SMEFTatNLO`, `dim6top_LO_UFO` are NOT part of the reliable core; EFT UFOs come and go across builds. **`ls models/<name>/` before asserting presence OR absence** — do not answer from this page. When absent, any claim about `heft/vertices.py` (ggH/gggH/ggggH/H-γγ, ggHH) or SMEFT/dim6 content CANNOT be verified against `models/` — the model must be fetched from the online DB or installed first. The shipped effective-vertex content lives in `hgg_plugin`, not `heft` (hgg_plugin uses order names HIG/HIW). Route physical heft/SMEFT-content questions to a fetch/install first.

**Durable on-disk EFT anchor** (present even when `models/SMEFTatNLO/` is not): the test fixture `$MADGRAPH_INSTALL/tests/input_files/SMEFTatNLO_running/` — a complete SMEFTatNLO UFO. `ls` it for the exact file set (`coupling_orders.py`, `couplings.py`, `parameters.py`, `vertices.py`, `CT_*.py`, and its `restrict_*.dat` variants — read the actual restrict filenames off disk, do not assume). Use it to anchor SMEFTatNLO/SMEFT-convention grammar facts. SMEFTsim's own UFO (different WC block naming, different EW-scheme files, NPprop/NPcpv/NPshifts/SMHLOOP orders) is NOT on disk in any form → GAP; SMEFTsim-specific declaration values are unverifiable here.

A model's directory NAME does not tell you its content or even that it is on disk — resolve both by `ls models/<name>/` then reading its `.py` files.

## Online model database — get_model_db / import_model_from_db (import_ufo.py)
When `import model X` finds no local dir, the DB path fires (orchestration = model-loader/installation slice; the fetch functions themselves are here):
- `get_model_db()` (`import_ufo.py:104-133`): two hardcoded mirrors — `http://madgraph.phys.ucl.ac.be/models_db.dat` and `http://madgraph.mi.infn.it//models_db.dat` (:107-108), tried in RANDOM order (`random.randint(0,1)`, :110-111). The `MG5aMC_WWW` env var (:114-116), if set, PREPENDS `$MG5aMC_WWW/models_db.dat` and is tried FIRST (index 2 inserted at front). All-fail → `MadGraph5Error` "Impossible to connect any of us servers" (:129).
- `import_model_from_db(model_name, local_dir=False)` (:135-200): reads `models_db.dat` line-by-line, each line is `<name> <url>`; matches `model_name==split[0]`, else logs "no model with that name found online" and returns `False` (:150-152). Target dir defaults to `pjoin(MG5DIR,'models')` (:174; a special-case PYTHONPATH/`UFOMODEL` branch is gated on username in `['omatt','mattelaer','olivier','omattelaer']`, :164-172 — dead for other users). Downloads via `misc.wget(link,'tmp.tgz',...)` (:180) then untars: `.tgz/.tar.gz/.tar` via `tar -xzpvf` with `tar -xpvf` fallback (:183-189), `.zip` via `unzip` (:191-196); unpack failure → "Please install it manually".

## hgg_plugin — the shipped effective-vertex plugin (concrete anchor)
`hgg_plugin/coupling_orders.py`: four `CouplingOrder`s — `QCD`, `QED`, **`HIG`**, **`HIW`** (read expansion_order/hierarchy at the decls). The HIG/HIW `expansion_order=1` sentinel caps each effective insertion to one power (vs QCD/QED's no-cap sentinel).

`hgg_plugin/vertices.py` — count entries in the file; the coupling order lives on the Coupling (NO `order=` field on the Vertex objects), read from `hgg_plugin/couplings.py`:
- `V_12`: `A A H` → GC_1 `-(AH*i)`, order **{HIW:1}** — the H-γγ (diphoton) vertex.
- `V_13`: `G G H` → GC_13 `-(i*GH)`, order **{HIG:1}** — ggH.
- `V_41`: `G G G H` → GC_14 `-(G*GH)`, order **{HIG:1,QCD:1}** — gggH.
- `V_42`: `G G G G H` → GC_15 `i*G**2*GH`, order **{HIG:1,QCD:2}** — ggggH.
- `V_37`: `G G h1` → GC_16, order {HIG:1}; `V_43`: `G G G h1` → GC_17, order {HIG:1,QCD:1}.

So HIG governs {ggH, gggH, ggggH}; HIW governs {H-γγ}. hgg_plugin ALSO carries a second scalar `h1` (pdg 9000006, self-conjugate; `particles.py:37`) with `G G h1` / `G G G h1` effective couplings — an extra field beyond the SM Higgs. **No double-Higgs contact** (`G G H H` / `H H` anything) vertex exists in hgg_plugin. Model-content viability of any Higgs-effective process should be resolved against THESE 6 vertices, not a heft assumption.

## loop_sm triple-Higgs (anchor for lam-derived couplings)
`loop_sm/vertices.py`: `V_1` = `[H,H,H]`, lorentz `SSS1`, coupling `GC_30` (:80-84). `GC_30 = '-6*complex(0,1)*lam*v'`, order {QED:1} (`loop_sm/couplings.py:131-133`) — proportional to `lam` (internal, `=MH**2/(2 v**2)`) × `v`. The quartic `V_HHHH`=`[H,H,H,H]` → `GC_HHHH` sits at `vertices.py:74`. So the trilinear-Higgs coupling is fixed by MH and v through the internal `lam`, not a free card input.

## Pickle-cache pointer
Model caching (gauge-selected `py3_model*.pkl`, `dec_` decay prefix, `is_uptodate`+`version_tag`+prefix validity) is `ufo-loader-gauge-and-pickle.md`. Confirmed at `import_ufo.py:355-390` (pickle name `py3_model.pkl` unitary / `py3_model_FDG.pkl` gauge-3 / `py3_model_Feynman.pkl` else; `files_list` includes import_ufo.py itself, :352).
