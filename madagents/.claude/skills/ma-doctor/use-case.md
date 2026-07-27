# What this agent system is for

The product the harness serves. A structural change must serve these goals or it is not worth making.

## What it is

An **add-on a user drops into an existing Claude Code session** to give it MadGraph competence — not a standalone app. It layers onto the user's setup and should add to any existing agent system without taking it over. It is implemented entirely through the Claude Code CLI surface (markdown agents, skills, rules, settings, hooks); a capability that exists only in some other SDK is out of scope.

## What users use it for

A spectrum: install MadGraph and the stack; learn MadGraph; get deep insight into MadGraph internals; run autonomous multi-step simulation campaigns — with the human still supervising.

## What it must be

- **Communicative** — a conversational assistant; the human stays on the loop.
- **Accurate always, fast where it can be** — match effort and latency to difficulty; never trade accuracy for speed.
- **Out of the box** — works immediately, cold, first try.
- **Self-improving** — better over time via memory and learning.
- **Additive** — layers onto the user's setup without taking it over.
- **Easy to use.**
- **Token-frugal** — must not eat many tokens.

## Who it beats

The bar is **bare Claude Code**. The user could just ask their own session to do the MadGraph work, so this must be **better than bare Claude Code** to be worth adding: more accurate, and worth its token and latency overhead. Every scaffold earns its keep against that baseline. The core tension: the rich multi-agent setup must stay token-frugal enough to beat bare Claude Code.

## Interactive, human-on-the-loop

This is an interactive product — the user converses with it, follows up, and stays on the loop, including during autonomous campaigns. Design for that, not for a no-human one-shot: asking instead of guessing, surfacing a choice, a hedge the user acts on, and recovery across follow-ups are all part of the product.

## Why a change is conservative

Validation is expensive and the product must work cold, in front of a user. A wrongly-cut piece of scaffolding surfaces as a cold failure that is hard to detect or recover from. So prefer **reasoned leanness** over speculative cutting: remove only what is clearly redundant or inferable; when in doubt, keep. The cost of a cold failure outweighs the token saving of a speculative cut. This is why a structural change is recommended, discussed, and gated — never made blindly.

## Future direction

The setup should perform well even with weaker (e.g. local open-source) models — "warm and well trained at start" yet evolving with use. The trained state (memory + wiki) carries performance when the model is weaker, so a thinning justified only by "the model is strong" is a present-tense call, not future-proof.
