# External audit exports for AI

This directory contains machine-readable and AI-readable exports collected from external code-analysis services.

## Sources

- `sonar/` — SonarQube Cloud public project discovery, issues, security hotspots, measures and analyses when exposed by the public endpoints.
- `deepsource/` — DeepSource repository issues/occurrences, dependency vulnerabilities and analysis runs fetched from the official GraphQL API.
- `codescene/` — CodeScene project/analysis data, file-level Code Health and hotspots exposed by the REST API.

## Access / how to recover it later

The actual secret values must **never** be committed to the repository. Values needed by the workflows live in GitHub repository secrets under **Settings → Secrets and variables → Actions**.

### SonarQube Cloud

Reference / project access:

`https://sonarcloud.io/organizations/SONAR_KEY/projects`

GitHub repository secret:

`SONAR_KEY`

`SONAR_KEY` is the public Sonar organization/key reference contained in the URL above. It is **not** treated as an API token and the collector does not authenticate to Sonar with it. If the organization reference changes later, recover the value from the `/organizations/<key>/projects` URL and update the `SONAR_KEY` repository secret.

### DeepSource

Current programmatic access:

`https://api.deepsource.com/graphql/`

GitHub repository secret:

`DEEPSOURCE_API`

`DEEPSOURCE_API` is a DeepSource Personal Access Token used as a Bearer token by the official GraphQL API. Create/rotate it from the DeepSource user settings **Tokens** page, then replace the `DEEPSOURCE_API` GitHub Actions repository secret. The collector never writes the token to the repository.

The previous shared-report reference is kept here only so the historical setup can be found later:

`https://app.deepsource.com/report/7497cac1-bd35-47f8-ac92-3503e0a34c65`

Previous secret name: `DEEPSOURCE_PASS` (legacy shared-report password; no longer used by the collector).

### CodeScene

GitHub repository secret:

`CODESCENE_TOKEN`

CodeScene describes these tokens as usable to **access REST API and other programmatic endpoints**. If the token expires or is revoked, generate a replacement CodeScene API/PAT token and replace `CODESCENE_TOKEN` in GitHub repository secrets.

## Refresh policy

The exports are **not refreshed on every push**. The single permanent workflow `.github/workflows/external-code-audit.yml` owns both supported refresh modes:

- **Weekly automatic refresh** — every Sunday at `04:17 UTC` through its built-in `schedule` trigger.
- **Manual refresh** — run **External Code Audit** through its `workflow_dispatch` trigger whenever a fresh snapshot is needed immediately.

The retired `.github/workflows/external-code-audit-refresh.yml` convenience launcher is intentionally no longer part of the repository; scheduling and manual dispatch are consolidated in the collector itself.

The service collectors live under `scripts/external_audit/` so API-specific logic stays out of the workflow YAML and can be maintained/tested independently.

Typical reasons for a manual refresh: after substantial repository changes, before/after a cleanup/refactor pass, after changing the Sonar organization key, rotating `DEEPSOURCE_API`, rotating the CodeScene token, or when fresh audit evidence is explicitly requested.

## Contract

- These files are **read-only audit evidence**. They do not apply fixes.
- Secrets/passwords/tokens are never written here.
- `summary.md` files are compact indexes intended for AI/code-review consumption.
- Raw JSON is kept alongside summaries so findings can be checked against the source payload.
- `STATUS.md` shows which collectors succeeded or failed on the latest run and which access mode was used.
- Sonar uses its public organization key; DeepSource uses the official GraphQL API with `DEEPSOURCE_API`; CodeScene uses its REST API token.
