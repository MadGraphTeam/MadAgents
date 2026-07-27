# 31 — Ask before guessing

> When the task is ambiguous, ask 2-3 scoping questions before doing non-trivial work — don't fire and forget.

The routing rule is "ambiguous task → ask for clarification." The named fix for fire-and-forget
behavior is a standing instruction: before starting any non-trivial task, ask 2-3 questions to
confirm the scope and acceptance criteria — interview the user, like a product manager doing
requirements clarification, rather than starting immediately on an unclear goal.

**In a harness like this.** Ask-don't-guess is right for an interactive product. An autonomous,
one-shot evaluation can never reward a clarify-and-route — it cannot answer back — so this is a
product principle that outcome scores are blind to; carry it as an explicit instruction, not
something inferred from how runs score. Claude Code already asks clarifying questions by default,
so encoding it partly preserves a default and makes it reliable rather than mood-dependent.

## Where the books say it

- **CC-Guide** — §06/§12. Let the model interview you; the routing rule is that ambiguity triggers a question.
- **Codex** — §10/App C. The AGENTS.md fix line instructs the agent to ask two or three scope-and-acceptance questions before starting any non-trivial task (starting immediately is the pitfall; asking first is the safer default).
- **Skills** — ch8. The skill-creator asks clarifying questions the way a product manager runs requirements clarification — clarify before generating.
