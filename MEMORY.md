# NiakVIO — Recovery Memory

Last authoritative checkpoint: 2026-09-07 Europe/Paris.

This file is the durable recovery source of truth for the active NiakVIO work. Prefer current repository state and exact GitHub Actions/native logs over older chat summaries. Update this file automatically at every important correction, failure, publication, native proof, security proof, or architecture decision before moving to the next risky step.

## Repository topology / execution policy

- Repository: `niakw/NiakVIO`.
- **`main` is the only active write/publication target.** Do not recreate a persistent workbench branch.
- Durable Learning proposal branch: `brain-learning/proposals`; proposal storage only, not publication authority.
- Cleanup completed after 5.21.35 publication: `workbench` deleted, `hotfix/runtime-tmdb-credentialless-v28` deleted, PR #92 closed and never merged.
- Expected branches: `main` + `brain-learning/proposals` only.
- Catalogue target remains **all 96 Provider Objects**, including disabled/off rows for census/recoverability. Never shrink the catalogue to manufacture green metrics.
- A structural/materialization green is not real stream proof. Real route/network/yield/native evidence remains mandatory.
- Do not patch official NuvioTV/NuvioMobile/NuvioDesktop production behavior to make Labs green. Native Labs are observational.

## Accepted publication — 5.21.35

- Current accepted public generation remains **5.21.35** until a later checkpoint explicitly records a verified public 5.21.36.
- Final 5.21.35 publication commit: `9db07b3aa42ce2535ec1d7c19866beb43586badd` — `fix: restore Provider CONFIG in final publication 5.21.35`.
- Publication trigger commit: `96957c79403908028964aaab388bdb4c80a5bbe2`.
- Workflow `MAIN - Provider CONFIG Publication Hotfix`, run **34061529965**, job **101562800243**, completed success.
- Root `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` were all verified as `5.21.35`.
- 96 provider versions/hashes were regenerated and Provider CONFIG validation passed 96/96.
- Temporary 5.21.35 publication workflow/script self-removed as intended.
- Flemmix authoritative domain is `flemmix.kim`; `.men` is stale. Commit `bdf11932ea5b949837c29b71c8a61b903e91c57b` fixed final DATA audit authority.

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
- **published Provider JS contains only common ProviderBase + structured DATA/CONFIG + managed Provider/Core Lego + envelope/minimizer-preserved structure**;
- no provider file/adapter may own duplicated identity, media-type, year, sanitizer, presentation, or other shared business rules;
- provider-local `strictIdentityScore`, `routeIdentity`, year rejection, or duplicated season/episode identity logic are architecture violations;
- ProviderBase may transport evidence and call shared Core services but must not own a second copy of Core policy;
- provider behavior belongs in DATA or owned Provider Lego;
- Core is provider-agnostic and each concern has one owner;
- managed Lego uses `STARTFIX` / `CLOSEFIX` (+ `FIXDATA` when needed);
- Provider Lego precedes Core boundary; Core Lego follows it;
- reverse reconstruction must be deterministic/byte-verifiable;
- Terser forbidden; production minimizer is `scripts/provider_v3_minimizer.py` and must preserve comments/markers/structure.

Core order:
`Provider -> STREAM_FACTS -> STREAM_IDENTITY -> MEDIA_TYPE -> STREAM_PRESENTATION -> PROVIDER_BRANDING -> SANITIZER`.

Ownership:
- `CORE.STREAM_IDENTITY.V1` is the **sole owner** of title/type/ID/year/season/episode identity acceptance semantics.
- `CORE.RUNTIME_MEDIA_SAFETY.V4` owns only playback/media safety: URL shape, P2P rejection, HLS/direct checks, bounded duration/playability. It must not own title/year/S/E collision policy.
- `engine_v2` may mirror Core policy for smoke/diagnostic tests, but provider-specific scoring APIs are forbidden.

## Identity / type / episodic-year contract — FINAL

- Provider input accepts **TMDB or IMDb**. Valid IMDb must not be rejected merely because TMDB enrichment is missing/unavailable.
- Episodic IMDb such as `tt11198330:3:1` preserves season/episode.
- Canonical semantic types: `movie`, `tv`, `anime`.
- Nuvio transport alias `series` maps to canonical `tv`; app-path tests cover movie/tv/series.
- Anime semantics remain distinct even when a provider uses a tv/movie transport lane.
- Capability/type gate must happen before provider network work.

Year policy:
- **MOVIE only**: title + type + movie year; year mismatch is strong evidence and may reject in strict mode.
- **TV / `series` / anime**: release/origin/season/episode year has **zero identity influence**, direct or indirect. No rejection, score promotion, `contentLike` promotion, or other heuristic may depend on year for episodic media.
- Episode resolution identity uses title/type + **season + episode**.
- Provider rows may expose original-series year, season year, episode year, or no year without affecting episodic acceptance.
- `House of the Dragon - Saison 3 (2026)` must be accepted against TMDB series origin 2022 when title/type/S3E1 are correct.

## Core identity 5.21.36 work — implemented source changes

Important commits after 5.21.35 include:
- `1723472`: ProviderBase runtime v9 migration introduced for episodic-year removal.
- `5b356ce`: `CORE.STREAM_IDENTITY.V1` shared catalogue identity API + movie-only year policy.
- `3600e8b`: ProviderBase delegates catalogue/HTML identity to `globalThis.__nuvioIdentityPolicyV1`.
- `491f1ba`: executable Core ownership regression for HOTD-like episodic year mismatch + strict movie year.
- `25e5148`: Workflow Gate includes identity ownership regression.
- `f62393a`, `fb76b5c`, `c1d8c43`: shared engine-v2 catalogue policy + Purstream HOTD S3E1 synthetic smoke.
- `398024c`: priority regression wording/contract changed to episodic-year-disabled/movie-only.
- `ef4073a`: ProviderBase provenance reports runtime reader v9.
- `a934df3`: one-shot Core identity ownership cleanup transaction.
- `c8bc366`: active-96 Provider JS Lego ownership test.
- `1d3a415`: identity-only ProviderBase materializer with `route_or_domain_mutation=false`.
- `d0824a8`: Kehflix-shaped final-row runtime regression: HOTD S03E01 survives, S03E02 rejects, movie year mismatch rejects.
- `9003a84`: MEMORY checkpoint recording the discovery that episodic year still indirectly influenced `contentLike()`.
- `c9e10ce`: migration strengthened to zero-year episodic identity v10; year cannot promote `contentLike()` for episodic requests.
- `8176123`: regression proves tv/series/anime produce the same decision with or without year.
- `a6f1b4bd`: authoritative retry workflow updated for v10.
- `ec8867c` + `7296e20`: Python test bootstraps fixed for direct Core Lego imports.
- `af73c025`: ownership test now inspects transformed ProviderBase snippets, not legacy source-anchor strings inside the migration tool.
- `c50806c`: Purstream contract accepts absent or empty `patch_scripts` as the same clean state; any non-empty legacy patch list remains forbidden.
- `05cce19c`: Purstream test aligned with real transport DATA: `published_types=[movie,tv]`, anime preserved semantically via `request_type_aliases={anime:tmdb_namespace}`.
- `e6ea30b`: Purstream recipe contract aligned with current DATA: `movieRoute=/stream/{id}`, `episodeRoute=/stream/{id}/episode?...`, `yearFields=[release_date]`; no `first_air_date` requirement for episodic identity.

## 5.21.36 publication attempts — exact state

**5.21.36 is NOT published at this checkpoint. Public manifest is still treated as 5.21.35.**

Workflow/run authority:
- Workflow: `MAIN - Core Identity Publication Retry 2`.
- Run: **34066073913**.

Earlier safe attempts:
- Run **34065556338**, job **101573573889**: failed before materialization because the one-shot Purstream migration expected one `strictIdentityScore(item, metadata, targetType)` occurrence but correctly found two (call + local definition). No publish.
- Retry run **34065727473**, job **101574024846**: cancelled/superseded before publication when zero-year v10 became authoritative.

Run 34066073913 progression:
- Initial job **101574939364**: migration and DATA scope passed; smoke failed only because `global_identity_policy_ownership_test.py` did not add `scripts/` to `sys.path`. No materialization/publish.
- Rerun job **101575336306**: bootstrap fixed; next failure was a test false-positive scanning `upgrade_provider_base_runtime_v5.py` source text and seeing the legacy validation literal `const movieIdentity...`. Runtime was not at fault. Fixed by inspecting only transformed ProviderBase snippets.
- Rerun job **101575867355**: **all smoke contracts passed**. Identity-only ProviderBase rematerialization itself passed **96/96**, then old Purstream contract failed because `patch_scripts` was omitted (`None`) rather than `[]`.
- Rerun job **101576053245**: all smoke contracts passed; ProviderBase rematerialization again passed **96/96**; old Purstream contract then failed because it expected `published_types=[movie,tv,anime]` instead of real `movie,tv` transport + semantic anime alias.
- Rerun job **101576310737**: all smoke contracts passed; ProviderBase rematerialization again passed **96/96**; old Purstream contract then failed because it expected historical `movieRoute=/media/{id}/sheet`. Current authoritative DATA says `/stream/{id}` and `yearFields=[release_date]`.

Repeated verified rematerialization line:
`IDENTITY_ONLY_PROVIDER_BASE_OK providers=96 unique_paths=96 common_digest=520ba9882661582dc4789f65e5d04c3c902fa22f79b1f436dc52823d845dd3fc runtime_reader=v9 route_or_domain_mutation=false`

Repeated smoke proof before the stale-contract blockers:
- global identity policy ownership: pass;
- Kehflix-shaped episodic identity runtime: pass;
- episodic zero-year regression: pass;
- engine-v2 Purstream adapter: pass;
- runtime media safety: pass;
- priority episodic-year-disabled/domain refresh regression: pass;
- native HLS integrity budget: pass;
- native provider loading compatibility: pass;
- global media resolver: pass;
- native dual IMDb/TMDB identity: pass;
- Provider v3 source plan v4 contract: pass.

The remaining transaction still must execute, on one successful run:
1. complete post-materialization Purstream contract;
2. recompose **all 96 active bundles** from common Base + existing DATA/CONFIG + Provider/Core Lego;
3. validate active-96 ownership and stream guards;
4. generate projections and synchronize release to **5.21.36**, bumping all 96 changed providers;
5. final reverse/static/ownership/integrity/fixed-point proof;
6. write final publication checkpoint to this file;
7. CAS-check `origin/main == base_sha` and atomically push publication;
8. verify public root/vf/no-anime/vf-no-anime manifests actually report 5.21.36 before telling the user to retest.

## Purstream current authoritative DATA relevant to this migration

- `published_types`: `movie`, `tv`.
- semantic anime request: capability alias `anime -> tmdb_namespace`, identity source `original_nuvio_request`.
- official site: `https://purstream.ad`.
- official API: `https://purstream.ad/api`.
- search route: `/search-bar/search/{query}`.
- movie stream route: `/stream/{id}`.
- episode stream route: `/stream/{id}/episode?season={season}&episode={episode}`.
- recipe `yearFields`: `release_date` only, used as movie catalogue evidence; episodic identity ignores year entirely.
- `strictIdentity=true`, `directSourcesOnly=true`.
- No provider-local identity algorithm is allowed; Core owns the semantics.

## Stream/player integrity

A URL or `#EXTM3U` response is not native playback proof. Keep separate:
1. extraction;
2. work/episode identity;
3. request context/headers;
4. playlist/variant resolution;
5. media/container integrity;
6. official native player outcome.

- `CORE.STREAM_SANITIZER.V6` is global and fail-closed on `probe_all_urls=true`.
- `tests/global_stream_output_guard_test.py` walks the 96 current manifest providers and requires one V6 managed sanitizer and terminal ordering.
- `tests/stream_output_sanitizer_fail_closed_test.py` executes fail-closed behavior.
- Historical Allwish ~20 s Interstellar result is a stream-level regression, not a reason to disable a provider. Allwish is not in current 5.21.35 manifest.
- Kehflix malformed MPEG-TS handling probes first media bytes when the runtime exposes them; lack of bridge byte access remains unknown rather than a fake provider-wide failure.
- HLS audio-child integrity `CORE.HLS_RUNTIME_INTEGRITY.V1` remains required.

## Five first-class Native Labs

Exactly five proofs:
1. TV Android — NuvioTV;
2. Mobile Android — NuvioMobile;
3. Mobile iOS — NuvioMobile;
4. Desktop macOS — NuvioDesktop;
5. Desktop Windows — NuvioDesktop.

Workflow mapping: Android matrix = TV + Mobile Android; Desktop matrix = macOS + Windows; iOS separate.

Runtime refs before final Labs:
- NuvioMobile audited/current: `68337ffac8578b986d0c3f6e432abf75f4a33521`.
- NuvioTV audited/current: `23d1fe478e380860dae3eb41c8770533361a0cc5`.
- NuvioDesktop last audited runtime-contract ref: `323c1037f3c0fbe0ebe255b77d42331c3fdeb2d7`.
- Desktop later advanced to `21aabeeb49fc6de835f9031a65cc5f8489419330`; compare showed player-shortcut/UI changes only, not provider/plugin runtime contract files.

## Security state

- Exact 5.21.35 publication SHA Default Setup CodeQL run: **34061759678**.
- Python analysis: success.
- GitHub Actions analysis: success.
- JavaScript/TypeScript was still pending at an older checkpoint; re-check final state rather than assuming.
- Final security completion also requires repository `SEC - CodeQL` / security-extended plus `npm audit --omit=dev --audit-level=high` on the final publication SHA.
- Direct code-scanning-alert enumeration is not exposed by current connector; never claim historical UI alerts were individually closed without evidence.
- Do not weaken CodeQL/security rules for green CI.

## Repository/documentation debts after runtime stabilization

Pending unless a later checkpoint says fixed:
- `CHANGELOG.md` was behind current release history.
- `VALIDATION.json` still carried stale release metadata.
- README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md`, and Domain Refresh docstring contained old official-site-only wording.
- `ARCHITECTURE.docx` must be regenerated/rechecked after final architecture wording.
- `.github/triggers/nuvio-client-lab.json` contained stale release/frozen route counters and should derive current truth instead.
- `automation/provider-v3-architecture.json` / ownership tests contained older branch-based publication assumptions; durable model is one workspace + CAS + atomic main commit.

## Domain Refresh — diagnosed, intentionally deferred until common runtime is stable

Current `refresh_authoritative_hub_domains.py` tries to reconcile terminal-domain derivatives, but the transaction has known inconsistencies:
1. scope validator/tests still encode old official-site-only mutation;
2. `update_provider_v3_domain_config.py` updates only `officialSite` instead of rebuilding full CONFIG from current structured source authority;
3. updater can emit old filename shape rather than source-qualified current publication shape;
4. generic old-host -> new-host logo/icon/favicon reconciliation still needs synthetic proof.

Required later fix: source authority + allowed scope gate + full CONFIG projection + source-qualified filename preservation + synthetic A->B tests + docs. ProviderBase/Core bytes must remain unchanged for domain-only updates.

## User Desktop HOTD S3E1 evidence on published 5.21.35

User supplied `nuvio-ux-20260907-001220.log`.

Observed chain:
- IMDb `tt11198330`, TMDB `94997`, type `series`, title `House of the Dragon` resolve correctly.
- Stream request reaches `type=series id=tt11198330:3:1`.
- `StreamsRepo Found 0 addons...` is ordinary addon-list state, not proof zero NiakVIO Provider JS ran; PluginRuntime network calls follow.
- Visible provider requests then include DNS failures for YFlix family, Nakios, Peachify and VidLink.
- Current priority is **not** a full route/domain sweep yet. First stabilize common TV/series/runtime architecture and already-viable providers such as Purstream/Kehflix; route census/repair across all 96 follows later.

## Active completion sequence

1. Finish 5.21.36 transaction through active 96-bundle recomposition, versioning, reverse/static/integrity and atomic publication.
2. Verify public 5.21.36 manifests and final active Provider JS ownership.
3. Have user re-test real Desktop HOTD S3E1; separate common-runtime results from route/network failures.
4. Stabilize any remaining common TV/series/player issues without narrowing provider scope.
5. Resume full real-route/domain recovery across **all 96**, testing routes live as they are discovered.
6. Fix Domain Refresh transaction defects.
7. Run complete five Native Labs on one exact final candidate SHA.
8. Finish Workflow Gate/security/dependency/CodeQL proof on final SHA.
9. Clean docs/machine architecture contracts/trigger metadata and regenerate `ARCHITECTURE.docx`.
10. Final branch/PR hygiene audit and final `MEMORY.md` checkpoint with exact SHA/run/artifact IDs.

## Completion principle

A green structural workflow is not proof that the 96 providers work. A native client failure is not automatically a provider failure. Keep identity, route/network, extraction, sanitizer, and player evidence separate; fix common NiakVIO-owned root causes at their owning layer; never delete providers, weaken validation, invent routes, or patch official clients to manufacture success.

## 2026-09-07 — Route reconstruction authority bug / proof-first redesign

- Critical architecture bug confirmed in `scripts/discover_candidates.py`: `infer_api_recipe()` can concatenate static route fragments (`search`, `stream`, `media`, `sheet`, `episode`) into executable `movieRoute`/`episodeRoute` templates without proving that the fragments form one real provider endpoint.
- `clean_provider_model()` also merges `patch.learned_routes`, `capability.routes`, and static `knowledge.routes` directly into executable `model.routes`; static observation therefore can leak into runtime Provider DATA before HTTP proof.
- `validate_provider_v3_routes_sequential.py` already contains the correct proof model in `derive_observed_route()`: start from an exact HTTP request observed while executing that provider, abstract only fixture values into placeholders, and refuse promotion when literal content/session/token residue remains.
- A second leak exists in sequential finalization: candidate `apiRecipe` is copied back to executable `apiRecipe` wholesale after route validation instead of filtering route fields by live proof.
- A third leak exists in `materialize_provider_v3_one.py`: `reconcile_provider_authority()` can copy `model.apiRecipe` back into `provider-overrides.api_recipe`, re-promoting stale/static recipe authority.
- `scripts/materialize_provider_v3_all.py::provider_model()` also merges static model routes/API recipe into the runtime model, so reconstruction must be changed to candidate-vs-executable separation.
- Final route model: **static/upstream/recognition data = candidate only; executable route/API recipe = provider-specific live HTTP proof only**. A route proof must preserve method, origin/base, route template, query/body fields, headers needed, semantic role/type, and evidence; static fragments never count as HTTP proof.
- `/stream/{id}` was NOT introduced by the current identity work. It was already in Purstream DATA on 5.21.35. Current Purstream engine adapter instead uses movie detail `/media/{id}/sheet` and episodic `/stream/{id}/episode?...`, exposing an existing route-authority inconsistency. Do not repair Purstream routes opportunistically inside the identity release; requalify them under the new proof-first route model.
- Next mandatory execution: patch reconstruction authority, reconcile all current routes to candidates, sequentially execute/requalify all 96 Provider Objects, persist only live-proven reusable routes, regenerate the 96 Provider v3 bundles from sanitized DATA, then run reverse/static/integrity proof before publication/testing.

## 2026-09-07 — Route-proof reconstruction/bootstrap architecture checkpoint

- User requires `MEMORY.md` to be updated automatically at each important architecture correction/failure/publication checkpoint without being reminded.
- Historical Provider JS route recovery uses the three original provider-source repositories: `Gowaru/gowaru-nuvio-providers`, `NuvioPlugin/All-in-One-Nuvio` (fallback `D3adlyRocket/All-in-One-Nuvio`), and `yoruix/nuvio-providers`. NuvioTV/NuvioMobile/NuvioDesktop are client validation repos only and are never route sources.
- `automation/provider-upstream-parity.json` currently maps **91/96** providers to an upstream source; five providers have no historical upstream mapping: `4khdhubnew`, `cinemm`, `goatapi`, `kehflix`, `toflix`.
- Last parity classification counted 19 `upstream_ok_niakvio_ko` providers, proving NiakVIO route/plan reconstruction regressed real upstream behavior for a nontrivial subset.
- Exact historical upstream bytes should be recovered from `upstream-lkg.json` using recorded provider URL + SHA-256 + capture time. If current raw bytes differ, search upstream Git history for the matching SHA. Current upstream is fallback; NiakVIO-native current source is only fallback for providers without usable upstream history.
- Static extraction is **candidate knowledge only**. It must never manufacture executable routes by concatenating fragments. The old `discover_candidates.py::infer_api_recipe()` / `clean_provider_model()` behavior that promoted static route fragments into runtime `routes/apiRecipe` is an architecture bug and is being replaced.
- Runtime route authority is proof-first **v5**: execute the Provider JS; capture exact sanitized HTTP request structure; capture bounded response identity hints; correlate later request values to prior provider responses; derive placeholders only from proven fixture/dataflow values; require successful provider HTTP evidence; then and only then promote executable DATA.
- `scripts/provider_route_proof.py` is the shared route-proof authority. It proves `search -> internal provider id -> later request` chains. A literal internal id such as `525` must never become `{id}` unless a previous provider response in the same trace proved that value.
- `scripts/bootstrap_provider_v3_routes.py` is the permanent bootstrap path for a **new empty provider**: input is provider source JS + provider id + supported semantic types; no prior `routes` or `apiRecipe` is required. It observes runtime HTTP and produces proof-v5 route DATA. `tests/provider_v3_empty_route_bootstrap_test.py` locks this zero-route onboarding contract.
- Difficult SPA/React/Next-like providers are not handled by guessed framework-specific routes. Runtime execution + network trace + response->request dataflow is the general fallback. Kehflix is explicitly one of the five NiakVIO-native/recent providers and historically accumulated many generic candidate routes, so it is a key proof case for this model.
- `scripts/upgrade_provider_worker_route_proof_v1.py` adds opt-in proof tracing to the hardened provider worker: exact sanitized URL, method, reproducible non-sensitive headers, body shape/values, content type, and bounded response id/slug hints. Existing health diagnostics remain separate.
- Request proof is not URL-only. `scripts/upgrade_provider_route_proof_request_spec_v1.py` abstracts request body/header fixture values (`{query}`, `{tmdbId}`, `{id}`, `{season}`, `{episode}`, `{media}`, `{year}` when merely transported) and rejects unresolved fixture/session residue.
- `scripts/upgrade_provider_base_route_requests_v1.py` teaches the **common ProviderBase** to replay structured `directRequest/searchRequest/movieRequest/episodeRequest` DATA including GET/POST/PUT/PATCH/DELETE, JSON/form body templates, and request headers. Provider-specific algorithms remain forbidden; request facts live in DATA.
- `scripts/recover_provider_routes_from_upstreams.py` is the 96-provider recovery/census harness. It uses upstream/LKG source where available, NiakVIO-native source for the five unmapped providers, runtime proof-v5, and produces a durable route recovery report.
- `scripts/upgrade_route_recovery_request_specs_v1.py` separates all HTTP-proven route observations from the subset safe for generic `routes[]` replay. POST/body/Referer/etc. requirements must not be lost merely because the URL was correct; complex calls belong in `routeData/apiRecipe` with request specs.
- `scripts/upgrade_provider_route_authority_v5.py` makes proof-v5 mandatory for runtime `routes/apiRecipe`: static discovery emits `candidateRoutes/candidateApiRecipe`; materialization only consumes executable routes when `route_proof_version >= 5` and recipe `proofModelVersion >= 5`; sequential finalization filters candidate recipes field-by-field against live routes instead of copying the candidate recipe wholesale.
- Generic catalogue preflight must no longer require `year`. Movie-year identity remains Core-owned; TV/series/anime year has zero identity influence.
- Provider JS architecture remains: common ProviderBase + structured DATA/CONFIG + PROVIDER.* Lego + CORE.* Lego. Reconstruction/discovery tooling is never embedded as provider-specific runtime business logic.
- Public release remains **5.21.35** until the new route-proof census + 96/96 reconstruction + reverse/audit/integrity + version sync are actually green and a later checkpoint records a verified bump.

## 2026-09-07 — Route-proof reconstruction run 34069211303 failure

- Workflow , run **34069211303**, job **101583333823**, failed safely in workspace before route census, DATA application, reconstruction or publication. Public release remained 5.21.35.
- Baseline freeze passed: 5.21.35 / 96 providers.
- , worker route-proof v1, request-spec proof v1 and ProviderBase runtime v9 all applied successfully before the failure.
- Failure was migration cardinality only:  assumed the legacy  call was unique for directRoute, but ProviderBase has exactly three stable call sites: directRoute, catalogue search, movie/episode resolve. It raised .
- No census was executed and no route result from this run is authoritative.
- Commit  fixes the upgrader to require cardinality exactly 3 then replace the three calls deterministically in stable semantic order.

## 2026-09-07 — Purstream HOTD S3E1 final proof requirement

- User explicitly requires a final **real Purstream → House of the Dragon S3E1** proof after the 96/96 route-proof reconstruction/audit. It must not be satisfied by the synthetic engine smoke alone.
- The final Purstream test must exercise the real provider/network path for HOTD S3E1, verify `tv`p/`series` transport and season=3/episode=1, and prove that the provider-side 2026 season year is not rejected against TMDB series origin 2022.
- Do not consider the next release publishable until this Purstream HOTD S3E1 check is green or is precisely classified as the remaining real-world blocker with evidence.

## 2026-09-07 — Route-proof reconstruction run 34069559315 failure

- Workflow , run **34069559315**, job **101584262866**, again failed safely before census/DATA application/reconstruction/publication. Public release remained 5.21.35.
- The previous ProviderBase request-spec cardinality bug was fixed:  passed.
- New blocker was another migration-anchor bug in : it searched exactly for  but  currently imports ; failure was .
- Commit  fixes this by injecting  before the stable  anchor and requiring that stable anchor exactly once.
- No provider route census result exists yet from runs 34069211303 or 34069559315; both failed before the live census step.
- Final candidate pipeline now includes a mandatory real Purstream / House of the Dragon S3E1 proof after reverse/static/integrity: both  and canonical  transports must return streams, have successful provider HTTP, and expose an observed episode request.


## TV runtime regression checkpoint — 2026-09-07

- User refreshed the current NiakVIO plugin on NuvioTV during route-proof work. Concrete native observation: Interstellar now returns streams from multiple providers; series/anime also return streams for some providers, but results can arrive much later after navigating away and appear to stack across works.
- This means series/anime are not globally broken. A major remaining systemic problem is stale provider work that keeps consuming the QuickJS/native fetch bridge after the user changes work.
- `CORE.MEDIA_TYPE_RESOLUTION.V1` currently has `requestSerial/requestToken` latest-result gating, but its `budgetedFetch()` is not bound to the invocation token. Superseded invocations can continue network/crawl work; because `global.fetch` is replaced by a later invocation wrapper, an older invocation may even execute later fetches under the newer request budget. Fix must be global/Core, never provider-specific.
- Required cancellation invariant: every provider invocation owns a request token; every wrapped fetch checks ownership before network and immediately after network; starting a newer invocation aborts the prior in-flight controller when supported; on runtimes where native bridge cancellation is not actually possible, the old in-flight call may finish but MUST NOT start any subsequent search/detail/player/crawl work or return output.
- Current platform contract says QuickJS clients expose AbortController/AbortSignal polyfills, but lifecycle teardown across already-entered native fetch remains not universally guaranteed. Therefore token gating remains mandatory even when abort is attempted.
- Native TV also exposed `Purstream - Inconnue` and `StreamZo - Inconnue`. Correct policy is NOT to discard quality blindly. `CORE.STREAM_FACTS`/`CORE.STREAM_PRESENTATION` must first recover a real quality from provider facts (`quality`, title/name/description, resolution/height, URL/manifest-derived facts). Only when no real quality can be recovered may the placeholder field (`Unknown`, `Inconnu`, `Inconnue`, `N/A`, null, etc.) be removed before terminal branding. Preserve real qualities such as 2160p/1080p/720p.
- Route-proof run #5 `34070914957`, job `101588047149`, materially progressed: migrations/proof-first tests/census/DATA apply/materialization reached green; candidate materialization was 96/96. The first failing post-materialization stage was prune/projection because `scripts/prune_unreferenced_providers.py` performs repeated per-file `git log --follow` calls while bootstrapping retention order and exceeded the bounded stage timeout. This is CI/tooling performance debt, not a provider runtime failure.
- Prune must be fixed by a batched Git-history scan/cache (single/bounded Git history traversal), preserving the rolling 10-generation retention semantics and all current/LKG/provenance/security protections; do not merely raise timeout.
- Final acceptance still requires rerun 96/96 -> reverse/static/integrity -> quick-yield -> real Purstream House of the Dragon TMDB 94997 S3E1 in both `series` and `tv`, plus the native-facing cancellation and quality regressions fixed.


## TV shared-runtime repair run 1 — 2026-09-07

- One-shot workflow `MAIN - TV Runtime Repair`, run **34072829930**, job **101593230828**, failed safely in the migration step before tests/commit/publication.
- `CORE.MEDIA_TYPE_RESOLUTION.V1` latest-request/cancellation patch applied successfully in the ephemeral workspace; failure occurred afterward because the `STREAM_FACTS` migration anchor still used old local variable name `r` while current Core source uses `row`.
- No generated provider, manifest, DATA or public version changed from this failed run.
- Fix the migration anchor against current `global_stream_facts_v1.py`, then rerun the full focused cancellation + quality + batched-prune test set before committing any Core repair.


## TV shared-runtime repair run 2 — 2026-09-07

- `MAIN - TV Runtime Repair` retry run **34073021357**, job **101593778197**, failed safely in migration validation before focused tests/commit/publication.
- The current-source `STREAM_FACTS` prepatch succeeded (`STREAM_FACTS_QUALITY_V2_PREPATCH_OK`) and wrote the intended richer quality-fact logic in the ephemeral workspace.
- Failure was only the upgrader's own stale validation literal: it still required `r&&r.resolution` / `r&&r.height`, while current `global_stream_facts_v1.py` correctly uses `row&&row.resolution` / `row&&row.height`.
- No provider bundle, manifest or public version changed. Fix the migration validator, then rerun the full focused cancellation + quality + batched-prune suite.


## TV shared-runtime repair run 3 — 2026-09-07

- `MAIN - TV Runtime Repair` run **34073127250**, job **101594076771**: all three migrations succeeded in workspace (latest-request cancellation, quality recovery, batched prune history).
- The new **functional cancellation regression passed**: observed calls were exactly `/1/one` then `/2/one`; the superseded request's catch/fallback `/1/two` never reached network. This directly proves latest-request-wins for the stale-fallback shape reported on NuvioTV.
- The run then failed before executing the quality behavior because `tests/stream_quality_recovery_tv_test.py` imported `global_stream_presentation_v1.py` without adding `scripts/` to `sys.path`, causing `ModuleNotFoundError: provider_patch_blocks`.
- This is a test bootstrap defect only. No Core repair was committed and no provider/manifest/public version changed. Fix the test import path and rerun the complete focused suite; do not alter the proven cancellation behavior.

### TV shared-runtime repair — final consolidated checkpoint (2026-09-07)
- Retry 4: Actions run `34073319355` proved stale-request cancellation but exposed that `resolution: 1920x1080` was not converted to `quality: 1080p`.
- Retry 5: Actions run `34073668673` proved cancellation, Purstream/StreamZo quality recovery (`1080p`, `1080p`), and batched prune; it then exposed a stale runtime-only-TMDB test bootstrap.
- Retry 6: Actions run `34073743529` restored full presentation metadata but exposed two TMDB requests for one movie invocation.
- Retry 7: Actions run `34073960958` had zero jobs because checkpoint text escaped the YAML block; no Core/product code executed.
- Retries 9/10 (`34074004747`, `34074084167`) proved the duplicate was not solved by presentation reuse alone: MEDIA_TYPE clears transient `__nuvioMediaContext`, while its durable cache is populated only after the inner identity layer has already run.
- Retry 11: Actions run `34074160651` instrumented the exact requests. The first was STREAM_IDENTITY's legacy lightweight `append_to_response=external_ids`; the second was MEDIA_TYPE's canonical rich metadata request. Final cache key was `movie:157336`.
- Retry 12: Actions run `34074347630` applied shared TMDB ownership successfully, then stopped on the obsolete identity revision literal in a test.
- Retry 13: Actions run `34074404812` passed cancellation, quality, prune, media resolver, full identity semantics and presentation V20. It then exposed that `global_stream_presentation_metadata_fallback_test.py` expected TMDB metadata without injecting the required runtime-only TMDB credential.
- Final repair run: Actions run `34074478047`. STREAM_IDENTITY delegates TMDB metadata acquisition to `__nuvioCoreGetTmdbDataV1` when installed, so identity, media-type and presentation share one canonical cache/network owner; the legacy lightweight call is compatibility-only when the shared capability is absent.
- Shared Core acceptance: stale A→B network sequence only `/1/one`, `/2/one`; Purstream/StreamZo quality fixtures both `1080p`; batched prune retention; media-type + identity contracts; exactly one movie TMDB request through the full presentation pipeline; metadata fallback under explicit runtime credentials; sanitizer fail-closed/direct-normalization.
- Public manifest remains `5.21.35` until the separate 96/96 route-proof reconstruction, reverse/static/integrity, quick-yield, real Purstream HOTD S3E1 `series` + `tv` proof, and publication transaction are green.

## 2026-09-07 — Route-proof runs 8–10 / HOTD dual-provider checkpoint

- Shared runtime repair is durable on `main` from commit `0162eeeb85763ced98fb090ad09f7260bfb600ae`: stale-request cancellation A→B, real stream-quality recovery, batched prune history, shared TMDB ownership/cache, presentation and sanitizer focused regressions all passed together in run `34074478047`.
- Route-proof reconstruction run #8 `34074736796` reached census/DATA/materialization/prune/runtime/cardinality green. First reverse blocker was legitimate: MOVIX had been re-enabled even though census classified it `no-proven-route` with zero proven routes. Route-proof activation policy was added so MOVIX remains disabled/neutralized until a future positive route proof; it never auto-enables on proof alone.
- Route-proof reconstruction run #9 `34075701458`, job `101601231061`, proved census **96/96** with `91` historical-upstream mappings + `5` NiakVIO-native providers, `46` providers with proven routes, `310` proven routes, `23` simple API recipes, and zero source-unavailable providers. MOVIX stayed `enabled=false` through DATA application, materialization, prune and 96-provider cardinality.
- Run #9 also passed reconstructed 96 runtime/Core ownership, global stream output guard, episodic zero-year policy, native HLS budget, provider-loading compatibility, media resolver and dual-ID tests. Reverse then failed only on a stale Purstream type assertion: it expected `supportedTypes=[movie,tv]` even though current architecture separates canonical semantic capability from client transport compatibility.
- Purstream type contract is now explicit: `canonicalSupportedTypes=[movie,tv]`; transport compatibility exposes `supportedTypes=[movie,tv,series]`, where `series` is a Nuvio transport alias for canonical `tv`. Reverse checker commit `c1c022609b202ec36f49cb77d5486db89017d1f9` validates this split instead of rejecting the required `series` lane.
- User requires final real **House of the Dragon S3E1** proof to test **both Kehflix and Purstream**, on both `series` and `tv` transport. Expected diagnostic pattern supplied by user: **Kehflix OK / Purstream NOT OK**. Do not force that result; measure and report the real per-provider verdict. Kehflix is the required positive control; Purstream is diagnostic at this stage.
- This supersedes older MEMORY wording that required Purstream itself to be green before the route-proof run could complete. Current acceptance is: **Kehflix must be OK**; Purstream must be measured and reported exactly. If the measured pattern is Kehflix OK / Purstream NOT_OK, preserve that report and wait for the user's follow-up explanation before deciding whether publication may proceed with the Purstream diagnostic blocker.
- Latest completed census before run #10: Kehflix = `proven`, 5 reusable route patterns; Purstream = `no-proven-route`, 0 proven routes despite two provider requests per Interstellar / Breaking Bad S1E1 / HOTD S3E1 fixture and an accessible server. Do not call Purstream candidate/static paths "new routes".
- Purstream candidate-only paths currently retained for recognition/recovery, NOT executable route authority: `/search-bar/search/{query}`, `/stream/{id}`, `/stream/{id}/episode?season={season}&episode={episode}`, plus the official status hub candidate. `route_proof_version=5`, `provenRouteCount=0`, `learned_routes=[]`.
- Kehflix proven reusable patterns in the same census are `/api/streams/movie?id=&k=`, `/api/streams/tv?id=&k=`, `/api/streams/episode?id=&season=&episode=&k=`, `/api/stream-gw`, `/api/track-view` on `https://kehflix.lol`.
- Final live probe is `scripts/hotd_s3e1_live_probe.py`; it executes the reconstructed Kehflix and Purstream Provider JS through the hardened worker separately for `series` and `tv`, records stream count / provider HTTP success / episode-route observation, and emits `automation/hotd-s3e1-live.json` without printing stream URLs. The script exits non-zero only when required positive control Kehflix fails.
- Route-proof run #10 `34076409932` is triggered from commit `4229ae02b95625c8cc3d2fba4834ba12d8f56fd0` after the Purstream canonical/transport reverse assertion fix. Its 96-provider census and DATA/activation-policy step are green; materialization/prune are green and runtime tests were running at the latest checkpoint. Public manifest is still **5.21.35**; no 5.21.36 publication is accepted yet.
- Publication rule: do **not** reuse the old identity-only 5.21.36 workflow. If route-proof + reverse/static/integrity + quick-yield + HOTD proof succeeds, promote the **exact validated artifact** rather than running a second network census, revalidate the current cancellation/quality/TMDB Core and MOVIX neutralization, then CAS-push and verify all public manifest projections post-push.
- Documentation debt added by user: after runtime/publication stabilization, replace user-facing/documentation terminology **"Lego"** with a generic term such as **block / Core block / Provider block**. Preserve marker semantics and compatibility while removing trademarked wording from docs/log labels/names where practical. Do this as a later clean step, not inside the current functional run.
- User explicitly reminded that `MEMORY.md` must be updated at every important state transition. Treat this as a hard execution rule: checkpoint significant red/green runs, root-cause fixes, publication changes and final proofs before moving on.

## 2026-09-07 — Route-proof run 10 reverse green / static-audit naming failure

- Route-proof run #10 `34076409932`, job `101603292174`, completed failure safely before quick-yield/HOTD/publication. Public release remains `5.21.35`.
- Run #10 census: 96 providers, 91 historical-upstream mapped + 5 NiakVIO-native, **47 providers with proven routes, 303 proven routes, 23 simple API recipes, 0 source-unavailable**. This differs slightly from run #9's 46/310 because live route proof is network-dependent; catalogue cardinality and source mapping remained stable.
- Purstream remained `no-proven-route`, 0 proven routes. Kehflix remained `proven`, 5 reusable routes. MOVIX remained `no-proven-route`, 0 routes and `enabled=false` through DATA policy, materialization, prune and cardinality.
- Full 96 Provider JS materialization, prune/projections/config validation, reconstructed runtime/Core ownership, stream-output guard, episodic-zero-year, HLS, native-loading, media resolver and dual-ID tests all passed.
- **Reverse reconstruction passed byte-identical 96/96**: `PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation=66809df74d148b02 byte_identical=96/96`.
- The next command `audit_provider_v3_static.py` failed on `anime-sama-aaa6dc71f60a1d3e.js` even though the computed SHA prefix was exactly `aaa6dc71f60a1d3e`. Root cause: the static audit only accepted final publication filename shape `provider--source--hash.js`, while route-proof workspace materialization intentionally uses `provider-hash.js`.
- Correct fix: make the static audit context-aware. `publication=false` / workspace must require the exact simple content-addressed materialization filename; `publication=true` / release/main must retain the stricter source-qualified publication filename. Do not weaken final publication naming validation.
- Quick-yield and final HOTD Kehflix/Purstream proof were skipped because static/integrity stage failed first. No HOTD verdict exists from run #10.

## 2026-09-07 — Workflow Gate source-v10 alignment

- `CORE - Workflow Gate` run `34077502006` on route-proof source SHA `914048e5de06c3adab0cf348cd932265ecd0a936` failed in workflow architecture contracts because direct source tests still asserted obsolete identity revision `cross-client-shared-catalogue-policy-movie-year-only-v9`.
- This was source-test metadata drift, not a provider/runtime regression: the repository `global_stream_identity_v1.py` is already `cross-client-shared-tmdb-owner-movie-year-only-v10`, while route-proof workspace migration subsequently upgrades the candidate to combined `cross-client-shared-tmdb-owner-zero-episodic-year-v11`.
- Commits `2064b526a51d8ccda375b47bb981a137dad6e938` and `181ec48edd3847be1a40400aefe6e8db47839e50` align only the direct-source revision assertions in `priority_tv_year_domain_refresh_test.py` and `global_identity_policy_ownership_test.py` with source v10. The full behavioral assertions were preserved; no Provider/Core/DATA/manifest byte changed.
- `CORE - Workflow Gate` run `34077884061`, job `101607483550`, then completed **success**: pinned Actions, Python syntax, multi-device runtime contract, workflow architecture contracts, native provider-loading compatibility and side-effect-purity all passed.
- These test-only commits did not trigger or mutate route-proof run `34077501994`; that candidate remains fixed to source SHA `914048e5de06c3adab0cf348cd932265ecd0a936`.
- Exact-artifact publication may allow these two named test-only drifts after the route-proof source SHA, but any product/runtime/DATA/manifest drift must still require a fresh route-proof candidate.

## 2026-09-07 — Route-proof run 11 integrity / pre-release validation checkpoint

- Route-proof run #11 `34077501994`, job `101606427031`, source SHA `914048e5de06c3adab0cf348cd932265ecd0a936`, passed baseline, proof-first migration tests, 96-provider census/DATA application, materialization, prune/projections, reconstructed runtime/Core tests and 96-provider cardinality.
- Run #11 also passed reverse reconstruction **96/96 byte-identical**, the context-aware static audit, and release-hash generation. It failed only in release-integrity activation preservation because `health-report.json` still carried an older MOVIX promotion row with `enabled=true` while the proof-v5 manifest/override policy correctly kept MOVIX `enabled=false` with zero proven routes. Quick-yield and HOTD were therefore skipped; run #11 produced no HOTD verdict.
- MOVIX fix is explicit proof-v5 evidence, not a generic network-failure exception: `published-disabled-no-proven-route` + `route_proof_no_proven_route` requires schema/proof v5, current `provider-route-recovery-v5` authority and zero proven routes. Future positive route proof removes the stale zero-route reason but never auto-enables MOVIX. Durable commits: `910b5669366818a419b8e091d122d9d49e8c317a`, `db4f52f7f16377abec6736ba99236003013e4ba0`, `220829104086af20f755e588510f57fcf63b744d`, `cd26ee3af00d5506a01769616a70dcba5d4cc71a`.
- Media capability documentation/tests were reconciled with runtime truth: canonical semantic values remain `movie/tv/anime`; `series` is transport-only; episodic anime/tv expose `tv+series`; anime never gains artificial movie capability. Machine/test commits include `3febf63ce11610f53fd27f2dedc55ca48f60cf20`, `6ecd053bb4571b86f987dc61092625e980916586`, `5b84350454db6f3f368bf9922df2ffd3f0b1db1e`.
- Public/static filename audit now uses explicit execution context: route-proof sets `NUVIO_PROVIDER_V3_CONTEXT=workspace` and requires `provider-hash.js`; unspecified/public execution fails closed to source-qualified `provider--source--hash.js`, even if historical materialization metadata still says workspace. Commits `64d89c58901082971a86dcab05893e975b848baa` and `2e3c1d9a8bb8cede580af1e9f70e49cd7c0c88d9`.
- Workflow Gate run `34090076713` on `2e3c1d9a8bb8cede580af1e9f70e49cd7c0c88d9` is fully green. CORE Quick run `34090076686` validates public docs/types/five-Lab contract, minimizer, HTML security, strategy plan and static audit, then reports source-vs-public Core block non-idempotence because unreleased 5.21.36 Core source is ahead of the accepted 5.21.35 published bytes. That pre-release drift is not used as candidate proof; candidate authority remains reverse byte-identical reconstruction.
- Public manifest remains **5.21.35**. Next action is route-proof retry 8 through quick-yield and real HOTD S3E1 Kehflix + Purstream (`series` + `tv`). If measured result is Kehflix OK / Purstream NOT_OK, preserve the report and stop before publication for the user's Purstream explanation.

## 2026-09-07 — HOTD targeted acceptance: Kehflix OK / Purstream NOT_OK

- Public remains **5.21.35**; no publication was performed.
- Full route-proof retry 9: run `34091368865` reached census 96/96, DATA apply, materialization 96/96, runtime/Core-block tests, cardinality, reverse `96/96 byte_identical`, static audit, release integrity and quick-yield. Census: 96 providers, 91 historical upstream + 5 NiakVIO native, 46 providers with proven routes, 311 proven routes, 23 API recipes, 0 source-unavailable.
- Retry 9 HOTD initially measured Kehflix NOT_OK / Purstream NOT_OK. Kehflix reached HTTP episode routes but returned zero streams; Purstream was still zero.
- Root cause 1: proof-v5 generalized signed/identity query calls too aggressively (`id=&k=` etc.) and even rewrote literal `User-Agent: NiakVIO/3` into `NiakVIO/{season}` for S3. Added `scripts/upgrade_route_proof_dataflow_safety_v2.py` + `tests/route_proof_dataflow_safety_v2_test.py` to preserve literal static headers, reject blank signed routes as executable, and preserve a richer runtime plan over weak observations.
- Kehflix terminal discovery run `34094560163`: `kehflix.lol` is redirect-only to `kehflix.com/`; both `kehflix.com` and `kehflix.wiki` preserve `/title/tv/94997-house-of-the-dragon`. The detail page exposes a signed `/player` URL. The signed HOTD S3E1 episode API returned media-like values: `.com`=1, `.wiki`=5. Canonical runtime terminal chosen for the repair: `kehflix.wiki`, alternate live terminal `kehflix.com`.
- Added `scripts/upgrade_kehflix_terminal_domain_v1.py` and `scripts/upgrade_signed_player_api_v1.py`. The signed-player family now executes deterministic TMDB detail -> signed player -> episodic stream API dataflow instead of assuming a direct unsigned `/player?tmdbId` call is sufficient.
- Targeted real HOTD run **`34095052891`** materialized only Kehflix from current Core + structured DATA and then executed the same final probe against Kehflix + Purstream in both `series` and `tv`.
- **ACCEPTED TARGET:** Kehflix `OK`: `series_streams=6`, `tv_streams=6`, HTTP=true, episode route=true for both transports. Purstream `NOT_OK`: `series_streams=0`, `tv_streams=0` (provider HTTP and episode route were reached in this targeted baseline). `HOTD_S3E1_EXPECTED_PATTERN kehflix=OK purstream=NOT_OK matched=true`.
- Per user instruction, stop before publication/full next retry at this exact pattern and wait for the user explanation about Purstream.
- Purstream current structured/upstream route family to preserve for the next discussion: domain discovery `https://raw.githubusercontent.com/wooodyhood/nuvio-repo/main/domains.json`; search `/search-bar/search/{query}`; movie `/stream/{id}`; episode `/stream/{id}/episode?season={season}&episode={episode}`; API base is dynamically `https://api.purstream.<current-tld>/api/v1` with matching site Referer.
- Cleanup reminder after final publication: replace the word `Lego` in docs/workflow labels with a neutral term such as `block`/`bloc`.

## 2026-09-07 — Route-proof 5.21.36 final publication

- Exact validated artifact: route-proof run `34096200193`, source `8173adc4db674189ccc3169fe9ffe90043790d21`.
- Public filename projection preserved provider bytes; reverse rebuild remained 96/96 byte-identical and static publication audit passed.
- Published release target `5.21.36`, 96 providers. Kehflix HOTD S3E1 proof is OK (6 series / 6 tv); Purstream remains NOT_OK diagnostic pending operator explanation.


## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint

- **This checkpoint supersedes all earlier wording that says the public release is still 5.21.35 or that 5.21.36/5.21.37 is pending.** Current public release is **5.21.37**.
- Publication workflow: `FIX - Publish Terminal Session V29`, run **34120732027**, job **101737919476**, completed success.
- Final publication commit: **`6f74939efa11b2c886e82002c242b923a4f87f6c`** (`fix(core): publish terminal labels and stale-session isolation V29`). Push to `main` completed successfully.
- Public manifests verified after push: `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` all report **5.21.37**.
- 96/96 published Provider JS were rematerialized and physically verified to contain `tmdb-data-contract-launch-gate-v29-native-abort-race`, `requestAbortPromise(controller,requestToken)`, and presentation client-projection V20.
- V29 closes the stale-session hole where a native QuickJS fetch bridge may ignore `AbortSignal`: provider fetch now races the native call against request cancellation. Functional regression with an intentionally never-resolving old native fetch completed in ~1 ms after supersede and observed only `/1/one` then `/2/one`; superseded fallback `/1/two` never reached network.
- Terminal stream-label bug was localized outside provider-specific quality calculation: Engine V2 accepted labels such as `Kehflix - Inconnue` as provider names. Engine V2 now strips terminal placeholder suffixes and mirrors final projected `title` into `name`, matching the client-facing Core projection. Placeholder quality (`Unknown`, `Inconnue`, `N/A`, etc.) collapses to provider-only; meaningful qualities remain, including `1080p` and `2160p -> 4K`.
- `CORE.STREAM_SANITIZER.V6` output guard passed across all 96; release integrity and fixed-point override checks passed.
- Nuvio client upstream drift seen during release: NuvioDesktop audited contract remained accepted; NuvioMobile had a safe upstream advance; NuvioTV had a separate semantic-sensitive subtitle-cache drift requiring review. Provider publication intentionally continued against pinned audited client contract refs.

### Live yield on exact 5.21.37 candidate

- Interstellar matrix tested **55 enabled movie-capable providers**. Only **6** returned automatic streams: `castle`, `hindmoviez`, `streamflix`, `streamzo`, `videasy`, `wookafr`. VF automatic providers: **2**, `streamzo` + `wookafr`. **49/55** returned no streams. This is materially better than the earlier native observation of only StreamZo/Kehflix/Castle in one client session, but still far below the 96-provider objective and must not be considered provider recovery completion.
- Notably Kehflix returned zero in the CI Interstellar matrix even though it is a known viable provider in other live/native fixtures; treat this as route/runtime/fixture evidence, not provider-wide disablement.
- User Desktop anime fixture was correctly identified as **The Unwanted Undead Adventurer S01E02**, IMDb `tt30177477`, not Hell Mode. Candidate matrix tested **62 episodic/anime-capable providers**: **2 positive** (`anime-sama`, `neko-sama`), network reached **49**, successful provider HTTP **37**.
- Secondary Hell Mode S01E12 (`tt38646634`) matrix produced the same provider-positive set: **2/62**, `anime-sama` + `neko-sama`; network reached 49, successful HTTP 36.
- These anime results prove the global `series -> tv/anime` transport is not completely broken, but extraction/runtime route yield is still severely underperforming after successful network access for many providers.
- User Desktop logs separately showed DNS/host failures including `api.nakios.live`, `*.eat-peach.sbs`, and VidLink-related traffic. Current main domains can be alive while historical/API subdomains or route families are stale; domain, route, extraction and player evidence must remain separately classified.

### Current priority after 5.21.37

1. Keep V29 terminal-label/session isolation immutable while provider recovery continues.
2. Resume **proof-first real route recovery across all 96**, including disabled/off rows for recoverability; test a route live at discovery time and never promote static fragments as executable routes.
3. Use `MAIN - Route Proof Reconstruction 96` as a non-public candidate workflow. Its baseline must derive from `.github/triggers/route-proof-reconstruction.json`, not be hard-coded to 5.21.35.
4. For every candidate, compare live yield against the accepted 5.21.37 baselines: Interstellar 6/55 automatic (2 VF), Unwanted Undead 2/62, Hell Mode 2/62. A structurally green reconstruction that does not improve/accurately explain these results is not completion.
5. Route families already requiring scrutiny include VidLink historical `/api/b/...` versus current documented `/movie/{tmdbId}` and `/tv/{tmdbId}/{season}/{episode}`, and Nakios principal-site versus stale `api.nakios.live`. Do not replace routes solely from documentation; require provider-specific executable HTTP proof before promotion.
6. Preserve the five Native Labs requirement after route/runtime stabilization: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows.
7. Continue automatic `MEMORY.md` checkpoints for every important green/red run, root cause, architecture change, publication, native proof, and security proof.

## 2026-09-07 — Route-proof retry 16 pre-census failure

- Candidate workflow `MAIN - Route Proof Reconstruction 96`, run **34123018893**, job **101745186842**, failed before route census; no provider route result from this run is valid because all proof/yield steps were skipped.
- Baseline modernization itself passed: `ROUTE_PROOF_BASELINE_OK version=5.21.37 providers=96`.
- Exact blocker: `scripts/apply_core_identity_ownership_cleanup.py` still attempted the historical v10 -> v11 one-shot migration and required exactly one `cross-client-shared-tmdb-owner-movie-year-only-v10` anchor. Current main is already v11 (`cross-client-shared-tmdb-owner-zero-episodic-year-v11`), therefore anchor count was 0 and the migration aborted.
- This is a stale/idempotency defect in the route-proof bootstrap, not a V29/session/presentation regression and not route/network evidence.
- Required correction: make the one-shot identity cleanup detect an already-current v11 source state, validate all expected final ownership invariants, and exit successfully without rewriting; only run historical transformations when the legacy anchor is actually present.
- Do not weaken identity tests: TV/series/anime episodic year influence remains zero; V29 terminal label + abort-ignorant request cancellation remain mandatory in every reconstructed candidate.

## 2026-09-07 — Identity cleanup fixed-point correction

- Stale route-proof bootstrap defect from run 34123018893 is corrected in commit **`3ca80acc513720bab4c91ede3467894f3c4a1120`** (`fix(core): make identity ownership cleanup idempotent`).
- `scripts/apply_core_identity_ownership_cleanup.py` now detects the already-current `cross-client-shared-tmdb-owner-zero-episodic-year-v11` implementation, validates the full expected final source state, reports `already_current=true`, and exits successfully without attempting historical rewrites.
- Repair workflow `TEMP - Identity Cleanup Fixed Point V1`, run **34123475865**, completed success; both patch application and a direct second execution of the cleanup script on the current source were green, proving fixed-point/idempotent behavior.
- Temporary repair workflow/script were cleaned after the verified source commit. Route-proof recovery may now proceed to its actual proof/census stages without reapplying the obsolete v10 -> v11 migration.

## 2026-09-07 — Route-proof run 17 request-spec bootstrap failure

- Candidate workflow `MAIN - Route Proof Reconstruction 96`, run **34123692126**, job **101747285815**, again failed before route census; no route/yield conclusion from this run is valid.
- Baseline and the previously fixed identity cleanup passed on exact **5.21.37**. `apply_core_identity_ownership_cleanup.py` reported `already_current=true`; ProviderBase current checks and route-proof authority v5 migration also passed.
- Exact new blocker is `scripts/upgrade_route_recovery_request_specs_v1.py` validation after `upgrade_provider_route_authority_v5.py`: it still requires the obsolete literal `patch["learned_routes"] = execution_routes`, which is no longer present in the current route-recovery/applier wiring. Assertion: `recovery request-spec wiring missing: patch["learned_routes"] = execution_routes`.
- This is another stale bootstrap/migration validation mismatch, not provider route/network evidence. Census, materialization, quick-yield and all three candidate live matrices were skipped.
- Required correction: inspect the current structured route recovery writer and update the migration/validation to assert the current proof-v5 DATA/request-spec contract semantically, while preserving the hard rule that only live-proven executable routes may enter runtime `routes/apiRecipe`; candidate/static routes must never be promoted merely to satisfy the test.

## 2026-09-07 — Proof-v5 request-spec validator fixed to current runtime selection

- Run 34123692126 exposed an obsolete validator expectation in `scripts/upgrade_route_recovery_request_specs_v1.py`: it still required direct `patch["learned_routes"] = execution_routes` assignment.
- Current route recovery intentionally uses `select_runtime_routes(existing_routes, candidate_routes, execution_routes)` so a weak new census cannot demote a richer already-proven runtime plan. Directly restoring the old assignment would have weakened route authority/dataflow safety.
- Durable fix commit: **`44b245ae333c4092cc2901468a6fd4c618e21dee`** (`fix(routes): validate current proof-v5 runtime selection`).
- Repair workflow `TEMP - Route Request Spec Validator V2`, run **34124033946**, completed success. It proved the request-spec migrator, route-authority v5 migrator, Python compilation, provider route-proof authority, manifest policy and empty-route bootstrap tests; the migrator also passed a second execution in the same run.
- The validator now requires semantic current wiring: `executionRoutes`, `generic_execution_route`, reusable request specs, conservative `select_runtime_routes`, `patch/model routes = runtime_routes`, `genericExecutionRouteCount`, and `runtimePlanPreserved`; it also explicitly rejects reintroduction of the obsolete direct execution-route overwrite.
- This correction preserves the core rule: only live-proven executable routes may enter runtime DATA, while static/candidate routes stay non-executable unless separately proven.

## 2026-09-07 — Route-proof reconstruction 96/96 fully green (candidate only)

- Public baseline remains `5.21.37`; no Provider candidate was published by this run. Successful workflow: `MAIN - Route Proof Reconstruction 96`, run `34124189951`, workflow run number 18 / internal retry 13, trigger commit `c68da2edeecde5241486dd2089ebe7d703ce1a9e`. Trigger target is `5.21.38-candidate` and required proof is `proof-v5-96+interstellar+unwanted-undead+hellmode+hotd`.
- Full workflow PASS end-to-end: baseline freeze; proof-v5/shared-runtime migrations; proof-first authority and zero-route onboarding; 96-provider live census; DATA/activation application; 96/96 materialization; prune/projections/CONFIG; reconstructed runtime + managed-block contracts; workspace cardinality; reverse/static/integrity; quick-yield; live comparison; HOTD S3E1; artifact upload.
- Census exact result: `96` providers = `91` historical-upstream mapped + `5` NiakVIO-native, `source_unavailable=0`; `45/96` providers produced live proven routes, `286` proven routes total, `23` simple API recipes, statuses `45 proven / 51 no-proven-route`. The report was applied to all 96 providers. A weak/empty new observation does not demote a richer previously proven runtime plan; `select_runtime_routes(existing,candidate,execution)` preserves the better plan.
- Materialization exact generation: `f492fb39d2a5927c`, `96/96`, device-agnostic JS for TV/Mobile/Desktop. Projections after reconstruction: VF `29`, no-anime `73`, VF-no-anime `17`. Provider CONFIG validation PASS. `Movix` remains disabled with zero proven routes.
- V29/runtime invariants survived complete reconstruction: `ROUTE_PROOF_V29_PRESENT providers=96`; episodic year influence remains zero for TV (`year=ignored`, S/E authoritative), movie year core-owned; media-type resolver, dual IMDb/TMDB identity, latest-request cancellation, abort-ignorant native fetch cancellation, stream presentation/branding/sanitizer order all PASS.
- Reverse/static/integrity exact proof: `PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation=f492fb39d2a5927c byte_identical=96/96`; static audit PASS; release integrity PASS.
- Quick-yield exact result across `193` representative tasks: `raw providers=9`, `playable providers=9`, `verified providers=8`, `wrong_content providers=3`. Playable providers: `allwish, anime-sama, castle, hindmoviez, kehflix, neko-sama, streamzo, videasy, wookafr`. Verified: same list except `neko-sama`. Type breakdown: movie `7/82` playable+verified; TV `6/71` playable, `4/71` verified; anime `2/40` playable+verified. Main failure stages: network zero result `74 tasks / 38 providers`, HTTP error `64/33`, network exception `19/12`, missing runtime plan `16/9`, zero before provider network `5/3`.
- Interstellar candidate matrix: `7/63` automatic providers = `castle, hindmoviez, kehflix, streamflix, streamzo, videasy, wookafr`; VF `3` = `kehflix, streamzo, wookafr`; no settings gap. Prior accepted 5.21.37 checkpoint was `6/55` with `2 VF`, so absolute provider/VF yield increased, but denominator changed and must not be presented as a normalized-rate comparison.
- The Unwanted Undead Adventurer S01E02: `3/62` positives = `anime-sama, kehflix, neko-sama`, network reached `50`, successful HTTP `39`. Prior accepted checkpoint was `2/62`, so candidate adds one positive provider.
- Hell Mode S01E12: `2/62` positives = `anime-sama, neko-sama`, network reached `50`, successful HTTP `38`; count unchanged from accepted checkpoint.
- HOTD S3E1 real probe: Kehflix PASS on both `series` and `tv`, `4 streams` on each transport, HTTP reached and episode route observed. Purstream remains NOT_OK: HTTP reached but `0 streams`, no episode route. Expected accepted pattern `kehflix=OK / purstream=NOT_OK` matched.
- Candidate artifact: `route-proof-reconstruction-96-34124189951`, artifact id `10020094655`, size `152561733` bytes, SHA-256 `46627b78e445ea0d70d50f09e8bbe7b17dd272e64391232079fb3a9d564bb4d5`, retention 14 days.
- CI cleanup performed during the run: obsolete one-shot workflow `fix-terminal-label-session-v1.yml` removed in `be1f771400dca148991a4ae8ff77e89505836ee0`; obsolete `lab-timeout-isolation-fix.yml` removed in `6430091699152c2eadb504b8c1ac41c86f3bf5be`. Durable source/test fixes remain.
- Memory checkpoint transport upgraded to non-empty sentinel file `automation/memory-checkpoint-pending-v2.md` because the connector Contents wrapper repeatedly returned SHA mismatch 409 when updating the previous empty blob. The permanent writer now consumes v2 and resets it to `` instead of a zero-byte blob.
- Next canonical release step: do not run `CORE - Finalize Accepted Release` directly on the current main, because the successful 5.21.38 candidate exists only in the workflow workspace/artifact (`publication=false`, `mainTouched=false`). First hydrate/commit the exact accepted candidate onto a non-main release branch, include the deterministic migration/source changes needed for reverse rebuild, rerun bounded acceptance there, then merge the accepted candidate and finalize the synchronized release version on the exact accepted main SHA.

## 2026-09-07 — Route recognition V6 retry/dependency checkpoint

- Active experimental branch: `workbench/route-recognition-v6`; no publication from this branch. The public accepted release remains whatever the earlier publication checkpoint says until an explicit verified publication occurs.
- Canonical Repair/Learn/Force engine is `scripts/run_provider_repair_pipeline_v6.py`; all three modes use the same recognition -> correction -> rematerialization -> targeted-yield path.
- Network skip set remains 9 previously validated providers: `allwish`, `anime-sama`, `castle`, `hindmoviez`, `kehflix`, `neko-sama`, `streamzo`, `videasy`, `wookafr`. Retry-4 run `34136291243` proved `tested=87 skipped=9 overlap=0`; common ProviderBase changes still rematerialize all 96 and therefore require deterministic 96-provider regressions.
- Retry-4 route census: 87 targeted, 39 providers with proven upstream routes, 238 targeted routes; merged proof = 46/96 providers and 299 routes. Post-reconstruction acceptance remained `raw=0 playable=0 verified=0`; 21 representative upstream-positive provider/type pairs were lost after reconstruction. Therefore route proof alone is not a repaired provider.
- Adaptive recognition retries are implemented: default 3 attempts, max 4, only for transient network/execution states (timeouts, reset/DNS-temporary, 408/425/429/5xx, worker-no-result/network exception). Deterministic source/runtime failures such as `MODULE_NOT_FOUND` and source-policy blocks are not retried.
- PlayIMDb is explicitly treated as a typed resolver/API family, not as a generic absolute-route or VidSrc-like multi-hop template. Its upstream currently calls `https://streamdata.vaplayer.ru/api.php`, uses `Origin/Referer` playback context from `nextgencloudfabric.com`, and returns URLs under `data.stream_urls`. V11/V12 work is scoped to proof-backed `typed-resolver-api` recipes; multi-hop/search/player chains are not flattened.
- A reconstruction parser defect was identified: plural resolver containers such as `stream_urls` were ignored by common `_sourceUrls`. V12 adds bounded explicit plural stream/source containers plus safe inherited playback headers (`Origin`, `Referer`, `User-Agent`, `Accept-Language`) without scanning arbitrary JSON URLs.
- `MODULE_NOT_FOUND` root cause: upstream Provider JS is executed from a temporary directory, so bare npm imports could not see NiakVIO's locked root `node_modules`. The single owner is `upgrade_provider_worker_module_resolution_v1.py`: only top-level declared dependencies may fall back to project-root resolution, Cheerio is redirected to parser-only `cheerio/slim`, and blocked Node built-ins remain blocked.
- Dependency probe run `34147056268` succeeded: 16/16 formerly `MODULE_NOT_FOUND` providers no longer hit that error; `allanime` immediately produced 4 proven routes. This is an environment/recognition recovery, not yet an end-to-end repaired provider until reconstructed `raw/playable` passes.
- Do not count PlayIMDb or AllAnime as repaired until the targeted post-reconstruction yield returns real streams. Do not expand the green skip set from route proof alone.

