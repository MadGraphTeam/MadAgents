---
description: Which models are bundled vs online in v3.7.1; how to determine the loop-capable bundled set (scan models/*/coupling_orders.py with perturbative_expansion>0, never "=1") and the _online_model db entries. Bundled SET + count DRIFT across builds — always re-list models/ and re-scan; do not cache the count. loop_qcd_qed_sm bundled-presence flips build to build (online-only on some).
---

# Bundled vs online loop-capable models (v3.7.1)

Verified for `$MADGRAPH_INSTALL` v3.7.1 — version-specific AND build-specific, re-check on
every install (the bundled set demonstrably drifts, see Caution). Do NOT carry a flat count;
re-run the live scan below on the target install.

## Bundled models — re-list every time (`$MADGRAPH_INSTALL/models/`)
The bundled directory set DRIFTS across builds/installs; never carry a listing. Get it live:
`ls models/ | grep -vE '__pycache__|template_files|\.(py|pkl)$'`.
`loop_qcd_qed_sm` in particular flips in/out of `models/` build to build (online-only on some);
settle with `ls -ld models/loop_qcd_qed_sm`. Locally-installed external models (SMEFTatNLO, the
2HDM-NLO family, dim6top_LO_UFO) also come and go with the install — do NOT assume any is present.

## Loop-capable bundled set (scan: a coupling order with perturbative_expansion>0)
Derive it, never recall it — for each `models/*/coupling_orders.py`, apply the importer's OWN
predicate `perturbative_expansion>0` (import_ufo.py:501), NOT the brittle literal `=1`:
```
for d in models/*/; do co="$d/coupling_orders.py"; [ -f "$co" ] || continue;
  hit=$(grep -oE "perturbative_expansion *= *[0-9]+" "$co" | grep -vE "= *0$");
  [ -n "$hit" ] && echo "$(basename $d): $hit"; done
```
A model qualifies iff some order scans `>0`; that order name(s) become `perturbation_couplings`.
Each loop-capable model also carries a `CT_vertices.py`; a model with neither is tree-level.
CURRENT SNAPSHOT (re-read, NOT durable — 2026-07, this build): the scan returns exactly ONE —
`loop_sm` (QCD `perturbative_expansion=1` at `coupling_orders.py:12`, QED unset→0 at :17) →
`perturbation_couplings==['QCD']`, QCD-only. NO 2HDM/SMEFT/dim6top present this build (all absent
from `models/`); `loop_qcd_qed_sm` absent (online-only). A PRIOR build scanned to FIVE (loop_sm +
2HDM5F_NLO + 2HDMtII_NLO + 2HDMtypeII + SMEFTatNLO, all QCD-only) — the count demonstrably drifts
1↔5↔6, so treat any number here as a stale example and re-scan. (When present, `SMEFTatNLO` is an
external/FeynRules model living under models/ only if locally installed, NOT in `_online_model`;
`dim6top_LO_UFO` is LO despite shipping a CT stub. Verify presence with `ls`, never assume.)

### The scan predicate is `>0`, NOT `=1` — this is what makes the count oscillate
`import_ufo.py:501` tests `if(order.perturbative_expansion>0)`. loop_qcd_qed_sm declares
`perturbative_expansion = 99` (an order-cap-like sentinel) on BOTH QCD and QED — `99>0`, so
it qualifies. A scan written as `grep "perturbative_expansion = 1"` SILENTLY MISSES it and
reports five. ALWAYS scan with the `>0` semantics (e.g. `grep -oE "perturbative_expansion *=
*[0-9]+" | grep -vE "= *0$"`), never a literal `=1`. (Full oscillation analysis in the
Caution below — the 5↔6 flip is this predicate bug AND genuine set drift.)

## Whether ANY bundled model perturbs QED depends on loop_qcd_qed_sm's presence
The only bundled model that ever perturbs QED is `loop_qcd_qed_sm` (QCD+QED, `gauge=[1]`
Feynman-only). Every other loop model examined (loop_sm, the 2HDM-NLO family, SMEFTatNLO) is
QCD-only (`perturbation_couplings == ['QCD']`, `gauge=[0,1]`). So whether any bundled model
perturbs QED == whether `loop_qcd_qed_sm` is in `models/` this build. When it is absent (as in
the current snapshot above), the EW/QED gauge-forcing branch (perturbation_couplings not in
`[[],['QCD']]`) is bundled-UNreachable, and `[QED]` against any bundled loop model is rejected
(Gate 2, process-loop-capability-gates; for sm-family it is the CheckLoop INFO + auto-upgrade
to loop_qcd_qed_sm which then downloads it). When it IS bundled, that branch is reachable.
Re-derive from the live scan, never assert from memory.

## _online_model dict (`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py:2894`)
Downloadable via `import model <name>`; value = list of restriction tags:
```
'2HDM':[], 'loop_qcd_qed_sm':['full','no_widths','with_b_mass ','with_b_mass_no_widths'],
'loop_qcd_qed_sm_Gmu':['ckm','full','no_widths'], '4Gen':[], 'DY_SM':[],
'EWdim6':['full'], 'heft':['ckm','full','no_b_mass','no_masses','no_tau_mass','zeromass_ckm'],
'nmssm':['full'], 'SMScalars':['full'], 'RS':[''], 'sextet_diquarks':[''],
'TopEffTh':[''], 'triplet_diquarks':[''], 'uutt_sch_4fermion':[''], 'uutt_tch_scalar':['']
```
(The dict content is version-dependent — re-read it at the cited coordinate, don't trust the
snippet above verbatim.)
- `loop_qcd_qed_sm` / `_Gmu`: full SM at NLO (QCD+QED perturbed). On the current build
  `loop_qcd_qed_sm` is **absent** from `models/` (online-only — both `ls` and the `>0` scan
  agree) and present only in this dict; `_Gmu` is likewise online-only. Both differ from loop_sm
  (QCD-only). The bundled presence of `loop_qcd_qed_sm` flips across builds — exactly the drift
  in the Caution below; do not assert it bundled without a live `ls`.
- `heft`: Higgs Effective Theory (ggH effective vertex) — relevant to the TIR HEFT branch.
- `EWdim6`, `TopEffTh`: EFT models. `_online_model2` (2910) is filled at runtime from the
  online db when the user does `display modellist`.

## Caution — the bundled SET drifts across builds; ALWAYS re-list + re-scan
- "Only loop_sm is loop-capable bundled" happens to be TRUE on some builds (the current one) and
  FALSE on others (builds carrying the 2HDM-NLO family / SMEFTatNLO). Never answer from a
  memorized set — scan coupling_orders.py for `perturbative_expansion>0` across models/ on the
  target install.
- The count OSCILLATES (this wiki has shipped 1, 5, and 6 across passes, each correct for its
  build at the time). Two independent causes, both settled by the live `>0` scan + `ls`:
  1. **Genuine set drift** — external models (loop_qcd_qed_sm, 2HDM-NLO, SMEFTatNLO, dim6top)
     present on some builds, absent on others. Settle with `ls -ld models/<name>`.
  2. **Scan-predicate bug** — `loop_qcd_qed_sm` declares `perturbative_expansion = 99`, so a
     `grep "= 1"` SILENTLY DROPS it and reports a phantom count. Scan with the importer's own
     test `>0` (`import_ufo.py:501`), NEVER `=1`.
- A LOW count is NOT necessarily a predicate miss — the models can be genuinely absent. Verify
  with `ls` AND the `>0` scan; when both agree, it is real set drift, not a scan miss.
- Corollary that flips with the set: whether ANY bundled model perturbs QED == whether
  `loop_qcd_qed_sm` is in `models/` this build (the only candidate with QED perturbed).
  Re-derive from the live scan — never assert from memory.
