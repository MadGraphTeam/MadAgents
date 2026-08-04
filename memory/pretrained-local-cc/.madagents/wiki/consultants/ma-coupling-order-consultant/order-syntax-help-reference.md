---
description: The authoritative help_generate documentation of coupling-order syntax (LO template, ^2 squared-ME interference, operator set, loop before-[/after-] amplitude-vs-squared placement and the loop +2 rule).
---

# Order-syntax help reference (`help_generate`)

`$MADGRAPH_INSTALL/madgraph/interface/madgraph_interface.py`, `help_generate`
(`601-646`) and `help_add` (`648-655`). This is the canonical user-facing grammar
for the coupling-order constructs THIS slice parses. Probe-confirmed (loop_sm,
v3.7.1) that this text renders verbatim at `help generate` runtime, and that the
documented interference example parses.

## LO syntax template (`605-606`, verbatim)
```
generate INITIAL STATE > REQ S-CHANNEL > FINAL STATE $ EXCL S-CHANNEL / FORBIDDEN PARTICLES COUP1=ORDER1 COUP2^2=ORDER2 @N
Example: generate l+ vl > w+ > l+ vl a $ z / a h QED<=3 QCD=0 @1
```
Coupling orders (`COUP1=ORDER1`, `COUP2^2=ORDER2`) sit at the END of the line,
after filters and before `@N`. This is why `extract_process`'s `order_pattern`
parses from the BACK (see `order-parsing-overview.md`).

## Default when no orders given (`609-610`)
> If no coupling orders are given, MG5 will try to determine orders to ensure
> maximum number of QCD vertices.

So an unconstrained process is NOT "all orders" — MG picks the QCD-maximal
leading contribution. (This is the diagram-enumeration default the
`default_unset_couplings` cap competes with; see `default-unset-couplings.md`.)

## Squared-ME / interference syntax (`611-616`, verbatim)
> Desired coupling orders combination can be specified directly for the squared
> matrix element by appending '^2' to the coupling name. For example,
> `p p > j j QED^2==2 QCD^2==2` selects the QED-QCD interference terms only. The
> other two operators '<=' and '>' are supported. Finally, a negative value
> `COUP^2==-I` refers to the `N^(-I+1)LO` term in the expansion of the COUP order.

- `^2` -> squared-amplitude (matrix-element) constraint (lands in
  `squared_orders`).
- The interference example `QED^2==2 QCD^2==2` is the canonical use of squared
  orders to isolate an interference term. PROBE-CONFIRMED (sm, v3.7.1):
  `generate p p > j j QED^2==2 QCD^2==2` parses and propagates both squared
  constraints to every subprocess (`g g > g g QCD^2==2 QED^2==2 @1`, ...).
- Negative `^2` value = sub-leading-term selector (detail:
  `negative-order-values.md`).

## Operator set (`617-618`, verbatim)
> allowed coupling operator are: `==`, `=`, `<=` and `>`.
> `==` request exactly that number of coupling while `=` is interpreted as `<=`.

This is the help-text statement of the same accepted set the validator enforces
(`_valid_amp_so_types` / `_valid_sqso_types`, `3036-3037`). PROBE-CONFIRMED an
out-of-set operator is rejected: `generate p p > t t~ QCD<2` ->
`InvalidCmd : Amplitude order constraints can only be of type =, <=, ==, >, not '<'.`

## Loop syntax — before-`[` vs after-`]` placement (`630-639`, verbatim, LOAD-BEARING)
```
core process [ <NLO_mode=> LoopOrder1 LoopOrder2 ... ] SQUAREDCOUPi=ORDERi
Example: generate p p > t~ t QED=0 QCD=2 [ all= QCD ] QCD=6
```
- **Restrictions BEFORE `[`** restrict the orders of the born *amplitudes*. In
  the example, `QCD=2` restricts the born amplitude to AT MOST QCD=2, and loop
  amplitudes to AT MOST QCD=2+2 (`634-636`) — the `+2` is because QCD loops add
  two powers of the perturbed coupling.
- **Restrictions AFTER `]`** restrict the orders of the matrix element (the
  squared amplitudes). In the example, `QCD=6` = born amplitudes with QCD=2
  squared against loop amplitudes with QCD=4, adding up to 6 (`637-639`).

This placement is the syntactic switch that decides whether a value lands in
`orders` (amplitude, before `[`) or `squared_orders` (matrix element, after `]`).
NOTE the help writes `QCD=2`/`QCD=6` with bare `=`; recall `=` -> `<=` ("at
most") in BOTH places (the help text itself says "at most"). The `+2` loop-power
arithmetic and the born-vs-loop split are loop-diagram-generation territory; what
is IN this slice is the PLACEMENT rule (before `[` -> `orders`, after `]` ->
`squared_orders`) and the `=`->`<=` reinterpretation.

## NLO_mode default (`640`)
`<NLO_mode=>` is optional; `all=` by default if absent. The mode set itself
(`_valid_nlo_modes`, `3035`) and bracket parsing are nlo-syntax slice; recorded
here only because the help template shows where orders sit relative to it.

## Boundary
The help text is in-slice as the authoritative grammar for the order constructs
THIS slice parses. The loop `+2` born/loop power arithmetic, the QCD-maximal
default selection, and what diagrams survive each restriction are
diagram-enumeration / loop-diagram-generation territory.
