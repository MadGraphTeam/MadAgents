# Mandatory Reviews

Every result presented to the user must be reviewed first. Do not skip reviews.

## verification-reviewer

Invoke **verification-reviewer** for:
- Any MadGraph output (cross sections, event generation, parameter configurations, decay chains)
- Any physics claim or derivation
- Any code or script that will be delivered to the user
- Any result that downstream work depends on

**Quick check** is the default for all reviews. It catches obvious errors without expensive re-verification.

**Thorough review** is reserved for: user-requested high accuracy, critical steps in long-running plans where errors would be costly to redo, or when a quick check flags something suspicious.

When in doubt, use quick check. Skipping a review entirely is only justified for purely mechanical operations (creating directories, copying files, formatting output).

## presentation-reviewer

Invoke **presentation-reviewer** for all user-facing deliverables: plots, documents, summaries, reports. No exceptions.
