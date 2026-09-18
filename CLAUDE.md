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
  Install and edit under `.agents/` — going through the link works (it resolves to the same
  files) but reach for the real path so the source of truth stays obvious.
- **Never replace one of those symlinks with a real directory.** If a skill installer wants to
  create `.claude/skills/`, point it at `.agents/skills/` instead, or move the result there and
  restore the link. The SessionStart hook warns when one of them has become a real directory.
- `.claude/settings.json` holds what only Claude Code understands: the permission allow/deny/ask
  rules and the hook wiring. The hook *scripts* themselves live in `.agents/hooks/` and read
  JSON on stdin, so another harness can call them too.
- `/verify`, `/ship` and `/eval` are defined in `.agents/commands/`.
- Skills in `.agents/skills/` load by description match. Codex reads that directory natively;
  Claude Code reaches it through the symlink.
