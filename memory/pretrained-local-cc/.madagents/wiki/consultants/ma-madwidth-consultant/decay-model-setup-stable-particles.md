---
description: How DecayModel determines which particles get widths (stable-particle determination via parity-protected decay groups + kinematic iteration, lazy-eval), plus scale-running, gauge-dependence, and on-shell conditions gating channel enumeration.
---

# DecayModel setup & stable-particle gating (v3.7.1)

All citations `mg5decay/decay_objects.py` unless noted. `DecayModel` extends `model_reader.ModelReader` (1293).

## Build path (from do_decay_diagram, madgraph_interface.py:10174-10180)
`DecayModel(self._curr_model, True)` then `read_param_card(param_card_path)`. The param_card is REQUIRED — masses from it determine on-shell/off-shell channel splits, so the same particle can enumerate different channels under different cards.

## read_param_card (1943)
- `set_parameters_and_couplings(param_card)`, then `exec`s every parameter/coupling into module globals (1949-1952) so the apx formulas can eval them.
- Builds `decaywidth_list[(pid, True)] = float(value.real)` from each particle's param-card width (1953-1956) — the seed widths.
- Sets `amZ0 = aS` (1958-1959): alpha_s at the Z pole is stashed before any running.

## Lazy evaluation of stable/groups (the non-obvious trigger)
`DecayModel.get(name)` (1364-1380) overrides access:
- `get('stable_particles')` when empty → calls `find_stable_particles()` (1367-1368).
- `get('decay_groups')` or `get('reduced_interactions')` when empty → `find_decay_groups_general()` (1373-1374).
- `get('max_vertexorder')` when 0 → `get_max_vertexorder()`.
So merely reading these attributes computes them; you don't call the finders explicitly.

## find_decay_groups_general (2400) — parity/Z2-style grouping
- "SM-like" = all MASSLESS particles (docstring 2403). `decay_groups[0]` is the SM-like group.
- Iteratively reduces interactions: 2 non-SM particles in a vertex → same group; 1 → SM-like; collapses until each remaining reduced interaction has ≥3 non-SM particles in distinct groups (2410-2429). Particles unrelated to others become lonely singleton groups.
- This is the conserved-quantum-number / dark-parity grouping: particles that can only be pair-produced/destroyed share a group, the lightest of which may be stable.

## find_stable_particles (2631) — two-pass
Pass 1 (parity-protected): for each non-SM group find the lightest massive member(s) (degeneracy kept as a sublist). Then iterate `reduced_interactions`: if any particle's `2*m > sum(masslist)` it can decay → clear that group's stable candidate, replace its lightest mass by `sum-m`, repeat until stable (2680-2698). Massless particles are pre-marked stable (2653-2657).
Pass 2 `find_stable_particles_advance` (2717): purely kinematic. For every interaction, if a non-stable particle has `2*m - total_m` above a round-off threshold it can decay → mark unstable, replace its mass by `total_m - m`, iterate to fixpoint. Anything never marked unstable is stable (2768-2776).
Both passes set `is_stable` on the particle AND its antiparticle.

## Stable particles are skipped in enumeration
`find_all_channels_smart` (2856) explicitly `if part.get('is_stable'): continue` (2810, 2826). So a particle judged stable gets NO width channels enumerated regardless of body_decay. A massless particle is always stable here (never gets a width).

## Scale running before each particle's enumeration
Before estimating a particle's channels, the engine runs couplings at scale = that particle's mass:
- `DecayParticle.find_channels` (799-800): `model.running_externals(abs(eval(self.get('mass'))))` + `running_internals()`.
- `find_all_channels_smart` (2814-2815, 2833-2834) and `find_all_channels` (2894-2895, 2919-2920): same, per particle.
`running_externals` (1963) re-solves alpha_s by Newton iteration from `amZ0` (the stashed Z-pole value) to the requested scale q (returns early below a low-mass cutoff — read the literal at :1963). `running_internals` (2099) then recomputes derived params. Consequence: apx widths use RUNNING couplings at the decaying particle's mass, not pole-scale values.

## On-shell condition uses ANTIPARTICLE mother mass
`Channel.get_onshell` (3615-3628): `onshell = ini_mass > sum(final_mass_list)` where `ini_mass = abs(eval(mass of get_anti_initial_id()))` — the mother's mass is taken from the antiparticle. Final masses are `abs(eval(...))` (handles complex/negative mass entries). On-/off-shell label is cached on the channel.

## Gauge-dependence drop (avoids double-counting soft/collinear radiation)
`Channel.check_gauge_dependence` (3575). MadGraph `spin` = 2S+1 (scalar=1, fermion=2, vector=3). The check `if part.get('spin') % 2 == 0: continue` SKIPS fermions (spin=2), so it only fires on BOSONS (odd spin value: scalar, vector). For each massless boson in the final state (3581-3583), it removes that particle, sorts the remaining ids, and looks for an existing ON-SHELL channel of the mother with the same reduced final state (`initial.get_channels(len(base), True)`, 3588). If found → returns False. Consumed in `find_channels_nextlevel` (952, 1007): `if not temp_c.check_gauge_dependence(model): continue` — drops the channel. Physics: a channel = (resolved on-shell channel) + (one massless boson, e.g. extra photon/gluon) off a propagator is gauge-dependent soft/collinear radiation already represented by the lower-multiplicity on-shell channel; counting both would double-count and break gauge invariance.

## Cautions
- Stable-particle determination is purely mass+interaction kinematics (plus parity grouping); it ignores coupling SIZE. A particle with an allowed-but-tiny coupling is still "unstable" and gets channels enumerated. Conversely a kinematically-blocked particle gets NO width even if listed AUTO.
- Massless particles are always stable here → never assigned an auto-width by the engine.
- The on-shell split (hence which channels exist) depends on the supplied param_card masses; recomputing widths with a different mass card can change the channel set.
- Scale running can fail/return-early below the low-mass cutoff (:1963, read the literal) — very light states use the unrun (pole) couplings.

## Boundaries
- The apx_decaywidth estimator and body_decay enumeration loop: see channel-enumeration-bodydecay page.
- The two-stage 2-body-FR / N-body-MadEvent compute and write-back: see compute-widths-flow page.
- AUTO-string survival through restriction: see autowidth-restriction-callback page.
