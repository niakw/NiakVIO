

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
