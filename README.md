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

## CI / GitHub Actions

Three workflows live in `.github/workflows/`:

| Workflow | Trigger | Runner | Purpose |
|----------|---------|--------|---------|
| `generate-report.yml` | Push to `data/*.csv` or manual dispatch | `ubuntu-latest` | Run `analyze.py`, commit charts, upload artifacts |
| `scan.yml` | Manual dispatch or cron schedule | `self-hosted` + label `rtl-sdr` | Capture RTL-SDR scan, analyse, commit results |
| `lint.yml` | Push / PR touching `scripts/*.py` | `ubuntu-latest` | `ruff check` + `ruff format --check` |

### Self-hosted runner setup (required for `scan.yml`)

Because scanning requires a physical RTL-SDR dongle, `scan.yml` targets a
self-hosted runner labelled `rtl-sdr`. Follow these steps once per host machine:

**1. Register the runner**

Go to **Settings → Actions → Runners → New self-hosted runner** in the GitHub
repository, choose your OS, and follow the on-screen download and configuration
instructions. When prompted for labels, add `rtl-sdr`:

```bash
# Example configuration step (token shown by GitHub)
./config.sh --url https://github.com/kbode63/sdr-fm-scan \
            --token <RUNNER_TOKEN> \
            --labels rtl-sdr
```

**2. Install RTL-SDR tooling**

```bash
# macOS
brew install librtlsdr

# Debian / Ubuntu
sudo apt install rtl-sdr
```

Verify the dongle is detected:

```bash
rtl_test -t
# Expected: "Found 1 device(s)"
```

**3. Install Python dependencies**

```bash
pip3 install matplotlib numpy pandas
```

**4. Install and start the runner service**

```bash
# macOS (launchd)
./svc.sh install && ./svc.sh start

# Linux (systemd)
sudo ./svc.sh install && sudo ./svc.sh start
```

The runner is now online. Trigger a scan from **Actions → Run Scan → Run
workflow** and set the frequency range and duration inputs.

**5. Enable periodic scans (optional)**

Uncomment the `schedule:` block in `.github/workflows/scan.yml` and set the
cron expression to your desired cadence:

```yaml
schedule:
  - cron: "0 */6 * * *"   # every 6 hours
```

### Linting locally

```bash
pip3 install ruff
ruff check scripts/
ruff format --check scripts/

# Auto-fix
ruff check --fix scripts/ && ruff format scripts/
```

Config lives in `ruff.toml` at the repo root (`target-version = py39`,
`line-length = 100`).

## Project layout

```
sdr-fm-scan/
├── .github/workflows/
│   ├── generate-report.yml     # Auto-generate charts from CSV data
│   ├── scan.yml                # RTL-SDR scan on self-hosted runner
│   └── lint.yml                # ruff lint + format check
├── data/
│   └── output.csv              # Raw rtl_power scan (reference)
├── charts/
│   ├── heatmap.png             # Time/frequency waterfall
│   ├── spectrum_peaks.png      # Annotated spectrum (6 dB threshold, 15 signals)
│   └── final_report_chart.png  # Full 3-panel report (3 dB threshold, 29 signals)
├── scripts/
│   ├── analyze.py              # Standalone analysis CLI (peak detection + all charts + JSON)
│   ├── rtl_heatmap.py          # Heatmap generator
│   └── scan.sh                 # End-to-end scan + heatmap runner
├── ruff.toml                   # Linter / formatter configuration
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

# Named band presets
./scripts/scan.sh --band fm          # FM broadcast  87.5–108 MHz
./scripts/scan.sh --band marine      # Marine VHF    156–174 MHz
./scripts/scan.sh --band airband     # Aviation VHF  118–137 MHz
./scripts/scan.sh --band weather     # NOAA weather  162.4–162.55 MHz
./scripts/scan.sh --band 2m          # 2m amateur    144–148 MHz
./scripts/scan.sh --band 70cm        # 70cm amateur  430–440 MHz
./scripts/scan.sh --band ism433      # ISM/LoRa 433  433–434.79 MHz

# Custom range
./scripts/scan.sh --freq 156M:174M --step 25k

# Override duration or threshold for any preset
./scripts/scan.sh --band marine --duration 120 --threshold 6
```

Run `./scripts/scan.sh --help` for the full option list.

### Full analysis from an existing CSV

```bash
python3 scripts/analyze.py data/output.csv --outdir charts/
```

Outputs three charts (`_heatmap.png`, `_spectrum.png`, `_report.png`) and a
`_summary.json` into the specified directory.

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
