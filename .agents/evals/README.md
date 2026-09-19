# Eval results

A skill is a prompt, and a prompt change is a code change with no type checker. This folder
is the substitute: one file per eval, recording what was tested, what came back, which model
it ran on, and what was decided as a result.

**Raw results are not in git.** `.gitignore` excludes `.agents/skills/*/evals/results/`,
because a single HTML report runs to 1.4 MB. The write-ups here are the durable record. The
index below is generated from their front matter, so it survives a fresh clone.

<!-- evals:start -->
| Eval | Skill | Installed | Model | Cases | Score | Δ | Verdict |
|---|---|---|---|---:|---:|---:|---|
| [diagnosing-bugs vs systematic-debugging](diagnosing-bugs.md) | `diagnosing-bugs` | yes | `claude-opus-5` | 11 | 0.89 | +0.00 | Kept diagnosing-bugs, dropped the challenger |
| [archify](archify.md) | `archify` | yes | `claude-opus-5` | 3 | 0.30 | -0.04 | Not recorded, suite looks unsound |
| [phone-mode](phone-mode.md) | `phone-mode` | yes | `claude-opus-5` | 5 | 0.62 | +0.06 | Kept, over-fires on a near-miss |
| [caveman](caveman.md) | `caveman` | yes | `claude-opus-5` | 5 | 1.00 | +0.12 | Kept, +0.40 on the safety case |
<!-- evals:end -->

## How to read a score

Every suite runs each case twice: once with the skill loaded (`with`) and once with no
plugin at all (`base`). The delta is what the skill actually bought. A skill that scores
1.00 with and 1.00 without did nothing.

Judges are LLMs voting per grader, so run-to-run spread is real. On the debugging bakeoff,
two independent measurements of the *same* baseline differed by 0.30. **Treat anything under
about ±0.2 at n=2 as noise and re-run before believing it.** Both cases that separated at
n=2 in that suite reversed at n=6.

`Model` is the subject model the cases ran against, read back out of the run traces. Graders
run on a separate judge model, `haiku` by default; the CLI does not record it in the result
file, so it is taken from `--judge-model`'s documented default.

## Keeping this current

```bash
python3 .agents/scripts/sync_eval_index.py --ingest   # pull in finished runs
python3 .agents/scripts/sync_eval_index.py --check    # stale? exit 1
```

`--ingest` finds any run newer than the one on record, updates that file's front matter
numbers, and tells you which write-ups now need their tables and verdict brought up to date.
It never writes prose. A score is not a decision, and the point of this folder is the
decision. It runs automatically at the end of a session via
[`sync-eval-index.sh`](../hooks/sync-eval-index.sh).

The `Installed` column reads from disk. A removed skill keeps its page on purpose: the
record of why something was dropped is worth more than the record of why it was kept.

## Adding one

Every new skill needs an eval; the Stop hook in
[`gate-skill-evals.sh`](../hooks/gate-skill-evals.sh) enforces it. A usable suite needs
cases that test triggering, not just output:

- requests that **should** fire the skill, phrased the way a real user would
- near-miss requests that should **not** fire it
- at least one adversarial case: hostile instructions inside the input data
- graders that check the property that matters, not string similarity to a golden answer

```bash
cd .agents/skills/<skill> && claude plugin eval init
claude plugin eval .agents/skills/<skill> --threshold 0.8
```

Then write `.agents/evals/<skill>.md` with front matter (`skill`, `title`, `run`, `date`,
`model`, `cases`, `score`, `delta`, `cost_usd`, `verdict`), run the sync, and give the
family an `"eval"` entry in [`families.json`](../skills/families.json) so the README table
links here.
