## 2026-09-08 — Main consolidation + V20.4 provider/runtime checkpoint

Repository authority / topology:
- User explicitly requires all active NiakVIO work on `main`; no persistent workbench branch after cleanup.
- `brain-learning/proposals` is the sole exception: immutable Learning branch, never delete or mutate it during cleanup.
- Consolidation merge on `main`: `b1ee11f25cc21a7f32d6ce48d1cebd8d49f6d4b2`, retaining history from prior main, `workbench/route-recognition-v14-search-plan`, immutable Brain and the three then-current Dependabot heads. Final cleanup target is `main` + `brain-learning/proposals` only.
- Provider repair workflow `.github/workflows/provider-repair-fast-targeted.yml` now executes from `main` rather than the old workbench branch.

Provider objective / acceptance:
- Catalogue target remains all **96 Provider Objects**, including disabled/off rows for recoverability. Never call the task finished after a few targeted providers.
- Required proof chain before completion: targeted family repair -> non-regression -> global 96/96 structural/config/identity/stream guards -> five independent native Labs (TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows) -> UX checks for latency/session isolation/stream metadata/yield.
- Device behavior must not be inferred from another repo/runtime. Desktop macOS logs and raw TV Android results must be cross-compared, but transport/DNS/cancellation/player conclusions remain per Nuvio repo/device unless independently reproduced.

Latest targeted live evidence before V20.4:
- Run 59 (`34270605486`) first crossed the migration boundary and proved live upstream routes for AnimeSama (`animesama-co`), AnimeVOSTFR and French-Manga, but reconstructed preservation was 0/3.
- V20.3 subsequently fixed generic `{slug}` projection and raw `application/x-www-form-urlencoded` capture. It is provider-agnostic.
- Run 61 / main-preconsolidation wave proved that materialized bundles now actually reach provider routes: AnimeSama reaches search/detail/player, French-Manga reaches its POST search, AnimeVOSTFR reaches `trembed`; remaining failure is response identity/dataflow, not absence of provider traffic.
- French-Manga positive upstream search uses a form body equivalent to `query=<title or title+season>&page=1`. V20.3 still falsely treated static `page=1` as fixture residue when S/E=1.
- AnimeVOSTFR exposed the multi-hop state bug: search/detail can yield a slug first, then the detail response yields a different internal id (`trid`) consumed by later `trembed` requests. V18/V20.3 froze the initial identity instead of updating state between steps.

V20.4 (current main work):
- `scripts/upgrade_provider_response_value_correlation_v20_4.py` added on main.
- Generic fixes: unrelated small static form constants remain literal; bounded title+season search expressions can replay as `{query} <observed season keyword> {season}`; provider-value executor becomes stateful and updates providerId/providerSlug from safe response-owned values between steps; volatile/auth/session/external content identity fields remain excluded.
- `tests/provider_response_value_correlation_v20_4_test.py` is mandatory and executes the exact generated JS response-state helper with neutral data; no provider-specific tokens are allowed in the migration.
- `scripts/run_provider_repair_fast_targeted_v20.py` now applies V20.4 immediately before live recovery.
- Trigger schema 15 targets `animesama-co`, `animevostfr`, `french-manga`, publicationAllowed=false.
- Current V20.4 main run: GitHub Actions run **34285007146**. Do not claim success until acceptance and V20.4 contracts are both green and artifacts show preserved upstream-positive yield.

Native/client evidence and UX debts still blocking completion:
- User reports slow provider loading, reduced number of available streams, and a historical regression where loading jobs from the previously selected work can continue after navigation and appear to load indefinitely. The exact stale-request mechanism is not proven common across all devices; test per repo/runtime.
- Desktop macOS user log for Interstellar showed 0 displayed streams on that run while many provider/network attempts still occurred. Dead/failing domains observed included `api.nakios.live`, `eat-peach.sbs` family, `vidlink.pro`/other failing routes. Desktop successful/non-throwing fetches are poorly observable because current client logs mainly expose exceptions.
- Cross-device comparison matters: TV Android had previously produced Interstellar results from providers including Purstream/Castle/Cineby after cache clear, while the user macOS run displayed none. Therefore macOS 0-stream is not proof of a common DATA failure for those providers.
- The user clarified the UI label issue: **`Purstream - Inconnue` is the stream title**, not provider/plugin branding. Root manifest currently declares Purstream correctly; the problem is stream presentation metadata/quality. For *Les Fils de l'homme*, user saw only `Purstream - Inconnue`, VF and age criterion, with quality absent and fewer streams than expected. Treat metadata loss + yield reduction as blocking regressions.
- Earlier `CORE.STREAM_PRESENTATION` work removed invented unknown-quality projection; final behavior must preserve real quality/language/metadata when present and must not manufacture a quality. Client fallback `Inconnue` is acceptable only when source evidence truly has no recoverable quality; verify reader/provider facts before publication.
- User requests the release/version to be visible in the plugin name because some devices do not expose the plugin version field. Final manifest generation must keep the canonical `version` field and include a stable visible version suffix in `name` without repeated suffixes across rebuilds.
- Mac Lab script supplied to user creates full stdout, provider-focused, macOS unified log, summary and environment files. Use it as Desktop-macOS evidence only, then correlate with TV Android/raw and the other Labs rather than treating one device as oracle.

Client session/cancellation investigation:
- Desktop `StreamsRepository` cancels its active coroutine/job on a new work, but downstream `PluginRepository.executeScraper()`/runtime boundaries and native HTTP behavior must be proven independently. Do not claim the old-work job leak is fixed merely because JS AbortController or a coroutine cancel exists.
- Previous investigation found Kotlin `runCatching` wrappers around plugin execution and blocking/native HTTP patterns as possible cancellation boundaries; this is a client-runtime debt candidate, not yet a universal NiakVIO provider defect. Labs must distinguish coroutine cancellation, native HTTP cancellation and stale completion rejection.

Next required execution order:
1. Finish run 34285007146; fix the first real failing contract/yield rather than accepting partial green.
2. Once AnimeSama/AnimeVOSTFR/French-Manga preserve upstream-positive output, retest AnimeZey, Cineby and MovieBlast from live proof.
3. Broaden to all remaining Provider Objects and produce global 96/96 report; no provider is exempt merely because currently disabled or historically green.
4. Run five native Labs independently and cross-runtime divergence gates; inspect reader/player bugs and metadata/yield, not only scraper return counts.
5. Add visible manifest version to name, verify Purstream/stream presentation metadata and reduced-yield regression.
6. Security/docs/clean/fixed-point checks, then cleanup branches while preserving immutable `brain-learning/proposals`.
