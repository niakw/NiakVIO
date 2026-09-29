

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
