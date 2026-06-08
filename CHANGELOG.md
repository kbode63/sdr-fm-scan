# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [v1.2.0] — 2026-06-08

### Added
- `scripts/main.py` — unified CLI entry point with four subcommands:
  `scan`, `analyze`, `gui`, `heatmap`. Each delegates to the existing
  underlying script for a consistent single-command interface.
- `requirements.txt` — pinned Python 3.14 venv dependencies (`streamlit`,
  `matplotlib`, `numpy`, `watchdog`, and transitive packages).
- `charts/` — committed airband (118–137 MHz) and ISM 433 scan artifacts
  from prior runs.

### Changed
- `launch-gui.sh` — replaced hardcoded Python 3.9 user-site path with
  automatic venv detection (`.venv/bin/streamlit`); falls back to PATH.
- `README.md` — new `main.py` section with synopsis, quick examples, and
  options tables; updated Installation to use `python3 -m venv` +
  `pip install -r requirements.txt`; updated project layout.

### Infrastructure
- Homebrew installed and configured as the macOS package manager.
- Python 3.14.5 installed via Homebrew, replacing the system Python 3.9.
- Project virtual environment created at `.venv`.

---

## [v1.1.0] — 2026-05-31

### Added
- Streamlit web GUI (`scripts/gui.py`) with live scan output streaming,
  progress bar, band presets, and signal classification.
- Voice/data signal classification by frequency range.
- Progress bar (0 → 100%) tracking both `rtl_power` capture and analysis.
- `launch-gui.sh` convenience script.
- 30-minute maximum scan duration slider.
- All valid R820T gain steps exposed in the GUI.

### Changed
- Default step size set to `5k` in custom-range mode.

---

## [v1.0.0] — 2026-05-31

### Added
- `scripts/scan.sh` — end-to-end RTL-SDR capture and analysis with named
  band presets (FM, airband, weather, marine, 2m, 70cm, ISM 433).
- `scripts/analyze.py` — standalone CSV analysis: peak detection, heatmap,
  spectrum, full 3-panel report, and JSON summary.
- `scripts/rtl_heatmap.py` — lightweight standalone heatmap generator.
- Signal tier classification: STRONG / MEDIUM / WEAK / MARGINAL by SNR.
- GitHub Actions workflows: lint (`ruff`), report generation, self-hosted
  scan runner with `rtl-sdr` label.
- Reference scan data (`data/output.csv`) and charts.
