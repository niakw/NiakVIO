# NiakVIO checkpoint — 2026-09-09 — Desktop HTTP-200 zero + Core budget + durable media identity

## Desktop root-cause narrowing
- Official NuvioDesktop protected-byte bisect run **34338322836** (macOS, PersianStremio, Interstellar) proved the runtime loads the protected PersianStremio bundle and performs `GET https://persianstremio.vercel.app/stream/movie/157336.json` successfully (`HTTP 200`, `application/json`). Sanitized response-shape instrumentation proved the JSON itself contains no stream rows: `kind=object rows=0 objectRows=0 httpUrlRows=0 externalUrlRows=0`; final plugin result is `count=0` in under one second.
- Therefore the PersianStremio Desktop zero is **not** a QuickJS JSON/result-parser loss and is not caused by the former 25/30 s Core budget. The numeric TMDB backend route itself is empty for this fixture.
- Official NuvioDesktop uses a single positional identity at its plugin boundary: `StreamsRepository` -> `PluginRepository` -> `PluginRuntime.executePlugin(tmdbId, mediaType, season, episode)` -> `getStreams(tmdbId, mediaType, season, episode)`. NuvioMobile has the same structural four-argument contract. Mobile/Desktop must not require users to configure a TMDB key to recover IMDb identity.
- NuvioTV uses the same four-argument ABI but has an audited runtime TMDB capability, allowing Core to hydrate TMDB metadata/external_ids and derive IMDb. Treat this as an equivalent identity capability, **not** permission for shared provider bundles to depend on `TMDB_API_KEY`.

## Core timeout authority fixed in source
- `CORE.MEDIA_TYPE_RESOLUTION` previously owned a shorter internal execution deadline while Native Labs owned an outer deadline. This created competing timeout authorities and could drop valid late results after network return.
- Source fix commit **a2ccd335ea3be285e3a37807488605abdc195865** (`fix(core): unify provider execution budget at 60s`) sets canonical Core `providerTimeoutMs=60000` and `tvProviderTimeoutMs=60000`, revision `tmdb-data-contract-launch-gate-v30-unified-60s-budget`.
- Validation run **34339079601** completed fully green, including media-resolution contracts, latest-request cancellation, abort-ignoring native-fetch cancellation and Core budget non-regression.
- Do **not** rematerialize this Core into already protected green provider lanes until required live A/B proves no regression. Green lane bytes remain immutable authority.

## Desktop media-identity A/B history
- Baseline evidence is stable: protected PersianStremio bytes on official Desktop call `/stream/movie/157336.json`, receive HTTP 200 with zero stream rows, and finish `count=0`.
- Host resolution for Interstellar maps TMDB **157336** to IMDb **tt0816692**. TMDB credentials are used host-side only for the Lab resolution and are never projected into provider JavaScript.
- Run **34341065713** established a valid baseline (`count=0 imdb_route=false numeric_route=true`); its first dual branch was harness-invalid because mutation happened before human-UX purity audits. Never weaken those audits.
- Run **34343072382** is valid evidence against the *V2 injection point*, not against dual-ID itself. Baseline job **102438235395** passed. Dual job **102438235616** successfully resolved `tt0816692`, injected the canonical `tmdbMetadata.external_ids.imdb_id` shape after checkout purity audits, executed the provider, but still produced `count=0 imdb_route=false numeric_route=true`. Provider bytes remained unchanged.
- Exact source inspection then proved why V2 could not work: NiakVIO Core itself rewrites `globalThis.__nuvioMediaContext = a.__nuvioContext || null` before provider execution and again after authoritative resolution. Core also initializes `var mediaCache=Object.create(null); globalThis.__nuvioTmdbMetadataCacheV1=mediaCache` while the provider/Core bundle is evaluated. Therefore any host identity global/cache injected **before** `evaluate(wrappedCode)` is destroyed or superseded before the provider consumes it.
- PersianStremio's existing `hydrateImdb()` already consumes the canonical shared metadata surfaces in order: `__nuvioMediaContext.tmdbMetadata`, `__nuvioTmdbMetadataCacheV1[<namespace>:<tmdbId>]`, then `__nuvioCoreGetTmdbDataV1`. The correct host bridge is therefore systemic, not provider-specific.

## Canonical identity architecture restored and locked
- Architectural invariant: positional `getStreams(tmdbId, mediaType, season, episode)` is **transport**, not the complete media identity contract.
- Canonical context IMDb path: **`__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`**.
- Canonical shared metadata cache: **`__nuvioTmdbMetadataCacheV1`**, with host-provided entries shaped as `state=ok` + `metadata.external_ids.imdb_id`.
- A host-side identity bridge must populate the shared metadata identity **after provider/Core bundle initialization and before `getStreams` invocation**. Pre-bundle injection is explicitly invalid because Core initializes/rewrites these globals.
- No end-user TMDB credential may be required for NiakVIO compatibility, and no TMDB secret may be projected into provider JavaScript merely to recover IMDb identity.
- Desktop/Mobile currently have a documented host identity-hydration gap; Android TV currently has equivalent Core hydration through its audited runtime metadata capability.
- V3 Lab bridge commit **bf37cbdf20dfefd6be3e6e033ea44f1fae675f2e** moves identity injection after `evaluate(wrappedCode)` and populates Core's canonical metadata cache before `getStreams`. Test commit **f65a8dfdd243e3ad963cc358f320a95a23c2e5eb** locks ordering, cache shape, no-secret behavior and idempotence. Commit **9135b4036f38fd5dca97e2a12d6ef1c3eb045b35** keeps only a temporary V2 marker for compatibility with the one-shot A/B harness; V3 is the active bridge.
- Runtime compatibility is now being made executable, not documentary only: migration `scripts/upgrade_runtime_media_identity_contract_v1.py` commit **12aec359e851fb080d41839f518c40968748b6f7**; strengthened `scripts/runtime_contract_gate.py` commit **988e2374fc05fb5aef62641e7b8a1a41bffaa544**; renderer commit **39bf05a107f2d3ce345f5031c20c350ef100a455**. The canonical JSONs/README must be generated and pass CI before this checkpoint is considered complete.
- Runtime-contract materialization workflow run **34344595051** was queued from commit **bc217211be6e4fd6226b5b93416b868d5c3a7feb**. It must prove migration idempotence, renderer fixed point, semantic assertions, and executable runtime gate before committing generated JSON/Markdown.
- V3 Desktop A/B run **34344396120** was in progress at this checkpoint. Do not claim the media identity root fix until the dual job proves an IMDb route and `count>0` with the protected PersianStremio bytes unchanged.

## Memory durability
- `.github/workflows/memory-checkpoint.yml` was previously main-only, so workbench checkpoints could remain outside `MEMORY.md`. Commit **c78baa379950bd30604a9463dd06be62d479f357** makes the writer branch-aware for `main` and `workbench/**`, checks out/pulls/pushes the actual branch, and keeps the append idempotent.
- This pending checkpoint update must trigger the branch-aware writer. Verify physically that this heading appears in workbench `MEMORY.md` and that the pending file is reset before considering memory persistence complete.

## Immediate continuation authority
1. Collect V3 A/B run **34344396120**. Success requires protected bytes unchanged, `/stream/movie/tt...json` observed, and `FIELD_NATIVE_RESULT count>0`; otherwise continue the runtime bisect without forcing the conclusion.
2. Collect runtime-contract run **34344595051** and verify generated `automation/platform-runtime-contracts.json`, `automation/nuvio-client-compatibility-matrix.json`, and `automation/PLATFORM-RUNTIME-CONTRACTS.md` physically contain the identity invariant.
3. Verify the branch-aware Memory writer appends this checkpoint into workbench `MEMORY.md` and clears `automation/memory-checkpoint-pending-v2.md`.
4. Once the V3 mechanism is proven, convert the Lab-only bridge into the smallest backward-compatible client/runtime contract for Desktop and Mobile; preserve the four-argument provider ABI and keep provider bytes/secrets untouched.
5. Remove one-shot/temporary workflow and marker after evidence is persisted.
6. Resume lane-scoped Repair across all 96 Provider Objects; protected green lanes remain exact-byte immutable unless live A/B proves a non-regressing replacement.
7. Mandatory end state remains all 96 plus five Native Labs (Android TV, Android Mobile, iOS Mobile, macOS Desktop, Windows Desktop), final projections, security/docs/minimizer/fixed-point gates, and the real Purstream House of the Dragon S3E1 check before publication.
