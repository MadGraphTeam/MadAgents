---
description: Invented post-> operators (/=) and glued-paren tokens ((b) fall through to particle-name resolution and raise "No particle X in model" loud at parse time, no output dir; the LOUD members of the "syntax-accepted != amplitude-scope" trap family. Covers the space_before tag-set (= and ( not normalized), the two distinct raise sites (5242 leg loop / 5617 extract_particle_ids), the history[-1] attribution, and the paren balance-vs-resolution branch.
---

# Loud parse-rejection traps: fall-through to particle-name resolution (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`. These are the **LOUD** members of the "syntax accepted != amplitude scope" trap family — they fail at parse/tokenization with `InvalidCmd`, **no output dir is created**. Contrast the SILENT-fail members (a filter/chain that parses but quietly drops amplitudes), which live in diagram-filter / chain-decay slices.

## Root cause shared by both: the space_before tag-set is narrow
The spacing-normalisation regex (`extract_process`, **4836**):
```
space_before = re.compile(r"(?P<carac>\S)(?P<tag>[\[\]/\,\$\>|])(?P<carac2>\S)")
```
The tag set is exactly `[ ] / , $ > |`. It does **NOT** include `=` or `(`. And it requires `\S` on BOTH sides — a tag already adjacent to a space is not normalised. So `=` and `(` are never given their own token boundaries; they stay glued to whatever they touch and ride into particle-name resolution as part of a token.

## Two distinct `No particle %s in model` raise sites
Same message string, different code paths — which one fires depends on whether the bad token is in a FILTER position or a LEG position:
- **Leg loop, line 5242** — `raise self.InvalidCmd("No particle %s in model" % part_name)` when a process-leg token resolves to nothing (not multiparticle, get_copy miss, first char not a digit). See particle-name-resolution.md.
- **`extract_particle_ids`, line 5617** — `raise self.InvalidCmd("No particle %s in model" % part_name)` when a FILTER substring (`/`, `$`, `$$`, `> >`) or a `do_define` RHS token resolves to nothing. See extract-particle-ids-or-expansion.md. `extract_particle_ids` is at 5591; the `/` forbidden-particle position calls it at 5300.

## (A) Invented post-`>` operator `/=` → raises at 5617 (extract_particle_ids)
Probe (v3.7.1, sm): `generate p p > l+ l- /= z` →
`InvalidCmd : No particle = in model` — **no output dir**.

Traced path:
- The `/` filter peel (5007-5019): `slash > 0`, `dollar < 0`, so regex `r"^(.+)\s*/\s*(.+\s*)$"` matches. In `l- /= z`, the `/` already has a space *before* it (`l- /`), so `space_before` cannot insert a space *after* it (needs `\S` on the left). group(1) = `'p p > l+ l- '` (kept as the leg line), group(2) = `'= z'` (the forbidden-particle string).
- `forbidden_particles = '= z'` → `extract_particle_ids('= z')` (5300) → `split_arg` → `['=', 'z']`. Token `'='`: not get_copy, not multiparticle, not `'|'`, not a digit → **5617 raise** on the FIRST token. The message names `=` (singular) because it raises before `z` is examined.
- **There is no `/=` or `!=` operator in the grammar.** Invented post-`>` operators fall through to particle-name lookup and raise `No particle <fragment> in model`. The exact fragment depends on the spacing the peel regex leaves.

## (B) Glued-paren token `(b` in a chain decay → raises at 5242 (leg loop)
Probe (v3.7.1, sm): `generate p p > t t~, t > (b w+, w+ > l+ vl), t~ > b~ w-, w- > l- vl~` →
`InvalidCmd : No particle (b in model` — **no output dir**. (The intended chain-decay grammar puts the `(` BEFORE the parent — that scoping is chain-decay's slice.)

Traced path:
- `split_arg` (extended_cmd.py:687, regex `r"(?:[^\s'\"]|...)+"`) splits only on whitespace (quote-aware). `(` is an ordinary non-space char and is NOT in the `space_before` tag set, so `(b` stays **one glued token**.
- Leg loop: `(b` is not a multiparticle, `'('.isdigit()` is False (so no digit/duplication path), `get_copy('(b')` returns None → `mylegids` empty → **5242 raise**.

### Balance-vs-resolution branch (which paren error you get)
A `(` failure has TWO possible outcomes depending on paren COUNT:
- **Balanced** parens (case B has one `(`, one `)`): the `check_process_format` balance check at **1154** PASSES, so the glued `(b` token survives to the leg loop → `No particle (b in model` (5242).
- **Unbalanced** parens: caught EARLIER at 1154 → `InvalidCmd : Invalid Format, no balance between open and close parenthesis` — never reaches token resolution. Probe-confirmed: dropping the closing `)` in case B flips the error to the balance message.

## Attribution is REAL, not cosmetic (history[-1])
The "interrupted in sub-command" wrapper (`extended_cmd.py` 1347-1351) names `self.history[-1]` — the command actually executing when the exception bubbled up:
```
elif self.history:
    error_text = 'Command "%s" interrupted in sub-command:\n' % line   # line = top-level (e.g. import script)
    error_text += '"%s" with error:\n' % self.history[-1]              # history[-1] = the raising command
```
- A malformed `generate ...` line raises during ITS OWN `extract_process`, so `history[-1]` is that `generate` line. Both probes attribute to the `generate` line.
- A malformed `define <name> = (b w+` attributes to its own `define ...` line (probe-confirmed: `No particle (b in model`, raised via `extract_particle_ids`/5617). The error CANNOT leak forward from a clean `generate` onto an unrelated later command — it always names the command whose own parse raised. **Attribution is real; when the error appears on a later line it is because the bad token lived on that later line.**
