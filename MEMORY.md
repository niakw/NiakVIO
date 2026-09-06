# NiakVIO — Recovery Memory

Last authoritative rewrite/checkpoint: 2026-09-06.

This file is the durable recovery source of truth when conversation context is lost. Prefer the current repository state and exact GitHub Actions evidence over historical chat summaries. Git history remains the source for retry-by-retry detail; this file records architecture, product decisions, current fixes, exact release state, known failure families and the remaining completion sequence.

## Current repository topology

- Repository: `niakw/NiakVIO`.
- **Current and only active write target: `main`.**
- Durable Learning proposal branch: `brain-learning/proposals` is a passive proposal store, not a direct publication authority.
- PR #91 was a closed, superseded reverse-sync attempt and must not be merged.
- Historical `chore/secondary-clean-*` / `workbench/*` refs are not active write targets and must not appear in workflow triggers/current instructions.
- Before deleting any historical branch/PR, verify that no code, DATA, docs or generated artifacts needed for the final state exist only there.
- Last observed `main` HEAD before this MEMORY checkpoint was `2fb536f910474a6d98cd478e8c18e251357ff1a3`, a bot-only `chore(audit): refresh external AI audit logs [skip ci]` commit. Always re-read HEAD immediately before the next write because audit/workflow bots can advance it.

## Execution method

- Complete the requested task; do not stop at a plan, diagnosis, first edit, first workflow dispatch or first green test.
- Do not ask for confirmation when the next implementation/test step is already implied.
- Group failures by common root cause and batch corrections before expensive rebuilds.
- Use cheap structural/unit/security gates before expensive 96-provider materialization or Native Labs.
- If a tool or test fails, diagnose, retry or use an alternate path and continue.
- Never claim a test/workflow passed if it was not actually executed.
- Record important progress here as it happens because conversation state can be lost.
- Before completion, re-check every requested deliverable and exact final SHA.

## Current active priority — 2026-09-06

The active task is no longer secondary-clean-only. The user explicitly requested the **latest five Native Lab artifacts**, so a final five-platform pass is mandatory after the current harness/runtime fixes stabilize.

Current priority order:
1. fix NiakVIO-owned harness regressions exposed by latest official Nuvio client SHAs without patching official runtime behavior;
2. fix current stream presentation/title regression (`- Inconnu`) at the shared Core/Lego level;
3. reject demonstrably false/non-feature media such as the current Allwish ~20 s result for *Interstellar* without globally disabling the provider;
4. preserve/verify HLS audio-child integrity behavior;
5. finish exact CodeQL + dependency security proof on final candidate;
6. run the complete five Native Labs on one post-fix SHA and capture artifacts/outcomes;
7. finish DOCX sync/render QA, repository hygiene, final MEMORY checkpoint and exact-SHA validation.

Catalogue target remains **all 96 Provider Objects**, including disabled/off entries for census/recoverability. Never shrink the catalogue to improve a metric.

## Accepted release/version state

- Current accepted published release generation is **`5.21.32`**.
- Manifest version: `5.21.32`.
- 96/96 provider versions were synchronized to `5.21.32`.
- Movix was restored to `enabled: true` in the accepted version bump.
- Version bump commit: `643bcedd443b6eac0c7e61e974ab3a7e855f51a6`.
- That bump commit changed version/hash/projection metadata only; it did **not** change Provider JS bytes.
- Do **not** create `5.21.33` merely for docs/workflow/harness-only changes.
- If a later security/runtime/provider fix changes published Provider JS bytes, the affected published bytes must be revalidated and the accepted release finalization/version synchronization rerun.

### Durable release finalizer

The premature one-shot cache-bump behavior was removed. Accepted finalization is now durable and explicit:

- `.github/workflows/release-finalize.yml`
- `scripts/release_version_baseline.py`
- `tests/release_version_baseline_test.py`

Contract:
- finalizer runs only after the validation pile is accepted;
- takes an explicit accepted SHA;
- uses explicit baseline SHA or computes the oldest commit in the current release-version generation on first-parent history;
- does **not** repair, reconstruct or rematerialize providers;
- atomically synchronizes affected provider versions + manifest/global cache/release metadata + hashes/projections/integrity when published bytes changed;
- no provider/cache bump for docs/workflow/harness-only changes when published provider bytes are unchanged versus release baseline.

A historical temporary one-shot full-cache-bump workflow was removed by commit `c89d4e993da2f8c9b6038360b1d452a586a4a460`; never restore that premature model.

## Provider v3 architecture

A generated provider is composed from:
1. clean ProviderBase v3;
2. structured provider DATA/static knowledge;
3. provider-owned `PROVIDER.*` Lego;
4. shared `CORE.*` Lego;
5. conservative NiakVIO minimizer before content hashing.

Hard rules:
- published/upstream/historical Provider JS is knowledge/reference only, never a reconstruction seed;
- ProviderBase stays clean; provider-specific behavior belongs in DATA or owned Lego;
- managed Lego uses `STARTFIX` / `CLOSEFIX` and `FIXDATA` ownership where required;
- Provider Lego precedes exactly one global Core boundary; Core Lego follows it;
- reverse reconstruction must be deterministic and byte-verifiable;
- Terser is forbidden;
- runtime Provider JS is a specialized reader, not a crawler/Learning engine.

Conceptual runtime order:
```text
BEGIN PROVIDER
  gate provider selection/capability before network work
  if provider protocol requires TMDB metadata before first provider call
    resolve/cache needed identity first
  endif
  execute provider DATA/protocol plan
  if useful streams > 0
    run provider/core stream fixes, identity, presentation and sanitization
  endif
END PROVIDER
```

## Canonical media type vs Nuvio transport — critical

Never collapse semantic capability and client transport into one field.

`canonicalSupportedTypes` describes what the provider semantically serves: `movie`, `tv`, `anime`.

`supportedTypes` describes how Nuvio may launch the provider.

An anime-only provider may intentionally expose:
```json
{
  "canonicalSupportedTypes": ["anime"],
  "supportedTypes": ["anime", "tv", "movie"]
}
```

`tv` is transport compatibility for episodic anime and `movie` is transport compatibility for anime films. These aliases do not make an anime provider a generic movie/TV provider. Authoritative identity logic must still reject ordinary non-anime works. Castle-like generic movie/TV providers must not accept anime merely because anime can use TV-shaped transport elsewhere.

## TMDB / identity contract

Official Nuvio provider input remains conceptually `getStreams(tmdbId, mediaType, season, episode)`.

- capability/type gate before provider network work;
- non-launch events return `[]` before provider/network work;
- TMDB enrichment only when declared provider plan needs it;
- catalogue/title/external-id plans can require preflight identity before first provider call;
- direct plans should not pay unnecessary metadata work;
- identity/cache scoped safely by work/type/season/episode;
- IMDb/external IDs available when protocol requires them;
- zero streams never manufacture success;
- one broken stream never disables a provider globally.

## Source repositories: references, not runtime dependencies

Historical/provider repos such as Gowaru, Yoru and All-in-One may be consulted during reverse engineering, but production reconstruction must rely on NiakVIO-owned DATA, observations and contracts.

- do not require those repos during ordinary 96/96 reconstruction;
- do not embed/execute their Provider JS;
- persist learned request/route/identity behavior into NiakVIO DATA;
- source shape is provenance, not runtime taxonomy.

## Route recognition contract

Generalized recognition must statically/safely understand, where observable:
- literal URLs/routes;
- template strings/concatenations;
- variables later passed to fetch;
- dynamic paths/hosts while retaining meaningful provider path DATA;
- GET/POST/PUT/PATCH/DELETE;
- JSON/form bodies and body field names;
- `Referer` / `Origin` requirements;
- JSON vs HTML/text response evidence;
- search/detail/player/source/episode-index roles;
- TMDB/IMDb/title/season/episode identity dependencies;
- movie/tv/anime evidence;
- bounded static decoding of common string tables without executing JS;
- junk-route rejection for assets/helper/admin/login/oEmbed/HTML-attribute noise.

Fail closed on missing evidence. Do not invent routes merely because a shape looks plausible. Durable route/protocol ownership is `provider.model.routeData`; other projections are derived views.

## Important recovered provider examples

### Frenchstream
- Maintenance/address hub: `https://fstream.website/`.
- Hub locates/supplements the active provider; it does not replace the actual DLE-style search/detail/player protocol.
- Frenchstream is not a permanent quarantine.

### Kehflix
- Manual recovery proved title -> player -> `/api/streams/...` and became a generalized route-recognition reference case.

### AnimeKai
- Search route `/browser?keyword={query}`.
- Result/watch and episode paths dynamically assembled.
- `data-video` is extraction evidence, not an HTTP route.

### AnimeZey
- Search uses worker-hosted `/1:search` behavior with POST JSON and provider-specific request fields/Referer evidence.
- Worker origins are DATA and may rotate; generic recognizer must not hardcode provider.

### Anime-Ultime
- `/VideoPlayer.html` / `/VideoPlayer` are player route evidence; historic issue was role classification.

## Quarantine and provider health

Historically validated quarantine evidence included DVDPLAY, MOVIEBOX, NETMIRROR, TOPCARTOONS and VIXSRC, but quarantine is evidence-based and can change. Do not use it to hide missing reconstruction logic.

- missing route evidence means unknown, not automatically dead;
- zero streams from one request do not globally disable a provider;
- stream-level failures are not provider-level disable evidence;
- temporary timeout/fetch failure can be inconclusive.

## Runtime/player evidence

A `.m3u8` URL or `#EXTM3U` response is not proof of native playback. Keep distinct:
1. extraction;
2. identity;
3. request context/headers;
4. playlist/variant resolution;
5. media/container integrity;
6. official native player outcome.

HTML/JSON disguised as media or positively malformed transport/container data can be rejected. Temporary fetch failure, unsupported diagnostic byte access or encryption is not automatically provider-wide failure.

### HLS audio integrity fix retained

The accepted published providers still contain the shared HLS integrity logic that validates separate HLS audio children rather than accepting a master solely because its video playlist parses.

- source patch: `scripts/provider_patches/hls_runtime_integrity_v1.py`;
- published providers include `/* STARTFIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */`;
- shared helper includes `audioUris(...)` and validates `TYPE=AUDIO` child playlists;
- this addresses the class of native playback failures where a master exists but its referenced audio track is broken/missing;
- do not regress/remove this while fixing presentation or Allwish false media.

## Five first-class Native Labs

Exactly five platform proofs:
1. TV Android — official NuvioTV;
2. Mobile Android — official NuvioMobile;
3. Mobile iOS — official NuvioMobile;
4. Desktop macOS — official NuvioDesktop;
5. Desktop Windows — official NuvioDesktop.

Native Labs are observational:
- consume official clients as-is;
- consume exact NiakVIO candidate bytes;
- test-only plumbing allowed only when behavior-neutral and needed to expose official path;
- **never patch NuvioTV/NuvioMobile/NuvioDesktop production behavior merely to make a Lab green**;
- upstream compile/dependency/packaging/runtime/player/QuickJS failures remain visible evidence.

The old Android helper `scripts/harden_nuvio_mobile_device_test.py` was an upstream-masking workaround and is intentionally removed.

### First fresh Lab trigger and upstream DSL drift

First fresh five-Lab trigger commit:
- `1ef46a8288027b2d09955894be1f269ece042f47`
- reason: post-5.21.32 final native Labs with current security/workflow cleanup.

Runs launched from that trigger included:
- Android Reader `34004792453` (TV Android + Mobile Android)
- iOS Reader `34004792486`
- Desktop Reader `34004792525` (macOS + Windows)

Mobile Android exposed a NiakVIO test-bootstrap compatibility drift before provider execution. Latest official NuvioMobile SHA observed: `eb43a6d6d82d709b29cfad94106f76f3797f38e9`. Its Gradle DSL changed from old `withHostTest {}` to `withHostTest { isIncludeAndroidResources = true }`.

NiakVIO test-only bootstrap was updated to support both forms without changing official app runtime:
- commit `60d4d813108b962d4490d62e65e50c69e53ae11d` — `ci: follow current NuvioMobile device-test DSL`;
- commit `2b4817561b5d21d574d0a7485c7db66e9ec8c63b` — test both DSL forms + idempotence;
- commit `2d87f268b95a30e4c738d818117d4639575ad0b9` — gate bootstrap compatibility in Workflow Gate.

### Latest Android Lab failures supplied by user

Latest shared Android run explicitly supplied by user:
- run `34005735542`
- TV Android red job `101412521722`
- Mobile Android red job `101412531973`

Current diagnosis from the exact logs:

#### Mobile Android `101412531973`
- This is a **test/instrumentation infrastructure failure before meaningful provider proof**, not evidence that Provider JS itself failed.
- NuvioMobile instrumentation process crashes because Sentry auto-initialization runs without a configured DSN in the Lab environment.
- Required fix belongs in NiakVIO **test-only bootstrap/instrumentation plumbing** so the official app runtime behavior is not altered. Disable/neutralize Sentry initialization only for the Lab test process/configuration, then rerun.

#### TV Android `101412521722`
- TV reaches real provider execution.
- A concrete failing case is **Allwish returning a media object for *Interstellar* whose media duration/content is only about 20 seconds**.
- The Lab correctly treats that as invalid feature playback evidence; do not loosen the TV gate to manufacture green.
- Fix should be at stream/media validation level: reject demonstrably non-feature placeholder/trailer/broken outputs while keeping provider health stream-scoped rather than disabling Allwish globally.

These two reds have different ownership and must not be conflated.

## Current stream-title presentation bug

User reported provider stream titles showing `- Inconnu`. Current localization points to shared `CORE.GLOBAL_PROVIDER_BRANDING.V1` behavior rather than quality normalization itself: branding reconstructs/preserves a suffix from an earlier title even when that suffix is merely unknown/placeholder language/quality text.

Required correction:
- fix the shared branding/presentation Lego once for all providers;
- never append placeholder suffixes such as `Inconnu`/`Unknown` to provider display title;
- preserve meaningful title/provider/quality/language metadata;
- add/extend contract tests so repeated materialization cannot reintroduce placeholder suffixes;
- if this changes published Provider JS bytes, re-materialize/reverse/minimize/integrity-check and release-finalize a new version after validation; if only source generator changes with identical published bytes, no bump.

## Performance / common-latency concern

User also reported a common latency issue across providers. Treat this as systemic until disproved. Check shared runtime path before provider-by-provider tuning:
- capability gate timing;
- TMDB preflight/cache work;
- sequential vs bounded parallel network steps;
- duplicated provider fetches introduced by shared Core;
- media validation cost;
- native bridge/test harness overhead separately from production runtime.

Do not reduce the catalogue or remove correctness checks merely to improve latency.

## Workflow ownership

### `CORE - Verify & Publish`
`sync.yml` owns routine verification/publication.
- Quick: deterministic structural/runtime/unit/security/minimizer checks over candidate bytes.
- Deep: broader read-only network/hub/provider observations, diagnostics, projections/integrity evidence.
- Quick/Deep do not repair/reconstruct Provider JS and do not routinely bump versions.

### Learning
`brain-learning-lab.yml` is isolated code-evolution/repair sandbox. Learning can produce reviewable proposals; it is not uncontrolled production mutation.

### Domain Refresh
`domain-refresh.yml` is narrow:
- validate official provider hubs/domains;
- update only validated `official_site` CONFIG data;
- must not repair APIs/routes/Core/provider code;
- must not require unrelated `staging/candidates.json` merely to refresh domains.

Historical `missing staged candidate registry` was workflow coupling and must not return.

### Full reconstruction / route recognition
- full reconstruction/materialization owns ProviderBase + DATA + Lego generation and reverse byte proof;
- route-only recognition/census updates route/protocol DATA/projections only, not Provider JS by implication.

## Minimizer contract

`scripts/provider_v3_minimizer.py` is the only production minimizer policy.

- production enabled;
- Terser forbidden;
- conservative marker/comment-aware transforms only;
- preserve `BEGIN/END`, `STARTFIX/CLOSEFIX`, `FIXDATA`, Core boundary;
- no arbitrary replacements, identifier renaming, semantic reordering or risky folding;
- template-literal providers may remain byte-stable when safe minimization cannot be proven;
- final proof requires fixed-point/idempotence, Node parse where applicable, exact portfolio coverage and reverse reconstruction/native parity gates.

## Security state and contract

Security completion is measured on exact final candidate bytes, not only source scripts.

Current work already completed:
- `.github/workflows/codeql.yml` produces local `security-extended` SARIF evidence;
- local SARIF parser/gate blocks High/Critical findings;
- `Audit production dependencies` job runs `npm audit --omit=dev --audit-level=high`;
- on run `34004792452`, dependency audit job completed **success**;
- initial useful Python CodeQL scan analyzed 517/517 Python files and found exactly 4 current findings, all `py/incomplete-url-substring-sanitization`, with 0 High/Critical;
- those four NiakVIO-owned URL substring checks were remediated structurally using URL parsing/validation;
- old `one_shot_*` and `prepare_retry_targets.py` helpers were removed;
- deterministic published-byte scanner continues to block the historical unsafe HTML-filter regex family across all 96 published provider files.

Still mandatory before final completion:
- run/inspect exact final Python + JS/TS CodeQL jobs on stabilized candidate;
- record `CODEQL_RESULT_COUNT`, per-rule counts and `high_or_critical` from logs;
- inspect GitHub Default Setup result for same candidate when available;
- direct Code Scanning alert enumeration through the current GitHub connector is unavailable (`INVALID_ARGUMENT` on direct alert endpoint). Do not pretend the historical UI alert list was directly closed; use exact SARIF/Default Setup evidence and state this connector limitation precisely if it remains.

Security rules:
- do not disable CodeQL/security rules for green CI;
- keep bounded execution/network/resource/redirect/SSRF guards;
- keep dependency High/Critical audit;
- distinguish GitHub infra/model/action failures from NiakVIO findings.

## Documentation and README work completed

README English/French parity was refreshed.

English-image issue fixed:
- both README variants previously referenced the French-text `assets/branding/how-it-works.png`;
- new English-only `assets/branding/how-it-works-en.svg` added;
- commit `85e67f2d869bf9a9f30ef885bb5aa608a58aac4a` — English pipeline artwork;
- README EN now points to English SVG;
- README FR intentionally keeps the French PNG.

README/docs commits:
- `3ea2cd8835f802d47be2e9361a0e07b68b0e702b` — EN README documents release finalizer/security and uses English artwork;
- `cf052a26ebfdf4d513bb51f773b9178ee3a35f67` — FR README mirrors accepted finalization/security semantics;
- recommended stack remains NiakVIO providers + Ultra MAX metadata/catalogue + SubSense subtitles + SIMKL tracking.

## Architecture docs state

`ARCHITECTURE.md` was materially updated by commit:
- `2231472604eca5a1bb538971a208f1fe4d8b6ddb` — `docs: define accepted release finalization contract`.

It now documents:
- Quick/Deep do not routinely bump release;
- explicit accepted-release finalizer and baseline semantics;
- no reconstruction/repair in finalizer;
- atomic version/projection/hash/integrity synchronization only when published bytes changed;
- security-extended SARIF + High/Critical dependency audit;
- docs/workflow/harness-only changes with unchanged provider bytes do not bump release;
- 18 architecture invariants including finalization contracts.

`ARCHITECTURE.docx` was regenerated locally from the updated Markdown and rendered through the required DOCX render pipeline. Visual QA was done page-by-page on 6 pages:
- no clipping;
- no overlap;
- no broken glyphs/tables;
- page headers/footers/numbers clean;
- an orphan `Règles :` on page 2 was fixed using keep-with-next;
- page 6 sparse but clean.

**At this checkpoint the regenerated `ARCHITECTURE.docx` still needs to be uploaded/committed to GitHub.** Use Git blob/tree/commit/ref for the binary DOCX if text content API is insufficient. After commit, update this MEMORY entry to the exact DOCX commit SHA.

`automation/PLATFORM-RUNTIME-CONTRACTS.md` is generated and should not be hand-edited for the NuvioMobile Gradle test DSL drift; that drift is harness compatibility, not runtime contract semantics.

## PR template / hygiene

Current PR template already covers:
- summary/root cause/scope;
- exact candidate SHA/evidence;
- semantic provider types;
- reconstruction/repair ownership;
- five Native Labs and no upstream runtime patching;
- security;
- version/cache decision;
- validation performed;
- limitations/follow-up.

Final hygiene audit still required:
- only `main` and `brain-learning/proposals` branches;
- no `workbench` refs;
- no stale `one_shot`, `once`, `retry`, `temp`, `tmp-` migration helpers;
- old hardener remains gone;
- PR template still current.

## Final publication/completion order

1. settle current shared presentation (`- Inconnu`), Allwish false-media validation and Mobile Android Sentry test-bootstrap fixes;
2. if published provider bytes changed: materialize exact Provider v3 bytes;
3. conservative minimizer + fixed-point + parse/reverse proof;
4. structural/runtime/security gates;
5. provider/network/yield evidence;
6. run **all five Native Labs** on one post-fix exact SHA and capture artifact names/outcomes;
7. accept validation pile;
8. if published bytes changed after 5.21.32, run release finalizer and synchronized new bump; otherwise retain 5.21.32;
9. regenerate/validate hashes/projections/integrity metadata when content/version changed;
10. commit regenerated `ARCHITECTURE.docx` and confirm docs parity;
11. final CodeQL + dependency + Default Setup evidence;
12. repository hygiene/branch audit;
13. update this MEMORY file with final SHA, exact workflow run/job IDs, Native Lab artifact names, CodeQL counts and any remaining external limitation;
14. final exact-SHA audit before declaring completion.

## Completion principle

A green structural workflow is not proof that 96 providers produce streams, and a native client failure is not automatically a provider failure. Keep each layer explicit, preserve evidence, fix common NiakVIO root causes where NiakVIO owns them, and never manufacture success by deleting providers, weakening validation, or patching official Nuvio production clients.

## 2026-09-06 — Canonical dual-ID input contract
- NiakVIO historically accepts provider work identity as either TMDB or IMDb. This is a permanent Core contract, not a provider exception.
- Regression identified in 5.21.33: stronger TMDB title/category/year verification left early Core gates TMDB-only, so a valid IMDb request could be converted into an empty provider result before provider execution.
- Input forms must accept numeric/prefixed TMDB and IMDb (`tt...`), including episodic transport suffixes such as `tt11198330:3:1`; season/episode are preserved separately.
- TMDB metadata remains the authoritative enrichment/classification source when available, but failure/unavailability of enrichment must not make a syntactically valid IMDb/TMDB identity invalid.
- `series` is a Nuvio transport alias for canonical `tv`; it belongs in `supportedTypes`, never in `canonicalSupportedTypes`.
- Native Labs must test production selection for both `tv` and `series`, not only direct provider execution.
- Domain Refresh owns terminal-domain derivatives (domain substitution/replacement maps and provider-owned manifest icon URLs) as well as `official_site`; historical alias keys are retained while their destination is reconciled to the authoritative terminal.

## 2026-09-06 — Main-only completion checkpoint (5.21.35 publication)

- **Execution policy tightened by user:** all active corrective work must be finished directly on `main`. Do not create another temporary/workbench implementation branch. `workbench` / PR #92 is archive-only: compare its 23 commits selectively, recover only genuinely missing ideas, then delete/close it after main contains everything useful. At this checkpoint it is 23 commits ahead and 55 behind `main`; never merge it wholesale.
- `MEMORY.md` must be updated at every important checkpoint/failure/correction so the active state remains recoverable even if chat context is lost.
- Main corrective commit `76e6e05b12fe73bf0fa9f9517f5000e78b2fa3da` fixes the **producer** of the global Core boundary: the finalizer now inserts `NUVIO_GLOBAL_CORE_START_BOUNDARY_V1` before the full `STARTFIX:CORE.*` ownership rectangle instead of inside the first Core implementation body. The static audit was deliberately not weakened.
- Retry attempt 3 of workflow run `34059449378`, job `101559752846`, proves that correction: step 8 `Finalize published 96 from Base plus structured CONFIG plus Lego` is now **green**, and step 9 generated `5.21.35` with **96 provider versions bumped**. The final Provider CONFIG validator is green 96/96; dual IMDb/TMDB, canonical media resolver and Source Plan v4 tests are also green.
- **5.21.35 is still not published/accepted.** Step 10 currently fails in `scripts/audit_provider_v3_static.py` on `AssertionError: flemmix` because final `providerDataSha256` no longer matches the stale materialization evidence for Flemmix after final publication. The final commit/push step was skipped. Diagnose and fix evidence/projection ownership; do not rerun the heavy 96-provider Repair unless evidence proves materialization itself is wrong.
- Flemmix domain state was rechecked live on 2026-09-06: current hub authority points to **`flemmix.kim`**; `.men` is an older blocked domain. Main CONFIG already uses `.kim` for `official_site`, logo and legacy substitutions/replacements, so no domain mutation is required.
- `- Inconnu` is no longer merely a planned source fix: `scripts/provider_patches/global_provider_branding_v1.py` is V7 (`post-presentation-name-title-quality-v7`) and explicitly strips placeholder suffixes such as `Inconnu` / `Unknown` while preserving meaningful quality/language suffixes. Remaining work is runtime/native validation on final published bytes.
- Main already contains stronger native application-path selection evidence than workbench: Mobile/Desktop instrumentation calls production `getEnabledScrapersForType()` for `movie`, `tv` and **`series`**, and `tests/native_app_provider_selection_gate_test.py` makes `series=0` blocking. Do not cherry-pick the older workbench version that only covered movie/tv.
- Current official NuvioTV `dev` source also maps `supportsType("series")` to `series`, `tv`, and `anime`, and `PluginManager` filters enabled scrapers through that method. The final TV Lab must prove this application path against exact current upstream bytes; do not patch NuvioTV production code to manufacture compatibility. NiakVIO's stored NuvioTV runtime-contract ref is older and should only be advanced after source/runtime review.
- Latest short-publication run also reported upstream contract review required for NuvioMobile, NuvioDesktop and NuvioTV. That drift review is separate from provider publication and must not be confused with a Provider JS failure.
