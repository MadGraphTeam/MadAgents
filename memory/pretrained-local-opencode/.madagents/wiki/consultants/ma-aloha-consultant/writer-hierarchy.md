---
description: ALOHA multi-target writer hierarchy (aloha_writers.py) — WriteALOHA base, WriterFactory dispatch, Fortran/QP/Loop/C++/GPU/Python emitters, HELAS argument layout.
---

# Writer hierarchy (aloha_writers.py)

Cites `$MADGRAPH_INSTALL/aloha/aloha_writers.py` v3.7.1.

## Base + dispatch
- `WriteALOHA` (`:28`) — base emitter. `__init__` (`:39`) sets `momentum_size` (2 normal, 4 if `aloha.loop_mode`, `:40-43`) and `type_to_size` map of wavefunction array sizes by spin-letter (`:45-49`): default `S:3, T:18, V:6, F:6, R:18`; FD gauge (`unitary_gauge==3`) bumps `S:7, V:7` (`:47`). Builds routine name via `get_routine_name` (`:53`); `outname`/`outgoing` track the off-shell leg, flipping parity for conjugate legs (`:71-73`).
- `pass_to_HELAS` (`:81`) — maps a Lorentz index to its Fortran array slot: single index → `index + start + momentum_size` (`:86`); reads `lorentz_ind` (or per-`SplitCoefficient` for loops, `:88-97`).
- Generic emit hooks: `get_header_txt`/`get_declaration_txt`/`get_momenta_txt`/`get_foot_txt`/`define_argument_list` (`:107-249`); object-tree writers `write_obj`, `write_MultVariable`, `write_MultContainer`, `write_obj_Add` (`:286-385`); `make_call_list`/`make_declaration_list` (`:404`/`:432`).
- `WriterFactory` (`:2561`) / `__new__` (`:2563`) dispatches on `(data.expr type, language, tags)`:
  - `SplitCoefficient` expr → loop writer (asserts fortran): `ALOHAWriterForFortranLoopQP` if `'MP' in tags` else `ALOHAWriterForFortranLoop` (`:2569-2574`).
  - `fortran` → `ALOHAWriterForFortranQP` (MP) / `ALOHAWriterForFortran` (`:2575-2579`).
  - `python`/`cpp`/`gpu|cudac` → respective writers (`:2580-2585`); a `WriteALOHA` subclass passed as `language` is used directly (`:2586`).

## Subclasses
- `ALOHAWriterForFortran` (`:448`) — primary target. `.extension`/`.type_to_variable`; `get_fct_format` (`:466`), `get_header_txt` (`:499`), `get_declaration_txt` (`:523`), `get_momenta_txt`/`get_one_momenta_def` (`:612`/`:689`), `change_var_format`/`change_number_format` (`:730`/`:751`), `define_expression` (`:788`), `define_symmetry` (`:931`), `write_combined` (`:954`).
- `QP` mixin (`:1041`) + `ALOHAWriterForFortranQP` (`:1050`) — quad/double-precision variant (`mp_` prefixing, real*16 / complex*32).
- `ALOHAWriterForFortranLoop` (`:1055`) — loop coefficients (`SplitCoefficient`); own `define_expression` (`:1068`), `get_loop_argument` (`:1282`), loop-specific arg list (`:1189`). `ALOHAWriterForFortranLoopQP` (`:1318`).
- `ALOHAWriterForCPP` (`:1429`) — emits `.cc`+`.h` (`get_h_text` `:1836`, `write_combined_cc` `:1859`).
- `ALOHAWriterForGPU(ALOHAWriterForCPP)` (`:2004`) — CUDA/GPU; overrides headers + test-variant object writers (`:2055`,`:2104`).
- `ALOHAWriterForPython` (`:2179`).
- `Declaration_list(set)` (`:2531`) — dedups variable declarations.

## HELAS-call argument convention
- `make_call_list` (`:404`) builds the routine's argument names as `<spin-letter><leg-number>` (e.g. `F1`, `V2`, `S3`), iterating `self.particles` and SKIPPING the off-shell leg (`:415-416`). For a conjugate (`C<n>`-tagged) fermion leg the adjacent pair is swapped: leg at a `C` position emits its partner's name (`:412`,`:418-424`) — the Majorana flow swap surfaces in the call args, not just the kernel.
- `make_declaration_list` (`:432`) emits one declaration per leg via `declare_dict[spin] % (index+1)`; sizes come from `type_to_size`/`declare_dict` (gauge/loop-mode dependent).

## Naming helpers
- `get_routine_name(name,outgoing,tag,abstract)` (`:1324`) and `combine_name` (`:1351`, hashes long combined names via `myHash` `:1354`).

## Why this matters
One symbolic kernel → many targets. The factory is the single switch; tags (`MP`, loop via expr type) pick precision/loop flavor. Array sizes (`type_to_size`) and `momentum_size` are gauge-/loop-mode dependent, so the same Lorentz routine emits different layouts under FD gauge or loop mode — verify the active gauge before reasoning about a routine's argument layout.
