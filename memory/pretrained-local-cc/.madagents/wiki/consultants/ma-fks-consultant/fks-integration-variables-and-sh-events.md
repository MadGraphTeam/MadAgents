---
description: The three FKS integration variables (xi_i, y_ij, phi_i) and their MINT folding slots; S-event (n-body Born-like) vs H-event ((n+1)-body real) decomposition; NLO_mode='real' skips virtuals (no MadLoop link).
---

# FKS integration variables, folding, and S/H events

## The three FKS integration variables
FKS parametrises the real-emission phase space with three variables of the
"FKS parton" i and its collinear partner j:
- `xi_i` — rescaled energy fraction of the FKS parton i (the SOFT variable;
  xi_i→0 is the soft limit).
- `y_ij` — cosine of the angle between i and j (the COLLINEAR variable;
  y_ij→1 is the collinear limit).
- `phi_i` — azimuthal angle of the FKS parton i.
Runtime carrier: `common/fksvariables/xi_i_fks_ev, y_ij_fks_ev, ...`
(`montecarlocounter.f:657-659`); the MC subtraction `xmcsubt(pp,xi_i_fks,y_ij_fks,...)`
takes xi and y (`montecarlocounter.f:545,614,820`).

## run_card `folding` → FKS variables (claim confirmed)
`run_card_NLO` param `folding = [1,1,1]` (`banner.py:5706`, RunCardNLO-owned);
each of the 3 entries ∈ {1,2,4,8} (`banner.py:5928-5932`, else `InvalidRunCard`).
The three slots map, IN ORDER, to xi_i, y_ij, phi_i — confirmed by the MINT
driver prompt/read (`driver_mintMC.f:615-617`):
```
'Set the three folding parameters for MINT' / 'xi_i, y_ij, phi_i'
read (*,*) ixi_i, iy_ij, iphi_i
```
and the folding-array wiring (`driver_mintMC.f:195-200`, same in `driver_mintFO.f:187-189`):
```
ifold_energy = ndim-2 ; ifold_yij = ndim-1 ; ifold_phi = ndim
ifold(ifold_energy)=ixi_i ; ifold(ifold_phi)=iphi_i ; ifold(ifold_yij)=iy_ij
```
Folding = MINT importance-sampling refinement over each FKS variable
(higher value = more sub-samples folded per point, smoothing the integrand
around the soft/collinear peaks at the cost of CPU).

## S-events vs H-events
FKS/MC@NLO event decomposition (`add_write_info.f`, `Hevents` logical flag,
`:1,:149,:186-207,:313-373`):
- **H-events**: (n+1)-body real-emission kinematics. Weight ~ real ME minus the
  MC (shower) counterterms. `Hevents=.true.` branch writes the full n+1 partons.
- **S-events**: n-body Born-like kinematics (Born + virtual + integrated FKS
  subtraction counterterms + soft-virtual). `Hevents=.false.` branch, i<->j
  mapping collapsed onto the Born configuration.
`put_on_MC_mshell(Hevents,...)` (`add_write_info.f:336`) puts partons on shell
per the event type. The n-body vs n+1-body prefactor machinery lives in
`fks_singular.f` (`compute_prefactors_nbody` / `_n1body`, factors f_b/f_nb,
`:1143-1152`). (This is the FKS/MC@NLO scheme structure; detailed weight
assembly & the emission exporter are nlo-export/amcatnlo runtime.)

## NLO_mode='real' ([real=QCD]) — FKS-side gating
`generate_virtuals()` is called ONLY for `NLO_mode in ['all']`
(`fks_base.py:272-274`); `'real'` and `'LOonly'` are accepted modes but skip it,
so **NO virtual amplitude is generated and NO MadLoop link is made**. The
interface also skips the compiler check for real/LOonly (`amcatnlo_interface.py:479`)
and `validate_model('real')` does not require a loop-capable model.
BUT the born still gets `generate_reals()` (`fks_base.py:258`) — the real-emission
amplitudes and their fks_infos ARE built even in real mode; what real-only mode
omits is the virtual (MadLoop) piece and, downstream, the S-event integrated
subtraction (that subtraction wiring is nlo-export/amcatnlo runtime, not the
FKS generation object). Bracket parsing of `[real=...]` itself is nlo-syntax.
