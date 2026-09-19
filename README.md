# ai-builder-starter-kit

A skills pack for coding agents: **29 skills, 3 commands, 5 guards.** Python 3 is required for README sync.

![Skills](https://img.shields.io/badge/skills-29-000000?style=flat-square)
![Commands](https://img.shields.io/badge/commands-3-000000?style=flat-square)
![Guards](https://img.shields.io/badge/guards-5-000000?style=flat-square)
![Runtime](https://img.shields.io/badge/runtime-Python%203.9%2B-000000?style=flat-square)
[![Stars](https://img.shields.io/github/stars/EricTechPro/ai-builder-starter-kit?style=flat-square&color=000000)](https://github.com/EricTechPro/ai-builder-starter-kit)

## Install

Paste this into Claude Code, Codex or Cursor:

```
Clone https://github.com/EricTechPro/ai-builder-starter-kit into a temp dir and copy its
.agents/, .claude/, AGENTS.md and CLAUDE.md into this project, keeping .claude/ symlinks
intact. Then read AGENTS.md and help me fill in the blanks for this repo.
```

Claude Code reads `.claude/` (three symlinks into `.agents/`). Codex reads `.agents/` and
`AGENTS.md` natively. `AGENTS.md` is the only file you edit.

## Skills

<!-- skills:start -->
| Skill Family | # Skills | Description Short Brief (max 15 words) | Eval |
|---|---:|---|---|
| [Matt Pocock’s Skills](https://github.com/mattpocock/skills) | 25 | Planning, development, testing, debugging, architecture, research, and code review. | [Kept over obra/superpowers](.agents/skills/EVALS.md#diagnosing-bugs-vs-systematic-debugging) |
| Eric Tech’s Skills | 1 | Custom skills created and curated by Eric Tech. | [Kept, over-fires](.agents/skills/EVALS.md#phone-mode) |
| [Graphify](https://github.com/Graphify-Labs/graphify) | 1 | Build and query knowledge graphs of code, documentation, and project content. | — |
| [Archify](https://github.com/tt-a1i/archify) | 1 | Validated architecture, workflow, sequence, data-flow, and lifecycle diagrams as standalone HTML. | [0.30, undecided](.agents/skills/EVALS.md#archify) |
| [juliusbrussee/caveman](https://github.com/juliusbrussee/caveman) | 1 | Token compression with an auto-clarity layer that suspends it for irreversible steps. | [Kept, +0.40 on safety](.agents/skills/EVALS.md#caveman) |
<!-- skills:end -->

Vendored as copies, not plugins — they travel with the repo and you can edit them.
Provenance: [`UPSTREAM.md`](.agents/skills/UPSTREAM.md).

[Automatic README updates](.agents/hooks/README-skills.md): Git hook for every harness;
optional live watcher for updates while editing. Requires Python 3.9+.

## Commands

| | |
| --- | --- |
| [`/verify`](.agents/commands/verify.md) | Typecheck → lint → test → build. Stops at the first real failure |
| [`/ship`](.agents/commands/ship.md) | Verify, branch, commit, open the PR. Never commits to `main` |
| [`/eval`](.agents/commands/eval.md) | Scores a prompt change against a stashed baseline, per case |

## Guards

Hooks that run automatically. JSON in, JSON out — not Claude-specific.

| | |
| --- | --- |
| [guard-secrets](.agents/hooks/guard-secrets.sh) | Blocks shell commands that read a dotenv file or key |
| [guard-key-literals](.agents/hooks/guard-key-literals.sh) | Blocks a live key being pasted into source |
| [gate-skill-evals](.agents/hooks/gate-skill-evals.sh) | Won't let you ship a changed skill with no eval run |
| [gate-readme-skills](.agents/hooks/gate-readme-skills.sh) | Won't let this README's count drift from the tree |
| [session-context](.agents/hooks/session-context.sh) | Injects branch, scripts and package manager at startup |

Plus two subagents — [prompt-reviewer](.agents/agents/prompt-reviewer.md) and
[cost-tracer](.agents/agents/cost-tracer.md) — for LLM-seam review and token spend.

---

Skills load themselves on a description match. Commands you type. Guards run at their configured tool or session events.
Adding a skill? Write `SKILL.md`, add an eval, and record its source. The [README updater](.agents/hooks/README-skills.md) maintains this table and the skill counts.
