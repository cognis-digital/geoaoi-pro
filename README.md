# geoaoi-pro — MIL-STD-2525 + APP-6 helpers for QGIS

[![CI](https://github.com/cognis-digital/geoaoi-pro/workflows/CI/badge.svg)](https://github.com/cognis-digital/geoaoi-pro/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Validate, audit, and sanity-check MIL-symbol GeoJSON layers used in QGIS or anywhere else.

<!-- cognis:layman:start -->
## What is this?

geoaoi-pro is a command-line tool that checks map data files used in military and intelligence operations. It reads GeoJSON files — a common format for storing location data — and flags problems like missing or incorrectly formatted military symbol codes (the standardized codes that identify friendly, hostile, or neutral forces on a map). The tool is useful for GIS analysts, defense contractors, and anyone working with QGIS map layers who needs to make sure their military symbology data meets MIL-STD-2525 standards before using it in operations or reports.
<!-- cognis:layman:end -->

## Upstream

Forks / wraps **https://github.com/qgis/QGIS**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- MIL-STD-2525C symbol-code validation (15-char SIDC)
- APP-6 affiliation/scheme dictionaries
- AOI bbox + haversine helpers
- GeoJSON layer auditor

<!-- cognis:install:start -->
## Install

`geoaoi-pro` is source-available (not published to PyPI) — every method below installs
straight from GitHub. Pick whichever you prefer; the one-line scripts auto-detect
the best tool available on your machine.

**One-liner (Linux / macOS):**
```sh
curl -fsSL https://raw.githubusercontent.com/cognis-digital/geoaoi-pro/HEAD/install.sh | sh
```

**One-liner (Windows PowerShell):**
```powershell
irm https://raw.githubusercontent.com/cognis-digital/geoaoi-pro/HEAD/install.ps1 | iex
```

**Or install manually — any one of:**
```sh
pipx install "git+https://github.com/cognis-digital/geoaoi-pro.git"     # isolated (recommended)
uv tool install "git+https://github.com/cognis-digital/geoaoi-pro.git"  # uv
pip install "git+https://github.com/cognis-digital/geoaoi-pro.git"      # pip
```

**From source:**
```sh
git clone https://github.com/cognis-digital/geoaoi-pro.git
cd geoaoi-pro && pip install .
```

Then run:
```sh
geoaoi-pro --help
```
<!-- cognis:install:end -->

## Install

```bash
# Shared library (only once for the whole ecosystem):
pip install -e ../../shared

# This tool:
pip install -e .
```

## Demo

```bash
geoaoi-pro demos/
```

Outputs are available in five formats — all respect an operator-supplied
classification banner (passed via `--classification`):

```bash
geoaoi-pro <target> --format=console     # default
geoaoi-pro <target> --format=json
geoaoi-pro <target> --format=sarif       # for code-scanning pipelines
geoaoi-pro <target> --format=markdown    # for PRs / briefings
geoaoi-pro <target> --format=oscal       # OSCAL Assessment Results skeleton
```

## Classification banner

All output is wrapped with an operator-supplied classification banner.
**Default**: `UNCLASSIFIED//FOR PUBLIC RELEASE`.

> ⚠️ This tool **does not** generate or validate the *content* of higher
> classifications. Operators on cleared systems supply real markings at runtime.
> See [`../shared/cognis_mil/classmark.py`](../../shared/cognis_mil/classmark.py).

## Compliance crosswalks (built in)

Every finding can carry references to:
- **NIST 800-53 Rev 5** controls (e.g. `AC-2(1)`)
- **DISA STIG** rule IDs (e.g. `V-242414`)
- **MITRE ATT&CK** technique IDs (e.g. `T1078`)
- **CCI** (Control Correlation Identifier)

These are emitted in JSON, SARIF, and the OSCAL skeleton.

## CI / RMF integration

```yaml
- name: geoaoi-pro scan
  run: |
    pip install "git+https://github.com/cognis-digital/geoaoi-pro.git"
    geoaoi-pro . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).

<a name="verification"></a>
## Verification

[![tests](https://img.shields.io/badge/tests-4%20passing-2ea44f.svg)](AUDIT.md)

Every push is verified end-to-end. Latest audit (2026-06-13):

```text
tests        : 4 passed, 0 failed, 0 errored
compile      : all modules parse
cli          : geoaoi-pro 0.1.0
package      : geoaoi_pro
```

<details><summary>CLI surface (<code>--help</code>)</summary>

```text
usage: geoaoi-pro [-h] [--format {console,json,markdown,sarif,oscal}]
                  [--out OUT] [--fail-on {very_high,high,moderate,low,none}]
                  [--classification CLASSIFICATION] [-v]
                  [target]

geoaoi-pro — Cognis Digital · Military/IC ecosystem

positional arguments:
  target                Path/target

options:
  -h, --help            show this help message and exit
  --format {console,json,markdown,sarif,oscal}
  --out OUT             Write output to file
```
</details>

Full machine-readable results: [`AUDIT.md`](AUDIT.md) · regenerate with `python -m geoaoi_pro --help` + `pytest -q`.

<div align="right"><a href="#top">↑ back to top</a></div>

