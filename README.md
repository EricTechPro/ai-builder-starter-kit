# AI Builder Starter Kit

My Claude Code + Codex setup, with curated skills and a reusable project template for building AI products.

## What's inside

- **Skills** — 25 bundled skills for planning, development, debugging, code review, and documentation.
- **Project template** — shared instructions in `AGENTS.md` and capabilities in `.agents/`.
- **Workflows** — commands to verify changes, ship work, and evaluate prompts.
- **Claude Code setup** — adapters, permissions, and hooks that connect to the shared configuration.

Clone the repo, copy the setup into your project, and make it your own. No framework or package dependencies to install; the hooks use `jq`.

## Use it

```bash
cp -R ai-builder-starter-kit/.agents  your-project/.agents
cp -R ai-builder-starter-kit/.claude  your-project/.claude   # Claude Code adapter
cp    ai-builder-starter-kit/AGENTS.md your-project/AGENTS.md
cp    ai-builder-starter-kit/CLAUDE.md your-project/CLAUDE.md
```

Then fill in `AGENTS.md`. Every `<angle-bracket>` is a blank; delete the sections that do not
apply. Never edit `CLAUDE.md` for project guidance — it only imports `AGENTS.md`.

Copy `.agents/` alone if you are not using Claude Code.

## Layout

```
AGENTS.md                          Source of truth — instructions, any harness
.agents/                           Source of truth — capabilities, any harness
  skills/                          25 vendored skills + UPSTREAM.md provenance
  commands/
    verify.md                      /verify — run the check chain, report failures
    ship.md                        /ship   — verify, branch, commit, open PR
    eval.md                        /eval   — run or write an eval for a prompt change
  agents/
    prompt-reviewer.md             Reviews the app↔model seam
    cost-tracer.md                 Maps where tokens and latency go
  hooks/
    guard-secrets.sh               Blocks shell access to secrets
    session-context.sh             Branch, scripts, package manager
CLAUDE.md                          Adapter → imports AGENTS.md
.claude/
  settings.json                    Permissions + hook wiring (Claude-only concepts)
  settings.local.json.example      Personal overrides (copy, don't commit)
  skills    -> ../.agents/skills   symlink
  commands  -> ../.agents/commands symlink
  agents    -> ../.agents/agents   symlink
```

Nothing is duplicated. `.claude/` is three symlinks and one settings file.

### Installing new skills

Put them in `.agents/skills/`. Writing to `.claude/skills/` also works — it is a symlink, so
the files land in `.agents/skills/` regardless — but the real path keeps the source of truth
obvious.

The one way this forks silently is an installer that does `rm -rf .claude/skills` then `mkdir`,
turning the link into a real directory: two copies, edits landing in whichever one you opened.
`session-context.sh` checks all three links at session start and warns with the exact path and
fix if it happens. To repair it by hand:

```bash
mv .claude/skills/* .agents/skills/ 2>/dev/null
rm -rf .claude/skills
ln -s ../.agents/skills .claude/skills
```

**commands vs agents vs skills** — commands are what *you* invoke by name (`/verify`).
Agents are delegated fan-out work that returns a conclusion instead of a pile of file reads.
Skills load themselves when the task matches their description, which is why the discipline
you want applied *without remembering to ask for it* belongs in `skills/`.

## Why `.agents/` and `AGENTS.md`, both plural

Not a style choice — it is what the other harnesses actually look for. From Codex's source:
skills are resolved from `.agents/skills` directories discovered between the project root and
cwd, and project `AGENTS.md` files are concatenated walking root → cwd. Singular `.agent/` or
`AGENT.md` would be found by nothing.

So `.agents/skills/` is read **natively** by Codex — the adapter directory is only needed for
Claude Code, which looks in `.claude/`.

## The two hooks

**`guard-secrets.sh`** closes the door that permission rules leave open. Deny rules on the
Read tool do nothing about `cat` in a shell. This hook inspects the shell command and denies
those, while deliberately allowing the checked-in example env file — that file is how an agent
is meant to learn which keys exist.

It matches on the command text, so a command that merely *mentions* a secret filename is
blocked too. That is the intended trade: the false positives are rare and loud, and the escape
hatch is to run the command yourself with the `!` prefix.

Test it after any change:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}' | .agents/hooks/guard-secrets.sh
# → a permissionDecision: "deny" payload
```

**`session-context.sh`** front-loads a few facts that otherwise cost three tool calls every
session: current branch and dirty-file count, the `package.json` scripts, and which package
manager the lockfile implies. Keep its output short — it is prepended to every session.

Both scripts read JSON on stdin and write JSON on stdout, so they are not Claude-specific. Only
the *wiring* in `.claude/settings.json` is; another harness points its own hook config at the
same files.

Both fail open if `jq` is missing, rather than blocking all work.

## Permissions

`.claude/settings.json` allows read-only inspection (git status/diff/log, ripgrep, find) and
the standard check commands, so ordinary work does not generate prompts. It denies secret reads
and history-rewriting git commands outright, and asks before anything that leaves the machine
— `git push`, `gh pr merge`, `npm publish`, `vercel`.

Adjust the allowlist to the project's real package manager. The defaults cover pnpm and npm.

## Bundled skills

`.agents/skills/` holds 25 skills vendored from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT, v1.2.3) — TDD, code review,
domain modelling, diagnosing bugs, spec and ticket flows, grilling a plan, writing docs for
agents, and more. They are copied in, not installed as a plugin, so they travel with the repo
and can be edited in place. `.agents/skills/UPSTREAM.md` records the version, the commit, and
how to pull updates without discarding local edits.

Because they are copies, `settings.json` carries:

```json
"enabledPlugins": { "mattpocock-skills@claude-plugins-official": false }
```

That switches off the marketplace plugin **for this project only**, so the skills do not load
twice. A global install stays active everywhere else. Project settings override user settings,
which is what makes the project-scoped `false` stick.

If you would rather subscribe than fork — automatic updates, read-only — flip that value to
`true` and delete the vendored directories.

## Bring it to a live call

Found a bug, have a question, or want to suggest an improvement? [Open an issue](https://github.com/EricTechPro/ai-builder-starter-kit/issues). We’ll use the Issues page to choose what to work on together during every live call.

## Notes

- Hooks are picked up by the settings watcher only for directories that had a settings file
  when the session started. In a fresh copy, open `/hooks` once or restart Claude Code.
- The `.claude/*` symlinks are relative and committed as symlinks. On Windows without developer
  mode or `core.symlinks=true`, git checks them out as plain text files — replace them with
  real copies or junctions there.
- `settings.local.json` is gitignored by `.claude/.gitignore`. Keep real secrets in the local
  dotenv file — which the guard blocks — and list the key names in the example env file.
