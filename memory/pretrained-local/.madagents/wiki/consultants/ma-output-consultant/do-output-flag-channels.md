---
description: do_output flag-routing topology — one CLI arg fans into up to four channels (local bools / flaglist / line_options->output_options / raw args), built at different parse points so an arg-mutation reaches some channels but not others (the ordering trap) (MG5_aMC v3.7.1)
---

# do_output flag channels and the parse-ordering trap

The generalization behind no-helrecycling-two-mechanisms.md and eps-jpeg-two-gates.md:
a single `output` CLI arg does NOT flow to one place. It fans into up to FOUR
independent channels with different consumers, and the channels are CONSTRUCTED at
different points in the `do_output` parse — so an arg that mutates `args` mid-parse
reaches the channels built *after* the mutation but not those tested *before* it.
This page is the routing topology; what each consumer DOES with its channel value is
the instance pages / other slices.

File: `$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `do_output` flag
block `:9116-9145`.

## The four channels (build order matters)
1. **Local bools** — `noclean = '-noclean' in args` (`:9116`), `force` (`:9117`),
   `nojpeg` (`:9118`, also set True by `--noeps=True` at `:9119-9120`). Consumed
   directly in `do_output`; `nojpeg` is passed to BOTH `export()` (`:9345`) and
   `finalize()` (`:9348`).
2. **flaglist** — a list built `:9121-9142` by membership TESTS on `args`:
   `'store_model'` (`--postpone_model`, `:9123`), `'no_helrecycling'`
   (`--hel_recycling=False`, `:9125`), `'me_exporter=<n>'` (`:9135`),
   `'no_helrecycling'` again from spin>3 (`:9141`). Passed ONLY to `finalize()`
   (`:9348`). NOT seen by the exporter constructor.
3. **line_options** — `dict` of every `--k=v` (or `--k`->True) built at `:9144`
   from `args`, AFTER all the arg-mutations. Passed as `cmd_options` to
   `ExportV4Factory`/`ExportCPPFactory` (`:9291-9316`) -> `opt['output_options']`
   (export_v4.py:9870). This is the exporter's channel.
4. **raw args** — the (mutated) `args` list itself is passed positionally to
   `export()` (`:9345`, 4th arg). A 4th consumer.

So: flaglist -> finalize; line_options -> exporter; nojpeg -> both; args -> export.
A flag answers "does it reach the exporter / finalize / both?" by which channel(s)
it lands in.

## The ordering trap (the load-bearing subtlety)
The flaglist membership tests run at `:9123/:9125/:9135/:9141`. The line_options dict
is built at `:9144`. Two arg-mutations happen IN BETWEEN:
- `:9132` `args.append('--hel_recycling=False')` when `--me_exporter=` present.
- `:9142` `args.append('--hel_recycling=False')` when spin>3.

Because line_options is built at `:9144` (after both appends) but the
`no_helrecycling` flaglist test ran at `:9125` (before them):
- An arg appended at `:9132`/`:9142` DOES enter `line_options` (-> exporter opt).
- It does NOT enter `flaglist` (the `:9125` test already ran).

Verified: there is NO `args.append` anywhere between `:9145` and the factory/finalize
calls (grep-confirmed `:9144-9260` empty of `args.append`), so line_options is the
complete post-mutation snapshot and flaglist is frozen at the pre-`:9132` state plus
its own direct appends. The trap is purely the `:9125`-test-above-`:9132`-append
ordering.

## Consequence for an arbitrary flag --X
- A user-typed `--X=v` reaches BOTH line_options (always, via `:9144`) and flaglist
  ONLY if there is an explicit membership test for it in `:9121-9142`.
- A flag that another flag *self-appends* (like `--hel_recycling=False` appended by
  `--me_exporter`/spin>3) reaches line_options but NOT the flaglist gate that tested
  for it earlier. This is why `--me_exporter=cpp` turns the exporter recycling opt off
  (line_options) yet the finalize `no_helrecycling` flaglist gate still fires (P1N
  routines emitted) — see no-helrecycling-two-mechanisms.md.
- The recycling state of an output is therefore the PAIR (flaglist gate, exporter opt),
  and they diverge exactly under arg-self-appends.

## The two instances (each is this principle on one flag pair)
- **no-helrecycling-two-mechanisms.md** — `--hel_recycling`/`--me_exporter`/spin>3:
  Mechanism 1 = flaglist `no_helrecycling` -> finalize P1N gate (`:9707`);
  Mechanism 2 = line_options `hel_recycling` -> exporter opt. `--me_exporter` self-appends
  so it hits Mechanism 2 only (the trap).
- **eps-jpeg-two-gates.md** — `--noeps`/`-nojpeg`: EPS gate reads
  line_options/output_options `noeps` (string, generate_subprocess_directory);
  raster(PNG) gate reads the `nojpeg` flaglist (finalize). `--noeps=True` ALSO sets the
  local `nojpeg` bool (`:9119-9120`) so it closes both; `-nojpeg` is not a `--k=v` so it
  never enters output_options and touches only the flaglist/local-bool channel.

## Why this catches more than the instances
A new or rarely-used do_output flag (or a programmatic caller, or a plugin that injects
an arg) inherits this topology automatically: to predict where `--foo` lands you read
the channel map, not the helrecycling/eps pages. The instances answer two specific flag
pairs; this page answers the routing question for ANY flag, including ones with no
dedicated page. The boundary: this page is the routing topology + ordering rule only —
what each consumer DOES with the value (the P1N algorithm, the gs raster device, the
exporter opt semantics) lives in the instance pages and other slices.

## Caution
- The `:9125`-vs-`:9132` ordering is the whole trap; if a future version moves the
  line_options build above the arg-appends, or moves a flaglist test below them, the
  divergence flips. Re-read `:9116-9145` for the current build order rather than trusting
  this ordering verbatim — it is the one thing that makes the instances behave as they do.
