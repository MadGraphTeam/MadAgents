---
description: Your chain has a step past parton level (shower, detector, analysis) and you assume it fires because you named it.
---

# Downstream-tool card-existence gate — cross-tool dispatch playbook

## When it applies
- User asks "did Delphes / Rivet / MA5 / PGS actually run?" or "why didn't the detector sim / analysis run?" after a `generate_events` / `launch` chain.
- User is surprised a downstream step was **skipped** (it was "in the chain") or surprised it **ran** (they didn't ask for it).
- Composing a multi-tool simulation-spec and you need to predict which downstream steps will fire end-to-end.
- "Why isn't Rivet / Delphes even offered in the `launch` switch menu?"

## The cross-tool principle (dispatch orientation — facts live in the consultant pages)
Three independent conditions decide a downstream step, and they fail in different slices:

1. **Tool reachability** — `<tool>_path` config set (`delphes_path` / `madanalysis5_path` / `rivet_path`, plus for analysis tools `'PY8' in available_module`). Unset → the `launch` switch never *offers* it. Owned by the tool's interface slice; the PY8 boolean is **pythia8-interface-owned** (see routing pages seam).
2. **Operative card existence** — in the automated chain, a downstream step **silently no-ops** when its `Cards/<tool>_card.dat` is missing (the `--no_default` convention). The same command issued **directly by the user** asks-or-raises instead. Card existence is the on/off switch.
3. **Card non-default-ness / validity** — a card that exists but is the shipped default may be a no-op (MA5's `skip_analysis`), or detected as the wrong type by content. **Present ≠ active.**

The trap this playbook exists to kill: **do not assume a chained downstream step ran just because it was in the `generate_events` chain.** Confirm the card-present + non-default + path-set conditions with the owning interface consultant per tool.

## Dispatch sequence
1. Identify the tool (Delphes / Rivet / MA5 / PGS / Pythia8).
2. Dispatch that tool's interface consultant for its card-existence-gate page (below). Mark any cross-tool premise ("Given the chain reached the shower step…").
3. If switch-availability is the question, also dispatch pythia8-interface for the `'PY8' in available_module` truth (it gates Rivet's offer and Delphes/MA5 shower auto-resolution).

## Instance pages (cite — never restate their MadGraph facts here)
- **Delphes** — `../consultants/ma-delphes-interface-consultant/operative-card-existence-is-the-detector-switch.md`: `Cards/delphes_card.dat` existence is the detector on/off at four entry points; `--no_default` silent skip; `consistency_detector_shower` forces a shower on when Delphes is selected. Auto-chains after the shower step (LO); NLO does **not** auto-chain (`nlo-amcatnlo-delphes-path.md` — and the NLO-`None`-filepath path *crashes* with a Python `TypeError` rather than silently no-opping). Card-identity routing: `card-identity-substring-routers.md` — identity is resolved by substring at **two** routers keyed on different things (`detect_card_type` on content vs `Banner.add` on filename), which can disagree on a renamed card.
- **MA5** (dedicated three-gate page) — `../consultants/ma-madanalysis5-interface-consultant/ma5-three-gate-availability.md`: MA5 running at all is gated by three independent checks at three lifecycle stages (path-truthy at switch-surface time / card-exists at dispatch time / card-non-default at load time), each silently no-opping MA5 with a **distinct** symptom → "MA5 produced no plots" has three separate root causes. This is MA5's endpoint of this playbook.
- **Rivet** — `../consultants/ma-rivet-interface-consultant/rivet-suppression-gates.md`: four independent silent-suppression gates (path-validity / switch-availability via `'PY8' in available_module` / card-editor card-SET membership / `do_rivet` card-presence), each keyed off a different input, each with its own diagnostic.
- **MA5 (card-identity complement)** — `../consultants/ma-madanalysis5-interface-consultant/card-identity-and-banner-roundtrip.md`: `detect_card_type` is content-based and the shipped `@MG5aMC skip_analysis`-only default detects as **`'unknown'`** (not as an MA5 card); operative MG paths key off the literal **filename**, so they are unaffected — but content-classifying tooling mis-identifies it. The shipped default parses to `skip_analysis=True` → no-op out of the box (this is MA5's Gate-3 mechanism). **Exception to the silent-skip rule:** MA5's Layer-2 `_reco_*` handler **hard-raises** `MadGraph5Error` on a missing reconstructed event file — see `failure-handling-two-layers.md` (post-launch failures are not uniformly quiet).
- **Pythia8** — card-*precedence* (a different axis: value precedence across card layers, not existence) — `../consultants/ma-pythia8-interface-consultant/py8-card-precedence.md`, `interface-divergence-main164-vs-old.md`.

## Anticipated traps
- **Present ≠ active** (MA5 `skip_analysis` default; a content-`'unknown'` card). Always check non-default-ness, not just file existence. **The third gate (non-default-ness) is NOT a uniform mechanism across tools**: MA5's is the `@MG5aMC skip_analysis` escape tag; Delphes/Rivet's is "card is the shipped default / empty template." Don't assert a single third-gate test across tools — ask the owning slice.
- **Path-unset ≠ card-missing** — `delphes_path`/`madanalysis5_path`/`rivet_path` unset means the step is never *offered*; card-missing means it's offered-then-skipped. Different diagnosis, different fix.
- **Silent-skip has exceptions** — MA5's reco-raise hard-fails; don't over-generalize "downstream failures are quiet."
- **LO auto-chains, NLO often doesn't** — confirm per tool (Delphes NLO has no `run_delphes3` in the NLO template at all).

## Return-interpretation hint
A consultant reporting "the card exists" answers only condition 2. Necessary, not sufficient — re-check condition 1 (path/PY8) and condition 3 (non-default / content-type) before concluding the step ran. An empty `## Implications` plus a `## Rejected (out-of-slice)` usually means you sent the PY8-boolean question to the wrong downstream slice — route the boolean's truth to pythia8-interface.

## Relation to other lead pages
Supersedes the routing pages "Downstream `--no_default` dispatch convention" seam (which flagged this as a candidate playbook pending consultant confirmation — now confirmed by delphes + rivet + MA5 independently authoring the gate pages). Sibling to `config-value-lifecycle-layers` (that one is "written card value ≠ enforced value"; this one is "card existence/identity ≠ step fired").
