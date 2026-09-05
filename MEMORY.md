# NiakVIO — Recovery Memory

Last authoritative rewrite: 2026-09-05.
This file is the recovery source of truth if ChatGPT/session context is lost. Prefer current repository state over older chat summaries. Older retry-by-retry history remains in Git history; this file intentionally records current architecture, non-negotiable product decisions, active branches, proven regressions, current route/DATA work and exact completion order.

## Branch safety / current topology
- Production baseline is `main`.
- Current active development branch for route/DATA recognition: `workbench/provider-v3-recognition-routes-data`.
- Draft PR for the current recognition lab: PR #89, `workbench/provider-v3-recognition-routes-data` -> `main`.
- The earlier runtime/yield workbench was `workbench/provider-v3-performance-playback`; do not assume it is still the active write target after the route-recognition branch was cut.
- DO NOT write directly to `main` while the current workbench is incomplete.
- Reconstruction may commit only to a selected non-main workbench branch.
- Before deleting branches/PRs, ensure no code, DATA, docs or generated artifacts needed for the final main state are left behind.

## Non-negotiable execution method
- User expects complete execution, not a plan or a partial diagnosis.
- Do NOT ask for confirmation when the next implementation/test step is already implied by the task.
- Do NOT stop after one edit, one green test, one workflow or one reconstruction.
- For every candidate SHA, collect all visible failing jobs when practical, group failures by common root cause, then batch the correction.
- Avoid the wasteful loop `one failing test -> one tiny fix -> expensive rebuild -> discover next test`.
- Use cheap/unit/structural gates before another expensive 96/96 materialization or native Lab run.
- When a newer reconstruction request supersedes an older one on the same branch, cancel/replace the stale run rather than letting it hold the branch.
- If a tool/run fails, diagnose it, try a correction/alternate route and continue.
- Before declaring completion, re-check the user request and explicitly account for every requested deliverable.

## Absolute current priority — ROUTES / DATA
The user explicitly re-confirmed on 2026-09-05: **routes are always the priority**.

Order of attention while provider yield is weak:
1. recover/validate executable provider routes and business protocol DATA;
2. recover request semantics (GET/POST, body fields, form/JSON encoding, Referer/Origin, response kind, dynamic path construction);
3. recover provider identity/type requirements;
4. materialize clean ProviderBase + DATA + Lego;
5. run yield/playback verification;
6. only then spend significant time on secondary docs/diagrams/cleanup.

Do not let documentation, style cleanups or green structural checks distract from missing route/protocol DATA.

## Primary target
- Catalogue target: ALL 96 providers, including disabled/off providers for structural completeness and future recoverability.
- A low live yield such as 3/96, 7/96 or 10/96 is a systemic regression, not an acceptable release state.
- Do not focus only on Kehflix/Castle/StreamZo/Purstream or any small currently-working subset.
- Objective is maximum real usable provider count, then official native client/playback acceptance.
- A provider returning zero streams in one request should not automatically be globally disabled.
- Stream-level failures must not globally disable a provider.
- Quarantine only when NiakVIO has sufficiently strong evidence that a provider cannot safely execute; never use quarantine to hide missing reconstruction logic.

## Provider v3 architecture
A generated provider is composed from:
1. clean ProviderBase v3;
2. structured provider DATA;
3. provider-owned `PROVIDER.*` Lego;
4. shared `CORE.*` Lego.

Hard rules:
- Historical/upstream/published provider JS is knowledge/reference only, never an executable reconstruction seed.
- ProviderBase is conceptually immutable/clean; provider-specific behavior belongs in DATA or owned Lego rather than ad-hoc corruption of the base.
- Provider envelope markers are mandatory:
  - `/* BEGIN NIAKVIO_PROVIDER */`
  - `/* END NIAKVIO_PROVIDER */`
- Provider Lego precedes exactly one Core boundary.
- Core Lego follows that boundary.
- Managed Lego uses STARTFIX/CLOSEFIX + FIXDATA ownership.
- Reverse reconstruction must remain deterministic/byte-verifiable.
- No Terser.

Conceptual provider envelope previously agreed with the user:
```text
BEGIN PROVIDER
  if provider is selected / launchable
    if this provider protocol requires TMDB metadata before its first provider call
      resolve/cache TMDB data first
    endif
    run provider DATA/Core protocol
    if streams > 0
      run provider/core stream fixes and presentation
    endif
  endif
END PROVIDER
```
This is a logical contract, not permission to add unnecessary TMDB calls.

## Provider taxonomy
Use the existing architecture taxonomy; do not invent a parallel provider type system:
- `official_domain_hub`
- `api_stream_resolver`
- `html_scraper`
- `mixed_embed_resolver`
- `direct_media`
- `iframe_player`
- `quarantined`

Last structurally validated quarantine set was five providers:
- DVDPLAY
- MOVIEBOX
- NETMIRROR
- TOPCARTOONS
- VIXSRC

Frenchstream is NOT a permanent quarantine.
- maintenance/address hub: `https://fstream.website/`
- actual provider protocol: DLE-style search/detail/player business flow.
- Hub supplements/locates the active service; it must not blindly replace provider protocol DATA.

## Canonical media type vs Nuvio transport — CRITICAL
Never collapse semantic capability and client transport into one field.

### Canonical capability
`canonicalSupportedTypes` describes WHAT the provider catalogue semantically serves:
- `movie`
- `tv`
- `anime`

An anime-only provider can correctly have:
- `canonicalSupportedTypes = ["anime"]`

Do NOT add ordinary `movie` semantic capability merely because anime films launch through movie-shaped transport.

### Nuvio launch compatibility
`supportedTypes` is the transport/launch surface consumed by Nuvio.

Anime providers MUST be compatible with:
- `anime`
- `tv` for episodic anime / Nuvio series-shaped requests
- `movie` for anime films present in anime catalogues

Therefore this is valid and intentional:
- `canonicalSupportedTypes = ["anime"]`
- `supportedTypes = ["anime", "tv", "movie"]`

`movie` here is transport compatibility, NOT permission to return arbitrary non-anime movies.
Authoritative TMDB/canonical classification must still reject non-anime works for anime-only providers.

Client aliases:
- `series`, `show`, `other` normalize to TV-shaped input.
- Anime may be discovered from trusted TMDB metadata and then transported through the real TV/movie namespace.

Castle example: semantically/movie+tv provider; anime requests must not be accepted merely because anime can alias to TV transport elsewhere.

## TMDB / identity contract
Official Nuvio provider signature remains conceptually:
- `getStreams(tmdbId, mediaType, season, episode)`

Core owns TMDB metadata resolution/cache and normalized identity context.
Important gates:
- Provider capability/type gate must happen before network work.
- Non-launch provider events return `[]` before provider/network work.
- Zero-output providers should not pay unnecessary TMDB work unless their declared DATA plan requires metadata BEFORE execution.
- Catalogue/title/external-id plans may require TMDB preflight.
- Ordinary direct plans can run first and pay canonical verification only when needed.
- TMDB metadata cache must be request-safe and must not leak media context between works.
- External IDs such as IMDb must be retained/exposed when provider protocol needs them.
- Provider JS/runtime receives TMDB identity from Nuvio/Core; do not redesign around arbitrary user-supplied title strings as the primary API contract.

## Source repositories are references, not runtime dependencies
The user explicitly does NOT want NiakVIO to become dependent on the three historical provider repositories.

Observed repository layouts:
- Gowaru: real provider-local modular source exists (`src/<provider>/extractor.js`, `http.js`, `index.js`, config/build); useful as knowledge when available.
- Yoru: template branch exposes `_template` interface files plus compiled provider bundles; template describes method/interface, not provider-specific route DATA.
- All-in-One: mostly compiled/obfuscated `providers/*.js`; not a proper reusable source tree.

Architectural rule:
- These repositories may be consulted during research/recovery, but **production reconstruction and durable Provider v3 recognition must work from NiakVIO-owned DATA/observations/materialized contracts**.
- Do not require Gowaru/Yoru/AIO network access during ordinary 96/96 reconstruction.
- Do not identify runtime behavior by repository name.
- Do not embed or execute their JavaScript.
- Once useful behavior is understood, persist the route/request/identity contract in NiakVIO DATA and make that the durable authority.

## Route recognition skill — generalized Kehflix requirement
The user explicitly asked for a genuine generalized route/type/data recognition skill similar to the manual reverse coding that recovered Kehflix, not shallow literal grep and not provider-by-provider hardcoding.

Recognizer must understand, statically and safely:
- literal routes and full URLs;
- template strings;
- string concatenation such as `BASE + '/browser?keyword=' + encodeURIComponent(query)`;
- routes assigned to variables before `fetch(variable)`;
- dynamic suffixes such as `selected.url + '/ep-' + episode`;
- dynamic hosts such as `'https://' + workerDomain + path` while retaining provider path DATA separately;
- GET/POST/PUT/PATCH/DELETE where observable;
- form encoding / URLSearchParams;
- JSON body encoding;
- body field names;
- Referer / Origin requirements;
- JSON vs HTML/text response evidence;
- search/detail/player/source/episode-index route roles;
- TMDB/IMDb/title/season/episode identity dependencies;
- movie/tv/anime evidence;
- safe bounded static decoding of common obfuscated string tables, without executing JS;
- garbage-route rejection (`resolvers.js`, assets, admin/login/oEmbed, HTML data attributes, etc.).

Fail closed on truly missing executable plans; do not invent routes.

## Current route-recognition implementation — 2026-09-05
New NiakVIO modules on `workbench/provider-v3-recognition-routes-data`:
- `scripts/provider_route_expression_analyzer.py`
  - static expression/concatenation analysis;
  - fetch-variable recovery;
  - POST JSON/form + body fields + Referer/Origin evidence;
  - consumes bounded static decoded strings from NiakVIO discovery decoder;
  - never executes provider JavaScript.
- `scripts/provider_route_role_classifier.py`
  - extends route-role classification, including `VideoPlayer.html`-style player paths.
- `scripts/provider_route_normalization_guard.py`
  - preserves `{query}` / `{episode}` placeholders through legacy normalization;
  - rejects HTML attributes such as `/data-video=` as fake routes.
- `scripts/provider_contract_local_enricher.py`
  - production/local-only contract enrichment from NiakVIO durable knowledge + seeds + overrides;
  - no external provider-repository HTTP request.
- `automation/provider-v3-recognition-seeds.json`
  - NiakVIO-owned reviewed route/request seeds for contracts that were recovered and must survive external source disappearance.

Compatibility entry point:
- `scripts/enrich_provider_v3_static_knowledge.py` now routes ordinary enrichment through the local-only enricher rather than the external-source recognizer.

Tests:
- `tests/provider_contract_recognizer_test.py` covers Gowaru-shaped modular requests, template-interface no-route behavior, DLE/Frenchstream, Kehflix title->player->streams, compiled bundles, AnimeKai-shaped concatenation, AnimeZey-shaped POST JSON helper/worker route, bounded string decoding, Anime-Ultime player classification and junk-route rejection.
- The test is invoked from `tests/provider_v3_strategy_plan_contract_test.py`, so it is part of the real Quick/reconstruction gate rather than a decorative test.

## Exact recent recognizer/reconstruction history
Earlier source-aware recognizer commits on the predecessor workbench:
- `c0b2c34a...` — add provider contract recognition skill.
- `34cf73bc...` — compatibility wrapper.
- `90f5fce3...` — recognizer tests.
- `a69b5276...` — wire recognizer test into strategy gate.
- `5ec1ef303efdb0725713da6f1f262d734b6a9920` — migration-idempotence fix.

Runs:
- reconstruction #81, run `33942206137`: failed before recognizer because cumulative source-plan migration expected canonical source text; fixed by restoring migration-compatible classifier shape.
- reconstruction #82, run `33942264556`: reached recognizer and intentionally fail-closed on exactly three providers with no executable recognized route at that point:
  - `animekai`
  - `animezey`
  - `anime-ultime`

This failure was useful evidence, not a reason to quarantine the providers.

## Recovered routes/contracts for the three fail-closed providers
### AnimeKai
Recovered business chain:
- base known at recovery: `https://www3.anikai.cc`
- catalogue search: `GET /browser?keyword={query}`
- result page: `/watch/{slug}`
- episode page: `/watch/{slug}/ep-{episode}`
- episode HTML contains player/embed `data-video` values;
- embed/player page then yields stream media, commonly HLS.

Important recognizer lesson:
- `/data-video=` is an HTML attribute, NOT an HTTP route.
- concatenation/variable analysis is required because important AnimeKai paths are not always one quoted literal.

### AnimeZey
Recovered contract:
- worker-domain search API rotates between NiakVIO-known worker origins;
- search route recovered as `/1:search`;
- method `POST`;
- JSON body;
- episode search fields: `q`, `page_token`, `page_index`;
- movie search at minimum requires `q`;
- Referer required by observed request contract;
- result paths can resolve through returned worker player paths and/or `/download.aspx`;
- download path may carry `file`, `expiry`, `mac` query material.

Durable NiakVIO worker-origin DATA currently seeded:
- `https://1.animezey23112022.workers.dev`
- `https://1.animezeydl.workers.dev`
- `https://animezey16082023.animezey16082023.workers.dev`

Do not hardcode this provider into the generic recognizer; persist these as DATA and let generic request/route machinery execute them.

### Anime-Ultime
Durable NiakVIO DATA already contained player evidence such as:
- `/VideoPlayer.html`
- `/VideoPlayer`

The missing piece was route-role recognition, not justification for another repository dependency. `VideoPlayer.html` must classify as player/executable route evidence.

## Durable DATA quality rules
- `model.routes` is executable route DATA and must be aggressively clean.
- `knowledge.routes` / `routeFragments` may retain useful diagnostics, but junk/infrastructure routes should still be pruned.
- Never emit source filenames or helper assets as executable routes.
- `resolvers.js` is not a provider request route.
- `/wp-json/oembed/...`, admin/login endpoints and image/css/font assets are not executable provider media plans.
- HTML attributes such as `data-video` are extraction evidence, not routes.
- Route placeholders must remain syntactically complete, e.g. `{query}` not `{query`.
- Persist method/body/header semantics when known instead of reducing every route to generic GET scraping.

## Source-plan/runtime recovery families
Systemic losses found during Provider v3 reconstruction were not just dead domains:
- business protocols were flattened into generic scraping;
- generic crawler ordering could waste budget on feeds/comments instead of download intermediates;
- JSON APIs were treated as generic media URLs;
- corrupted/templated routes survived into executable DATA;
- source-family classification selected wrong handlers;
- dynamic/concatenated URLs were missed;
- POST/headers/body semantics were lost.

Known family examples:
- Frenchstream: DLE POST search -> detail/news id -> movie/season/episode endpoints -> players; TV historically uses `get_seasons.php` and `eps_<id>.txt`-style data.
- Kehflix: title -> player -> `/api/streams/...` chain; recovered manually and used as the model for generalized route recognition.
- Anime-Sama: catalogue search POST -> typed `/catalogue/.../episodes.js` routes -> provider player resolution.
- MoviesHunt/HindMoviez/MoviesMod/UHDMovies/4KHDHub family: search/detail -> Abhilinks/HubCloud/VCloud/Driveseed-style intermediates -> final host.
- JSON stream-API family: source response objects must be converted to Nuvio stream rows after correct identity resolution.

Fix families/shared Core where possible; do not hand-patch 89 providers when one lost protocol explains many reds.

## Yield checkpoints
Historic baseline:
- Fast-yield run `33927727936` on reconstructed v5: about 7/96 unique providers playable.

Later shared runtime/source-plan work improved the fast-yield baseline to roughly 10/96 unique providers playable, still far below target.
At that checkpoint, approximately 86/96 providers produced no playable result and the dominant systemic families were generic `catalogue-html` / `catalogue-html-embed`, proving route/protocol recovery remained the main problem.

Therefore:
- never describe 10/96 as success;
- every new yield comparison must run against the exact newly reconstructed bot SHA;
- a structural 96/96 generation without materially improved live yield is not completion.

## ProviderBase/source-plan runtime checkpoints
Important predecessor commits:
- `e7b02f20...` — ProviderBase v7 source plan upgrader.
- `42a0261e...` — deterministic DLE source-plan parser.
- previous green reconstruction bot commit before the new recognizer: `b872a18b...`.

The current route/DATA branch exists because runtime improvements alone were insufficient while DATA still lacked executable routes/protocols.

## JSON stream-API family clarification
Some providers expose a JSON `streams[]`-style API. This is a SOURCE API contract, not a change of target client.
Nuvio remains the target runtime/client.
Do not describe the work as "moving to Stremio"; adapt those source JSON responses into Nuvio stream objects.

DesiFlix/Persian-style observation showed 200 responses with zero output when provider identity was wrong/fell back to raw TMDB.
Earlier commit `0691e922` added a path that can obtain external IMDb identity from Core TMDB metadata before calling those source APIs.
This still requires validation on the exact final reconstructed generation/yield.

## Native Labs
Final acceptance surface is exactly five first-class client/platform Labs:
1. TVAndroid — official NuvioTV
2. MobileAndroid — official NuvioMobile
3. MobileIOS — official NuvioMobile
4. DesktopMACOS — official NuvioDesktop
5. DesktopWindows — official NuvioDesktop

Labs are observational evidence only:
- no provider reconstruction;
- no repair;
- no mutation of Nuvio clients to manufacture greens;
- preserve reader/player errors;
- save/keep Labs open where possible to avoid repeated expensive startup;
- use the fastest path to the exact provider/work playback evidence under test.

Do NOT launch the full five Labs while shared 96-provider route/runtime/yield is still structurally weak. First get reconstruction + fast yield credible, then use Labs for native proof.

## Playback / reader integrity
Kehflix previously produced `Cannot find sync byte / parsing_container_malformed` on a real playback path.
Shared HLS Core therefore needs bounded first-segment/container proof:
- preserve Referer/Origin;
- validate MPEG-TS sync or fMP4 structure when bytes are readable;
- reject positive HTML/JSON/malformed container evidence;
- network uncertainty/encrypted HLS remain non-blocking;
- stream-level failures must not disable whole provider.

Final acceptance must inspect actual reader/player logs, not only provider result counts or green workflows.

## Runtime platform contract
Authoritative comparison document:
- `automation/PLATFORM-RUNTIME-CONTRACTS.md`

Key differences that matter:
- all clients execute JS through QuickJS-compatible native runtimes;
- Android/TV and Desktop/iOS fetch bridges differ;
- TV lacks some capabilities exposed elsewhere; TextEncoder/TextDecoder/WebAssembly gaps have historically mattered;
- transport/header/subtitle/description/name projection differs by client.

Whenever official Nuvio client refs change, re-audit the platform contract rather than guessing.

## Minifier
- Terser is forbidden.
- `scripts/provider_v3_minimizer.py` is the NiakVIO-aware conservative minimizer integrated into materialization.
- It must preserve BEGIN/END provider envelope, STARTFIX/CLOSEFIX/FIXDATA, Core boundary and ownership comments.
- It must adapt safely to comments/owned markers rather than global textual replacements.
- It must not rename identifiers, reorder expressions, fold literals or perform unsafe transforms.
- Providers with risky template-literal state may remain byte-stable.
- Fixed-point + Node parse + reverse reconstruction + native parity are required.

## Security
The earlier ~25 CodeQL high alerts were traced to a shared unsafe HTML-filtering regex shape in generated provider code.
ProviderBase/Core moved to deterministic HTML scanners and published bundles must remain gated against reintroduction.
Before final merge:
- exact final 96/96 generated bytes pass HTML-filter security tests;
- npm audit/high dependency gate is clean;
- CodeQL/security is checked on exact final branch/PR SHA;
- distinguish GitHub security-agent/model infrastructure errors from actual NiakVIO findings.

## Workflow ownership
Routine workflow:
- `CORE - Verify & Publish` (`.github/workflows/sync.yml`)

Quick:
- static/runtime/unit safety;
- no reconstruction/repair.

Deep:
- broader read-only observation and report/manifest projection;
- still no provider repair/reconstruction.

Manual full reconstruction:
- `.github/workflows/provider-v3-reconstruct-all.yml`
- only path for full 96/96 materialization;
- non-main only for commits;
- rebuild from ProviderBase + NiakVIO DATA + owned Lego;
- reverse proof + runtime/integrity gates required.

Current route/DATA architectural change:
- ordinary reconstruction enrichment must be local-only and must not call Gowaru/Yoru/AIO.
- the old `refresh_static_knowledge` branch that refetched external provider repositories is being removed from the active reconstruction path.
- `finalize_gowaru_provider_v3_source_plans.py` must not be part of ordinary reconstruction because it refetches Gowaru; any still-useful knowledge must already be persisted in NiakVIO DATA.

LEARN:
- only automated code-evolution/repair owner;
- proposals/sandbox/PR flow, not silent production mutation.

Domain Refresh:
- only routine narrow DATA-write exception;
- official domain/config scope only;
- never a substitute full provider repair/reconstruction engine.

## Current active implementation checkpoint
Current branch commits added during the new route-recognition lab include:
- `c35f9f6d33ad7c647580790324f71cb6944b8735` — route role classifier.
- `06fb8ffa2a18e31d7a0af87a3b644bef67f806db` — placeholder-preserving normalization guard.
- `bcd1b1caa76775f91990e4e8a230fd896223835a` — install normalization/role handling in recognition tests/pipeline.
- `d10abd2e3e21b27e3254a669f36f7ffcda854198` — persist NiakVIO recognition seeds for AnimeKai/AnimeZey/Anime-Ultime.
- `1da4b5711b49838b8175df2a05b658ea04a4f6b5` — local-only Provider contract enricher.
- `ecf6c4d456bbc95cea1cde01595cfde447efda2d` — route compatibility entry point to local-only enrichment.

First Quick failure after adding expression analysis proved routes were recovered but legacy normalization truncated closing braces:
- observed routes: `/browser?keyword={query`, `/ep-{episode` plus junk `/data-video=`.
- the normalization guard was added specifically to fix this class globally.

Python CodeQL analysis for the first recognizer batch completed successfully; `CORE - Verify & Publish` then failed in the real recognizer test, which is expected useful gate behavior rather than a hidden failure.

## Completion order from this checkpoint
1. Finish conversion of `provider-v3-reconstruct-all.yml` to local-only route/DATA enrichment; remove ordinary external repository fetches.
2. Ensure the workflow tracks the current workbench branch and commits generated DATA/artifacts safely only there.
3. Run/observe Quick gates and collect all reds for the latest exact SHA.
4. Fix all known recognizer/local-enricher failures in a batch.
5. Trigger full 96/96 reconstruction on the current route/DATA workbench.
6. Require reverse rebuild + release/runtime/security integrity green.
7. Inspect generated durable DATA for at least AnimeKai, AnimeZey, Anime-Ultime, Frenchstream and Anime-Sama; verify route placeholders/roles/methods and ensure junk such as `resolvers.js` or `data-video` is not executable DATA.
8. Capture exact bot reconstruction SHA.
9. Run one fast-yield 96/96 census against exactly that bot SHA.
10. If yield remains weak, group every live failure by protocol/family and continue route/DATA/shared-runtime corrections; do not stop at a few providers.
11. Once yield is credible, run all five native Labs on exact bytes and inspect actual reader/playback evidence.
12. Fix native-specific/runtime/player gaps, then final security/docs/minifier/clean/PR/merge preparation.
13. Merge only when the final requested work is actually viable; after merge, clean obsolete branches/PRs without losing any required artifact.

## Never infer "done" from these alone
None of the following by itself means NiakVIO is finished:
- 96/96 files generated;
- reverse reconstruction 96/96;
- one green GitHub workflow;
- 3, 7 or 10 providers returning streams;
- a few working providers on one client;
- structurally valid manifests;
- a green recognizer unit test;
- a route list without playback proof.

Done means the full requested workbench is coherent, routes/protocol DATA are materially restored across the catalogue, live yield is materially restored, exact final bytes pass structural/security gates, and the five official Nuvio client Labs provide acceptable reader/playback evidence before merge.


## 2026-09-05 route/DATA recovery lock — run 33979458656 {#run-33979458656-route-data-recovery}
- This is the authoritative recovery checkpoint for route/DATA work after the original successful artifact was not persisted to Git.
- Source workflow run: `33979458656`, head SHA `b1891055fc0830f690bc6afa9f7d2708844a1394`.
- Recovered canonical snapshot contains all 96 providers and already carries the previously accumulated 1→18 state.
- Batch report itself covers providers 19→58: 40 processed, 17 final-bundle verified, 4 terminal-blocked, 19 defer-to-learn, 0 hard failures.
- Final-bundle verified in 19→58: `animesalt`, `animetsu`, `animevostfr`, `castle`, `cineby`, `cinemm`, `coflix`, `french-manga`, `hianime`, `kurage`, `moviesmod`, `neko-sama`, `playimdb`, `streamzo`, `toflix`, `videasy`, `vidfast`.
- Terminal-blocked in 19→58: `animesultra`, `animezey`, `cinemacity`, `movix`.
- `mugiwarastream` is a deliberate validated-DATA-retained/final-bundle-unverified case: keep its validated DATA while provider authority remains demoted until repaired.
- Exact recovered SHA-256: static knowledge `aab5f7eb12743c1beba7bf37148cb8428307fe3971c30dfe283d06f47ea28df5`; overrides `6f651b8b065438c70501877952653c3879c7baf189f5325231bad713e3f70b5a`; batch report `a0f30ce73d805c720a75d89836cc24fab7a2278c8c67575d1aaf97f322cb58db`.
- Durable report path: `automation/provider-v3-batch-checkpoints/run-33979458656-batch-019-058.json`.
- Do NOT rerun 19→58 merely because a chat/session is lost. Resume recognition at provider 59 unless explicitly auditing a regression.
- A route is validated DATA only after actual live HTTP execution. Static recognition, source inspection, seed data or inferred route shape alone remain candidate/diagnostic evidence.
- Every subsequent recognition batch MUST commit `automation/provider-v3-static-knowledge.json`, `provider-overrides.json`, its exact batch report checkpoint, and a MEMORY checkpoint before proceeding to another batch.
- Full Provider reconstruction is intentionally deferred until route/DATA recognition across the full 96-provider catalogue is complete.


## Route/DATA batch checkpoint run 33985303336 {#batch-run-33985303336-route-data-checkpoint}
- Range: 59→96; processed: 38; hard failures: 0.
- Final-bundle verified (12): `voiranime`, `wookafr`, `1shows`, `allanime`, `allwish`, `animevost-fr`, `dvdplay`, `fullanime`, `mallumv`, `moviebox`, `showbox`, `vidsrc`.
- Terminal-blocked (8): `animeworld`, `cinevibe`, `ctgmovies`, `fibwatch`, `onlykdrama`, `vidlove`, `vidnest-anime`, `vixsrc`.
- Deferred-to-learn (18): `voiranime-homes`, `voiranime-rip`, `vostfree`, `yflix`, `anime-ultime`, `cinefreak`, `einthusan`, `frenchstream`, `goatapi`, `gramcinema`, `kisskh`, `moonflix`, `mycima`, `netmirror`, `topcartoons`, `vidnest`, `waveanime`, `xpass`.
- Exact durable report: `automation/provider-v3-batch-checkpoints/run-33985303336-batch-059-096.json`. Canonical static knowledge and overrides were committed in the same checkpoint commit.
- Resume only after this Git checkpoint exists; never advance a recognition batch from artifact-only state.
