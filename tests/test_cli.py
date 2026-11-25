from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


class OfflineWorkflowTest(unittest.TestCase):
    def run_tool(self, *arguments):
        return subprocess.run([sys.executable, '-m', *arguments], cwd=ROOT,
                              text=True, capture_output=True, timeout=60)

    def test_synthetic_demo_metadata_analysis_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            iq = directory / 'demo.cf32'
            metadata = directory / 'demo.metadata.json'
            output = directory / 'analysis'
            generated = self.run_tool('tools.generate_demo', '--output', str(iq))
            self.assertEqual(generated.returncode, 0, generated.stderr)
            result = self.run_tool('tools.analyze_iq', str(iq), '--metadata', str(metadata),
                                   '--output-dir', str(output), '--verify-hash')
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(summary['source'], 'synthetic')
            self.assertTrue(summary['input_hash_verified'])
            self.assertAlmostEqual(summary['peak_rf_frequency_hz'], 10_125_000, delta=1000)
            self.assertTrue((output / 'analysis.png').is_file())
            repeated = self.run_tool('tools.analyze_iq', str(iq), '--metadata', str(metadata), '--output-dir', str(output))
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn('already exist', repeated.stderr)
