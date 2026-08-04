---
description: LHE event output format — Fortran event writer (rw_events.f write_event), init/event/particle record layout, event_norm normalization + written_weight per-mode formula, LHA strategy, SPINUP three-occurrence story (external=selected-nhel / reconstructed status-2 intermediates=9 via addmothers.f:332 / Python default=9), VTIMUP=0, nevents=0 no-file. v3.7.1.
---

# LHE event writing + event_norm normalization (v3.7.1)

Files: `$MADGRAPH_INSTALL/Template/LO/Source/rw_events.f` (Fortran writer), `.../Template/LO/SubProcesses/unwgt.f` (fills the record), `.../madgraph/various/lhe_parser.py` (Python re-writer + final unweight/normalization), `.../madgraph/various/banner.py` (init block + run_card param), `.../madgraph/interface/madevent_interface.py` (drives final unweight).

## The actual Fortran event writer — rw_events.f:225 `write_event`
Called from `unwgt.f:861` (per surviving unweighted event). Layout (rw_events.f:280-304):
- `'<event>'` (280).
- **Event header** (281): `write(lun,'(i2,i5,e16.7e3,3e15.7)') nexternal,ievent,wgt,scale,aqed,aqcd` → LHE fields `NUP IDPRUP XWGTUP SCALUP AQEDUP AQCDUP`. Note order: **AQED before AQCD**. (lhe_parser.py:2236 comment confirms "Nexternal IEVENT WEIGHT SCALE AEW AS"; parse asserts exactly 6 fields, 2239.)
- **Particle records** (282-285): `ic(1,i),ic(6,i),(ic(j,i),j=2,5),(p(j,i),j=1,3),p(0,i),p(4,i),0.,real(ic(7,i))` under `format 51 = (i11,5i5,5e19.11,f3.0,f4.0)` (304). Columns 1-13:
  1. IDUP = `ic(1)` (PID)
  2. ISTUP = `ic(6)` (−1 initial / +1 final / +2 decayed) — note ISTUP is stored in `ic(6)` but written **2nd**
  3-4. MOTHUP(1,2) = `ic(2),ic(3)`
  5-6. ICOLUP(1,2) = `ic(4),ic(5)`
  7-10. PUP(1..4) = px,py,pz,E = `p(1),p(2),p(3),p(0)`
  11. PUP(5) = mass = `p(4)`
  12. VTIMUP = `0.` (hardcoded, `f3.0`) — the proper-lifetime column is **uniformly 0** in every MG-written record (no source path sets it non-zero here)
  13. SPINUP = `real(ic(7))` = **the per-event selected helicity**, `f4.0`
- Optional trailers: `<scales>`/`#` buffer (286-287), `<rwgt><wgt id='bias'>` unless `impact_xsec` (288-293), `<mgrwt>` systematics buffer if `u_syst` (294-298), `<clustering>` if matched (299-301), `'</event>'`.
- `ic(*)` filled in `unwgt.f:590-610`: `ic(7)=jpart(7)=nhel(i)` from `get_helicities` (607-609) — the MC-selected helicity for THIS event.
- Twin writer `write_event_to_stream` (rw_events.f:136, format 51 at 221) must be kept in sync (229-230 note).

## SPINUP: THREE separate occurrences of the value 9 (supersedes "only Python")
SPINUP = `real(ic(7,i))` at write time (rw_events.f:284). `ic(7)` carries different helicity provenance depending on the record TYPE, so `9` appears from THREE independent sources — the earlier "the 9 is ONLY a Python artifact" claim was wrong (it missed the second, Fortran-written one):

1. **External legs (status ±1) → the MC-selected helicity.** `unwgt.f:590-610` fills `ic(7,i)=jpart(7)=nhel(i)` from `get_helicities` for the true final/initial-state particles — e.g. `-1.`, `1.`. This is the per-event MC-selected helicity; NOT 9.
2. **Reconstructed intermediate resonances (status 2) → `9` (Fortran-written).** When `addmothers.f` reconstructs the s-channel mother records (the decayed intermediates it inserts into the record, e.g. the `23  2 ... 9.` Z line in `e+e- > mu+mu-` at √s=M_Z), it has no MC-selected helicity for them and hardcodes the LHE "unknown" sentinel: **`addmothers.f:332` `jpart(7,i) = 9`** under comment `c  Just No helicity info for intermediate states`. This runs in the intermediate-resonance loop (bodies at 270-333, per-s-channel `i`), then jpart is reordered into output positions at `addmothers.f:364` (`jpart(j,ito(i))=jpart(j,i)`, all 7 columns incl. helicity) and emitted as `ic(7)` → SPINUP. So the Fortran writer path itself emits `9.` on every reconstructed status-2 mother record. (Empirically, for that process at √s=M_Z, nearly every event carries the reconstructed Z line with `9.` — but the *fraction* of events with a reconstructed status-2 intermediate is **process- and kinematics-specific, not a general rate**; it depends on which s-channel resonances are on-shell-reconstructible for the given process and BW window. Measure per-process; do not cache a universal fraction.)
3. **Python `lhe_parser.Particle` default → `9`.** `self.helicity=9` (lhe_parser.py:94,117) is the constructor default for a Particle built with no source line — the standard LHE "unknown" sentinel. This is a THIRD, separate occurrence, unrelated to the Fortran write path; when parsing a real MG event line the last column is read back verbatim (so external legs read ±1, intermediates read 9).

Net: in an MG-generated LHE file, external legs carry the selected `nhel` and reconstructed status-2 intermediates carry `9.` — the `9` on intermediates is genuinely written by Fortran (addmothers.f:332), not injected by Python.

## Init block format — banner.py
- Header line (`init` line 0) has **10 fields** (get_lha_strategy 322-326): `IDBMUP(1,2) EBMUP(1,2) PDFGUP(1,2) PDFSUP(1,2) IDWTUP NPRUP`. `field[-2]=IDWTUP=lha_strategy`, `field[-1]=NPRUP`.
- Per-process lines (modify_init_cross 364-380): 4 fields `%+13.7e %+13.7e %+13.7e %i` = **XSECUP XERRUP XMAXUP LPRUP**. XSECUP set to `cross[pid]`; XERRUP/XMAXUP scaled by `ratio=cross/old_xsec`. Cross-section is written into `<init>` regardless of event_norm (claim 6 ✓).
- LHA strategy set by `set_lha_strategy` (328-343), clamped `-4..4`. Sign kept from current strategy; magnitude from normalization (see below). madevent bias path forces `-4` (madevent_interface.py:4042).

## event_norm — default + per-mode weight formula
- **Default = `average`** for both LO (banner.py:4298, `allowed=['sum','average','unity']`) and NLO (5619). Auto-flip to `'bias'` if `flavour_bias[1]!=1` (5943-5945).
- Final unweighting: `AllEvent.unweight(..., event_target=nevents, normalization=run_card['event_norm'])` (madevent_interface.py:3922-3925 / 3885). `AllEvent` is a `MultiEventFile`.
- **`MultiEventFile.unweight` sets `self.written_weight = new_wgt`** by mode (lhe_parser.py:1224-1239, when `event_target>0`):
  - `sum`   → `new_wgt = Σacross / event_target`, strategy 3 → **Σ of weights = σ**
  - `average` → `new_wgt = Σacross`, strategy 4 → every `|XWGTUP| = σ`, so **average of weights = σ**. Under the DEFAULT `event_norm=average`, every unweighted event carries an **identical** XWGTUP equal to the cross-section σ (confirmed).
  - `unit`  → `new_wgt = 1.`, strategy 3 → weights = **±1**
- Each written event weight = `written_weight(x) = copysign(self.written_weight, x)` (lhe_parser.py:467; applied 571/580). So all unweighted events carry equal magnitude, sign preserved (claim 6 ✓). Base `EventFile.unweight` also sets LHA strategy `3` for `['unit','sum']` else `4` (519-522).
- The per-event unweighting keep-test: `abs(wgt) < r*max_wgt → skip`; survivors get `±written_weight(max(|wgt|,max_wgt))` (564-584) — sub-max weights raised to max_wgt (partial-unweighting truncation), same floor logic as combine_runs.copy_events.

## CAUTION — `unity` vs `unit` token mismatch
run_card `event_norm` allowed value is **`unity`** (banner.py:4298), but the consumer `MultiEventFile.unweight` compares against **`unit`** (lhe_parser.py:1232), as does `EventFile.unweight` (519) and `madevent_interface.py:4627`. `madevent_interface.py:4034` checks `'unity'`. The if/elif at lhe_parser.py:1226-1234 has no `else`, so a literal `'unity'` string would match none of sum/average/unit → `new_wgt`/`strategy` unset. Whether `event_norm=unity` actually reaches this branch unconverted (→ crash) or is normalized upstream is a **runtime prediction, not verified** — probe before asserting. Do not claim `unity` "just works".

## nevents = 0 → no event file (claim 7 ✓)
madevent_interface.py:3909-3911: if `gridpack` or `nevents==0`, each channel `events.lhe` is deleted and skipped (`continue`) so `AllEvent` stays empty → `nb_event=0`, no `unweighted_events.lhe` written. Cross-section is still summed (3905-3907) and written to init. So `nevents=0` = integration/σ only. The `nevents` run_card default is registered at banner.py:4214 (LO; NLO at 5615) — read it fresh there, do not cache the number.

## Output path (claim 1 ✓)
`Events/<run_name>/unweighted_events.lhe` written then `misc.gzip` → `unweighted_events.lhe.gz` (madevent_interface.py:3922/3927).

## Weighted (varying-weight) events (claim 8)
Varying per-event weights arise from `bias_module` (the `<wgt id='bias'>` line, rw_events.f:288-293; XWGTUP carries the biased weight, unbias factor removed later at madevent_interface.py:4015) and from reweighting (systematics slice owns `ReweightInterface`). The bias piece is mine; alternate-weight reweighting indexing in `<rwgt>` is systematics' slice.
