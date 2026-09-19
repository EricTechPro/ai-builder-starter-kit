---
description: Run the project's full check chain and report what actually failed
argument-hint: "[optional: path or test name to narrow to]"
---

Run this project's checks in order, stopping to report rather than pushing past a failure.

1. Read the **Commands** table in `CLAUDE.md` to get the real invocations. Do not guess the
   package manager — check for a lockfile if the table is unfilled.
2. Run, in this order, skipping any the project does not define:
   - typecheck
   - lint
   - tests $ARGUMENTS
   - build (only if typecheck, lint and tests all passed)
3. If evals are defined and anything under the prompts directory changed in the working tree,
   run the evals too and report the score delta.

Report format — no preamble:

- One line per check: `✅ typecheck` / `❌ lint (3 errors)`.
- For each failure: the file:line, the actual error text, and your one-sentence read on the cause.
- Then stop. Do not fix anything unless asked — a failing check is information, and the user
  may want to see it before it is papered over.

If a check is slow, run it in the background and keep going with the others.
