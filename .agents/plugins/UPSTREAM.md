# Vendored plugins

Claude Code plugins, checked in so a clone gets them without a network fetch or a
per-machine `/plugin marketplace add`. Wired up in `.claude/settings.json` via
`extraKnownMarketplaces` + `enabledPlugins`, which is the documented way to give a
team the same plugin sources.

| Plugin | Source | Pinned at | Vendored on |
| --- | --- | --- | --- |
| `codex` (marketplace `openai-codex`, v1.0.6) | [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) | `db52e28` | 2026-09-19 |
| `claudex-loop` (marketplace `claudex-loop`, v2.1.0) | [chaseai-yt/claudex-loop](https://github.com/chaseai-yt/claudex-loop) | `8cf5e2c` | 2026-09-19 |

Both are MIT. Each directory is the upstream repo with `.git/` removed, so the
vendored copy is a snapshot, not a submodule.

## Why the paths are relative

`claude plugin marketplace add ./path --scope project` writes an **absolute** path,
which breaks on every other clone. The paths in `.claude/settings.json` were changed
to `./.agents/plugins/<name>` by hand afterwards. Verified: the relative form resolves
against the project directory, and `claude plugin marketplace list` prints the same
absolute path for both forms. **Re-running `marketplace add` re-absolutises them** —
if you do, change them back.

## Updating

```bash
rm -rf .agents/plugins/<name>
git clone --depth 1 <url> .agents/plugins/<name>
rm -rf .agents/plugins/<name>/.git
```

Then update the pinned SHA in the table above. No `npm install` is needed for either:
`codex` runs on Node 18.18+, `claudex-loop` on Python 3.10+, neither has runtime deps.
Both still require the `codex` and `claude` CLIs to be installed and authenticated —
the plugins drive those binaries, they do not replace them.
