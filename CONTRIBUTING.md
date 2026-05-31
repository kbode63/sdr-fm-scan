# Contributing

Thank you for your interest in contributing to **sdr-fm-scan**! This guide
covers everything you need to get started.

## Table of contents

- [Code of conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Submitting changes](#submitting-changes)
- [Coding standards](#coding-standards)
- [Adding a new scan session](#adding-a-new-scan-session)

---

## Code of conduct

Be respectful and constructive. Harassment or abusive behaviour will not be
tolerated.

---

## Ways to contribute

- **Bug reports** — open an issue with steps to reproduce, your OS, Python
  version, and RTL-SDR hardware model.
- **Feature requests** — open an issue describing the use-case before
  starting work on a PR.
- **New scan data** — share a scan from a different location or frequency
  band; see [Adding a new scan session](#adding-a-new-scan-session).
- **Script improvements** — better peak detection, new visualisation types,
  performance improvements, etc.
- **Documentation** — fix typos, clarify instructions, or add examples.

---

## Development setup

### Prerequisites

| Tool | Install |
|------|---------|
| RTL-SDR dongle | Realtek RTL2832U-based (e.g. RTL2838UHIDIR) |
| librtlsdr | `brew install librtlsdr` (macOS) / `sudo apt install rtl-sdr` (Linux) |
| Python ≥ 3.9 | <https://www.python.org/downloads/> |
| Python packages | `pip3 install matplotlib numpy pandas` |

### Clone and verify

```bash
git clone https://github.com/kbode63/sdr-fm-scan.git
cd sdr-fm-scan
rtl_test -t          # confirm dongle is detected
python3 scripts/rtl_heatmap.py data/output.csv /tmp/test.png  # smoke test
```

---

## Submitting changes

1. **Fork** the repository and create a branch from `main`:

   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes.** Keep commits focused — one logical change per
   commit. Write clear commit messages:

   ```
   Short summary (≤ 72 chars)

   Longer explanation of what and why, if needed.
   ```

3. **Test your changes:**

   ```bash
   # Regenerate heatmap from reference data and confirm it produces output
   python3 scripts/rtl_heatmap.py data/output.csv /tmp/check.png
   ```

4. **Push and open a pull request** against `main`. Fill in the PR template
   (what changed, why, and how it was tested).

5. A maintainer will review and merge. Please respond to review comments
   within a reasonable time.

---

## Coding standards

- **Python** — follow [PEP 8](https://peps.python.org/pep-0008/). Keep
  lines ≤ 100 characters. Use f-strings over `%`-formatting.
- **Shell scripts** — start with `#!/usr/bin/env bash` and `set -euo pipefail`.
  Quote all variables.
- **No secrets** — never commit API keys, credentials, or personal location
  data.
- **Charts** — if a script produces a chart, it must also print the output
  path to stdout so it can be piped or scripted.

---

## Adding a new scan session

To contribute a scan from a different location or band:

1. Run a scan and name the output with a timestamp:

   ```bash
   ./scripts/scan.sh 85M 110M 125k 60
   # produces data/scan_<timestamp>.csv and charts/heatmap_<timestamp>.png
   ```

2. These files are excluded by `.gitignore` by default. If you want to
   include a reference scan, rename `data/scan_<timestamp>.csv` to
   `data/<band>_<location>.csv` (e.g. `data/fm_sanfrancisco.csv`) and add
   it explicitly:

   ```bash
   git add -f data/fm_sanfrancisco.csv
   ```

3. Update `README.md` with a summary row in the **Detected signals** table
   and open a PR.

---

## Questions?

Open an issue at <https://github.com/kbode63/sdr-fm-scan/issues> or start a
discussion on the repository's Discussions tab.
