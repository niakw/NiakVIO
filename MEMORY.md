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

### Flemmix final DATA audit correction
- Root cause of the step-10 Flemmix failure: `provider-v3-materialization.json` is **earlier-stage evidence**. Its `providerDataSha256` can legitimately become stale when current structured CONFIG/domain DATA changes before final publication. Flemmix exposed this after `.kim` reconciliation.
- Commit `bdf11932ea5b949837c29b71c8a61b903e91c57b` changes `audit_provider_v3_static.py` to rebuild the expected Provider DATA in-memory from the current authoritative sources (`provider-overrides.json` + `provider_capabilities` + `provider-v3-static-knowledge.json` + current manifest entry) and compare the decoded final CONFIG to that exact deterministic projection.
- The audit remains read-only and does **not** reconstruct Provider JS. It no longer treats a historical materialization DATA hash as final-publication authority.
- Next action is another short publication retry from current `main`; heavy Repair remains unnecessary unless this stronger current-source comparison proves a genuine DATA mismatch.

## Final-byte Provider CONFIG invariant — 2026-09-06

- Current corrected manifest generation at this checkpoint: **`5.21.35`**.
- `NIAKVIO_PROVIDER_MODEL` is NiakVIO-owned structured runtime DATA, materialized as exactly one `PROVIDER.<ID>.CONFIG.V1`; ProviderBase and Source Plan v4 (`_spv4Family`) may reference it but ProviderBase itself must remain DATA-free.
- Regression found in `5.21.34`: the authoritative materializer correctly composed Base + CONFIG + Lego, but `reapply_published_overrides.py` restarted final publication from the clean ProviderBase and replayed Core without re-running `compose_provider_bundle()`. This produced final bundles that referenced `NIAKVIO_PROVIDER_MODEL` without defining it.
- Final publication now reuses the same structured `provider_model -> build_provider_data_model -> compose_provider_bundle` path as the 96-provider materializer before replaying Provider/Core Lego.
- The final Core boundary is outside every managed Core ownership rectangle: `PROVIDER.* -> NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 -> STARTFIX:CORE.*`. The previous finalizer searched for an implementation marker inside the first Core body, which could place the boundary inside that Core Lego; `audit_provider_v3_static.py` correctly rejected this and the producer was fixed rather than weakening the audit.
- A final-manifest 96/96 gate validates the actual hashed JS referenced by `manifest.json`, not only `provider-v3-materialization.json`: one CONFIG START/CLOSE pair, one `NIAKVIO_PROVIDER_MODEL = Object.freeze(...)`, matching providerId, safe final path and Provider envelope. A missing model is publication-fatal.
- Identity remains dual-source: valid TMDB **or IMDb** input is accepted; TMDB enrichment verifies/enriches identity but cannot invalidate a valid IMDb input. Episodic IMDb suffixes such as `tt11198330:3:1` retain season/episode.
- `series` remains a Nuvio transport alias for canonical `tv`; it belongs in `supportedTypes`, never in `canonicalSupportedTypes`.

<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-07-main-rollback-v37-incident-v6 -->
## 2026-09-07 — CRITICAL recovery checkpoint: V6 repair progress, broken 5.21.37, rollback to 5.21.35, Anime-Sama wrong-content incident, mandatory publication invariants

This checkpoint supersedes older release-state statements where they conflict. It must be read before any future provider/runtime/publication work.

### Current production/main safety state

- Catalogue remains **96 providers**. Never shrink the catalogue to improve metrics.
- `main` was urgently restored to the **exact 5.21.35 published tree** after 5.21.37 caused a severe production regression where *Children of Men* exposed only Anime-Sama streams and launched unrelated ~2h58 content.
- Broken 5.21.37 was preserved before rollback as **`backup/main-5.21.37-broken-20260907`**. Never merge/restore that branch wholesale.
- The rollback was done by a normal non-force commit because branch protection blocked force-push. Production rollback must preserve history.
- A minimal Anime-Sama identity hotfix was proven on top of the restored 5.21.35 tree. PR **#100** is the safety patch candidate; it must not import V29 or other 5.21.37 reconstruction changes.
- Candidate validation run for the 5.21.35 Anime-Sama hotfix: **`34157621920`**. It proves: *Children of Men* => Anime-Sama `raw=0`, `playable=0`; no requests descend to the known wrong path; **95 other providers remain unchanged**.
- Verified candidate commit before clean publication work: **`5c145102...`**; generated Anime-Sama bundle **`anime-sama-fe222ff3b14216b2.js`**. Re-read exact current PR/main SHAs before any future merge because subsequent doc/bot commits may advance refs.
- Restored durable MEMORY writer commit on main: **`400a065c5832a19005a989e498bc6fa0360b915c`**.

### Exact Anime-Sama / Children of Men incident — root cause proven, not hypothetical

The bad media path was reproduced on both exact 5.21.35 and broken 5.21.37 using *Children of Men* identity (TMDB `9693`, IMDb `tt0206634`, expected runtime ~109 min).

Observed wrong path on the broken/provider runtime:
1. expected Anime-Sama slug `les-fils-de-l-homme` => 404;
2. provider-specific Anime-Sama fallback search runs;
3. its custom `searchSlugs()` logic takes early `/catalogue/<slug>` results without proving title identity;
4. observed unrelated catalogue slugs included **`lag`** then **`les-mikails`**;
5. runtime descends to an embed at **`ansembed.net`**;
6. embed resolves an HLS at **`vmcld.space`**;
7. media is technically readable but measured around **10,691.8 seconds (~2h58)** and unrelated to *Children of Men*;
8. downstream presentation stamped requested-work metadata such as *Les Fils de l'homme*, 2006 and expected duration ~109 min onto the wrong source, making the player-facing row look legitimate.

Critical conclusion:
- **The Roblox/unrelated ~2h58 stream was NOT created by V29.** It was reproducible on 5.21.35 too.
- 5.21.37 made the incident dramatically visible because many other providers disappeared, leaving the pre-existing Anime-Sama false positive almost alone.
- Wrong-content detection in Labs/probes correctly recognized **`strong_title_mismatch` / `identity_contradiction`**, but that diagnostic was not a mandatory runtime rejection boundary before provider-specific detail/player resolution.

### Why existing route/DATA/integrity checks did not stop Anime-Sama

Do not ever describe this incident as “Anime-Sama somehow bypassed a working global gate”. The architecture allowed a path that never invoked the gate.

- Route/DATA checks proved that observed routes and structured provider DATA were real/coherent. They did **not** prove that every search result selected by provider-specific code matched the requested work.
- Anime-Sama had a **provider-specific Lego/runtime path** with its own `searchSlugs()` behavior.
- That path extracted early catalogue slugs and continued toward detail/player without requiring a positive title-identity decision from shared Core.
- Structural integrity tests verified markers, Core presence, CONFIG shape, hashing/materialization, syntax and similar invariants, but did not prove **control-flow domination**: that every provider-specific path must pass the identity boundary before player/source resolution.
- Labs could detect wrong content after the source was already returned, which is too late for runtime safety.

Permanent invariant from this incident:
> **No provider-specific Lego, generic crawler, API recipe, Source Plan or fallback may reach detail/player/source resolution unless the work identity required by that plan has been positively established. Presence of identity code in the bundle is insufficient; execution must be dominated by the identity decision.**

For catalogue search specifically:
- **No positive title match => no candidate.** Type, year, provider ID, HTTP success or playable media can add confidence only after a positive title/identity match; they can never compensate for absent/contradictory title identity.
- An opaque playable URL is not proof of work identity.
- `playable` must never override `wrong_content` / explicit identity contradiction.
- Expected TMDB duration is work metadata, not measured source-media duration. Do not present expected duration as if it were a fact observed from the stream.

### Anime-Sama hotfix contract

The proven minimal 5.21.35 safety fix changes only Anime-Sama identity/search behavior and its generated bundle/projection as needed.

Required behavior:
- search result slug must be allowed only after positive title identity;
- *Children of Men* must produce **zero Anime-Sama streams**;
- no fetch to `lag`, `les-mikails`, `ansembed.net`, `vmcld.space` for this fixture;
- 95/95 non-Anime-Sama provider files remain byte-identical in the minimal production hotfix candidate.

Do not “fix” this by provider-specific hardcoding of *Children of Men*, Roblox domains, known bad slugs or duration alone. The rule is generic identity fail-closed.

### 5.21.35 -> 5.21.36 -> broken 5.21.37: global provider-yield regression

Anime-Sama alone does **not** explain why 5.21.37 showed almost no other providers. Treat the global disappearance as a separate systemic regression.

Important timeline and findings:

1. **ProviderBase V7 family-first existed already in 5.21.35.** Do not blame that change merely because family-first is conceptually risky; it is not the new `.35 -> .36` delta.
2. A dangerous **ProviderBase V8 “API recipe precedence”** change appears between 5.21.35 and 5.21.36. Commit identified: **`6a67049b4075160d38aecaa9d6c7820108da1ea0`**.
3. The V8 behavior effectively does:
   - if `apiRecipe` exists, execute recipe first;
   - if recipe returns streams, return them;
   - if recipe returns 0 and `allowGenericFallback !== true`, **return `[]` immediately**;
   - therefore do not reach Source Plan/generic/historical path that may have worked in 5.21.35.
4. V6 repair evidence later proved that many synthesized `apiRecipe`s were partial, polluted, stale or incapable of expressing multi-hop behavior. Therefore recipe precedence can systematically suppress providers even when their original/upstream path remains functional.
5. Broken 5.21.37 additionally introduced **V29 terminal/session changes** and rematerialized all 96 bundles again. Exact V29 commit found: **`6f74939efa11b2c886e82002c242b923a4f87f6c`**. Do not assume V29 is the sole global regression until `.35/.36/.37` same-run yield comparison proves it.
6. Earlier hypothesis that V29 providers cancel one another through shared `globalThis` was checked against current NuvioTV execution: TV creates a fresh QuickJS execution context per provider invocation, so cross-provider shared-global cancellation does **not** by itself explain TV catalogue collapse. Do not repeat that hypothesis as fact.

### V29 intended fixes — must be recovered without importing broken 5.21.37 wholesale

V29 mixed two legitimate concerns:

A. **Stream presentation cleanup**
- remove placeholder suffixes such as `- Inconnue`, `Unknown`, `N/A`;
- keep meaningful provider/quality/language presentation;
- synchronize final `title`/`name` presentation consistently.

B. **Stale/switch request settlement**
- native/host fetch may ignore `AbortController` and remain pending after provider/work switches;
- intended fix races host fetch against an abort/stale promise so stale work settles quickly and does not pile up;
- this is about stale invocation cleanup and performance, not provider route precedence.

Recovery rule requested by user:
- produce a **functional 5.21.37-equivalent** from restored 5.21.35, reapplying useful `.37` corrections one by one;
- **do not re-import 255 mixed commits or rematerialize 96 providers blindly**;
- **do not import ProviderBase V8 API-recipe precedence** unless redesigned and independently proven to preserve yield;
- preserve 5.21.35 provider behavior/bytes as baseline wherever a Core patch does not require a provider byte change.

Active candidate branch for this work: **`hotfix/5.21.37-functional-v2`**. It is based on restored/safe 5.21.35 + Anime-Sama safety context, not broken `.37` wholesale.

Files already staged on that branch for the new safe method include:
- `scripts/apply_v29_functional_hotfix.py` — intended to apply only V29 presentation + native abort race, while explicitly refusing V8/provider route/DATA reconstruction;
- `scripts/compare_quick_yield_preservation.py` — baseline-to-candidate provider preservation gate. Continue strengthening it to cover `raw`, `playable`, `verified`, and new wrong-content regressions.

### Mandatory before/after yield preservation gate — publication rule

This rule exists because `.37` structural tests were green while production behavior collapsed.

For any shared Core/ProviderBase/Lego change affecting published Provider JS:
1. run a live-yield **baseline** on the exact currently accepted tree;
2. apply only the candidate change;
3. run the same fixtures/providers in the **same workflow/environment**;
4. compare provider sets at minimum for:
   - raw/non-empty provider output;
   - playable provider output;
   - verified provider output;
   - wrong-content / identity-contradiction set;
5. rerun only candidate losses with adaptive retries to eliminate transient 429/timeout/reset noise;
6. **any baseline-positive provider still lost after targeted retry blocks publication** unless the loss is an explicit, documented wrong-content/security correction;
7. **any new wrong-content provider blocks publication**;
8. structural 96/96, hash, CONFIG, parse, unit/security tests remain necessary but are no longer sufficient.

Use existing `scripts/audit_provider_quick_yield.py` for portfolio-yield evidence. Do not publish a common runtime change based only on “96 bundles materialized”, marker presence or unit tests.

### V6 provider-repair progress as of incident

The repair branch work remains relevant but must stay separated from urgent production recovery.

Initial protected green/skip set was 9:
- `allwish`
- `anime-sama`
- `castle`
- `hindmoviez`
- `kehflix`
- `neko-sama`
- `streamzo`
- `videasy`
- `wookafr`

After real targeted repair, **PlayIMDb became the first V6 red -> green**, so protected skip became **10/96**. This does not mean only 10 historical providers work; it means only 10 had been promoted into the current V6 “proven green, do not re-probe” contract.

PlayIMDb acceptance:
- run **`34147372929`**;
- reconstructed result `raw=1`, `playable=1`, `verified=1`;
- both upstream-positive movie+TV lanes preserved `2/2`, `lost=0`;
- global 96-provider structural/runtime regression suite remained green.

V6 retry4 before later family fixes:
- targeted unresolved: 87; protected skip: 9 at that moment;
- 39/87 providers had live proven routes;
- 238 proven routes;
- 21 upstream-positive provider/type pairs observed;
- reconstructed portfolio for the 87 was still initially `raw=0/playable=0/verified=0`, proving that route recognition alone was not enough and the proof->runtime bridge was broken.

Key V6 common root causes already discovered/fixed or under active repair:
- false causal attribution: old recovery stamped final task stream count onto every request, making early metadata/search helpers look terminal;
- metadata helpers such as `arm.haglund.dev` / `v3-cinemeta.strem.io` must be evidence/identity only, never executable provider recipes;
- generic `directRoute` must not override valid typed movie/episode routes;
- absolute typed resolver recipes must not require an unrelated search/base gate;
- stream JSON containers such as `stream_urls` / `streamUrls` require bounded parser support;
- temp worker `MODULE_NOT_FOUND` was an environment resolution issue, not provider death: source providers copied into temp dirs could not resolve project-declared modules. After correction, 16/16 affected providers started without that error; do not classify those providers dead from old logs;
- AnimeZey exposed POST body proof/replay limitations. V9/V9.1 added fail-closed reusable text-body abstraction: bounded printable body, no secret/token patterns, must abstract fixture identity into placeholders; opaque static text remains non-reusable;
- NetMirror old quarantine/catalogue model was stale relative to fresh typed TV resolver evidence. V8 repair work changed it from zero provider fetch / lost upstream lane to `raw` output with upstream lane preserved, though stream-level playability remained unresolved due source HTTP behavior;
- Source Plan V10 corrected live search-domain authority, runtime domain replacements, fail-open from partial recipe toward Source Plan, season-aware catalogue scoring and obvious navigation noise;
- FrenchStream TV reached `playable=1/verified=1` under this work, but provider was not promoted because movie remained lost;
- PapaDuStream original contract confirmed as `TMDB -> IMDb -> /series/{imdbId} -> parse series page -> select S/E HLS`, with Origin/Referer. Never freeze fixture IMDb/HLS routes in DATA;
- multi-hop families (AnimeKai, Movies4u, MoviesHunt, Mugiwara, FrenchStream, PapaDuStream, VoirAnime family, French-Manga, Cineby) require structured dataflow/source plans, not flattened single-route recipes.

### Adaptive retry contract

User explicitly requested more per-provider retries where useful.

- Do **not** blindly run every provider N times.
- Retry only transients: timeout, connection reset, temporary DNS, HTTP 408/425/429 and suitable 5xx.
- Stop retrying after valid proof is obtained.
- Do not waste retries on structural failures such as missing module, unsupported plan, deterministic policy rejection or impossible source mapping; repair those at common runtime/sandbox level.
- Three targeted attempts is an acceptable current default for unstable providers; preserve previous positive evidence when current upstream is temporarily 429, but do not declare repaired until acceptance can be re-proven.

### Provider ON/OFF terminology — do not confuse it again

At the latest V6 checkpoint before the production incident:
- 96 total catalogue entries;
- **10 protected/proven V6 green** after PlayIMDb;
- 86 not yet promoted to that protected-green set;
- **0 provider had been proven definitively dead/irrecoverable**.

Important distinction:
- `enabled=false` / temporarily OFF in NiakVIO due insufficient current proof is **not** the same as “provider/site permanently dead”.
- No route proven from one census is unknown/inconclusive, not death.
- A provider may have historical/local success outside the strict V6 protected set. Earlier campaigns observed on the order of 30-40 useful providers in some local matrices; do not rewrite history as “only 10 providers ever worked”.

### Permanent anti-regression rules from 2026-09-07 incident

1. **Never publish a 96-provider common Core/ProviderBase change without same-run before/after live-yield preservation.**
2. **Never use a structural green result as proof of functional provider preservation.**
3. **Never allow provider-specific Lego to bypass mandatory identity decision boundaries.** Tests must prove control-flow behavior, not marker presence.
4. **Catalogue search is fail-closed on title/work identity.** No positive title identity => no detail/player/source.
5. **Playable is not identity.** HTTP 200/206, valid HLS, duration, provider ID, year/type alone cannot convert unrelated media into the requested work.
6. **Explicit wrong-content/identity contradiction is publication/runtime-fatal for that stream.** Never keep it merely as a diagnostic while returning the row.
7. **Expected metadata is not observed stream fact.** Keep requested-work title/year/duration separate from source-measured metadata.
8. **A new API recipe may be preferred only when its evidence/coverage is sufficient.** A zero-result partial recipe must not suppress a previously functional fallback/source plan by default.
9. **Do not rematerialize all 96 merely because a small shared source patch exists** unless generated bytes genuinely require it and yield preservation proves the result. Prefer byte-preserving/minimal targeted publication when possible.
10. **Rollback before extended diagnosis when production is clearly broken.** Preserve broken tree on a backup branch first; restore known-good public behavior, then reproduce off-main.
11. **Never debug production by weakening gates.** Wrong-content and player integrity guards must become stricter when contradicted evidence is observed.
12. **Always store incident/root-cause/checkpoint evidence in `MEMORY.md` before continuing major work.**

### Immediate continuation sequence after this checkpoint

Urgent production/release recovery takes precedence over broad V6 repair until a safe functional `.37` equivalent exists.

1. Confirm this checkpoint was appended to `MEMORY.md` and pending file reset.
2. Keep public main behavior on restored 5.21.35 plus only the independently proven Anime-Sama wrong-content safety hotfix when merged.
3. On `hotfix/5.21.37-functional-v2`, finish the preservation comparator (`raw` + `playable` + `verified` + wrong-content).
4. Run exact same-workflow `.35 baseline -> candidate with presentation cleanup only`; reject any lost provider.
5. Add native-abort/stale-session race separately and rerun the full preservation comparison; if it loses providers, fix/withdraw that part rather than publishing it.
6. Do not import ProviderBase V8 recipe precedence from `.36/.37`; redesign only on V6 repair branch with explicit fallback-preservation tests.
7. Verify *Children of Men* no longer exposes Anime-Sama wrong content in the final production candidate.
8. Verify representative movie/TV/anime yield is not below accepted `.35` baseline; retry only transient losses.
9. Run 96 structural/runtime/integrity/security checks.
10. Run the five Native Labs on one exact accepted candidate SHA.
11. Only then publish/version the functional replacement for broken `.37`.
12. Resume broad V6 repair of the remaining unresolved providers without re-probing protected greens unnecessarily.

<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-07-correction-v8-chronology -->
## 2026-09-07 — CORRECTION to incident checkpoint: ProviderBase V8 chronology

This correction overrides one statement in the immediately preceding incident checkpoint.

- Earlier working diagnosis said ProviderBase **V8 API-recipe precedence appeared between 5.21.35 and 5.21.36** and could therefore explain the production regression specific to `.37`.
- That chronology is **wrong**.
- Exact verification against accepted **5.21.35 commit `9db07b3aa42ce2535ec1d7c19866beb43586badd`** shows published provider bundle `providers/purstream--nuvio--ec203db0a04b6453.js` already contains marker:
  - `/* NIAKVIO_PROVIDER_BASE_API_RECIPE_FIRST_V8 */`
  - including the `apiRecipe` precedence / `allowGenericFallback` logic.
- Therefore **V8 is not a new `.35 -> .36/.37` delta and must not be cited as the root cause of the sudden `.37` catalogue collapse without additional evidence**.
- V8 can still be architecturally problematic for V6 repair/multi-hop providers and may require redesign, but that is a separate issue from the production regression that appeared today.
- Future diagnosis of the `.37` collapse must compare exact published bytes and live behavior across exact 5.21.35 / 5.21.36 / 5.21.37 trees, especially V29/session/presentation and any DATA/Core rematerialization deltas, rather than inferring causality from source-generator chronology.
- Permanent rule reinforced: **before assigning a regression to a migration/version marker, verify the marker/behavior in the exact previously-good published bytes, not only in source generators or commit messages.**

<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-07-v6r7-v14-v29 -->
## 2026-09-07 — Route repair V6 #7 / V14 isolation checkpoint

- V6 retry #7: run `34161809385`, job `101865008551`, head `961f09c6dd26eb8bce390b444bf50ed9b3189386`.
- Scope remained exactly 4 unresolved targets: `animekai`, `movies4u`, `papadustream`, `frenchstream`; protected skip set=10 and recognition overlap=0.
- Recovery proved all 4 targets live: 43 targeted routes. Merged state: 46/96 providers with proven routes, 317 routes, 22 recipes.
- Historical typed-recipe sanitizer worked: `typed_direct_sanitized=4`; it removed stale generic direct precedence from preserved typed recipes including PlayIMDb.
- Whole-portfolio baseline was raw/playable=8, verified=7, wrong=3. Candidate became raw/playable=11, verified=10, wrong=3. No lost raw/playable/verified providers and no new wrong-content; `portfolio_gate=true`.
- V6 #7 still correctly failed global preservation because exactly three upstream-positive pairs remain lost: `animekai:anime`, `frenchstream:movie`, `movies4u:movie`. PapaDuStream and FrenchStream remain real gains; do not label V6 globally accepted yet.
- Initial isolated V14 run `34162464280` passed contracts but was rejected: it regressed FrenchStream TV by allowing a transient positive search host to override the explicit runtime domain replacement. Portfolio stayed preserved but target losses became `animekai:anime`, `frenchstream:movie`, `frenchstream:tv`, `movies4u:movie`.
- V14 diagnosis from artifact: Movies4u structured search plan executed and `GET /?s={query}` returned 200, but generic search->detail selection failed. Original Movies4u selects search results using anchor label/title/year before detail->m4uplay/HubCloud resolver traversal.
- V14.1 branch work adds two provider-agnostic rules: only positive `source`/`player` hosts may suppress historical domain substitutions; search/detail success stays evidence only. HTML detail URL scoring can also use its anchor label, while same-provider/detail eligibility stays mandatory and explicit movie-year mismatch remains rejected.
- V14.1 isolated retry is run `34164198835` on `workbench/route-recognition-v14-search-plan`; no publication/main writes are allowed by this repair pipeline.
- Functional `.37` V29: V29 cancellation tests themselves passed, including native fetch ignoring AbortController. The previous V3 run failed during rematerialization only because `provider_base_store_test.py` asserted obsolete `_playerLike` nested-discovery syntax. Test was updated to current `_crawlEligible` + score/slice contract; retry run is `34163731580` on `hotfix/5.21.37-functional-v2`. No `.37` publication is authorized until final live portfolio + Children of Men guard pass.

<!-- NIAKVIO_MEMORY_CHECKPOINT:2026-09-08-fast-v15-v29-provider-wave -->
## 2026-09-08 — Fast provider-repair loop, V15 status, V29 restoration gate

### Provider repair status and counting
- Catalogue remains 96/96. Zero providers are "never seen": all 96 have been through at least one general census.
- `automation/provider-repair-skip.json` is only the proven-green recognition skip set, not a complete count of working providers. Do not equate `skip=10` with "only 10 providers work".
- Last safe V13.2 portfolio proof had 11 playable / 10 verified providers with no new wrong-content after typed-recipe sanitation; historical local campaigns have shown 30+ positive providers.
- Latest merged route report has 46/96 providers with at least one live-proven route. Of the 86 not formally closed, 38 already have live-proven routes and mainly need reconstruction/stream-finalization; 48 still need fresh route/protocol requalification.
- Current priority recoverable upstream-positive wave: AnimeKai, Movies4u, FrenchStream movie, MugiwaraStream, then the remaining multi-hop positives, then the 48 without usable live proof.
- MugiwaraStream is explicitly recoverable: original/upstream is positive and the latest quick-yield reaches `/api/search` then `/catalogue/.../films`; its loss is after catalogue/detail, not evidence of a dead provider.

### New acceleration policy — mandatory without reducing quality
- Use `provider-repair-fast-targeted.yml` / `run_provider_repair_fast_targeted_v1.py` for iterative repair loops.
- Fast loop: run migrations/contracts + targeted upstream recognition + materialize only touched providers + targeted acceptance. Do NOT rematerialize all 96 for every failed experiment.
- Only after a targeted smoke produces a real positive gain may a common-runtime change pay the full portfolio before/after gate.
- Final acceptance still requires full portfolio preservation (`raw`, `playable`, `verified`, `wrong_content`) and the normal 96 deterministic/global contracts. Acceleration changes cadence, not proof quality.
- Retries remain targeted to observed losses/transient failures rather than rerunning all providers.

### V15 targeted smoke evidence
- Experimental branch: `workbench/route-recognition-v14-search-plan`; publication remains forbidden.
- V15 is provider-agnostic. It adds bounded explicit player attributes (`data-video`, `data-embed`, etc.), rejects arbitrary noisy `data-*` values as URLs, allows the current proven search-response origin locally for detail parsing, adds bounded catalogue article/title-year identity, and allows short third-party `/e/<id>` resolver traversal only after provider identity is established.
- V15 must not encode AnimeKai, Movies4u, FrenchStream, Mugiwara or their hosts/fixtures as runtime rules.
- Fast run `34166932027` proved the acceleration path works and fully reached live recognition/materialization in ~targeted scope instead of a full repair wave.
- Upstream recognition in that run: 4/4 targets proven, 48 total proven routes: AnimeKai 8, FrenchStream 14, Movies4u 16, MugiwaraStream 10.
- Merged report after targeted recognition: 46 providers proven, 319 routes, 23 recipes, 4 historical typed-direct recipes sanitized.
- Only the 4 target providers were rematerialized in the fast loop; 96 CONFIG and deterministic global output/identity/media-type guards still passed.
- V15 targeted result is NOT accepted: `raw=0 playable=0 verified=0`, upstream-positive pairs=5, preserved=0, lost=5 (`animekai:anime`, `frenchstream:movie`, `frenchstream:tv`, `movies4u:movie`, `mugiwarastream:anime`). No full portfolio gate should be run from this failed smoke.
- This failure is useful: routes are real, but the reconstruction/execution model still misses later multi-hop semantics. Diagnose per family from the fast artifact before another common change.

### Known deterministic provider-family gaps
- AnimeKai: reconstruction reaches correct search/watch/episode chain; remaining known gap is final server/player extraction from `data-video`/embed data and crawl semantics. Do not invent AnimeKai-specific route constants.
- Movies4u: live search request is proven and requires structured request context; search returns 200. Original chain selects a matching catalogue article/bookmark before `m4uplay`/resolver. Preserve title+year identity and same/current response origin without weakening movie-year contradiction rejection.
- FrenchStream: V13.2 recovered TV previously. V14/V14.1 regressed it and were rejected. Search/detail evidence may hit 429 on DLE search while secondary API routes return 200; treat this as availability/fallback evidence, not permission to overwrite a previously working TV path.
- MugiwaraStream: upstream-positive multi-hop provider; search/catalogue is live and working, so continue after the catalogue stage rather than classifying it OFF.

### Unique-provider patch debt
- Provider-specific runtime patches such as `anime_sama_runtime_v1.py` can exist when a provider protocol cannot yet be represented by global DATA/plan primitives.
- Do NOT prioritize deleting/consolidating those patches now. First maximize provider recovery.
- After provider recovery stabilizes, audit provider-specific runtime patches and absorb any patch whose behavior is expressible by the generalized Search Request Plan / Source Plan / identity / player primitives.

### Anime-Sama incident lesson retained
- Route/DATA checks being green did not guarantee that every provider-specific Lego path was dominated by the shared identity gate.
- The Roblox false-positive showed that a provider-specific `searchSlugs()` path could reach player resolution without positive title identity.
- Production `main` is currently 5.21.35 plus the narrowly validated Anime-Sama fail-closed hotfix; experimental V6/V14/V15 code must not be published there directly.
- Future integrity must test control-flow dominance/behavior, not merely presence of Core markers/routes/DATA.

### `.37` functional restoration / V29
- Rebuild the functional `.37` from the restored `.35` baseline; do not restore the broken `.37` tree wholesale.
- Presentation fix for `- Inconnue` has preserved portfolio behavior after targeted retry and is considered safe to retain.
- V29 native-abort/session source passes its dedicated synthetic race test, including a host fetch that ignores AbortController.
- Run `34163731580` still did NOT reach final live-yield after V29 because rematerialization failed on a stale shape assertion in `tests/provider_base_store_test.py`: it expects literal `requests < 7` while current bounded crawler uses the newer request budget. This is a test-contract drift, not evidence that V29 runtime failed.
- Update only the stale contract to assert the actual bounded-current behavior, then rerun the same `.35 -> presentation -> V29 -> full live-yield preservation` workflow. Do not authorize release until final live portfolio and Children-of-Men/Anime-Sama negative gate pass.

### Publication safety rules reinforced
- Repairing one provider/family must never silently regress another positive provider.
- Every common Core/ProviderBase change: baseline portfolio before, candidate after, compare raw/playable/verified/wrong-content, targeted retries for losses, fail on persistent loss or new wrong-content.
- A targeted provider improvement is not sufficient for publication.
- A route being live/proven is not equivalent to an end-to-end playable provider.
- Do not classify unresolved providers OFF merely because current reconstruction yields zero.
