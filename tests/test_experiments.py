from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tools.new_experiment import create_experiment


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'experiments').mkdir()
        (self.root / 'templates').mkdir()
        (self.root / 'templates/experiment.md').write_text('# {{id}}: {{title}}\n{{date}}\nplanned\n', encoding='utf-8')
        (self.root / 'experiments/index.json').write_text(json.dumps({
            'schema': 'plc-phy-lab.experiments.v1', 'experiments': []}), encoding='utf-8')

    def test_creates_planned_record_and_registry(self):
        directory = create_experiment(self.root, 'first-test', 'First experiment')
        self.assertEqual(directory.name, 'EXP-0001-first-test')
        self.assertIn('EXP-0001', (directory / 'README.md').read_text(encoding='utf-8'))
        entry = json.loads((self.root / 'experiments/index.json').read_text(encoding='utf-8'))['experiments'][0]
        self.assertEqual(entry['status'], 'planned')
        self.assertIsNone(entry['performed_date'])

    def test_second_record_has_new_id(self):
        create_experiment(self.root, 'first-test', 'First')
        directory = create_experiment(self.root, 'second-test', 'Second')
        self.assertEqual(directory.name, 'EXP-0002-second-test')

    def test_duplicate_slug_does_not_overwrite(self):
        directory = create_experiment(self.root, 'first-test', 'Original')
        before = (directory / 'README.md').read_text(encoding='utf-8')
        with self.assertRaises(ValueError):
            create_experiment(self.root, 'first-test', 'Replacement')
        self.assertEqual((directory / 'README.md').read_text(encoding='utf-8'), before)

    def test_path_traversal_is_rejected(self):
        for slug in ['../outside', 'a/b', '..', 'a--b', 'a\\b']:
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                create_experiment(self.root, slug, 'Bad path')
