

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
