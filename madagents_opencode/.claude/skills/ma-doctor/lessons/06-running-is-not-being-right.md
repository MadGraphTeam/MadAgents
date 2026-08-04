# 06 — Running is not being right

> "It ran" is not "it's right." Verify functional correctness against the user's actual ask, not just that it executed.

The biggest verification blind spot is checking internal quality (it is well-formed, it ran)
but not functional correctness (it does what the user asked). Verification debt hides "in the
gap between 'runs' and 'right'" — output that runs fine but is wrong at the root. The two axes
are distinct: "is it written correctly?" (review) and "does it actually run?" (a runtime
probe). Both are needed, and neither is the user's actual goal until checked against the ask.

## In a harness like this

This *names* one of the core traps: parser-acceptance is not amplitude-attachment — a spec parses,
the tool runs to completion, and the result is the wrong observable. Reviewers must check the
result answers the user's actual question, not just that the setup is internally valid or that the
tool exited cleanly; a runtime probe supplies the behavioral axis (read the banner/log), catching
what static review cannot. "It ran" is never the consultant's evidence of correctness. When
auditing a harness, check that the verification path covers both axes — that some agent confirms
the output is what the user asked for, not only that it executed without error.

## Where the books say it

- **Loop** — §07/§08. Verification debt is the gap between running and being right; output that runs fine while being wrong at the root can sit under green tests and an open PR until a shipping morning.
- **Harness** — §06/§04 (Boeckeler's blind spot: a process constrains how code is written without verifying that it does what users need), §10 (the top agent failure — re-reading its own work, finding it fine, and stopping; verify against the ask before declaring done).
- **CC-Guide** — §08. Two verification axes — a security-reviewer asking whether it is written correctly, paired with a verify-app agent asking whether it runs.
- **Src-Analysis** — ch9/ch11. To verify is to demonstrate that the code works, not to confirm that it is present — re-run and compare, graded PASS/FAIL/PARTIAL.
- **CC-Guide** — §09/§11 · **Codex** — §09. Favour verification over raw development speed, since slower is faster — verify at every step (skeleton built, test it; API done, curl it), because catching a problem early is cheap and tracking it down afterward is expensive.
