#!/usr/bin/env python3
"""Keep .agents/evals/README.md in sync. Python standard library only.

One file per eval in `.agents/evals/`, each carrying its numbers in front
matter. This script builds the index table from that front matter, and can pull
fresh numbers out of a finished run.

Why the index is built from the write-ups and not from the results directory:
`.gitignore` excludes `.agents/skills/*/evals/results/`, because one HTML report
runs to 1.4 MB. On a fresh clone there are no results at all. An index generated
from them would come back empty and silently delete the only record of why the
skills here are the ones here.

So the front matter is the record, and `--ingest` is how a finished run gets
into it:

    python3 .agents/scripts/sync_eval_index.py            # rebuild the index
    python3 .agents/scripts/sync_eval_index.py --check    # stale? exit 1
    python3 .agents/scripts/sync_eval_index.py --ingest   # pull in new runs

`--ingest` only ever touches the numbers. The verdict and the prose are written
by a person, because "0.62" is not a decision.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

START = '<!-- evals:start -->'
END = '<!-- evals:end -->'
EVALS = '.agents/evals'
SKILLS = '.agents/skills'
NUMERIC = {'cases': int, 'score': float, 'delta': float, 'cost_usd': float}
REQUIRED = ['skill', 'title', 'run', 'date', 'model', 'cases', 'score', 'verdict']


def front_matter(text, path):
    """Parse the leading `---` block. Flat `key: value` only, which is all the
    index needs and avoids a YAML dependency in a stdlib-only script."""
    match = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError(path.name + ': missing front matter')
    data = {}
    for line in match[1].splitlines():
        if not line.strip():
            continue
        if ':' not in line:
            raise ValueError(path.name + ': not a key: value line: ' + line)
        key, _, value = line.partition(':')
        key, value = key.strip(), value.strip()
        if any(c in value for c in '\n|'):
            raise ValueError(path.name + ': value must be a single table cell: ' + key)
        data[key] = NUMERIC[key](value) if key in NUMERIC else value
    for key in REQUIRED:
        if key not in data:
            raise ValueError(path.name + ': missing required key: ' + key)
    return data


def entries(root):
    out = []
    for path in sorted((root / EVALS).glob('*.md')):
        if path.name == 'README.md':
            continue
        data = front_matter(path.read_text(), path)
        data['path'] = path.name
        # An eval whose skill was uninstalled is the most useful row in the
        # table, not a row to drop: it is the record of a decision to remove.
        data['installed'] = (root / SKILLS / data['skill'] / 'SKILL.md').is_file()
        out.append(data)
    return sorted(out, key=lambda d: (d['date'], d['skill']), reverse=True)


def table(root):
    lines = ['| Eval | Skill | Installed | Model | Cases | Score | Δ | Verdict |',
             '|---|---|---|---|---:|---:|---:|---|']
    for d in entries(root):
        delta = '%+.2f' % d['delta'] if 'delta' in d else '—'
        lines.append('| [%s](%s) | `%s` | %s | `%s` | %d | %.2f | %s | %s |' % (
            d['title'], d['path'], d['skill'], 'yes' if d['installed'] else '**removed**',
            d['model'], d['cases'], d['score'], delta, d['verdict']))
    return '\n'.join(lines)


def render(text, generated):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('README must contain exactly one evals:start / evals:end marker pair')
    before, rest = text.split(START)
    _, after = rest.split(END)
    return before + START + '\n' + generated + '\n' + END + after


def newest_run(root, skill, min_cases=3):
    """Newest result for a skill that looks like a suite rather than a smoke run."""
    best = None
    for path in (root / SKILLS / skill / 'evals/results').glob('*/aggregate-result.json'):
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if data.get('aggregates', {}).get('casesTotal', 0) < min_cases:
            continue
        if best is None or path.parent.name > best[0]:
            best = (path.parent.name, data, path)
    return best


def model_of(path):
    """The subject model, read back out of the run traces. The CLI records it
    per message rather than in a header field, so take the most common one."""
    raw = path.read_text()
    found = re.findall(r'\\"canonicalModel\\":\\"([^"\\]+)\\"', raw)
    return max(set(found), key=found.count) if found else 'unknown'


def ingest(root):
    changed = []
    for path in sorted((root / EVALS).glob('*.md')):
        if path.name == 'README.md':
            continue
        text = path.read_text()
        data = front_matter(text, path)
        found = newest_run(root, data['skill'])
        if not found or found[0] <= data['run']:
            continue
        stamp, result, json_path = found
        agg = result['aggregates']
        updates = {
            'run': stamp,
            'date': stamp[:10],
            'model': model_of(json_path),
            'cases': str(agg['casesTotal']),
            'score': '%.2f' % agg['overallScore'],
            'delta': '%+.2f' % agg['meanDelta'],
            'cost_usd': '%.2f' % result['costUsd'],
        }
        for key, value in updates.items():
            if re.search(r'^%s:.*$' % re.escape(key), text, re.M):
                text = re.sub(r'^%s:.*$' % re.escape(key), '%s: %s' % (key, value), text, count=1, flags=re.M)
            else:
                text = text.replace('\n---\n', '\n%s: %s\n---\n' % (key, value), 1)
        write(path, text)
        changed.append('%s: %s -> %s (score %s, the tables and the verdict are yours to update)'
                       % (path.name, data['run'], stamp, updates['score']))
    return changed


def write(path, text):
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.sync-', delete=False) as handle:
        temp = Path(handle.name)
        handle.write(text)
    try:
        if path.exists():
            os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def sync(root, check=False):
    path = root / EVALS / 'README.md'
    original = path.read_text()
    updated = render(original, table(root))
    if original == updated:
        return False
    if check:
        raise ValueError('Eval index is stale. Run python3 .agents/scripts/sync_eval_index.py')
    write(path, updated)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--ingest', action='store_true', help='Pull numbers from any run newer than the one on record')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        if args.ingest:
            for line in ingest(root):
                print('Ingested ' + line)
        if sync(root, args.check):
            print('Updated eval index')
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print('Eval index sync: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
