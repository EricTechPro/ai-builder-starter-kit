---
description: Verify, commit on a branch, and open a PR
argument-hint: "[optional: PR title]"
---

Take the current working-tree changes all the way to an open PR.

1. **Verify first.** Run the check chain from `/verify`. If anything fails, stop and report —
   do not commit broken work, and do not "fix" it by loosening the check.
2. **Review the diff.** `git status` and `git diff` (staged and unstaged). If the diff contains
   anything the user did not ask for — a stray debug log, a reformatted unrelated file, a
   commented-out block — call it out before committing.
3. **Branch.** If on the default branch, create a descriptive branch first. Never commit
   directly to `main`/`master`.
4. **Commit.** One logical commit unless the work genuinely splits. The message says *why*,
   not a restatement of the diff. Include the repo's attribution trailers.
5. **Push and open the PR** with `gh pr create`. Title: $ARGUMENTS if given, else derived from
   the change. Body: what changed, why, how it was verified, and anything a reviewer should
   look at closely.
6. If prompts or model-call code changed, put the before/after eval numbers in the PR body.
   A prompt change with no eval evidence should be flagged as such in the PR, not hidden.

Report the PR URL when done. If `gh` is not authenticated, stop and say so rather than
falling back to something else.
