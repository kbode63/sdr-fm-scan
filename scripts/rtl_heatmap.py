#!/usr/bin/env python3
"""
Generate a frequency/time heatmap from rtl_power CSV output.
Usage: python3 rtl_heatmap.py [input.csv] [output.png]
"""

import csv
import sys
from collections import defaultdict
from datetime import datetime

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/karlbode/output.csv"
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else "/Users/karlbode/heatmap.png"

# ── Parse rtl_power CSV ──────────────────────────────────────────────────────
# Format: date, time, Hz_low, Hz_high, Hz_step, samples, dB, dB, ...
rows_by_time = defaultdict(dict)  # {timestamp: {freq_hz: power_db}}

with open(INPUT, newline="") as f:
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
                rows_by_time[ts][freq] = p
        except (ValueError, IndexError):
            continue

if not rows_by_time:
    print("No data parsed from", INPUT)
    sys.exit(1)

# ── Build 2-D grid ────────────────────────────────────────────────────────────
times = sorted(rows_by_time)
freqs = sorted({f for t in rows_by_time.values() for f in t})

grid = np.full((len(times), len(freqs)), np.nan)
freq_idx = {f: i for i, f in enumerate(freqs)}

for ti, ts in enumerate(times):
    for freq, pwr in rows_by_time[ts].items():
        grid[ti, freq_idx[freq]] = pwr

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 6))

freqs_mhz = np.array(freqs) / 1e6
vmin = np.nanpercentile(grid, 5)
vmax = np.nanpercentile(grid, 99)

img = ax.imshow(
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

cbar = fig.colorbar(img, ax=ax, pad=0.02)
cbar.set_label("Power (dBm)", fontsize=11)

ax.set_xlabel("Time (UTC)", fontsize=12)
ax.set_ylabel("Frequency (MHz)", fontsize=12)
ax.set_title(
    f"RTL-SDR Frequency Scan Heatmap — {freqs_mhz[0]:.1f}–{freqs_mhz[-1]:.1f} MHz",
    fontsize=14,
)

plt.tight_layout()
plt.savefig(OUTPUT, dpi=150)
print(f"Heatmap saved → {OUTPUT}")
print(f"  Frequencies : {freqs_mhz[0]:.3f} – {freqs_mhz[-1]:.3f} MHz ({len(freqs)} bins)")
print(f"  Time steps  : {len(times)}")
print(f"  Power range : {vmin:.1f} – {vmax:.1f} dBm")
