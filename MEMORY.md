# NiakVIO — Recovery Memory

Last authoritative checkpoint: 2026-09-07 00:18 Europe/Paris.

This file is the durable recovery source of truth for the active NiakVIO work. Prefer current repository state and exact GitHub Actions/native logs over older chat summaries. Update this file at every important correction/failure/publication checkpoint before moving to the next risky step.

## Repository topology / execution policy

- Repository: `niakw/NiakVIO`.
- **`main` is the only active write/publication target.** Do not recreate a persistent workbench branch.
- Durable Learning proposal branch: `brain-learning/proposals`; proposal storage only, not publication authority.
- Cleanup completed after 5.21.35 publication: `workbench` deleted, `hotfix/runtime-tmdb-credentialless-v28` deleted, PR #92 closed and never merged.
- Current expected branches after cleanup: `main` + `brain-learning/proposals` only.
- Catalogue target remains **all 96 Provider Objects**, including disabled/off rows for census/recoverability. Never shrink the catalogue to manufacture green metrics.
- Do not patch official NuvioTV/NuvioMobile/NuvioDesktop production behavior to make Labs green. Native Labs are observational.

## Accepted publication — 5.21.35

- Final accepted/published generation: **5.21.35**.
- Final publication commit: `9db07b3aa42ce2535ec1d7c19866beb43586badd` — `fix: restore Provider CONFIG in final publication 5.21.35`.
- Publication trigger commit: `96957c79403908028964aaab388bdb4c80a5bbe2`.
- Workflow `MAIN - Provider CONFIG Publication Hotfix`, run **34061529965**, job **101562800243**, completed success.
- Root `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` were all verified as `5.21.35`.
- 96 provider versions/hashes were regenerated. Final Provider CONFIG validation passed 96/96.
- The temporary publication workflow/script self-removed from final main as intended.
- Flemmix authoritative domain is `flemmix.kim`; `.men` is stale. Commit `bdf11932ea5b949837c29b71c8a61b903e91c57b` fixed the final DATA audit to rebuild expected CONFIG from current structured sources instead of treating the earlier materialization DATA hash as final authority.
- A green 96/96 structural/materialization audit is **not** proof that 96 providers return playable streams. Real route/network/yield/native evidence remains mandatory.

## Provider v3 architecture — invariant

Generated provider composition:
1. clean immutable ProviderBase v3;
2. structured provider DATA/static knowledge;
3. provider-owned `PROVIDER.*` Lego;
4. one global Core boundary;
5. shared `CORE.*` Lego;
6. conservative NiakVIO minimizer + content hash.

Hard rules:
- published/upstream/historical Provider JS is knowledge/reference only, never a reconstruction seed;
- ProviderBase remains clean/DATA-free;
- provider behavior belongs in DATA or owned Provider Lego;
- Core remains provider-agnostic;
- managed Lego uses `STARTFIX` / `CLOSEFIX` (+ `FIXDATA` when needed);
- Provider Lego precedes Core boundary, Core Lego follows it;
- reverse reconstruction must be deterministic/byte-verifiable;
- Terser forbidden; only `scripts/provider_v3_minimizer.py` production minimizer policy;
- minimizer must preserve comments/markers/structure and never arbitrary-rewrite semantics.

Current conceptual Core order:
`Provider -> STREAM_FACTS -> STREAM_IDENTITY -> MEDIA_TYPE -> STREAM_PRESENTATION -> PROVIDER_BRANDING -> SANITIZER`.

## Identity / type / TV-year contract

- Provider input accepts **TMDB or IMDb**. Valid IMDb must never be rejected merely because TMDB enrichment is missing/unavailable.
- Episodic IMDb input such as `tt11198330:3:1` preserves season/episode.
- Canonical semantic types: `movie`, `tv`, `anime`.
- Nuvio transport alias `series` maps to canonical `tv`; `series` belongs in transport `supportedTypes`, never canonical semantic capability.
- Capability/type gate must happen before provider network work.
- Anime semantics stay distinct even when transport aliases expose TV/movie launch lanes.

Canonical year behavior:
- MOVIE: title + type + movie year; year mismatch is strong evidence and may reject in strict mode.
- TV: title + media type primary; `seriesYear` = original series year, `seasonYear` = season/episode year secondary evidence; **neither year may hard-reject TV by itself**.
- Episode resolution uses season + episode. A provider result such as `House of the Dragon - Saison 3 (2026)` must not be rejected because the series origin year is 2022.
- Current shared TV soft-year contract is already implemented/tested; the 2026-09-07 Desktop HOTD failure below occurs **after** identity/series transport selection, so do not regress into an artificial year exception.

## Stream/player integrity

A URL or `#EXTM3U` response is not native playback proof. Keep separate:
1. extraction;
2. work/episode identity;
3. request context/headers;
4. playlist/variant resolution;
5. media/container integrity;
6. official native player outcome.

Shared terminal sanitizer:
- `CORE.STREAM_SANITIZER.V6` is global and fail-closed on `probe_all_urls=true`.
- Global policy uses direct-media/all-URL probing and `min_vod_duration_seconds=60`.
- `tests/global_stream_output_guard_test.py` explicitly walks the 96 current manifest providers and requires one V6 managed sanitizer, current fail-closed hook, `probeAllUrls=true`, and terminal ordering.
- `tests/stream_output_sanitizer_fail_closed_test.py` executes the fail-closed behavior.
- Historical Allwish ~20 s *Interstellar* result is a generic stream-level regression case, not a reason to disable/re-add a catalogue provider. Allwish is not in the current 5.21.35 manifest.
- Kehflix malformed MPEG-TS handling probes first media bytes when the runtime exposes them; on bridges without byte access, lack of proof remains unknown rather than a fake provider-wide failure.
- HLS audio-child integrity (`CORE.HLS_RUNTIME_INTEGRITY.V1`) must remain intact.

## Five first-class Native Labs

Exactly five proofs:
1. TV Android — NuvioTV;
2. Mobile Android — NuvioMobile;
3. Mobile iOS — NuvioMobile;
4. Desktop macOS — NuvioDesktop;
5. Desktop Windows — NuvioDesktop.

Current workflow mapping: three workflows cover the five platforms: Android matrix = TV + Mobile Android; Desktop matrix = macOS + Windows; iOS separate.

Runtime audit refs before final Labs:
- NuvioMobile audited/current: `68337ffac8578b986d0c3f6e432abf75f4a33521`.
- NuvioTV audited/current: `23d1fe478e380860dae3eb41c8770533361a0cc5`.
- NuvioDesktop last audited runtime-contract ref: `323c1037f3c0fbe0ebe255b77d42331c3fdeb2d7`.
- Desktop upstream advanced to `21aabeeb49fc6de835f9031a65cc5f8489419330`, but compare showed only player-shortcut/UI files (`PlayerEngine.kt`, `PlayerScreenRuntimeUi.kt`, `NativePlayerController.kt`, `controls.js`), not provider/plugin runtime contract files.

Native application-path tests must cover `movie`, `tv`, and `series`. Main has the stronger `series=0` blocking gate; do not restore the older workbench movie/tv-only version.

## Security state

- Exact final publication SHA Default Setup CodeQL run: **34061759678**.
- Python analysis: success.
- GitHub Actions analysis: success.
- JavaScript/TypeScript analysis was still `in_progress` at the latest poll before this checkpoint; no failure conclusion yet.
- NiakVIO security completion also requires the repository `SEC - CodeQL` (`security-extended`) + `npm audit --omit=dev --audit-level=high`; Default Setup alone is not the whole proof.
- Direct code-scanning-alert enumeration is not exposed by the current connector. Never claim historical UI alerts were individually closed without actual evidence.
- Do not weaken CodeQL/security rules for green CI.

## Repository/documentation debts discovered after 5.21.35

These are pending unless a later checkpoint says fixed:
- `CHANGELOG.md` head still stops at 5.21.16 while current release is 5.21.35.
- `VALIDATION.json` still reports `release: 5.15.0`; field appears to be metadata, not a reconstruction baseline. It should be synchronized to current manifest and covered by a consistency test.
- README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md`, and the Domain Refresh script docstring still describe Domain Refresh as `official_site`-only, contradicting current structured-domain reconciliation.
- `ARCHITECTURE.docx` exists on main but should be regenerated/rechecked after the final architecture wording is corrected.
- `.github/triggers/nuvio-client-lab.json` still carries stale `5.21.32` and frozen route counters (`228/96/92/40`) even though the test contract says route totals must be derived from the current manifest. Remove frozen totals rather than updating another duplicate truth.
- `automation/provider-v3-architecture.json` and architecture/workflow ownership tests still encode an older branch-based reconstruction publication contract. Desired durable model: reconstruct/materialize/version/integrity in one workspace, CAS-verify `origin/main == base_sha`, then one atomic main publication commit. No persistent workbench branch.

## Domain Refresh — diagnosed systemic defects (NOT YET FIXED at this checkpoint)

Current source authority `refresh_authoritative_hub_domains.py` already tries to reconcile terminal-domain derivatives in `provider-overrides.json`, including domain substitution/replacement maps, provider-owned manifest logo/icon/favicon URLs, and notes.

But the transaction is internally inconsistent:
1. `validate_domain_refresh_scope.py` / tests still enforce old `official_site`-only mutation and can reject the derivatives the refresh itself changes.
2. `update_provider_v3_domain_config.py` currently decodes CONFIG and only does `next_data["officialSite"] = site`; it does **not** deterministically rebuild full current CONFIG via the same `provider_model() -> build_provider_data_model()` source path used by full materialization. Therefore `domainSubstitutions` can remain stale in published runtime CONFIG after a domain rotation.
3. That updater emits old-style filenames `providers/{id}-{hash}.js`, while final 5.21.35 audit requires source-qualified publication filenames. A future changed-domain transaction can therefore fail final audit even when the bytes are otherwise valid.
4. Manifest logo/icon/favicon reconciliation currently needs a real synthetic old-host -> new-host transition test; Flemmix already being `.kim` does not prove the generic algorithm.

Required fix is atomic: source authority + allowed scope gate + full CONFIG projection + source-qualified filename preservation + synthetic A->B tests + machine policy/docs. ProviderBase/Core bytes must remain unchanged for domain-only updates.

## 2026-09-07 — User Desktop test: House of the Dragon S3E1 returns zero visible streams

User supplied Desktop log `nuvio-ux-20260907-001220.log` while testing published 5.21.35.

Observed chain:
- Metadata resolves correctly: IMDb `tt11198330`, TMDB `94997`, `type=series`, title `House of the Dragon`, 26 videos.
- Requested stream identity reaches the stream stage exactly as **`type=series id=tt11198330:3:1`**.
- Log line: `StreamsRepo Found 0 addons for stream type=series id=tt11198330:3:1`. This is the ordinary addon list, **not** proof that zero NiakVIO Provider JS ran: PluginRuntime network calls follow immediately.
- Therefore the S3E1 failure is **after** metadata/transport identity and is not evidence for a hard TV year rejection.

Provider/runtime requests visible immediately after the S3E1 request:
- YFlix family (`1moviesz.to`): `GET https://1moviesz.to/api?#` and root `/?#` -> `UnknownHostException`.
- Nakios (`api.nakios.live`): tries both `/api/sources/movie/94997?#` and `/api/sources/tv/94997/3/1?#` -> `UnknownHostException`.
- Peachify (`uwu.eat-peach.sbs`, `usa.eat-peach.sbs`): `net/tv/94997/3/1`, `moviebox/tv/94997/3/1`, `air/tv/94997/3/1`, `multi/tv/94997/3/1`, `holly/tv/94997/3/1` -> all `UnknownHostException`.
- VidLink (`vidlink.pro`): `/api?#`, `/api/b/movie/?#`, `/api/b/tv/?#`, root `/?#` -> `UnknownHostException`.

Interpretation / next correction priority:
- NuvioDesktop is executing NiakVIO providers and season/episode reaches provider URL building.
- No successful extraction is visible for this fixture because every visible provider host in this path fails DNS.
- Several generated URLs also contain suspicious placeholder fragments `?#`, and movie-shaped attempts for a series (Nakios movie route, VidLink movie route). These must be audited at Source Plan v4 / provider DATA level, not patched as a HOTD exception.
- Priority is to map every attempted URL back to its provider DATA/route plan, test current authoritative hub/domain live where possible, repair stale domain/route DATA generically, and ensure TV-capable providers receive canonical TV + S3/E1 without movie fallback unless the provider protocol explicitly requires such fallback.
- Real-route discovery must test the route live at discovery time; never store an invented/unverified endpoint as “real”.
- The user still sees **no streams** for HOTD S3E1 on current 5.21.35 Desktop. Do not call TV/series fixed until this exact fixture returns provider evidence/playable streams in a real client test.

## Active completion sequence after this checkpoint

1. Diagnose/fix HOTD S3E1 route/domain/source-plan failures generically across all 96, starting with the concrete YFlix/Nakios/Peachify/VidLink evidence above; do not special-case HOTD.
2. Run real provider/route probes for the affected route families and update DATA only from observed/authoritative evidence.
3. Fix the Domain Refresh transaction defects so future domain rotations correctly project full CONFIG and preserve final filename contract.
4. Re-materialize/reverse/minimize only as required by actual provider DATA/Core changes; if published provider bytes change, finalize a new synchronized release after validation.
5. Re-run exact HOTD S3E1 Desktop test and representative movie/anime fixtures; confirm visible streams and player behavior, not merely structural green.
6. Run complete five Native Labs on one exact candidate SHA.
7. Finish `CORE - Workflow Gate`, `SEC - CodeQL`, `SEC - Final Gate`, dependency audit, Default Setup evidence on the final exact SHA.
8. Clean docs/machine architecture contracts/trigger metadata and regenerate `ARCHITECTURE.docx`.
9. Final branch/PR hygiene audit and final `MEMORY.md` checkpoint with exact SHA/run/artifact IDs.

## Completion principle

A green structural workflow is not proof that the 96 providers work. A native client failure is not automatically a provider failure. Keep identity, route/network, extraction, sanitizer, and player evidence separate; fix common NiakVIO-owned root causes at their owning layer; never delete providers, weaken validation, invent routes, or patch official clients to manufacture success.
