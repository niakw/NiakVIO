## 2026-09-16 — cross-device/non-display maximum-repair checkpoint before final release

### Publication / branches / transaction state
- Public release remains **5.21.48**. Do **not** claim 5.21.49 published until the authoritative `CORE - Finalize Accepted Release` workflow has pushed it to `main` and the public manifests/hashes are verified.
- Active repair branch: `fix/non-display-recovery-20260916`; open PR **#122** (`Fix non-display provider routes and harden parity semantics`). `main` remains the public authority and must not be merged until final PR gates are green on the exact final head.
- Separate diagnostic branch `diag/max-repair-20260916` is temporary evidence/work only and must be deleted after the maximum-repair pass. It must never become publication authority.
- Current repair work uses **46 visible rows = 44 active + 2 disabled-retained**. `manifest-hub46.json`/native transport projection is 44 active; root/catalog visible scope is 46. Never hardcode 46 as the active transport count.
- Authoritative release finalization workflow is `.github/workflows/release-finalize.yml`. It checks exact accepted `main` SHA, re-applies durable patches, runs final minimizer/fixed-point, syncs release/provider cache versions, rebuilds Hub46 native projection/hashes, CAS-checks `origin/main`, then pushes atomically.

### Cross-device native audit conclusions
- Frozen native source used for the five-Lab audit: `6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1`.
- Android TV+Mobile run `35033132967`; iOS `35033132980`; Desktop macOS+Windows `35033133048`.
- iOS: 3299 results; 89 count>0 = VidRock 58 + VoirAnime 31; 89/89 player ready. Strong positive control.
- Windows: 2116 rows; positives HindMoviez movie4/TV4, VidRock movie1/TV1; 9 player ready / 1 timeout. A red exhaustive matrix is **not** Desktop-wide zero.
- macOS: 2091 rows; HindMoviez movie4, VidRock movie1/TV1; 6/6 player `mpv_create_failed`.
- Android Mobile: VidRock positive on Avatar/HOTD; previous player diagnostic was a launcher false-red caused by assuming `com.nuvio.app/.MainActivity`. Android Mobile diagnostic was changed to resolve installed launch Activity through PackageManager.
- TV user evidence remains authoritative for user-visible behavior. Interstellar showed Purstream 720p, Papadustream 480p, Castle English/Hindi with inconsistent duplicate quality, StreamZo with `French Dub` text but no actual FR track, Kehflix multiple streams with inconsistent badges, and no reliable visible 4K before the later StreamZo fix. HOTD S1E2 showed Purstream, StreamZo, Castle, VidRock, HindMoviez. Hell Mode S2E12 showed French-Manga/VoirAnime.homes and prompted Anime-Sama/Mugiwara follow-up.
- Desktop user logs showed VidRock only for Interstellar/HOTD and playback not launching; Hell Mode S2E12 zero. Changing work reset streams correctly, so do **not** generalize the TV stale/late-stream symptom to Desktop.
- macOS real-device root cause is external to provider extraction: immediately before failure logs show `Non-C locale detected. This is not supported.` and then `mpv_create failed`. Upstream NuvioDesktop `player_bridge.mm` calls `mpv_create()` while libmpv requires `LC_NUMERIC=C`. Correct upstream fix is to ensure `setlocale(LC_NUMERIC, "C")` before `mpv_create()` with thread-safety/restoration care. NiakVIO connector cannot push upstream, so this is an external blocker and must not be hidden by a Lab-only environment hack.

### Global Core/presentation/runtime corrections already established
- Final Core order for presentation path is `CORE.STREAM_PRESENTATION.V1 -> CORE.STREAM_SANITIZER.V6 -> CORE.RUNTIME_MEDIA_SAFETY.V4 -> CORE.PROVIDER_BRANDING.V1`; branding runs after sanitizer/safety so visible quality/title reflects final stream facts.
- Language/badge logic is evidence-only from structured stream fields (`language`, `languages`, `languageTracks`, `audioLanguage`, `audioLanguages`, `audioTracks`). Provider catalogue fallback/title-name inference must not invent VF/MULTI. `French Dub` label alone cannot create VF. Audio VF + VOSTFR subtitle remains VF audio + VOSTFR subtitle, **not** fake MULTI.
- Branding removes Unknown/Inconnue quality placeholders and builds deterministic provider/final-quality visible title while retaining source facts separately.
- Runtime contract docs were enriched with per-device differences and anti-inference rules: extraction/client projection/player readiness are independent; exhaustive red != provider-wide failure when count>0 exists; TV late/stale symptom is not generalized to Desktop; client-visible quality is post-sanitizer; language/badges require stream-level evidence.
- Core timeout remains 25 s. A→B→C stale-generation suppression and HTTP 403 fail-closed remain mandatory.
- StreamZo generic quality recovery recognizes `s2160p`; Interstellar live proof reached **2160p/4K** after bundle rematerialization.

### Anime / 4K facts that must not be forgotten
- Anime-Sama Hell Mode S2 had **11 published episodes** at audit time. S2E12 was therefore an invalid Anime-Sama regression fixture. Valid **S2E11** probe returned **2 VOSTFR 1080p streams, 2/2 playable, identity match**. Never condemn a provider using an episode beyond its current site publication count.
- Mugiwara old `/api/search?q=` now returns 403. Current frontend contract is same-origin `/api/suggest/lookup?q=` with browser-like headers (`Referer`, `Sec-Fetch-Site:same-origin`, `Sec-Fetch-Mode:cors`, `Sec-Fetch-Dest:empty`); cookies are **not** required. Discovery must happen before stale native search to avoid consuming the network budget.
- Mugiwara player contract changed again: page exposes `SCRIPT_URL`, then frontend calls `/api/episodes-script/version?url=...` and `/api/episodes-script?url=...&filever=...`; response defines `eps1..eps4` (bounded parser, do not execute remote JS). Hell Mode S2E11 was proven through this current chain with a terminal **1080p VOSTFR HLS**.
- UHDMovies: Interstellar 4K page exists, but current public cloud handoff reaches a generic/stale destination with no media handoff. Treat as source/coverage debt; do not force stale links.
- 4KHDHub: current search route did not expose a real Interstellar target anchor. Treat as resample/current source drift, not a proved provider success.
- StreamZo Interstellar source contains an `s2160p` HLS path; quality recovery now maps it to 2160p and live proof showed terminal 4K.

### Non-display/provider recovery — exact evidence and current scope
- Historical ZERO/quarantine ledgers are evidence only; re-prove against current bytes. VidRock is the key counterexample: old ZERO ledgers are stale because native Android/iOS/Desktop later proved count>0.
- A targeted parity sweep over 18 active suspects was built with 3 samples/lane and terminal verification. Current persisted ledger before the newest AnimeSamaCo retry: **FULL=4, RESAMPLE=6, ZERO=8, REGRESSION=0** after semantic guard corrections.
- FULL controls: `animevostfr`, `neko-sama`, `voiranime`, `voiranime-rip`.
- RESAMPLE: `4khdhub`, `allanime`, `coflix`, `sekai`, `showbox`, `wookafr`.
- ZERO: `allwish`, `animesalt`, `animesama-co`, `flemmix`, `moviebox`, `moviesmod`, `vidfast`, `vidlove`.
- Exact inventory run on diagnostic branch: **35142139141**. It proves the above counts and per-provider HTTP/error state.

### Six earlier proved regressions and clean-room recovery
- The 18-provider sweep originally found six certain NiakVIO regressions: `animesama-co`, `animevostfr`, `coflix`, `neko-sama`, `sekai`, `voiranime-rip`; `voiranime` had already become positive.
- Exact fixtures used included High School DxD (`45950`), JJK (`95479`), Thor (`10195`), HOTD (`94997`), My Hero Academia (`65930`), Spy x Family (`120089`).
- Clean-room recovery Legos were added; they reproduce observed HTTP contracts only and pass embeds/players through NiakVIO’s bounded direct-media crawler rather than copying upstream source or returning HTML player URLs as streams.
- AnimeVOSTFR/JJK and Coflix/HOTD were proven positive early. Neko was fixed by correcting a syntax error in the shared V2 block and later became FULL positive. VoirAnime itself remains FULL positive.
- Sekai current upstream/site uses sitemap/page/Sibnet rather than the old `/api.php?tmdb=...` model. VoirAnime.rip current route is search -> season/episode -> Sibnet. Neko current path is WordPress/page -> player -> Vidmoly. These are distinct route families, not one generic display bug.

### Coflix semantic guard / Thor false-positive finding
- Coflix authority is `coflix.wiki`; old `coflix.group` authority was stale for the proved route.
- Coflix HOTD became terminal-positive. Thor remained local 0 while upstream reported 1.
- Detailed same-run tracing proved the upstream “Thor” terminal player correlated only to Coflix results `hulk-vs-thor-*`, not **Thor (2011)**. The upstream Vidzy mirror used `vidzy.live` while site result used `vidzy.org`; canonicalize those two embed hosts for correlation only, never the CDN `u14.vidzy.cc`.
- Semantic guard is **fail-closed**: it downgrades `upstream_ok_niakvio_ko` only when it can replay provider search/players and prove the upstream terminal belongs to a different work. Otherwise the regression remains red.
- Targeted semantic proof run **35134942553** succeeded and classifies this as `upstream_semantic_untrusted` / `correlated_different_work`.
- Do **not** resurrect the discarded Coflix Referer/Origin/UA V2. Real `thor-vf` Livavid discovery returned a signed HLS that was 403 immediately even in-process with Referer+Origin+matching UA. This did not produce a valid terminal and was correctly removed from production.

### Current AnimeSamaCo exact regression and newest repair attempt
- Secured publication candidate run **35140246168** reached the seven-route live parity after HTML-security/fixed-point hardening and found one genuine exact regression left: `animesama-co` High School DxD S1E1 local=0 while upstream=1 terminal. The other exact routes passed / were semantically trusted.
- Root differential: NiakVIO recovery parsed only Sibnet `shell.php` URLs from the episode page, while current upstream also parses inline `videoUrls` / `filmUrls` objects and default iframe players. A non-Sibnet player therefore made Niak return 0 even though upstream could resolve media.
- New recovery upgrade on branch adds `NIAKVIO_ANIMESAMACO_PLAYER_DISCOVERY_V2`: parse bounded inline `videoUrls|filmUrls` and iframe `src`, dedupe with Sibnet candidates, then pass all candidates through existing `_crawlDirectMedia`; never return player/embed HTML directly as a stream.
- Source upgrade commit: **af8d9abcc7a27fca8a152ed14f40dc2c0a74a0f8**; contract test commit **266a3df054744def5659ac57cf5aa729eb138fae**.
- Retry workflow commit: **a13aed1d878b0c5778f36843b79c59bf1fc3007a**. Run **35141628131** is the authoritative secured retry. At the moment this memory checkpoint was staged: source/ownership/security step was green; reapply/security/minimizer/fixed-point step was still running. Do not infer the live DxD verdict until step 9 finishes.
- Because this memory checkpoint intentionally moves the repair branch, the running transaction may later fail its final CAS/push even if all proofs are green. If so, **do not redo diagnosis**: rerun/persist the already-proved candidate on the new branch head.

### HTML security + minimizer facts
- Provider HTML-cleaning regexes like `/<[^>]+>/`, regex stripping of `<script>`/`<style>` are forbidden in published provider code by the security gate.
- The attempted separate V3 HTML-security Lego was rejected correctly because it mutated V1-owned code outside its own marker block. Correct architecture: patch the owner `non_display_recovery_runtime_v1.py` itself, then rematerialize its provider-owned V1 blocks.
- Owner-source hardening replaces HTML regex stripping with a deterministic character scanner that skips tag contents and script/style blocks; tests cover both source and published 46 bundles.
- Final safe minimizer currently **is not a true JavaScript minifier**. `scripts/provider_v3_minimizer.py` explicitly sets `TERSER_ALLOWED=False`, does not rename identifiers/fold/reorder expressions, and only removes safe indentation/trailing whitespace/blank code lines/unmanaged full-line comments. Visual output therefore remains close to readable multi-line authoring.
- Desired future optimization is **minification level 2**: compact whitespace/newlines aggressively (potentially one line), preserve identifiers and all NiakVIO/NUVIO/STARTFIX/CLOSEFIX/FIXDATA/provider-envelope markers, no mangling/obfuscation initially. Goal is smaller/faster provider payloads while keeping Lego edit/rebuild/remove deterministic.
- Marker patching itself is content-based, not absolute-position based. `provider_patch_blocks.py` finds `BEGIN/END NIAKVIO_PROVIDER` and exact `STARTFIX/CLOSEFIX` marker content using searches/regex/cardinality checks and computes owned spans dynamically; replacing/deleting an existing Lego does **not** depend on original line numbers/offsets.
- One blocker before true one-line minification: clean-v3 insertion of a **new** Provider/Core Lego currently requires a line boundary (`before.endswith("\n" or "\r")`). Before enabling level-2 one-line minification, change this contract to a marker/whitespace-safe boundary and add tests for insert/replace/delete/reverse-rebuild on fully compacted provider bytes. Do not enable strong minification until these tests + `node --check` + fixed-point + live/native parity prove no behavioral drift.

### Maximum-repair queue — exact current plan
1. **`animesama-co`** — current exact regression; finish DxD proof first using retry run 35141628131.
2. **High-repairability ZERO because local reaches HTTP 200**: `flemmix`, `moviebox`, `vidfast`, `vidlove`, then `moviesmod`. Diagnose site-direct route/player/terminal even when upstream is 403/429. These are more promising than pure anti-bot failures because Niak already reaches the site.
3. **RESAMPLE with HTTP 200 / likely fixture-capability issue**: `4khdhub`, `allanime`, `showbox`, `sekai`. Choose works known to exist on the current site; if terminal exists upstream/site and Niak misses it, repair route/parser. If the declared lane is not truly covered, correct capability instead of inventing streams.
4. **`coflix`**: movie + TV already positive. Re-evaluate whether anime capability is actually legitimate; if not, remove/correct the anime capability. Do not manufacture anime coverage.
5. **`wookafr`**: current local traces show no requests while older macOS logs showed DNS failure. Prioritize domain/authority refresh and direct-site discovery.
6. **Hard anti-bot cases**: `allwish`, `animesalt`. Current local samples often hit 403. Reproduce browser/site contract; if browser works but CI remains blocked even with legitimate same-origin headers/session-independent routes, classify as external runner/site anti-bot limit rather than fake provider success.
7. Maintain FULL controls (`animevostfr`, `neko-sama`, `voiranime`, `voiranime-rip`) and previously proved StreamZo/Mugiwara/Anime-Sama valid-episode routes as non-regression sentinels while repairing the queue.
8. Exit condition for “maximum reparable”: every ZERO/RESAMPLE must end as either (a) terminal media positively proved, (b) capability corrected to match real site coverage, or (c) external/site/CDN/anti-bot impossibility documented with direct evidence. `0/0` alone is never a final verdict.

### Exact residual HTTP inventory from run 35142139141
- `4khdhub`: RESAMPLE; movie/tv samples 0/0 with HTTP 200 both sides. Needs real catalogue fixture and 4K-specific probe.
- `allanime`: RESAMPLE; anime samples 0/0 HTTP 200. Needs current catalogue fixture.
- `allwish`: ZERO; local often 403 (sometimes 200 then 403), upstream absent/403. Anti-bot/terminal chain investigation.
- `animesalt`: ZERO; local 403 or 200->403, upstream no stream. Historical browser had page/player 200 while runner 403; prioritize browser-vs-runner contract.
- `animesama-co`: ZERO in old 18 ledger; now separately exact-regressed on DxD and under active V2 recovery retry.
- `coflix`: RESAMPLE overall but **positive movie Interstellar** and **positive TV Squid Game/HOTD**; anime lane remains 0/0 and may be invalid capability.
- `flemmix`: ZERO; local HTTP 200 on movie/tv while upstream often 403. High repairability; site current authority observed upstream config `https://flemmix.me` with search + sitemaps + `minochinos` player selectors, but Niak historical DATA/domain must be rechecked before mutation.
- `moviebox`: ZERO; local frequently HTTP 200 while upstream 429. High repairability; investigate parser/player without relying on rate-limited upstream.
- `moviesmod`: ZERO; local 200/403, upstream 403. Medium repairability; likely player/CDN/anti-bot chain.
- `neko-sama`: FULL positive; AoT terminal local while upstream timed out.
- `sekai`: RESAMPLE; 0/0 with HTTP 200 (one 400). Needs current site catalogue fixture/player proof.
- `showbox`: RESAMPLE; local HTTP 200, upstream no useful network evidence. Needs current catalogue fixture/player proof.
- `vidfast`: ZERO; local HTTP 200, upstream 403. High repairability.
- `vidlove`: ZERO; local HTTP 200, upstream 403. High repairability.
- `voiranime`: FULL positive; Maid-Sama terminal both sides.
- `voiranime-rip`: FULL; Hunter x Hunter terminal local while upstream timeout; Dan Da Dan upstream advantage remained unconfirmed/flaky, not a certain regression.
- `wookafr`: RESAMPLE; local no recorded request/status, upstream 200/403 or 404. Domain/authority/plan investigation first.

### Final completion sequence after maximum repair
1. Persist final candidate bytes and durable source Legos; remove all temporary diagnostic workflows/scripts/branches.
2. Run all PR gates on the exact final SHA: Quick Verify, Provider Non-Regression, Provider Overrides, Media Type & Playback, Workflow Gate, CodeQL/security as applicable.
3. Merge PR #122 only with expected final head SHA.
4. Run `CORE - Finalize Accepted Release` on exact merged `main` SHA; let it determine the actual release number (expected next generation may be 5.21.49, but never invent it before workflow output).
5. Verify public root/VF/no-anime/VF-no-anime manifests, Hub46 projection and release hashes from final `main`.
6. Post-release focused probes: Hell Mode valid published episode for Anime-Sama + Mugiwara (S2E11 remains known valid; S2E12 only if site has published it by then); Interstellar on StreamZo plus 4KHDHub/UHDMovies/current 4K candidates; re-check quality/language/title presentation.
7. Record final merge SHA, release SHA/version, run IDs, remaining external blockers and maximum-repair verdict in a second final `MEMORY.md` checkpoint.
