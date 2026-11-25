"""Plot bounded IQ data and uncalibrated digital PSD; never infer dBm."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import signal

from tools.common import load_metadata, positive_finite, read_iq, write_json_exclusive


def welch_psd(samples: np.ndarray, sample_rate: float, nfft: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    rate = positive_finite(sample_rate, "sample_rate")
    if len(samples) < 2 or nfft < 2:
        raise ValueError("At least two samples and an FFT length of at least two are required")
    if not np.isfinite(samples).all():
        raise ValueError("Samples must be finite")
    length = min(nfft, len(samples))
    frequencies, density = signal.welch(
        samples, fs=rate, window="hann", nperseg=length, noverlap=length // 2,
        detrend=False, return_onesided=False, scaling="density",
    )
    return np.fft.fftshift(frequencies), np.fft.fftshift(density)


def sample_statistics(samples: np.ndarray) -> dict:
    power = np.abs(samples) ** 2
    mean_power = float(np.mean(power))
    peak_power = float(np.max(power))
    return {
        "mean_power_unit_squared": mean_power,
        "rms_sample_units": float(np.sqrt(mean_power)),
        "peak_magnitude_sample_units": float(np.sqrt(peak_power)),
        "papr_db": float(10 * np.log10(peak_power / mean_power)) if mean_power > 0 else None,
        "dc_i_sample_units": float(np.mean(samples.real)),
        "dc_q_sample_units": float(np.mean(samples.imag)),
        "near_unit_component_fraction": float(np.mean((np.abs(samples.real) >= 0.99) | (np.abs(samples.imag) >= 0.99))),
    }


def plot_analysis(samples: np.ndarray, metadata: dict, frequencies: np.ndarray,
                  density: np.ndarray, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rate = metadata["sample_rate_hz"]
    center = metadata["center_frequency_hz"]
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), constrained_layout=True)
    source = metadata["source"].upper()
    suffix = " / teaching signal, not a HomePlug waveform" if source == "SYNTHETIC" else " / uncalibrated"
    fig.suptitle(f"PLC-PHY-Lab | SOURCE: {source}{suffix}", fontsize=11)

    indices = np.unique(np.linspace(0, len(samples) - 1, min(len(samples), 25000), dtype=int))
    axes[0].plot(indices / rate * 1000, np.abs(samples[indices]), linewidth=0.6)
    axes[0].set(xlabel="Time (ms)", ylabel="Magnitude (sample units)")
    axes[0].grid(alpha=0.25)

    axes[1].plot((frequencies + center) / 1e6, 10 * np.log10(np.maximum(density, 1e-30)), linewidth=0.8)
    axes[1].set(xlabel="RF frequency (MHz)", ylabel="PSD (dB re 1 unit^2/Hz)")
    axes[1].grid(alpha=0.25)

    length = min(1024, len(samples))
    possible_starts = np.arange(0, len(samples) - length + 1, max(1, length // 2))
    starts = possible_starts[np.unique(np.linspace(0, len(possible_starts) - 1, min(256, len(possible_starts)), dtype=int))]
    frames = samples[starts[:, None] + np.arange(length)]
    window = signal.get_window("hann", length)
    transforms = np.fft.fftshift(np.fft.fft(frames * window, axis=1), axes=1)
    spectrogram = np.abs(transforms) ** 2 / (rate * np.sum(window ** 2))
    freq_edges = np.linspace(center - rate / 2, center + rate / 2, length + 1) / 1e6
    time_centers = (starts + length / 2) / rate * 1000
    if len(time_centers) == 1:
        time_edges = np.array([starts[0] / rate, (starts[0] + length) / rate]) * 1000
    else:
        mids = (time_centers[1:] + time_centers[:-1]) / 2
        time_edges = np.r_[max(0, time_centers[0] - (mids[0] - time_centers[0])), mids,
                           time_centers[-1] + (time_centers[-1] - mids[-1])]
    image = axes[2].pcolormesh(freq_edges, time_edges, 10 * np.log10(np.maximum(spectrogram, 1e-30)),
                             shading="flat", cmap="viridis")
    axes[2].set(xlabel="RF frequency (MHz)", ylabel="Time (ms)")
    fig.colorbar(image, ax=axes[2], label="dB re 1 unit^2/Hz")
    fig.savefig(output, dpi=130)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iq", type=Path)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-samples", type=int, default=2_000_000)
    parser.add_argument("--nfft", type=int, default=4096)
    parser.add_argument("--verify-hash", action="store_true")
    args = parser.parse_args()
    try:
        metadata = load_metadata(args.metadata, args.iq, verify_hash=args.verify_hash)
        samples = read_iq(args.iq, metadata["format"], args.max_samples)
        frequencies, density = welch_psd(samples, metadata["sample_rate_hz"], args.nfft)
        stats = sample_statistics(samples)
        peak_index = int(np.argmax(density))
        summary = {
            "schema": "plc-phy-lab.analysis.v1",
            "source": metadata["source"],
            "iq_file": args.iq.name,
            "format": metadata["format"],
            "sample_rate_hz": metadata["sample_rate_hz"],
            "center_frequency_hz": metadata["center_frequency_hz"],
            "total_samples": metadata["sample_count"],
            "analyzed_samples": len(samples),
            "analyzed_duration_seconds": len(samples) / metadata["sample_rate_hz"],
            "analyzed_region": "start_of_file",
            "psd_unit": "dB re 1 sample-unit squared per Hz; uncalibrated",
            "psd_method": "two-sided Welch; periodic Hann window; 50 percent overlap; detrend disabled",
            "fft_length": min(args.nfft, len(samples)),
            "fft_bin_spacing_hz": metadata["sample_rate_hz"] / min(args.nfft, len(samples)),
            "psd_integral_unit_squared": float(np.sum(density) * metadata["sample_rate_hz"] / len(density)),
            "peak_rf_frequency_hz": float(frequencies[peak_index] + metadata["center_frequency_hz"]) if stats["mean_power_unit_squared"] else None,
            "input_sha256_from_metadata": metadata["sha256"],
            "input_hash_verified": args.verify_hash,
            "rf_power_calibration": "not_applied",
            "statistics": stats,
            "limitations": [
                "This is not a HomePlug decoder or calibrated RF power meter.",
                "Sample-domain PAPR depends on the selected interval, noise and idle time.",
                "Near-unit components alone do not establish ADC clipping.",
                "File integrity does not establish absence of capture sample drops.",
            ],
        }
        image_path = args.output_dir / "analysis.png"
        summary_path = args.output_dir / "summary.json"
        if image_path.exists() or summary_path.exists():
            raise FileExistsError("Analysis outputs already exist; choose a new output directory")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        plot_analysis(samples, metadata, frequencies, density, image_path)
        write_json_exclusive(summary_path, summary)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Analysis error: {error}", file=sys.stderr)
        return 2
    print(f"Analysis written: {args.output_dir} (source={metadata['source']}, samples={len(samples)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
