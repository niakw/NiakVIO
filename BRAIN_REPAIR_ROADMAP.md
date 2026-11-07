# NiakVIO — Brain Repair Roadmap and Decision Register

> **Baseline: 2026-11-07, Europe/Paris.** This is an evidence-led execution roadmap, not a claim that broken providers are repaired. All acceptance decisions must reference the **actual tested source SHA and immutable run/artifact**. Do not confuse historical/carry-forward FULL status with freshly decoded playable content.
>
> **Source checkpoint:** NiakVIO `3b07e1f5a4430f7111708047fccce815ec645756` · Brain-LLM `1f7096babc0bf8ca80d0878238d912e630b47a3f` (new Brain CI pending at document creation). Current protected working branch: `main` in both repositories; no repair candidate has publication authority.

## 1. Decision dashboard

| Indicator | Last evidenced value | Interpretation / limitations |
| --- | ---: | --- |
| Verified repairs performed end-to-end by Brain | **0** | The only admissible success is generated → applied → materialized → executed → media decoded and identity-verified → regression-safe → persisted. |
| Active repair queue | **17** | From `automation/provider-census-status.json`; includes two replay-only historical candidates. Do not extrapolate to all 800 future hubs. |
| Current census inventory | **46** | 21 FULL, 3 PARTIAL, 2 CANDIDATE, 10 ROUTE, 2 CHAIN, 1 NO PROOF, 2 REGRESSION, 5 DISABLED. |
| Fresh full proof in last authoritative census | **0/21 FULL; 0/3 PARTIAL** | All FULL/PARTIAL positive classifications were **carried**, not replayed in that census. Run `42321364499`; see `PROVIDER_CENSUS_STATUS.md`. |
| Best demonstrated mutation | **Generated + applied + differing executed bundle bytes** | Hosted run `42358985990`, 4KHDHub; nevertheless **0 accepted, 0 decoded**. |
| Reader exploration gap in that proof | **16 announced candidate players, 1 explored** | Announced 1080p/2160p is not a verified playable variant. Baseline and candidate both returned 0 streams. |
| Film/series/anime fixture mismatch in Brain sandbox | **Correction landed, CI gates passed** | NiakVIO `f751cc7` + `09b9c10`; Core gate `42358986168`, non-regression `42358986032` succeeded on `09b9c10`. End-to-end Brain still failed. |
| Learning after an executed but ineffective decoded patch | **Correction landed, CI pending** | Brain-LLM `057d8d0` / `1f7096b` recognizes `decoded_repair_no_new_fixture_control` and preserves real player-fanout gains before rotating source locality. Do not count as repaired until tested. |
| Security release gate | **Unverified/blocked** | `42359913056` displayed SUCCESS but log said `FIELD_CODEQL_STALE_2531_DEFERRED` due to source drift. A green retirement workflow is **not** confirmation #2531 is closed. |
| ~800-provider/hub ambition | **Not qualified** | No evidence of autonomous repair portability at that scale. No mass import/promotion before family-level proofs. |

Useful evidence: [Hosted 4KHDHub run](https://github.com/niakw/NiakVIO/actions/runs/42358985990) · [Brain evidence report](automation/hosted-repair-evidence/42358985990.json) · [Evaluation](automation/hosted-repair-evidence/42358985990-evaluation.json) · [Current census](automation/provider-census-status.json) · [Architecture](BRAIN_REPAIR_ARCHITECTURE.md).

## 2. Milestones and exit criteria

Status key: **DONE** = correct scoped implementation with exact test evidence; **IN PROGRESS** = change published but incomplete validation; **BLOCKED** = prerequisite or observed failure; **OPEN** = not yet evidenced; **GATED** = intentionally withheld until prerequisite succeeds.

| ID / priority | Milestone | Status 2026-11-07 | Observable exit criterion | Blocker / decision |
| --- | --- | --- | --- | --- |
| R0 · P0 | Reconstruct current state and prevent false success | DONE (inventory), continuous | Record branch, SHA, model SHA, run, artifact, fresh/carry status, actual decoded and accepted count for each conclusion. | Census positive carry-forward is not live media. |
| R1 · P0 | Correct category-specific strict fixtures and durations | DONE for code+Core tests; runtime still insufficient | Existing film/TV/anime contracts chosen by manifest; accurate duration and TMDB; same immutable fixtures before/after; no wrong-episode promotion. | Current strict evaluation has 0 decoded proof. |
| R2 · P0 | Learning-feedback parity for executed decoded failures | IN PROGRESS | Brain CI on `1f7096b` green, regression proves rotation only with unchanged player/variant coverage; next hosted run uses this exact Brain pin. | Existing NiakVIO hosted workflow used older Brain `0f559e4`. |
| R3 · P0 | Recover **one** causal Brain-generated repair | BLOCKED | A provider selected from real queue has new verified decoded playable media, correct title/TMDB/season/episode/duration, no lost previous fixture; final code bytes and SHA proven. | Qwen3B proposals mostly no-op/deletion or non-improving regex edits; 4KHDHub 16 players/1 explored. |
| R4 · P0 | Observe complete multi-reader/quality fanout | OPEN | Evidence for every discovered candidate's visited/skipped reason, terminal host, quality, audio and subtitles; improve exploration with bounded budgets and no unproven 4K badge. | Announced candidates are not crawled or playable candidates. Diagnose harness/runtime/network separately. |
| R5 · P0 | Recover historical CANDIDATE program exactly | BLOCKED | Recover precise historical program and bundle SHA; compile and replay on current source; validated current media. | `animesama-co` and `animevostfr` remat from current DATA is **not** historical Brain patch replay; run `42351582449`: 0 playable/0 verified. |
| R6 · P1 | Stronger generator A/B benchmark (without changing validator) | OPEN | Compare Qwen local vs interchangeable stronger hosted/GPU model on same source SHA, immutable fixtures, permitted scopes, token/time/budget; record edit causality, compiled/applied ratio, new decoded proof and spend. | Hosted/model secrets, cost ceiling and allowed sanitized context must be configured and verified. More parameters alone are not proof. |
| R7 · P1 | Family representative qualification | GATED on R3 | ≥1 independent Brain-produced, executed and decoded-positive repair for each *relevant observed failure family*, with regression suite. | Must not infer a family fix from same-name providers or manually injected fixes. |
| R8 · P1 | 17-provider bounded repair sweep | GATED on R7 | All eligible rows classified into repaired/blocked/external/needs-generation with per-provider evidence and no silent retry loop. Update census only on verified proofs. | WAF, replay-only, harness and network cases cannot be masqueraded as JS repair failures. |
| R9 · P1 | Protect TMDB, TV S00, miniseries and special-event identity | OPEN (live proof) | Cross-client end-to-end proof for film, ordinary episode, miniseries, cross-catalog special/S00 and wrong-season negative controls: **selected content = decoded terminal content**. | Prior Core heuristics do not identify opaque media. Explicit Spartacus S00/S201 ambiguity remains an acceptance test, not a claimed fix. |
| R10 · P1 | Release/security and projection | BLOCKED / separate | Actual CodeQL alert inventory and final gate verified on exact current HEAD; source→published bytes/manifest hashes reconciled; TV/Mobile/Desktop proof where available. | #2531 retirement success was deferred; published output is not implied by a repo commit. |
| R11 · P2 | Learn from validated solutions and expand toward hubs | GATED | Retain failure signature, executed candidate, negative outcomes and verified reusable function/Lego/pattern; prove one unseen hub/provider per family before scale. | 800-hub ambition unbenchmarked; no fresh verified family repair yet. |

**Recommended priority now:** R2 (exact-SHA CI) → R3/R4 together (one causal repair plus full reader coverage evidence) → R6 if the same evidence shows generator limitations → R7 → R8. Continue R9 and R10 as independent guards; never weaken identity, security or terminal decode criteria to make the scoreboard green.

## 3. Full current 17-provider queue

Source: committed `automation/provider-census-status.json` on checkpoint NiakVIO `3b07e1f`. Status/diagnostic labels are *not* current decoded playback proof.

| Provider | Census state | Dominant recorded symptom | Required lane / caution |
| --- | --- | --- | --- |
| `4khdhub` | ROUTE PROVEN | provider_network_zero_result ×2 | Brain synthesis; last attempted DOM token change yielded no streams; inspect player enumeration and source parsing. |
| `allanime` | CHAIN REACHED | provider_network_zero_result | Brain synthesis; HTTP 200 can still hide GraphQL errors/null results; prior Qwen no-op. |
| `allwish` | NO PROOF | provider_waf_challenge ×2 | Evidence/authority investigation first; do not synthesize provider JS on a WAF-only diagnosis. |
| `animekai` | REGRESSION PROVIDER | provider_network_exception | Brain synthesis only if proven code-causal, otherwise network/transport classification. |
| `animesalt` | ROUTE PROVEN | provider_waf_challenge | Browser/residential/transport differentiation before mutation. |
| `animesama-co` | CANDIDATE OK | provider_network_http_error | **Replay-only** historical candidate program; not a new mutation workflow. |
| `animesultra` | ROUTE PROVEN | timeout | Investigate execution/runtime and upstream latency; strict budgets. |
| `animevost-fr` | ROUTE PROVEN | provider_network_http_error | Classify provider-vs-upstream HTTP cause before coding. |
| `animevostfr` | CANDIDATE OK | provider_network_zero_result | **Replay-only** historical candidate program; not current DATA remat. |
| `flemmix` | ROUTE PROVEN | provider_waf_challenge ×2 | WAF/harness differential before provider mutation. |
| `mallumv` | CHAIN REACHED | provider_network_zero_result | Brain synthesis on real movie fixtures; earlier syntax-only edit failed strict proof. |
| `moviebox` | ROUTE PROVEN | provider_network_exception ×2 | Network exception layer and actual reader traversal. |
| `moviesmod` | ROUTE PROVEN | provider_waf_challenge ×2 | WAF/harness separation first. |
| `uhdmovies` | REGRESSION PROVIDER | provider_network_zero_result | Representative Brain synthesis; repeated Qwen no-op debt retained. |
| `vidfast` | ROUTE PROVEN | provider_network_http_error ×2 | Upstream HTTP, media identity and correct terminal reader. |
| `vostfree` | ROUTE PROVEN | provider_waf_challenge | WAF/harness differential before mutation. |
| `yflix` | ROUTE PROVEN | provider_network_exception ×2 | Separate environment, DNS/TLS and provider logic evidence. |

**Do not reinterpret WAF/network errors as proven provider-code breakage.** Do not hide the two candidate replay rows simply because source synthesis cannot process them. The queue remains 17 until independent, trustworthy criteria justify a status change.

## 4. Explicit failure taxonomy and decision log

| Observed signal | Owner to test first | Decision / next experiment | Never claim |
| --- | --- | --- | --- |
| Model no-op, cosmetic regex tweak, pure deletion | Brain generator, context/RAG, selection, negative-memory | Reject and rotate exhausted source unit; compare same fixture with stronger generator if repeated; persist failure fingerprints. | 'Provider repaired' from a valid JSON edit. |
| No candidate materialized despite generated patch | Brain converter, compiler, selector, apply/remat | Prove exact changed source bytes, bundle SHA and runtime trace; fix infrastructure before touching provider. | 'Executed' from generated diff alone. |
| Category/duration wrong | Brain evaluation/harness | Static + realistic movie/TV/anime strict fixtures on both baseline/candidate. | 'Model failed' from unrelated 24-minute anime check. |
| Zero streams, announced but unexplored readers | Provider traversal, Core/harness/network observation | Enumerate bounded players, actual visited/skipped causes and network progression before selecting edit locality. | 1080p/4K playable from metadata or announcement. |
| Candidate reproduces same 0/0 media result | Brain feedback and generation locality | Archive immutable negative; avoid repeating same unchanged program without genuinely new evidence. | Acceptance or promotion from byte difference. |
| Candidate historical label, patch bytes missing | Brain persistence/replay | Locate original program + full bytes and replay; otherwise mark unrecoverable and reconstruct with Brain under a new track. | Current DATA remat = historical candidate replay. |
| WAF, DNS, TLS, HTTP challenge, browser-only access | External/harness/transport | Diagnose egress and client differential; preserve negative. | Provider JS broken solely due to GitHub CI challenge. |
| Wrong TV season/S00/episode, opaque player | Core identity + provider extraction + client | Decode terminal identity or keep unverified; negative controls for S00/S201 and separate mini-series. | TMDB match from title alone proves correct video. |
| CodeQL job 'success' with drift/deferred diagnostic | Security workflow | Read log marker, alert API state and current HEAD Final Gate, then decide manual policy route. | Alert dismissed without explicit closure evidence. |

## 5. Definition of a verified repair

All boxes must be met for **one** concrete fixture, with no regression on previously passing fixtures:

- [ ] Exact source repository SHA, Brain SHA, manifest/fixture version and model identified; no undisclosed manual override.
- [ ] Failure reproduced, responsible layer and immutable baseline evidence recorded.
- [ ] LLM-generated candidate is a **causally substantive** change; not no-op, pure deletion or ad-hoc fixture cheat.
- [ ] Candidate compiled, applied, materialized, and exact executing bytes/bundle SHA recorded.
- [ ] Same content fixture replayed before/after with media player/server candidate exploration recorded.
- [ ] Terminal stream is **really decoded**; content identity, TMDB ID, season/episode or S00, duration, language, quality and headers checked as applicable.
- [ ] At least one new verified playable control; prior passing controls preserved; other declared lanes remain explicitly unresolved until tested.
- [ ] Negative/positive experiment and reusable family mechanism persisted in Brain Learning/RAG.
- [ ] Security, Core and provider non-regression gates run at the exact tested SHA; current source and published projection reconciled.
- [ ] Only then update status/census, `MEMORY.md`, this roadmap and release artifacts.

## 6. Decisions needed if progress stalls

**D1 — Generator**: After two genuinely distinct, source-backed generation attempts per representative family without a useful executable edit, benchmark stronger generation *on the same verified fixtures* instead of increasing blind retries. Compare success, latency, cost, privacy and regressions. Keep local Qwen for observation/routing if helpful.

**D2 — Transport**: If website/reader works only in browser or residential egress but not Node/client, invest in harness/Core transport reproduction before provider-code mutations.

**D3 — Provenance**: If exact historical candidate patch bytes are unrecoverable, label the replay gap explicitly; start a Brain reconstruction experiment, never transfer the historical 'CANDIDATE OK' badge as current proof.

**D4 — Scale**: Do not dispatch all 17 as 17 separate free-form generations until at least one validated family mechanism exists; benchmark controlled representative family waves first.

**D5 — Media correctness**: A playable URL without verified selected episode, season, duration and actual terminal decode does not close R3 or R9.

## 7. Maintenance and evidence update rules

1. Update this table only after checking `main`, actual HEAD, model pin, authoritative census state, latest hosted artifact, CI logs, security and any concurrent writes.
2. Each update records **tested SHA vs current HEAD**, outcome, relevant run/artifact, what was and was not executed, and unresolved limitations. An in-progress or superseded run never proves the newer HEAD.
3. Back claims with observable artifacts, not GitHub job color alone. A green workflow that emits `DEFERRED`, `SKIPPED`, `publicationAuthority=false`, or zero decoded media remains non-success.
4. Persist meaningful work in `MEMORY.md`; update `BRAIN_REPAIR_ARCHITECTURE.md` on structural pipeline changes.
5. Prefer Brain-owned fixes (observability, prompt/RAG, tooling, compiler/apply/remat, deterministic validator, learning persistence); do **not** manually fix a single provider to mask Brain incapacity.
6. Keep this document as a decision register. Its numbers are a timestamped snapshot, not an automatically refreshed live dashboard. Compare with the cited current JSON and CI before deciding.
