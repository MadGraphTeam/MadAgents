---
description: MadSpin decay-chain grammar at the interface — card-line->do_decay boundary (#/;/\ split, comma NOT a separator), reorder_branch normalization, @-correlation tag grammar, multi-line->chain assembly, silent-drop-vs-Exception pruning, and get_proc_with_decay splice onto the production line (the generate-line-chain vs MadSpin seam)
---

# MadSpin decay-chain grammar and the generate-line splice seam

MadSpin is the *alternative* decay-attachment path to a generate-line chain decay. This page caches the
**interface-facing grammar** of that path: what a card `decay` line may carry, how separate card lines fuse
into one chain string, and exactly where/how that string is spliced onto the production process line. The
splice point is the precise seam where the generate-line chain and the MadSpin decay path interact (and
where one specific generate-line chain shape makes MadSpin abort). The BW-sampling / decay-ME physics that
consumes the spliced command is out of slice (decay.py internals); the string construction is interface.

## A card `decay` line is itself a (nested) chain
The default card (`Template/Common/Cards/madspin_card_default.dat`) ships a **two-level chain on one line**:
`decay t > w+ b, w+ > all all`. So a single card `decay` statement already carries a comma-separated nested
decay chain (top decays; the W from that top decays) — parallel to the generate-line parenthesized chain
`p p > t t~, (t > w+ b, w+ > ...)`, but written WITHOUT the outer parens and as a card line, not a generate
line. Each card `decay` line dispatches to `do_decay` (interface_madspin.py:420).

## Card-line -> do_decay grammar boundary (why commas survive into one decaybranch string)
The MadGraph caller feeds the card via `madspin_cmd.import_command_file(path)` (common_run_interface.py:4216).
`import_command_file` (extended_cmd.py:1691) does `open(filepath).readlines()` (:1702) and `for line in ...`
(:1712) — it reads **one card line at a time**, strips `\n` (:1715), and dispatches the whole line via
`exec_cmd` (:1718). The per-line `precmd` (extended_cmd.py:1009) is where the line-level grammar fires:
- `#` -> comment, everything after the `#` stripped (:1029-1030).
- trailing `\` -> line continuation, buffered into `save_line` (:1024-1026).
- `;` -> command separator: `line.split(';')` and each subline run as its own command (:1033-1041). So
  `decay a > b c ; decay d > e f` on one card line IS two `do_decay` calls.
- **comma is NOT a separator** — no comma handling in `precmd`. `onecmd` strips only the leading `decay`
  keyword and routes the rest to `do_decay(decaybranch)`, so the entire `t > w+ b, w+ > all all` (commas and
  all) arrives as ONE `decaybranch` string. THIS is exactly why `reorder_branch` (below) must itself tokenize
  on commas — the card reader never splits them. The comma is a *chain-nesting* operator inside a decay line,
  never a command separator.

## do_decay grammar normalization — reorder_branch (interface_madspin.py:433 -> decay.py:1772)
Every card `decay` line is run through `self.decay.reorder_branch(decaybranch)` before being stored in
`list_branches[init_part]` (interface_madspin.py:433-436). `reorder_branch` (decay.py:1772) tokenizes on
spaces after padding `, ( )` with spaces (:1778-1783), then for each comma whose preceding parent product
matches the sub-decay's mother, **swaps that mother to sit adjacent to the comma** (:1787-1810). Probe-confirmed:
- `t > w+ b , w+ > e+ ve` -> `t > b w+ , w+ > e+ ve` (decaying `w+` moved last, next to comma).
- `t > b w+ , w+ > e+ ve` -> `t > b w+ , w+ > e+ ve` (already canonical; unchanged).
- `t > w+ b` (no sub-decay) -> `t > w+ b` (unchanged — swap only fires when a `, X >` sub-decay names that product).
So the normalization positions the decaying daughter adjacent to its sub-decay comma; both input orders land
on the same canonical string. Return is `(new_branch_string, list_branch[0])` where `[0]` is the initial
particle used as the `list_branches` key.

## Multi-line -> single chain assembly (decay.py:2845-2862)
Separate card lines (`decay t > w+ b`, `decay w+ > all all`, `decay z > all all`) live as independent
`list_branches` entries. At full-ME build they are fused into ONE `decay_text` chain string:
- `decay_text_correlated = {'':[]}` groups branches by `@`-correlation tag (:2846).
- per branch: if `'@' in decay` -> split off the correlation key (:2850-2854); else key `''`.
- **default coupling order**: `if '=' not in decay: decay += ' QCD=99'` (:2856-2857). Every branch with no
  explicit coupling order gets `QCD=99` appended. THIS (decay.py:2857, inside the LIVE
  `decay_all_events.generate_all_matrix_element`, :2741) is the reachable site of the decay-coupling default.
  The onshell-spinmode override `decay_all_events_onshell.generate_all_matrix_element` (decay.py:4201)
  carries its own live copy at decay.py:4280. A THIRD copy lives in the DEAD
  `interface_madspin.py:1803` method (no caller, ends in `raise Exception` at interface_madspin.py:1844),
  with the same default at interface_madspin.py:1816 — see `madspin-onshell-interface-algorithm`. Carry the
  FILE with these line numbers: a bare `:1816` resolves into decay.py's unrelated `reorder_branch` return.
- **nested wrap**: `if ',' in decay: curr.append('(%s)' % decay)` (:2858-2859) — a card line that itself
  contains a comma (a chain) is parenthesized before joining; a single-level branch is appended bare (:2861).
- `decay_text = ', '.join(decay_text_correlated[''])` (:2862) — the uncorrelated branches join into one string.
So multiple card `decay` lines become a single comma-joined chain `decay_text` handed to the splice.

## `@`-correlation tag in a card decay line (separate grammar from the @N production tag)
A card `decay` branch may carry an `@<key>` suffix (e.g. `decay t > w+ b @0`). At assembly (:2850-2854) each
branch is checked for `'@' in decay`; if present it splits `decay, correlated = decay.split('@')` and the
branch is filed under that correlation key instead of the default `''` bucket (`decay_text_correlated[key]`).
This is the spin-CORRELATION grouping grammar: branches sharing a key are spliced TOGETHER but SEPARATELY from
the uncorrelated set. Consequence at command build (:2864-2881):
- **no correlated keys** (`not decay_text_correlated` after the `''` is `del`-ed at :2863): one
  `get_proc_with_decay(proc, decay_text, ...)` per production proc (:2865-2870) — the common case.
- **correlated keys present**: for EACH key, build `one_decay` = the uncorrelated `decay_text` (if any) +
  `', '` + that key's joined branches (:2872-2880), and emit a SEPARATE `get_proc_with_decay` command per
  (key, proc) pair. So N correlation keys -> N spliced commands (each a distinct standalone ME). All commands
  are concatenated into one `commandline` and the leading `add process` rewritten to `generate` (:2870/:2881).
NOTE this branch-level `@key` is DISTINCT from the production-line `@N` process-class tag that
`get_proc_with_decay` relocates after the decay spec (:3001-3011, test_madspin.py:88-102). Same `@` character,
different grammar role: `@N` on the *production* line is a process number; `@key` on a *card decay branch* is a
correlation bucket. The default card uses neither (`madspin_card_default.dat` lines 23-27 are plain decays).

## Silent-drop vs hard-Exception when a decay names a non-final-state particle (decay.py:2833-2838)
After building production MEs, branches are pruned (`# remove decay which are not present in any production ME`,
:2823): for each `list_branches` key not in any production final state AND not a multiparticle
(`key not in self.mgcmd._multiparticles`):
- if `len(self.list_branches) > 1` -> **silently `del`** that branch (:2835-2836).
- else (it is the SOLE branch) and not `onlyhelicity` -> **`raise Exception(" No decay define for process.")`**
  (:2838). (The `logger.info('keeping dummy decay for passthrough mode')` on :2839 is dead — after the raise.)
So a stray/mistyped decay particle is tolerated (dropped) when other valid decays exist, but aborts the run
when it is the only decay requested. This is the assembly-stage analogue of the launch-time "Nothing to
decay …" cross-check (interface_madspin.py:630-651, madspin-launch-and-decay) — that one fires earlier and
returns gracefully; this one fires at full-ME build and either drops or hard-raises.

## The splice — get_proc_with_decay (decay.py:2967-3035), comma-count divergence rule
`get_proc_with_decay(proc, decay_text, model, msoptions)` fuses `decay_text` onto each production process
string `proc` (the generate/add-process line, taken from the banner). This is the seam. NLO `[...]` procs are
first expanded to LO definitions via `get_LO_definition_from_NLO` (:2970-2972). For each base proc the rule
keys on **how many commas the production line already has** (`nb_comma = baseproc.count(',')`, :3019):
- **0 commas** (production has no chain decay): `"<proc>, <decay_text> <@N> <opts>"` (:3021) — simple append.
  Probe: `generate p p > t t~` + `t > w+ b` -> `generate p p > t t~, t > w+ b  --no_warning=duplicate;`.
- **1 comma** (production ALREADY carries one chain decay): splits at the comma and **distributes**
  `decay_text` both at top level AND inside the existing chain:
  `"<before>, <decay_text>, (<after>, <decay_text>) ..."` (:3022-3024).
  Probe: `generate p p > t t~, t > w+ b` + `w+ > all all` ->
  `generate p p > t t~, w+ > all all, ( t > w+ b, w+ > all all)   --no_warning=duplicate;`.
- **>=2 commas**: if ANY part contains `(` (a *parenthesized / multi-level* production chain) ->
  **`raise Exception('too much decay at MG level. this can not be done for the moment)')`** (:3026-3028).
  Otherwise (>=2 flat commas, no parens) distribute `decay_text` into each part (:3030-3033).
  Probe: `generate p p > t t~, (t > w+ b, w+ > e+ ve)` + decay -> RAISES `Exception` (matches test
  `tests/unit_tests/madspin/test_madspin.py:115`).

Trailing `--no_warning=duplicate` is force-added and options sorted (:2990-2999); `@N` is moved AFTER the
decay spec (:3001-3011); `msoptions['global_order_coupling']` appends `@0 <order>` if set (:3013-3017).

## Squared-order (`^2` / `NP^2==N`) in a card decay line is REJECTED — by the SHARED core guard, not a MadSpin guard
A card `decay` line carrying a squared-order constraint (`t > b w+ NP^2==2`, any `<order>^2 <op> N`) is
rejected — but the rejection is **inherited from the shared MG5 decay-chain parser**, NOT from any
MadSpin-specific check. Trace:
- `do_decay` (interface_madspin.py:420-437) does NOT inspect for `^2`. Its only order-related action is a
  WARNING when `=` is in the branch under spinmode full/madspin (interface_madspin.py:431-432, the
  BR-mismatch note). `^2` survives `reorder_branch` and is stored in `list_branches` verbatim.
- At full-ME build, `get_proc_with_decay` splices the branch (with its `^2`) onto the production line and the
  fused `commandline` (a decay-CHAIN `generate` string) is run via `mgcmd.exec_cmd` (decay.py:2869/2883).
- That lands in the shared core `do_add`/`extract_decay_chain_process` path. The guard
  **madgraph_interface.py:3301-3304**:
  `if myprocdef.decays_have_squared_orders() or myprocdef['squared_orders']!={}: raise MadGraph5Error("Decay processes cannot specify squared orders constraints.")`.
  `decays_have_squared_orders()` (base_objects.py:3576-3582) recurses `decay_chains`, returning True if any
  sub-process has a non-empty `squared_orders` dict.
- The sibling guards in the same block: decay chains with `[...]` brackets are barred earlier
  (madgraph_interface.py:3285-3289, "cannot be used in conjunction with decay chains"); perturbed decays
  (:3296-3297) and negative orders (:3305-3307) also raise.

**How this differs from the tree-level `generate` path that DOES accept `NP^2==N`:** a *non-chain* `generate`
line (no comma) goes through `extract_process` (madgraph_interface.py:3310) which parses `^2` into
`squared_orders` and accepts it (the `^2` grammar at :4927-4940). The squared-order rejection is triggered
ONLY by the decay-CHAIN branch (:3292, reached because the line has a comma). Because MadSpin ALWAYS fuses
its decay onto the production line as a comma-chain (the splice above), a squared order anywhere in a MadSpin
decay branch necessarily lands on the chain path and is rejected. So the practical rule "MadSpin decays
cannot carry squared orders" is real, but the enforcing code is the generic decay-chain guard, not MadSpin
interface code — same guard that rejects `p p > t t~, t > b w+ NP^2==2` typed directly on a generate line.
Note the default-append is `QCD=99` (ordinary amplitude order, :2857), never a squared order, so the default
path never trips this.

## The seam stated (generate-line chain vs MadSpin decay path)
The two decay paths DIVERGE exactly at `get_proc_with_decay`:
- A production line with NO chain decay, or with at most a **single flat** chain decay, can be further decayed
  by MadSpin (the 0/1-comma branches splice cleanly).
- A production line that already carries a **parenthesized (multi-level / nested) chain decay** CANNOT be
  further decayed by MadSpin — the >=2-comma+paren branch hard-raises. So if you put a full nested chain on
  the generate line (`p p > t t~, (t > w+ b, w+ > ...)`), MadSpin cannot attach an additional decay layer;
  you must either do ALL decays on the generate line OR leave the resonance stable on the generate line and
  let MadSpin do the (possibly nested) decay. The chain-decay generate-line *syntax itself* is the chain-decay
  slice; this page owns only the MadSpin-side splice rule and the abort.

## Card vs generate-line: which path you are on
- generate-line chain (`generate p p > t t~, t > w+ b`): decay attached at generation; NO MadSpin needed; the
  comma is in the banner's proc line. (chain-decay slice owns the generate-line semantics.)
- MadSpin card `decay t > w+ b, w+ > all all`: decay attached POST-generation by MadSpin onto stable-particle
  LHE; the comma is in the card, assembled at :2862 and spliced at :3021/3024/3033. Spin correlation preserved
  per spinmode (full/madspin) — the preservation algorithm is decay.py internals.

## Cautions
- A nested chain placed on the GENERATE line forecloses a later MadSpin decay of the inner products (hard
  Exception at decay.py:3028) — diagnose the "too much decay at MG level" abort as this seam.
- The `QCD=99` default (:2857) is appended to ANY decay branch lacking an explicit `=` coupling order; a user
  who wants to restrict the decay coupling order must write it in the card decay line, and `do_decay` warns
  (interface_madspin.py:431-432) that a coupling-order restriction is not tied to a specific BR (cross-section
  may then use the wrong BR) under full/madspin.
- `reorder_branch`'s swap only normalizes the *order* of products; it does not validate the chain. An invalid
  sub-decay surfaces later at ME generation, not at do_decay.
- A `^2`/`NP^2==N` in a card decay line is NOT caught by `do_decay` (only `=` warns); it surfaces at full-ME
  build as "Decay processes cannot specify squared orders constraints" (madgraph_interface.py:3303) — the
  shared decay-chain guard, same as typing the squared order on a generate-line chain. Diagnose that error
  under MadSpin as "squared order in a decay branch", and route the physics of squared-order isolation to the
  coupling-order (tree) / nlo-syntax (NLO) slice — the interface only relays the branch to the chain parser.

## Gaps / out of slice
- BW off-shell sampling of the spliced chain, spin-correlation preservation across the chain, the decay-ME
  generation that consumes the `generate ...` command — MadSpin internals (decay.py), out of slice.
- The generate-line chain-decay grammar (parenthesized syntax, coupling orders on the generate line) is the
  chain-decay slice.

## Source-grounding note
Comma-count branches and the reorder swaps are probe-confirmed at runtime (inline `get_proc_with_decay` and
`reorder_branch` calls, sm model, 3.7.1): 0c/1c splice strings and the paren-Exception reproduced exactly,
matching test_madspin.py:115. The assembly/coupling-default sites (:2856-2862), the `@`-correlation grammar
(:2850-2881), and the prune drop/raise (:2833-2838) are source-visible. The card-line
boundary (`import_command_file`:1691 readlines/per-line; `precmd`:1009 `#`/`\`/`;`-split, no comma) is
source-visible in extended_cmd.py; the comma-survives-into-one-string consequence is the read of those two
together (not separately probed — flagged for a probe-candidate below). The squared-order rejection
(do_decay non-inspection at interface_madspin.py:431-432, splice at decay.py:2869/2883, shared guard at
madgraph_interface.py:3301-3304, predicate base_objects.py:3576-3582) is source-visible; the end-to-end
"card `decay` with `^2` -> that specific error" is a read of the chain (not runtime-probed — probe-candidate).
