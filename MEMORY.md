## 2026-10-02 — All-provider fan-out authority can no longer be erased by targeted census

- Root cause of the missing CoFlix/Papa/PersianStremio dynamic debt after Repair was persistence semantics, not provider recovery: workflow-run/unresolved sharded census replaced `automation/provider-census-sharded-latest.json` with a 19-provider symptomatic subset.
- Brain Repair reads that file for announced/explored/returned completeness evidence, so a targeted census could erase nominally green providers from the dynamic completeness cohort even though no provider bytes changed.
- Sharded persistence now always stores the run-specific artifact and refreshes current status/history, but only `scope=all` may replace `provider-census-sharded-latest.json` and its summary. Unresolved/targeted runs explicitly retain the last global fan-out authority.
- The persisted run summary used in commit messages now comes from the current run's temporary summary, not whichever global snapshot remains on disk.
- A fresh `scope=all` census is triggered to restore global authority on current bytes. After it lands, CoFlix remains the first representative Brain FORCE; subsequent targeted Repair census cannot make the wider completeness cohort disappear.
- No provider runtime bytes were manually edited for this correction.

## 2026-10-02 — Repair V6 now selects dynamic completeness debt

- Brain already classified sharded fan-out loss as `variant_coverage_gap`, but canonical Repair V6 still intersected every target with `provider-census-status.json:repairQueue`. A nominally `FULL OK` provider such as CoFlix could therefore be diagnosed by Brain yet silently excluded before provider mutation.
- Repair selection now unions the durable repairQueue with bounded current dynamic variant debt from `automation/provider-census-sharded-latest.json`. Gap states are `announced-not-explored`, `explored-not-resolved`, `returned-subset` and `quality-gap`; an announced>=2 / returned<announced row is also treated as debt.
- This new authority is selection-only. It does not grant proof/publication authority and still respects provider authority blockers. Every mutation must pass current-byte application, rematerialization, playback, identity, measurable completeness gain and portfolio non-regression.
- Contracts prove a FULL OK provider with 19 announced / 2 returned re-enters Repair, while a 2/2 `fanout-observed` provider remains excluded. This is generic and applies to the wider provider cohort, not only CoFlix.
- CoFlix FORCE is retriggered after this wiring. No CoFlix provider runtime was manually edited.

## 2026-10-02 — Repair V6 Core migration blocker fixed semantically

- Canonical Repair run `36965535816` failed before any provider mutation in `scripts/apply_core_identity_ownership_cleanup.py`: it required the historical Stream Identity revision v10 anchor, while current Core is already `cross-client-player-page-identity-v15`.
- Current v15 bytes already satisfy the intended ownership behavior: `contentLike(candidate,q)`, episodic year excluded from the heuristic, movie-only catalogue year policy, and the old context-free/year-active forms absent.
- The migration now detects those behavioral invariants instead of one historical revision label. A newer correct Core is therefore a no-op success rather than a fleet-wide Repair blocker.
- Added `tests/core_identity_cleanup_idempotence_test.py` and wired it into Workflow Gate; it validates the current Core and executes the migration entrypoint as an idempotent no-op.
- CoFlix is explicitly retriggered in FORCE after this fix. The target remains Brain-owned: current census returned-subset + coflix.ac REST 10+9 structure -> Brain mutation -> apply -> rematerialize -> playback/identity/completeness validation. No CoFlix provider runtime was manually edited.

## 2026-10-02 — Dynamic completeness causal class preserved through Learning

- CoFlix FORCE run `36964956962` proved the upstream Brain router was correct (`variant_coverage_gap`) but exposed a downstream NiakVIO planner regression: the Learning sandbox returned `runtime_empty`, causing the runtime planner to relabel the same provider `transport_blocked` and select generic `adaptive_runtime_recovery`. The 7B guidance file consequently contained zero provider rows and no FORCE candidate was materialized.
- NiakVIO Brain now treats `variant_coverage_gap` as a first-class failure class and reads current sharded census fan-out directly into the runtime planner census prior. Current `announced/explored/returned` debt with repair-target authority survives weaker sandbox runtime-empty/transport relabels.
- The precedence remains fail-safe: identity mismatch, short-media/audio and reader parser/decoder safety evidence may still override completeness debt.
- Synthetic contracts prove FULL OK + 19 announced / 2 returned + sandbox runtime-empty/403 stays `variant_coverage_gap` and targets capability `variant_enumeration`; a simultaneous identity contradiction still becomes `identity_mismatch`.
- No CoFlix runtime byte was manually edited. The same representative FORCE must be rerun and produce/apply/rematerialize a Brain-owned candidate before this repair can be called functional.

## 2026-10-02 — Causal strategy preflight drift closed

- CoFlix FORCE rerun `36964786372` passed the cron/full-coverage contract but stopped next in `brain_causal_strategy_profile_test.py` before any Brain mutation.
- The stale assertion dated from before commit `a1794eb2dcc7aad6603d2da4fac34ca1246193d1`, which deliberately made all generic causal failure families executable and mapped `unknown_failure` to `adaptive_runtime_recovery`.
- Runtime, JS planner and LLM contracts already agree on that mapping. The test now locks the current behavior instead of rejecting it.
- Run `36964786372` produced no provider mutation; this remains Brain preflight debt, not a CoFlix repair result.
- The same CoFlix architecture FORCE is retriggered from the current main after this contract alignment.

## 2026-10-02 — CoFlix FORCE preflight gate corrected

- Explicit CoFlix FORCE run `36964643052` correctly resolved target `coflix`, `architecture_force=true` and a 60-minute bounded slot, but no Brain/provider mutation ran because `tests/brain_cron_full_coverage_test.py` failed before Learning execution.
- The failing assertion required the literal text `github.event_name == 'schedule'` anywhere in the workflow. That was stale: `publish-learning` now has no event filter and therefore naturally runs after `experiment` for scheduled executions.
- The contract now checks the actual invariant instead: cron trigger remains present and the sanitized-memory publication job has no event-name gate. Repair/architecture proposal jobs remain separately restricted to explicit manual/FORCE conditions.
- This was a Brain pipeline gate failure, not a CoFlix/provider failure. No provider runtime bytes were changed by run `36964643052`.
- The same commit retriggers the CoFlix representative FORCE from census `36958527070` and current structure evidence (coflix.ac REST + 10/9 fan-out).

## 2026-10-02 — Probe failures removed from provider Repair debt

- Root cause of the stale 1/46 census flooding Repair was architectural: `invalid_probe_output`, `missing_tmdb_credential` and harness `audit_error` were grouped with provider-owned JS failures. A broken probe could therefore manufacture `PROVIDER JS BROKEN` rows and expand the Brain repairQueue across unrelated providers.
- These stages now form a separate harness-infrastructure class. When they are the current lane evidence, census reports `HARNESS/ENV BLOCKED` and automated provider Repair is ineligible.
- Proof history treats these stages as neutral: they neither increment provider technical failures nor reset prior provider/network streaks.
- Workflow Gate now executes both the current-provider-structure evidence contract and the census harness-infrastructure classification contract. No provider runtime bytes were changed.

## 2026-10-02 — Current provider structure now reaches Brain Repair

- The user-supplied current CoFlix player page proves a provider-contract drift that stale runtime execution cannot discover by itself: current origin `coflix.ac`, resolver `/wp-json/coflix/v1/resolve`, request-key names `tmdb/type/year/pid`, and 2 server groups exposing 10 + 9 indexed choices (19 total) with VF/VFF/VOSTFR labels.
- Persisted only a sanitized observation in `automation/provider-current-structure-evidence.json`; raw HTML, parameter values, tokens and stream URLs are not stored. Both proof and execution authority are explicitly false.
- Brain-LLM main `5ee8123f657277bb2fc21f6dc4146a307ba58926` adds generic ingestion of this channel into Repair observations and route context as `observation-only`. It does not promote the observed route directly to executable Provider DATA.
- This lets Repair distinguish “stale runtime follows an old provider contract” from “current contract has a simple output cap”. CoFlix remains the representative first repair; no provider production runtime byte was manually changed.

## 2026-10-02 — Variant URL tokenization exact-host guard

- The generic keyed URL extractor used a character class that excluded the literal letter `s` instead of whitespace. Candidate counts could therefore stay numerically correct while hostnames were silently truncated (for example a `.test` reader).
- Corrected the keyed URL token boundary and strengthened the response-variant contract to assert the exact six Papa-style reader hosts, not only the candidate count.
- This is harness/Brain evidence plumbing only; no provider runtime or provider-owned production byte was edited. The in-flight census pinned to `c1024586ae28` predates this correction and is diagnostic; final authority requires a rerun on the corrected HEAD.

## 2026-10-02 — HTML fan-out false-positive filter

- Partial authority run `36957631178` exposed a generic observation bug before Brain mutation: PapaDuStream movie returned 2 playable/verified streams but broad HTML URL extraction advertised 23 candidates and included unrelated hosts such as `image.tmdb.org` / `www.w3.org`. This run is therefore diagnostic only and must not become completeness-repair authority.
- Quick census fan-out now distinguishes structured JSON from HTML. JSON stream/source arrays keep their bounded full variant count even when variants share CDN hosts; HTML reader/server multiplicity is conservative and uses explicit indexed menus, iframe multiplicity and off-origin hosts actually traversed by the provider runtime.
- Nested player JSON may contribute its structured variant count; nested HTML remains index-driven to avoid counting player-page assets/ads/navigation as terminal choices.
- Added contracts for noisy 23-URL HTML collapsing to the 2 actually evidenced readers, while a structured JSON response with 17 stream variants remains 17.
- No provider runtime bytes were changed. A fresh `scope=all` census is required before CoFlix or any cohort provider can enter Brain FORCE from dynamic completeness evidence.

## 2026-10-02 — Sharded fan-out evidence wired into Brain Repair

- The quick/sharded census probe now runs the generic response variant detector and persists bounded player/server/quality fan-out hints instead of dropping them before Brain Repair.
- Quick census rows now derive the hierarchical announced → explored → returned state, including nested player responses (representative contract: two player hosts exposing 10 + 9 choices => 19 announced variants).
- NiakVIO-Brain-LLM main is already CI-green with automatic static + dynamic completeness cohort selection: current sharded fan-out debt can classify FULL/PARTIAL/CANDIDATE providers as `variant_coverage_gap`; player/server/mirror/quality/language vocabulary is part of the repair reference model.
- NiakVIO commits in this sequence: `72343d5e` (probe hints), `5d33c901` (persist quick fan-out), `63a21936` (hierarchical contract test), `f6f8aab2` (gate), `e27620ca` (all-provider census trigger).
- Current all-provider sharded census run: 36947484182, source `e27620ca344b0de1f3b9aa7ca4633f20a770c635`. It is not authority until the merged ledger is persisted and inspected.
- An unrelated current-bytes census run failed on the pre-existing 4KHDHub behavior assertion (expected one movie result, got none); do not attribute that failure to the fan-out changes.
- No provider runtime bytes were manually changed for this fan-out work.

## 2026-10-02 — Completeness Repair is manifest-current

- Brain guidance automatic completeness selection is now bounded to providers present in the current NiakVIO manifest. Historical/retired runtime registrations in `provider-overrides.json` cannot consume Repair/FORCE cycles merely because static cap patterns remain in archived provider infrastructure.
- Brain-LLM `edf7ad0a` intersects repair/static/dynamic cohorts with the current manifest; `ee8f704d` locks the workflow contract. Brain LLM CI #1340 (`36945585325`) is green.
- Current static source search confirms completeness-cap patterns are broader than CoFlix/HindMoviez and include multiple active runtime families; the authoritative dynamic cohort will come from the fresh all-provider census rather than treating every static cap as a defect.

## 2026-10-02 — Brain Repair auto-selects current multi-player/server debt

- Brain-LLM now audits `automation/provider-census-sharded-latest.json` as bounded current execution evidence and automatically promotes providers with observed hierarchical fan-out debt into the Repair guidance cohort, even when census status is FULL/PARTIAL/CANDIDATE and no static numeric cap is detectable.
- Dynamic target selection is prior-only for publication (`proofAuthority=false`): it can make Repair inspect a provider, but FORCE acceptance still requires isolated current-byte materialization, playback, identity and measurable completeness improvement.
- Brain-LLM commits `c4db3132`, `4f50a9b2`, `a864bb15`, `ef1a8fd8`, `62b18e3e`, `7f6cf33f` implement and test current dynamic fan-out audit + automatic cohort union `repairQueue ∪ static coverage debt ∪ dynamic fan-out debt`. Brain LLM CI #1338 (`36945152626`) is green.
- The representative hierarchy semantics are explicit: `announced_player_candidates` is the strongest direct candidate count seen on one response (10 in the 10+9 oracle), top-level server multiplicity is carried by `announced_player_hosts` (2), and `announced_variant_candidates` is the hierarchical total (19). NiakVIO test correction `ca1890d07` locks this distinction.
- NiakVIO Brain Repair runtime family coverage was also repaired generically: `a1794eb2` adds missing generic causal strategy mappings including `search_gap`; `4b6fe792` requires parity with declarative `FAILURE_EXECUTORS`. CORE Workflow Gate #7069 (`36944685487`) and Provider Non-Regression Gate #2776 (`36944685536`) are green.
- No provider runtime was manually edited. Next authority is a fresh `scope=all` sharded census on the new fan-out persistence bytes, then representative Brain-generated CoFlix FORCE only if current execution proves a subset.

## 2026-10-02 — Dynamic fan-out reaches Brain Repair

- Quick census now retains bounded multi-player/server fan-out evidence (`57e4804d`, `85643acb`), and Deep health exposes `returned-subset` (`3d4e2115`).
- Brain-LLM now projects this current sharded evidence into Repair and can classify nominally healthy providers as `variant_coverage_gap` from execution evidence (`32750e4a`). Contract `b71ba927` proves 2 players / 19 announced / 8 returned; Brain LLM CI #1330 is green.
- NiakVIO functional contract `542c8e44` proves hierarchical 10+9 aggregation and `607f5d66` adds it to the actions gate. Architecture contract `d1bb39fd` records the FULL/PARTIAL completeness exception.
- No provider runtime bytes were manually changed. A fresh all-provider census is required before any representative Brain FORCE mutation.

## 2026-10-02 — Multi-provider fan-out completeness cohort

- CoFlix is the representative first witness, not a one-off fix. Current runtime audit also found bounded player/stream enumeration patterns in at least: PapaDuStream, StreamZo, MoviesMod, Cineby and UHDMovies. These are candidate completeness-debt providers, not automatically broken providers.
- Representative validation order stays Brain-first: prove one CoFlix repair end-to-end from current fan-out evidence, then validate at least one additional runtime family before expanding to the wider cohort.
- No provider runtime is to be hand-edited merely to remove caps. Brain must classify the current bytes, produce the bounded provider-owned mutation, and pass isolated rematerialization + playback + identity + non-regression + measurable completeness gain.
- The all-provider sharded census remains the authority source because some completeness-debt providers are currently FULL OK and would be skipped by unresolved-only scope.

## 2026-10-02 — Corrected CoFlix fan-out authority rerun

- Sharded census run `36939639436` persisted successfully from trigger SHA `2029449709c56625d5cf266b2cb417633f9849b0` with 23/46 operational providers and CoFlix still FULL OK. This run remains valid for general provider status.
- It is **not** accepted as final CoFlix hierarchical fan-out authority: the index-only detector was corrected immediately afterwards by `e683528b1fbda70bd2e27c0f8509c265752ebb50` and contract coverage by `f8f5a92e21522eddcec8263dccee9a78f0784abe`.
- Corrected all-provider fan-out authority was re-triggered on `b022bee0e8570935c63a7ff299ff560613e0f047` with `scope=all`. Required evidence before Brain mutation: CoFlix announced indexed choices (expected 19 from the user-supplied 2-server/10+9 menu), explored player requests and returned distinct streams.
- No CoFlix production provider bytes were manually changed. Brain remains responsible for any accepted `variant_coverage_gap` repair after current-byte evidence, isolated rematerialization, identity/playback validation and measurable completeness gain.

## 2026-10-02 — CoFlix index-only menu fan-out is now observable

- User supplied current CoFlix Interstellar player markup proving two top-level server menus with 10 + 9 indexed choices (19 total). The terminal choice URLs are not present directly on those menu buttons, so the prior URL-only response hint extractor could undercount the real fan-out even after hierarchical host counting.
- Generic harness fix `4eca5a96217ad107c7ed0f48dc919a4e1af64b92` adds bounded index-only player-menu counting without depending on CoFlix `cfp-*` classes. It accepts numeric `data-i` / `data-index` / player/server index attributes only in explicit media/player context and records only the count.
- Contract commit `d4bf6c2343e2dc75301ba05c95cdb4ce0d56d4c7` models two server groups with indices 0..18 and requires `declared_player_candidate_count == 19`; an indexed navigation menu without media context remains 0. Bare scalar `data-src="1"`/2 values are rejected as URL candidates, preventing fake player hosts.
- Local contract execution passed before publication. No Coflix/PapaDuStream production runtime bytes were changed; this is observation/Brain infrastructure only.
- Required next authority: rerun current-byte `scope=all` census on/after this HEAD, verify CoFlix/PapaDuStream announced/explored/returned fan-out fields, then let Brain repair CoFlix first if current evidence proves truncation. Any accepted repair still requires isolated rematerialization, identity/playback and completeness gain before persistence.



## 2026-09-28 — Secondary stream-language regressions closed

- `scripts/upgrade_manual_tv_live_regressions_v34.py` now validates the canonical Hindi alias as `["hindi","hi"]`; the historical template may still contain display label `Hindi`, but the validator contract is canonical-code based.
- `tests/core_media_policy_test.py` now expects canonical public language `fr` for generic French/VFF evidence instead of the legacy public identity `VF`.
- These two items are closed on `main`; they are not pending provider-repair work and must not be reintroduced as repair debt.


## 2026-09-28 — CORE.TELEMETRY.V1

- Added global `CORE.TELEMETRY.V1` as the outermost `getStreams()` observer, after `CORE.STREAM_SCORE.V1`; it never mutates stream rows and never blocks or swallows provider errors.
- Telemetry is fail-silent/fire-and-forget and disabled unless a valid host/VPS endpoint plus a stable `installId` are available.
- Identity is never derived from IP. Preferred identity comes from host bridge `globalThis.__NIAKVIO_TELEMETRY_V1__.installId`; `localStorage` key `niakvio.installId.v1` is the fallback. Reinstall dedupe cannot be perfect without host/account continuity.
- Optional `accountPseudonym` must be injected already pseudonymized by the host; raw Nuvio account IDs are never exposed to provider runtime. `sessionId` is ephemeral.
- Payload is privacy-minimal: provider id, media type, success/failure, stream count, latency, install/session ids, optional account pseudonym/app version. No stream URLs, headers, tokens, titles, raw TMDB/media identifiers or IP identity.
- Collector target is the VPS OVH via the host bridge `endpoint`; provider code contains no hard-coded collector URL.


## 2026-09-28 — Telemetry display surface

- The current display surface is a standalone static dashboard in `niakw/eitty-web`: `https://www.eittyweb.fr/niakvio-telemetry.html`.
- No iframe is required yet. `CORE.TELEMETRY.V1` remains observational/provider-agnostic and owns no UI.
- The dashboard now reads live same-origin aggregates from `https://www.eittyweb.fr/niakvio-telemetry-data.php`; collection is accepted only through POST `https://www.eittyweb.fr/niakvio-telemetry-collect.php`.
- The Eitty/VPS collector persists only server-HMAC-hashed install/session/account identities plus aggregates; the dashboard exposes no raw identity. Counters remain zero until a NiakVIO host supplies a stable install identity and the collector endpoint through the existing host bridge.
- Public deployment was verified on 2026-09-28: dashboard HTTP 200, aggregate endpoint HTTP 200 with `collector.status=live`, collector GET rejected by Nginx, and Eitty telemetry CI green.
- Future iframe integration may reuse this page unchanged; host bridge injection remains separate from provider code.


## 2026-09-28 — Secondary contracts fully revalidated on remote main

- Clean worktree from remote `main` passed the targeted secondary chain with exit 0: telemetry privacy contract, Core media/language policy, VF/general manifest metadata consistency, badge assets/versioning, global presentation/player facts, HLS master facts and presentation badges, short-HLS guard, and StreamScore contract.
- Historical tests were aligned with current contracts: versioned manifest names are accepted, subtitle chips remain hidden from runtime `badgeIds` while subtitle tracks/description stay preserved, and telemetry test imports the shared patch helper path correctly.
- These secondary items are closed and must not be reopened as provider-repair debt unless a new regression is observed.


## 2026-09-28 — Local FORCE 13 sandbox verdict persisted

- Brain local evidence from Brain b1fc86b4652417795590f6650c8194202461a813 / NiakVIO a218aaecb1764a74f9e2f26c10f2a10a7c8955f6 produced 6 sandbox-authority candidates: mallumv, 4khdhub, animesultra, vidfast, yflix, allwish.
- NiakVIO isolated current-byte sandbox evaluated all 6 with baseline + candidate Deep health and automatic identity gate: 0 accepted.
- All six mutations were applied/rematerialized successfully but failed to improve required playable proof; no candidate has publication authority.
- Exact outcomes are persisted in evidence/brain-force/2026-09-28/local13-sandbox-report.json and merged into automation/brain-llm-force-memory.json so unchanged provider bytes cannot replay the same rejected mutations.
- The six prior abstentions remain allanime, moviebox, anime-ultime, animesalt, animevost-fr, flemmix; moviesmod remains the single bounded local timeout from that 13-provider generation.
- Next Brain generation must consume these negative outcomes instead of restarting the 13-provider cohort from scratch.
## 2026-09-28 — HTTP-200 interactive challenge classification fixed locally

- MalluMV current evidence reaches MalluMV search/detail/internal pages, `vik1ngfile.site/f/*`, the Viking custom JS asset and `vikingfile.com/fast-download/*` with HTTP 200 but returns no stream.
- Fresh Viking JS inspection proved the terminal media handoff is interactive: `cloudflareCallback(token)` POSTs `cf-turnstile-response=<token>` to the current page and only the JSON response exposes `response.link`. Challenge-token fabrication is not an acceptable provider repair.
- Root classification defect: `scripts/nuvio_tv_probe_tmdb_ci.cjs` inspected anti-bot bodies only on 403/429/503 and `debugStage()` considered only the final provider fetch. A 200 Turnstile page/JS asset followed by another 200 request was therefore mislabeled `provider_network_zero_result`.
- Local patch now inspects bounded HTML and JavaScript response clones for explicit Turnstile evidence on successful responses, never persists bodies, preserves terminal hard-failure precedence, and retains an earlier observed challenge when a later harmless 200 occurs.
- Python `audit_provider_quick_yield.classify_debug_stage` was aligned with the same causal precedence so Node/Python diagnostics cannot diverge.
- Targeted local contracts are green: Node syntax, provider census identity diagnostics, runtime-dispatch diagnostics, WAF census transport merge, WAF browser-session contract, and `git diff --check`.
- Live Viking asset check on 2026-09-28: HTTP 200 `application/javascript`, explicit Turnstile marker detected. Full MalluMV targeted recovery on this Mac is still unvalidated because the local environment has no `TMDB_API_KEY`/`TMDB_ACCESS_TOKEN`; the authorized CI secret path must provide the end-to-end proof before census promotion/reclassification is considered validated.

## 2026-09-28 — Targeted recovery evidence continuity restored

- Confirmed a state-loss bug in targeted Repair persistence: run 36461136076 probed only MalluMV and replaced the same-census targeted snapshot that previously contained 13 providers, causing the other 12 providers to become synthetic `not-probed` inputs during batch refinement.
- The affected snapshot and its predecessor share `sourceCensusRunId=36320455627`; therefore the 12 untouched provider rows were restored from the immediately preceding same-census snapshot, while MalluMV keeps the newer `provider_waf_challenge` evidence.
- `run_provider_targeted_recovery.py` now merges explicit targeted runs into the existing snapshot only when `sourceCensusRunId` matches. A new census deliberately starts a fresh evidence epoch, and sharded runs do not inherit repository snapshots into individual shards.
- Restored current snapshot contains 13 provider evidence rows: 1 newly observed MalluMV row plus 12 retained same-census rows. Refined repair groups return to 13 evidence-specific groups instead of collapsing unselected providers to `not-probed`.
- Current MalluMV evidence is an HTTP-200 interactive Turnstile challenge; this is transport/WAF evidence, not provider-code mutation authority. Playback remains unverified.
- Targeted continuity/refinement/history/workflow tests pass locally, and the restored snapshot was regenerated from committed same-census evidence rather than invented data.

## 2026-09-28 — Bounded response-shape evidence for Brain Repair

- Local post-routing FORCE validation on the restored 13-provider snapshot showed AllAnime cleanly abstaining on both provider patch and provider Bloc, while 4KHDHub abstained on the authored patch and exhausted its Bloc budget. No provider repair was accepted.
- Root evidence gap: current targeted recovery persisted request routes/statuses but discarded response structure; the seven provider-repair candidates therefore reached live HTTP without giving Brain enough safe causal evidence to distinguish schema/parser drift from a missing traversal.
- The TMDB/provider probe now derives a bounded `response_shape` from cloned responses. Bodies remain ephemeral and are never persisted.
- JSON shape contains only validated key names, coarse top type/array bucket and bounded nested schema keys. HTML/JavaScript shape contains only bounded element/function counts and a closed fixed marker vocabulary; no response values, cookies, request headers or query secrets are retained.
- `run_provider_targeted_recovery.py` re-sanitizes the shape before adding it to same-census targeted evidence. Unsafe key names, unknown fields and unknown markers are dropped.
- This evidence is diagnostic only. It does not make a stream playable or grant publication authority; candidates still require isolated current-byte NiakVIO playback/identity/non-regression validation.

## 2026-09-28 — Targeted network evidence redaction

- Durable targeted-recovery evidence now normalizes network paths before persistence. Numeric path segments become `{id}`; long/high-entropy, encoded-JSON and token-like segments become `{opaque}`.
- The retained evidence keeps route family, host, method, status and bounded response shape while dropping opaque values that are unnecessary for causal repair.
- The current same-census targeted snapshot was re-sanitized in place and the refined repair groups were regenerated from that sanitized evidence.
- Verification on the regenerated snapshot reports zero `auth_token` occurrences and zero encoded-JSON `%7B%22` path occurrences.
- This is an evidence-hygiene change only: it does not alter provider status, playback proof, repair eligibility or publication authority.

## 2026-09-28 — Final local Brain repair stop state

- Local Brain/Qwen repair execution was intentionally stopped to avoid further host resource/network impact. No local Brain planner or llama-server process remains running.
- 4KHDHub: final local Brain result abstained with **0 mutations** after provider-patch and provider-Bloc validation attempts. Not repaired.
- YFlix: final local Brain result abstained with **0 mutations** after provider-patch and provider-Bloc validation attempts. Not repaired.
- MovieBox: provider patch was rejected as a no-op; provider-Bloc correction timed out. No publication candidate exists. Not repaired.
- AllAnime final rerun was interrupted before verdict. Anime-Ultime, AnimeSultra and VidFast were not executed in that final sequence.
- MalluMV remains excluded from provider-code mutation authority by current HTTP-200 Turnstile/WAF evidence.
- No census/provider status is promoted by these local Brain attempts; current-byte NiakVIO playback/identity proof remains the only publication authority.

## 2026-09-28 — GitHub FORCE convergence repaired

- GitHub Brain execution is authoritative on current `NiakVIO-Brain-LLM/main`; stale `niakvio-guidance` cache state may no longer block checkout of newer Brain code.
- Cached external guidance is still allowed only after sanitization and now must also match the exact current Brain SHA. A stale Brain revision is discarded instead of reused.
- Explicit architecture/FORCE Learning no longer inherits the ordinary advisor ceiling: its compact advisor generation uses 768 max tokens, 180 s model timeout and one model worker; ordinary Learning keeps 160 tokens / 45 s / two workers.
- Full-cohort convergence is currently owned by `provider-fast-repair.yml`: the current repairQueue is dispatched as an explicit 13-provider cohort with 5 waves, 2400 s total Brain budget and 3 rounds, and stale runs requeue themselves on current `main`. The separate Recognition FORCE lane remains intentionally bounded and does not auto-resume unvisited providers; a first inline resume attempt was reverted after making the workflow invalid YAML.
- These changes close two fleet-scale failure modes directly: stale guidance blocking current Brain code and structural generations being cut off by the old Learning ceiling. Full repairQueue coverage is currently enforced by the explicit Fast Repair cohort/requeue path; Recognition auto-resume remains unresolved architecture debt rather than being falsely marked fixed.
- No provider is marked repaired by these architecture changes alone; provider status changes only after the existing NiakVIO proof and publication gates pass.

## 2026-09-28 — Brain FORCE abstention root cause and receiver alignment

- Fast Repair run `36481857972` visited all 13 current repairQueue providers with 5 waves / 2400 s / 3 rounds: **0 candidates, 0 validated, 13 deferred**, `experiment_variants_exhausted`, not time-budget exhaustion.
- Authoritative Brain executable-guidance cycle on `cf4e6c8e…` completed all 13 requested providers but published `niakvio-force-mutations.json` with **providerCount=0**. Concrete LLM targets repeatedly abstained because no supplied editable unit was considered suitable.
- Brain root cause was fixed upstream: generated `provider_bloc` is now a true invention fallback over generic complete provider functions, not restricted to taxonomy-keyword-matched helpers.
- NiakVIO receiver bound is aligned from 1200 to **1800 chars** for generated Bloc replacement so a complete bounded function rewrite is not rejected after Brain synthesis.
- No provider is marked repaired by this receiver change. Only isolated current-byte candidate evaluation + playable/identity-safe improvement may publish a provider mutation.

## 2026-09-28 — Brain causal-prior WAF override fixed upstream

- Confirmed that several current ROUTE PROVEN providers had identity-safe residential replay with `provider_zero_before_provider_network`, while older targeted seed observations still carried `provider_waf_challenge`.
- Brain adapter already preserved the provider failure in that case, but its causal-prior layer independently re-overrode it to harness, suppressing executable LLM repair.
- Upstream Brain now makes clean current full-provider replay authoritative over the narrower WAF seed; tests for route and chain provider classes are green (Brain CI #885).
- Persistent challenge evidence with no clean provider replay remains transport/harness and must not be “fixed” by fake provider mutations.

## 2026-09-28 — Current authoritative Repair cohort expanded to 14

- Re-read current census run `36484610716` from repository HEAD: repairQueue/symptomaticProviders now contain **14 providers**: 4khdhub, allanime, allwish, anime-ultime, animesalt, animesultra, animevost-fr, flemmix, mallumv, moviebox, moviesmod, vidfast, vostfree, yflix.
- `vostfree` is ROUTE PROVEN with one anime route, latest verdict `provider_waf_challenge`, `testedThisRun=false`, `reconciledFromCarriedGreen=true`, and a consistency note that carried green contradicts the latest lane verdict. It is not valid to claim 13/13 completion or mutate Vostfree from carried evidence alone.
- Brain main now includes semantic stale-publication protection and detailed routing observability; Brain CI #902 is green at `9cb448519e2a8089219e96cb2620e815b79e1a53`.
- Final convergence target is **14/14 resolved with current evidence**, allowing genuine transport/environment cases to remain non-provider mutations rather than manufacturing provider fixes.


## 2026-09-29 — External Brain FORCE winners are persisted independently

- The NiakVIO FORCE receiver no longer requires every targeted external Brain candidate to survive isolated sandbox validation before any winner can be applied.
- Artifact coverage is still checked before sandbox evaluation, but once candidates are evaluated, valid winners are applied independently; rejected candidates are reported through `FIELD_BRAIN_LLM_FORCE_PARTIAL_ACCEPTANCE` instead of aborting the whole batch.
- When `requireExternalForceMutations=true`, unresolved explicit targets now skip canonical Repair with `reason=external-force-only`. This keeps an authoritative Brain-only proof clean: Brain mutation → isolated current-byte sandbox → accepted winners only, with no hidden canonical fallback.
- Safety remains fail-closed when no external candidate passes, when the artifact is stale/incomplete for the explicitly requested candidate cohort, or if a sandbox unexpectedly accepts a provider outside that cohort.
- When at least one validated Brain winner is actually persisted to `main`, Repair now explicitly dispatches `temp-current-bytes-full-provider-census.yml` with `reason=force-winner-persisted`; final census no longer depends only on path filters catching the direct-apply commit.
- This change is provider-neutral: no provider source bytes were modified. It is intended for the current 14-provider Brain FORCE cycle generated from NiakVIO `a7c1ad0013394fb010bcc176447554bc53a8f454`.


## 2026-09-29 — Brain FORCE #147 page-1 structural rejection discovered

- Authoritative Brain cycle on `fdda761b006305d3d89ad448ce34a0f385802522` published page 1/2 for the current 14-provider cohort: 8 providers processed, 6 remaining.
- The page produced two executable-looking `provider_bloc` rows, for `anime-ultime` and `flemmix`, but both minimized edits replace the selected `_routeKind` function identity with an `_extractUrls` function.
- Root cause is in Brain's selected-function envelope guard: its own contract says an explicit wrong function declaration must fail closed, but the implementation returned any explicit `function ...` replacement unchanged when the name differed.
- These two page-1 rows are therefore not accepted repair proof and must not be promoted. NiakVIO sandbox execution is deferred until the complete 14/14 artifact is published and the Brain compiler guard is corrected.
- A Brain fix is staged separately from `fdda761b` so the in-flight #147 continuation cannot be invalidated by a newer Brain main.


## 2026-09-29 — Partial external Brain cohorts no longer block valid winners

- External FORCE coverage is now evaluated in two stages. Before sandbox, an explicit cohort may contain Brain abstentions as long as at least one requested provider has an executable mutation; only unexpected providers or zero executable mutations fail closed.
- Missing pre-sandbox candidates emit `FIELD_BRAIN_LLM_FORCE_ARTIFACT_PARTIAL ... action=evaluate-present-only` instead of aborting valid candidates.
- After isolated evaluation, accepted winners are applied independently and rejected/absent targets remain unresolved with `FIELD_BRAIN_LLM_FORCE_PARTIAL_ACCEPTANCE ... action=apply-winners-only`.
- With `requireExternalForceMutations=true`, unresolved targets do not fall through to canonical Repair. This preserves causal attribution to the external Brain while allowing useful partial progress.

## 2026-09-29 — FORCE #147 receiver/architecture follow-up

- Brain FORCE #147 completed 14/14 but its three raw candidates (Anime-Ultime, Flemmix, MoviesMod) were invalidated upstream by a helper-identity/minimization defect before NiakVIO sandbox publication.
- Brain now guards helper identity before minimization and requires body-only generation for complete function units.
- Audit showed dedicated runtime resolvers already exist for 12/13 current repairQueue providers; Brain scope precedence now prefers those provider-specific runtimes before generic Bloc invention.
- NiakVIO receiver was hardened so partial external batches and partial sandbox winners can make independent progress while unresolved targets remain Brain-only and do not silently fall through to canonical Repair.
- A persisted external winner explicitly dispatches a fresh current-byte full census.


## 2026-09-29 — Targeted transport evidence now gates provider repair eligibility

- A queue split-brain was confirmed: same-census targeted recovery could classify a provider request as current `provider_waf_challenge`, while the census still kept that provider in `repairQueue` because retained ROUTE/CHAIN proof made the status provider-repair-eligible.
- This caused repeated no-progress Brain cycles: the census scheduled the provider for mutation while Brain correctly routed the same fresh targeted WAF evidence away from provider mutation and abstained.
- Added `scripts/merge_targeted_census_transport.py`. It never changes playback/route status; it projects only same-census targeted transport causality into a new `transportRepairEligible` gate.
- A provider with current targeted WAF/challenge, no playable/verified targeted lane, and provider-origin evidence is excluded from `repairQueue` while retaining `ROUTE PROVEN` / `CHAIN REACHED` status and proof.
- A later same-census targeted run that no longer shows the blocker automatically restores transport repair eligibility. Stale targeted evidence fails closed.
- The targeted recovery workflow now applies this overlay, re-renders the census markdown, and persists the targeted evidence + refined batch + census state atomically.
- Current targeted evidence suggests five members of the 13-provider queue are immediate transport-gate candidates: allwish, animesalt, flemmix, mallumv, moviesmod. This is not a claim that they are repaired; the workflow must persist the overlay before the queue reduction is considered validated.


## 2026-09-29 — Repair queue materially reduced 13 -> 8 by causal transport gating

- Same-census targeted recovery run `36540208957` was projected into census authority for census `36531469863-retest`.
- The automated provider repair queue is now **8**, down from 13: `4khdhub, allanime, anime-ultime, animesultra, animevost-fr, moviebox, vidfast, yflix`.
- Five providers are no longer sent to provider mutation because their current targeted probe explicitly classified provider-origin `provider_waf_challenge` with no playable/verified lane: `allwish, animesalt, flemmix, mallumv, moviesmod`.
- Their semantic proof is preserved: they remain NO PROOF / ROUTE PROVEN / CHAIN REACHED as applicable. They are **not repaired** and are not promoted; `transportRepairEligible=false` only moves causal ownership away from provider code until stronger residential/native replay disproves the transport blocker.
- Plain HTTP 403 is deliberately insufficient for this gate. Anime-Ultime and VidFast remain provider-repair-eligible because their current targeted stage is `provider_network_http_error`, not explicit WAF.
- Refined batch routing now maps explicit targeted WAF groups to `harness-compatibility`; the execution router treats `targetedTransportBlockedQueue` as transport-owned so those providers remain observable instead of disappearing from automation.
- This closes the split-brain where census repeatedly scheduled providers that Brain correctly refused to mutate.


## 2026-09-29 — Fresh residential replay narrows causal WAF ownership to MalluMV

- Targeted WAF/browser run `36541459500` completed with a private residential exit and persisted its transport evidence.
- The narrow seed probes still show browser/direct/OkHttp/residential challenge on `allwish, animesalt, flemmix, mallumv, moviesmod`, but full provider replay changes causal ownership for four of them.
- `allwish, animesalt, flemmix, moviesmod`: full residential provider runtime completed identity-safe with zero media and `provider_zero_before_provider_network`. Therefore the challenged seed URL is **not the current causal blocker**; these providers return to ordinary Repair/Brain.
- `mallumv`: remains `HARNESS/ENV BLOCKED` with `residential-exit-all-challenged`; it is the only one of the five still transport/WAF-owned by current evidence.
- Current authoritative queues after the WAF merge: **12 provider Repair** (`4khdhub, allanime, allwish, anime-ultime, animesalt, animesultra, animevost-fr, flemmix, moviebox, moviesmod, vidfast, yflix`) and **1 environment/WAF** (`mallumv`).
- A follow-up consistency fix clears stale targeted WAF fields when full residential provider replay transfers causal ownership back to provider Repair. This is metadata/queue correctness only; it does not promote provider playback.


## 2026-09-29 — Residential replay aggregation bug found; 12/1 split is provisional pending re-run

- The residential full-provider replay summary previously persisted only the lane row's final `debug_stage`. In `audit_provider_quick_yield.run()`, that lane-level stage is the **last adaptive fixture**, while earlier fixtures remain in `samples[]`.
- Therefore a lane could probe provider network/WAF on earlier fixtures and finish on a later `provider_zero_before_provider_network`, then be incorrectly summarized as a clean pre-network provider failure.
- This directly affects the recent causal transfer of `allwish, animesalt, flemmix, moviesmod` from targeted WAF to provider Repair. The current 12-Repair / MalluMV-only-WAF split must be treated as provisional until those providers are replayed with sample-stage-aware evidence.
- `merge_residential_provider_replay.py` now persists only privacy-safe adaptive aggregates: `sampleCount`, `sampleDebugStages`, `sampleStatuses`, and `sampleProgressStages`. Fixture titles, URLs, response bodies, cookies and IP/device data remain excluded.
- `merge_waf_census_transport.py` now evaluates all persisted adaptive sample stages/statuses. Any earlier WAF/network-timeout evidence prevents a later clean fixture from erasing the blocker.
- Regression tests prove both privacy and causal monotonicity. A fresh WAF/residential replay is required before the queue split is authoritative again.


## 2026-09-29 — Explicit WAF target replay selection fixed

- The sample-aware five-provider WAF rerun exposed a second selection bug: `select_residential_provider_replay.py` only selected providers whose current census status was HARNESS/ENV/CLIENT TRANSPORT/NETWORK BLOCKED.
- After the previous provisional WAF merge, four of the requested five had already been moved back to NO PROOF / ROUTE PROVEN, so an explicit five-provider rerun full-replayed only MalluMV. This is why only MalluMV received fresh `sampleDebugStages` / `sampleStatuses`.
- The selector now accepts an explicit provider list from the WAF workflow. Explicit providers are added only when they are still present in current symptomatic/repair/environment/harness/brain queues and authority repair is not disabled.
- The WAF workflow now passes `TARGET_PROVIDERS` into residential full-provider selection. This allows a causal requalification request to replay the exact requested symptomatic cohort even if a previous provisional overlay changed their status class.
- The selector remains provider-neutral and has been added to the external Brain drift whitelist. No provider bytes or proof status were changed by this fix.
- A new five-provider replay is required before treating the current all-13 Repair queue as authoritative.


## 2026-09-29 — Sample-aware residential replay makes all 5 seed-WAF cases provider-owned

- Authoritative follow-up WAF/residential persistence commit `cd593db1e625bb87f48d029cc3f0569ba7d7ec0c` replayed the explicit five-provider cohort with the corrected selector and sample-aware aggregation.
- AllWish movie/tv, AnimeSalt anime, Flemmix movie/tv and MoviesMod movie/tv each ran 4 adaptive fixtures; every persisted `sampleDebugStages` set contains only `provider_zero_before_provider_network`, with no WAF/timeout sample.
- MalluMV has one available adaptive fixture and likewise reports `provider_zero_before_provider_network`, identity-safe, with no WAF/timeout sample.
- Therefore the earlier browser/direct/OkHttp challenge seeds are real observations but **not the current causal blocker** for these provider runtimes. They must not be used to suppress provider Repair.
- Current authoritative census queue is **13 provider Repair, 0 environment/harness/targeted-transport**: `4khdhub, allanime, allwish, anime-ultime, animesalt, animesultra, animevost-fr, flemmix, mallumv, moviebox, moviesmod, vidfast, yflix`.
- None of these 13 is repaired by this reclassification; it only establishes causal ownership. Provider bytes still require actual mutation + isolated current-byte playable/identity-safe proof.


## 2026-09-29 — Vostfree proof restored; Fast 12 exhausted; Learning/Force scope guards closed

- Sharded census had regressed Vostfree from a carried/current green to ROUTE PROVEN even though the durable residential full-provider replay already contained strict current proof: `status=playable_verified`, `raw=1`, `playable=1`, `verified=1`, `identitySafe=true`, `contradictions=0`.
- Root cause was census-chain divergence: sharded census merged the WAF ledger for seed/browser diagnostics but did not run the canonical `merge_waf_census_transport.py` residential replay overlay before persisting status/batch-plan authority.
- Fixes: `5c6bd1ea...` reapplies the residential replay overlay before sharded status/batch planning; `3532850a...` locks the ordering contract. Evidence-only projection `2fe4ed5f...` restored Vostfree to FULL OK, and the following corrected sharded census run `36546710702` persisted **27 FULL OK + 2 PARTIAL OK / 46**, repairQueue **13**, confirming the fix in the normal census path.
- Fast Repair run `36545761845` processed the 12 provider-local Fast cohort and produced **0 candidates / 0 validated**, with `experiment_variants_exhausted` and no time-budget exhaustion. All 12 were handed to Learning; this is real strategy exhaustion, not a timeout.
- Targeted AllWish Learning produced prior `provider_origin_failover_v1` / `provider-owned-origin-header-and-domain-replay` at confidence 0.96. Immediate Fast replay run `36546272263` still produced **0 candidates** with `no_new_repair_experiment`, proving the prior remained inside already-exhausted experiment space.
- Two Learning scope leaks were fixed: cached external guidance is now filtered to the exact routed target cohort (`05622930...`, test `5cf7137a...`), and an empty `FAST_MISSING_PROVIDERS` can no longer erase an explicit `provider_filter` during architecture FORCE (`b454e4a9...`, test `601582e1...`). A targeted AllWish architecture FORCE must now remain AllWish-only end to end.
- External Brain Force source-drift logic now treats only evidence/queue artifacts (census, WAF ledger, Fast summary, Repair batch/handoff/retest artifacts, census markdown, authority/experience evidence) as neutral (`2705dee7...`, test `f0763438...`). Provider bytes/config remain non-neutral and every Force candidate still requires exact `mutationContextFingerprint` plus isolated sandbox validation.
- Current authoritative provider repair cohort remains 13: `4khdhub, allanime, allwish, anime-ultime, animesalt, animesultra, animevost-fr, flemmix, mallumv, moviebox, moviesmod, vidfast, yflix`.
- Current external Brain FORCE was re-triggered on current Brain with reserved structural second-hop context at Brain commit `e2aef03e...`, source NiakVIO `969d1147...`. No current mutation is considered produced until `niakvio-guidance` publishes a matching page/state.

## 2026-09-29 — Fast 12 exhausted; Force receiver now rejects function signature drift

- Fast Repair run `36545761845` selected 12 providers (`4khdhub, allanime, anime-ultime, animesalt, animesultra, animevost-fr, flemmix, mallumv, moviebox, moviesmod, vidfast, yflix`) and finished with **0 candidate providers, 0 retested, 0 validated**, `experiment_variants_exhausted`, `brainTimeBudgetExhausted=false`.
- All 12 were persisted to the LEARN handoff as pending strategy debt. AllWish remains the 13th Repair row and has separate provider-side Learning/Force coverage.
- External FORCE page 1 from Brain `e2aef03e...` produced one AnimeSalt mutation that changed synchronous `req(a)` to async. This is invalid because `resolve()` consumes `req(a)` synchronously.
- NiakVIO `apply_brain_llm_force_mutations.py` now compares named JS function signatures before/after authored provider_patch/provider_js application and fails closed on async/name/parameter drift, restoring original bytes on rejection.
- The receiver-safety script and tests are classified as provider-neutral source drift so an otherwise valid external Force candidate is not rejected merely because this safety guard was added after its source SHA.
- Current census `36547529107` remains **27 FULL OK · 2 PARTIAL OK · 9 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 4 DISABLED**, repairQueue 13. No new provider is claimed repaired by these guard changes.


## 2026-09-29 — Receiver guards invalid FORCE candidates while 9-provider FORCE runs

- Fast Repair run `36545761845` produced 0 candidates / 0 validated providers across its 12-target cohort and handed all 12 to Learning; census remains 27 FULL OK · 2 PARTIAL OK · 9 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 4 DISABLED, repairQueue 13.
- NiakVIO receiver now rejects authored provider mutations that change an existing named function's asyncness/name/parameter signature while still allowing uniquely named helper additions.
- Receiver also rejects provider_bloc rewrites that remove a network helper's request/return semantics. This blocks the invalid AllWish FORCE candidate before sandbox/publication.
- These receiver/test changes are provider-byte-neutral and must not invalidate external FORCE guidance by source drift.


## 2026-09-29 — Manual provider-edit detour reverted; Brain ownership restored

- During the current 13-provider repair effort, the orchestrator incorrectly hand-edited provider runtime Lego files for AllWish, AnimeSalt, Flemmix, MalluMV, MoviesMod and VidFast while investigating provider failures.
- This violated the intended repair architecture: Brain/LLM must author provider-local mutations; NiakVIO must only orchestrate evidence, sandbox application, playable/identity proof, non-regression, census and publication.
- All six provider runtime files were restored byte-for-byte to commit `164159ae8386691a30f9d1b705ba83caba2d495e`. `provider-overrides.json` and `tests/provider_vidfast_multibase_runtime_test.py` were also restored, and the temporary `provider_canonical_title_fallback_contract_test.py` was deleted.
- The exploratory runs generated during the detour are retained only as historical evidence; none of the hand-authored provider changes is a valid repair result.
- From this point, provider-local fixes must originate from Brain guidance/mutation output and pass the existing isolated current-byte validation chain before publication.

## 2026-09-29 — Brain FORCE compiler recovered before next 13-provider cycle

- Provider-local mutation ownership remains Brain-only; the earlier manual provider edit detour stays reverted.
- Brain compact FORCE is CI-green after fixing four repair-mechanism defects exposed by the previous 13-provider zero-mutation cycle: complete-function wrapper normalization is limited to generated `provider_bloc`; authored patch signature drift remains fail-closed; editable-unit budgets cannot overflow; structural call-graph selection follows named callbacks such as `.then(parser)` so second-hop terminal helpers can be exposed.
- Brain CI proof: run `36582057653`, job `109452493685`, green at `e5bbe01b5725acc70dc9602c02cd97074f805ec1` with 189 tests.
- Current NiakVIO census authority remains `36547529107` with 13 provider Repair targets. No provider status changes from the compiler fix alone; the next step is a fresh Brain-authored 13-provider FORCE followed by NiakVIO isolated current-byte playable/identity/non-regression validation.
## 2026-09-29 — Brain FORCE compiler recovered before next 13-provider cycle

- Provider-local mutation ownership remains Brain-only; the earlier manual provider edit detour stays reverted.
- Brain compact FORCE is CI-green after fixing four repair-mechanism defects exposed by the previous 13-provider zero-mutation cycle: complete-function wrapper normalization is limited to generated `provider_bloc`; authored patch signature drift remains fail-closed; editable-unit budgets cannot overflow; structural call-graph selection follows named callbacks such as `.then(parser)` so second-hop terminal helpers can be exposed.
- Brain CI proof: run `36582057653`, job `109452493685`, green at `e5bbe01b5725acc70dc9602c02cd97074f805ec1` with 189 tests.
- Current NiakVIO census authority remains `36547529107` with 13 provider Repair targets. No provider status changes from the compiler fix alone; the next step is a fresh Brain-authored 13-provider FORCE followed by NiakVIO isolated current-byte playable/identity/non-regression validation.

## 2026-09-29 — Single-provider proof milestone: 4KHDHub evidence is now structurally useful

- Fleet-wide FORCE loops are paused as a success metric until one provider is repaired end-to-end. The witness provider is `4khdhub`.
- The first isolated 4KHDHub Brain run produced the first executable FORCE mutation after the compiler recovery, proving the pipeline is no longer stuck at `0 mutation`.
- That candidate was **not accepted as a repair**: it targeted generic ProviderBase `_routeKind` bytes and replaced them with URL-extraction logic, rather than editing the dedicated `PROVIDER.4KHDHUB.RUNTIME.V1` surface.
- Current live 4KHDHub evidence is more precise: TMDB returns HTTP 200; 4khdhub.one search returns HTTP 200; no detail request follows; movie search HTML contains current structural classes including `movie-card`, `movie-card-title`, `movie-card-format`, `movie-card-meta`, and `pagination-container`.
- Provider-neutral evidence collection now retains bounded/sanitized HTML `classTokens` and `idTokens`, with Node execution coverage and workflow path invalidation so changing the probe invalidates targeted evidence.
- Exact targeted recovery run `36591361698` completed successfully for 4KHDHub and persisted the structural evidence for census `36547529107`.
- No provider status is promoted by these evidence changes. 4KHDHub remains ROUTE PROVEN / repair-eligible until a Brain-authored candidate survives isolated current-byte playable + identity-safe validation.


## 2026-09-29 — Brain architecture PR #220 superseded; 4KHDHub witness is the only repair gate

- PR #220 (`brain: Learning architecture evolution proposal`) was audited and closed without merge. It changed only generated architecture proposal JSON/Markdown, was far behind current `main`, and its important concepts are already implemented as executable architecture/tests on current main (`brain_meta_learning.py`, architecture FORCE materializer, causal taxonomy/capability-gap/meta-learning/verification/novelty/promotion layers).
- Do not reopen or merge #220 as a repair dependency; current executable architecture supersedes it.
- Batch repair is paused as a success criterion. The next expansion gate is one provider witness only: `4khdhub`.
- Current 4KHDHub causal proof: TMDB resolves; provider search returns HTTP 200 and current `movie-card*` structural tokens/anchors; no provider detail request follows and no stream is produced. The witness therefore targets provider-side search/detail selection before terminal extraction.
- Qwen2.5-Coder-3B is negative evidence for this witness: after compiler/call-graph/prompt fixes it completed multiple calls but returned only no-op edits. More 3B retries are not useful.
- Brain main is CI-green with a targeted 7B FORCE configuration and compact two-function `route_proven_gap` context. The next provider action must be a Brain-authored 4KHDHub mutation followed by NiakVIO isolated baseline/candidate playback + identity + non-regression sandbox. No provider is considered repaired until that passes and a fresh census reflects it.


## 2026-09-29 — 4KHDHub witness: live class-token prefix collision isolated

- Fresh targeted evidence run `36605262984`, persisted at `af2801c80224d78f953fd942ca3cee27052658f7`, proves current TMDB and provider-origin requests both return HTTP 200 while movie/TV still return zero streams.
- The live 4KHDHub HTML exposes an exact `movie-card` class together with a dense sibling prefix family: `movie-card-format`, `movie-card-content`, `movie-card-formats`, `movie-card-image`, `movie-card-meta`, `movie-card-overlay`, `movie-card-title`.
- Privacy-safe class facts show these are real structural elements, not stale token guesses. In the movie response, `movie-card` appears on mixed `a/div/span` elements while multiple `movie-card-*` children are independently frequent.
- The current provider runtime parses `classBlocks(html, "movie-card")` / `classText(...)` with regex word boundaries around the requested class. Because hyphen is a non-word character, a boundary after `movie-card` also matches `movie-card-format` / `movie-card-content` etc. The parser can therefore promote nested sub-elements as complete cards before title/type/year scoring.
- This is the current deterministic causal hypothesis for the 4KHDHub witness. It is **not yet a validated repair**. Provider bytes remain Brain-owned; the next step is a Brain-generated class-token-boundary mutation followed by current-byte sandbox playback, identity and non-regression proof.
- The targeted probe was extended with privacy-safe `classFacts` (counts/tags/selfHref/nestedAnchors/allowlisted semantic signals only) and a bounded sanitized probe-error field. Two instrumentation regressions were detected and fixed before accepting the final evidence; invalid intermediate probe runs are obsolete.

### 2026-09-29 — Manual provider patch rejected; Brain capability generalized
- PR #224 was closed without merge because its initial 4KHDHub CSS-class fix was hand-written provider code, not a Brain-generated repair. Its generated/materialized provider bytes are not authority.
- The reusable cause is now encoded in Brain profile `html_class_token_exact_v1`: detect class-attribute RegExp builders whose dynamic class is followed by `\\b`, replace the unsafe CSS-token boundary with an exact token terminator, then require ordinary sandbox/playback/identity/non-regression proof.
- The profile is provider-agnostic: no provider IDs, domains, routes or fixture selectors are embedded.
- FORCE Learning now derives scope from current canonical census repair/environment queues; stale Fast operator snapshots no longer veto newer Learning debt.
- Targeted publication now hardens bytes before final minimization and byte proof, keeping published output a minimizer fixed point.
- Rule reinforced: reusable provider bugs must become Brain capabilities; do not retain hand-written provider patches as the system-level solution.

### 2026-09-29 — Learning debt must self-converge across persisted phases
- Fast/Autopilot Learning handoff previously dispatched slot_remaining_minutes=60, which always consumed the entire remaining budget in phase 1 and made next_remaining=0. The long-slot continuation machinery therefore existed but could never continue targeted repair debt automatically.
- Brain-owned Learning handoffs now start with 360 persisted minutes. Each phase remains capped at 300 minutes by brain-learning-lab.yml, leaving a bounded 60-minute continuation phase when debt remains.
- The same budget is used for stale-main FORCE requeue so a valid unfinished generation is not silently reduced to another one-phase run.
- This changes orchestration only; it does not relax current-byte validation, playback, identity, non-regression or publication authority and does not hand-patch provider bytes.

### 2026-09-29 — Materialization proof contract aligned with hardened final-byte order
- Provider non-regression run on the Learning multi-phase orchestration change exposed a stale test assertion, not a provider/materializer regression.
- Single-provider materialization intentionally hardens source bytes before final minimization, validates the minimized hardened text, then performs byte proof and a final hardening assertion.
- The contract test now pins that actual ordering instead of counting the legacy bundle-level assertion twice.

### 2026-09-30 — FORCE Learning requeue permission fixed
- Learning run 36637242526 completed sandbox repair/evidence and sanitized memory, then failed only when stale-main FORCE promotion attempted to re-dispatch brain-learning-lab.yml.
- Exact failure: GitHub Actions returned HTTP 403 Resource not accessible by integration because publish-architecture-proposal had contents/pull-requests write but no actions: write.
- The architecture promotion job now has actions: write, matching the existing continue-learning-slot and complete-cloud-convergence jobs that are allowed to dispatch workflows.
- Contract test pins this permission whenever the architecture job contains gh workflow run brain-learning-lab.yml.
- This is orchestration-only. No provider bytes are hand-edited; provider-local mutations remain Brain-authored only.

### 2026-09-30 — NiakVIO FORCE model routing synchronized with Brain-LLM 7B witness contract
- Current census remained at 9 ROUTE PROVEN / 3 CHAIN REACHED / 1 NO PROOF because no Brain-authored mutation had yet passed current-byte playable + identity-safe validation.
- A cross-repo drift was found: NiakVIO-Brain-LLM commit fb387771780302b3d537e2d0fdcc0f420cca8a38 had already escalated FORCE repair to Qwen2.5-Coder-7B after Qwen2.5-Coder-3B repeatedly produced no-op edits on the 4KHDHub witness, but NiakVIO brain-learning-lab.yml still launched 3B for architecture_force.
- NiakVIO now keeps 3B for ordinary low-cost advisor work, but architecture_force uses Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M with context 16384, one parallel slot, max_tokens 512 and timeout 240s, matching the validated Brain-LLM witness contract.
- The FORCE architecture materializer also receives model qwen2.5-coder-7b. Contract tests pin both 3B normal routing and 7B FORCE routing.
- This is a Brain/runtime capability correction only. No provider bytes are hand-edited; provider-local mutations remain Brain-authored and must still pass isolated current-byte playback, identity and non-regression validation before publication.

### 2026-09-30 — Qwen 7B FORCE feasibility proven on GitHub-hosted Actions
- NiakVIO-Brain-LLM guidance run 36614527989 completed successfully on GitHub-hosted Actions with Qwen/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M, context 16384 and one parallel slot.
- The live log shows the 7B cache restored, llama-server started, one LLM FORCE call completed, and a sanitized executable provider mutation produced for 4khdhub. No OOM/killed condition occurred.
- NiakVIO run 36641082807 failed before model startup only because brain_llm_learning_workflow_contract_test.py still pinned the superseded 3B FORCE values max_tokens=768 / timeout=180.
- The contract is now aligned to the validated 7B FORCE runtime: max_tokens=512, timeout=240, 16k context, single slot, while ordinary non-FORCE work remains on 3B.


### 2026-09-30 — Main-only FORCE guard fixed; 7B still needs a provider mutation witness
- Learning/FORCE run `36643038761` generated architecture output but failed during FORCE promotion because `scripts/enforce_main_only_repository_policy.py` still expected the obsolete dedicated `REPAIR_BRANCH="brain-repair/proposal"` cleanup shape while branch maintenance had already moved to a generic main-only cleanup loop.
- NiakVIO commit `c17a89a69681ee8115ad0fe8843be100f91e0f3f` updated the policy checker to accept the current loop-based delete-only cleanup contract without restoring proposal-branch development. Brain branch maintenance passed on the fix.
- The provider non-regression failure observed on that infrastructure commit remained the known 4KHDHub witness failure (`provider_4khdhub_runtime_behavior_test.py` returned no movie stream); it was not caused by the policy-checker change.
- The replayed 7B architecture FORCE later completed successfully and promoted `bcc9c9bc6b3e3b2f82efee64ac3a57ac551bec35`, adding explicit `terminal_media` recognition to `scripts/brain_meta_learning.py`. This is a generic Brain capability change only.
- Fresh sharded census run `36652937378` on that architecture still reports **27 FULL OK · 2 PARTIAL OK · 9 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 4 DISABLED**, with **13 providers in Repair**. No provider may be claimed repaired from the architecture promotion alone.
- The external Brain guidance cache was then found stale at NiakVIO `33e125e...` with `providerCount=0` / `rows=[]`. Brain trigger commit `00980f128972486f97d5749c306f827bf6702bd5` now replays the single 4KHDHub witness against current NiakVIO `299526d5c53f487302fdbf15f6d66521a6240a72` using the 7B advisor.
- Expansion back to the 13-provider cohort remains blocked until one Brain-authored provider-local mutation survives NiakVIO current-byte playback, identity-safe and non-regression validation.


### 2026-09-30 — Repair-family memory added for 700–800 provider scale

- Repeated 7B cycles left the authoritative census at **27 FULL OK · 2 PARTIAL OK · 13 Repair**, proving that provider-by-provider reasoning is not a viable scaling model for a future 700–800-provider fleet.
- NiakVIO Force sandbox results now carry sanitized `repairFamily` and `mechanismFamily` metadata end-to-end. This metadata contains no provider bytes, domains, routes, credentials or publication authority.
- `scripts/update_brain_llm_force_memory.py` now persists accepted family/mechanism pairs into `validatedFamilies` (schema v2). Entries remain `autoApply=false`, `proofAuthority=false`; every new provider still requires exact-current-byte application, materialization, playable proof, identity and non-regression.
- Brain-LLM now computes provider-independent repair families, ranks validated same-family experience across providers, imports NiakVIO `validatedFamilies`, and has a deterministic `family_replay` path before any LLM call for supported mechanisms. Failed recompilation escalates only the current provider.
- Current Force memory has **0 accepted mutations**, therefore no validated family replay is active yet. Existing 4KHDHub failures remain negative memory and must not be promoted as reusable skills.
- Scaling target: expensive reasoning should trend with **novel repair-family count + exceptional providers**, not raw provider count.


### 2026-09-30 — 13 Repair providers now map to 5 causal repair families

- Brain fleet-scale classification over the authoritative 13-provider Repair queue now groups current failures into **5 causal families**, rather than treating all 13 as independent novel repairs:
  - 7 `route-proven-gap:route-parser`
  - 2 `route-proven-gap:dom-selector-container`
  - 2 `chain-terminal-gap:dom-selector-container`
  - 1 `chain-terminal-gap:terminal-extraction`
  - 1 `provider-transport-gap:provider-transport`
- Family identity deliberately ignores response format (HTML vs JSON), catalogue/media/status metadata and provider identity when those do not change the reusable repair mechanism.
- Until a family has a NiakVIO sandbox-accepted mechanism, only one rotating representative spends novel Force/LLM budget. Siblings remain deferred. Once validated, deterministic family replay may recompile the mechanism on each sibling's exact bytes, still behind all normal proof gates.
- This is **not** a provider repair claim: census is still **27 FULL OK · 2 PARTIAL OK · 13 Repair**. Live validation run: Brain Advisor `36738108323` against NiakVIO `a2be5abfb32cc3a5bdc3f82031f9611a0e851ce5`.

## 2026-09-30 — Secondary Core fixes finalized as release 5.21.86

- Release-finalize trigger commit `cf4dc69daab2b3731b164395ff364544238c0610` targeted accepted main SHA `4c1ffb836fdf2b5e2c072058522a93f7559e225a`. `CORE - Finalize Accepted Release` run `36757225321` (#49) completed SUCCESS, and the corresponding `CORE - Workflow Gate` run `36757225551` (#6920) also completed SUCCESS.
- The finalizer reapplied durable Core/provider patches across all 42 active Provider v3 bundles, reached the provider minimizer fixed point, passed published/static/security/versioning/native Hub46/release-integrity gates, bumped the synchronized release from `5.21.85` to `5.21.86`, bumped all 42 active provider versions, staged generation at `bd787607eb430ca95b27dda2501b756eea250d3f`, finalized at `5d55d7f10af9ab2f09f63973f280fc6c56bdc575`, and atomically pushed that final SHA to `main`.
- Published bundle inspection confirms the secondary Core revisions are materially present, not only described by the trigger. PersianStremio `1.4.101` and VidLove `1.0.103` both contain Stream Identity v12, Stream Presentation v32, Telemetry v2 anonymous fallback, the visible `⭐ Stream Score:` text token, country-aware age badge mappings, and the corresponding global Core markers.
- Secondary contracts covered before acceptance include: catalogue-driven international age classifications (including bare US `R`/PG and country-qualified mappings), enriched player/HLS technical facts, visible StreamScore text projection, anonymous telemetry events to the Eitty collector without fabricated install IDs, and the short explicit-title wrong-content identity guard. The L'Arène / Spartacus regression specifically rejects explicit `Spartacus` rows returned for TMDB TV 331669 by PersianStremio/VidLove while preserving legitimate one-word titles.
- The redesigned StreamBadge public feed was materialized and pinned as immutable v10 before the accepted release.
- Evidence boundary: Core/release/published-byte proof is green. This does **not** by itself prove client rendering for every stream that arrives after an initial provider result, nor live collector/dashboard reachability from every Nuvio runtime. No dedicated named late-arriving-row UI regression was found in the checked release log/history, and the telemetry web endpoint could not be independently exercised by the current web inspection path. Keep those two items as live/client revalidation, not as unproven Core publication claims.

## 2026-09-30 — Provider family architecture documented and Brain-indexed

- Added `PROVIDER_FAMILY_ARCHITECTURE.md` as the canonical composition map for scaling Provider v3 toward hundreds of providers.
- The document separates **GLOBAL** Core Blocs, **FAMILY** reusable provider-level mechanisms, and **PERSONAL** provider DATA/runtime. It lists the canonical Core sequence and shows how a provider-personal `PROVIDER.<ID>.RUNTIME.*` resolver stays behind common security, identity, HLS, presentation, sanitizer, StreamScore and telemetry contracts.
- Runtime/protocol families are explicitly distinct from causal Brain repair families. A validated repair-family mechanism may be deterministically recompiled on a sibling's exact bytes, but never copied as raw provider runtime and never gains proof authority without the sibling's own sandbox/playback/identity/non-regression pass.
- `ARCHITECTURE.md` and `BRAIN_REPAIR_ARCHITECTURE.md` link to the new map. NiakVIO-Brain-LLM public RAG now indexes all three architecture documents at high authority.
- Architecture-only root Markdown drift is now explicitly neutral for external Brain guidance import. This prevents a valid current-byte candidate from being rejected solely because architecture documentation advanced after its source SHA.
- The documentation gate exposed an unrelated stale assertion that still required StreamBadge v8 while the accepted release had already published immutable v10. `ARCHITECTURE.md` and `provider_v3_documentation_contract_test.py` now both pin StreamBadge v10.
- Evidence note: causal family count is dynamic. Live Advisor run `36738108323` recorded `input=13 selected=4 families=4`; older 5-family counts are historical snapshots, not a fixed architecture constant.

## 2026-09-30 — Brain route-proof → runtime-synthesis bridge

- Current unresolved census remains 27 FULL OK · 2 PARTIAL OK · 9 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 4 DISABLED. The dominant provider-repair problem is no longer generic route discovery alone: many unresolved providers already own qualified route/chain evidence but still lack a playable terminal runtime.
- Brain audit confirmed a scaling gap between NiakVIO route authority and Qwen runtime synthesis. Rich provider route knowledge already exists in `provider-overrides.json` (learned/candidate routes, structured request plans, canonical execution preferences, live route evidence), but the Brain advisor previously received that primarily as clipped serialized override text.
- NiakVIO-Brain-LLM now projects that knowledge into a compact sanitized `route_contract` and preserves it through normal and Force prompt budgets. The contract contains route paths, method, role, lanes, non-sensitive header names, canonical route preference and compact live/proven route counts; sensitive query/header values are excluded/redacted.
- Brain CI run `36764118314` proved the initial implementation green on `14d424162e44b2cfcf0a07200fcec6a694e87c9f`; subsequent trigger head `eff926db7a2e1cfc55784ffae288c0c5acf936a5` runs the route-contract-aware family-first FORCE cycle against NiakVIO source `43a31dbcce92da502443b677702f68ed011d0864`.
- This is infrastructure only until a candidate survives NiakVIO sandbox/playback/identity/non-regression proof. Do not count it as a provider repair by itself.

## 2026-10-01 — 5.21.90 provider rematerialization published and byte-verified

- Accepted Core state was finalized by `CORE - Finalize Accepted Release` run `36790437873` (#54). The workflow executed exact checkout `4cf05a256a2ef2a7064459ba61898d7ca850bf2b` (accepted `9a181049...` plus the release-trigger-only commit); exact-sha Workflow Gate run `36790437885` was SUCCESS.
- Finalizer step 5 rebuilt all 42 active Provider v3 bundles, reached the minimizer fixed point, regenerated VF/general-no-anime/VF-no-anime projections, pruned superseded generations, and passed `PROVIDER_V3_STATIC_AUDIT_OK active=42 visible=44`. No provider-local manual repair was introduced in this finalization.
- Release synchronization bumped every published manifest/transport/hash surface from `5.21.89` to `5.21.90`. All 42 active provider versions advanced exactly one patch version and all 42 content-addressed provider filenames changed. Provider-generation SHA: `e35015bad82a5b790cf00302046d6ff9cd0d7415`.
- Pinned native Hub46 was rebuilt for 42 providers; release hashes were regenerated (`core=55 files=6718 patch=6719`) and release integrity passed. Atomic publication succeeded: base `4cf05a256a2ef2a7064459ba61898d7ca850bf2b` → final release SHA `daefc38746adacc4d579b140b34cf9a041a26ff2`.
- Post-push inspection of the exact files referenced by `manifest.json` verified 42/42 published JS bundles contain the current global contracts: Stream Identity `cross-client-player-page-identity-v15`, HLS `native-master-facts-late-batch-v15`, Stream Presentation `all-providers-client-projection-player-facts-age-catalog-v33`, StreamScore `evidence-weighted-global-score-v2`, sanitizer network-evidence v10 plus `implementationVersion:10` short-MP4 guard, and telemetry `privacy-minimal-vps-telemetry-v4-client-install-gated`.
- StreamBadge v11 post-push inspection passed on fusion/dark/light/transparent feeds: each has 309 filters / 17 groups; generic `age-12` matches `12+` but rejects `FR 12+`, while `age-fr-12` accepts `FR 12+`. This prevents duplicate generic/French 12+ classification.
- Evidence boundary: publication/materialization/static/integrity/post-push-byte checks are green. The Mac Desktop Commander endpoint was offline during finalization, and the workflow-originated final push did not create a second post-push workflow suite; therefore no claim is made here about a fresh native-device playback session after `daefc387...`. The published bytes themselves were fetched and inspected after the atomic push.



## 2026-10-01 — Brain #222 published novel 4KHDHub format-gate candidate

- Brain Private-Guided Advisor run `36859533598` (#222) completed SUCCESS on Brain `b63821990e1eeb02f3edb327b8f84a6a1459e595`, pinned to unchanged NiakVIO `d6a3d6396b00ee1ea629e723eb83044cd249a261`.
- Slots 1–4 retained all executed-negative class-selector memory. Slot 1 generated a new deterministic `optional_metadata_format_gate` mutation on exact current provider_bloc bytes; slots 2–4 did not recycle it and produced no additional executable winner.
- Public Force artifact now contains exactly one novel 4KHDHub candidate: mutation fingerprint `24c7624590ce10b4fb93bada35bd3b9f3b819dd944fbe334f08d9fd503156e41`, context fingerprint `7a515c2e3d4a6e82d24c5f4776b7f0c8319a95a53e7b0e6a1511de2f09ebb8d7`, mechanism `optional-metadata-format-gate`.
- This is candidate evidence only, not a repair. The next authoritative step is isolated Repair V6 current-byte application/rematerialization and required movie + TV playable/identity proof with external-Force-only semantics.


## 2026-10-01 13:55 Europe/Paris — 4KHDHub catalogue-query candidate queued from Brain #223

- Repair V6 #254 (`36861067528`) executed Brain candidate `24c7624590ce10b4fb93bada35bd3b9f3b819dd944fbe334f08d9fd503156e41` (`optional_metadata_format_gate`) on isolated current bytes, applied it, rematerialized 4KHDHub, then replayed 8 fixtures. Result remained `no_streams`: 0 streams, 0 runtime errors before and after. The candidate was rejected and persisted in `automation/brain-llm-force-memory.json`; no provider candidate bytes were published.
- Brain main `2931fb97ddf4560246a7161e91159703341cd142` is green in CI #1295 and guidance #223 produced a new executable current-byte candidate for 4KHDHub: fingerprint `a6afd0ce15ea36b47e326e8548593e85c3826063630e30de41ba770707d6f7c6`, mechanism `catalog_identity_query_variants`.
- The new hypothesis is causally distinct from the exhausted DOM-selector family: it broadens bounded catalogue search queries using current TMDB title/original-title/year/season evidence while preserving existing type, title-score, year/season identity gates and terminal extraction. It is Brain-generated, not a manual provider patch.
- Repair trigger retry 191 targets NiakVIO `f90341b9d75c411c497b91706dc8291fb596005d` and requires isolated movie + TV playable/identity proof before any publication. Rejection must be persisted and must not fall through to manual/canonical provider repair.


## 2026-10-01 — Architecture FORCE exact-anchor ownership moved into the materializer

- Learning architecture-FORCE runs #433 (36861325923) and #434 (36864572453) independently failed at the same point after successful provider Learning: Qwen selected the correct allowlisted architecture surface but returned a replace find that occurs more than once in scripts/brain_meta_learning.py. Asking the model to restate an exact anchor did not resolve the ambiguity.
- brain_architecture_force_materializer.py now owns this textual anchoring step. For a repeated replace only, it requires the exact focused source snippet already supplied to the model to occur once in the full file and the model find to occur once inside that snippet. It then widens the intended find with unchanged current bytes until the full-file anchor is unique, applying the same prefix/suffix to the replacement.
- The resolver never guesses between multiple focused occurrences, never changes provider files, never exceeds the existing find/replace bounds, and leaves unresolved ambiguity to the existing fail-closed validator. Telemetry FIELD_BRAIN_ARCH_FORCE_ANCHOR_RESOLVED records only path and bounded counts/lengths, not source content.
- Regression tests cover both exact focused disambiguation and ambiguous fail-closed behavior. This is a Brain/Learning pipeline correction; 4KHDHub remains ROUTE PROVEN until a Brain-produced provider mutation passes isolated movie + TV playable/identity proof.


## 2026-10-01 — 4KHDHub architecture-FORCE replay after anchor resolver

- Brain LLM main `4f57d58c7babc45daf0c891e5c575bce6e286850` is green in CI #1297 (`36865419990`): unit suite and privacy audit both passed. Its speculative one-shot slots retain four-slot deterministic progression while capping post-reservation LLM diversification and suppressing redundant recovery retries.
- NiakVIO `723e5726b0a0c0099e42646bfc25e61713666f44` contains the focused exact-anchor materializer correction after architecture-FORCE runs #433 and #434 independently failed on the same repeated `scripts/brain_meta_learning.py` find.
- The permanent Learning reconstruction trigger is narrowed to `4khdhub`, `architecture_force=true`, budget 60 minutes. This replay must prove the materializer can turn the Brain's architecture intent into a unique allowlisted executable patch, pass Brain architecture tests, and only then promote via the existing direct-main FORCE guard.
- Provider-specific static non-regression remains independently red on the already-known 4KHDHub class-prefix behavior fixture; the current materializer/trigger commits do not modify provider bytes. That existing provider defect is the Brain witness to repair, not evidence that the control-plane patch changed provider behavior.


## 2026-10-01 — Architecture FORCE ambiguity traced to duplicated Brain taxonomy source

- Architecture-FORCE replay #435 (`36866475649`) still failed with `replace find must occur exactly once: scripts/brain_meta_learning.py` even after the focused-anchor resolver. Inspection of the exact `bf027a2c...` source found one and only one duplicated literal line in that file: the `route_transition_graph_v1` entry appeared twice consecutively inside `FAILURE_FAMILY_TAXONOMY`.
- This explains why the resolver could not legally disambiguate: the model was focused on `route_transition_graph_v1`, but the repeated find was duplicated inside the same exact focused snippet, so choosing one occurrence would have been guessing.
- The duplicate taxonomy literal is removed at the Brain infrastructure layer. A source-AST regression guard now rejects any duplicate literal key in `FAILURE_FAMILY_TAXONOMY`; runtime dict equality alone cannot catch this because Python silently retains only the last duplicate key.
- No provider bytes are changed by this correction. 4KHDHub remains ROUTE PROVEN and the latest executed provider candidates `optional_metadata_format_gate` and `catalog_identity_query_variants` remain rejected until a new Brain-produced candidate passes isolated movie + TV playable/identity proof.


## 2026-10-01 — Replay armed after taxonomy-anchor de-duplication

- NiakVIO Brain infrastructure commit `c41de9e8372b93d3b274dcefa13224b744c53899` removes the only duplicated literal line found in `scripts/brain_meta_learning.py` and adds a source-AST regression guard that rejects duplicate literal keys in `FAILURE_FAMILY_TAXONOMY`.
- The prior focused-anchor resolver remains fail-closed; it is no longer asked to choose between two byte-identical `route_transition_graph_v1` anchors inside the same focused source snippet.
- The reconstruction trigger is narrowed to 4KHDHub with `architecture_force=true`. This replay is only an architecture witness: success requires an allowlisted executable Brain patch plus Brain architecture tests. Provider repair still separately requires Brain-generated provider bytes to pass isolated movie + TV playable/identity proof.


## 2026-10-01 — Architecture FORCE contract validation moved inside the transaction

- Learning #436 (`36882904336`) proved the focused-anchor problem is now crossed: after one bounded 7B timeout/retry the materializer emitted `FIELD_BRAIN_ARCH_FORCE_MATERIALIZED edits=1 files=scripts/brain_meta_learning.py`.
- The generated edit was syntactically valid but reintroduced a second literal `route_transition_graph_v1` taxonomy key. The new source-AST contract caught it immediately in `tests/brain_meta_learning_gap_synthesis_test.py`, so the architecture patch was not promoted.
- Root pipeline gap: `validate_materialized_edits()` only ran parser/compiler validation transactionally. The three focused Brain architecture contracts ran only after `--apply`, too late for the materializer's same-run correction loop.
- The materializer now runs the same bounded Brain contracts transactionally after syntax validation and before accepting a generated edit: meta-learning gap synthesis, architecture-force materializer, and self-architecture. A contract failure is wrapped as `MaterializedValidationError`, candidate bytes are restored, and the exact failure is fed into the existing bounded corrective model loop with `mustPassMaterializedContractValidation=true`.
- Regression coverage proves a syntax-valid but contract-invalid edit is corrected in the same `validated_model_plan()` call and never leaks into baseline bytes. This remains Brain infrastructure only; 4KHDHub is still ROUTE PROVEN.


## 2026-10-01 — Architecture FORCE transactional semantic replay

- Brain infrastructure `39c51c3809e1a72798fc88746aa68256df81a88b` passed Workflow Gate #7013 (`36884349311`) including workflow architecture contracts, native provider-loading compatibility and side-effect checks.
- Learning #436 (`36882904336`) crossed the former non-unique-anchor failure and materialized one `scripts/brain_meta_learning.py` edit. The edit was syntactically valid but reintroduced the duplicate `route_transition_graph_v1` taxonomy key; the meta-learning source-AST contract rejected it and no architecture patch was promoted.
- The materializer now executes the focused Brain architecture contracts transactionally before accepting candidate bytes, allowing the existing same-run corrective loop to consume the exact semantic failure and retry before `--apply`.
- Main subsequently advanced only through availability-diagnostics commit `5cf10e3b15851a37d2470219db3f6b27f58f6988`; Brain/materializer/provider inputs are unchanged relative to the green pipeline proof.
- The next 4KHDHub-only architecture-FORCE replay is armed on current main. It remains Brain infrastructure work only; 4KHDHub stays ROUTE PROVEN until a later Brain-generated provider candidate passes movie + TV playable/identity proof.
- Git hygiene: obsolete branch `fix/learning-force-canonical-queue` is now included in branch maintenance deletion when no open PR exists; Brain memory/proposal refs remain retained.


## 2026-10-01 — Daily Domain Refresh outage and chronological-authority fix

- Scheduled Domain Refresh run #1078 (36848172715) failed after successful authoritative resolution because tests/user_provider_manual_evidence_crosscheck_test.py still hard-pinned Flemmix domain substitutions to flemmix.party. Scheduled runs #1069, #1070, #1071, #1072, #1073 and #1078 were red from 2026-09-26 through 2026-10-01; the last scheduled successes were #1058/#1059 on 2026-09-24/25.
- The #1078 artifact proved a second generic defect: Purstream discovery already saw purstream.cat from official Telegram message 114, but equal-score tie-breaking selected older message 109 (purstream.club) because ascending document order beat chronology. The same report showed refresh-generated explicit_current values masking newer official Telegram announcements for HindMoviez (hindmovie.dev) and WookaFR.
- Domain Refresh now treats monotonic Telegram message_id as freshness evidence after trust/semantic safety. A safe high-confidence same-brand newest Telegram announcement may supersede refresh-generated explicit_current; immutable operator_pin remains locked, stale/backup-labelled announcements remain rejected.
- The durable manual-evidence regression no longer pins Flemmix domain values. It protects the DLE/search route family only; current terminal/substitution ownership remains with Domain Refresh.
- No provider domain is manually patched by this fix. The authoritative workflow must rediscover, reconcile, rematerialize, validate and publish current domains itself.


## 2026-10-01 — Domain Refresh #1079 crossed discovery; remaining stale-domain test removed

- Domain Refresh #1079 (36890189793) on f68ecf4d resolved 21 providers and proposed 3 authoritative rotations with no Core mutation: Flemmix -> flemmix.eu, HindMoviez -> hindmovie.dev, Purstream -> purstream.cat. The artifact ordered Purstream Telegram message 114 (purstream.cat) ahead of messages 113/112/109, proving chronological selection now works.
- Publication was still blocked at provider_domain_metadata_reconcile_test.py because that test hard-pinned HindMoviez to hindmovie.icu and WookaFR to wookafr.boston. Those exact current-domain assertions are invalid for refreshable explicit_current providers and are replaced by structural authority/registry consistency checks.
- WookaFR remained on boston in #1079 despite official Telegram message 133 advertising wookafr.blog. The priority wrapper now enforces the declared latest_telegram_domain contract directly: the newest safe high-confidence provider-branded Telegram message outranks refresh-generated explicit_current LKG state. operator_pin remains immutable.
- This remains a generic Domain Refresh pipeline correction. No provider domain is manually edited.


## 2026-10-01 — Main-only PR/branch enforcement restored

- User-required repository hygiene is now enforced structurally rather than by manual cleanup. Scheduled/push Learning may still generate and persist sanitized evidence, but provider-repair and architecture proposal PR jobs are gated to an explicit workflow_dispatch with publish_proposal=true. Architecture FORCE remains the only automatic structural promotion lane and continues to publish validated allowlisted changes directly to main.
- PR #227 (Brain architecture proposal) and PR #226 (Dependabot grouped Actions update) were closed unmerged. Neither proposal was treated as production state.
- Branch maintenance now uses an allowlist instead of a growing hard-coded tombstone list: only main and the read-only persistent Brain memory ref brain-learning/proposals are retained automatically. Any other remote branch with no open PR is deleted; an explicitly requested open PR protects its branch until that PR closes.
- This prevents closed Dependabot/proposal/workbench branches from accumulating and prevents automatic Learning schedule/push runs from recreating review PRs behind the user's main-only workflow.


## 2026-10-01 — Domain Refresh CONFIG-derived URL rematerialization

- Post-publication Verify on domain transaction b7097f7018b2b291dabbea0163f93a1ab6605b02 found a real split-brain: Purstream structured CONFIG and registry were current at purstream.cat, but the exact published Provider CONFIG still retained purstream.club inside observedUrls/origins. Full static audit failed with provider-data-drift even though the narrower domain-only gate had passed.
- Root cause: Domain Refresh projected officialSite/knownSite/officialHub/domainSubstitutions, but treated observedUrls/origins as unrelated DATA even when those entries were mechanically derived from the previous site origin.
- The transaction now rewrites only explicit old-site -> current-site host mappings inside CONFIG observedUrls/origins, preserving unrelated API/CDN/player URLs. Projection-drift detection also recognizes this stale-byte state so an idempotent later refresh rematerializes it even when officialSite is already current.
- Provider lifecycle regression was also corrected to handle ShowBox after it has moved from the current manifest into archived-provider-old state; the prior test dereferenced rows["showbox"] before its archive branch.


## 2026-10-01 — Domain Refresh #1081 closes CONFIG/materialization split-brain

- Domain Refresh #1081 (`36895452117`) completed SUCCESS from base `4066f09b4cbdb10c67de10f16196542765cb5bdb` and atomically published provider stage `8a8ba4540606f820c1492ebfbc37928dd0bb198b` then final release `110db85eff30b1271ce86d02808c535d5fca3664`.
- The run reported `projection_drift=17`, rebuilt 17 affected bundles, passed rollback/stale guards, DNS observation, domain-only Provider v3 static audit, Hub46 projection, release hashes and release integrity, then pushed main successfully.
- Exact post-push Purstream bundle `providers/purstream--nuvio--18f7e1fe73730189.js` now has CONFIG `officialSite=https://purstream.cat`, `knownSite=https://purstream.cat`, observedUrls using `https://purstream.cat`, and origins using `https://purstream.cat`. Historical `purstream.club` remains only as an explicit substitution key to the current host, which is intentional migration memory rather than executable current authority.
- Current authoritative address state after the same live refresh: Purstream `purstream.cat`, HindMoviez `hindmovie.dev`, WookaFR `wookafr.boston`, Flemmix `flemmix.eu`. These are workflow-derived current values, not hand-patched provider domains.
- The remaining Workflow Gate red on the pre-publication control-plane SHA was a stale test assertion in `brain_architecture_deferred_cohort_test.py` expecting automatic push-triggered architecture PRs. The contract is aligned with main-only policy: proposal PR publication is explicit workflow_dispatch + publish_proposal=true; architecture FORCE direct-main validation remains allowed.


## 2026-10-01 — Domain-derived CONFIG projection made comparative/fail-closed

- Post-#1081 lifecycle audit crossed the Purstream drift but exposed Anime-Sama over-projection: published observedUrls/origins had collapsed an intentional historical `anime-sama.to` entry into a second `animes-sama.fr`, while the canonical structured model still retained both hosts.
- Cause: the first derived-URL fix blindly applied every runtime domain substitution to observedUrls/origins. Those lists are mixed knowledge: some values are current-site derived, others are intentional historical/route evidence.
- Domain Refresh now changes observedUrls/origins only when the complete list delta is explained by the explicit domain map. It accepts two exact cases: rewriting published values produces canonical expected values (stale-domain repair), or rewriting canonical expected values reproduces the published list (recovery from the prior over-projection). Any unrelated mismatch remains untouched and fail-closed for its owning pipeline.
- This keeps Purstream club->cat repair valid while restoring Anime-Sama's intentional anime-sama.to + animes-sama.fr knowledge instead of inventing duplicate current origins.


## 2026-10-01 — Domain rollback guard accepts versioned latest-Telegram reuse

- Domain Refresh #1082 (`36897509018`) correctly recovered the over-projected CONFIG knowledge in staging, but the transaction guard stopped publication because WookaFR's latest official Telegram post (message 133) points to historical `wookafr.blog`, while main still held `wookafr.boston`.
- The guard previously recognized fresh historical-domain reuse only from hub/source_redirect labels, even though the authority layer already supports registry-scoped official `telegram_public` address feeds. This made the authority resolver and rollback guard disagree.
- Fresh rollback/reuse evidence now accepts `telegram_public` only when the selected candidate has a positive public message id and the resolver explicitly marks it `latest-telegram-domain chronological authority`. The existing source-authority gate still requires that exact Telegram URL to be configured as an official/authoritative current-address source. Missing message ids remain rejected.
- No failed #1082 bytes were published; main stayed at `de4090a988011a2928573c95c9904334507f42f2`.


## 2026-10-01 — StreamScore estimate visibility, player-language precedence and domain-history recovery

- StreamScore root cause: the global scorer used the 0.60 measured-confidence threshold for unmeasured rows too. A stream proving only real resolution contributes 0.30 video confidence, so many providers never received a grade while richer Kehflix rows did. Measured scoring keeps 0.60; no-network technical estimates use 0.30 and remain explicitly mode=technical-estimate. No video evidence still produces no grade/badge and no missing codec/bitrate/network facts are invented.
- Python and materialized JS scoring contracts are aligned. Python no longer fabricates an 8-bit dynamic-range contribution when bit depth/HDR was absent.
- Player language precedence is now factual player evidence > provider row > manifest fallback. Scalar audioInfo language/lang is lifted into audioLanguage and, when no track array exists, one factual audioTracks row. This prevents provider language=fr from leaving a lang-fr badge when the player proves English.
- Domain Refresh comparison now recognizes prior over-projection even when several historical origins collapsed to one current host. Canonical historical origin rows are restored exactly; this addresses HindMoviez .fit/.icu history lost under .dev without hand-editing provider DATA.


## 2026-10-01 — Badge v12 + global provider projection for StreamScore/player-language

- Current Core source is correct for the reported UI regressions, but exact published provider bytes on main still carried StreamScore v2 and lacked `playerAudioLanguage`; multiple non-Kehflix providers were inspected directly. This is a Core-source -> published-provider projection drift, not a per-provider bug.
- Badge mapping v11 was internally inconsistent: catalogue/feed authority is v11 but `mapping_core_brain_ui_v11_complete.json` still pointed native feeds/publicFeedVersion to v10. Because published snapshots are immutable, v11 is not rewritten. New immutable v12 catalogue/mapping/feed snapshots are added; artwork/filter rows are unchanged, while the mapping now points to v12 feeds and records the technical-estimate StreamScore threshold.
- Global stream presentation revision advances to `all-providers-client-projection-player-language-streamscore-v34` and reads the v12 catalogue. The projection trigger explicitly requires every published provider to rematerialize shared Core bytes; later acceptance checks exact provider JS, not source scripts alone.
- Flemmix runtime source no longer hard-pins a mutable fallback domain. It requires the current Domain Refresh base through provider_lego_options and fails closed if absent. Its regression test derives the current terminal dynamically rather than pinning `.party`.


## 2026-10-01 — Native Lab scope + exact-head reconcile concurrency

- Verify on a8fd67b2 exposed a stale native-scope assertion: current manifest has 42 executable providers while the durable Hub evidence matrix still contains historical Animetsu/ShowBox rows. Activation authority is providers/ lifecycle, not historical matrix cardinality. Native declared-route validation now uses Hub evidence intersected with active_provider_ids(), matching validate_activation_preservation and preserving the historical matrix without resurrecting archived providers.
- Projection Reconcile now uses cancel-in-progress=true. Because publication already rejects when origin/main != event SHA, an older queued/running reconcile is guaranteed non-publishable after main advances. Cancelling it is correctness-preserving and removes hours of needless stale rematerialization.
- A fresh exact-head projection trigger is armed for the shared StreamScore/player-language v34 + badge v12 rematerialization.


## 2026-10-01 — Native declared-matrix gate now honors current lifecycle authority

- CORE Verify on 4d2d9b524c39675e75d6298a3607633a27350dd2 failed only because gate_native_declared_provider_matrix.py loaded the durable Hub-46 scope literally and rejected historical Animetsu/ShowBox rows that are no longer present in the 42-provider executable manifest.
- The regression test already computed Hub scope intersected with active providers, but the gate subprocess reloaded the raw historical file and reintroduced the archived rows. The gate now intersects durable scope evidence with the exact manifest identities before building expected routes.
- Historical evidence remains preserved; no provider is re-enabled or removed from history. This closes validation split-brain so current shared Core StreamScore/player-language bytes can be verified independently of archived scope rows.


## 2026-10-01 — FORCE variant coverage requires verified quality gain

- HindMoviez Brain guidance #227 produced the intended deterministic `bounded_variant_enumeration_before_cap` current-byte mutation, but the generic Force sandbox previously accepted only by stream-count improvement + identity. More 480p mirrors must not count as repaired 720p/1080p/2160p coverage.
- Deep health evidence now records bounded safe `returned_quality_heights` from provider-returned stream metadata, independently of probe count.
- The isolated Brain Force evaluator applies a mechanism-specific gate for `bounded-variant-enumeration-before-cap`: no runtime/malformed/identity/playable/stream regression, automatic identity gate, and a verified coverage gain. Reported quality labels alone are insufficient; at least one playable-height, audio-language or reachable-host dimension must improve.
- The Hub46 strategy-plan contract now permits historical matrix rows to be absent from current catalogue only when provider-disabled-lifecycle proves `archived-provider-old`. Animetsu/ShowBox history is preserved without resurrection.


## 2026-10-01 — FORCE readiness contract follows mechanism-aware sandbox

- Workflow Gate on `63a0ba62906a72651576ed93b3a3131174784f56` proved the new isolated Force evaluator tests pass, including verified variant-coverage acceptance/rejection. The only gate failure was a source-string contract still requiring the former two-argument `evaluate_pair(baseline, candidate)` call.
- Readiness now asserts the mechanism-aware evaluator call and `mechanism_family` wiring instead of the obsolete literal signature.


## 2026-10-01 — HindMoviez verified-coverage Force sandbox armed

- Brain guidance #227 produced deterministic fingerprint `58d187d1e146a38bc0c5226fcd665674679b07c32ea5ba37b2cfa4eb2a7e1e82`, family `bounded_variant_enumeration_before_cap`, from NiakVIO `8cc61b4af6f2003f5e2712d84102b004385b5eed`. It removes the outer `out.length>=4` break from the bounded `k<8` aggregation loop and leaves inner per-source limits intact.
- Since guidance generation, only tests/harness/MEMORY and availability diagnostics changed; provider bytes did not. `availability-history.json` and `availability-report.json` are now explicitly classified as neutral guidance drift, consistent with release-hash policy that already excludes them from executable authority.
- Repair trigger retry 192 requires external Brain mutation and mechanism-specific verified variant coverage. Stream-count-only gain cannot win.


## 2026-10-01 — Explicit FORCE can validate completeness debt on FULL providers

- HindMoviez Repair/FORCE #257 (`36928384531`) did not execute the Brain candidate. Baseline proof was healthy but only 480p (`qualityHeights=[480]`, max playable 480), then the sandbox bridge skipped the candidate as `outside-current-repair-scope` because HindMoviez is census FULL OK. The evaluation row correctly had `executionObserved=false`, so no negative Force memory entry was created.
- This exposed a scope-model mismatch: census FULL proves playable identity, not exhaustive variant coverage. Brain can now diagnose `variant-coverage-gap` on FULL providers, so explicit FORCE must be able to sandbox such a current provider without changing routine Repair scope.
- `apply_brain_llm_force_mutations.py` now keeps routine calls bound to `repairQueue`, but an explicit `--provider` may target any current non-disabled census provider. The bridge still has no publication authority and exact context fingerprint + isolated rematerialization/playback/identity/coverage proof remain mandatory.
- Targeted Learning follows the same rule only under explicit `architecture_force=true`: routine Learning remains repair/environment scoped, while explicit FORCE may carry current FULL providers as `completenessProviders`. Disabled/unknown providers remain rejected.
- This is pipeline capability only; HindMoviez is not yet claimed repaired. The existing Brain candidate must now be re-executed and prove a real playable quality/language/host coverage gain before publication.


## 2026-10-01 — Completeness FORCE workflow contract alignment

- Workflow Gate on `f58a1ab605dbd297a2304ee0528d7b70b635ca2d` reached the Brain Learning workflow tests and failed only because `brain_learning_push_target_workflow_test.py` still required the obsolete literal error text `target provider is not in current census repairQueue`.
- The runtime workflow already implements the intended rule: routine Learning remains repair/environment scoped; explicit architecture FORCE may target a current non-disabled provider carrying completeness debt. The regression assertion is aligned to the new fail-closed message.
- Provider Non-Regression on the same SHA passed HindMoviez and UHDMovies contracts before stopping on the pre-existing 4KHDHub movie=[] witness; no new provider regression was introduced by the scope change.


## 2026-10-01 — Dynamic fan-out evidence after PapaDuStream/Coflix reports

- User evidence exposed the same blind spot on two current FULL providers: PapaDuStream Interstellar exposes about six HD players but the client surfaces one 480p stream; Coflix exposes about nine servers but the client surfaces one 480p stream.
- Static runtime inspection was not sufficient. Coflix's current published provider contains its multiflux runtime, which requests the provider player list and loops over up to eight rows; the obsolete Coflix REST runtime is not present in published bytes. Therefore missing fan-out can occur during player exploration/resolution/validation even when provider source nominally loops over several candidates.
- Added provider-agnostic redacted response fan-out diagnostics. When provider code consumes HTML/JSON/text, the harness records only candidate-player count, candidate hostnames and advertised quality heights; raw candidate URLs and response bodies are not persisted.
- Deep health now distinguishes announced candidates, explored candidate requests/hosts, returned stream hosts/qualities, and playable output, with diagnostic states `announced-not-explored`, `explored-not-resolved`, `quality-gap`, or `fanout-observed`.
- Brain planner and FORCE evaluation now receive these fields. FULL OK remains playback/identity status; fan-out evidence is separate completeness debt and never grants publication authority by itself.
- No provider-specific bytes were changed. PapaDuStream and Coflix are representative cases for Brain-driven completeness repair after current-byte evidence is collected.


## 2026-10-02 — FULL-provider completeness census unlocked for hierarchical fan-out

- User evidence clarified Coflix as a hierarchical fan-out case: about 2 provider servers, each exposing many terminal choices (roughly 10 + 9 in the observed title). PapaDuStream is another representative multi-player case. Counting server rows is not equivalent to stream completeness.
- Current Coflix and PapaDuStream runtimes both still contain local aggregate caps of 8 around shared crawler output, so a provider can remain FULL OK while later valid variants are silently dropped.
- Brain-LLM main now owns the corrective mechanism: deterministic `bounded_variant_enumeration_before_cap` can widen exact current-byte shared-crawler functions from small header caps to a bounded 16 server / 32 aggregate stream envelope. No provider-specific production bytes were manually edited.
- NiakVIO fan-out diagnostics already distinguish announced candidates, explored player requests, returned hosts/qualities and playable output, but sharded trigger pushes previously forced `scope=unresolved`, excluding FULL providers from fresh evidence.
- Sharded census orchestration now exports an explicit `census_scope` from the trigger file and honors `scope=all` on push. Contract coverage was extended.
- Next: run current-byte all-provider census, inspect Coflix/PapaDuStream fan-out states, send Coflix first to Brain as the representative repair, require isolated rematerialization + identity/playback + verified completeness gain, then cross-check PapaDuStream before cohort expansion.


## 2026-10-02 — Hierarchical completeness pipeline closed end-to-end; authority rerun pending

- User clarified the representative Coflix topology: the observed title exposes about **2 provider servers**, with roughly **10 + 9 terminal choices** behind them. A server/player count is therefore not a stream-completeness count.
- NiakVIO Deep health now derives a bounded hierarchical count `announced_variant_candidates`: provider responses can announce player hosts, then consumed responses from those player hosts contribute their strongest redacted candidate count per host+route. This preserves provider-specific HTML/JSON parsing while giving Brain a generic `player -> variants` completeness signal.
- The Brain-safe projection and FORCE evaluator carry this field. FORCE can accept a `bounded_variant_enumeration_before_cap` candidate for a verified increase in distinct returned streams when sampled playability does not regress, identity/runtime/malformed-request gates stay clean, and current fan-out evidence proves multiple announced variants.
- Brain-LLM main `fdc92fd522956a69b4f5b2da2fbb8fdf213e8059` is CI green (Brain LLM CI #1328 / run 36936177346). Its deterministic compiler recognizes numeric shared-crawler caps such as `i<8` / `out.length<8`, keeps traversal bounded, and separates a 16-player/server envelope from a 32 aggregate-stream envelope. No Coflix or PapaDuStream production bytes were manually edited.
- Sharded census trigger pushes can now explicitly request `scope=all`; this is required because Coflix/PapaDuStream are currently FULL OK and were previously excluded from fresh completeness evidence by unresolved-only runs.
- Earlier census runs #235 / #236 are superseded by the later hierarchical-output and FORCE-validation changes and must not be used as final authority unless their prepare job demonstrably pinned the newer source SHA.
- 4KHDHub remains unresolved. Published bytes do contain `PROVIDER.4KHDHUB.RUNTIME.V1`, but still contain the class-boundary implementation under test. Brain candidate fingerprint `a21eaa643f0c0df30a14cffe8bbb7d3bef3258ea9217de595565902b189eb974` (`exact_class_attribute_tokens`, Brain f1503702...) was rejected by isolated FORCE with `required_category_playable_proof:movie,tv`; it was not published. This is an unresolved Brain/validation problem, not a successful materialization.
- Provider Non-Regression now scopes provider-specific behavior tests with the materialization impact classifier: `none` keeps global/static contracts only, explicit provider impact runs the corresponding behavior tests, and `all` still runs every provider-specific test. This prevents a known unresolved provider from blocking unrelated control-plane changes without hiding it when provider bytes may actually change.
- Next authority sequence: gates green on the pipeline HEAD -> one final `scope=all` current-byte census -> inspect Coflix and PapaDuStream hierarchical fan-out fields -> Brain repairs Coflix first -> isolated rematerialization/playback/identity/completeness proof -> PapaDuStream family cross-check -> only then consider wider cohort expansion.
