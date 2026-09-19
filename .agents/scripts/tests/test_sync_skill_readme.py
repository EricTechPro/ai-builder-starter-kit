import importlib.util
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'sync_skill_readme.py'

class SyncTests(unittest.TestCase):
    def test_add_delete_and_preserve_prose(self):
        spec = importlib.util.spec_from_file_location('sync', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / '.agents/skills/demo').mkdir(parents=True)
            (root / '.agents/skills/demo/SKILL.md').write_text('---\nname: demo\n---\n')
            (root / '.agents/skills/families.json').write_text('{"families": []}')
            (root / '.agents/skills/UPSTREAM.md').write_text('')
            readme = root / 'README.md'
            readme.write_text('Before\n<!-- skills:start -->\nold\n<!-- skills:end -->\nAfter\n')
            self.assertTrue(module.sync(root))
            self.assertIn('| Local Skills | 1 |', readme.read_text())
            self.assertTrue(readme.read_text().startswith('Before\n'))
            self.assertTrue(readme.read_text().endswith('\nAfter\n'))
            self.assertFalse(module.sync(root))
            (root / '.agents/skills/demo/SKILL.md').unlink()
            module.sync(root)
            self.assertNotIn('| Local Skills |', readme.read_text())


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        import shutil
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        source = SCRIPT.parents[2]
        for path in ['.agents/scripts/sync_skill_readme.py', '.agents/skills/families.json', '.agents/skills/UPSTREAM.md', 'README.md']:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / path, target)
        for name in ['phone-mode', 'graphify', 'tdd']:
            self.skill(name)

    def skill(self, name):
        path = self.root / '.agents/skills' / name / 'SKILL.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('---\nname: ' + name + '\ndescription: test skill\n---\n')
        return path

    def command(self, *args, ok=True):
        import subprocess
        result = subprocess.run(['python3', str(self.root / '.agents/scripts/sync_skill_readme.py'), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        return result

    def git(self, *args):
        import subprocess
        return subprocess.check_output(['git', '-C', str(self.root), *args]).decode()

    def test_new_upstream_and_metadata_changes(self):
        import json
        self.skill('caveman')
        with (self.root / '.agents/skills/UPSTREAM.md').open('a') as file:
            file.write('\n| `caveman` | [juliusbrussee/caveman](https://github.com/juliusbrussee/caveman) | today |\n')
        self.command()
        text = (self.root / 'README.md').read_text()
        self.assertIn('| [juliusbrussee/caveman](https://github.com/juliusbrussee/caveman) | 1 |', text)
        self.assertIn('| Eric Tech’s Skills | 1 | Custom skills created and curated by Eric Tech. |', text)
        config = self.root / '.agents/skills/families.json'
        data = json.loads(config.read_text())
        data['families'][0]['description'] = 'Updated engineering workflow.'
        config.write_text(json.dumps(data))
        self.command('--check', ok=False)
        self.command()
        self.assertIn('Updated engineering workflow.', (self.root / 'README.md').read_text())
        before = (self.root / 'README.md').read_bytes()
        self.skill('tdd').write_text('Changed skill body')
        self.command()
        self.assertEqual(before, (self.root / 'README.md').read_bytes())

    def test_invalid_metadata_and_markers_leave_readme_intact(self):
        import json
        readme = self.root / 'README.md'
        before = readme.read_bytes()
        config = self.root / '.agents/skills/families.json'
        original = config.read_text()
        data = json.loads(original)
        data['families'][0]['description'] = 'word ' * 16
        config.write_text(json.dumps(data))
        self.command(ok=False)
        self.assertEqual(before, readme.read_bytes())
        config.write_text(original)
        readme.write_text('Unrelated README with no markers\n')
        self.command(ok=False)
        self.assertEqual('Unrelated README with no markers\n', readme.read_text())

    def test_git_hook_uses_index_and_never_stages(self):
        self.git('init', '-q')
        self.command()
        self.git('add', '.')
        self.command('--install-hook')
        self.command('--install-hook')
        self.command('--pre-commit')
        self.skill('untracked')
        self.command('--pre-commit') # untracked skill cannot invalidate staged snapshot
        self.git('add', '.agents/skills/untracked')
        index = self.git('write-tree')
        self.command('--pre-commit', ok=False)
        self.assertEqual(index, self.git('write-tree'))
        self.assertIn('| Local Skills | 1 |', (self.root / 'README.md').read_text())
        self.git('add', 'README.md')
        self.command('--pre-commit')
        self.git('rm', '-q', '-f', '.agents/skills/phone-mode/SKILL.md')
        self.command('--pre-commit', ok=False)
        self.assertNotIn('| Eric Tech’s Skills |', (self.root / 'README.md').read_text())
        self.git('add', 'README.md')
        self.command('--pre-commit')

    def test_existing_hooks_are_preserved(self):
        self.git('init', '-q')
        hook = self.root / '.git/hooks/pre-commit'
        hook.write_text('existing hook\n')
        self.command('--install-hook', ok=False)
        self.assertEqual('existing hook\n', hook.read_text())
        self.git('config', 'core.hooksPath', 'custom-hooks')
        self.command('--install-hook', ok=False)

    def test_watcher_reacts_without_harness(self):
        import subprocess
        import time
        self.command()
        process = subprocess.Popen(['python3', str(self.root / '.agents/scripts/sync_skill_readme.py'), '--watch'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.skill('watched')
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if '| Local Skills | 1 |' in (self.root / 'README.md').read_text():
                    break
                time.sleep(0.1)
            self.assertIn('| Local Skills | 1 |', (self.root / 'README.md').read_text())
        finally:
            process.terminate()
            process.wait(timeout=3)

    def test_legacy_skill_claims_only(self):
        readme = self.root / 'README.md'
        readme.write_text('A skills pack for coding agents: **28 skills, 3 commands, 5 guards.**\n'
                          '![Skills](https://img.shields.io/badge/skills-28-000000?style=flat-square)\n'
                          'A separate example: 99 skills.\n' + readme.read_text())
        self.command()
        self.assertIn('**3 skills, 3 commands, 5 guards.**', readme.read_text())
        self.assertIn('/badge/skills-3-', readme.read_text())
        self.assertIn('A separate example: 99 skills.', readme.read_text())

if __name__ == '__main__':
    unittest.main()


class EvalColumnTests(unittest.TestCase):
    """The Eval column is the only thing in the README that says why a skill is
    here. A family with no measurement has to read as "no measurement", never as
    a blank that looks like a passing grade."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location('sync', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / '.agents/skills/demo').mkdir(parents=True)
        (self.root / '.agents/skills/demo/SKILL.md').write_text('---\nname: demo\n---\n')
        (self.root / '.agents/skills/UPSTREAM.md').write_text('')
        (self.root / 'README.md').write_text(
            'A skills pack for coding agents: **9 skills,** x\n'
            '<!-- skills:start -->\nold\n<!-- skills:end -->\n')

    def families(self, text):
        (self.root / '.agents/skills/families.json').write_text(text)

    def test_family_with_an_eval_links_into_the_ledger(self):
        self.families('{"families": [{"name": "Demo", "description": "d",'
                      ' "skills": ["demo"],'
                      ' "eval": {"verdict": "Kept, +0.40", "anchor": "demo-vs-other"}}]}')
        self.module.sync(self.root)
        self.assertIn('[Kept, +0.40](.agents/skills/EVALS.md#demo-vs-other)',
                      (self.root / 'README.md').read_text())

    def test_family_without_an_eval_says_so(self):
        self.families('{"families": [{"name": "Demo", "description": "d", "skills": ["demo"]}]}')
        self.module.sync(self.root)
        self.assertIn('| Demo | 1 | d | \u2014 |', (self.root / 'README.md').read_text())

    def test_anchor_must_be_a_slug(self):
        self.families('{"families": [{"name": "Demo", "description": "d", "skills": ["demo"],'
                      ' "eval": {"verdict": "Kept", "anchor": "Not A Slug"}}]}')
        with self.assertRaises(ValueError):
            self.module.sync(self.root)
        self.assertIn('old', (self.root / 'README.md').read_text())

    def test_skill_count_survives_the_extra_column(self):
        self.families('{"families": [{"name": "Demo", "description": "d", "skills": ["demo"],'
                      ' "eval": {"verdict": "Kept", "anchor": "demo"}}]}')
        self.module.sync(self.root)
        self.assertIn('**1 skills,**', (self.root / 'README.md').read_text())
