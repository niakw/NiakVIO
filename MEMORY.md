# NiakVIO — Recovery Memory

Last authoritative checkpoint: 2026-09-07 01:06 Europe/Paris.

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
1. clean immutable/common ProviderBase v3;
2. structured provider DATA/CONFIG/static knowledge;
3. provider-owned `PROVIDER.*` Lego;
4. one global Core boundary;
5. shared `CORE.*` Lego;
6. conservative NiakVIO minimizer + content hash.

Hard rules:
- published/upstream/historical Provider JS is knowledge/reference only, never a reconstruction seed;
- **published Provider JS must contain only common ProviderBase + structured DATA/CONFIG + managed Provider/Core Lego + envelope/minimizer-preserved structure**;
- no provider file/adapter may own duplicated identity, media-type, year, sanitizer, presentation or other shared business rules;
- functions such as `strictIdentityScore`, `routeIdentity`, provider-local year rejection or duplicated season/episode identity logic are architecture violations unless they are merely thin calls into the unique owning Core Lego and should preferably be removed entirely;
- ProviderBase remains common/DATA-free; it may call shared Core services but must not own a second copy of Core policy;
- provider behavior belongs in DATA or owned Provider Lego;
- Core remains provider-agnostic and each concern has a single owner;
- managed Lego uses `STARTFIX` / `CLOSEFIX` (+ `FIXDATA` when needed);
- Provider Lego precedes Core boundary, Core Lego follows it;
- reverse reconstruction must be deterministic/byte-verifiable;
- Terser forbidden; only `scripts/provider_v3_minimizer.py` production minimizer policy;
- minimizer must preserve comments/markers/structure and never arbitrary-rewrite semantics.

Current conceptual Core order:
`Provider -> STREAM_FACTS -> STREAM_IDENTITY -> MEDIA_TYPE -> STREAM_PRESENTATION -> PROVIDER_BRANDING -> SANITIZER`.

Ownership rule clarified 2026-09-07:
- `CORE.STREAM_IDENTITY.V1` is the **sole owner** of title/type/ID/year/season/episode identity acceptance semantics.
- `CORE.RUNTIME_MEDIA_SAFETY.V4` may own only playback/media safety (URL shape, P2P rejection, HLS/direct checks, bounded duration/playability). Any title/year/season/episode collision logic in it must be removed or delegated to `CORE.STREAM_IDENTITY.V1`.
- `engine_v2` smoke/diagnostic code may mirror the Core policy for tests but must not expose provider-specific scoring APIs. Purstream's old `strictIdentityScore()` export is being removed; adapter calls must use the shared engine mirror directly.
- Add an architecture test that fails if provider/adapter files define local identity scoring/rejection helpers.

## Identity / type / episodic-year contract

- Provider input accepts **TMDB or IMDb**. Valid IMDb must never be rejected merely because TMDB enrichment is missing/unavailable.
- Episodic IMDb input such as `tt11198330:3:1` preserves season/episode.
- Canonical semantic types: `movie`, `tv`, `anime`.
- Nuvio transport alias `series` maps to canonical `tv`; `series` belongs in transport `supportedTypes`, never canonical semantic capability.
- Capability/type gate must happen before provider network work.
- Anime semantics stay distinct even when transport aliases expose TV/movie launch lanes.

Canonical year behavior — FINAL:
- **MOVIE only**: title + type + movie year; year mismatch is strong evidence and may reject in strict mode.
- **TV / `series` / anime**: release/origin/season year is **not part of identity acceptance at all**. Do not reject or score-match episodic content from year.
- Episode resolution identity is title/type plus **season + episode**; provider catalogue rows may expose original-series year, season year, episode year, or none without affecting episodic acceptance.
- A provider result such as `House of the Dragon - Saison 3 (2026)` must be accepted against TMDB series origin 2022 if title/type/S3E1 are correct.
- 2026-09-07 audit refinement: `CORE.STREAM_IDENTITY.V1::contentLike()` still used the mere presence of a 4-digit year as an indirect signal that a candidate looked content-like. Even though no TV year value was compared, this could indirectly change whether a TV/series/anime row entered contradiction analysis. This violates the final zero-year episodic contract. Before 5.21.36 publication, year-based `contentLike` promotion must be gated to **non-episodic/movie only**, so year is completely inert for tv/series/anime, including heuristics.

Corrections already committed after 5.21.35:
- `1723472`: introduced ProviderBase runtime v9 migration for episodic-year removal.
- `5b356ce`: `CORE.STREAM_IDENTITY.V1` gained shared catalogue identity API and final `movie-only` year policy.
- `3600e8b`: ProviderBase v9 changed from owning `_recipeScore`/HTML year semantics to delegating catalogue/HTML identity to `globalThis.__nuvioIdentityPolicyV1` from `CORE.STREAM_IDENTITY.V1`.
- `491f1ba`: added executable Core ownership regression: HOTD-like TV/series/anime year mismatch passes, same mismatch in movie fails; ProviderBase must not retain local `Math.abs(year...)` policy.
- `25e5148`: Workflow Gate runs the Core identity ownership regression.
- `f62393a` + `fb76b5c` + `c1d8c43`: engine_v2 shared catalogue policy + Purstream HOTD S3E1 synthetic smoke; TV metadata year 2022 vs provider row 2026 must still resolve S3E1.
- `398024c`: priority regression updated from old “TV-year-soft” wording to **episodic year disabled / movie year only**.
- `ef4073a`: ProviderBase store provenance now reports reader v9 instead of stale v5 metadata.
- `a934df3`: added one-shot Core identity ownership cleanup transaction source.
- `c8bc366`: added active-96 Provider JS Lego ownership test.
- `1d3a415`: added one-shot identity-only ProviderBase materializer with `route_or_domain_mutation=false`.
- `d0824a8`: added Kehflix-shaped final-row episodic identity runtime regression.
- `8e14b54`: triggered first 5.21.36 Core identity publication workflow.
- `940e1ef`: triggered retry workflow after first safe failure.

Publication attempt state:
- First Core identity publication run **34065556338**, job **101573573889**, failed safely at step `Apply single-owner identity architecture cleanup`, before any materialization/version bump/push.
- Exact first failure: `AssertionError: Purstream rank identity call count=2`. The one-shot migration expected one `strictIdentityScore(item, metadata, targetType)` occurrence but the old adapter has exactly two: one rank call + the local function definition that the migration intends to delete. No published bytes changed.
- Retry workflow run **34065727473**, job **101574024846**, was still queued at this checkpoint. Retry logic expects exactly two occurrences, replaces only the first call with the shared helper, then deletes the local function definition. The full 96/96 transaction still must pass before any 5.21.36 push.
- Because the indirect `contentLike()` year heuristic was discovered while the retry remained queued, the final 5.21.36 must also make episodic year completely inert before publication. Do not tell the user to test until this is included and the public manifest is verified.

Pending before next publication:
- remove Purstream's now-redundant exported `strictIdentityScore()` wrapper and update its tests/contracts to call shared engine policy directly;
- remove duplicated identity/collision logic from `CORE.RUNTIME_MEDIA_SAFETY.V4` (`identityBlob`, `explicitYears`, `containsAny`, `routeIdentity`, collision fixtures, season/episode/year rejection) and leave only media/playback safety there;
- clean `identityInput.requiredFields` so generic catalogue DATA does not encode `year` as universally required for episodic requests;
- make `contentLike()` year signal movie-only so episodic year has zero direct or indirect identity effect;
- enforce repository-wide architecture test forbidding provider-local identity scoring/rejection implementations;
- rematerialize 96 ProviderBase/bundles, reverse/audit/integrity, then bump synchronized manifest (expected 5.21.36 if no intervening release).

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
- Therefore the S3E1 failure is after metadata/transport identity; current cleanup focuses first on shared architecture/identity ownership before the separate route census.

Provider/runtime requests visible immediately after the S3E1 request:
- YFlix family (`1moviesz.to`): `GET https://1moviesz.to/api?#` and root `/?#` -> `UnknownHostException`.
- Nakios (`api.nakios.live`): tries both `/api/sources/movie/94997?#` and `/api/sources/tv/94997/3/1?#` -> `UnknownHostException`.
- Peachify (`uwu.eat-peach.sbs`, `usa.eat-peach.sbs`): `net/tv/94997/3/1`, `moviebox/tv/94997/3/1`, `air/tv/94997/3/1`, `multi/tv/94997/3/1`, `holly/tv/94997/3/1` -> all `UnknownHostException`.
- VidLink (`vidlink.pro`): `/api?#`, `/api/b/movie/?#`, `/api/b/tv/?#`, root `/?#` -> `UnknownHostException`.

Current priority clarified by user:
- do **not** start a full remaining-route/domain sweep yet;
- first finish common architecture/runtime tasks and make already-viable TV-capable providers such as **Purstream, Kehflix and others** work correctly for `series/tv`;
- route census/repair of remaining dead providers comes later.

## Active completion sequence after this checkpoint

1. Finish Core ownership cleanup: no provider/adapter-local identity policy; remove identity logic from runtime media safety; clean DATA required-fields contract; make episodic year completely inert including `contentLike()` heuristics.
2. Run synthetic Purstream HOTD S3E1 and representative Kehflix/TV contract tests plus Workflow Gate.
3. Materialize current ProviderBase v9 + current DATA + Provider Lego + Core Lego across all 96; reverse/audit/minimizer/integrity.
4. Publish synchronized next manifest (expected 5.21.36) only after the actual bundles contain the fix; then tell user to retest HOTD S3E1.
5. Re-test real Desktop HOTD S3E1; separate provider-route/network failures from common runtime failures.
6. Only after common TV/series/runtime architecture is stable, resume full real-route/domain recovery across all 96.
7. Fix Domain Refresh transaction defects.
8. Run complete five Native Labs on one exact final candidate SHA.
9. Finish Workflow Gate/security/dependency/CodeQL proof on final SHA.
10. Clean docs/machine architecture contracts/trigger metadata and regenerate `ARCHITECTURE.docx`.
11. Final branch/PR hygiene audit and final `MEMORY.md` checkpoint with exact SHA/run/artifact IDs.

## Completion principle

A green structural workflow is not proof that the 96 providers work. A native client failure is not automatically a provider failure. Keep identity, route/network, extraction, sanitizer, and player evidence separate; fix common NiakVIO-owned root causes at their owning layer; never delete providers, weaken validation, invent routes, or patch official clients to manufacture success.