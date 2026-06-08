# SDR Frequency Scanner

RTL-SDR passive spectrum scanner with automated peak detection, heatmap
generation, and multi-band preset support. Ships with named presets for FM
broadcast, marine VHF, aviation, amateur, NOAA weather, and ISM bands.

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

## Usage

### Installation

```bash
# macOS
brew install librtlsdr

# Debian / Ubuntu
sudo apt install rtl-sdr
```

Install Python dependencies into a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify your dongle is recognised:

```bash
rtl_test -t
# Expected: "Found 1 device(s)"
```

---

### `main.py` — unified CLI entry point

`scripts/main.py` is the single entry point for all scanner operations.
It wraps `scan.sh`, `analyze.py`, `gui.py`, and `rtl_heatmap.py` behind a
consistent subcommand interface.

#### Synopsis

```
python3 scripts/main.py <COMMAND> [OPTIONS]

Commands:
  scan      Capture + analyse spectrum (RTL-SDR dongle required)
  analyze   (Re-)analyse an existing CSV without the dongle
  gui       Launch the Streamlit web interface
  heatmap   Generate a standalone heatmap PNG from a CSV
```

#### Quick examples

```bash
# Launch the web GUI
python3 scripts/main.py gui
python3 scripts/main.py gui --port 8502

# Scan a named band (dongle required)
python3 scripts/main.py scan --band fm
python3 scripts/main.py scan --band marine --duration 120 --threshold 6
python3 scripts/main.py scan --freq 156M:174M --step 25k

# Re-analyse an existing CSV
python3 scripts/main.py analyze data/output.csv
python3 scripts/main.py analyze data/output.csv --threshold 10 --outdir /tmp/charts

# Generate a standalone heatmap
python3 scripts/main.py heatmap data/output.csv charts/heatmap.png
```

#### Options — `scan`

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--band` | `-b` | — | Named band preset (see table below). Mutually exclusive with `--freq`. |
| `--freq` | `-f` | — | Custom range as `LOW:HIGH`, e.g. `156M:174M`. |
| `--step` | `-s` | preset default | Frequency bin size, e.g. `25k`. |
| `--duration` | `-d` | `60` | Scan duration in seconds. |
| `--gain` | `-g` | `49.6` | Tuner gain in dB (0–49.6). |
| `--threshold` | `-t` | `3.0` | Minimum SNR in dB above noise floor. |

#### Options — `analyze`

| Flag | Default | Description |
|------|---------|-------------|
| `csv` | *(required)* | Path to an `rtl_power` output CSV. |
| `--outdir` | `charts/` | Directory to write charts and JSON into. |
| `--threshold` | `3.0` | Minimum SNR in dB above noise floor. |
| `--prefix` | *(none)* | String prepended to all output filenames. |
| `--json-out` | `<outdir>/<stem>_summary.json` | Override JSON output path. |

---

### `scan.sh` — capture and analyse

`scripts/scan.sh` runs `rtl_power`, then pipes the output straight into
`analyze.py` to produce charts and a JSON summary in one step.

#### Synopsis

```
scripts/scan.sh [--band BAND] [--freq LOW:HIGH] [--step STEP]
                [--duration SECS] [--gain DB] [--threshold DB]
```

#### Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--band` | `-b` | — | Named band preset (see table below). Overrides `--freq`. |
| `--freq` | `-f` | — | Custom range as `LOW:HIGH`, e.g. `156M:174M`. |
| `--step` | `-s` | preset default | Frequency bin size, e.g. `25k`. Overrides the preset default. |
| `--duration` | `-d` | `60` | Scan duration in seconds. |
| `--gain` | `-g` | `49.6` | Tuner gain in dB (0–49.6). |
| `--threshold` | `-t` | `3.0` | Minimum SNR in dB above noise floor for peak detection. |
| `--help` | `-h` | — | Print usage and exit. |

#### Band presets

| Preset | Range | Default step | Typical use |
|--------|-------|-------------|-------------|
| `fm` | 87.5–108 MHz | 125 kHz | FM broadcast stations |
| `airband` | 118–137 MHz | 25 kHz | Aviation voice (AM) |
| `weather` | 162.4–162.55 MHz | 2.5 kHz | NOAA Weather Radio (US) |
| `marine` | 156–174 MHz | 25 kHz | Marine VHF (DSC, distress, working channels) |
| `2m` | 144–148 MHz | 12.5 kHz | 2 m amateur radio |
| `70cm` | 430–440 MHz | 12.5 kHz | 70 cm amateur radio |
| `ism433` | 433.05–434.79 MHz | 5 kHz | ISM band / LoRa devices |

#### Examples

```bash
chmod +x scripts/scan.sh

# Scan by preset
./scripts/scan.sh --band fm
./scripts/scan.sh --band marine
./scripts/scan.sh --band airband

# Longer scan with a lower detection threshold
./scripts/scan.sh --band marine --duration 120 --threshold 6

# Override the step size for higher resolution
./scripts/scan.sh --band fm --step 50k

# Fully custom range
./scripts/scan.sh --freq 156M:174M --step 25k --duration 60

# Show all options
./scripts/scan.sh --help
```

#### Output files

All outputs are written relative to the repo root:

```
data/scan_<band>_<timestamp>.csv                      raw rtl_power data
charts/<band>_scan_<band>_<timestamp>_heatmap.png     time/frequency waterfall
charts/<band>_scan_<band>_<timestamp>_spectrum.png    annotated spectrum + SNR bars
charts/<band>_scan_<band>_<timestamp>_report.png      full 3-panel report
charts/<band>_scan_<band>_<timestamp>_summary.json    machine-readable signal list
```

Timestamps are UTC in `YYYYMMDDTHHMMSSz` format.
Raw CSVs are excluded from git by `.gitignore`; charts and JSON are committed.

---

### `analyze.py` — analyse an existing CSV

Use this to (re-)generate charts from any scan CSV without running the dongle.

#### Synopsis

```
scripts/analyze.py CSV [--outdir DIR] [--threshold DB]
                       [--prefix STR] [--json-out PATH]
```

#### Options

| Flag | Default | Description |
|------|---------|-------------|
| `CSV` | *(required)* | Path to an `rtl_power` output CSV. |
| `--outdir` | `charts/` | Directory to write chart and JSON output into. |
| `--threshold` | `3.0` | Minimum SNR in dB above noise floor for peak detection. |
| `--prefix` | *(none)* | String prepended to all output filenames. |
| `--json-out` | `<outdir>/<stem>_summary.json` | Override the JSON summary path. |

#### Examples

```bash
# Regenerate all charts from the reference scan
python3 scripts/analyze.py data/output.csv

# Stricter threshold — only signals 10 dB above noise
python3 scripts/analyze.py data/output.csv --threshold 10

# Write to a custom output directory
python3 scripts/analyze.py data/output.csv --outdir /tmp/charts

# Export JSON summary to a specific path
python3 scripts/analyze.py data/output.csv --json-out results/summary.json
```

#### Output

For an input file `data/output.csv`, the following are written to `--outdir`:

| File | Description |
|------|-------------|
| `output_heatmap.png` | Time × frequency waterfall (inferno colour map) |
| `output_spectrum.png` | Mean spectrum with annotated peaks + SNR bar chart |
| `output_report.png` | Full 3-panel report (waterfall + spectrum + SNR) |
| `output_summary.json` | JSON with scan metadata and per-signal metrics |

#### Signal tiers

Peaks are classified by SNR above the median noise floor:

| Tier | SNR | Colour |
|------|-----|--------|
| STRONG | > 20 dB | Red |
| MEDIUM | 14–20 dB | Orange |
| WEAK | 6–14 dB | Green |
| MARGINAL | 3–6 dB | Blue |

---

### `gui.py` — Streamlit web interface

A browser-based GUI that wraps `scan.sh` and `analyze.py` with live output
streaming, interactive controls, and inline chart display.

#### Launch

```bash
cd ~/sdr-fm-scan
streamlit run scripts/gui.py
# Opens automatically at http://localhost:8501
```

#### Sidebar controls

| Control | Type | Description |
|---------|------|-------------|
| Frequency source | Radio | Switch between **Band preset** and **Custom range** |
| Band | Dropdown | All 7 presets — Marine VHF pre-selected |
| Low / High freq | Text | Custom range inputs when in Custom mode |
| Step | Text | Defaults to `5k`; leave blank in Band mode to use the preset default |
| Duration | Slider | **5–1800 s (up to 30 min)** — longer scans catch intermittent signals |
| Gain | Select-slider | All valid R820T gain steps (0–49.6 dB) |
| SNR threshold | Slider | 1–20 dB above noise floor |
| ▶ Start Scan | Button | Disabled while a scan is running |

#### Progress indicator

A progress bar appears below the live output heading as soon as a scan starts:

- Fills **0 → 95%** proportionally over the target duration (updated on every
  output line from `rtl_power`)
- Jumps to **98%** when `analyze.py` begins generating charts
- Reaches **100% ✅** on completion
- Label shows elapsed time in `Xm XXs elapsed / N s target` format

#### Results panel

After a scan completes (or on first launch, the most recent scan is loaded
automatically from `charts/`):

- **Metadata strip** — frequency range, duration, noise floor, signal count, time (UTC)
- **Chart tabs** — Heatmap · Spectrum · Report (full-res PNGs from `analyze.py`)
- **Tier badges** — 🔴 Strong · 🟠 Medium · 🟢 Weak · 🔵 Marginal counts
- **Signal table** — freq, **type**, **service**, mean/peak power, SNR, tier, stability
- **Download buttons** — JSON summary and report PNG

#### Signal classification

Every detected peak is automatically classified into a signal type and service
based on its frequency:

| Type | Emoji | Example services |
|------|-------|------------------|
| Voice | 🎙 | FM Broadcast, Aviation (AM), Marine VHF, NOAA Weather Radio |
| Data | 📡 | DSC Channel 70, ISM / LoRa, Weather satellites, Aeronautical nav |
| Mixed | 🎙/📡 | 2m Amateur, 70cm Amateur |
| Unknown | ❓ | Frequencies outside all known allocations |

The classifier matches the **narrowest** frequency range, so overlapping
allocations resolve correctly (e.g. 156.525 MHz → DSC Channel 70 rather
than the broader Marine VHF entry).

#### Live output

While scanning, the last 30 lines of `scan.sh` stdout update in real time inside
a scrolling code block, so you can monitor `rtl_power` progress and `analyze.py`
output without leaving the browser.

#### Notes

- The GUI requires the RTL-SDR dongle to be connected for scanning; it will
  display an error with exit code if the device is not found.
- Streamlit 1.50+ is required (`pip3 install streamlit` installs the latest).
- To run on a remote host and access via a local browser, add
  `--server.address 0.0.0.0` to the launch command.

---

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
│   ├── main.py                 # Unified CLI entry point (scan / analyze / gui / heatmap)
│   ├── analyze.py              # Standalone analysis CLI (peak detection + all charts + JSON)
│   ├── gui.py                  # Streamlit web interface
│   ├── rtl_heatmap.py          # Heatmap generator
│   └── scan.sh                 # End-to-end scan + band-preset runner
├── requirements.txt            # Pinned Python dependencies
├── ruff.toml                   # Linter / formatter configuration
└── README.md
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
