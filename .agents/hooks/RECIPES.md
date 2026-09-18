# Hook recipes for AI builder starter kits

Research notes, September 2026. Grounded in the official
[hooks reference](https://code.claude.com/docs/en/hooks) and
[hooks guide](https://code.claude.com/docs/en/hooks-guide).

The question this answers: which hooks are worth shipping in a starter kit that any AI
builder can pick up. Not "every hook that exists", but the short list that stops the
mistakes people building AI apps actually make.

---

## The three handler types

Most hook writing online only covers `command`. There are three, and picking the right one
is most of the design work.

| Type | What it is | Use when |
| --- | --- | --- |
| `command` | Shell script, JSON on stdin, decision via exit code or printed JSON | The rule is deterministic. Grep, path check, exit status. Default choice. |
| `prompt` | Single LLM call (Haiku by default), returns `{"ok": bool, "reason": str}` | The rule needs judgment but the hook input alone is enough to decide. |
| `agent` | Subagent with Read, Grep, Bash. Up to 50 turns, 60s default timeout | The rule needs to check the actual state of the codebase. **Experimental.** |

Rule of thumb: a `command` hook that is turning into a pile of regexes wants to be a
`prompt` hook. A `prompt` hook that keeps guessing wants to be an `agent` hook.

### Exit codes and output, for `command` hooks

- Exit 0, plain stdout: on `SessionStart`, `UserPromptSubmit` and `PostModelSwitch` the text
  is added to Claude's context. On other events it is just logged.
- Exit 2: blocks. Works on `PreToolUse`, `UserPromptSubmit`, `UserPromptExpansion`, `Stop`,
  `SubagentStart`, `PreCompact`, `PreModelSwitch`, `SessionStart`, `Setup`.
- Printed JSON, for precise control:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Hardcoded API key. Read it from the environment."
  }
}
```

On `PostToolUse` use `additionalContext` instead: it cannot block, but the text lands in
Claude's context so the model fixes the thing on its next turn.

### Narrowing with `if`

`if` takes permission-rule syntax and only works on tool events (`PreToolUse`,
`PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`). Adding it to
any other event silently stops the hook from running.

```json
{ "type": "command", "if": "Bash(git *)", "command": "..." }
```

It is best-effort, not a security boundary. Anything that must never happen belongs in
`permissions.deny`, not in a hook.

---

## Tier 1: ship these by default

These five are the ones every AI project wants. They are cheap, they are language-agnostic
in shape, and each one stops a mistake that costs real money or real credibility.

### 1. Secret guard (PreToolUse)

**Already in this kit** as `guard-secrets.sh`. Blocks shell access to the local dotenv file
so a live key never lands in the transcript.

Why it matters: a key in the transcript is a key in the context window, and from there it
reaches logs, screenshots and any place the session gets shared.

Pair it with a `permissions.deny` rule on the same files. The hook covers the shell path,
the permission rule covers the tool path. You need both.

### 2. Key-in-code guard (PostToolUse on Edit|Write)

The single most common AI builder mistake: pasting a live key inline "just to test it", then
committing it.

Scan the file that was just written for key shapes. `sk-`, `sk-ant-`, `AKIA`, `ghp_`,
`xoxb-`, a 32+ char hex string assigned to something named `key` or `token`. Return
`additionalContext` telling Claude to move it to the local dotenv file and read it from the
environment.

`PostToolUse` cannot block, which is fine. Claude fixes it on the next turn, and the
feedback loop is faster than a pre-commit hook that only fires at commit time.

### 3. Model ID drift guard (PostToolUse on Edit|Write)

Model strings scatter. Six months later half the codebase is on a model that was retired
and nobody knows which calls are which.

Grep the written file for a model-shaped string (`claude-*`, `gpt-*`, `gemini-*`). If the
file is not your pinned-models module, flag it. One place owns model IDs; every call site
imports from there.

This is the hook that makes "pinned models live in one file" a real rule instead of a line
in AGENTS.md that gets ignored.

### 4. Eval gate on prompt changes (Stop)

The highest-leverage AI-specific hook, and the one almost nobody ships.

If anything under the prompts directory changed during the session and the eval never ran,
exit 2. Claude keeps working and runs the eval.

A `command` version tracks changed paths against `git diff --name-only`. A `prompt`
version reads better:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Did this session change any file under lib/prompts/? If yes, and the eval suite was not run afterward, respond {\"ok\": false, \"reason\": \"Prompt files changed. Run pnpm eval and report before/after numbers.\"}. Otherwise {\"ok\": true}. $ARGUMENTS"
          }
        ]
      }
    ]
  }
}
```

Without this, prompt changes ship on vibes. With it, they ship with numbers.

### 5. Format and typecheck the touched file (PostToolUse on Edit|Write)

Generic, but it belongs in tier 1 because it removes a whole class of churn. Run the
formatter on the one file that changed, then the typechecker. Feed errors back as
`additionalContext`.

Scope it to the single file. A full-project typecheck after every edit turns a fast loop
into a slow one.

---

## Tier 2: the ones that separate a good kit

### 6. Session context injection (SessionStart)

**Already in this kit** as `session-context.sh`. Worth extending for AI projects. Print:

- branch and uncommitted file count
- which model IDs are currently pinned
- any key name present in the checked-in example env file but missing locally
- the last eval score, if the kit writes one

Claude reads the stdout as context. That is a free, always-accurate briefing at zero prompt
cost to the user.

### 7. Unbounded model call lint (PostToolUse on Edit|Write)

Flag a model call written with no `max_tokens`, no timeout, and no retry bound. This is the
shape that turns into a hung request or a surprise bill.

Same for a model call inside a loop with no concurrency cap. A `prompt` hook handles this
better than a regex, because it can read the diff and judge.

### 8. Untrusted-input boundary check (PostToolUse on Edit|Write)

Prompt injection, made concrete. If an edit drops a tool result, a retrieved document, a
scraped page or a user upload straight into a prompt template, flag it.

A `command` heuristic gets you most of the way: a template literal in a prompt file
containing a variable named like `userInput`, `toolResult`, `document`, `scraped`, `page`.
A `prompt` hook gets you the rest.

Ship it as a warning, not a block. False positives on a block are how people turn hooks off.

### 9. Inline prompt guard (PostToolUse on Edit|Write)

Flag a long string literal containing "You are" or "Your task" in a file outside the prompts
directory. Prompts belong in one place, versioned, evaluable, diffable. Pasted variants
inline are how a project ends up with four slightly different system prompts.

### 10. Test-before-stop (Stop)

If source files changed and the test suite never ran, exit 2. Same shape as the eval gate.
The `agent` handler does this well since it can actually run the suite:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "Verify the unit tests pass. Run the suite and check the results. $ARGUMENTS",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

Agent hooks are experimental. For a kit other people depend on, the `command` version is
the safer ship.

### 11. Branch guard (PreToolUse on Bash, `if: "Bash(git commit *)"`)

Deny a commit when `git rev-parse --abbrev-ref HEAD` says main. Three lines of shell, saves
a revert.

---

## Tier 3: quality of life

### 12. Attention notification (Notification)

Matchers worth wiring: `permission_prompt`, `idle_prompt`, `agent_needs_input`,
`agent_completed`. On macOS, `osascript -e 'display notification ...'`.

The single highest-satisfaction hook per line of config. People start long runs and walk
away; this is what tells them to come back.

### 13. Context snapshot (PreCompact)

Write the session's open decisions to a file before compaction. Cheap insurance on long
sessions, and it makes resume useful instead of lossy.

### 14. Subagent cost log (SubagentStop)

Append agent type, duration and exit reason to a log. After a week you can see where fan-out
actually goes. Useful the moment a kit ships subagents.

### 15. Dotenv watcher (FileChanged)

When the checked-in example env file gains a key, tell Claude to update the setup docs. Note
the `FileChanged` matcher is a narrow exact-match set, letters, digits, `_` and `|` only.
Not a glob.

### 16. Session log (SessionEnd)

Append what changed to a running log. Turns "what did I do last week" into a file read.

---

## Design rules worth following

- **Earliest correct event.** Blocking at `PreToolUse` beats complaining at `Stop`.
- **Narrowest useful matcher.** A `PostToolUse` hook with no matcher fires after every tool
  call, including every Read. That is the main way hooks get slow.
- **Deterministic beats clever.** A hook that sometimes fires gets disabled.
- **Fail open, except on secrets.** A broken hook should not brick the session. Secrets are
  the exception.
- **Warn before you block.** New hooks ship as `additionalContext`. Promote to `deny` once
  the false positive rate is known.
- **Runnable outside Claude Code.** Hook scripts read JSON on stdin and nothing else. That
  is what lets Codex and CI call the same file.
- **Test on a throwaway repo first.** A bad `PreToolUse` hook can lock you out of your own
  project.

### Multiple hooks on one event

All matching hooks run to completion; one returning `deny` does not cancel the others' side
effects. For `PreToolUse`, the most restrictive answer wins, ordered `deny`, `defer`, `ask`,
`allow`. Every hook's `additionalContext` is kept and passed to Claude together.

---

## Suggested default set for this kit

| Hook | Event | Type | Status |
| --- | --- | --- | --- |
| Secret guard | PreToolUse: Bash | command | shipped, `guard-secrets.sh` |
| Session context | SessionStart | command | shipped, `session-context.sh` |
| Key-in-code guard | PreToolUse + PostToolUse | command | shipped, `guard-key-literals.sh` |
| Skill eval gate | Stop | command | shipped, `gate-skill-evals.sh` |
| Model ID drift | PostToolUse: Edit\|Write | command | proposed |
| Format + typecheck touched file | PostToolUse: Edit\|Write | command | proposed |
| Eval gate on prompt changes | Stop | prompt | proposed |
| Test-before-stop | Stop | command | proposed |
| Attention notification | Notification | command | proposed, opt-in |

Nine hooks. Four exist. Five to write.

---

## Evals for skills, not just prompts

A skill is a prompt. Editing one without an eval is a prompt change shipped on vibes, and
the failure mode is quieter than a bad prompt: the skill stops firing at all, or fires on
the wrong request, and nothing errors.

`claude plugin eval` handles this natively. The target can be a path, so it resolves a bare
skill folder, not only an installed plugin:

```bash
claude plugin eval .agents/skills/phone-mode --threshold 0.8
```

Useful flags for a gate:

| Flag | Why |
| --- | --- |
| `--threshold <0..1>` | Exit 1 if any case scores below it. This is what makes it a gate. |
| `--ablation with-without` | Runs a no-plugin baseline arm and reports the delta. Answers "did the skill help at all", which is the question that matters for a skill. |
| `--max-cost-usd` | Hard ceiling. Each case spawns real `claude` child runs on your credential. |
| `--json <path>` | Machine-readable result for CI. |
| `--trust-plugin` | Skips the first-run trust prompt. For CI only. |

### The eval suite shape

`claude plugin eval init --bare <name>` scaffolds it inside the skill folder:

```
.agents/skills/my-skill/
  SKILL.md
  evals/
    <case>/
      prompt.md          front matter: max_turns, allowed_tools
      graders/
        criteria.md      front matter: type (llm), weight
```

`prompt.md`:

```markdown
---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Ask the thing a real user would ask.
```

`graders/criteria.md`:

```markdown
---
type: llm
weight: 1
---

Describe what a successful response looks like.
```

A grader marked `tool_used: Skill` is a with-only indicator under ablation: it tells you the
skill actually fired, rather than scoring the answer.

### What a skill eval has to cover

Output quality is the easy half. The half people skip:

- **Triggering.** Requests that should fire the skill, phrased the way a real user would,
  not the way the description is written.
- **Near misses.** Requests that should NOT fire it. A skill that fires on everything is
  worse than no skill.
- **One adversarial case.** Hostile instructions inside the input data.

### A worked example, with real numbers

The suite under `.agents/skills/phone-mode/evals/` is five cases against a formatting
skill. Run on 18 September 2026, `--runs 2`, two arms, 102 seconds, $2.79:

| Case | With | Without | Δ |
| --- | --- | --- | --- |
| adversarial-injected-instructions | 1.00 | 1.00 | 0.00 |
| fires-on-implicit-signal | 0.60 | 0.00 | +0.60 |
| fires-on-mobile-signal | 0.50 | 0.00 | +0.50 |
| near-miss-desk-detail | 0.00 | 0.60 | **-0.60** |
| near-miss-phone-feature | 1.00 | 1.00 | 0.00 |

Mean Δ +0.10. Three things that reading the skill would not have told you:

- **A negative delta.** On `near-miss-desk-detail` the skill made the answer worse. The
  prompt was "give me the long version", which is the skill's own documented phrase for
  turning itself off. It fired anyway, twice out of two runs, and compressed a request
  that explicitly asked for depth. The skill documents the right behaviour and does the
  opposite, so no amount of re-reading it surfaces this.
- **Two zero deltas.** The adversarial case and one near-miss scored 1.00 in both arms.
  The skill is not what is producing that behaviour, and without the baseline arm you
  would have read 1.00 as the skill working.
- **A grader that is doing its job and one that is not yet.** `one-decision`, a regex
  counting a single trailing marker, passed cleanly. `card-shape`, an LLM rubric on the
  same replies, failed 3 votes to 0 on every triggering run. When a deterministic grader
  and a judge disagree that consistently on the same output, suspect the rubric before
  the skill, and re-run with `--keep-temp` to read the actual reply rather than guessing.

This is the argument for the gate in one table: the eval found a regression, two
non-contributions, and a probable bug in its own rubric, in under two minutes.

### How the gate knows the eval ran

No state file. `claude plugin eval` writes results to `<skill>/evals/results/<timestamp>/`,
so "is the eval current?" is a mtime comparison against the skill's source files.

That comparison covers all three ways a skill changes, because git sees all three the same
way: editing one, installing a new one (untracked directory), and updating a vendored one.

`gate-skill-evals.sh` is the implementation. `SKILL_EVAL_GATE=off` skips it.

---

## Before or after: which event for a guard

Worth being deliberate about, because the two are not interchangeable.

| | PreToolUse | PostToolUse |
| --- | --- | --- |
| Sees | `tool_input`, the pending arguments | `tool_result`, plus the file on disk |
| Can block | Yes, `permissionDecision: "deny"` or exit 2 | No, `additionalContext` only |
| Good for | Stopping a bad write before it lands | Catching what arrived some other way |

For credentials, wire **both**. `PreToolUse` on `Edit|Write|NotebookEdit` reads the content
Claude is about to write and denies it, so the key never touches disk. `PostToolUse` reads
the file as it now exists, which catches a key that arrived through a path the matcher did
not cover, and feeds it back so Claude fixes it next turn.

Add a `PreToolUse` arm on `Bash` too. A heredoc, an `echo >> file` or a `sed -i` writes
source without ever calling Edit or Write, and a guard that only watches the edit tools
never sees it.

One rule that matters more than any of the above: **a secret guard must never print what it
matched.** Echoing the key into the deny reason puts the key in the transcript, which is the
exact thing the guard exists to prevent. Report line numbers.

## Sources

- [Hooks reference](https://code.claude.com/docs/en/hooks)
- [Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide)
- [Claude Code Hooks: 6 Production Patterns](https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns)
- [Best Claude Code Hooks Examples and Templates in 2026](https://promptessor.com/blog/best-claude-code-hooks-examples-for-safer-automated-coding-workflows-in-2026)
- [15 Best Claude Code Hook Examples](https://www.ayautomate.com/blog/best-claude-code-hooks-examples)
