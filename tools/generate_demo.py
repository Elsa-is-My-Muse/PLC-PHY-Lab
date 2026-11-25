"""Generate repeatable synthetic IQ, explicitly unrelated to a HomePlug frame."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from tools.common import build_metadata, write_json_exclusive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw/synthetic_demo.cf32"))
    args = parser.parse_args()
    metadata_path = args.output.with_suffix(".metadata.json")
    try:
        if args.output.exists() or metadata_path.exists():
            raise FileExistsError("Demo already exists; choose another --output or reuse its metadata")
        rate = 1_000_000.0
        count = 65_536
        times = np.arange(count) / rate
        rng = np.random.default_rng(20261125)
        samples = 0.005 * (rng.standard_normal(count) + 1j * rng.standard_normal(count))
        for frequency, amplitude, start, end in [(125_000, 0.3, 0.012, 0.035), (-210_000, 0.15, 0.040, 0.055)]:
            mask = (times >= start) & (times < end)
            samples[mask] += amplitude * np.exp(2j * np.pi * frequency * times[mask])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(samples.astype("<c8").tobytes())
        metadata = build_metadata(
            args.output, iq_format="cf32_le", sample_rate=rate, center_frequency=10_000_000,
            source="synthetic", notes="Seed=20261125. Noise plus bursts at +125 kHz and -210 kHz; not HomePlug.",
        )
        metadata["generator"] = {"seed": 20261125, "tones_baseband_hz": [125000, -210000]}
        write_json_exclusive(metadata_path, metadata)
    except (OSError, ValueError) as error:
        print(f"Demo error: {error}", file=sys.stderr)
        return 2
    print(f"Synthetic IQ written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
