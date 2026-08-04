---
description: NLO (aMC@NLO) LHE event-output format — events.lhe.gz filename, event_norm→IDWTUP weight convention (sum/average/unity/bias, negative weights), and the per-event #aMCatNLO FKS/MC@NLO metadata line + S-vs-H event structure that distinguishes NLO events from LO.
---

# NLO (aMC@NLO) LHE event-output format

Covers the weight convention and event-record structure of the parton-level LHE that aMC@NLO / aMC@LO / noshower modes emit. The Python-side *assembly* (collect_events, reweight branch gating) is [[print-summary-and-event-assembly]]; this page owns the *weight convention* (Fortran, event_norm) and the *per-event record differences vs LO*. Filename provenance is also in [[scripted-nlo-execution-and-launch-flags]].

## Filename — `events.lhe.gz` (NOT `unweighted_events.lhe.gz`)
Final parton-level file = `Events/<run_name>/events.lhe.gz` (amcatnlo_run_interface.py:3881 assembly, 1858 run()-assert hardcode). LO madevent's `unweighted_events.lhe.gz` name does NOT appear at NLO. (do_plot:1557-1564 transiently renames to `unweighted_events.lhe` and back — a plotting quirk, not the artefact.)

## event_norm → IDWTUP (lha_strategy) + weight convention — driver_mintMC.f:669-688
This is the load-bearing NLO weight fact. `event_norm` (RunCardNLO default `'average'`, banner.py:5619; allowed at LO `['sum','average','unity']` + `'bias'` auto-set, 4298/5945) maps to the LHE `<init>`-block **IDWTUP** field and rescales the per-event `event_weight`:

| event_norm | IDWTUP | per-event weight | sum/avg semantics |
|---|---|---|---|
| `average` (default) | **-4** | `event_weight` unchanged (≈ σ, signed) | AVERAGE of N event weights = σ |
| `sum` | **-3** | `event_weight/nevents` | SUM of N event weights = σ |
| `unity` | **-3** | `1d0` (weights = ±1) | pure sign; σ recovered via XSECUP |
| `bias` | -4 | (biased) XMAXUP=-1 | flagged DO-NOT-USE ([[print-summary-and-event-assembly]]:3295) |

- IDWTUP set at driver_mintMC.f:670 (`-3` for unity/sum) / 677 (`-4` else). `-3`=unweighted (equal-magnitude weights, sign only — NLO negatives allowed); `-4`=weighted (weights in pb, sum to σ). The negative IDWTUP (vs LO's positive) signals to the shower that **negative weights are present** — intrinsic to aMC@NLO's MC@NLO subtraction.
- `unity`: XMAXUP=1 (672), event_weight=1 (685). `sum`: XMAXUP/=nevents (674), event_weight/=nevents (687).
- Readback: `Banner.get_lha_strategy()` (banner.py:316-326) parses IDWTUP as init-line field `[-2]` (= `init.split()[8]`, cf init_dict['idwtup'] at amcatnlo_run_interface.py:4623); `set_lha_strategy` bounds it to `-4..4` (331). So the shower learns the weight convention from IDWTUP in the banner `<init>` block.
- The Python reweight path mirrors this: for `average`/`bias` (and nevents≠0) the reweight normalization weight is set to `1/nevents` (amcatnlo_run_interface.py:4814-4815); histogram combine uses norm=1 for `sum` else `1/nsplit_jobs` (4314-4317). `EVENT_NORM=<val>` is also passed to the shower via MCatNLO/banner.dat (banner_to_mcatnlo:4729).

**Consequence for the user:** an NLO LHE is inherently weighted with per-event weights that can be **negative** (unlike LO unweighted events, all +1). To get σ you sum (event_norm=sum/unity via XSECUP) or average (event_norm=average, the default) — you cannot treat NLO events as equal-weight. Negative-weight fraction is a real statistical cost of aMC@NLO.

## NLO event-record structure vs LO — the `#aMCatNLO` line + S/H events
Two structural differences from an LO `<event>` record, both written by write_event.f:

1. **Per-event `#aMCatNLO` metadata comment line** (write_event.f:210-233, format 201 at :267; also analysis_lhe.f:189-203). Appended as the event `buff`/comment when `AddInfoLHE` (hardcoded `.true.`, madfks_mcatnlo.inc:21 / reweight_xsec_events.f:118). Fields: `#aMCatNLO iSorH ifks jfks fksfather ipartner scale1 scale2 [kwgtinfo nexternal iwgtnumpartn ...]`. Carries the **FKS pair indices** (ifks/jfks), color partner, and **two shower starting scales** (scale1_lhe/scale2_lhe) that the MC@NLO shower reads to set its starting scale and veto — information an LO event never carries.

2. **S-events vs H-events** (add_write_info.f:149-155). Each aMC@NLO event is one of two classes, tagged by `iSorH_lhe`:
   - **H-event** (`iSorH_lhe=2`): full real-emission kinematics, `nexpart = nexternal` (n+1 partons).
   - **S-event** (`iSorH_lhe=1`): projected to Born kinematics, `nexpart = nexternal-1` (n partons).
   So a single aMC@NLO run's LHE contains events with **two different particle multiplicities**, unlike an LO run where every event has fixed multiplicity. This is the MC@NLO soft/hard subtraction surfacing in the event file — NOT two separate "counter-event" files; both S and H events live in the one `events.lhe.gz`, distinguished by the `#aMCatNLO` line.

3. **`<initrwgt>` / per-event weight blocks** for scale/PDF variation are written only when reweighting is on (`do_rwgt_scale`/`do_rwgt_pdf`, handling_lhe_events.f:33-98) — gated by the same reweight knobs as [[print-summary-and-event-assembly]]:3869-3871. Not NLO-specific in format, but at NLO the reweight branch is the built-in uncertainty path (systematics_program='none' by default, [[runcardnlo-defaults-and-ickkw]]).

## Cautions
- "NLO events are unweighted like LO" is WRONG — default `event_norm=average` → IDWTUP=-4, weighted, signed. Negative weights are intrinsic.
- The weight-convention answer is CLASS/mode-specific: read event_norm from the run_card and the IDWTUP mapping above; do not assume +1 weights.
- The `#aMCatNLO` line and S/H split are always present (AddInfoLHE hardcoded true) — a downstream tool that assumes uniform multiplicity or ignores the comment line will misread aMC@NLO events.
- Runtime predictions (exact bytes of the emitted line, negative-weight fraction) are source-read from the Fortran templates, not probed end-to-end on a live run.
