# NiakVIO — open-task recovery checkpoint — updated 2026-09-16

This is the operational recovery list for current `main`. Exact repository state and current GitHub Actions/native evidence override older chat summaries and historical sections of `MEMORY.md`. The old `fix/labs-5.21.44-20260912` campaign is historical, not an active write policy.

## Current authority

- Current public release: **5.21.48**.
- Active write/publication target: **`main`** only. Do not recreate a persistent workbench/repair branch.
- Recovery census remains **96 Provider Objects**: 46 current rows plus 50 historical archive rows. Never shrink this census to manufacture green metrics.
- Current physical manifest has **46 rows**, of which **44 are active** and **2 disabled-retained**; active Native execution is defined by `automation/evidence/hub-lab-matrix-46.json`.
- Wrong title/type/season/episode is worse than zero. Identity/media integrity remains fail-closed.
- Hub/registry presence is discovery knowledge, never execution proof. Telegram remains discovery-only.
- Runtime/client portability is Core-global Bloc. Timer shims, fetch/URL portability, stale-generation suppression, HTTP 403/media fail-closed and terminal sanitation must never become provider-specific runtime patches.
- Provider timeout remains **25 s**. Preserve A→B→C latest-generation isolation even if fetch ignores `AbortSignal`.
- Terser is forbidden. Provider v3 uses `scripts/provider_v3_minimizer.py` and must preserve managed boundaries, deterministic reverse rebuild and byte fixed point.

## Publication / immutable Hub-46 transport

- [x] Release 5.21.48 is synchronized across root/VF/no-anime/VF-no-anime manifests, package metadata and release hashes.
- [x] PR **#120** restored immutable Hub-46 transport and was merged normally at `e401e61688dd79996002f9e37b9abfc923846735`.
- [x] Final provider publication used by Native transport is immutable commit `425756cf1646380fb8172f380d176758c3734ce6`.
- [x] `native-hub46/manifest.json` pins absolute provider URLs to that publication SHA.
- [x] `tests/native_hub46_transport_manifest_test.py` proves each pinned provider blob exists at the pinned commit.
- [x] PR #120 final gates passed: Provider Non-Regression, Media Type & Playback, Workflow Gate, Verify & Publish and CodeQL.
- [x] CodeQL #889 hostname parsing fix is already on main (`c60ec1871dc5d3b2217e69581d2c2a5a6615fc84`); do not duplicate it.

## Five first-class Native Labs — current authoritative run

Trigger SHA: `6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1`.

- [ ] TV Android — run `35033132967`, job `tv-route-reader`: runtime corpus in progress at last checkpoint.
- [ ] Mobile Android — run `35033132967`, job `mobile-android-reader`: runtime corpus in progress at last checkpoint.
- [ ] Mobile iOS — run `35033132980`: native Lab session in progress at last checkpoint; unsigned device IPA build/upload already green.
- [ ] Desktop macOS — run `35033133048`: bridge build green, rotating route runtime in progress at last checkpoint.
- [ ] Desktop Windows — run `35033133048`: WebView2 + bridge build green, rotating route runtime in progress at last checkpoint.
- [ ] Do not declare a platform green until its exhaustive Hub-46 matrix step completes and route evidence is uploaded/analyzed.
- [ ] Keep reader/player failures separate from provider extraction failures. Never patch official Nuvio clients merely to turn a Lab green.

## Future Native run latency

- [x] Exact-client prebuild caches are installed for TV Android, Mobile Android, iOS, macOS and Windows.
- [x] Cache keys include exact official-client SHA + OS/toolchain + relevant NiakVIO harness/native-manifest hash.
- [x] No permissive `restore-keys`: stale builds from another client revision cannot be silently reused.
- [x] Runtime corpus and exhaustive provider-matrix gates still execute even on cache hit.
- [x] The temporary cache installer workflow was removed after installation.

## Provider parity / repair queue

- [x] Upstream parity authority is `engine_v2/config/provider-upstreams.json`; the old `sources.json` lookup is obsolete.
- [x] Only exact `upstream_ok_niakvio_ko` evidence is a certain NiakVIO regression. ZERO/technical inconclusive is not automatic repair debt.
- [x] Historical full32 campaign separated three then-certain regressions from fifteen ZERO/technical-inconclusive rows; that historical classification must not be blindly reused as a current queue after later publications.
- [ ] Re-prove any remaining regression against **current 5.21.48 bytes** before mutating it. Historical names that require explicit re-check if still failing include `animevostfr`, `kurage`, `voiranime`.
- [ ] Preserve the historical ZERO/inconclusive list as anti-forgetting evidence, not an automatic mutation queue: `4khdhub`, `allanime`, `allwish`, `anikototv`, `anime-ultime`, `animesalt`, `animetsu`, `flemmix`, `fullanime`, `moviebox`, `moviesmod`, `showbox`, `vidfast`, `vidlove`, `vostfree`.
- [ ] Current named follow-ups from later manual evidence remain: HindMoviez host/search variability and downstream timeouts; AnimePahe provider/runtime I/O versus runner 403; AnimeSalt browser-positive/runner-403 behavior. Diagnose only from fresh evidence.
- [x] Nakios troll/short HLS is rejected by Core fail-closed media safety; do not weaken the validator.
- [x] StreamZo/Frenchstream missing-host-timer class is owned by `CORE.RUNTIME_COMPAT.V1`, not provider-specific timer hacks.
- [ ] Keep a nominative blocker/evidence classification for every current provider: domain/hub, metadata identity, search/detail, API/player extraction, anti-bot/network, stream transport, content identity, native player, or unknown/opaque. `0 streams` alone is not opaque.

## Core/runtime invariants

- [x] `CORE.RUNTIME_COMPAT.V1` owns missing `setTimeout`/`clearTimeout` and Desktop URL/fetch portability.
- [x] Provider-specific ownership of Core-global runtime modules is rejected.
- [x] HTTP 403/404/410 and terminal sanitizer behavior remain fail-closed.
- [x] Explicit no-timer execution proof exists; Desktop-like runtimes without host timer globals must not make providers disappear.
- [x] Capability/type gate occurs before provider network work; semantic anime remains distinct while Nuvio transport may use `tv`/`movie` aliases.
- [x] TMDB/IMDb identity remains dual; episodic year must not affect TV/anime identity; strict year identity is movie-only.

## Domain Refresh

- [x] Domain Refresh is the full-CONFIG transaction v2, not the obsolete `officialSite`-only updater.
- [x] Source authority, CONFIG rebuild, source-qualified/content-hashed filenames, projections/versioning, cycle/rollback safety, idempotence and Core/Bloc invariance are covered by current contracts.
- [ ] Keep generic old-host → new-host derivative reconciliation and synthetic A→B proof covered if this subsystem changes again.

## Brain / Learning / discovery

- [x] Weekly upstream/provider discovery is structurally scheduled (`37 3 * * 3`), read-only and non-P2P.
- [ ] Verify a real scheduled weekly execution/artifact before treating the schedule as historically proven operationally.
- [ ] Review real multi-day Brain differential evidence before treating Learning state as production authority.
- [ ] Preserve international discovery candidate data and country/UHD balance.

## Repository hygiene / docs

- [x] Temporary Native pin-repair and prebuild-cache installer workflows have been removed.
- [x] `VALIDATION.json` now identifies release 5.21.48, `main`, immutable Hub-46 publication SHA and the current five-Lab run IDs.
- [x] `MEMORY.md` now carries an authoritative 2026-09-16 checkpoint covering 5.21.48, PR #120, immutable Hub-46 transport, CodeQL #889, prebuild caches and the current Native runs while retaining older material as history.
- [x] `CHANGELOG.md` now starts with the 5.21.48 Hub-46/publication/native-Lab checkpoint.
- [x] `provider_catalog.json` visible names are synchronized to 5.21.48, and `sync_release_versions.py` plus its regression test now keep catalogue names/version aligned.
- [x] Provider Non-Regression push policy targets `main`; its compatibility contract was aligned and passed.
- [x] Obsolete one-shot Hub-46/rotating-corpus migration scripts were confirmed unreferenced and removed.
- [ ] Recheck `ARCHITECTURE.docx` only after final wording is stable; do not let it override current Markdown/runtime truth.

## Privacy / repository metadata

- [x] Tracked-content searches found no user-specific personal identifiers in the scanned categories; current documentation uses only generic privacy wording.
- [!] Git commit author metadata contains a personal author identity/email on some historical/recent commits. This is **history metadata**, not tracked file content.
- [ ] Do not rewrite Git history while immutable Hub-46/current Labs depend on exact SHAs. If historical author metadata is to be purged, perform it later as a dedicated migration with repinning/republication and downstream SHA reconciliation.
- [ ] Configure a GitHub noreply/private commit email for future human-authored commits outside this automation path.

## Completion rule

The current campaign is complete only when the five Native Labs above finish and their evidence is analyzed; any genuine current provider regression is repaired or precisely fail-closed; current manifests/projections/fixed-point/security remain coherent; durable memory/docs match 5.21.48; obsolete temporary files are removed; and every remaining issue is recorded with exact evidence/reason rather than inherited from an older branch campaign.
