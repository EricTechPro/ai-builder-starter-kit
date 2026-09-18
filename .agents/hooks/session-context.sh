#!/usr/bin/env bash
# SessionStart: inject a few facts that would otherwise cost several tool calls.
# Keep the output SHORT - it is prepended to every session in this project.
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

out=""

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || branch=""
if [ -n "$branch" ]; then
  dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  out="${out}Branch: ${branch} (${dirty} uncommitted file(s))"$'\n'
fi

if [ -f package.json ] && command -v jq > /dev/null 2>&1; then
  scripts=$(jq -r '(.scripts // {}) | keys | join(", ")' package.json 2>/dev/null)
  [ -n "$scripts" ] && [ "$scripts" != "" ] && out="${out}package.json scripts: ${scripts}"$'\n'
  pm="npm"
  [ -f pnpm-lock.yaml ] && pm="pnpm"
  [ -f yarn.lock ] && pm="yarn"
  [ -f bun.lockb ] && pm="bun"
  out="${out}Package manager: ${pm} (lockfile present)"$'\n'
fi

[ -f .env.example ] && out="${out}Key names are in .env.example; .env* itself is blocked by the secrets guard."$'\n'

# Drift check: .claude/{skills,commands,agents} must stay symlinks into .agents/.
# An installer that does `rm -rf` then `mkdir` replaces one with a real directory,
# which forks the source of truth silently. Make that loud instead.
drifted=""
for link in skills commands agents; do
  path=".claude/$link"
  [ -e "$path" ] || continue
  if [ ! -L "$path" ]; then
    drifted="${drifted} ${path}"
  fi
done

if [ -n "$drifted" ]; then
  out="${out}WARNING - these should be symlinks into .agents/ but are now real directories:${drifted}."$'\n'
  out="${out}The source of truth has forked. Move the contents into the matching .agents/ directory, "
  out="${out}delete the real directory, and recreate the link: ln -s ../.agents/<name> .claude/<name>"$'\n'
fi

[ -z "$out" ] && exit 0

if command -v jq > /dev/null 2>&1; then
  jq -n --arg ctx "$out" '{
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: $ctx
    }
  }'
fi
exit 0
