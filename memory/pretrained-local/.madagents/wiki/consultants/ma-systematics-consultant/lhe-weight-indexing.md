---
description: LHE weight indexing convention — initrwgt header weight-id-to-description map, per-event <rwgt><wgt id> blocks, id allocation (get_id/start_id), weight_format, mg_reweighting includeIdInWeightName.
---

# LHE weight indexing convention

How variation/reweight weights are keyed in the LHE banner header vs per-event blocks.

## Header: `<initrwgt>` (banner)
Lives in the LHE banner. Contains `<weightgroup>` blocks, each holding `<weight id="NAME" ...> description </weight>` lines. The `id` is the key; the body text is the human description.
- Systematics groups (sys.py:603-738): `<weightgroup name="Central scale variation" combine="envelope">`, `"Emission scale variation"` (ALPS), per-PDFSET groups with `combine=<errorType>`. Each weight tag carries `MUR=` `MUF=` `[ALPSFACT=]` `[DYN_SCALE=]` `PDF=` attributes (`get_wgt_tag`, sys.py:769-781).
- Reweight group (ri.py:871-876): `<weightgroup name='mg_reweighting' weight_name_strategy='includeIdInWeightName'>` with `<weight id='rwgt_<id>'>` entries; the id encodes the param-card diff.
- EW Sudakov reweight (ri.py:532-535, 967-971): derives Sudakov weight ids from existing scale-weight ids — header id `X` → `'2'+X[1:]` (e.g. `1001`→`2001`); per-event id ending `NN` → `'20'+NN`; header body `<diff>scale_10NN_sud`. See `ew-sudakov-reweight` page.

## Per-event: `<rwgt>` block (`parse_reweight`, lhe_parser.py:1486-1504)
- Pattern: `<wgt id='NAME'>VALUE</wgt>` inside `<rwgt>...</rwgt>`. Parsed into `reweight_data={id:float}` and `reweight_order=[id,...]` preserving file order.
- Written back (lhe_parser.py:2615-2621): `<rwgt>` block joining `reweight_order` entries that exist in `reweight_data`. Order preserved; any data-keys not in order appended.
- **The per-event `<wgt id=...>` must match an `<weight id=...>` in the header `<initrwgt>` to be interpretable.** The id is the join key between header description and event value.

## id allocation (`get_id`, sys.py:784-795)
- `start_id` option (`--start_id=`) overrides — returns `int(start_wgt_id)`.
- Else if `initrwgt` present: parses existing `<weight id='...'>`, takes `max(numeric ids)+1` so new weights don't collide.
- Else starts at a base value (read at sys.py:795).
- New Systematics weights numbered sequentially from this base (`run()`, sys.py:399 builds ids via `get_wgt_name(*args, cid=lowest_id+i)`).

## weight_format / weight_info (`get_wgt_name`/`get_wgt_info`, sys.py:740-767)
- `--weight_format=` : a python `%`-format string with keys `mur,muf,alps,pdf,dyn,id` — customizes the weight `id` NAME. Default: the bare integer `cid`.
- `--weight_info=` : `%`-format with same keys plus `s`(space)/`n`(newline) — customizes the description body. Default: auto MUR/MUF/alpsfact/dyn_scale_choice/PDF string.

## remove_wgts / keep_wgts (`is_wgt_kept`, sys.py:344-379)
- `--remove_wgts=` accepts `all`, `min,max` ranges, names, or regex-ish patterns (chars `*?.([+\`). `--keep_wgts` takes precedence. `remove_old_wgts` (sys.py:381-388) deletes matching ids from the event's parsed reweight data + order before adding new ones.

## Are ids arbitrary or a scale/PDF convention? (doc-myth: "1001")
- **systematics.py LO path: ids are sequential integers, they do NOT encode the scale/PDF combo.** `get_wgt_name` default is the bare integer `cid` (sys.py:745); `write_banner` starts at `cid=get_id()` and does `cid+=1` per weight (sys.py:606,693). The scale/PDF combination is carried in the `<weight>` tag ATTRIBUTES `MUR/MUF/[ALPSFACT]/[DYN_SCALE]/PDF` (`get_wgt_tag`, sys.py:769-781), NOT in the numeric id. So the id is a join key, not a scale index.
- **The `1001` numbering in docs is NOT from systematics.py.** `get_id` defaults to a base (fresh banner, sys.py:795) or `max(existing ids)+1` (sys.py:793) or `--start_id`. The `1001`-based scheme is the **NLO-integrator convention** (amcatnlo's slice — Fortran reweight emission writes ids in a scale/PDF-block scheme). It surfaces in my slice only as a hardcoded FALLBACK: EW Sudakov reweight seeds `rwgt_dict['1001']=orig_wgt` when the event has no existing `<rwgt>` block (`ri.py:1354`), then derives Sudakov ids `'20'+ending` (ri.py:1358-1361). Do not claim systematics.py emits 1001.

## Per-event write format (verbatim)
- `<wgt id='%s'> %+13.7e </wgt>` (lhe_parser.py:2620), joined inside `<rwgt>\n...\n</rwgt>` (2619). Value is fixed 7-digit sci-notation.

## Cautions
- A duplicate id (e.g. reusing `--start_id` over existing weights) will overwrite/collide; `get_id` normally guards by scanning existing ids but `--start_id` bypasses that guard.
- The header description for an id and the per-event value live in different parts of the file; an id present in events but absent from `initrwgt` carries a value with no description.
