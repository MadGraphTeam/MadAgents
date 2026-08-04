---
description: Source-visible hazards in the chain-decay slice — comma+loop incompatibility, parser-acceptance vs amplitude-attachment (incl. flat-subdecay discard + self-decay warning), shared onshell field with $ filter, DiagramTag onshell=False false-friends, booldict drift, negative leg numbers, cascade > not in comma parser.
---

# Cautions — chain-decay slice

Source-visible hazards (pointers, not runtime-outcome claims). MG5_aMC v3.7.1.

## 1. Comma + `[`/`]` at NLO is a hard error — but the REACHING guard is the Switcher-routed aMC@NLO check, NOT the base textual `:3285` guard
(Superseded in-place — an earlier version claimed "`:3285` is what actually rejects a `p p > t t~ [QCD], t > ...` line"; that was WRONG. Probe-confirmed against the nlo-syntax slice in v3.7.1.)

**Canonical case `p p > t t~, t > w+ b [QCD]` (well-formed perturbation bracket, whether it binds the core or the decay) → reaching guard = `amcatnlo_interface.py:523`, message `"Decay processes cannot be perturbed"` (no trailing period).** Trace:
- `master_interface.py:162 extract_process_type` — `loopRE` (:175) is `^(.*)(\[(\s*(\w+)\s*=)?(.+)?\])(.*)$`; the greedy `.*` on both sides matches a `[...]` bracket ANYWHERE in the line, so a bracket on the DECAY subprocess still classifies the whole line as `('NLO','all',['QCD'])` — position-independent.
- `Switcher.do_add:209-215` (and the twin `do_generate:266-273`) — `type=='NLO'`, `nlo_mode='all'` → `change_principal_cmd('aMC@NLO')` → `:229 self.cmd.do_add` now dispatches to `aMCatNLOInterface.do_add` (:452), which OVERRIDES `MadGraphCmd.do_add` (:3232). The base interface never runs for this line.
- `aMCatNLOInterface.do_add` has NO textual `[`/`]`-in-comma guard; at `:520 if ',' in line:` → `extract_decay_chain_process` (:521) → `:522 if myprocdef.are_decays_perturbed(): raise MadGraph5Error("Decay processes cannot be perturbed")` (:523). This is a SEMANTIC perturbed-decay check, not a textual coincidence check.

So the base textual guard is SHADOWED for the entire input class "comma decay chain + well-formed perturbation bracket." (nlo-syntax owns the aMC@NLO bracket-parse guards; this slice owns the reaching-guard characterization.)

**The base textual guard `madgraph_interface.py:3283-3289`** (`MadGraphCmd.do_add`, in the LO interface) — verbatim :3285-3288:
```
The '[' and ']' syntax cannot be used in cunjunction with decay chains.
This implies that with decay chains:
  > Squared coupling order limitations are not available.
  > Loop corrections cannot be considered.
```
This lives on the LO interface's `do_add`. It is the reaching guard ONLY when `self.cmd` is `MadGraphCmd` at dispatch, i.e. `extract_process_type` returned `'tree'` and the Switcher kept/selected MadGraph (`:226-227` else-branch). **When does a comma line with a `[`/`]` char return `'tree'`? Only when the bracket is MALFORMED and fails `loopRE`** — a stray unbalanced `[` or `]`, or an empty `[]` (loopRE's orders group is optional, so `[]` matches but yields no orders → the `:193` else → `('tree',None,[])`). In those degenerate cases the Switcher routes to `MadGraphCmd.do_add`, whose `:3282 if ',' in line:` → `:3283 if ']' in line or '[' in line:` catches the stray char and raises `:3285`. **For any WELL-FORMED perturbation bracket, `:3285` is shadowed/dead — it is the reaching guard only for the "comma + malformed-bracket-character" degenerate class** (INFERRED from the routing trace; the malformed-bracket firing path is not probe-confirmed, only the canonical `[QCD]` shadowing is).

**The three FURTHER base post-parse guards** in the same LO `else:`-branch (`:3290-3307`, reached only for a comma line the base interface actually parses — i.e. NO bracket, since a bracket routes away): `are_decays_perturbed()` → `"Decay processes cannot be perturbed."` (WITH period, :3296-3297; note the aMC@NLO twin at :523 has NO period — the period distinguishes which interface raised); `decays_have_squared_orders() or myprocdef['squared_orders']!={}` → "Decay processes cannot specify squared orders constraints." (:3302-3304); `are_negative_orders_present()` → "Decay processes cannot include negative coupling orders constraints." (:3305-3307). These are the LO interface's belt-and-suspenders; the `:3296` perturbed-decay one is self-described "Redundant with above" and is effectively unreachable for bracketed lines (they never reach the base `else:`).

**Variant (core bracket, unperturbed decay) `p p > t t~ [QCD], t > w+ b`** — `are_decays_perturbed()` is False (the DECAY carries no bracket), so `:523` does NOT fire; the nlo-syntax slice's grounded premise routes this to a DIFFERENT guard `loop_interface.py:245-247` `if proc['decay_chains']: raise InvalidCmd("ML5 cannot yet decay a core process including loop corrections.")` (reached on the ML5/MadLoop path). That bracket-parse guard is nlo-syntax's territory; I confirm only the `:245-247` citation verbatim and that it is a distinct guard from `:523`.

Takeaway: a user combining NLO `[…]` with comma decays does not silently degrade — it errors. But quote the RIGHT guard: perturbed-decay `[QCD]` → `amcatnlo_interface.py:523` (no period); the base `:3285` textual message is shadowed and fires only on a malformed stray bracket.

## 2. Parser-acceptance ≠ amplitude-attachment (decay can be DISCARDED, not just unflagged)
`extract_decay_chain_process` only builds the textual `ProcessDefinition` tree. The `onshell=True` flag (→ gForceBW=1) is set far later in `DecayChainAmplitude.trim_diagrams` (diagram_generation.py:1284-1299), gated on the decay's incoming PDG id being among `decay_ids` AND appearing as a final-state external leg (`leg.get('state')`). A syntactically accepted comma-decay whose parent particle never materializes as a core final-state leg sets NO flag → that leg stays `onshell=None` → gForceBW=0. Do not infer gForceBW=1 from the mere presence of a comma; verify the leg was actually flagged (inspect decayBW.inc).

Stronger than "no flag": when a decay's parent id is absent from every core leg, `DecayChainAmplitude.__init__` (diagram_generation.py:1399-1424) emits a RED warning ("Decay without corresponding particle in core process found... Decay information for particle(s) X is discarded... usually means you forgot parentheses") AND **removes** that decay amplitude/chain entirely. This drop is the "no in-scope pdg-match" outcome of the general BINDING rule — see decay-binding-is-scope-times-match.md (binding = paren-scope × set-based pdg-match, read by topology fingerprint). Classic trigger: flat un-parenthesised nested subdecay `t > b w+, w+ > e+ ve` after `p p > t t~` (the `w+ > e+ ve` is read as a SIBLING decaying a non-existent core `w+`). Probe-confirmed: the discarded subdecay produces no forced-BW line in decayBW.inc (the `t` mother stays /1/, no extra w+ line). The fix is parentheses: `p p > t t~, (t > b w+, w+ > e+ ve)` to nest w+ under t. See onshell-flag-and-decayBW.md "Post-flag validation".

## 2b. Particle decaying to itself — warning only, NOT discarded
`DecayChainAmplitude.__init__` (diagram_generation.py:1428-1443): a decay whose decaying particle's `abs(id)` reappears in its own final state (e.g. `t > t g`) emits a RED "Decay(s) with particle decaying to itself" warning but is NOT discarded — the process still generates. Probe-confirmed (`g g > t t~, t > t g`). Distinguish from case 2 (discard): self-decay is warn-and-keep, missing-core-parent is warn-and-drop.

## 3. The `$` diagram-filter shares the onshell field
`onshell=False` (→ gForceBW=2) is set by the forbidden-s-channel / `$` path (diagram_generation.py:779-830), NOT by the comma parser. The tri-state field is shared across two slices. When reasoning about a decayBW.inc value of `2`, that is the diagram-filter slice's territory even though it surfaces in our artefact. A `$` filter can also RESET onshell back to `None` (diagram_generation.py:828-830) in a specific case.

## 4. booldict can drift across versions
The `{None:"0", True:"1", False:"2"}` map (export_v4.py:5884) is a small literal at the top of `write_decayBW_file`. Read it directly per question rather than trusting recall — enumerations drift across MG versions.

## 5. Negative leg numbers in decayBW.inc
The first index of `gForceBW` is `leg.get('number')` of an INTERNAL s-channel mother — these are low/negative because `get_s_and_t_channels` renumbers the resulting leg to `min()` of its contributors (helas_objects.py:1983/2039, see onshell-helas-bridge.md), NOT by a flat "internal ⇒ negative" rule. Don't expect external final-state leg numbers there, and don't map a decayBW leg number back to a command-line particle — read configs.inc. The same mother leg recurs across multiple iconfigs (confirmed in probe).

## 6. Cascade `>` never enters the comma parser
`>` is the basic process arrow inside `extract_process`; `extract_decay_chain_process` splits only on `,`/`(`/`)`. If a question conflates "the `>` operator builds the decay chain", that is wrong — the comma orchestrates the chain; `>` stays in the core/decay process fragments handed whole to `extract_process`.

## 7b. A decay fragment must be exactly 1→N (else hard InvalidCmd)
`DecayChainAmplitude.__init__` (diagram_generation.py:1383-1385) raises `InvalidCmd("Decay chain process must have exactly one incoming particle")` for any comma-decay fragment with ≠1 incoming particle. Probe-confirmed: `generate p p > t t~, t t~ > b b~ w+ w-` errors (the `t t~ > ...` 2→N fragment after the comma is rejected, NOT reinterpreted). Two sibling guards at the same site: decays can't be perturbed (1378-1379) and `is_decay_chain` is force-set (1381-1382). See onshell-helas-bridge.md.

## 7. Not every `onshell=False` write is the gForceBW=2 / `$`-filter setter
`grep -n "set('onshell'" / "onshell.*False"` surfaces SEVERAL `onshell=False` writes/reads. Only ONE is the semantic forbidden-s-channel flag that reaches `decayBW.inc` as `value 2`; the others are transient placeholders in DiagramTag reconstruction, immediately overwritten by the consumer, or pure reads. Verify which you're looking at. (`diagram_generation.py:793` and `:830` are NOT the only writers of `onshell=False` — `diagram_generation.py:214` and `:244` ALSO write it, as placeholders; see below.)

**The semantic forbidden-s-channel write (the gForceBW=2 path):**
- `diagram_generation.py:793` `newleg.set('onshell', False)` — forbidden-s-channel marking ($/diagram-filter slice's gForceBW=2 path). Block opens at the "Mark forbidden (onshell) s-channel propagators" comment :779-791. The reset `lastleg.set('onshell', None)` at :830 (under `if lastleg.get('onshell') == False:` :829) flips it back in a specific case.

**Transient placeholder writes in the BASE `DiagramTag` reconstruction (NOT semantic — overwritten downstream):**
- `diagram_generation.py:214` `onshell= False` inside `DiagramTag.leg_from_legs` (base class at :46; method :198-219). Comment at :213: "this needs to be done before combining decay chains." This IS a write of False, but it is a placeholder default for the reconstructed resulting leg.
- `diagram_generation.py:244` `'onshell':False` inside `DiagramTag.leg_from_link` (:236-247) — placeholder default for a reconstructed external end-leg.
- Why they are NOT the gForceBW=2 path: the production config-tag class `CanonicalConfigTag` (helas_objects.py:274) drives `diagram_from_tag` at :341. It **overrides `leg_from_link`** (:504-513, sets `onshell:None` at :512), so base :244 is never used in that path. It does **NOT override `leg_from_legs`**, so base :214's `onshell=False` IS executed — but `CanonicalConfigTag.vertex_from_link:534` immediately overwrites the resulting leg with the REAL onshell from the vertex_id tuple: `vertex.get('legs')[-1].set('onshell', vertex_id[1][1])`. So :214's False is a transient placeholder, gone by the time the leg reaches configs.inc/decayBW. (See onshell-helas-bridge.md DiagramTag round-trip.)

**A `== False` READ, not a write:**
- `helas_objects.py:214` `vertex.get('legs')[-1].get('onshell') == False` inside `IdentifyMETag.vertex_id_from_vertex` (class :59) — zeroes the s-channel PDG (`s_pdg = 0`) for identity tagging. Reads onshell, never writes. NOTE: this is a DIFFERENT file from `diagram_generation.py:214`; the two `:214`s are easy to conflate.

**Constructor/placeholder defaults of `None`:**
- `helas_objects.py:386` `'onshell': None` (CanonicalConfigTag get_s_and_t_channels, the new s-channel leg from popped legs) and `:512` (the `leg_from_link` override). Real value written back at :534.

Takeaway: a `value 2` in decayBW.inc traces ONLY to `diagram_generation.py:793` (`$`/diagram-filter slice). The other `onshell=False` writes (`diagram_generation.py:214`/`:244`) are base-`DiagramTag` reconstruction placeholders overwritten at the `CanonicalConfigTag` consumer (:534), and `helas_objects.py:214` is a read. The false-friend is NOT "only :793 writes False" — it is "only :793's False is SEMANTIC and survives to the artefact." Verify the set-vs-read AND the file (two `:214`s).

**The overwrite is NOT a side-path, it is THE decayBW-feeding write:** the `s_and_t_channels` argument `write_decayBW_file` reads is produced by `CanonicalConfigTag.get_s_and_t_channels` (helas_objects.py:283), which calls `self.diagram_from_tag(model)` (:341) — exactly the reconstruction that runs base `leg_from_legs` (placeholder `onshell=False` at diagram_generation.py:214) then `CanonicalConfigTag.vertex_from_link` (:534, overwrites `legs[-1].onshell` with `vertex_id[1][1]`). Export call chain: `HelasMatrixElement.get_s_and_t_channels` (helas_objects.py:3120-3123, builds the `CanonicalConfigTag`) → `write_configs_file` collects `s_and_t_channels` → `write_decayBW_file` (export_v4.py:4475) reads `schannels` last-leg onshell at :5891-5894. So `:214`'s False is overwritten **on the very leg decayBW reads** — `:534`'s write is the operative source of every decayBW value, restoring the real onshell that `vertex_id_from_vertex` packed into `vertex_id[1][1]` at :480 (a 3-tuple only for non-final s-channel vertices, so the `len(vertex_id[1])==3` guard at :534 fires exactly on s-channel propagators; the last-vertex 2-tuple at :471-474 is correctly skipped). This makes "only :793's False is semantic" precise: :214's placeholder is unconditionally overwritten at :534 for every s-channel leg, so it can never reach value 2 even in principle.
