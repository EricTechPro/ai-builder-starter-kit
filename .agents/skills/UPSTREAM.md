# Vendored skills — provenance

These 25 skill directories are copied from **[mattpocock/skills](https://github.com/mattpocock/skills)**,
MIT licensed (see `LICENSE` in this directory).

| | |
| --- | --- |
| Upstream version | `1.2.3` |
| Upstream commit | `c55ee46` |
| Vendored on | 2026-09-18 |
| Set | the 25 skills listed in the upstream `.claude-plugin/plugin.json` — its curated set, which excludes `in-progress/`, `deprecated/` and `misc/` |

## Why vendored rather than installed as a plugin

The files live here so they travel with the repo and can be edited in place. That is the
trade upstream describes: the plugin route is a subscription that updates when Matt ships;
copying the files is a fork you own.

Because these are copies, `.claude/settings.json` sets
`"mattpocock-skills@claude-plugins-official": false` — that disables the marketplace plugin
**for this project only**, so the skills are not loaded twice. A global install stays active
in every other project.

## Updating

There is no automatic update. To pull upstream changes:

```bash
git clone --depth 1 https://github.com/mattpocock/skills.git /tmp/mp-skills
# review what changed against this directory before copying anything over
diff -rq /tmp/mp-skills/skills/engineering/tdd .agents/skills/tdd
```

Copy the directories you want and update the version and commit in the table above. Review
the diff rather than overwriting wholesale — the point of vendoring is that local edits are
yours to keep, and a blind copy discards them.

## Local edits

Record any deliberate divergence from upstream here, so the next update does not silently
revert it.

- _(none yet)_
