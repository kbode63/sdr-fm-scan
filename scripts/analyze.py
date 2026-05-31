#!/usr/bin/env python3
"""
analyze.py — RTL-SDR scan analysis: peak detection, all charts, JSON summary.

Usage:
    python3 scripts/analyze.py data/output.csv
    python3 scripts/analyze.py data/output.csv --outdir charts/ --threshold 3
    python3 scripts/analyze.py data/output.csv --json-out summary.json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# ── Parsing ───────────────────────────────────────────────────────────────────


def parse_csv(path):
    freq_powers = defaultdict(list)
    rows_by_time = defaultdict(dict)
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if len(row) < 7:
                continue
            try:
                ts = datetime.strptime(row[0].strip() + " " + row[1].strip(), "%Y-%m-%d %H:%M:%S")
                hz_low = float(row[2])
                hz_step = float(row[4])
                powers = [float(x) for x in row[6:] if x.strip()]
                for i, p in enumerate(powers):
                    freq = hz_low + i * hz_step
                    freq_powers[freq].append(p)
                    rows_by_time[ts][freq] = p
            except (ValueError, IndexError):
                continue
    if not freq_powers:
        print(f"ERROR: no data parsed from {path}", file=sys.stderr)
        sys.exit(1)
    return freq_powers, rows_by_time


def build_grid(times, freqs, rows_by_time):
    grid = np.full((len(times), len(freqs)), np.nan)
    fi = {f: i for i, f in enumerate(freqs)}
    for ti, ts in enumerate(times):
        for freq, pwr in rows_by_time[ts].items():
            grid[ti, fi[freq]] = pwr
    return grid


# ── Peak detection ────────────────────────────────────────────────────────────


def detect_peaks(freqs_hz, means, noise, threshold_db=3.0, merge_hz=300_000):
    threshold = noise + threshold_db
    raw = []
    window = 2
    for i in range(window, len(means) - window):
        if means[i] < threshold:
            continue
        if means[i] == means[i - window : i + window + 1].max():
            if not raw or i - raw[-1] > 2:
                raw.append(i)
    merged = []
    for p in sorted(raw, key=lambda i: means[i], reverse=True):
        if not any(abs(freqs_hz[p] - freqs_hz[m]) < merge_hz for m in merged):
            merged.append(p)
    return sorted(merged, key=lambda i: freqs_hz[i])


def tier(snr):
    if snr > 20:
        return "STRONG", "#ff2244"
    if snr > 14:
        return "MEDIUM", "#ffaa00"
    if snr > 6:
        return "WEAK", "#44dd88"
    return "MARGINAL", "#66aaff"


# ── Chart 1: waterfall heatmap ────────────────────────────────────────────────


def plot_heatmap(grid, times, freqs_mhz, outpath):
    fig, ax = plt.subplots(figsize=(16, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    vmin = np.nanpercentile(grid, 5)
    vmax = np.nanpercentile(grid, 99)
    ax.imshow(
        grid.T,
        aspect="auto",
        origin="lower",
        interpolation="nearest",
        cmap="inferno",
        vmin=vmin,
        vmax=vmax,
        extent=[
            mdates.date2num(times[0]),
            mdates.date2num(times[-1]),
            freqs_mhz[0],
            freqs_mhz[-1],
        ],
    )
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()

    cbar = fig.colorbar(
        plt.cm.ScalarMappable(norm=plt.Normalize(vmin=vmin, vmax=vmax), cmap="inferno"),
        ax=ax,
        pad=0.02,
    )
    cbar.set_label("Power (dBm)", fontsize=11, color="white")
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    ax.set_xlabel("Time (UTC)", color="white", fontsize=12)
    ax.set_ylabel("Frequency (MHz)", color="white", fontsize=12)
    ax.set_title(
        f"RTL-SDR Frequency Scan Heatmap — {freqs_mhz[0]:.1f}–{freqs_mhz[-1]:.1f} MHz",
        color="white",
        fontsize=14,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444")

    plt.tight_layout()
    plt.savefig(outpath, dpi=150, facecolor="#0d1117")
    plt.close()
    print(f"  heatmap        → {outpath}")


# ── Chart 2: annotated spectrum + SNR bars ────────────────────────────────────


def plot_spectrum(freqs_mhz, means, maxs, noise, peaks, outpath):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [2, 1]})
    fig.patch.set_facecolor("#0d1117")

    for ax in (ax1, ax2):
        ax.set_facecolor("#0d1117")
        ax.tick_params(colors="#cccccc")
        ax.spines[:].set_color("#333")
        ax.grid(axis="y", color="#222", linewidth=0.5)

    ax1.fill_between(freqs_mhz, means, noise, where=(means > noise), color="#ff6b35", alpha=0.3)
    ax1.plot(freqs_mhz, means, color="#ff8c55", linewidth=0.85, label="Mean power")
    ax1.plot(freqs_mhz, maxs, color="#ffd700", linewidth=0.5, alpha=0.5, label="Peak power")
    ax1.axhline(
        noise,
        color="#888",
        linewidth=0.8,
        linestyle="--",
        label=f"Noise floor ({noise:.1f} dBm)",
    )
    ax1.axhline(
        noise + 6,
        color="#44aaff",
        linewidth=0.7,
        linestyle=":",
        label="+6 dB threshold",
    )

    for idx in peaks:
        f = freqs_mhz[idx]
        m = means[idx]
        snr = m - noise
        _, col = tier(snr)
        ax1.plot(f, m, "o", color=col, markersize=4.5, zorder=6)
        ax1.axvline(f, color=col, linewidth=0.5, alpha=0.4)
        ax1.annotate(
            f"{f:.2f}",
            xy=(f, m),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.5,
            color=col,
            rotation=70,
        )

    ax1.set_xlim(freqs_mhz[0], freqs_mhz[-1])
    ax1.set_ylabel("Power (dBm)", color="#cccccc", fontsize=11)
    ax1.set_title(
        f"RTL-SDR Active Frequency Analysis — {freqs_mhz[0]:.1f}–{freqs_mhz[-1]:.1f} MHz",
        color="white",
        fontsize=13,
    )
    ax1.legend(loc="upper left", fontsize=8, facecolor="#1a1a2e", labelcolor="white")

    fmhz = [freqs_mhz[i] for i in peaks]
    snrs = [means[i] - noise for i in peaks]
    cols = [tier(s)[1] for s in snrs]
    ax2.bar(fmhz, snrs, width=0.08, color=cols, zorder=3)
    for f, snr, _col in zip(fmhz, snrs, cols):
        ax2.text(
            f,
            snr + 0.2,
            f"{f:.2f}",
            ha="center",
            va="bottom",
            fontsize=6.5,
            color="white",
            rotation=70,
        )
    for level, col in [(6, "#44aaff"), (14, "#ffaa00"), (20, "#ff2244")]:
        ax2.axhline(level, color=col, linewidth=0.7, linestyle=":", alpha=0.6)

    ax2.set_xlim(freqs_mhz[0], freqs_mhz[-1])
    ax2.set_ylabel("SNR (dB)", color="#cccccc", fontsize=11)
    ax2.set_xlabel("Frequency (MHz)", color="#cccccc", fontsize=11)
    patches = [
        mpatches.Patch(color="#ff2244", label="Strong  > 20 dB"),
        mpatches.Patch(color="#ffaa00", label="Medium  14–20 dB"),
        mpatches.Patch(color="#44dd88", label="Weak    6–14 dB"),
        mpatches.Patch(color="#66aaff", label="Marginal 3–6 dB"),
    ]
    ax2.legend(
        handles=patches,
        loc="upper right",
        fontsize=8,
        facecolor="#1a1a2e",
        labelcolor="white",
    )

    plt.tight_layout(h_pad=1.5)
    plt.savefig(outpath, dpi=150, facecolor="#0d1117")
    plt.close()
    print(f"  spectrum peaks → {outpath}")


# ── Chart 3: 3-panel full report ──────────────────────────────────────────────


def plot_full_report(grid, times, freqs_mhz, means, maxs, stds, noise, peaks, outpath):
    BG = "#0d1117"
    fig = plt.figure(figsize=(18, 14), facecolor=BG)
    gs = gridspec.GridSpec(3, 1, figure=fig, height_ratios=[1.6, 1.2, 1.0], hspace=0.38)
    ax_wf = fig.add_subplot(gs[0])
    ax_sp = fig.add_subplot(gs[1])
    ax_snr = fig.add_subplot(gs[2])

    for ax in (ax_wf, ax_sp, ax_snr):
        ax.set_facecolor(BG)
        ax.tick_params(colors="#cccccc")
        ax.spines[:].set_color("#333")

    # Waterfall
    vmin = np.nanpercentile(grid, 5)
    vmax = np.nanpercentile(grid, 99)
    ax_wf.imshow(
        grid.T,
        aspect="auto",
        origin="lower",
        interpolation="nearest",
        cmap="inferno",
        vmin=vmin,
        vmax=vmax,
        extent=[
            mdates.date2num(times[0]),
            mdates.date2num(times[-1]),
            freqs_mhz[0],
            freqs_mhz[-1],
        ],
    )
    ax_wf.xaxis_date()
    ax_wf.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate(rotation=0, ha="center")
    ax_wf.set_ylabel("Frequency (MHz)", color="#cccccc", fontsize=10)
    scan_ts = times[0].strftime("%Y-%m-%d %H:%M") + "–" + times[-1].strftime("%H:%M UTC")
    ax_wf.set_title(
        f"RTL-SDR Active Frequency Report — {freqs_mhz[0]:.1f}–{freqs_mhz[-1]:.1f} MHz"
        f"  |  {scan_ts}",
        color="white",
        fontsize=13,
        pad=10,
    )
    for idx in peaks:
        snr = means[idx] - noise
        _, col = tier(snr)
        ax_wf.axhline(freqs_mhz[idx], color=col, linewidth=0.6, alpha=0.5, linestyle="--")

    # Mean spectrum
    ax_sp.fill_between(freqs_mhz, means, noise, where=(means > noise), color="#ff6b35", alpha=0.3)
    ax_sp.plot(freqs_mhz, means, color="#ff8c55", linewidth=0.85, label="Mean power")
    ax_sp.plot(freqs_mhz, maxs, color="#ffd700", linewidth=0.5, alpha=0.5, label="Peak power")
    ax_sp.axhline(
        noise,
        color="#888",
        linewidth=0.8,
        linestyle="--",
        label=f"Noise  {noise:.1f} dBm",
    )
    ax_sp.axhline(
        noise + 6,
        color="#44aaff",
        linewidth=0.7,
        linestyle=":",
        label="+6 dB threshold",
    )
    for idx in peaks:
        f = freqs_mhz[idx]
        m = means[idx]
        snr = m - noise
        _, col = tier(snr)
        ax_sp.plot(f, m, "o", color=col, markersize=4.5, zorder=6)
        ax_sp.axvline(f, color=col, linewidth=0.5, alpha=0.4)
        yoff = 7 + (list(freqs_mhz).index(f) % 3) * 5
        ax_sp.annotate(
            f"{f:.2f}",
            xy=(f, m),
            xytext=(0, yoff),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6,
            color=col,
            rotation=70,
        )
    ax_sp.set_xlim(freqs_mhz[0], freqs_mhz[-1])
    ax_sp.set_ylabel("Power (dBm)", color="#cccccc", fontsize=10)
    ax_sp.legend(
        loc="upper left",
        fontsize=7.5,
        facecolor="#1a1a2e",
        labelcolor="white",
        framealpha=0.85,
    )
    ax_sp.grid(axis="y", color="#222", linewidth=0.5)

    # SNR bars
    fmhz = [freqs_mhz[i] for i in peaks]
    snrs = [means[i] - noise for i in peaks]
    cols = [tier(s)[1] for s in snrs]
    ax_snr.bar(fmhz, snrs, width=0.07, color=cols, zorder=3)
    for f, snr, _col in zip(fmhz, snrs, cols):
        ax_snr.text(
            f,
            snr + 0.15,
            f"{f:.2f}",
            ha="center",
            va="bottom",
            fontsize=5.8,
            color="white",
            rotation=70,
        )
    for level, col in [(6, "#44aaff"), (14, "#ffaa00"), (20, "#ff2244")]:
        ax_snr.axhline(level, color=col, linewidth=0.7, linestyle=":", alpha=0.8)
    ax_snr.set_xlim(freqs_mhz[0], freqs_mhz[-1])
    ax_snr.set_ylabel("SNR (dB)", color="#cccccc", fontsize=10)
    ax_snr.set_xlabel("Frequency (MHz)", color="#cccccc", fontsize=10)
    ax_snr.grid(axis="y", color="#222", linewidth=0.5)
    patches = [
        mpatches.Patch(color="#ff2244", label="Strong  > 20 dB"),
        mpatches.Patch(color="#ffaa00", label="Medium  14–20 dB"),
        mpatches.Patch(color="#44dd88", label="Weak    6–14 dB"),
        mpatches.Patch(color="#66aaff", label="Marginal 3–6 dB"),
    ]
    ax_snr.legend(
        handles=patches,
        loc="upper right",
        fontsize=7.5,
        facecolor="#1a1a2e",
        labelcolor="white",
        framealpha=0.85,
    )

    plt.savefig(outpath, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close()
    print(f"  full report    → {outpath}")


# ── JSON summary ──────────────────────────────────────────────────────────────


def build_summary(freqs_hz, means, maxs, stds, noise, peaks, times, csv_path, threshold_db):
    signals = []
    for idx in peaks:
        f = freqs_hz[idx] / 1e6
        m = float(means[idx])
        mx = float(maxs[idx])
        sd = float(stds[idx])
        snr = m - noise
        tname, _ = tier(snr)
        stability = "stable" if sd < 1.5 else "variable" if sd < 3.0 else "intermittent"
        signals.append(
            {
                "freq_mhz": round(f, 3),
                "mean_dbm": round(m, 1),
                "peak_dbm": round(mx, 1),
                "snr_db": round(snr, 1),
                "std_db": round(sd, 2),
                "tier": tname,
                "stability": stability,
            }
        )

    tier_counts = {}
    for s in signals:
        tier_counts[s["tier"]] = tier_counts.get(s["tier"], 0) + 1

    return {
        "scan": {
            "source_csv": str(csv_path),
            "start_utc": times[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_utc": times[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_s": int((times[-1] - times[0]).total_seconds()),
            "time_steps": len(times),
            "freq_bins": len(freqs_hz),
            "freq_low_mhz": round(freqs_hz[0] / 1e6, 3),
            "freq_high_mhz": round(freqs_hz[-1] / 1e6, 3),
        },
        "analysis": {
            "noise_floor_dbm": round(float(noise), 1),
            "threshold_db": threshold_db,
            "total_signals": len(signals),
            "by_tier": tier_counts,
        },
        "signals": signals,
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Analyse an rtl_power CSV scan.")
    parser.add_argument("csv", help="Path to rtl_power output CSV")
    parser.add_argument(
        "--outdir",
        default="charts",
        help="Directory for chart output (default: charts/)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="SNR detection threshold in dB (default: 3.0)",
    )
    parser.add_argument("--json-out", default=None, help="Write JSON summary to this path")
    parser.add_argument("--prefix", default="", help="Filename prefix for output charts")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix + "_" if args.prefix else ""

    print(f"Parsing {csv_path} ...")
    freq_powers, rows_by_time = parse_csv(csv_path)

    freqs = sorted(freq_powers)
    means = np.array([np.mean(freq_powers[f]) for f in freqs])
    maxs = np.array([np.max(freq_powers[f]) for f in freqs])
    stds = np.array([np.std(freq_powers[f]) for f in freqs])
    freqs_a = np.array(freqs)
    freqs_mhz = freqs_a / 1e6
    noise = float(np.median(means))
    times = sorted(rows_by_time)

    grid = build_grid(times, freqs, rows_by_time)
    peaks = detect_peaks(freqs_a, means, noise, threshold_db=args.threshold)

    print(f"  noise floor  : {noise:.1f} dBm")
    print(f"  peaks found  : {len(peaks)}  (threshold +{args.threshold} dB)")
    print("Generating charts ...")

    stem = prefix + csv_path.stem
    plot_heatmap(grid, times, freqs_mhz, outdir / f"{stem}_heatmap.png")
    plot_spectrum(freqs_mhz, means, maxs, noise, peaks, outdir / f"{stem}_spectrum.png")
    plot_full_report(
        grid,
        times,
        freqs_mhz,
        means,
        maxs,
        stds,
        noise,
        peaks,
        outdir / f"{stem}_report.png",
    )

    summary = build_summary(
        freqs_a, means, maxs, stds, noise, peaks, times, csv_path, args.threshold
    )

    json_path = Path(args.json_out) if args.json_out else outdir / f"{stem}_summary.json"
    json_path.write_text(json.dumps(summary, indent=2))
    print(f"  summary JSON   → {json_path}")

    print("\nSignals detected:")
    print(f"  {'Freq (MHz)':>11}  {'SNR (dB)':>9}  {'Tier':<9}  Stability")
    print("  " + "─" * 46)
    for s in summary["signals"]:
        print(f"  {s['freq_mhz']:>11.3f}  {s['snr_db']:>9.1f}  {s['tier']:<9}  {s['stability']}")


if __name__ == "__main__":
    main()
