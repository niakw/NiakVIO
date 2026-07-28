## 5.18.0

- Replace blind pre-build structural rewrites with a bounded baseline → diagnose → patch → exact deep retest → compare loop.
- Select repairs from generic runtime signatures and structural capabilities; the repair engine contains no provider IDs or domains.
- Add generic metadata-context recovery and DLE-like HTML search recovery as runtime-only profiles.
- Retain a generated JavaScript file only after a strict runtime improvement; runtime errors, neutral route-only changes and regressions keep the parent artifact.
- Revalidate the final staged tree after accepted repairs and publish `repair-report.json` with every accepted/rejected attempt.
- Keep URL/domain changes in simple durable overrides while behavioural adaptations remain shared profiles.
- Validate root and nested manifest paths, referenced provider files, and both `sources.json` version fields.
- Preserve 86 providers in the main manifest and 22 VF-capable providers, including disabled entries.

## 5.17.2

- Replace the provider-specific Frenchstream patch hook with a capability-driven, auto-applied HTML search-recovery profile.
- Apply the same recovery profile to every staged bundle exposing the same DLE-like search schema, regardless of provider ID.
- Keep provider-specific data limited to durable domain and wrapper compatibility overrides.
- Validate reusable patch-profile markers in staged and published provider files.
- Publish the Frenchstream final JS from the generic profile and keep manifests aligned.

## 5.17.1

- Finish the Frenchstream movie lookup patch on top of the locally verified `frenchstream.food` access.
- Parse current DLE search results across card, article, generic-link and data-id layouts.
- Remove obsolete `/films/.../` category fallbacks that currently return 404.
- Try multiple scored search matches before declaring the provider empty.
- Add a generic, versioned `patch_script` hook so complex provider fixes remain maintainable outside minified replacement strings.
- Update the Frenchstream manifest logo to the current domain.

## 5.17.0

- Restore trusted provider activation state and preserve enabled providers on inconclusive CI runs.
- Keep disabled French-capable providers in the VF manifest.
- Publish locally patched providers as deterministic `--nuvio--` JavaScript files.
- Persist Frenchstream domain, settings propagation and title fallback patches.

## 5.16.7

- Removed provider-specific origin probes and provider-specific deep-check fixtures.
- Added a global fixture-metadata fallback for TMDb title lookups when TMDb is unavailable or rejects the bundled key.
- Providers can now continue to their real site search routes, allowing genuine route observations instead of synthetic homepage probes.
- Mark synthetic TMDb fallback observations explicitly in health evidence.
- Apply the same diagnostic behavior to every provider without provider-specific blocking.

## 5.16.5

- Removed provider-specific strict route blocking from the global sync workflow.
- Route regressions and missing observations are now reported uniformly for every provider without failing unrelated providers.
- Kept `--strict` as a deprecated non-blocking compatibility flag.

## 5.16.2

## 5.16.4

- Added independent guarded origin probes for Frenchstream and StreamZo.
- Added provider-specific Tenet diagnostics for deep checks.
- Preserved network observations even when a provider crashes.
- Strict route validation now reports and blocks reachable origins with no observed lookup routes.
- Added regression tests for diagnostic fixtures and route-observation gaps.


- Make the promoted manifest version authoritative across `package.json`, `manifest.json`, `vf/manifest.json`, and `sources.json`.
- Add `scripts/sync_release_versions.py` so CI-generated manifest bumps cannot leave release metadata out of sync.
- Run release-integrity validation immediately before the manifest publication commit.
- Include all synchronized version files in the second publication phase.
- Add a regression test covering the synchronization workflow wiring.

## 5.16.1

- Align package, main manifest, VF manifest, and repository manifest versions.
- Pin all first-party GitHub Actions to immutable full commit SHAs.
- Add release-integrity checks for version alignment and immutable action references.
- Preserve the hardened provider, network, override, and route-regression controls from 5.16.0.

## 5.15.0

- Add a central `route_replacements` override namespace per provider, separate from domain replacements.
- Record sanitized HTTP method, request stage, host and path pattern for every provider request without publishing query values or tokens.
- Detect origin-reachable providers whose search/content routes mostly return 404/410 and publish `route-regressions.json`.
- Add an optional strict route gate for providers with validated route overrides.
- Preserve route diagnostics through the worker, health report and HTML/JSON diagnostics pipeline.
- Add regression tests for route-obsolescence detection and override schema validation.

## 5.14.4

- Persist the locally verified Frenchstream domain replacement: `french-stream.one` → `frenchstream.food`.
- Require the final published Frenchstream provider to contain `frenchstream.food`.
- Require the final published StreamZo provider to retain the verified `streamzo.fr` domain.
- Validate required domain values in both staging and final published provider files.
- Update Frenchstream logo URLs in the main and VF manifests.

# Changelog

## 5.17.4

- Fix the generic HTML-search patcher so it replaces complete top-level functions without deleting nested or adjacent helpers.
- Add syntax, load, and runtime smoke validation for every generated `--nuvio--` provider artifact.
- Reject invalid patched candidates before staging and revalidate the exact bytes before publication.
- Persist provider manifest metadata overrides, including the current Frenchstream favicon domain.
- Realign package, main manifest, VF manifest, and source manifest versions.

## 5.14.3

- Synchronize `manifest.json` and `vf/manifest.json` on version `5.14.2`.
- Treat `repository.manifest_version` as a version floor so unchanged runs cannot preserve an obsolete 5.13.x series.
- Add regression tests for manifest-series migration and normal patch increments.

## 5.14.1

- Added an end-to-end override pipeline gate that inspects the exact staged JavaScript later executed and promoted.
- Movix staging now fails if `api.movix.cash` survives or if a recorded replacement does not produce `api.movix.show`.
- Provenance now records `upstream_sha256`, `patched_sha256`, and `local_patches` for every selected provider.


## 5.14.0

- Added SSRF/DNS-rebinding protection for provider and media probes.
- Validate each redirect manually and reject private or metadata destinations.
- Added provider request, redirect and response-size quotas.
- Added durable, centrally tracked provider/domain overrides.
- Movix `api.movix.cash` is replaced with `api.movix.show` during staging.
- Preserve upstream SHA-256 separately from the locally patched SHA-256.
- Added stage-oriented JSON and HTML diagnostic reports.
- Added regression tests for the network guard and override pipeline.
- CI now runs the complete regression suite before upstream discovery.
