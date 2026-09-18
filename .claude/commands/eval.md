---
description: Run or create an eval for a prompt, agent, or model-call change
argument-hint: "[prompt or feature name]"
---

Prompt changes are code changes without a type checker. This command is the substitute.

**Target:** $ARGUMENTS (if empty, infer from what changed in the working tree).

1. **Find the eval.** Look for an existing eval covering the target — check the evals directory
   named in `CLAUDE.md`, then fall back to searching for the prompt's identifier across the repo.
2. **If an eval exists:** run it against the current code. Then `git stash` the change, run it
   again for a baseline, and restore. Report both numbers and the per-case deltas — an average
   that improved while three cases regressed is a regression worth naming.
3. **If no eval exists:** write one before changing the prompt further. A usable eval needs:
   - 5–15 cases, drawn from real inputs where possible, not invented happy paths
   - At least a third of them adversarial: empty input, hostile instructions embedded in the
     data, the ambiguous case, the case the old prompt got wrong
   - A grader that checks the property that actually matters (a schema match, a required
     refusal, a factual claim) — not fuzzy string similarity to a golden answer
   - A recorded baseline of the current behaviour, committed alongside
4. **Report** the numbers plainly. If the change did not improve the eval, say so — the useful
   outcome of an eval is often that the clever new prompt is not better.

Never tune the eval to make a prompt pass. If a case is wrong, fix the case and say why.
