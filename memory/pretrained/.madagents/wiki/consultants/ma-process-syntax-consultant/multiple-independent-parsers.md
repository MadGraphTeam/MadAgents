---
description: Process-line syntax is parsed by MULTIPLE independent tokenizers (extract_process, split_process_line, get_final_part, extract_particle_ids/define, Switcher) that re-implement the same idioms and DIVERGE — a token valid in one is not guaranteed valid in another.
---

# Multiple independent process-line parsers diverge (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py` + `master_interface.py`.

## The principle
There is no single shared process-line tokenizer. At least five code paths each re-implement the parse idioms independently. A syntax change to `extract_process` does NOT propagate to the others, and a token accepted by one parser can be REJECTED by another. When asked "does syntax X work?", the answer depends on WHICH command/path consumes it — always name the path.

## The four recurring idioms and where each is duplicated

1. **Spacing-normalisation** (`space_before` regex, inserts spaces around `[ ] / , $ > |`):
   - extract_process **4836** and extract_process_type/Switcher (`master_interface.py` **169**) — *byte-identical* regex, two copies.
   - `do_define` (**3538-3540**) uses a DIFFERENT, narrower normalisation: only `=`, `|`, `/` get spaced — NOT `> , $ [ ]`. So a `define` line is tokenized by a weaker normaliser than a process line.
   - `get_final_part` does NO normalisation (relies on caller passing a spaced `> ` — regex 5574 keys on the space).

2. **`@N` process-number strip** (`proc_number_pattern`):
   - extract_process **4844** `r"^(.+)@\s*(\d+)\s*(.*)$"`.
   - split_process_line **5486** — same regex (MadSpin/reweight path).
   - extract_decay_chain_process **5666** — VARIANT `r"^(.+)@\s*(\d+)\s*((\w+\s*\<?=\s*\d+\s*)*)$"` (also captures trailing orders; the captured orders land in the procdef's `'overall_orders'` key, not `'orders'`). See decay-chain-comma-handoff.md for the in-context mechanism. *Chain-decay slice owns this site's semantics* — flagged here only as a divergent copy.

3. **Leading-digit duplication / strip** (`X[0].isdigit()` → count or strip-and-retry):
   - leg loop **5213-5214**: `2j` → `duplicate, part_name = int(part_name[0]), part_name[1:]` → emits N copies of the leg.
   - `{pol}` spin lookup **5103-5104**: strip-and-retry (duplication-count name).
   - get_final_part **5583-5587**: strip-and-retry into name2pdg/multiparticles.
   - **NOT** in `extract_particle_ids` (5614 only handles plain `isdigit()` signed pids) — so `define`/`/`/`$`/`> >` filter positions do NOT understand the duplication idiom.

4. **Name → pid resolution** (three different mechanisms):
   - leg loop **5207** + extract_particle_ids **5605**: `model['particles'].get_copy(name)` — matches name OR antiname, sets `is_part`, has PDG-int fallback.
   - get_final_part **5521**: `model.get('name2pdg')` dict — antiname resolves (`u~`→-2) but NO `is_part` flag, NO PDG-int fallback.
   - digit branch: bare `int(name)` against `particle_dict`.

## Probe-confirmed divergence (v3.7.1, sm)
The same token `2j` (two jets, leading-digit duplication):
- `extract_process('e+ e- > 2j')` → **4 legs** (e+, e-, j, j). Accepted.
- `extract_particle_ids(['2j'])` → **`InvalidCmd: No particle 2j in model`**. Rejected.
- `define myx = 2j` → **`InvalidCmd: No particle 2j in model`** (define routes through extract_particle_ids). Rejected.

So `2j` is valid in a process-line final state but invalid in a `define` body or a filter — purely because they hit different parsers. This is the generalization: not a `2j` quirk, but a *class* of "valid here / invalid there" divergences.

## Why this matters / how to apply
- "Does syntax X work?" has no path-independent answer — qualify by command (`generate`/`add process` leg loop vs `define`/filter vs MadSpin/reweight vs the Switcher routing parse).
- A bug fix or feature in `extract_process` is NOT automatically in split_process_line / get_final_part / extract_particle_ids / the Switcher. Predict skew, not parity.
- get_final_part returns a *set* of pids (loses multiplicity/order); it answers "which species are final" for MadSpin, not "how many legs".

## Instances (kept, carry the per-path detail)
- extract-process-orchestration.md (leg loop pipeline), particle-name-resolution.md (get_copy + digit idiom), polarization-parse-step.md ({pol} strip-retry), define-command.md (extract_particle_ids), madspin-reweight-parse-helpers.md (split_process_line + get_final_part), switcher-predispatch-layer.md (second bracket parser + space_before copy), decay-chain-comma-handoff.md (extract_decay_chain_process @N variant + per-segment extract_process fan-out + helper-survival divergence).
