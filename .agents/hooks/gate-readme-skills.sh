#!/usr/bin/env bash
# Stop hook: the skill count in README.md has to match the tree before the turn ends.
#
# The README groups skills by source rather than listing all of them, so there is no
# per-skill link to check. What it does claim is a number, and a number is enough:
# adding or deleting a skill always moves it, which is exactly the moment the README
# needs a human decision (which group does this belong to, is it worth naming).
#
# Why a set comparison rather than "what changed this session", which is how
# gate-skill-evals.sh decides: drift has no session. A skill added three sessions
# ago and never written up is exactly the case worth catching, and a git-scoped
# check goes blind to it the moment the commit lands. Comparing the count to the
# tree is idempotent, so it stays silent while they agree and self-heals once they don't.
#
# One escape valve, because a gate with no way out gets deleted rather than fixed:
#   README_SKILLS_GATE=off    skips the gate for a session
#
# Fails open on anything unexpected. A broken hook must not brick the session.
set -uo pipefail

cat > /dev/null # drain stdin; the decision comes from the working tree

[ "${README_SKILLS_GATE:-on}" = "off" ] && exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" 2> /dev/null || exit 0

SKILLS_DIR=".agents/skills"
README="README.md"
[ -d "$SKILLS_DIR" ] || exit 0
[ -f "$README" ] || exit 0

# Skills on disk: a directory is a skill when it holds a SKILL.md. Anything else in
# here (LICENSE, UPSTREAM.md) is not one, so it must not move the count.
on_disk=$(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -name SKILL.md 2> /dev/null \
  | sed -n "s|^${SKILLS_DIR}/\([^/]*\)/SKILL.md$|\1|p" \
  | sort -u)
actual=$(printf '%s\n' "$on_disk" | grep -c .)

# A README that states no number is not wrong, so the claim is optional. Only the
# first "N skills" is read, since that is the headline a reader actually trusts.
claimed=$(grep -om1 '[0-9]\+ skills' "$README" 2> /dev/null | grep -o '[0-9]\+')
[ -z "$claimed" ] && exit 0
[ "$claimed" = "$actual" ] && exit 0

# Which skill probably moved the count. Asking the README ("which of these is not
# named here?") answers with every vendored skill, because the grouped table covers
# them by source rather than by name — 23 rows of noise around the one that matters.
# Git knows precisely: a new skill is an untracked or added path.
unnamed=""
if command -v git > /dev/null 2>&1 && git rev-parse --git-dir > /dev/null 2>&1; then
  unnamed=$(git status --porcelain --untracked-files=all -- "$SKILLS_DIR" 2> /dev/null \
    | grep -E '^(\?\?|A )' \
    | cut -c4- \
    | sed -n "s|^${SKILLS_DIR}/\([^/]*\)/.*|\1|p" \
    | sort -u)
fi

{
  echo "README.md says \"${claimed} skills\"; ${SKILLS_DIR}/ has ${actual}."
  echo
  echo "Update the count and put the skill in the right row of the group table."
  if [ -n "$unnamed" ]; then
    echo
    echo "New in the working tree — likely what moved the count:"
    for skill in $unnamed; do
      desc=$(sed -n 's/^description: *//p' "${SKILLS_DIR}/${skill}/SKILL.md" 2> /dev/null \
        | head -1 | cut -c1-90)
      echo "  ${skill} — ${desc:-<no description>}"
    done
  fi
  echo
  echo "Keep it to a row. The README is the map; SKILL.md is the territory."
  echo "To skip this gate for a session, set README_SKILLS_GATE=off."
} >&2

exit 2
