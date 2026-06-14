# geoaoi-pro — MIL-STD-2525 + APP-6 helpers for QGIS

[![CI](https://github.com/cognis-digital/geoaoi-pro/workflows/CI/badge.svg)](https://github.com/cognis-digital/geoaoi-pro/actions)
[![Classification](https://img.shields.io/badge/classification-UNCLASSIFIED-green.svg)](./UPSTREAM.md)

> Validate, audit, and sanity-check MIL-symbol GeoJSON layers used in QGIS or anywhere else.

## Usage — step by step

`geoaoi-pro` validates MIL-STD-2525 / APP-6 symbol codes (SIDC) and AOI coordinate geometry in your input files, emitting findings.

1. **Install:**

   ```bash
   pip install cognis-geoaoi-pro      # or: pip install -e .
   geoaoi-pro --version
   ```

2. **Run a scan** over a directory of symbol/AOI JSON files (`target` defaults to `.`):

   ```bash
   geoaoi-pro ./overlays --format console
   ```

3. **Emit JSON** for tooling and write it to disk (formats: `console`, `json`, `markdown`, `sarif`, `oscal`):

   ```bash
   geoaoi-pro ./overlays --format json --out sidc-findings.json
   ```

4. **Read the result** — findings flag missing SIDC (`GP-NOSIDC-*`), malformed SIDC (`GP-BADSIDC-*`), and bad coordinates (`GP-COORDS-*`), each with a severity:

   ```bash
   jq '.findings[] | {id, severity, location}' sidc-findings.json
   ```

5. **Gate it in CI** — fail the build on high-severity symbology errors:

   ```bash
   geoaoi-pro ./overlays --format sarif --out geoaoi.sarif --fail-on high
   ```

## Upstream

Forks / wraps **https://github.com/qgis/QGIS**. See [`UPSTREAM.md`](./UPSTREAM.md) for the
licensing posture, supported commits, and how to upgrade.

## What this adds for military / IC use

- MIL-STD-2525C symbol-code validation (15-char SIDC)
- APP-6 affiliation/scheme dictionaries
- AOI bbox + haversine helpers
- GeoJSON layer auditor

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
    pip install cognis-geoaoi-pro
    geoaoi-pro . --format=oscal --out=assessment-results.json --fail-on=high
- name: Upload to eMASS/Xacta
  run: cognis-rmf-package import assessment-results.json
```

## Part of the Cognis Digital military / IC ecosystem

12 repos. All MIT/Apache-2.0/GPL-3 (per upstream). Cognis additions are
Apache-2.0 unless stated otherwise.

See [the master index](../../MASTER-INDEX.md).

## Interoperability

`geoaoi-pro` composes with the 300+ tool Cognis suite — JSON in/out and a shared
OpenAI-compatible `/v1` backbone. See **[INTEROP.md](INTEROP.md)** for the
suite map, composition patterns, and reference stacks.

## Integrations

Forward `geoaoi-pro`'s findings to STIX/MISP/Sigma/Splunk/Elastic/Slack/webhooks via
[`cognis-connect`](https://github.com/cognis-digital/cognis-connect). See **[INTEGRATIONS.md](INTEGRATIONS.md)**.
