#!/usr/bin/env bash
# Guard against live credentials entering the codebase.
#
# guard-secrets.sh stops secrets getting OUT: it blocks shell commands that read
# the local dotenv file, so a key never lands in the transcript.
#
# This one stops them getting IN: a key pasted into source, a config file, or a
# hook script. Different direction, no overlap.
#
# Wired on two events so it covers before and after:
#   PreToolUse  (Edit|Write|NotebookEdit|Bash) -> deny, before the key hits disk
#   PostToolUse (Edit|Write|NotebookEdit)      -> catch what got through another
#                                                 path and tell Claude to fix it
#
# It never prints the matched value. Reporting the key would put the key in the
# transcript, which is the exact thing both guards exist to prevent. Line numbers
# only.
#
# Reads hook JSON on stdin. Fails open when jq is missing.
set -uo pipefail

payload=$(cat)
command -v jq > /dev/null 2>&1 || exit 0

event=$(printf '%s' "$payload" | jq -r '.hook_event_name // ""')
tool=$(printf '%s' "$payload" | jq -r '.tool_name // ""')

# Pull the text this event can actually see. PreToolUse gets the pending input,
# PostToolUse gets the file as it now sits on disk.
case "$event:$tool" in
  PreToolUse:Write)
    text=$(printf '%s' "$payload" | jq -r '.tool_input.content // ""')
    ;;
  PreToolUse:Edit)
    text=$(printf '%s' "$payload" | jq -r '
      [ .tool_input.new_string // ""
      , (.tool_input.edits // [] | map(.new_string // "") | join("\n"))
      ] | join("\n")')
    ;;
  PreToolUse:NotebookEdit)
    text=$(printf '%s' "$payload" | jq -r '.tool_input.new_source // ""')
    ;;
  PreToolUse:Bash)
    # Catches heredocs, `echo ... >> file`, sed -i. The other tools do not see these.
    text=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')
    ;;
  PostToolUse:*)
    file=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""')
    [ -n "$file" ] && [ -r "$file" ] || exit 0
    case "$file" in
      *.env.example | *.env.sample | *.env.template) exit 0 ;;
    esac
    text=$(cat "$file" 2> /dev/null) || exit 0
    ;;
  *) exit 0 ;;
esac

[ -z "$text" ] && exit 0

# Credential shapes worth blocking on. Each is specific enough that a false
# positive is rare; the generic assignment rule at the end needs 24+ chars.
KEY_RE='sk-ant-[A-Za-z0-9_-]{20,}'
KEY_RE="$KEY_RE"'|sk-proj-[A-Za-z0-9_-]{20,}'
KEY_RE="$KEY_RE"'|sk-[A-Za-z0-9]{24,}'
KEY_RE="$KEY_RE"'|AKIA[0-9A-Z]{16}'
KEY_RE="$KEY_RE"'|ASIA[0-9A-Z]{16}'
KEY_RE="$KEY_RE"'|gh[pousr]_[A-Za-z0-9]{30,}'
KEY_RE="$KEY_RE"'|github_pat_[A-Za-z0-9_]{30,}'
KEY_RE="$KEY_RE"'|xox[baprs]-[A-Za-z0-9-]{12,}'
KEY_RE="$KEY_RE"'|AIza[A-Za-z0-9_-]{35}'
KEY_RE="$KEY_RE"'|sbp_[a-f0-9]{40}'
KEY_RE="$KEY_RE"'|r8_[A-Za-z0-9]{35,}'
KEY_RE="$KEY_RE"'|hf_[A-Za-z0-9]{30,}'
KEY_RE="$KEY_RE"'|-----BEGIN [A-Z ]*PRIVATE KEY-----'
KEY_RE="$KEY_RE"'|(api[_-]?key|secret|token|password|passwd|bearer)[A-Za-z_]*["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9_/+=.-]{24,}["'"'"']'

# A line that reads from the environment is the correct pattern, not a finding.
SAFE_RE='process\.env|import\.meta\.env|Deno\.env|os\.environ|getenv|ENV\[|System\.getenv'
SAFE_RE="$SAFE_RE"'|secrets\.|vars\.|\$\{?[A-Z][A-Z0-9_]*\}?|%[A-Z][A-Z0-9_]*%'

# Obvious stand-ins. A starter kit is full of these on purpose.
FAKE_RE='your[-_]|my[-_]key|xxxx|<[A-Za-z_]|\.\.\.|placeholder|example|sample|template'
FAKE_RE="$FAKE_RE"'|changeme|change[-_]me|dummy|fake|redacted|REPLACE|TODO|\*\*\*\*'

hits=$(printf '%s\n' "$text" \
  | grep -nEi "$KEY_RE" 2> /dev/null \
  | grep -vE "$SAFE_RE" \
  | grep -vEi "$FAKE_RE" \
  | head -5)

[ -z "$hits" ] && exit 0

# Line numbers only. Never the value.
lines=$(printf '%s\n' "$hits" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')

reason="Possible live credential in this change, at line(s) ${lines}. Do not print or repeat the value. Move it to the local dotenv file, read it from the environment at the call site, and add only the key NAME to the checked-in example env file. If this is a placeholder or test fixture, make it obviously fake (prefix it with YOUR_ or example_) and retry. Checked by .agents/hooks/guard-key-literals.sh."

if [ "$event" = "PreToolUse" ]; then
  jq -n --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
else
  jq -n --arg r "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $r
    }
  }'
fi

exit 0
