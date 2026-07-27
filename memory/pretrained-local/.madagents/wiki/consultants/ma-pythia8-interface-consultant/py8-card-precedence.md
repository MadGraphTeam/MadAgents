---
description: User-vs-MadGraph precedence on the PY8 card — the four-setter ladder (userSet/systemSet/MadGraphSet/defaultSet) + write-time vetoParamWriteOut, seeded by read(setter='user'). The rule for any "does my pythia8_card.dat value survive?" question.
---

# PY8 card precedence: who wins, user or MadGraph

## Principle
Every value in the operative PY8 card got there through one of four setters, and the
collision between a user's `pythia8_card.dat` entry and MadGraph's auto-derivation is
resolved entirely by **which setter MG calls and whether it passes `force=True`**.
To answer any "if I set param X in pythia8_card.dat, does MG override it / does it reach
PY8?" question, do NOT reason from the param's meaning — trace the setter call site.

This catches params none of the per-facet pages name: the rule is mechanical (find the
setter + force flag + any veto), so it applies equally to a future MLM/CKKW knob, a PDF
override, a shower switch — anything MG might auto-derive over a user value.

Boundary: governs only what MG **writes** to the card on the LO `do_pythia8` path. It does
NOT govern PY8's own runtime interpretation (out of slice). The sibling generalization
interface-divergence-main164-vs-old.md governs a *different* write-time transform
(interface name-translation / SysCalc disabling) — that one is user-independent and keyed
on `use_mg5amc_py8_interface`; THIS one is keyed on user_set vs system_set. A full "what's
in the card" answer often needs both: precedence decides the value, interface decides the
name/whether-it's-stripped.

## The ladder (`banner.py:2074-2110`)
Seeded by composition: `do_pythia8` reads `pythia8_card_default.dat`, then overlays the
operative `pythia8_card.dat` with `read(setter='user')` (`madevent_interface.py:4666-4669`;
`PY8Card.read(file_input, setter='default')` def at `banner.py:2462`). The overlay tags every
user-edited param as `user_set`. That tag is what the rest of the ladder respects.

- `userSet` (`:2074`): sets, marks `user_set`, drops from `system_set`. (The read overlay uses this.)
- `systemSet` (`:2085`): sets only if `force` OR not `user_set`; marks `system_set`.
- `MadGraphSet` (`:2096`): sets if absent OR (`force` OR not `user_set`) (`:2103`). **Raises only when the param is already present AND `user_set` AND not `force`** (`:2106-2107`) — not merely "already set".
- `defaultSet` (`:2109`): unconditional, leaves `user_set` untouched.
- `vetoParamWriteOut` (`:2080`): adds to `params_to_never_write` — suppresses writeout at `write` time *even if the value was set*. Orthogonal to the ladder: a param can be set-and-vetoed.

## How MG uses these (the call-site catalogue)
- **Guarded auto-derivation** (user wins): `MadGraphSet` without `force`, often gated on a
  sentinel (`==-1.0`). E.g. `JetMatching:qCut` set to `<factor>*xqcut` (factor read fresh at `:4409` — see matching-param-handoff.md) only `if ['JetMatching:qCut']==-1.0`
  (`:4408-4409`, but that *call* passes `force=True` — see next). Sentinel-then-set is the common idiom.
- **Forced override** (MG wins regardless of user): `MadGraphSet(..., force=True)`. E.g.
  `HEPMCoutput:file` forced to `<tag>_pythia8_events.hepmc` (`:4362`), qCut auto (`:4409`),
  nJetMax/TMS/qCutList/tmsList autos all `force=True`. When MG intends to win it says so.
- **Non-clobbering default**: `defaultSet`. E.g. fifo path `defaultSet('HEPMCoutput:file', ...)`
  (`:4373`/`:4388`) — explicitly "not to overwrite the current userSet status".
- **Set-but-suppressed**: `vetoParamWriteOut`. MLM vetoes `Merging:TMS/Process/nJetMax`
  (`:4403-4405`); CKKW vetoes `JetMatching:qCut/doShowerKt/nJetMax` (`:4485-4487`); the default
  (no-merging) branch vetoes BOTH families (`:4570-4575`). This is why e.g. a user `Merging:Process`
  value does not appear in an MLM-run card even though the user set it.

## Worked answers (the rule applied)
- "I set `JetMatching:qCut` in pythia8_card.dat — does MG's `<factor>*xqcut` auto-derivation override it?" The auto
  fires only when qCut is still `-1.0` (`:4408`); a user value is not -1.0, so the auto branch is
  skipped and the user value stands. (The `force=True` on `:4409` only matters inside the taken branch.)
- "Does the fifo machinery clobber my explicit `HEPMCoutput:file`?" No — `defaultSet` (`:4373`).
- "Why is my `Merging:Process` missing from the written MLM card?" `vetoParamWriteOut` at `:4404`.
- "Can MG ever overwrite a value I set?" Yes — any `force=True` call site (e.g. `HEPMCoutput:file`
  `:4362` is rewritten to the canonical tag name regardless of user input).

## Instances this lifts from
py8-card-defaults.md (setter methods, abstract); matching-param-handoff.md (individual veto/force
calls in MLM/CKKW/default branches); hepmc-output-and-paths.md (defaultSet-for-fifo as a one-off).
None states the precedence rule itself or connects the abstract setters to the concrete force/veto
call sites. The principle: trace the setter + force + veto, don't reason from the param's meaning.
