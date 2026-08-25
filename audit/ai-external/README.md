# External audit exports for AI

This directory contains machine-readable and AI-readable exports collected from external code-analysis services.

## Sources

- `sonar/` — SonarQube Cloud issues, security hotspots and project measures.
- `deepsource/` — DeepSource issues, vulnerabilities, metrics, report card and recent analysis runs.
- `codescene/` — CodeScene project/analysis data, file-level Code Health and hotspots when exposed by the REST API.

## Contract

- These files are **read-only audit evidence**. They do not apply fixes.
- Secrets/tokens are never written here.
- `summary.md` files are compact indexes intended for AI/code-review consumption.
- Raw JSON is kept alongside summaries so findings can be checked against the source payload.
- `STATUS.md` shows which collectors succeeded or failed on the latest run.

Generated data is refreshed by `.github/workflows/external-code-audit.yml`.
