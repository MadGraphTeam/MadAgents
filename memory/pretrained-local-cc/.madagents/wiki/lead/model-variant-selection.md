---
description: A BSM model ships with the task and you are about to judge its content, or to go hunting a different variant.
---

## The mistake

For an HVT task I concluded "no qqVz vertices exist, so production must be VBF" — and I reached that by reading couplings/UFO files rather than running a probe. That conclusion was wrong: the HVT model provided for the task (installed at `models/HVT`, imported as `import model HVT`) **does** have qqVz vertices and **does** support single-resonant Drell-Yan production. A one-line `generate p p > vz` shows `u u~ > vz` (1 diagram), `d d~ > vz` (1 diagram), etc. immediately.

Two errors compounded: (a) inferring "no vertex" from a couplings read instead of a `generate` probe, and (b) wandering off to consider/download other model variants when the model already installed for the task was the correct one.

## The rule

1. **Use the model that is installed for the task, imported by its directory name.** The task ships its model under `models/<Name>` (e.g. `models/HVT`); import it as `import model <Name>`. Do not assume you need a different "canonical" variant or an online download — the provided model is the one to use. `display modellist` shows what is actually available locally.
2. **Verify production/vertex existence with a generate probe before claiming a coupling is absent.** `generate p p > <particle>` is a one-liner that tells you if production works. Never infer "no vertex" from reading UFO/coupling files — a quick probe is cheaper and authoritative.
3. **A "fermiophobic" or benchmark label does not mean zero all fermion couplings.** Check which coupling the label actually refers to (e.g. HVT fermiophobic ⇒ lepton coupling cl=0, but the quark coupling cq stays non-zero so Drell-Yan production survives). Confirm by probe, not by assumption.

## Scope

Fires when: a task names a BSM model and I need to test its production modes or vertex content. Before concluding a vertex/coupling is missing, run the generate probe against the installed model.
