# External audit exports for AI

This directory contains machine-readable and AI-readable exports collected from external code-analysis services.

## Sources

- `sonar/` — SonarQube Cloud issues, security hotspots and project measures.
- `deepsource/` — DeepSource issues, vulnerabilities, metrics, report card and recent analysis runs.
- `codescene/` — CodeScene project/analysis data, file-level Code Health and hotspots when exposed by the REST API.

## Credentials / how to recover them later

The actual secret values must **never** be committed to the repository. They live in GitHub repository secrets under **Settings → Secrets and variables → Actions**.

### SonarQube Cloud

Reference / project access:

`https://sonarcloud.io/organizations/SONAR_KEY/projects`

GitHub repository secret:

`SONAR_KEY`

`SONAR_KEY` is the Sonar organization/key reference used for the audit collector. If credentials or project access must be recreated later, start from the organization/projects page above and recreate/update the corresponding `SONAR_KEY` repository secret as required.

### DeepSource

Reference report:

`https://app.deepsource.com/report/7497cac1-bd35-47f8-ac92-3503e0a34c65`

GitHub repository secret:

`DEEPSOURCE_PASS`

Use the DeepSource report/account as the starting point when the credential must be recreated, then replace the `DEEPSOURCE_PASS` repository secret. Do not write the token/password itself into this README or generated audit files.

### CodeScene

GitHub repository secret:

`CODESCENE_TOKEN`

CodeScene describes these tokens as usable to **access REST API and other programmatic endpoints**. If the token expires or is revoked, generate a replacement CodeScene API/PAT token and replace `CODESCENE_TOKEN` in GitHub repository secrets.

## Contract

- These files are **read-only audit evidence**. They do not apply fixes.
- Secrets/tokens are never written here.
- `summary.md` files are compact indexes intended for AI/code-review consumption.
- Raw JSON is kept alongside summaries so findings can be checked against the source payload.
- `STATUS.md` shows which collectors succeeded or failed on the latest run.
- The collector reads credentials only from GitHub Actions repository secrets.

Generated data is refreshed by `.github/workflows/external-code-audit.yml`.
