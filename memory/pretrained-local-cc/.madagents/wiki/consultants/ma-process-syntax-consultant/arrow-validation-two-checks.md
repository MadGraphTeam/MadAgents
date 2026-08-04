---
description: The process-arrow count is validated TWICE — check_process_format (upstream, user-visible message) and extract_process (redundant secondary guard) — both with re.findall(r'>\D'); probe-confirmed message text.
---

# Arrow-count validation fires twice (v3.7.1)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`.

## Two independent checks, same regex, different messages
1. **Upstream, user-visible**: `check_process_format` (1150), reached via `do_add`→`check_add`(913)→`check_generate`(1122, calls `check_process_format` at 1146).
   - 1154: parenthesis-balance check (`(` vs `)` count) → `InvalidCmd('Invalid Format, no balance between open and close parenthesis')`.
   - 1160: splits on `,` and recurses per-subprocess (decay-chain aware).
   - 1167: `nbsep = len(re.findall(r'>\D', process))` (comment: "not use process.count because of QCD^2>2"). If `nbsep not in [1,2]` → `InvalidCmd('wrong format for "%s" this part requires one or two symbols ">", %s found')`.
   - 1174: `re.split(r'>\D', process)`; any empty piece → `InvalidCmd('"%s" is a wrong process format. Please try again')`.
2. **Secondary, inside extract_process** (4829): same `re.findall(r'>\D', line) in [1,2]` test → `do_help('generate')` + `InvalidCmd('Wrong use of ">" special character.')`.

## Probe-confirmed (v3.7.1, sm)
`generate u u~ > z > z > z` raises the **upstream** message:
`InvalidCmd : wrong format for "u u~ > z > z > z" this part requires one or two symbols '>', 3 found`
The extract_process message ("Wrong use of...") is NOT what the user sees for a malformed top-level process — `check_process_format` rejects first. The 4829 guard only protects callers that bypass `check_add` (e.g. direct `extract_process` calls).

## A THIRD layer pre-empts both: the Switcher
A line with a perturbation `[bracket]` is intercepted even earlier by `master_interface.py:Switcher` (see switcher-predispatch-layer.md). The Switcher validates the NLO mode and routes the interface BEFORE `MadGraphCmd.check_process_format` runs. So a line that is BOTH arrow-malformed AND has a bad NLO bracket yields the Switcher's NLO-mode message, not the arrow message. Probe (v3.7.1): `generate u u~ > z > z > z [badmode= QCD]` → `The NLO mode badmode is not valid...`, NOT the "3 found" arrow message. The arrow message only wins when no bracket is present.

## Why `>\D` not literal `>`
The regex requires a non-digit after `>`, so `QCD^2>2` (coupling order with `>` operator + digit) is NOT counted as a process arrow. Chain decay legitimately has 2 arrows; both checks allow `[1,2]`.
