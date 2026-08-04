---
description: MadGraph-side MadSpin invocation — launch -M flag, do_decay_events dispatch, card templating shortcuts, default madspin_card
---

# How MadGraph invokes MadSpin

## launch flow: the -M flag
`MELauncher.launch_program` at `$MADGRAPH_INSTALL/madgraph/interface/launch_ext_program.py:614`.
Builds a `generate_events <name>` command; if `self.madspin` is set, appends ` -M ` (:690-691). Also ` -R ` for reweight (:688), ` --cluster`/`--nb_core` for run mode (:678-681).

## do_decay_events — the dispatch into MadSpin
`$MADGRAPH_INSTALL/madgraph/interface/common_run_interface.py:4169`.
- `-from_cards` + no `madspin_card.dat` -> silent return (:4173). So MadSpin only runs if a card is present.
- imports `MadSpin.decay` and `MadSpin.interface_madspin` (:4184-4185); needs `mg5_path` set when run from a bare MadEvent dir (:4178-4182).
- unless `-from_cards`/`-f`: `ask_edit_cards(['madspin_card.dat'])` lets the user edit the card (:4194-4196).
- `madspin_cmd = interface_madspin.MadSpinInterface(args[0])` (:4203) — constructor calls `do_import(args[0])` immediately (interface :169-171).
- **option handoff** (two steps): first a bulk `madspin_cmd.mg5cmd.options.update(self.options)` copies ALL of MadGraph's options onto the inner mg5cmd's options dict (:4205); then a loop re-applies only the **string-valued** ones via `set %s %s --no_save` so their `post_set` validators fire (:4206-4208). Non-string options ride only on the bulk update, never through `set`. `madspin_cmd.cluster`/`mother` wired (:4209-4210).
- runs the card as a command file: `madspin_cmd.import_command_file(path)` where path = `<me_dir>/Cards/madspin_card.dat` (:4214-4216).
- run-name dir: from `madspin_cmd.me_run_name` (set by card's `launch -n`) else `<run_name>_decayed_<i>`; collisions get `_<i>` suffix (:4217-4229).
- moves `<input>_decayed.lhe[.gz]` into `Events/<new_run>/` (:4234-4247); if absent -> `logger.error("MadSpin fails to create any decayed file.")` and return (:4244).
- results bookkeeping: `nb_event * efficiency`, `cross = madspin_cmd.cross`, error includes `cross * err_branching_ratio` (:4251-4265).
- banner: appends the madspin card to the banner and writes `<run>_<tag>_banner.txt` (:4268-4271).

Trigger sites (madevent_interface.py): `decay_events -from_cards` is exec'd from generate_events post-steps and the launch switch (e.g. :2375, :2591, :2657, :7120). The launch-menu switch itself (allowed-mode table, ON/OFF default, switch->`set spinmode` card writer) is its own page — see madspin-launch-switch-gate.

## Card templating (what MG writes for MadSpin)
- default template: `$MADGRAPH_INSTALL/Template/Common/Cards/madspin_card_default.dat`. Ships commented hints (seed, Nevents_for_max_weight, BW_cut, spinmode) plus an active `set max_weight_ps_point` line (read the shipped value fresh from the template), example `decay t > w+ b ...` lines, and `launch`.
- `init_madspin` (common_run_interface.py:5359) registers two `set`-shortcuts on the card:
  - `spinmode VALUE` -> `add madspin_card --before_line="launch" set spinmode %(0)s` (:5365).
  - `nodecay` -> `edit madspin_card --comment_line="decay"` (removes all decay lines) (:5366).
  - help (:5368-5371): spinmode full|none|onshell. (Help text omits 'madspin' default.)
- `do_add_card`/decay editing for associated particles around :7250 lets `decay PARTICLE ...` lines be injected into the card.

## MG-side `do_decay` — the card-editing `decay` command (common_run_interface.py:7249)
This is the MG-side `do_decay` named in my card (distinct from `do_decay_events` :4169, the launch dispatch). Edits `madspin_card.dat` in place at the card-edit prompt:
- guards: aborts with warning if no `madspin_card.dat` present (:7254-7256) or if `>` absent from the line (:7258-7260).
- `decay PART > ... --add` (or `-add`): **accumulates** — appends a new `decay` line, inserted before the first `launch` (`text.replace('launch', "\ndecay ...\nlaunch\n",1)`) or appended if no `launch` (:7262-7271).
- `decay PART > ...` **without** `-add`: **replaces** — first regex-strips ALL prior `decay PART > ...` lines for that particle (`decay_pattern.sub('',text)`, :7278-7280), then inserts the new one before `launch`. So a plain `decay t > w+ b` overwrites existing top decays; `--add` is needed to keep multiple decay channels for one particle.
- writes the file and `reload_card`s it (:7286-7288).

## `set madspin_card` at the ME card-edit prompt (common_run_interface.py:6069-6077)
The generic `set` command rejects MadSpin-option edits: `set madspin_card default` copies `MS_default` over `madspin_card.dat` (:6070-6072), but ANY other `set madspin_card ...` logs "Command set not allowed for modifying the madspin_card. Check the command \"decay\" instead." and returns (:6075-6076). So MadSpin options (BW_cut, spinmode, seed, ...) are NOT settable through the ME prompt's generic `set` — they flow only via the card body, the `spinmode`/`nodecay`/`decay` shortcuts, or direct card edit.

## Banner handoff format — the madspin block (round-trip)
The decayed LHE records the MadSpin run as a banner block; this is the handoff format MadGraph
both writes and reads back.
- WRITE (interface_madspin.py): all three launch paths build the block from `self.history`
  (the accumulated `extended_cmd.Cmd` command lines, populated at `extended_cmd.py:1044`) with the
  resolved seed inserted at position 0 (`self.history.insert(0,'set seed %s')`), then
  `text='\n'.join(...)` and `self.banner.add_text('madspin', text)`:
  - full/madspin path: :662 (seed insert), :669 (text), :670 (`add_text('madspin')`).
  - run_bridge: :898 (seed insert) / :907 (`add_text('madspin')`).
  - run_onshell: :1437 (seed insert) / :1446 (`add_text('madspin')`).
  So the block is the literal MadSpin command sequence (set/define/decay/launch), seed-pinned.
- banner tag registry (`$MADGRAPH_INSTALL/madgraph/various/banner.py`):
  - `'madspin': 'madspin_card.dat'` in the tag->cardname map (:133).
  - `banner.add(path)` filename-detection maps `'madspin_card' in card_name` -> tag `'madspin'`
    (:484-485, used by the MG-side banner-append at do_decay_events :4268-4271).
  - `add_text(tag, text)` lowercases the tag and stores `self[tag.lower()] = text` (:499-516);
    `'madspin'` is already canonical (unlike `param_card`->`slha`, `run_card`->`mgruncard`).
- READ-BACK / re-decay guard: `do_import` aborts if `'madspin' in self.banner` (interface_madspin.py
  :240) — "This event file was already decayed by MS ... not possible to add a second decay". So the
  presence of this exact block makes a decayed file non-re-decayable. This is the round-trip: the
  block written at launch is the same key the next do_import keys on to refuse a second pass.

## Custom card path -> content-based type auto-detection (`detect_card_type`, common_run_interface.py:~1250-1290)
A card supplied by path is typed by CONTENT, not filename, via `detect_card_type` (the copy-to-right-location that follows is ask_edit_cards / keep_cards machinery — ma-interface/launch slice). The madspin-relevant branch (:1276-1290):
- `'launch' in text` AND `'madspin' in text` -> `madspin_card.dat` (:1279-1280).
- `'launch' in text` AND a bare `decay` line (`re.search(r"(^|;)\s*decay", fulltext, re.M)`) -> `madspin_card.dat` (:1281-1284).
- `'launch'` with only a `set decay ...` (no bare `decay` line) -> `reweight_card.dat` (:1285-1288).
So MadSpin vs reweight cards are disambiguated by (a) the literal `madspin` keyword or (b) a bare `decay X > ...` line vs `set decay`. This is why a custom `/path/to/mycard.dat` carrying `launch` + `decay ...` is auto-recognised as a MadSpin card. Both cards share `launch`/`decay`/`set` tokens — the `^decay`-vs-`set decay` regex is the tiebreak. (Confirms the "auto-detect card type from content" claim; the detection is source-visible, the subsequent copy is cross-slice.)

## Cautions
- Per-option handoff (:4206-4208) only forwards **string** options from MadGraph's config; it sets them on the inner `mg5cmd`, not on `MadSpinOptions` directly — MadSpin-specific options come from the card.
- If no `madspin_card.dat` exists under `-from_cards`, MadSpin is silently skipped (:4173) — not an error.
- The madspin banner block is seed-pinned to the LAUNCH-time seed (pre-increment); `options['seed']`
  read after launch is higher (per-PDG increments, see madspin-option-resolution-staging).

## Gaps
- NLO + MadSpin (amcatnlo `decay_events`) is the amcatnlo slice.
- compute_widths feeding widths to MadSpin is the madwidth slice.
