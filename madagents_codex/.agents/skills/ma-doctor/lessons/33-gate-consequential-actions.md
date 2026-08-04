# 33 — Gate consequential actions

> Default to dry-run, gate irreversible actions behind explicit confirmation, and skip work whose marginal gain doesn't clear its cost.

Match caution to stakes. Mature systems default to a paper/dry-run mode and require passing
explicit gates before switching to a consequential live action, and they skip an action whose
expected value doesn't clear its cost (a minimum-margin rule — don't act if the post-cost return
is below the threshold). This is distinct from allocating *effort* to difficulty (lesson 11):
here the question is whether to take a consequential or irreversible step at all, and the answer
is "not without a gate."

**In a harness like this.** Two transferable kernels. An **EV gate**: don't spin up a heavyweight
consultant cascade when the marginal accuracy gain doesn't clear the token cost (the earn-its-keep
rule). And **default-to-dry-run with explicit gates** before consequential or irreversible
operations — the confirm-before-acting discipline that governs autonomous campaigns and cluster
submission. With a human on the loop, the gate before a consequential action is a surfaced choice
(lesson 32), not an autonomous decision.

## Where the books say it

- **Polymarket** — §07. Mature bots skip a trade when expected value doesn't clear cost (a minimum net-margin rule — don't trade if the post-fee return is below the threshold) and default to paper trading, requiring three independent gates to be passed before going live; the four-tier intensity system graduates caution to stakes.
- **Src-Analysis** — ch5. The system reserves the deep/expensive path for when it is warranted — the cost-aware analog of an EV gate.
