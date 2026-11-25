"""Record actual capture settings and file integrity without opening an SDR."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.common import FORMAT_BYTES, build_metadata, finite_number, positive_finite, write_json_exclusive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iq", type=Path)
    parser.add_argument("--source", choices=["hardware", "synthetic"], required=True)
    parser.add_argument("--format", choices=sorted(FORMAT_BYTES), required=True)
    parser.add_argument("--sample-rate", type=float, required=True)
    parser.add_argument("--center-frequency", type=float, required=True)
    parser.add_argument("--if-gain", type=float)
    parser.add_argument("--vga-gain", type=float)
    parser.add_argument("--analog-bandwidth", type=float)
    parser.add_argument("--external-attenuation-db", type=float)
    parser.add_argument("--rf-amplifier", choices=["on", "off"], default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.iq.with_suffix(".metadata.json")
    try:
        receiver = {
            "if_gain_db": args.if_gain,
            "vga_gain_db": args.vga_gain,
            "analog_bandwidth_hz": args.analog_bandwidth,
            "external_attenuation_db_nominal": args.external_attenuation_db,
            "rf_amplifier": args.rf_amplifier,
            "protection_validation": "not_recorded",
        }
        for name, value in receiver.items():
            if isinstance(value, float):
                finite_number(value, name)
        if args.analog_bandwidth is not None:
            positive_finite(args.analog_bandwidth, "analog_bandwidth")
        if args.external_attenuation_db is not None and args.external_attenuation_db < 0:
            raise ValueError("external_attenuation_db must not be negative")
        metadata = build_metadata(args.iq, iq_format=args.format, sample_rate=args.sample_rate,
                                  center_frequency=args.center_frequency, source=args.source,
                                  receiver=receiver, notes=args.notes)
        write_json_exclusive(output, metadata)
    except (OSError, ValueError) as error:
        print(f"Metadata error: {error}", file=sys.stderr)
        return 2
    print(f"Metadata written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
