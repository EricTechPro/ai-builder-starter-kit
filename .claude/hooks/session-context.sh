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
