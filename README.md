# SDR FM Frequency Scan

RTL-SDR passive scan of the 85–110 MHz FM broadcast band, with automated
heatmap and spectrum-peak analysis.

## Hardware

| Component | Value |
|-----------|-------|
| Dongle | Realtek RTL2838UHIDIR (×2) |
| Tuner | Rafael Micro R820T |
| Gain | 49.6 dB |

## Scan parameters

| Parameter | Value |
|-----------|-------|
| Date/Time | 2026-05-31 10:33–10:34 UTC |
| Frequency range | 85.0 – 110.0 MHz |
| Step size | 125 kHz (297 bins) |
| Integration | 1 s per sweep |
| Duration | ~48 s (49 time samples) |
| Noise floor | −1.7 dBm |

## Results summary

29 signals detected across four tiers:

| Tier | Threshold | Count |
|------|-----------|-------|
| Strong | SNR > 20 dB | 1 |
| Medium | SNR 14–20 dB | 7 |
| Weak | SNR 6–14 dB | 7 |
| Marginal | SNR 3–6 dB | 14 |

**Dominant signal: 88.906 MHz** — SNR 25.4 dB, stable across entire scan.

See [`charts/final_report_chart.png`](charts/final_report_chart.png) for the
full annotated 3-panel report.

## Project layout

```
sdr-fm-scan/
├── data/
│   └── output.csv              # Raw rtl_power scan (reference)
├── charts/
│   ├── heatmap.png             # Time/frequency waterfall
│   ├── spectrum_peaks.png      # Annotated spectrum (6 dB threshold, 15 signals)
│   └── final_report_chart.png  # Full 3-panel report (3 dB threshold, 29 signals)
├── scripts/
│   ├── rtl_heatmap.py          # Heatmap generator
│   └── scan.sh                 # End-to-end scan + heatmap runner
└── README.md
```

## Quick start

### Dependencies

```bash
brew install librtlsdr
pip3 install matplotlib numpy pandas
```

### Run a new scan

```bash
chmod +x scripts/scan.sh
./scripts/scan.sh 85M 110M 125k 60
```

Arguments: `freq_low freq_high step duration_seconds`

### Generate heatmap from existing CSV

```bash
python3 scripts/rtl_heatmap.py data/output.csv charts/heatmap.png
```

## Detected signals

| # | Freq (MHz) | SNR (dB) | Tier | Stability |
|---|-----------|---------|------|-----------|
| 1 | 88.906 | 25.4 | Strong | stable |
| 2 | 107.917 | 17.7 | Medium | stable |
| 3 | 105.139 | 17.3 | Medium | stable |
| 4 | 99.031 | 18.6 | Medium | stable |
| 5 | 97.934 | 16.4 | Medium | stable |
| 6 | 106.267 | 16.4 | Medium | stable |
| 7 | 95.330 | 15.4 | Medium | stable |
| 8 | 93.681 | 14.9 | Medium | stable |
| 9 | 99.149 | 13.6 | Weak | stable |
| 10 | 95.937 | 14.0 | Weak | stable |
| 11 | 102.708 | 8.9 | Weak | intermittent |
| 12 | 101.146 | 8.2 | Weak | variable |
| 13 | 97.066 | 8.0 | Weak | variable |
| 14 | 91.070 | 7.2 | Weak | variable |
| 15 | 86.823 | 10.3 | Weak | stable |
| 16–29 | 85.5–108.9 | 3–6 | Marginal | intermittent |
