import importlib.util
import json
import pathlib
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'sync_eval_index.py'

PAGE = """---
skill: demo
title: demo
run: 2026-01-01T00-00-00-000Z
date: 2026-01-01
model: claude-opus-5
cases: 4
score: 0.80
delta: 0.10
cost_usd: 1.00
verdict: Kept
---

Body.
"""


class EvalIndexTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('idx', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        (self.root / '.agents/evals').mkdir(parents=True)
        (self.root / '.agents/skills/demo').mkdir(parents=True)
        (self.root / '.agents/skills/demo/SKILL.md').write_text('---\nname: demo\n---\n')
        self.page = self.root / '.agents/evals/demo.md'
        self.page.write_text(PAGE)
        self.readme = self.root / '.agents/evals/README.md'
        self.readme.write_text('Before\n<!-- evals:start -->\nold\n<!-- evals:end -->\nAfter\n')

    def result(self, stamp, cases=5, score=0.5, delta=-0.2, cost=2.0):
        path = self.root / '.agents/skills/demo/evals/results' / stamp
        path.mkdir(parents=True)
        (path / 'aggregate-result.json').write_text(json.dumps({
            'costUsd': cost,
            'aggregates': {'casesTotal': cases, 'overallScore': score, 'meanDelta': delta},
            'trace': '\\"canonicalModel\\":\\"claude-opus-5\\"',
        }))

    def test_index_is_built_and_prose_preserved(self):
        self.assertTrue(self.module.sync(self.root))
        text = self.readme.read_text()
        self.assertIn('| [demo](demo.md) | `demo` | yes | `claude-opus-5` | 4 | 0.80 | +0.10 | Kept |', text)
        self.assertTrue(text.startswith('Before\n'))
        self.assertTrue(text.endswith('\nAfter\n'))
        self.assertFalse(self.module.sync(self.root))

    def test_removed_skill_keeps_its_page_and_is_marked(self):
        (self.root / '.agents/skills/demo/SKILL.md').unlink()
        self.module.sync(self.root)
        self.assertIn('| **removed** |', self.readme.read_text())
        self.assertIn('[demo](demo.md)', self.readme.read_text())

    def test_ingest_takes_the_newer_run_only(self):
        self.result('2025-06-01T00-00-00-000Z')          # older than what is on record
        self.assertEqual(self.module.ingest(self.root), [])
        self.assertIn('score: 0.80', self.page.read_text())
        self.result('2026-09-19T00-00-00-000Z', cases=7, score=0.42, delta=0.33, cost=9.5)
        changed = self.module.ingest(self.root)
        self.assertEqual(len(changed), 1)
        text = self.page.read_text()
        self.assertIn('run: 2026-09-19T00-00-00-000Z', text)
        self.assertIn('cases: 7', text)
        self.assertIn('score: 0.42', text)
        self.assertIn('delta: +0.33', text)
        self.assertIn('cost_usd: 9.50', text)

    def test_ingest_never_rewrites_the_verdict_or_the_prose(self):
        self.result('2026-09-19T00-00-00-000Z', score=0.10)
        self.module.ingest(self.root)
        text = self.page.read_text()
        self.assertIn('verdict: Kept', text)
        self.assertIn('Body.', text)

    def test_smoke_runs_are_not_mistaken_for_suites(self):
        self.result('2026-09-19T00-00-00-000Z', cases=1)
        self.assertEqual(self.module.ingest(self.root), [])

    def test_missing_front_matter_key_is_refused(self):
        self.page.write_text(PAGE.replace('verdict: Kept\n', ''))
        with self.assertRaises(ValueError):
            self.module.sync(self.root)
        self.assertIn('old', self.readme.read_text())

    def test_check_mode_reports_staleness_without_writing(self):
        with self.assertRaises(ValueError):
            self.module.sync(self.root, check=True)
        self.assertIn('old', self.readme.read_text())
