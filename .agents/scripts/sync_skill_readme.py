#!/usr/bin/env python3
"""Keep the README skill-family table in sync. Python standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

START = '<!-- skills:start -->'
END = '<!-- skills:end -->'
CONFIG = '.agents/skills/families.json'
PROVENANCE = '.agents/skills/UPSTREAM.md'
EVALS = '.agents/evals'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode()


def read(root, path, staged=False):
    return git(root, 'show', ':' + path) if staged else (root / path).read_text()


def inventory(root, staged=False):
    if staged:
        paths = git(root, 'ls-files', '-z', '--', '.agents/skills').split('\0')
        return sorted({p.split('/')[2] for p in paths if re.fullmatch(r'\.agents/skills/[^/]+/SKILL\.md', p)})
    directory = root / '.agents/skills'
    if not directory.is_dir():
        raise ValueError('Missing .agents/skills directory')
    return sorted(p.name for p in directory.iterdir() if p.is_dir() and (p / 'SKILL.md').is_file())


def verdict(family):
    """Eval cell for a family: a link to its write-up in .agents/evals, or an
    explicit em dash. A blank would read as a passing grade rather than as the
    absence of a measurement."""
    entry = family.get('eval')
    if not entry:
        return '—'
    page = cell(entry['page'])
    if not re.fullmatch(r'[a-z0-9-]+', page):
        raise ValueError('Family eval pages must be lowercase-hyphen slugs: ' + page)
    return '[' + cell(entry['verdict']) + '](' + EVALS + '/' + page + '.md)'


def cell(value):
    if not isinstance(value, str) or not value.strip() or any(c in value for c in '\n\r|'):
        raise ValueError('Family text must be a nonempty, single-line Markdown table cell')
    return value


def table(root, staged=False):
    families = json.loads(read(root, CONFIG, staged))['families']
    by_source, by_skill = {}, {}
    for family in families:
        cell(family['name'])
        cell(family['description'])
        if len(family['description'].split()) > 15:
            raise ValueError('Family descriptions must contain at most 15 words')
        source = family.get('source')
        if source:
            cell(source)
            if not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+', source):
                raise ValueError('Family sources must be GitHub repository URLs')
            if source in by_source:
                raise ValueError('Duplicate family source: ' + source)
            by_source[source] = family
        for skill in family.get('skills', []):
            if skill in by_skill:
                raise ValueError('Duplicate skill assignment: ' + skill)
            by_skill[skill] = family
    # Explicit provenance rows override the seeded assignments. New upstream families
    # become rows automatically; their short summary can be customized in families.json.
    provenance = read(root, PROVENANCE, staged)
    for skill, label, source in re.findall(r'^\|\s*`([^`]+)`\s*\|\s*\[([^\]]+)\]\((https://github\.com/[\w.-]+/[\w.-]+)/?\)', provenance, re.M):
        if source not in by_source:
            family = {'name': cell(label), 'source': source, 'description': 'Additional skills from this upstream project.', 'link': True}
            families.append(family)
            by_source[source] = family
        by_skill[skill] = by_source[source]
    local = {'name': 'Local Skills', 'description': 'Skills without an assigned source family.'}
    families.append(local)
    counts = {id(f): 0 for f in families}
    for skill in inventory(root, staged):
        counts[id(by_skill.get(skill, local))] += 1
    lines = ['| Skill Family | # Skills | Description Short Brief (max 15 words) | Eval |', '|---|---:|---|---|']
    for family in families:
        count = counts[id(family)]
        if not count:
            continue
        name = family['name']
        if family.get('source') and family.get('link', True):
            name = '[' + name + '](' + family['source'] + ')'
        lines.append(f"| {name} | {count} | {family['description']} | {verdict(family)} |")
    return '\n'.join(lines)


def render(text, generated):
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('README must contain exactly one skills:start / skills:end marker pair; see .agents/hooks/README-skills.md')
    before, rest = text.split(START)
    current, after = rest.split(END)
    updated = before + START + '\n' + generated + '\n' + END + after
    count = sum(int(n) for n in re.findall(r'^\| .*? \| (\d+) \|', generated, re.M))
    # Compatibility with this kit's compact README: only its known skill claims.
    updated = re.sub(r'(A skills pack for coding agents: \*\*)\d+( skills,)', lambda m: m[1] + str(count) + m[2], updated)
    updated = re.sub(r'(https://img\.shields\.io/badge/skills-)\d+(-)', lambda m: m[1] + str(count) + m[2], updated)
    return updated


def sync(root, check=False):
    path = root / 'README.md'
    original = path.read_text()
    updated = render(original, table(root))
    if original == updated:
        return False
    if check:
        raise ValueError('README skill table is stale. Run python3 .agents/scripts/sync_skill_readme.py')
    # Validate everything before touching README; atomic replacement avoids partial writes.
    with tempfile.NamedTemporaryFile(mode='w', dir=root, prefix='.readme-skills-', delete=False) as file:
        temp = Path(file.name)
        file.write(updated)
    try:
        os.chmod(temp, path.stat().st_mode)
        if path.read_text() != original:
            raise ValueError('README changed during sync; retry')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return True


def pre_commit(root):
    original = read(root, 'README.md', staged=True)
    if render(original, table(root, staged=True)) != original:
        sync(root)
        raise ValueError('Staged README table is stale. Working README refreshed; review and stage the table with your skill changes, then commit again. No files were staged automatically.')


def install(root):
    if subprocess.run(['git', '-C', str(root), 'config', '--get', 'core.hooksPath'], capture_output=True).returncode == 0:
        raise ValueError('Existing core.hooksPath: add the command from .agents/hooks/README-skills.md to your existing pre-commit hook')
    target = Path(git(root, 'rev-parse', '--git-path', 'hooks/pre-commit').strip())
    if not target.is_absolute():
        target = root / target
    content = '#!/bin/sh\nexec python3 "$(git rev-parse --show-toplevel)/.agents/scripts/sync_skill_readme.py" --pre-commit\n'
    if target.exists():
        if target.read_text() == content:
            return
        raise ValueError('Existing pre-commit hook preserved. Add the command from .agents/hooks/README-skills.md to it')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as file:
        file.write(content)
    target.chmod(0o755)
    print('Installed Git pre-commit hook')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--watch', action='store_true', help='Refresh every second until Ctrl-C, regardless of editor or agent')
    mode.add_argument('--pre-commit', action='store_true')
    mode.add_argument('--install-hook', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        if args.install_hook:
            install(root)
        elif args.pre_commit:
            pre_commit(root)
        elif args.watch:
            last_error = None
            while True:
                try:
                    if sync(root):
                        print('Updated README skill table', flush=True)
                    last_error = None
                except (ValueError, OSError, KeyError) as error:
                    if str(error) != last_error:
                        print(str(error), file=sys.stderr, flush=True)
                    last_error = str(error)
                time.sleep(1)
        else:
            if sync(root, args.check):
                print('Updated README skill table')
    except KeyboardInterrupt:
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print('Skill README sync: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
