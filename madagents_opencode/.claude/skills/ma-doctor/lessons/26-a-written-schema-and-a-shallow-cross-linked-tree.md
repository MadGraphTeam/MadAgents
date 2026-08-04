# 26 — A written schema, a shallow cross-linked tree

> A written schema turns a general agent into a consistent author. Keep the knowledge tree shallow, and cross-link related pages so the agent traverses connections instead of re-searching.

A short written schema (naming, frontmatter, tag taxonomy, page structure, explicit triggers,
scoped operations, output format) turns a general-purpose model into a professional wiki curator — without
it the agent's conventions drift run to run. Keep the tree flat: each level of nesting costs path
tokens and deeply nested pages get overlooked during traversal. And cross-link related pages
(and source anchors) so the agent follows the network instead of relying on grep to get lucky —
the book calls the difference between an unlinked warehouse and a linked network "a qualitative
leap."

## In a harness like this

The harness prescribes the wiki page format in its `wiki-*` skills rather than letting consultants
free-form, and the wiki is already flat (`consultants/<name>/<slug>.md`, ~3 levels). A tight schema
is *cheap, reasoned structure* — squarely on the keep side, not speculative subtraction.

The cross-linking nudge needs the architecture's shape. The cross-links that fit are **source
anchors** (file:line back to the MadGraph source) and **lead → slice routing** pointers — both
present and worth keeping. Pervasive page→page cross-linking is largely *not* applicable here:
consultants navigate by the auto-loaded MEMORY index (lesson 23), which already lists every page in
the subtree, so a *within-subtree* link is redundant with the index; and read-scope forbids a
consultant reading another subtree, so a *cross-subtree* link is dead. So keep the schema's
cross-ref *permission* (relative paths, no `[[wikilinks]]`) but do not lean harder on page→page
links — the index is the navigation, and more links would add tokens for redundant or dead
structure. Lesson 26's link-traversal value is index-navigation here.

## Where the books say it

- **Obsidian** — §06 (`SCHEMA.md` unifies four things; §09.2: explicit triggers, scoped operations, specified output format, test small), §05 P3 (flat first — nesting costs path tokens, deep pages get missed), §02/§06 (cross-link so the agent traverses that network instead of relying on grep to get lucky).
- **Skills** — ch4/ch9. Specific, observable steps and a consistent authored shape — the model needs clear judgment criteria, not vague direction.
- **Skills** — ch2/ch3. Examples show what "good" is — a worked example of the wanted output teaches the standard by in-context learning, better than abstract description, since the model learns the target from examples; a few key ones, balanced against the length budget.
