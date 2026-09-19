# Keep the README skills table current

Python 3.9+ is the only dependency. No model calls or network access are used.

Run once from the repository root:

```sh
python3 .agents/scripts/sync_skill_readme.py --install-hook
```

This installs a Git `pre-commit` hook for this checkout, regardless of whether Claude Code,
Codex, Cursor, another agent, or a human makes the commit. Existing hooks and `core.hooksPath`
are preserved; if one is present, add this command to its pre-commit flow instead:

```sh
python3 "$(git rev-parse --show-toplevel)/.agents/scripts/sync_skill_readme.py" --pre-commit
```

The hook checks the **staged** skills, provenance, family metadata and README. If that table
is stale, it refreshes the working README and stops the commit. Review and stage the table
alongside your skill changes, then retry. It never stages files or unrelated README edits.
With partially staged skills, the working-tree table can differ from the staged inventory:
stage the intended skill set together or edit/stage just the matching table. Git hooks run
only on commits and can be bypassed with `--no-verify`; installation is per clone.

For updates while editing with **any** harness, keep this running in a terminal:

```sh
python3 .agents/scripts/sync_skill_readme.py --watch
```

It rechecks every second until Ctrl-C. Claude Code also invokes the same updater after
Edit, Write, NotebookEdit, and Bash tools through its project settings. Other harnesses do
not share Claude's hook API: use the watcher for immediate updates or the Git hook at commit.
The watcher is opt-in and is not installed as a background service.

Manual update or read-only check:

```sh
python3 .agents/scripts/sync_skill_readme.py
python3 .agents/scripts/sync_skill_readme.py --check
```

## Family attribution and descriptions

- Installed `.agents/skills/<name>/SKILL.md` files determine counts. Empty families disappear.
- `.agents/skills/families.json` holds the known family names, short summaries, optional links,
  and explicit skill assignments. Keep descriptions at 15 words or fewer.
- The `Other vendored skills` table in `UPSTREAM.md` supplies additional source assignments.
  Its `| `skill` | [owner/repo](https://github.com/owner/repo) ... |` rows override seeded
  assignments. A new source gets a row automatically; add its source and preferred summary
  to `families.json` to customize the row. Record provenance when installing external skills.
- Unassigned skills appear under **Local Skills**, avoiding incorrect author attribution.
- Eric Tech's family deliberately has no link. Editing a skill's contents triggers a recheck,
  but does not invent a new family summary; update the metadata if the family's purpose changes.

The table between `<!-- skills:start -->` and `<!-- skills:end -->` is regenerated.
The compact starter-kit headline and skills badge, when present, also get the current
skill count. Other README content is preserved.
Missing or duplicate markers and invalid metadata fail without writing the README. When
adopting this into another README, manually place those markers around its existing skills
family table first. The updater never guesses which unrelated Markdown table to replace.

Tests: `python3 -m unittest discover -s .agents/scripts/tests`.
