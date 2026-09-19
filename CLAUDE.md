# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

**This file is an adapter, not a source of truth.** The instructions live in `AGENTS.md`, so
that Codex and any other harness read the same thing. Put project guidance there, never here.

@AGENTS.md

If the import above did not pull it in, read `AGENTS.md` now before doing anything else.

## Claude Code specifics

Everything below is true only of this harness; it is deliberately absent from `AGENTS.md`.

- `.claude/skills`, `.claude/commands` and `.claude/agents` are **symlinks** into `.agents/`.
  Edit the real files under `.agents/` — editing through the link works, but reach for the
  real path so the source of truth stays obvious.
- `.claude/settings.json` holds what only Claude Code understands: the permission allow/deny/ask
  rules and the hook wiring. The hook *scripts* themselves live in `.agents/hooks/` and read
  JSON on stdin, so another harness can call them too.
- `/verify`, `/ship` and `/eval` are defined in `.agents/commands/`.
- Skills in `.agents/skills/` load by description match. Codex reads that directory natively;
  Claude Code reaches it through the symlink.
