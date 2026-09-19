#!/usr/bin/env bash
# PreToolUse(Bash) guard: refuse shell commands that read or pipe secret files.
#
# Permission deny rules already cover the Read and Edit tools. This closes the
# other door: `cat .env`, `source .env.local`, `grep KEY .env | curl ...`.
# `.env.example` and friends are deliberately NOT blocked - that file is how
# Claude is meant to learn which keys exist.
set -uo pipefail

payload=$(cat)

if ! command -v jq > /dev/null 2>&1; then
  # No jq: fail open rather than block every Bash call in the project.
  exit 0
fi

cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')
[ -z "$cmd" ] && exit 0

SECRET_RE='(^|[^A-Za-z0-9._-])\.env([^A-Za-z0-9._-]|$)'
SECRET_RE="$SECRET_RE"'|\.env\.(local|production|prod|staging|development|dev|test)([^A-Za-z0-9._-]|$)'
SECRET_RE="$SECRET_RE"'|(^|[^A-Za-z0-9._-])id_(rsa|ed25519|ecdsa)([^A-Za-z0-9._-]|$)'
SECRET_RE="$SECRET_RE"'|(^|[^A-Za-z0-9._-])\.npmrc([^A-Za-z0-9._-]|$)'
SECRET_RE="$SECRET_RE"'|(^|[^A-Za-z0-9._-])credentials(\.json)?([^A-Za-z0-9._-]|$)'
SECRET_RE="$SECRET_RE"'|service-account[A-Za-z0-9._-]*\.json'
SECRET_RE="$SECRET_RE"'|\.pem([^A-Za-z0-9._-]|$)'

if printf '%s' "$cmd" | grep -Eq "$SECRET_RE"; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Blocked by .claude/hooks/guard-secrets.sh: this command touches a secret file. Read .env.example for the key names, or ask the user to run the command themselves with the ! prefix."
    }
  }'
fi

exit 0
