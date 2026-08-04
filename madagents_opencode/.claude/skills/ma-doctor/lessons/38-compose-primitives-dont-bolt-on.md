# 38 — Compose primitives, don't bolt on

> Cover new scenarios by combining existing primitives, not by adding bespoke machinery per scenario. And gate a card on its preconditions so it surfaces only when it applies.

Squeeze the primitives to a minimum and cover new cases by combination — one system builds eight
collaboration patterns and its "swarm" from the same tasks/links/comments with no new engine
(no new primitives, only new combinations). One skill, one job, composed Unix-pipe style. Fire a
named, reusable skill rather than pasting a wall of one-off instructions nobody will maintain. And
surface a tool or card only when its runtime precondition holds, so it doesn't clutter the default
surface or invite a wrong pick.

**In a harness like this.** Build new workflows by composing existing skills and dispatch, not new
infrastructure — pairs with don't-add-machinery (lesson 36). A card that only applies under some
condition should surface only when that precondition holds, keeping it off the default
surface and out of the routing key's way (lesson 20). Composition over bespoke machinery is also the
token-frugal path: fewer primitives, fewer standing descriptions.

## Where the books say it

- **Hermes** — §16/§17 (compose primitives — no new primitives, only new combinations; the swarm is combinator sugar over the existing runtime), §11 (gate a consultant on its preconditions — `check_fn`: not installed, not configured or not triggered means the model simply cannot see them).
- **Skills** — ch7. One skill, one job / Unix-pipe composition (Principle 3).
- **Loop** — §03/§04. Trigger a named skill, not a wall of prompt — fire `$skill-name` instead of pasting a giant block of instructions into a schedule nobody will ever update.
- **CC-Guide** — §07/§12 · **Loop** — §04. Skills make a repeated workflow permanent — project knowledge fixed in a single file the agent reaches for instead of re-deriving every run — paying down the *intent debt* of re-explaining the project each time.
