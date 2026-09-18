#!/usr/bin/env bash
# Stop hook: a skill that changed this session has to have its eval run before
# the turn ends. Same idea as gating prompt changes on an eval, applied to skills.
#
# Skills are prompts. Editing one with no eval is shipping a prompt change on
# vibes, and the failure mode is worse than a bad prompt: the skill stops firing
# at all, or fires on the wrong request, and nothing errors.
#
# How it knows the eval ran, with no state file to keep in sync:
#   `claude plugin eval <path>` resolves a skill folder directly and writes its
#   results to <skill>/evals/results/<timestamp>/. So "is the eval current?" is a
#   mtime comparison between the skill's source files and its newest result.
#
# Covers all three cases the same way, because git sees all three:
#   - editing a skill      -> modified SKILL.md
#   - installing a skill   -> untracked new directory
#   - updating a vendored skill -> modified files
#
# Two escape valves, because a gate with no way out gets deleted rather than fixed:
#   SKILL_EVAL_GATE=off              skips the gate for a session
#   .agents/hooks/eval-gate-ignore   one glob per line, for skills you did not author
#
# Fails open on anything unexpected. A broken hook must not brick the session.
set -uo pipefail

cat > /dev/null # drain stdin; the decision comes from the working tree

[ "${SKILL_EVAL_GATE:-on}" = "off" ] && exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" 2> /dev/null || exit 0
command -v git > /dev/null 2>&1 || exit 0
git rev-parse --git-dir > /dev/null 2>&1 || exit 0

# A run already in flight is not a forgotten eval. Eval runs take minutes, so Claude
# will reach Stop in the middle of one; blocking there tells it to start a second run
# of the thing already running. The gate catches "you never ran it", not "you are
# running it right now".
#
# Scoped to the one skill on purpose. Matching any `plugin eval` process anywhere
# stands the gate down whenever an unrelated eval happens to be running, including
# one from another session or another project, and a gate that silently stops
# firing is worse than no gate.
eval_in_flight() {
  pgrep -f "plugin eval.*$1" > /dev/null 2>&1
}

SKILLS_DIR=".agents/skills"
IGNORE_FILE=".agents/hooks/eval-gate-ignore"
[ -d "$SKILLS_DIR" ] || exit 0

# A skill is exempt when its name matches a glob in the ignore file. Vendored and
# tool-installed skills belong here: you did not write them, so gating your own
# work on their eval coverage is noise, and it is the fastest way to get someone
# to turn the whole gate off.
is_ignored() {
  [ -f "$IGNORE_FILE" ] || return 1
  local name pattern
  name=$(basename "$1")
  while IFS= read -r pattern || [ -n "$pattern" ]; do
    case "$pattern" in '' | '#'*) continue ;; esac
    # shellcheck disable=SC2254
    case "$name" in $pattern) return 0 ;; esac
  done < "$IGNORE_FILE"
  return 1
}

# Every skill directory with an uncommitted change. cut -c4- keeps paths with
# spaces intact; the sed strips a rename's "old -> new" down to the new path.
changed=$(git status --porcelain -- "$SKILLS_DIR" 2> /dev/null \
  | cut -c4- \
  | sed 's/.* -> //' \
  | sed -n "s|^\(${SKILLS_DIR}/[^/]*\).*|\1|p" \
  | sort -u)

[ -z "$changed" ] && exit 0

# Newest mtime across the paths on stdin, as epoch seconds. Portable across the
# BSD stat on macOS and the GNU stat everywhere else.
newest_mtime() {
  local newest=0 file stamp
  while IFS= read -r file; do
    stamp=$(stat -f %m "$file" 2> /dev/null || stat -c %Y "$file" 2> /dev/null) || continue
    [ "$stamp" -gt "$newest" ] && newest=$stamp
  done
  printf '%s' "$newest"
}

no_evals=""
stale=""

while IFS= read -r skill; do
  [ -f "$skill/SKILL.md" ] || continue
  is_ignored "$skill" && continue
  eval_in_flight "$skill" && continue

  if [ ! -d "$skill/evals" ]; then
    no_evals="$no_evals $skill"
    continue
  fi

  # The whole evals/ tree is excluded from the "source" side, not just results/.
  # Authoring a case is eval work, not a skill change, and counting it as one makes
  # the gate unsatisfiable: every edit to a case re-marks the skill stale, so you
  # can never finish writing the suite.
  src=$(find "$skill" -type f -not -path "$skill/evals/*" 2> /dev/null | newest_mtime)
  res=$(find "$skill/evals/results" -type f 2> /dev/null | newest_mtime)

  [ "$res" -gt "$src" ] || stale="$stale $skill"
done <<< "$changed"

[ -z "$no_evals" ] && [ -z "$stale" ] && exit 0

{
  echo "Skill changes are not covered by a current eval. Do this before stopping."
  echo

  if [ -n "$stale" ]; then
    echo "Changed since their last eval run:"
    for skill in $stale; do
      echo "  claude plugin eval $skill --threshold 0.8"
    done
    echo
  fi

  if [ -n "$no_evals" ]; then
    echo "No eval suite yet:"
    for skill in $no_evals; do
      echo "  cd $skill && claude plugin eval init"
    done
    echo
    echo "A usable skill eval needs cases that test triggering, not just output:"
    echo "  - requests that SHOULD fire the skill, phrased the way a real user would"
    echo "  - near-miss requests that should NOT fire it"
    echo "  - one adversarial case: hostile instructions inside the input data"
    echo
  fi

  echo "Report the before and after numbers. --threshold exits non-zero on a"
  echo "failing case, so the score is the gate, not your read of the transcript."
  echo "To skip this gate for a session, set SKILL_EVAL_GATE=off."
} >&2

exit 2
