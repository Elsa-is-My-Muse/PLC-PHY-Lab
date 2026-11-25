"""IQ layout and capture metadata; no hardware access or assumed RF calibration."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

FORMAT_BYTES = {"cf32_le": 8, "cs8": 2}
SCHEMA = "plc-phy-lab.capture.v1"


def positive_finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def finite_number(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def sample_count(path: Path, iq_format: str) -> int:
    if iq_format not in FORMAT_BYTES:
        raise ValueError(f"Unsupported IQ format: {iq_format}")
    size = path.stat().st_size
    if size == 0 or size % FORMAT_BYTES[iq_format]:
        raise ValueError("IQ file must contain a nonzero integral number of complex samples")
    return size // FORMAT_BYTES[iq_format]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_exclusive(path: Path, content: dict) -> None:
    encoded = json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)


def build_metadata(
    iq_path: Path,
    *,
    iq_format: str,
    sample_rate: float,
    center_frequency: float,
    source: str,
    receiver: dict | None = None,
    notes: str = "",
) -> dict:
    if source not in {"hardware", "synthetic"}:
        raise ValueError("source must be hardware or synthetic")
    count = sample_count(iq_path, iq_format)
    rate = positive_finite(sample_rate, "sample_rate_hz")
    center = finite_number(center_frequency, "center_frequency_hz")
    if center < 0:
        raise ValueError("center_frequency_hz must not be negative")
    return {
        "schema": SCHEMA,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "iq_file": iq_path.name,
        "format": iq_format,
        "sample_rate_hz": rate,
        "center_frequency_hz": center,
        "sample_count": count,
        "byte_count": iq_path.stat().st_size,
        "duration_seconds_from_sample_count": count / rate,
        "sha256": sha256_file(iq_path),
        "receiver": receiver or {},
        "rf_power_calibration": "not_applied",
        "notes": notes,
    }


def load_metadata(path: Path, iq_path: Path, verify_hash: bool = False) -> dict:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("schema") != SCHEMA:
        raise ValueError("Unsupported metadata schema")
    if metadata.get("source") not in {"hardware", "synthetic"}:
        raise ValueError("Metadata source must be hardware or synthetic")
    positive_finite(metadata["sample_rate_hz"], "sample_rate_hz")
    center = finite_number(metadata["center_frequency_hz"], "center_frequency_hz")
    if center < 0:
        raise ValueError("center_frequency_hz must not be negative")
    if metadata.get("iq_file") != iq_path.name:
        raise ValueError("Metadata IQ filename does not match the input file")
    count = sample_count(iq_path, metadata["format"])
    if metadata.get("sample_count") != count or metadata.get("byte_count") != iq_path.stat().st_size:
        raise ValueError("IQ size or sample count does not match metadata")
    if verify_hash and sha256_file(iq_path) != metadata.get("sha256"):
        raise ValueError("IQ SHA-256 does not match metadata")
    return metadata


def read_iq(path: Path, iq_format: str, max_samples: int) -> np.ndarray:
    if max_samples < 2:
        raise ValueError("max_samples must be at least 2")
    count = min(sample_count(path, iq_format), max_samples)
    if count < 2:
        raise ValueError("Analysis requires at least two complex samples")
    if iq_format == "cf32_le":
        mapped = np.memmap(path, dtype="<c8", mode="r", shape=(count,))
        samples = np.array(mapped, dtype=np.complex128)
        del mapped
    else:
        mapped = np.memmap(path, dtype=np.int8, mode="r", shape=(count, 2))
        samples = (mapped[:, 0].astype(np.float64) + 1j * mapped[:, 1].astype(np.float64)) / 128.0
        del mapped
    if not np.isfinite(samples).all():
        raise ValueError("Analyzed IQ contains NaN or infinite samples")
    return samples
