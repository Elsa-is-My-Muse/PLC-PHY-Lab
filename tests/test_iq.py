from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import numpy as np
from tools.analyze_iq import sample_statistics, welch_psd
from tools.common import build_metadata, load_metadata, read_iq, sample_count, write_json_exclusive


class IQFormatTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_cf32_little_endian_iq_order(self):
        path = self.root / 'samples.cf32'
        expected = np.array([1 + 2j, -0.5 - 0.25j, 0j], dtype='<c8')
        path.write_bytes(expected.tobytes())
        np.testing.assert_array_equal(read_iq(path, 'cf32_le', 3), expected)
        self.assertEqual(sample_count(path, 'cf32_le'), 3)

    def test_cs8_signed_scaling(self):
        path = self.root / 'samples.cs8'
        path.write_bytes(np.array([-128, 127, 0, -64], dtype=np.int8).tobytes())
        np.testing.assert_array_equal(read_iq(path, 'cs8', 2), [-1 + 127j / 128, -0.5j])

    def test_truncated_complex_sample_is_rejected(self):
        path = self.root / 'broken.cf32'
        path.write_bytes(b'1234567')
        with self.assertRaises(ValueError):
            sample_count(path, 'cf32_le')

    def test_empty_file_is_rejected(self):
        path = self.root / 'empty.cf32'
        path.touch()
        with self.assertRaises(ValueError):
            sample_count(path, 'cf32_le')

    def test_nonfinite_samples_are_rejected(self):
        path = self.root / 'nan.cf32'
        path.write_bytes(np.array([np.nan + 0j, 0j], dtype='<c8').tobytes())
        with self.assertRaises(ValueError):
            read_iq(path, 'cf32_le', 2)

    def test_max_samples_limits_analysis_region(self):
        path = self.root / 'bounded.cf32'
        path.write_bytes(np.arange(20, dtype=np.float32).astype('<c8').tobytes())
        self.assertEqual(len(read_iq(path, 'cf32_le', 5)), 5)


class PSDTests(unittest.TestCase):
    def test_positive_and_negative_tones_keep_their_sign(self):
        rate = 1_024_000
        time = np.arange(32_768) / rate
        for frequency in [125_000, -125_000]:
            with self.subTest(frequency=frequency):
                tones = 0.5 * np.exp(2j * np.pi * frequency * time)
                axis, density = welch_psd(tones, rate)
                self.assertAlmostEqual(float(axis[np.argmax(density)]), frequency, delta=rate / 4096)
                self.assertAlmostEqual(float(axis[np.argmax(density)] + 10_000_000), 10_000_000 + frequency, delta=rate / 4096)

    def test_two_sided_psd_integrates_to_tone_power(self):
        rate = 1_024_000
        tone = 0.5 * np.exp(2j * np.pi * 125_000 * np.arange(32_768) / rate)
        axis, density = welch_psd(tone, rate)
        integrated = float(np.sum(density) * (axis[1] - axis[0]))
        self.assertAlmostEqual(integrated, 0.25, places=7)

    def test_dc_is_preserved_without_detrending(self):
        axis, density = welch_psd(np.ones(8192, dtype=complex) * 0.2, 1_000_000)
        self.assertEqual(float(axis[np.argmax(density)]), 0)
        self.assertAlmostEqual(float(np.sum(density) * 1_000_000 / len(density)), 0.04, places=7)

    def test_invalid_rate_is_rejected(self):
        for rate in [0, -1, float('nan')]:
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                welch_psd(np.ones(16, dtype=complex), rate)

    def test_zero_signal_statistics_are_defined(self):
        stats = sample_statistics(np.zeros(16, dtype=complex))
        self.assertEqual(stats['mean_power_unit_squared'], 0)
        self.assertIsNone(stats['papr_db'])


class MetadataTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.iq = self.root / 'capture.cf32'
        self.iq.write_bytes(np.array([0.1 + 0.2j, 0j, -0.3j], dtype='<c8').tobytes())
        self.metadata = build_metadata(self.iq, iq_format='cf32_le', sample_rate=1_000_000,
                                       center_frequency=10_000_000, source='synthetic')
        self.sidecar = self.root / 'capture.metadata.json'

    def test_round_trip_preserves_source_and_unknown_calibration(self):
        write_json_exclusive(self.sidecar, self.metadata)
        loaded = load_metadata(self.sidecar, self.iq, verify_hash=True)
        self.assertEqual(loaded['source'], 'synthetic')
        self.assertEqual(loaded['rf_power_calibration'], 'not_applied')
        self.assertEqual(loaded['receiver'], {})

    def test_integrity_check_catches_same_size_changes(self):
        write_json_exclusive(self.sidecar, self.metadata)
        data = bytearray(self.iq.read_bytes())
        data[0] ^= 1
        self.iq.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            load_metadata(self.sidecar, self.iq, verify_hash=True)

    def test_size_change_is_rejected_without_hashing(self):
        write_json_exclusive(self.sidecar, self.metadata)
        with self.iq.open('ab') as stream:
            stream.write(np.array([0j], dtype='<c8').tobytes())
        with self.assertRaisesRegex(ValueError, 'size or sample count'):
            load_metadata(self.sidecar, self.iq)

    def test_existing_metadata_is_not_overwritten(self):
        write_json_exclusive(self.sidecar, self.metadata)
        with self.assertRaises(FileExistsError):
            write_json_exclusive(self.sidecar, {'changed': True})
        self.assertEqual(load_metadata(self.sidecar, self.iq)['source'], 'synthetic')

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(ValueError):
            build_metadata(self.iq, iq_format='cf32_le', sample_rate=1, center_frequency=1, source='unknown')
