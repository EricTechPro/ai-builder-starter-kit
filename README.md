# ai-builder-starter-kit

A portable Claude Code setup to drop into a new AI-application project. It is configuration
only — no framework, no dependencies, nothing to install.

## Use it

```bash
cp -R ai-builder-starter-kit/.claude your-project/.claude
cp ai-builder-starter-kit/CLAUDE.md your-project/CLAUDE.md
```

Then fill in `CLAUDE.md`. Every `<angle-bracket>` is a blank; delete the sections that do not
apply. A short, true CLAUDE.md beats a long, aspirational one.

## What's in it

```
CLAUDE.md                          Project-conventions template
.claude/
  settings.json                    Shared baseline: permissions + hooks
  settings.local.json.example      Personal overrides (copy, don't commit)
  commands/
    verify.md                      /verify — run the check chain, report failures
    ship.md                        /ship   — verify, branch, commit, open PR
    eval.md                        /eval   — run or write an eval for a prompt change
  agents/
    prompt-reviewer.md             Reviews the app↔model seam
    cost-tracer.md                 Maps where tokens and latency go
  hooks/
    guard-secrets.sh               PreToolUse(Bash): blocks shell access to secrets
    session-context.sh             SessionStart: branch, scripts, package manager
```

## The two hooks

**`guard-secrets.sh`** closes the door that permission rules leave open. `Read(.env)` deny
rules stop the Read tool; they do nothing about `cat .env`, `source .env.local`, or
`grep KEY .env | curl`. This hook inspects the shell command and denies those, while
deliberately allowing `.env.example` — that file is how Claude is meant to learn which keys
exist.

It matches on the command text, so a command that merely *mentions* a secret filename is
blocked too. That is the intended trade: the false positives are rare and loud, and the escape
hatch is to run the command yourself with the `!` prefix.

Test it after any change:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}' | .claude/hooks/guard-secrets.sh
# → a permissionDecision: "deny" payload
```

**`session-context.sh`** front-loads a few facts that otherwise cost three tool calls every
session: current branch and dirty-file count, the `package.json` scripts, and which package
manager the lockfile implies. Keep its output short — it is prepended to every session.

Both hooks fail open if `jq` is missing, rather than blocking all work.

## Permissions

`settings.json` allows read-only inspection (git status/diff/log, ripgrep, find) and the
standard check commands, so ordinary work does not generate prompts. It denies secret reads
and history-rewriting git commands outright, and asks before anything that leaves the machine
— `git push`, `gh pr merge`, `npm publish`, `vercel`.

Adjust the allowlist to the project's real package manager. The defaults cover pnpm and npm.

## Bundled skills

`.claude/settings.json` declares one plugin dependency:

```json
"enabledPlugins": { "mattpocock-skills@claude-plugins-official": true }
```

[mattpocock/skills](https://github.com/mattpocock/skills) — engineering skills covering TDD,
code review, domain modelling, diagnosing bugs, spec and ticket flows, grilling a plan, and
writing docs for agents. Anyone who clones this kit gets them; it resolves from Claude Code's
official marketplace, so there is no marketplace to add first.

It is declared, not vendored. The upstream README warns that installing the plugin *and*
copying the skill files leaves you with every skill twice — so the kit takes the plugin route,
which also means updates arrive from upstream instead of freezing at today's copy.

To hack on the skills rather than subscribe to them, drop the `enabledPlugins` entry and run
`npx skills@latest add mattpocock/skills` instead, which copies editable files into the project.

## Notes

- Hooks are picked up by the settings watcher only for directories that had a settings file
  when the session started. In a fresh copy, open `/hooks` once or restart Claude Code.
- `settings.local.json` is gitignored by `.claude/.gitignore`. Keep real secrets in
  `.env.local` — which the guard blocks — and list the key names in `.env.example`.
