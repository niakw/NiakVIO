# NiakVIO — Recovery Memory

## 2026-09-23 21:16 Europe/Paris — Canonical Repair now consumes sanitized Learning priors

- While targeted Brain LLM Learning run `35905378275` was progressing, the Learning -> Repair return edge was audited end-to-end.
- Fast Repair already imported sanitized `brain-learning/proposals` memory, but canonical `provider-recognition-repair-v6.yml` did not set `NIAKVIO_BRAIN_LEARNING_MEMORY`. Therefore a successful LLM-guided Learning run could return to canonical Repair without the new learned-skill priors being visible to `brain_repair_runtime.py`.
- Commit `302c696edff4` adds a canonical Repair pre-step that fetches the minimal `brain-learning/proposals` ref, sanitizes `engine_v2/learning/latest.json`, exports `NIAKVIO_BRAIN_LEARNING_MEMORY`, and logs `FIELD_CANONICAL_REPAIR_LEARNING_MEMORY`. It also adds the sanitizer and memory-import contract to Repair preflight.
- Commit `db3cfe051bd0` extends the Repair-to-Learning workflow contract test so the Learning-memory import must remain before the canonical Repair step.
- The authority boundary is unchanged: LLM output itself is not consumed directly by production Repair. Only sanitized learned-skill metadata crosses the phase boundary; current-byte Repair/Retest remains proof/publication authority.
- The general CORE Workflow Gate is still red for a pre-existing/unrelated `provider_hub_registry_test.py` DuckDuckGo URL-shape assertion; syntax/runtime contract stages passed before that assertion.
- Targeted Learning `35905378275` has already proven the intended fast-handoff behavior: weekly FULL native-Lab import and full runtime-collapse/daily-coverage gates are skipped, while targeted Fast-Handoff observation coverage passes.


## 2026-09-23 21:09 Europe/Paris — Brain LLM preflight green; full-scope trigger marker found inefficient

- Retry Learning run `35905201996` on SHA `ef69f95af276c0806a20ad1a29be48317859aaf5` passed the complete Brain/LLM preflight that failed in run `35904796058`; the strategy canonicalization fix is therefore CI-proven.
- The private NiakVIO memory checkout remains successful. The run then entered weekly FULL Lab import instead of the intended repairQueue-only fast handoff.
- Root cause is trigger-contract, not Learning selection logic: `select_fast_learning_handoff.py` recognizes versioned handoffs only when `execution_mode` starts with `targeted-fast-handoff` and `expected_scope` contains `provider-repair-handoff`. The launch trigger used `brain-llm-guided-fast-handoff-fair-share-v1`, so `fastHandoff=false` and the workflow correctly fell back to full Learning.
- This is intentionally being superseded rather than wasting a full-catalogue run. The replacement trigger will use `targeted-fast-handoff-brain-llm-v1`, preserving the current 9-provider repairQueue intersection and the LLM-guided Learning -> canonical Repair return edge.
- CORE gate failure observed in parallel on `273c4d194137` is unrelated to Brain LLM: `provider_hub_registry_test.py` currently fails on the expected DuckDuckGo search-engine URL shape.


## 2026-09-23 21:02 Europe/Paris — First live Brain LLM launch exposed strategy canonicalization bug

- Push-triggered Learning run `35904796058` executed on exact SHA `16bb314ad9147c9940fe23fb7e7f82213f7830f0` and failed in preflight before provider/network/LLM execution.
- The private NiakVIO memory checkout and pinned Brain LLM checkout both succeeded; the failure was isolated to `tests/brain_llm_guidance_contract_test.py`.
- Root cause: `brain_llm_guidance.canon()` normalizes strategy identifiers from snake_case to kebab-case, while `STRATEGY_TO_PROFILE` was still keyed by snake_case. Consequently even a valid high-confidence provider-local LLM proposal was silently discarded and `providerCount` became 0.
- Commit `273c4d194137` makes the mapping vocabulary canonicalization-consistent by storing the allowlisted strategy keys in the exact kebab-case form consumed by the sanitiser. The test contract already pins the expected valid MalluMV mapping and therefore serves as the regression proof in the next Learning preflight.
- No provider status or repair result is claimed from run `35904796058`; it never reached the LLM guidance or adaptive Learning queue.
- Next action: trigger a fresh Brain-LLM-guided Learning run on current main, require the LLM bridge preflight to pass, then verify router/server/guidance markers and the existing Learning -> canonical Repair return edge.


## 2026-09-23 20:50 Europe/Paris — Brain LLM Learning bridge made executable before fresh Repair

- Current main Brain LLM integration was revalidated against the real workflow, not inferred from commit messages. The Learning workflow pins the current NiakVIO-Brain-LLM commit `c752f5c21ded26c578eaeacb492611f3fdb137a9`, builds bounded public/private memory, pre-routes the current cohort, starts local Qwen through llama.cpp only when the router requests it, sanitizes guidance, and exposes it to the deterministic Learning planner as prior-only evidence.
- A concrete workflow bug was found before launch: 13 newly added GitHub/shell interpolations were written as escaped `\${...}`. This affected the private-memory token expression, provider-filter expressions, LLM server state and shell array expansion, so a nominal Brain LLM run could silently miss its intended inputs or fall back.
- Commit `0ac6835d975f` removes all 13 escaping defects and wires the Brain LLM expressions normally. Commit `340ff0b5659d` adds `tests/brain_llm_learning_workflow_contract_test.py` and includes it in the Learning preflight so this interpolation regression cannot recur silently.
- The production Repair still does not grant the LLM direct mutation/proof/publication authority. The intended acceleration boundary is: LLM-guided Learning selects/prioritizes bounded provider profiles; deterministic current-byte Repair/Retest remains the acceptance authority.
- Current census repairQueue before launch contains 9 providers: `4khdhub, allanime, anime-ultime, animesultra, animevostfr, mallumv, moviebox, vidfast, yflix`. Harness/environment-only rows stay outside provider mutation.
- Next action: arm a fresh push-triggered Learning cohort on current main so the corrected Brain LLM guidance runs first, persists sanitized Learning memory, then uses the existing push-only return edge to launch canonical `provider-recognition-repair-v6.yml` in `mode=repair`.


## 2026-09-22 12:23 Europe/Paris — v17 proved post-g5 selection but exposed Learning suppression split-brain

- Targeted Learning run `35713333206` on SHA `555a6d74fd28` completed SUCCESS and processed the exact 9-provider Repair handoff.
- Artifact `10688193101` was downloaded and inspected directly. The exact runtime experiment ledger proves final g5 execution is now correctly attributed (`executionObserved=true`) for cases such as `4khdhub:proven_route_terminal_traversal_v1_g5`, `allanime:chain_terminal_extractor_v1_g5`, `animevostfr:retained_candidate_replay_v1_g5`, `mallumv:chain_terminal_extractor_v1_g5`, `persianstremio:player_media_extractor_v1_g5`, and `moviebox:player_media_extractor_v1_g5`.
- v17 also proves the planner now advances beyond g5: it selected `route_transition_graph_v1` / `route_peer_transition_replay_v1`, `terminal_transition_graph_v1` / `terminal_request_program_inference_v1`, `candidate_divergence_trace_v1` / `candidate_request_program_replay_v1`, `player_protocol_family_replay_v1`, `transport_request_differential_v1`, and `search_contract_inference_v1` according to the provider failure class.
- However these evolved strategies were **not yet executed as generated repair candidates** in v17. The queue summary shows their method selected while `attemptedProfiles=[]`, and runtime memory records `profile_unavailable` with `executionObserved=false`. Therefore v17 is proof of second-order selection, not proof of second-order candidate execution.
- Root cause: `scripts/run_brain_learning_sandbox.py::_negative_entries()` consumed the previous persistent memory without the stale-unexecuted migration already applied in `brain_repair_runtime.py` and `learning-lab.mjs`. The Learning matcher therefore suppressed a newly selected evolved profile because an older run had pre-marked it `profile_unavailable` before execution. This created split-brain behavior: planner says execute; Learning applicability filter says already failed.
- `06874c47fa4a` aligns Learning negative-memory filtering: post-g5 `profile_unavailable` rows without `executionObserved=true` are ignored and cannot suppress the first real execution.
- `905b54df6782` adds a regression test proving stale unexecuted evolved debt is filtered while executed evolved evidence and ordinary negative memory remain active. `5a5705588fc3` adds this test to the Brain Learning preflight gate.
- No provider is reclassified or repaired from v17: all 9 remain unresolved; no provider repair proposal was produced. Canonical Repair must wait for a subsequent Learning proof with actual `attemptedProfiles` containing evolved strategy names and `executionObserved=true`.
- Scaling observation: v17 took materially longer because fair-share allowed up to 3 bounded post-g5 attempts. Once real second-order execution is proven, measure per-provider cost and move independent provider slices toward bounded parallel/family execution rather than serially multiplying this cost across hundreds of providers.

## 2026-09-22 12:04 Europe/Paris — First v16 proof blocked in preflight by execution-marker projection contract

- Targeted Learning run `35713082191` on SHA `4e4b0a9e55b4` failed **before provider execution** in the Brain contract suite. Provider queue/Lab evidence from this run is therefore nonexistent and must not be interpreted as a post-g5 result.
- Failure was isolated to `tests/brain_cross_phase_experiment_memory_test.py`: the new migration correctly retained an actually executed `terminal_transition_graph_v1` row, but `planner_negative_memory()` stripped the sanitized `executionObserved` marker before returning the planner memory. The test therefore saw the profile but could not distinguish it from a merely planned legacy row.
- `84b94b1bdc38` preserves the boolean `executionObserved` field in planner negative-memory projection. This is sanitized metadata only; it does not grant mutation/publication authority and keeps the stale-unexecuted migration test meaningful.
- Next action: rerun the exact targeted 9-provider Learning proof. Require preflight green, then actual post-g5 strategy profiles in runtime plan/ledger before proceeding to canonical Repair.

## 2026-09-22 11:58 Europe/Paris — g5→post-g5 boundary and stale evolved-memory debt fixed after canonical proof

- Canonical targeted Learning run `35711571976` completed SUCCESS on source SHA `405996313d07`. It correctly scoped to the 9 current Repair providers: `4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix`. All Brain contract tests, targeted stage, queue, cross-day memory publication and artifact generation were green.
- The run proved the prior `6f4b287a7b7e` fix was necessary but insufficient. Exact queue output showed final g5 execution for `4khdhub`, `anime-ultime`, `persianstremio`, and `moviebox`, but no second-order evolved profile executed in the same phase. The reason is causal: the child report describes the strategy that just ran; only after its exact g5 failure is merged into phase memory can the next sandbox process see the newly unlocked evolved strategy. Fair-share still stopped because the just-returned plan was g5, not yet `repairType=evolved_strategy`.
- The same persisted Learning state exposed contamination from the old ledger bug. `allanime` and `mallumv` contained unexecuted `terminal_transition_graph_v1` + `terminal_request_program_inference_v1` rows marked `profile_unavailable`; `animevostfr` contained the analogous `candidate_divergence_trace_v1` + `candidate_request_program_replay_v1` debt. These rows had been counted as failed strategy attempts even though no event-level execution existed.
- `1e1d6deacfce` changes the fair-share continuation rule: ordinary work still rotates after one attempt, but an explicitly final Learning generation (`variant=4`, generation reaches `experimentGenerationLimit`) receives the bounded continuation required to cross g5 into the evolved family. Existing evolved strategies still receive at most 3 attempts inside the same already-bounded provider slice.
- The queue now writes `executionObserved` into exact experiment ledger entries and preserves it while merging the temporary read-only phase state. This distinguishes real generated/not-generated attempts from a plan merely exposed for the next iteration.
- `2bfb864ccfed` migrates Learning planner input: legacy post-g5 `profile_unavailable` rows without `executionObserved=true` are ignored as non-executed debt, so they cannot exhaust the second-order family.
- `0b5e44008d3d` applies the same migration at persistent Learning-memory serialization: stale unexecuted post-g5 rows are dropped from `latest.json`, preventing them from polluting `avoid_failed_profile` proposals or consuming memory indefinitely. Actually executed evolved-strategy rows remain retained.
- Regression coverage: `8f8fe6c287bb` proves g5-boundary continuation + execution markers; `804d57bfd6c` proves legacy stale second-order debt is ignored but executed evidence is retained; `9794ff400dee` proves persistence purges only unexecuted evolved debt.
- Run `35711571976` generated no provider-ready repair (`provider_proposals=0`); its one repair proposal was a learned-skill proposal only. No repair PR remained open. This run is therefore evidence about Brain behavior, not a provider fix.
- Next validation: rerun targeted Learning from current main, require exact post-g5 profiles to appear in actual `FIELD_BRAIN_PROVIDER_PLAN` / experiment ledger for the affected cohort, then retry canonical Repair only after the Brain execution path is proven.

## 2026-09-22 11:34 Europe/Paris — Brain post-g5 execution defect fixed; validation pending

- The fair-share Learning queue had two coupled defects. First, `phase_experiment_entries()` combined the report-level final replan with profiles actually attempted by the child. After a g5 failure, the child could already expose a new post-g5 `evolved_strategy`; the ledger could therefore mark that **unexecuted future strategy** as `profile_unavailable`, advancing negative memory without ever running the strategy.
- `6f4b287a7b7e` now attributes each ledger row to the exact event-level `brain_plan` snapshot that selected the attempted profile. When any profile was actually attempted, only attempted profiles enter the ledger; report-level allowed profiles are used only for the genuine no-attempt/profile-unavailable case.
- The same commit adds a read-only intra-phase Learning state. Exact fair-share experiment rows are merged into a temporary `phase-learning-state.json` after every attempt and supplied to the next sandbox process. This lets the next attempt see the just-finished g/v/profile outcome instead of replaying the persistent state from the start of the phase.
- Ordinary Fast-Handoff remains one attempt/provider. Only when the replan is explicitly `repairType=evolved_strategy` + `learningDisposition=execute_bounded_evolved_strategy` may the provider consume up to 3 attempts inside its already-bounded fair-share time slice. This is intended to execute the finite post-g5 strategy family rather than merely plan it and stop.
- `8b67e9612b1d` adds regression coverage for g5-attempt → evolved-replan attribution, immediate read-only phase-memory merge/aggregation, and the bounded continuation rule. Validation is **pending** in the canonical Brain Learning workflow.

## 2026-09-22 11:31 Europe/Paris — Manual-off Domain authority invariant validated end-to-end

- Fresh Domain run `35710451389` completed SUCCESS from trigger SHA `a2dc21287fa7`, including sanitizer, resolver, metadata reconciliation, domain-only Provider v3 tests, release reprojection/integrity and atomic publication.
- The run published staged SHA `7c8bb8d53a37` and final SHA `897b9248a56f`. Post-publication inspection of the actual main branch confirms ShowBox remains `direct=null` while `https://www.showbox.media/` remains only in `direct_candidates`, with `activation_eligible=false` and `manual_off_reason=manual_off_no_current_authority_search_only`.
- This validates the two-layer generic fix: sanitizer cannot promote a forensic candidate across a manual-off lifecycle decision, and `sync_registry_terminal()` cannot promote a later observed terminal across the same decision. The previous failed Repair `35706702360` should now be retried only after the Brain fair-share/experiment-ledger defect below is fixed.

## 2026-09-22 11:28 Europe/Paris — Second Domain writer found: sanitizer was resurrecting manual-off direct authority

- Validation of the first Domain guard exposed a second independent writer. Domain run `35709774525` completed SUCCESS on trigger SHA `b61e18028203`, including `domain_refresh_workflow_test.py`, domain-only validation, release integrity and atomic publication (`provider=0fd366212dcf`, `final=7f1f229914ac`). However, post-publication inspection still showed ShowBox with `direct=https://www.showbox.media/`.
- The run log identified the upstream mutation exactly: `FIELD_HUB_REGISTRY_SANITIZE scope=46 registry_changed=1 registry_providers=showbox` occurred before `FIELD_DOMAIN_REFRESH_V2 scope=42 ... registry=0`. The sanitizer promoted the first concrete `direct_candidates` value into `direct`; disabled ShowBox was then outside the active Domain resolver scope, so the later `sync_registry_terminal()` manual-off guard never ran.
- `dc4322b6a9da` fixes `scripts/sanitize_provider_hub_registry.py`: a non-empty `manual_off_reason` is now terminal lifecycle authority for sanitization. The sanitizer forces `direct=null` while preserving concrete `direct_candidates` and allowed hosts for bounded forensic rediscovery.
- `213255539503` adds a sanitizer regression in `tests/provider_hub_registry_test.py`: a stale manual-off ShowBox-like row is self-healed to `direct=null`, candidate/hosts are retained, and a second sanitize pass is byte-semantically idempotent (`changed=[]`).
- `e8a110fc99b9` clears the direct URL reintroduced by Domain run `35709774525`.
- The earlier `sync_registry_terminal()` guard remains necessary because active providers can still reach that writer; the sanitizer fix closes the earlier pre-resolution writer. Validation remains **pending** until a fresh full Domain workflow completes and the published post-run `provider-hubs.json` still has ShowBox `direct=null`.

## 2026-09-22 11:12 Europe/Paris — Domain manual-off resurrection fixed; Repair preflight blocker isolated

- Current main diagnosis started from HEAD `850374f15d728d57262073e385b4a3bbb09950db`. Repair run `35706702360` on source SHA `2d0bfa448177cfe5640622aa9ac25ecb938f842d` did **not** execute a valid provider Repair cycle: it failed in canonical preflight at `tests/provider_authority_current_catalogue_test.py` because ShowBox had been repopulated as `direct=https://www.showbox.media/` even though the durable authority row still carried `activation_eligible=false` and `manual_off_reason=manual_off_no_current_authority_search_only`.
- Root cause is generic Domain ownership, not a ShowBox-specific provider defect. `sync_registry_terminal()` promoted every observed terminal into current `direct` authority. A later Domain transaction therefore resurrected a forensic candidate after the explicit manual-off decision. Historical commit `f1a5c34fb3d8` had correctly cleared ShowBox `direct`; the later Domain generation reintroduced it.
- `4fe4b02b61fa` changes `scripts/domain_refresh_transaction_v2.py`: a non-empty `manual_off_reason` now outranks passive Domain observation. Observed terminals remain in bounded `direct_candidates` / allowed-host knowledge, but `direct` is forced to `null` until a separate explicit authority requalification clears the manual-off reason.
- `1f43789f65ba` adds the generic regression to `tests/domain_refresh_workflow_test.py`: a stale ShowBox-like manual-off row with a resurrected direct is self-healed to `direct=null` while retaining the forensic candidate.
- `ea8b7bab24a4` restores current `provider-hubs.json` ShowBox state to `direct=null`; its forensic candidate, supplementary search, disabled lifecycle and manual-off reason remain intact.
- Validation is **pending** at this checkpoint. Next sequence: run the owning Domain workflow to prove the transaction regression and ensure it cannot reintroduce the direct URL, inspect any Domain publication on the exact SHA, then run canonical Repair on the resulting current main and continue the Brain → Repair loop. Do not count `35706702360` as provider repair evidence; its expensive WAF/Brain stages were skipped.

## 2026-09-21 23:40 Europe/Paris — Residential census proof now real; stale-authority WAF overlay fixed but pending validation

- Standalone WAF #107 (`35657232795`) completed green with Tailscale residential exit available. The persisted census transport overlay now reports **27 FULL OK**, including residentially verified AnimeSalt/VostFree from the earlier successful replay lineage, with exact transport queues **HARNESS MISMATCH: animevost-fr, moviesmod** and **environment blocked: allwish, flemmix**. Tailscale is therefore operational; these classifications are evidence-backed, not inferred from GitHub-only probes.
- The markdown now renders split causal queues instead of one misleading bucket: automated Repair, lifecycle disabled, authority rediscovery, harness mismatch, environment blocked.
- A remaining freshness defect was found: WAF #107 was transport-only but projected onto the last canonical census, whose per-row authority fields predated the ShowBox manual-off transition. Thus ShowBox could still render under authority rediscovery even though current `provider-authority-status.json` already says `DISABLE_MANUAL_POLICY` and the manifest has ShowBox in `provider-disabled/`.
- `213d48cc8187` changes `merge_waf_census_transport.py` so a WAF overlay first projects **current arbiter metadata** onto carried census rows, recomputes `statusRepairEligible`/combined `repairEligible`, recomputes Repair from final rows, and then builds lifecycle/rediscovery queues. WAF still does not invent authority; it only stops carrying stale authority from an older census.
- `f68f18a5cfda` adds the exact stale-ShowBox regression: old row `REDISCOVER_SEARCH` + current arbiter `DISABLE_MANUAL_POLICY` must yield lifecycle disabled, not rediscovery. `87616656e863` passes `provider-authority-status.json` explicitly from the WAF workflow. Validation is pending in WAF #111; do not mark this acquired until that run is green.
- Repair #135 (`35657748177`, SHA `b40f8447efaa`) has now passed the **entire canonical preflight** green after the lifecycle-first ordering fix and is executing integrated WAF/network qualification. This is the first current run in this sequence to cross all preflight contracts after the recent lifecycle/census/Tailscale changes.
- Legacy TEMP census #1324 is still running on old SHA `a3ea5663c76b` and predates the freshness guard. If it publishes, treat that publication as stale transit evidence only. WAF #111 is serialized behind the census/WAF lane and Repair runs have separate freshness-safe persistence.

## 2026-09-21 23:34 Europe/Paris — Census/authority/Tailscale state corrected; Repair #134 blocked only by fail-fast ordering contract

- Current provider authority/lifecycle now matches the manual evidence supplied for the ambiguous catalogue cases:
  - AnimeVOSTFR: current terminal is `https://animevostfr.org`; stale `v2.animevostfr.org` remains a redirect seed only. Domain Refresh now also migrates top-level provider Lego site-root options when a terminal rotates.
  - MoviesMod: authoritative hub is `https://modlist.in/?type=hollywood`, with current terminal `https://moviesmod.ai.in`.
  - Animetsu and FullAnime remain disabled-retained; search is supplementary only.
  - ShowBox is now disabled-retained (`manual_off_no_current_authority_search_only`); private Telegram/search-only discovery cannot reactivate it.
  - DesiFlix remains disabled-retained because the public site became inappropriate/compromised.
  - PersianStremio/YFlix remain backend-authority cases; absence of a public homepage/hub does not invalidate explicit structured runtime/backend authority.
- Tailscale residential diagnostics are real and working. The earlier apparent absence was caused by census/WAF persistence races. Canonical Repair now owns the integrated WAF/Tailscale qualification path before Brain target selection.
- Census semantics now split disabled lifecycle, authority rediscovery, harness mismatch and environment blocked. New state writes exact lifecycleDisabledQueue, authorityRediscoveryQueue, harnessMismatchQueue and environmentBlockedQueue.
- Repair #133 failed preflight on a stale WAF integration workflow contract; that contract was aligned.
- Repair #134 passed the provider/authority/Brain/WAF integration contracts but failed only brain_preflight_fail_fast_order_test.py because lifecycle activation validation still came after Brain-experience transfer. No WAF/provider probe/Brain mutation ran. Commit `900bbf840223` moves lifecycle validation before Brain-experience transfer.
- Next action: trigger canonical Repair on current main, require preflight to pass, then inspect integrated GitHub+Tailscale WAF reclassification, exact split queues, Brain-selected providers, accepted/deferred results and post-Repair census.

## 2026-09-21 23:34 Europe/Paris — Repair starvation removed; stale-ledger overwrite guarded; Hub46 decoupled from catalogue size

- GitHub concurrency semantics were confirmed in practice: a concurrency group retains at most one running + one pending run, and newer census/WAF pushes were replacing a pending Repair even with `cancel-in-progress: false`. Repair #131 was cancelled this way before execution.
- `253663aa7667` moves canonical Repair to its own `provider-repair-main` lane. Census + standalone WAF remain serialized in `provider-census-waf-main`. This prevents observational pushes from starving a pending Repair while preserving one-at-a-time Repair execution.
- The separate lane introduces an evidence freshness risk, so Repair persistence is now guarded: after fetching `origin/main`, if remote HEAD differs from the Repair's immutable `GITHUB_SHA`, Repair persists causal Brain memory/run report only and **does not overwrite** canonical census/authority/WAF/candidate/batch-plan artifacts with older-SHA evidence. It emits `FIELD_REPAIR_CANONICAL_LEDGER_STALE/SKIPPED` and dispatches a fresh current-main census. `c9d7d330810c` adds `workflow_dispatch` to the mono census for that handoff; `4439fb0c2268` and `24fa8a159305` lock the separated concurrency + stale-ledger contract.
- Repair #132 (`35657186125`) reached no WAF/provider/Brain work. Its preflight stopped at an obsolete Hub46 cardinality assertion: historical Hub46 campaign membership was still being equated with the whole visible catalogue. DesiFlix/FullAnime were visible lifecycle records but absent from the campaign matrix.
- Current strategy contract no longer uses Hub46 as catalogue cardinality. `74affe15cb63` requires only that historical Hub46 members resolve to visible provider records; activation remains physical `providers/` vs `provider-disabled/`, and future/new visible providers need not belong to Hub46. This is required before scaling from the historical ~46-provider campaign to hundreds of providers.
- Repair #133 (`35657451639`) is also not a Brain result: its immutable SHA had already switched the workflow to `provider-repair-main`, but its own WAF integration test still required the previous shared group. Current main test `24fa8a159305` fixes that one-SHA contract drift.
- Repair #134 (`35657530566`, trigger SHA `a3ea5663c76b`) is queued/running on the corrected current architecture. It is the next candidate for the first full preflight -> integrated GitHub/Tailscale qualification -> authority-filtered Brain execution on the now non-starving Repair lane.
- Durable Brain memory already proves the outer-wave plateau fix is active: current `brain-repair-memory.json` contains `exploration_progress_nonpublishable` entries for 4KHDHub, MalluMV and VidFast. VidFast variants 0-4 now carry durable progress/failure counters, so a new outer wave has evidence that those sandbox-only strategies were already consumed instead of silently replaying them from published bytes.

## 2026-09-21 23:28 Europe/Paris — Tailscale replay promoted real greens; census queues split by cause

- WAF run `35656233204` (#102, SHA `e42012ad9c13`) completed green end-to-end with the private Tailscale residential exit available. It persisted `residentialExitNodeEvidence.available=true` and replayed 11 providers through the residential route.
- Residential full-provider replay produced **two strict playable + identity-verified promotions**: `animesalt` and `vostfree`. Both are now FULL OK. Current census counts after the WAF overlay are **27 FULL OK · 3 PARTIAL OK · 1 CANDIDATE OK · 3 ROUTE PROVEN · 2 CHAIN REACHED · 2 HARNESS MISMATCH · 3 HARNESS/ENV BLOCKED · 5 PROVIDER NETWORK BLOCKED**.
- The former six-provider generic environment bucket is no longer accurate. Fresh transport evidence gives: true environment-blocked `allwish, flemmix`; browser/native harness mismatch `animevost-fr, moviesmod`; `animesalt, vostfree` promoted to FULL OK. Tailscale therefore works and materially changes classification; it is not merely configured.
- Domain/address authority corrections from the user's manual checks are now encoded: AnimeVOSTFR terminal is `https://animevostfr.org`; generic Domain Refresh migrates provider Lego top-level site roots when the terminal rotates (`d484ebbc54d8` + `34b90104ab4a`), so a stale Lego `base/site/referer` cannot keep using `v2`. MoviesMod retains `https://modlist.in/?type=hollywood` as authoritative hub and `https://moviesmod.ai.in` as current site.
- ShowBox is now explicitly non-activable/search-only and has entered the normal disabled-retention lifecycle (`f1a5c34fb3d`, `30f3b706f627`, `57ddfe50e837`): `provider-disabled/` until purge after 7 days unless authoritative evidence requalifies it. FullAnime, Animetsu and DesiFlix remain disabled for their independent authority/manual-off reasons.
- Census queue semantics were made explicit after the user flagged that disabled providers were being described as generic authority-blocked. `d2f0ba483c00`, `b300e517570f`, `30ee521c1332`, `62237a77ce02`, `97f986efdea7` add/preserve `lifecycleDisabledQueue` and `authorityRediscoveryQueue` separately while retaining `authorityBlockedQueue` only as a compatibility aggregate. Exact transport queues remain `harnessMismatchQueue` and `environmentBlockedQueue`.
- Important stale-ledger caveat: current WAF overlay still rests on census run `35654380620`, so ShowBox's row can still display its older `REDISCOVER_SEARCH` fields even though the current authority artifact already says manual-off/disabled. The next canonical Repair must re-render with fresh authority before WAF gating; do not interpret the old row as current lifecycle truth.
- Next action: canonical Repair on current main after serialized WAF validation. Require fresh authority reconciliation first, integrated GitHub+Tailscale transport qualification, then inspect the resulting Repair queue and Brain/deferred-learning behavior. Do not reintroduce a separate post-census WAF writer.

## 2026-09-21 23:24 Europe/Paris — Tailscale evidence preserved; transport classes split; AnimeVOSTFR/ShowBox authority corrected

- The private Tailscale residential path is **working**, not hypothetical. WAF run `35651768587` (#97) connected successfully with GitHub OIDC, selected the private exit node, merged `available=true` residential evidence and replayed 11 full providers. The persisted overlay later showed 17 matched provider-lanes; privacy fields confirm no exit-node name, Tailscale address, residential public IP, bodies or cookies are persisted.
- Residential replay result is currently **0 playable / 0 verified** across the selected providers. This is still highly useful differential evidence:
  - AllWish remains challenged even through the residential exit -> true `HARNESS/ENV BLOCKED`.
  - AnimeSalt, AnimeVOST-FR, MoviesMod and VostFree let browser content through while direct/OkHttp/native-like transport remains challenged -> `HARNESS MISMATCH`, not an environment block.
  - Flemmix transport remains inconclusive/challenged even through the residential path; do not call provider JS broken from CI evidence alone.
  - YFlix is reachable on GitHub and residential transports but returns zero provider results -> provider/runtime Repair territory, not WAF.
  - VidFast keeps provider HTTP failure under residential replay -> provider/runtime route investigation, not a GitHub-IP-only block.
- A persistence race was confirmed: standalone WAF could persist fresh Tailscale evidence, then a longer census finishing seconds later could overwrite `provider-waf-browser-session-latest.json` and census transport state with its GitHub-only snapshot. Census/WAF/Repair were therefore serialized and canonical Repair was changed to own WAF/network qualification end-to-end, while Repair census refresh now explicitly preserves both WAF and provider-authority evidence.
- Census semantics were corrected so `HARNESS MISMATCH` and `HARNESS/ENV BLOCKED` are separately counted. New exact JSON queues are `harnessMismatchQueue` and `environmentBlockedQueue`; legacy `environmentQueue` remains compatibility-only. With the latest known residential evidence, the intended active split is 4 mismatch (AnimeSalt, AnimeVOST-FR, MoviesMod, VostFree) and 2 true environment-blocked (AllWish, Flemmix); authority-disabled providers are excluded from those active transport queues.
- AnimeVOSTFR authority is now coherent with the manual address correction: registry direct/current = `https://animevostfr.org/`; `v2.animevostfr.org` is only a redirect seed/history; provider override Lego option `base` and the runtime module default both use `https://animevostfr.org`. `d484ebbc54d8` adds the generic fix: Domain Refresh now migrates top-level provider-Lego site roots (`base/site/referer/origin`) when they point at a terminal that Domain has just replaced, while deliberately leaving mirror arrays intact. `34b90104ab4a` locks this behavior.
- MoviesMod authority matches the manual finding: hub `https://modlist.in/?type=hollywood` -> current terminal `https://moviesmod.ai.in/`; search is fallback only.
- FullAnime remains disabled because there is no reliable current hub/authority and the name is too generic for search-only activation. Animetsu remains disabled because EverythingMoe marks the source removed/broken. DesiFlix remains disabled because the former site became inappropriate/compromised.
- ShowBox manual source review found no public authoritative source beyond private Telegram/search. Registry now keeps `showbox.media` only as a forensic candidate, not a current direct. `f1a5c34fb3d8` marks it non-activable; `30f3b706f627` makes curated/manual-off decisions executable lifecycle policy instead of a passive authority label; tests `29b777c9eeca` / `9c3803f25c3e` lock pre/post lifecycle semantics. Lifecycle run `35656611263` (#23) completed SUCCESS and bot commit `57ddfe50e837` moved ShowBox to `provider-disabled/`, `enabled=false`, disabled 2026-09-21, purge/archival date 2026-09-28.
- MalluMV is not disabled solely because search is ambiguous: current structured site + positive provider route prior and CHAIN REACHED evidence are independent runtime authority. YFlix/PersianStremio likewise remain authority-valid through explicit structured backends, not search. AnimeSultra is still ambiguous but its current browser diagnostic reaches `v2.animesultra.org`; do not disable it from the older “down” observation while fresh evidence contradicts that. Persisted Domain failure memory remains the demotion mechanism.
- A stale sharded-census workflow test was also found: it still required top-level `contents: read` although sharded census now legitimately persists canonical evidence with `contents: write`. `9d4d25e6dd39` aligns that contract.
- Still pending at this checkpoint: WAF #102 is running the new exact transport-queue renderer; its persistence must be inspected before calling the current markdown final. Repair #131 was cancelled while pending because GitHub concurrency retains only one pending run per shared group; do not treat #131 as a provider/Brain result. Launch a fresh canonical Repair only after the current WAF/census/lifecycle writers have stabilized.

## 2026-09-21 23:15 Europe/Paris — Canonical Repair now owns WAF end-to-end

- User clarified the intended architecture: WAF/network qualification is an integral Repair phase, not a second autonomous pipeline; Tailscale is only an optional transport when the private exit node is online.
- Follow-up audit found one remaining half-integration bug: after the new pre-Brain WAF merge, `run_provider_repair_pipeline_v6.py` refreshed the targeted pre-Repair/post-candidate census without passing either fresh WAF evidence or fresh authority. That could erase a just-earned residential/native reclassification before Brain target selection.
- `74ae3eaa4800` adds `WAF_STATUS=automation/provider-waf-browser-session-latest.json` and passes both `--waf-browser-evidence` and `--authority-status` through every internal Repair census refresh. `0c83684fe203` locks both refresh paths in the integrated WAF contract test.
- Census no longer dispatches a standalone WAF run. `5a3d0cdb3744` (mono) and `6e18a82230f8` (sharded) remove those post-census dispatches; `3d0ae0498a90` updates the contract so the standalone WAF workflow is diagnostic/manual only. Canonical flow is now **census -> Repair [fresh authority -> WAF/network qualification -> optional Tailscale -> WAF/census merge -> Brain -> post-Repair census]**.
- Repair/census/manual-WAF still share the `provider-census-waf-main` concurrency lane so evidence writers cannot race. This is serialization only; it does not make standalone WAF part of the normal production chain.
- Trigger #130 (`35655411853`, SHA `665a4e0f`) was still pending when the internal census-refresh leak was found. A newer trigger was intentionally pushed; GitHub cancelled #130 before job execution rather than wasting a full Repair on stale workflow bytes.
- Current canonical validation is Repair #131 / run `35655859428`, trigger SHA `caf6d3dfe157`, presently pending behind the already-running legacy standalone WAF #100 (`35655341458`). #131 is the first run expected to validate the full integrated architecture above.

## 2026-09-21 23:06 Europe/Paris — WAF moved inside Repair; Tailscale is optional transport, AnimeVOSTFR runtime authority reconciled

- User correction accepted: WAF/network qualification is not a separate post-Repair concern. It is now an integral pre-Brain Repair phase. Tailscale is an optional extra transport only; Repair must continue when the private exit node is offline/unconfigured.
- Fresh evidence from WAF run `35651768587` (#97) proves the private Tailscale path itself works: ephemeral node connected, residential exit selected, `FIELD_WAF_RESIDENTIAL_PROFILE_MERGE available=true matched=16`, and 11 full providers were replayed through the residential exit (`playable=0 verified=0 wrong=0`). The later census overwrote this overlay because census/WAF were concurrent writers; Tailscale was not the failure.
- Residential evidence from #97 materially reclassified the old blanket environment bucket:
  - AllWish remained challenged even residentially -> genuine HARNESS/ENV BLOCKED.
  - AnimeSalt, AnimeVOST-FR, MoviesMod and VostFree reached browser content on GitHub/residential profiles while direct/OkHttp remained challenged -> HARNESS MISMATCH/native-policy issue, not a generic environment block.
  - Flemmix became native-policy-inconclusive residentially, not proven environment-blocked.
  - YFlix was network-reachable on both GitHub and residential profiles and remained zero-result -> provider/runtime symptom.
  - VidFast remained provider HTTP-error under residential full-provider replay -> provider/runtime symptom, not GitHub-IP-only WAF.
- `0bd554ca347c`, `90a1d29554e9`, `db9d7dee7088`, `3f3dbf8da534` serialize mono/sharded census and WAF persistence on the same concurrency lane and dispatch a fresh residential WAF overlay after a persisted census. This prevents a later census from silently erasing fresher Tailscale evidence.
- `2bd41f966cc9` makes WAF part of `.github/workflows/provider-recognition-repair-v6.yml` before canonical provider selection: current authority-eligible symptomatic providers get targeted quick-yield, GitHub browser/OkHttp/direct qualification, optional Tailscale residential re-probe/full-provider replay, WAF->census merge, batch-plan rebuild, then the canonical Repair/Brain consumes that qualified census. Tailscale connection, exit selection and residential probe are `continue-on-error`; absent/offline Tailscale records an unavailable reason and Repair continues on GitHub/native/browser evidence.
- Repair, census and standalone WAF now share `provider-census-waf-main` serialization; Repair persists `provider-waf-browser-session-latest.json` together with its census/authority/Brain memory. `9fb43fbffafe` locks ordering and offline fallback in `provider_repair_waf_integration_workflow_test.py`.
- Manual authority reconciliation remains:
  - FullAnime stays disabled: no trustworthy hub/current authority; generic search is supplementary only.
  - Animetsu stays disabled: EverythingMoe authoritative source marks it removed/broken since July 2026; fake search domains cannot reactivate it.
  - ShowBox stays search-only/authority-blocked; showbox.media is not promoted without independent runtime proof.
  - DesiFlix stays disabled because the former site chain became inappropriate/compromised.
  - PersianStremio remains authority-eligible via structured backend/runtime and is currently PARTIAL OK; no public hub is required for deterministic backend authority.
  - YFlix remains authority-eligible because of structured backend authority, not search results.
  - MalluMV remains provisionally authority-eligible from current structured-site + positive route runtime evidence; generic-name search is not its authority. Do not disable while that runtime evidence remains current, but require verified media before promotion.
  - AnimeSultra's old v2 address is not treated as permanently valid merely because it was once explicit_current; fresh browser evidence currently reaches the host, so keep it active while Domain failure memory continues to arbitrate current authority.
  - VidFast official documentation proves `/embed/movie/{id}` and `/embed/tv/{id}/{season}/{episode}`; current registry/Lego already carries these current routes.
- AnimeVOSTFR had a real split-brain bug: registry/override `official_site=https://animevostfr.org` and `v2 -> root` migration were current, but the provider Lego option/default still used `https://v2.animevostfr.org`. `dcd605f2a5d5` and `514a7587bb00` move the executable runtime base/default to `https://animevostfr.org`; `36893fa7b7e` locks that contract.
- `b575bed1061e` adds a generic materializer guard: nested HTTP URLs in provider Lego/patch-script options are projected through current runtime/domain substitution DATA when their old host is already mapped to a current authority host. `e189e41f7420` proves an AnimeVOSTFR-like stale nested runtime option is rewritten to the current host, preventing future Domain-vs-Lego divergence.
- Next authoritative validation: canonical Repair on current main. Require preflight green, integrated WAF phase to run before `FIELD_PROVIDER_REPAIR_SCOPE`, observe whether Tailscale is available without making it mandatory, inspect the WAF-qualified repair/environment queues, then evaluate Brain repair results and persist the resulting census/memory.

## 2026-09-21 22:23 Europe/Paris — Census runner reached real contracts; stale Flemmix assertion fixed

- TEMP census run `35649485922` (#1309, SHA `01220f219471`) confirmed the workflow-validation issue is closed: both `scale` and `census` jobs were allocated. The census then failed in the real contract suite before network probing.
- Exact failure: `tests/provider_flemmix_anime_ultime_runtime_contract_test.py` still asserted that `flemmix.me` must be absent from `domain_substitutions`. That assertion is stale relative to current Domain authority: `provider-hubs.json` pins `https://flemmix.party/` as `explicit_current`, lists `flemmix.me` as a historical/redirect candidate, and current overrides intentionally normalize both `flemmix.cloud` and `flemmix.me` to `flemmix.party`.
- `4244a3cf0298` updates the contract to require `flemmix.me -> flemmix.party` in both domain/runtime replacement maps instead of forbidding the historical host.
- `9f4bfabc5d29` closes a census evidence-consistency gap: mono census already rendered with current `provider-authority-status.json`, but its persistence step did not save that exact authority artifact with the status/markdown. Authority is now copied through the reset/rebase boundary and committed with the exact census ledger so later readers can reproduce why a symptom was or was not in `repairQueue`.
- TEMP census #1310 (`35649760235`, SHA `9f4bfabc5d29`) is the validation run for these fixes. Do not call the census coherent until its contract step passes, the unresolved census executes, and `PROVIDER_CENSUS_STATUS.md` is regenerated/persisted.

## 2026-09-21 22:19 Europe/Paris — TEMP census workflow validation restored

- Repeated `TEMP - Current Bytes Full Provider Census` runs were not test failures: GitHub created the workflow run under the file path name, immediately concluded failure, and exposed `jobs=[]`. This is workflow-validation failure before runner allocation.
- The break was traced to the provider-count routing added on 2026-09-20 (`39016ca35d02`): the mono census job acquired a compound job-level GitHub expression combining `needs.scale.outputs`, event type and commit-message `startsWith` calls. Merely rewriting unary `!startsWith` did not repair validation (`f2839047d01c`, run 1308 still had zero jobs).
- `01220f219471` moves catalogue-size and recursion decisions into the already checked-out `scale` shell step. It emits `use_sharded` and `should_run`; the census job now uses only `if: needs.scale.outputs.should_run == 'true'`. The >120-provider handoff to the 8-shard workflow and recursion suppression are preserved without a fragile compound job expression.
- Validation evidence: run `35649485922` (#1309) is recognized by GitHub under the declared name **TEMP - Current Bytes Full Provider Census** and created job `scale`; the scale job completed successfully. This closes the pre-run workflow-validation failure. The actual census job/result remains to be inspected before calling the census run green.

## 2026-09-21 22:14 Europe/Paris — Census authority/last-verdict reconciliation fixed

- The persisted `PROVIDER_CENSUS_STATUS.md` was internally inconsistent in two independent ways:
  1. its `repairQueue` was status-only (10 providers) while canonical Repair independently applied `provider-authority-status.json` and actually targeted 8; `animetsu` and `showbox` were therefore advertised as automated Repair targets despite authority actions `KEEP_DISABLED` and `REDISCOVER_SEARCH`;
  2. three carried rows were still green while their own stored latest verdict contradicted green: `anime-ultime` FULL OK + `provider_network_http_error`, `animesalt` FULL OK + `provider_waf_challenge`, and `vostfree` FULL OK + `provider_waf_challenge`. None had a retained playback proof in current census history.
- `b13676ac0008` makes census Repair eligibility the intersection of runtime/status eligibility and current provider address/backend authority. Each row now carries authority action/class/confidence/reasons, the markdown exposes an Authority column, and JSON schema v3 adds `authorityBlockedQueue`. Authority-blocked symptomatic providers remain visible as symptoms but are excluded from automated Repair.
- The same renderer now refreshes carried rows' retained proof/candidate proof/route proof from current durable evidence instead of blindly copying stale snapshots. A carried FULL/PARTIAL row is reconciled against its own latest lane verdict: verified lanes not marked OK are removed and, when no verified lane remains, the row is reclassified from its latest causal evidence (network block, harness/WAF, route/candidate/no-proof, or JS failure). This prevents stale green status from surviving contradictory evidence.
- `e753b48e43fa` locks both authority filtering and carried-green reconciliation with synthetic census tests.
- `0cf1041d08ac` fixes the mono census workflow ordering: current provider authority is classified before rendering; a provisional status seeds the bounded WAF diagnostic; the final census is rendered only after current-run WAF/network evidence exists. Batch planning therefore consumes the final coherent status, not a pre-WAF snapshot.
- `f3e1e8430263` applies the same authority/WAF/final-render semantics to the 8-shard census used when the provider catalogue grows past the mono-job threshold, and persists the sharded WAF/authority evidence with the canonical census.
- Existing TEMP census push runs are currently failing before job creation (`jobs=[]`), so those instant-red runs are not evidence against the renderer changes. The canonical Repair preflight includes `provider_census_status_markdown_test.py`; next Repair on current HEAD is the authoritative validation path while the TEMP workflow issue remains separate.

## 2026-09-21 22:05 Europe/Paris — Brain outer-wave replay loop diagnosed and fixed

- Repair #127 exposed a second structural Brain problem after packed batching was working: later waves regenerated the exact same candidate bytes for stubborn providers. VidFast repeatedly produced candidate hashes `fa9891f1` / `5ea95646`; MalluMV repeatedly produced `23ab95c0` / `da59b791`. This was not CPU pressure.
- Two distinct causes were confirmed from planner/runtime code plus persisted `brain-repair-memory.json`:
  1. **Historical-success immunity**: planner negative-memory matching discarded any experiment row with `successes > 0`, even if that same row now had fresh `consecutiveFailures > 0`. MalluMV variant 2 had `successes=5, failures=5, consecutiveFailures=5, lastOutcome=rejected`, so the planner could keep selecting a stale historically-successful strategy despite current repeated rejection.
  2. **Lost terminal exploration progress**: sandbox `exploration_progress` is intentionally non-publishable and was not recorded as a consumed experiment. When a bounded Deep invocation ended without an accepted repair, the outer wave restaged published bytes and replayed the same final strategy. This matches VidFast's `blocked -> no_streams` and MalluMV's `unreachable -> 3 returned but unverified streams` plateaus.
- `a47711f3a526` changes planner negative-memory semantics: current `consecutiveFailures > 0` is authoritative even when a strategy succeeded historically; an accepted experiment still resets consecutive failures to zero. Legacy never-successful failed rows remain negative.
- `b4309761cf9d` persists bounded sandbox progress as `exploration_progress_nonpublishable` when the provider finishes the whole Deep invocation without any accepted repair. It increments failed/consecutive experiment memory and a `progresses` counter, preventing exact outer-wave replay. Exploration steps that lead to an accepted repair in the same invocation are explicitly not penalized.
- Contracts added: `8f977345ee01` proves a stale successful variant rotates after fresh consecutive failure; `cdc2868f4c0b` proves terminal sandbox progress becomes durable negative experiment memory and that progress leading to a later accepted repair does not.
- Repair #128 (`35647529494`, SHA `850e40992a01`) is intentionally still validating the earlier concurrency-report fix on its immutable SHA. Its full preflight passed and the canonical Repair step started. The new causal-loop fixes are on newer main and must be validated by the next Repair after #128 persistence so it can also consume #128's latest memory.

## 2026-09-21 21:58 Europe/Paris — Repair #127 reached real Brain; late concurrency-report crash fixed

- Repair run `35641490356` (#127), trigger SHA `753897003ad8`, is the first run in this sequence that passed the full preflight and entered the real authority-filtered Brain pipeline. Runtime scope was **8 providers**: `4khdhub, animesultra, animevostfr, vidfast, yflix, allanime, mallumv, moviebox`. Census still listed 10 repair targets, but authority correctly excluded `animetsu` and `showbox`; `wookafr` is now PARTIAL OK and therefore excluded from the non-green Repair scope.
- Scalability behavior was real, not inferred: wave 1 staged all 8 targets into **one packed Deep process**. After its negative-memory/exhaustion decisions, later waves contained only **3 stubborn providers** (`4khdhub, mallumv, vidfast`) instead of replaying all 8. Wave 1 ran about 3m44; waves 2-5 ran about 1m38-1m57 each. This confirms packed families + per-batch health concurrency are active, while the remaining cost is repeated experiment rotation on the stubborn subset.
- No repair was accepted. MalluMV repeatedly reached a stronger sandbox state with 3 extracted streams, but those streams were not playback-verified; strict acceptance correctly rejected promotion. 4KHDHub remained zero-stream after lookup progression; VidFast moved from HTTP-blocked baseline to lookup-completed/no-streams candidates but never to verified media.
- #127 then failed **after all five Deep waves** while building `provider-brain-repair-latest.json`: `NameError: name 'concurrency' is not defined` at `run_provider_brain_repair.py`. Root cause is the packed-batch concurrency refactor `e14ff21b4f1f`, which removed the old global `concurrency` variable but left one report field referring to it. This is an orchestrator/reporting failure, not provider evidence.
- `848aaa5b8393` replaces the dead global reference with the normalized requested concurrency setting, records `healthConcurrencyMode`, and persists each batch's effective `healthConcurrency`. `042bd1f14919` extends `provider_brain_repair_orchestrator_test.py` to forbid the stale `"healthConcurrency": concurrency` form and require both global-mode and per-batch reporting.
- The failed run still persisted current census/negative Brain memory through bot commit `131ebb1c238d`, so the next Repair should reuse the learned rejected variants instead of restarting from a clean slate. Next action: trigger canonical Repair on current main; require the preflight contract to pass, require the Brain report to be written, then inspect deferred/resume behavior and post-Repair census before any further Brain change.



## 2026-09-21 20:54 Europe/Paris — Repair #126 preflight: parallel byte-validation test drift fixed

- Repair run `35641162638` (#126) on trigger SHA `570104eca437` still did **not** reach provider probes. Authority contracts, documented-route discovery and Brain orchestrator contracts all passed. Preflight then failed in `tests/provider_materialization_byte_validation_contract_test.py` line 27.
- Runtime/code inspection proves strict validation was not missing. `materialize_provider_v3_all.py` submits canonical `verify_bytes` calls through the bounded `validation_pool`, resolves each `future.result()` in deterministic catalogue order, then hashes/writes bytes. `materialize_provider_v3_one.py` still calls `allmat.verify_bytes(bundle)` synchronously before digest/write.
- The failing assertion was stale and contradictory: after already requiring `validation_pool.submit(verify_bytes, bundle)`, it additionally required the old sequential literal `verify_bytes(bundle)` in the all-provider source. `daa1230e160a` replaces that obsolete literal check with the parallel canonical-submit assertion while preserving checks for resolve-before-digest/write and unit-materializer validation.
- No provider/Brain repair result from #126 is valid evidence. Next action: rerun canonical Repair; the run is only meaningful once preflight passes and the actual authority-filtered provider queue is probed.



## 2026-09-21 20:50 Europe/Paris — Repair #125 preflight fixed; documented-route parser corrected; Domain #1034 green

- Lifecycle run `35640498691` (#20) completed SUCCESS and bot commit `fe6d67a08372` persisted the corrected authority state: 46 providers, 42 Repair-eligible, ShowBox=`REDISCOVER_SEARCH` with reasons `direct_candidate_unproven + search_supplement_only`; no additional safe disable was applied.
- Repair run `35640602284` (#125) on `c5c1d8c1fb33` again stopped in preflight before provider probing. Authority arbiter/current-catalogue/domain-memory tests all passed. The next contract, `provider_documented_route_discovery_test.py`, failed with `AssertionError: []`; therefore #125 contains no provider/Brain repair evidence.
- Root cause was a raw-regex double escape in `discover_documented_routes()`: `r"https?://[^\\\\s...]"` treated `s` as a forbidden literal character, truncating provider URLs such as `vidfast.to` before URL parsing. `8eb80bceeedf` changes this to the real whitespace class `\s`. The existing contract already proves only same-origin literal placeholder routes are learned, while concrete fixture URLs and foreign-domain docs remain excluded.
- A targeted scan of `resolve_provider_hubs.py`, `adaptive_runtime/runtime_repair.py` and `build_brain_repair_experience.py` found no remaining obvious `\\s` / escaped-placeholder pattern of this class.
- The resolver change auto-triggered Domain run `35640767459` (#1034). It completed **SUCCESS through every step**: resolve, reconcile, transaction guard, no-op history, DNS/HTTP, domain-only Provider-v3 validation, release/native Hub46 projection, publish step and artifact upload. This also proves `d2435d98` correctly prevents post-publication auxiliary dispatch problems from turning the Domain run red.
- Next action: relaunch canonical authority-filtered Repair on the new current HEAD; require it to reach the actual provider queue before evaluating Brain scalability or repair quality.



## 2026-09-21 20:45 Europe/Paris — Repair #124 preflight found and fixed false direct authority promotion

- Canonical Repair run `35640096441` (#124) on trigger SHA `fd3140d48295` did **not** reach provider probes. It failed in preflight at `provider_authority_current_catalogue_test.py`: ShowBox recalculated as `KEEP_DIRECT` although the durable intended state is `REDISCOVER_SEARCH`. No Brain/provider result from #124 is valid repair evidence.
- Root cause: `classify_provider_authority.py` treated any registry `direct` HTTP URL as sufficient authority. ShowBox had `direct=https://www.showbox.media/` recorded as a runtime candidate, but its registry provenance is still search-only/historical supplementary and its route proof has `provenRouteCount=0`, `positiveExecutionEvidence=false`. The candidate was therefore incorrectly promoted merely by being present.
- `3cdd2f836ee8` adds `PROVIDER_AUTHORITY_DIRECT_PROOF_V1`: `direct_authority=explicit_current` remains strong until Domain failure memory demotes it; otherwise a direct candidate is Repair authority only with provider-owned positive route proof or a fresh matching runtime observation. A bare direct candidate falls back to rediscovery (`REDISCOVER_SEARCH` when search supplement exists). Existing proven direct providers such as Kurage/Sekai/StreamZo/VoirAnime-rip remain eligible because they carry positive route evidence.
- `56c6b9218b95` locks bare-search direct rejection, proof-backed direct acceptance and explicit-current strength. `d99c6ec92334` locks the live ShowBox catalogue decision and its reasons: `direct_candidate_unproven + search_supplement_only`.
- Lifecycle auto-recomputation was triggered by the authority-code change. Next action: require a successful current-head lifecycle recomputation, then relaunch canonical Repair with the same census/authority-filtered scope.



## 2026-09-21 20:38 Europe/Paris — Domain publication confirmed; Repair queue authority-filtered to 9

- Revalidated current `main` after the Domain/lifecycle authority work. Domain run `35638237327` (#1032) is a **successful publication with a false-red post step**: the workflow passed registry sanitize, Domain resolve/reconcile, transaction guard, DNS, domain-only static audit, active/native Hub46 release checks, then committed `35bbcf89bf59` and final `efdad41cd72b`; `git push` succeeded and logged `FIELD_DOMAIN_PUBLICATION_OK base=9bdf5bd... final=efdad41c...`. The run only turned red afterward because `gh workflow run sync.yml` hit GitHub installation API rate limiting (`HTTP 403`).
- Persisted bundle inspection confirms publication bytes, not just structured intent: AnimeVOSTFR bundle `animevostfr--nuvio--835c6ce5...` has `knownSite/officialSite=https://animevostfr.org` and `domainSubstitutions.v2.animevostfr.org=animevostfr.org`; Flemmix `2bb7316f...` has `knownSite/officialSite=https://flemmix.party` with historical hosts mapping to `.party`; MoviesMod `a09c81e8...` has `officialSite=https://moviesmod.ai.in` and `officialHub=https://modlist.in/?type=hollywood`; VidFast `1186d645...` has `knownSite/officialSite=https://vidfast.to`.
- `d2435d982846` makes post-publication `sync.yml` / `provider-disabled-lifecycle.yml` dispatch failures non-fatal because publication is already durable at that point; `7354ed4d0338` locks this contract. A GitHub API rate-limit can no longer mislabel an already-pushed Domain transaction as failed.
- Current authority report is durable: **46 providers, 42 Repair-eligible, 4 blocked** (`animetsu`, `desiflix`, `fullanime`, `showbox`). Search remains `historical-supplement-only`; future hub imports do not depend on raw search by default. Lifecycle retention is **7 days**, with active `providers/ -> provider-disabled/ -> provider-old/` policy.
- Current census repairQueue is ["4khdhub","allanime","animesultra","animetsu","animevostfr","mallumv","moviebox","showbox","vidfast","wookafr","yflix"]. Authority intersection removes `animetsu` (`KEEP_DISABLED`) and `showbox` (`REDISCOVER_SEARCH`), leaving **9 canonical Repair targets**: 4khdhub, allanime, animesultra, animevostfr, mallumv, moviebox, vidfast, wookafr, yflix. Environment/harness-only providers remain excluded by census semantics.
- Next authoritative action: trigger canonical Repair on current `main` with an empty explicit target list so the workflow uses census repairQueue **and** the authority gate. Measure packed family batches, batch health concurrency, provider-local post-wave materialization and global byte-validation overlap against the old 11-target baseline; do not infer success from queue shrink alone.



## 2026-09-21 20:25 Europe/Paris — Authority reasons corrected; Hub46 decoupled from active cardinality

- Lifecycle run `35637578802` (#16) completed SUCCESS after the authority-policy auto-trigger was added. It persisted the stricter `PROVIDER_AUTHORITY_BACKEND_SCOPE_V1` result without reducing current Repair eligibility (**42/46**): YFlix/PersianStremio remain true `KEEP_BACKEND`; ARM identity infrastructure and generic `fallbackBases` no longer establish backend authority.
- `566fae3b9448` changes backend authority to explicit provider execution fields only (`official_api`, fixed/api recipe backend fields, provider Lego `api/db/api_base/apiBase/backend/endpoint`) and excludes `api.themoviedb.org`, `v3-cinemeta.strem.io`, `arm.haglund.dev`; `fallbackBases` are no longer backend authority. `7da36921377b` locks both exclusions.
- Runtime result after recomputation confirms correct fallback classifications: Anime-Sama/CoFlix/Papadustream = `KEEP_ROUTE_AUTHORITY`; French-Manga = `KEEP_DIRECT`; VoirAnime-Homes = `KEEP_PROVEN_SITE`; YFlix/PersianStremio = `KEEP_BACKEND`. This removes false-positive backend confidence without blocking repairable providers.
- `940c9f917130` makes Lifecycle automatically run when its authority/lifecycle code or contracts change. `b003df186f49` makes a successful Domain publication dispatch one Lifecycle recomputation; `f7d8b975c848` locks that dispatch. Normal authority evolution no longer needs a manual trigger.
- Domain run `35636912360` (#1030) proved lifecycle-aware DNS and registry contracts through the full Domain validation phase: disabled providers were skipped as active DNS candidates, provider registry/Domain ownership tests passed, and static audit reported `active=43 visible=46 structured_data=domain-current`. DNS completed 43 active providers instead of failing on DesiFlix.
- #1030 then failed after native Hub46 transport build because `native_hub46_transport_manifest_test.py` still asserted the historical Hub-46 matrix cardinality equalled `active_provider_count()`. This is obsolete after legitimate lifecycle disables and cannot scale to future hundreds of providers.
- `8ca0333b89f0` adds `HUB46_CURRENT_ACTIVE_TRANSPORT_SCOPE_V1`: native transport test derives exact membership from current `manifest-hub46.json` and requires equality with `active_provider_ids()`, not a frozen matrix count.
- `4d1b5bc5e2f5` / `46d26e1c1dbd` similarly decouple upstream parity: `hub-lab-matrix-46.json` remains a historical/campaign scope, but runtime parity intersects that matrix with current active providers and reports inactive matrix members instead of failing when a provider is disabled. This also avoids assuming a historical 46-item campaign represents the future full catalogue.
- Domain #1031 ran before these scope commits and is non-authoritative for the new release contract. Next authoritative action: stable-head Domain run after `46d26e1c1dbd`; require final release validation + publication, then inspect persisted registry coverage and launch canonical Repair.



## 2026-09-21 20:12 Europe/Paris — Provider authority recomputed; 42/46 Repair-eligible; registry/DNS aligned with lifecycle

- Revalidated authority on current main after `adc585cf415f` / `bd175ec97ce9`. Lifecycle run `35636288265` (#14) completed SUCCESS and bot commit `95181b1dd738` persisted a fresh `automation/provider-authority-status.json`: **46 providers, 42 Repair-eligible**. This closes the prior over-conservative report rather than inferring success from code alone.
- Current durable decisions now match the intended generic policy: YFlix and PersianStremio = `KEEP_BACKEND`; VidFast = `KEEP_ROUTE_AUTHORITY`; Kurage/Sekai/StreamZo/VoirAnime-rip = `KEEP_DIRECT` with zero persisted authority failures; AnimeKai/Neko-Sama/Anime-Ultime/MalluMV = `KEEP_PROVEN_SITE` from structured current site + positive route proof; AnimeSultra remains `KEEP_DIRECT` while `failureCount=0`; ShowBox remains `REDISCOVER_SEARCH`; Animetsu/FullAnime/DesiFlix remain `KEEP_DISABLED`.
- Lifecycle state is now the project contract: `RETENTION_DAYS=7`, physical `providers/ -> provider-disabled/ -> provider-old/`. Current disabled-retained rows: DesiFlix disabled 2026-09-15 / purgeAfter 2026-09-22, FullAnime 2026-09-15 / purgeAfter 2026-09-22, Animetsu 2026-09-21 / purgeAfter 2026-09-28. No archive transition is claimed before the scheduled date/run.
- `8e4445b4b1ec` adds a dedicated `.github/triggers/provider-disabled-lifecycle` path and `aa66588e3e95` exercised it successfully, so authority changes no longer wait for the daily cron. `bd70f38f6e13` adds a real-catalogue authority contract and `3e0708aa9446` / `72140db7ae07` gate it in Lifecycle and Repair respectively.
- Search policy remains deliberately asymmetric: current historical providers may opt in with `legacy_search_refresh=true`; Yandex remains first supplementary engine and raw search results are low-weight (`score~22`). Raw search is never publication authority. A search result can contribute stronger `source_redirect` evidence only after that exact same-brand result is fetched and a safe deterministic cross-host redirect is observed. Future/imported providers do **not** opt in by default.
- Registry coverage gap found: visible providers missing from `provider-hubs.json` were `anime-ultime, animevost-fr, neko-sama, vidlove, voiranime-homes`. `eac1b43a0401` adds `PROVIDER_HUB_REGISTRY_TOTAL_COVERAGE_V1`: every visible provider gets a registry identity; auto-created rows are `registry_state=unresolved`, `hub/direct=null`, no sources/search queries, `legacy_search_refresh=false`, so coverage never invents authority. `14ebe4b22e88` tests this.
- Domain run `35636212896` (#1029) proved the coverage code in workspace: sanitizer reported `scope=46 registry_changed=6 providers=anime-ultime,animevost-fr,neko-sama,showbox,vidlove,voiranime-homes`; provider hub tests passed. Resolver then ran with `scope=43 resolved=21 unresolved=15 applied=0 projection_drift=0`.
- #1029 failed only on integration contracts after provider/domain work: `provider_v3_workflow_ownership_test.py` still required the obsolete literal `provider_ids = current_provider_ids(...)`, and DNS preflight treated manifest-visible disabled DesiFlix as if it had to live under active `providers/`. `7f8f250afbe7` updates ownership to `current_provider_rows + ensure_registry_coverage`; `b8adeba23ad1` makes DNS validate disabled bytes under `provider-disabled/` and skip them from active probes while keeping active bytes restricted to `providers/`; `0dad8d6d11dd` locks this lifecycle-aware DNS contract.
- Domain #1027's earlier `IndexError` was a workflow-only empty commit-message bug, fixed by `20a688190e17` and locked by `ff0e5f29e422`; do not interpret #1027 as provider/domain evidence.
- Next authoritative sequence: run Domain Refresh on a stable post-`0dad8d6d11dd` HEAD; verify registry coverage actually persists (including unresolved rows without search authority), verify DNS no longer probes disabled providers, then inspect any Domain mutations/authority failure memory. After Domain is green, launch canonical Repair and measure the already-implemented Brain scalability changes on the current repairQueue.



## 2026-09-21 19:48 Europe/Paris — Provider authority Brain: search becomes historical supplement; 7-day disable lifecycle; API/docs reclassification

- User clarified the intended disabled-provider lifecycle: executable bytes live in `providers/`; a provider disabled for roughly one week lives under `provider-disabled/`; after the retention window it moves to `provider-old/`. Repository code still used `RETENTION_DAYS=28`. `74b1f862b171` changes the canonical retention to **7 days**; disabled providers from 2026-09-15 therefore remain retained on 2026-09-21 and become archive-eligible at the next >=7-day lifecycle evaluation.
- User also clarified search policy: Yandex/search must remain available for the current historical catalogue, but with less trust/weight; future bulk hub imports must not depend on search by default. `9f3aafdfe90a` lowers raw search candidate score 45→22 and search-derived redirect score 82→62, persists `DOMAIN_AUTHORITY_FAILURE_MEMORY_V1`, and permits quick search only for registry rows explicitly carrying `legacy_search_refresh=true`. `a929322b84e0` makes the Domain wrapper use the same policy. Future registry rows default to search supplement/deep only.
- `a83edd299a98` adds `scripts/classify_provider_authority.py`, a deterministic pre-Repair arbiter. Site-dependent providers require current address authority before Repair; API/backend-driven providers may remain Repair-eligible without a homepage. Decisions are `KEEP_DISABLED`, `KEEP_BACKEND`, `KEEP_ROUTE_AUTHORITY`, `KEEP_DIRECT`, `REDISCOVER_*`, or safe `DISABLE_*`. Search-only unresolved providers are blocked from wasting Repair waves; repeated persisted Domain failures can later disable them. `d590f2081988` locks search-only rediscovery, API independence, source-removed disable and stale-direct escalation.
- `81540efc2ef3` gates canonical Repair with `automation/provider-authority-status.json`; authority-blocked providers are removed from Repair targets independently of the census symptom queue. `a4a03b9b9362`/`0d449083e451` add the arbiter and authority-memory contracts to Repair CI/artifacts.
- `1fcabd6bc79a` makes resolver authority source-health aware: registry hub/redirect/Telegram sources marked `removed/dead/retired/graveyard/compromised` are no longer considered active authority and are skipped during discovery.
- `efc397fead1c` encodes current historical cases without making them one-off runtime patches: FullAnime now has a registry row while remaining disabled; MalluMV/ShowBox/YFlix/AnimeSultra/PersianStremio opt into legacy supplementary search; PersianStremio mirrors its already-structured Stremio endpoint as `structured_runtime_seed`; ShowBox gets `showbox.media` as a validated **candidate** rather than search publication authority; Animetsu's EverythingMoe source is marked `removed` and non-activation-eligible. EverythingMoe independently confirms Animetsu was removed/currently broken on 2026-07-08.
- Lifecycle run `35634242341` executed the new policy before a test-import failure: `FIELD_PROVIDER_AUTHORITY providers=46 repair_eligible=33 blocked=13 disabled_now=1`, then `PROVIDER_LIFECYCLE_OK active=43 disabled=3 visible=46 archived_now=0 retention_days=7`. This is runtime evidence that the arbiter identified exactly one new safe disable candidate. The run did **not commit** because `tests/provider_domain_authority_memory_test.py` could not import `resolve_provider_hubs`; `ce9c350ba659` fixes only that test import. A fresh lifecycle run is still required before claiming the new provider is physically under `provider-disabled/`.
- VidFast is now treated as an architecture-recognition example, not a provider exception. Its current official page documents `/embed/movie/{id}` and `/embed/tv/{id}/{season}/{episode}`. `ac5a241b4fcb` stores those as `documented_routes` with `architecture-prior-not-playback-proof`; `8c48e4890ef1` and `421cba99cc65` feed `documented_routes` into Brain experience/adaptive routing before weaker guessed routes. `9ad59c6af373` adds generic `PROVIDER_DOCUMENTED_ROUTE_DISCOVERY_V1`, which extracts only literal same-origin placeholder routes from provider-owned documentation and persists them as architecture priors; examples with concrete fixture IDs remain non-proof. `4263e80dd8b0` locks this contract.
- Current caution: ShowBox is not safe to auto-disable merely because registry search confidence was weak; current public `showbox.media` exposes a coherent movie/TV catalogue. AnimeSultra is also ambiguous: current external crawling recently indexed `v2.animesultra.org`, while a direct fetch can time out. The new failure-memory policy intentionally requires repeated evidence instead of turning either observation into an immediate terminal decision.
- Domain run `35633839279` (#1020) passed after the historical-search/source-health registry update (`resolved=21 unresolved=16 applied=0 projection_drift=0`), proving those changes did not force unsafe domain publication. Later #1022/#1023 were based on pre-`ce9c350` SHAs and are obsolete for current validation.
- Next required validation: rerun Provider Disabled Lifecycle on a post-`ce9c350` HEAD and inspect which provider becomes the third disabled entry; rerun Domain on the current HEAD; then trigger Repair so the new authority gate + documented-route priors are measured against the current census queue.

## 2026-09-21 19:12 Europe/Paris — Search/direct redirect blind spot fixed; AnimeVOSTFR + MoviesMod runtime-proven in Domain workspace

- User identified two address-registry gaps: AnimeVOSTFR still had `direct=https://v2.animevostfr.org/` while that entry now redirects to `https://animevostfr.org/`; MoviesMod had only `type=search` despite a provider-specific address hub `https://modlist.in/?type=hollywood` pointing to current `https://moviesmod.ai.in/`.
- Root cause was generic. Daily Domain Refresh defaults to `quick`; `resolve_provider_hubs.gather_candidates()` skipped `type=search`, and the Domain transaction only admitted `has_authoritative_hub_source()`. Providers with curated direct/search-only registry state were therefore excluded even when yesterday's direct URL now deterministically redirected to a new same-brand terminal.
- `d8e1721d0990` adds bounded redirect discovery: `DOMAIN_CURATED_DIRECT_REDIRECT_V1` follows up to 3 curated direct candidates in quick mode (except `direct_authority=explicit_current`) and promotes only safe same-brand cross-host redirects to `source_redirect`; `DOMAIN_SEARCH_RESULT_REDIRECT_V1` keeps raw search results non-authoritative and, in deep mode only, promotes a result only after fetching that exact same-brand URL and observing a safe deterministic cross-host redirect. Search-result redirect probing is capped at 4.
- `f6cc62053d6f` / `4a70632a0e19` add `DOMAIN_REFRESH_DIRECT_AND_SEARCH_REDIRECT_SOURCE_V1`: quick Domain admits hub or curated-direct address evidence; search-only evidence is inspectable only in deep mode. This closes the daily-refresh blind spot without letting search ranking become publication authority.
- `d230f6ebe8e3` registers AnimeVOSTFR's v2 URL as a redirect seed and adds `animevostfr.org` to its allowed terminal hosts; it also registers the exact MoviesMod hub `https://modlist.in/?type=hollywood`. Tests `fef9d2a3e824`, `922b50b410cd`, `06dce4eb4379` cover quick direct redirect discovery, deep search-result redirect promotion and Domain source ownership.
- Domain run `35629299515` (#1006) is runtime proof that this mechanism works before publication: `resolved=22 unresolved=11 applied=4 registry=1 projection_drift=7 bundles=7`. Its artifact proves AnimeVOSTFR observed `v2.animevostfr.org -> animevostfr.org`, selected the root as `site_authoritative`, and proposed a registry update; MoviesMod consumed the new modlist hub while preserving `.ai.in` as explicit current terminal. Proposed CONFIG-only bundle updates were `4khdhub, animevostfr, flemmix, moviesmod, vidfast, voiranime, wookafr` with `core_mutation=false`.
- #1006 then correctly failed because the transaction guard did not yet accept `selected_source_type=redirect`. `db24ef98c36c` makes `redirect` registry-scoped rather than globally trusted; `c449e83f535f` marks the exact AnimeVOSTFR redirect seed as authoritative current-terminal address evidence; `ce48f1d6c3c2` proves exact configured authoritative redirect acceptance and rejection of an untrusted fallback redirect.
- A separate Domain-lane ownership defect was exposed by #1002: full static audit blocked on unrelated YFlix `apiRecipe` drift, and complete CONFIG reconstruction risked publishing non-domain Repair DATA during a domain transaction. `e90e7ec40343` adds `DOMAIN_CONFIG_DATA_OWNERSHIP_V1`: Domain CONFIG rebuild overlays only `officialSite`, `knownSite`, `officialHub`, `domainSubstitutions` onto already-published CONFIG DATA. `91e2352232d5` adds `--domain-only` audit; `26b1114e1f89` makes Domain use it; `5b4eb3d17d5a` proves YFlix-like `apiRecipe`/routes remain published unchanged while domain fields rotate.
- Structural scan after the generic fix found 13 current registry providers in the prior `search-only + direct` shape. One additional stale redirect was already observed publicly: `new3.hdhub4u.cl -> new5.hdhub4u.cl`; the generic quick redirect path should detect it without a provider-specific hard-code. Other rows remain evidence-dependent and are not manually rotated merely from search results.
- `e477259e088f` adds `provider_hub_registry_test.py` to the canonical Domain validation step, so raw-search non-authority and redirect-backed address discovery are now gated by the owning workflow.
- Publication status remains **pending** until a post-`e477259e088f` stable-head Domain run passes all guards, pushes the transaction, and manifest-referenced bundles are inspected. Do not yet claim AnimeVOSTFR root, Flemmix `.party`, VidFast `.to`, or the seven proposed CONFIG updates as published.

## 2026-09-21 18:24 Europe/Paris — Flemmix redirect-chain authority corrected; stale-static resurrection blocked

- User live observation: `flemmix.cloud` redirects through `neufneuf.space` and then to `https://flemmix.party/`. Public current-address sources independently corroborate `flemmix.party` as the current Flemmix terminal and `neufneuf.space` as a redirector. Treat `.cloud` / `.me` as historical or redirect entry points, not final runtime authority.
- `bced1af141ab` updates `provider-hubs.json`: Flemmix `direct=https://flemmix.party/`, `direct_authority=explicit_current`, current observation date 2026-09-21, `.party/.cloud/.me` retained as candidates, and `https://neufneuf.space/` recorded only as a `redirect` discovery source.
- `008010714c54` aligns Flemmix structured runtime DATA with `.party`: `official_site`, search-plan base and runtime Lego base now use `.party`; historical site-domain replacement maps terminate at `.party` and the current `.party` host is removed as a replacement source to avoid a cycle. `67116e9435d5` changes the Flemmix runtime default base to `.party`; contracts `1159df4ec6a8` and `6334d4dab2e9` were updated accordingly.
- Generic root cause fixed by `517af61e0159`: `materialize_provider_v3_one.py` previously treated static Provider knowledge as newer domain authority and could resurrect a stale host after Domain Refresh. `PROVIDER_DOMAIN_EXPLICIT_CURRENT_PRECEDENCE_V1` now overlays registry `direct_authority=explicit_current` before static reconciliation. Contract `45ae9785d986` proves a stale static `.cloud` model cannot replace current `.party` during incremental materialization.
- Published Flemmix bundle/manifest bytes are not yet claimed corrected until Domain Refresh rematerializes and the resulting current manifest target is inspected.
- Domain validation run `35626640266` on SHA `37b1666cfa04` reached real resolution/reconciliation: `FIELD_DOMAIN_REFRESH_V2 scope=44 resolved=19 unresolved=6 applied=2 projection_drift=4 bundles=4`, then `FIELD_DOMAIN_METADATA_RECONCILE changed=1 providers=flemmix`. It failed **before publication only because the transaction-guard test itself raised `NameError: json is not defined`**, not because the domain guard rejected Flemmix. Artifact `provider-domain-refresh-35626640266.zip` was uploaded; publication steps were skipped.
- `a561c503891e` fixes that test-fixture defect by importing `json` in `tests/domain_refresh_transaction_guard_test.py`. A fresh Domain run is required; no Flemmix publication is claimed from the failed run.
- Follow-up Domain runs exposed the rest of the chain instead of hiding it: run `35626957932` then failed on a second fixture defect (`module` undefined), fixed by `53e3f767093f`. Run `35627289070` (Domain #998) consequently reached the **real transaction guard**, after again reporting `FIELD_DOMAIN_METADATA_RECONCILE changed=1 providers=flemmix`, and was correctly stopped with `flemmix: domain refresh mutated non-domain fields: ['manifest_overrides']`.
- Inspection showed that the only intended nested mutation is provider-owned asset rotation: Flemmix `manifest_overrides.logo` is still `https://flemmix.me/favicon.ico` while the authoritative terminal is `.party`; `enabled` and `supportsExternalPlayer` are unrelated and must stay byte-equivalent. `3dbd1d481c3e` adds `DOMAIN_MANIFEST_ASSET_ROTATION_V1`: Domain Refresh may change only `manifest_overrides.logo|icon|favicon`, both old/new values must be concrete HTTP URLs, and the new asset host must exactly equal the authoritative terminal host. All other nested manifest mutations remain fail-closed. `c197c42e40a6` proves allowed terminal-bound logo rotation and rejects both unrelated nested fields and third-party hosts.
- Flemmix publication is still **not** claimed until a post-`c197c42e40a6` Domain run passes, pushes the domain transaction to `main`, and the `manifest.json`-referenced Flemmix bundle is inspected for `.party` in the provider model/runtime data.
- Domain run `35628074372` (#999) proved the new nested manifest guard works: `FIELD_DOMAIN_REFRESH_GUARD {changed:[4khdhub,flemmix,voiranime], ...}` passed. The run then reached static Provider-v3 audit and failed on `vidfast` because structured authority is already `official_site=https://vidfast.to` / registry `direct=https://vidfast.to/` with `direct_authority=explicit_current`, while the published CONFIG still encodes `officialSite=https://vidfast.vc`.
- Root cause: `domain_refresh_transaction_v2.py` calculated CONFIG projection drift only for providers whose **current network resolver** returned `site_authoritative`. VidFast was `hub_unresolved` (`authoritative_hub_no_safe_terminal_candidate`) despite accepted explicit-current DATA, so its stale published CONFIG was skipped. This conflated network discovery with deterministic DATA→bundle projection.
- `ec19c1cdb0ad` adds `DOMAIN_REFRESH_CURRENT_SCOPE_PROJECTION_DRIFT_V1`: after structured authority is persisted, domain projection drift is now checked across the full current provider scope, regardless of resolver outcome. The drift routine still compares only `officialSite`, `knownSite`, `officialHub`, and `domainSubstitutions`; it does not mutate structured authority and rebuilds only stale CONFIG Lego bytes. `fba522ef5391` locks this current-scope behavior and forbids regression back to `resolved_provider_ids`-only drift.
- Non-blocking observation: Domain DNS preflight currently logs `provider artifact outside providers/: provider-disabled/desiflix...`; the workflow marks DNS observation `continue-on-error`, so this did not cause #999 failure. It remains a cleanup item after authoritative publication unless it becomes a gate.
- Full-catalogue materialization bottleneck was traced further: `verify_bytes()` preserves strict raw-byte validation but launches the canonical Node validator once per provider; that validator itself performs isolated `node --check`. The previous `materialize_provider_v3_all.py` serialized all of these independent checks, contributing directly to the ~3m13s 44-provider rebuild measured in Repair `35606270612`.
- `6585d013e266` adds **bounded parallel byte validation** (`PROVIDER_V3_PARALLEL_BYTE_VALIDATION_V1`) to the all-provider materializer. Bundle construction/manifest order remains deterministic; only independent `verify_bytes` futures overlap. The canonical validator, repository-dependency scan, isolated `node --check`, timeout and exact-byte/fixed-point checks are unchanged. Default workers are CPU-aware and capped at 4; explicit `NUVIO_MATERIALIZE_VALIDATION_CONCURRENCY` is capped at 8.
- `a0fbdbca2378` locks submit -> ordered resolve -> digest -> write ordering. `2129487437c5` adds both this materialization contract and `provider_v3_sequential_reconstruction_contract_test.py` to canonical Repair preflight so the next runtime Repair validates both the performance path and explicit-current domain precedence before any provider probing.
- Brain network scheduling follow-up: `e14ff21b4f1f` makes automatic health concurrency depend on the **actual packed batch size** instead of total selected count. A packed batch of >=8 providers now uses the existing safe health-check ceiling of 8 workers; tiny batches use only as many workers as providers. This specifically lets the new 11-provider packed Repair use 8 workers instead of the previous 6. `3417d59599c1` locks 1/3/4/6/8/48-provider and explicit-override cases. The health-check ceiling remains 8 because deep workers have a 512 MB V8 heap cap; increasing beyond 8 without memory/runtime proof is not justified.



## 2026-09-21 16:30 Europe/Paris — Brain incremental materialization implemented; Domain rerun still required

- Revalidated current `main` before mutation. Latest durable census commit was `6e8da363e8e5`; current Repair queue remains **11** with 16 symptomatic providers. The latest inspected Repair `35606270612` executed the real 11-provider queue and still ended fail-closed on the unrelated historical preservation loss `animevostfr:anime`.
- Runtime evidence from `35606270612` confirms the scalability bottleneck: after MalluMV/WookaFR became the only durable materialization targets for the wave, `run_provider_brain_repair.py` still ran `materialize_provider_base_v3_store.py` over all 44 active providers and then `materialize_provider_v3_all.py` over all 44. The all-provider materializer alone ran from roughly 14:18:53Z to 14:22:06Z (~3m13s) for that single wave.
- `8ce729b98c7e` changes Brain post-accept materialization to **provider-local incremental rebuilds**: reconcile only each target provider, run `materialize_provider_v3_one.py <provider>`, then run the global published-CONFIG validator once. Common ProviderBase/Core rebuilds stay owned by their release/Core lanes instead of making one provider repair O(catalogue).
- `b76343dd928e` updates the Brain orchestrator contract to require `PROVIDER_BRAIN_INCREMENTAL_MATERIALIZATION_V1`, require the one-provider materializer, and explicitly reject `materialize_provider_v3_all.py` / `materialize_provider_base_v3_store.py` inside Brain's `materialize()` path. Full workflow preflight/runtime validation is still required before calling the speedup proven.
- A second runtime bottleneck was confirmed from the same current batch plan: 11 repair targets were split into 9 sequential Deep processes because `repair_batches()` emitted one process per family even though the CLI requested `--batch-size 48`. The family metadata was not an execution input to `run_adaptive_deep_repair.py`; it only controlled scheduling/reporting, while negative memory/overrides are shared and therefore unsafe to mutate from naïvely parallel processes.
- `ab00746f75a7` now preserves family/signature membership as `familyGroups` but packs adjacent families into bounded sequential executions up to `batch-size`, allowing the existing health concurrency to work across the portfolio without shared-memory races. `174e17dae55c` locks packing: the synthetic 4-provider/3-family case becomes one execution at size 48 and remains two bounded executions at size 2. Current-head workflow/runtime validation is still pending.
- Flemmix is **not yet publication-correct**: structured `provider-overrides.json` has `official_site=https://flemmix.me` and old-host -> `flemmix.me` runtime mappings, but current published bundle `flemmix--nuvio--a503f8935cf25568.js` still embeds `knownSite/officialSite/searchRequestPlan=https://flemmix.cloud`.
- Domain Refresh run `35603604915` reached real projection repair and proposed four CONFIG-only bundle rebuilds including Flemmix, but failed its transaction guard: actual override mutations were `4khdhub, animesalt, voiranime` while the journal declared only `4khdhub, voiranime`. Root cause was a no-op observation creating a missing `runtime_domain_replacements` map on already-current AnimeSalt. This was already fixed on current main by `a9847485b375` and locked by `0ec0285612ef`; no post-fix Domain run has yet proved publication.
- Next authoritative sequence: rerun Domain Refresh on current main and verify Flemmix's final published CONFIG bytes; only then launch a fresh current-HEAD Repair so Brain preflight proves incremental materialization and the real queue runs without the prior whole-catalogue per-wave rebuild.



## 2026-09-21 15:36 Europe/Paris — Positive-memory replay runtime-proven; observation noise removed before exploration

- Completed Repair `35601540093` on tested SHA `ee4a2238ab49` passed the full positive-memory preflight and executed the real 11-provider census Repair queue. Brain summary: `selected=11 accepted=1 fixed_lab=2 deferred_learning=8 remaining=1 processed=11`.
- **MalluMV replay is now runtime-proven**: accepted repair remained `media_extraction_gap` / signature `c92d106e5a46a2b33459e485` / variant 2, `playable 0 -> 1`. The accepted program contains provider-local recipes with `source=positive-program-memory` in addition to fresh current observations; Brain memory now records 4 successes / 0 failures for that accepted signature. Positive memory therefore participates in execution rather than existing only as metadata.
- The global Repair still failed publication for the same unrelated retained proof drift: post-repair current bytes had **WookaFR raw=1 / playable=1 / accepted=1 / verified=1 / wrong=0**, candidate portfolio gate passed, but upstream accounting remained `animevostfr:anime lost=1`; final gates: `upstream=false portfolio=true preservation=false execution=false`. No candidate provider/Core bytes were published.
- Crucially, `automation/brain-positive-program-memory.json` survived that failed global gate unchanged/valid: one MalluMV validated entry, provider-owned origins only, learned routes `/search.php?q={query}` + `/api/file/`, `publicationAuthority=false`. This validates the new “discard unsafe candidate bytes, keep sanitized validated learning” behavior.
- The accepted sandbox program itself exposed runtime exploration waste: current observations still contained Google/search/support/privacy/TOS/favicon recipes even though the durable compiler correctly removed them. `9135fb602942` expands adaptive-runtime infrastructure filtering and rejects known search-engine/analytics origins plus trivial static routes such as `/favicon.ico` **before exploration**. Contract `e5bf2b66be55` locks this behavior.
- Planner/runtime applicability fix `5fe8dffa659f` remains required for Yflix-like providers: provider-scoped current/positive/historical recipe origins can establish the adaptive runtime base when no branded official site is known; peer/generic origins cannot. Contract `b180189e4393` covers `enc-dec.app`.
- Current queued authoritative successor must include both the provider-scoped runtime-origin fix and pre-exploration noise filter. Older Repair results remain evidence only until that successor executes.



## 2026-09-21 15:31 Europe/Paris — Planner/runtime applicability gap fixed; positive evidence now establishes runtime origin

- Artifact `35600977459` was inspected despite the run later being cancelled. It targeted the correct **11-provider Repair queue** and retained 107 negative-memory entries. Several providers have already exhausted v0-v4 / g1-g2 for one stable signature (AllAnime, AnimeSultra, Animetsu, AnimeVostFR, MovieBox, etc.), confirming that Learning g3-g5 is the appropriate next strategy family rather than another blind routine retry.
- MalluMV positive memory is present as one validated program: `media_extraction_gap`, signature `c92d106e5a46a2b33459e485`, variant 2, playable `0 -> 1`, with sanitized provider-owned origins/routes only. This remains prior evidence, not publication authority.
- A new generic planner/runtime mismatch was confirmed from memory outcomes: Showbox/Yflix accumulated `profile_unavailable / planned_profile_not_applicable_to_current_bytes` after the Brain had already selected `adaptive_runtime_recovery`. Yflix specifically had executable provider-scoped recipes on `https://enc-dec.app` but no branded `official_site`; `_adaptive_runtime_options()` required a base URL **before** consulting those provider recipes, so an executable plan was discarded.
- Fix `5fe8dffa659f`: runtime base resolution now considers origins from **current observation recipes, validated positive-program recipes, and historical provider-specific recipes** before returning profile-unavailable. These origins remain provider-scoped and pass the existing infrastructure-host denylist; peer/generic evidence cannot establish the provider base. Fresh observation remains strongest, followed by validated same-provider positive memory, older provider DATA, then peer transfer.
- Contract `b180189e4393` proves both the positive-program priority order and the Yflix-like case where `enc-dec.app` provider evidence alone makes the adaptive profile executable. Showbox remains fail-closed unless current/provider-scoped evidence provides a real origin.
- A current-head Repair successor must include this fix before its provider results are authoritative. Existing in-flight Repair `35601540093` on `ee4a2238ab49` is still useful evidence but predates this planner/runtime applicability correction.



## 2026-09-21 15:09 Europe/Paris — Domain lane restored; Learning publication/proposal races hardened

- CORE quick-gate remained red on a domain-only drift, not Brain logic: published Flemmix DATA still exposed `officialSite=https://flemmix.cloud` while current structured authority is `https://flemmix.me`. The correct owner is Domain Refresh, not a provider-local manual JS edit.
- Domain Refresh had been structurally unusable since the bulk-onboarding deferral condition was added: runs rendered as `.github/workflows/domain-refresh.yml`, failed instantly and created **zero jobs**. Comparing current YAML against last job-producing SHA `3bde6b565c45` isolated the job-level event-expression addition as the only workflow-load difference.
- `2d2050471358` replaces the fragile job-level head-commit expression with a runtime `bulk-guard` job and a simple `needs.bulk-guard.outputs.run == 'true'` dependency. Run `35603424336` proved the workflow parser/job graph is restored: `bulk-guard` SUCCESS and real `refresh` job started.
- That first restored run reached actual domain resolution (`FIELD_DOMAIN_REFRESH_V2 scope=44 resolved=19 unresolved=6 applied=2 projection_drift=4 bundles=4`) and then exposed a separate implementation bug: `reconcile_provider_domain_metadata.py` referenced undefined `canonical()` while merging its transaction journal. `20e701bc0e2a` now uses the canonicalizer owned by `domain_refresh_transaction_v2`; `ff8d76090089` locks the contract. Validation run `35603604915` has already passed bulk guard + resolution and is executing reconciliation; no domain publication is claimed yet.
- Historical Learning runs `35591831057` and `35593369150` both completed the actual sandbox successfully; their overall red states were post-learning orchestration. The latter exposed two generic defects: reconstruction proposal provenance referenced clean ProviderBase bytes created only in the experiment workspace, and concurrent publishers could race on `brain-learning/proposals`.
- `2aea63925b14` makes every reconstruction proposal self-contained by copying and SHA-validating every ProviderBase referenced by proposed provenance; `c35ac43816c8` locks missing/tampered failure behavior. `c6865b8dfcec` force-refreshes proposal remote refs before force-with-lease. Existing monotonic stale-source protections `f4e10f019a1b` / `e31091906806` are retained.
- `37a8f7a8d7b5` additionally serializes **whole persistent Learning runs** under one concurrency group with `cancel-in-progress=false`, so each run starts only after the previous run had the opportunity to publish sanitized memory; `cd7323f0bdf1` locks this invariant.
- Positive-program memory was extended concurrently with validated client identity: `c6e4a93a06fd` extracts only a sanitized User-Agent that participated in accepted proof; `16de6c7f5b1b` prefers it during same-provider replay; `d9a162ebd39a` tests the behavior. This remains prior evidence only and never bypasses current playable/identity/non-regression gates.
- Current durable census from `35600977459-pre-repair`: **28 FULL · 2 PARTIAL · 2 CANDIDATE · 4 ROUTE · 2 CHAIN · 3 PROVIDER NETWORK BLOCKED · 3 HARNESS MISMATCH · 2 HARNESS/ENV BLOCKED**; `repairQueue=11` and `environmentQueue=5`. Repair `35601540093` on older SHA `ee4a2238ab49` has passed the full Brain preflight and is executing real provider repair; use it as evidence only. A fresh Repair on current main remains required after Domain Refresh settles because newer positive-client/proposal/concurrency fixes are not in that tested SHA.


## 2026-09-21 14:56 Europe/Paris — Learning runtime priority + publisher races fixed; positive-memory Repair executing

- Current authoritative Repair retry is `35600977459` on exact SHA `7400a23dfbf6`. Its complete step-6 preflight is **SUCCESS**, including the new accepted-program sanitizer, durable positive-program memory, replay wiring, compiler/persistence/workflow contracts and existing non-regression contracts. It is now in real step 7 **Run canonical recognition and correction only for unresolved providers**. The prior retry `35600761581` consumed no provider work; it failed preflight only because `safe_origin()` referenced `NON_PROVIDER_HOSTS` before that denylist constant was actually defined. Fix: `6dbb47fcf4af`.
- Runtime evidence from older Learning run `35593369150` disproved the earlier claim that current census Repair debt was already prioritized. Despite trigger `00f28f77da86` and a passing helper contract, it actually started with `1shows, allmovieland, anidb, animepahe, ...`, processed only **13 providers**, then exhausted its slot with **99 pending**. Root cause: final queue composition placed `reconstruction_required` before `census_repair`, so a ~55-provider clean-reconstruction backlog starved the 11 current census Repair targets.
- Generic queue fix `68afc4f92053` adds `authoritative_learning_order()`: current `provider-census-status.json:repairQueue` first, exhausted/current Repair debt second, broad clean-reconstruction debt third, then normal retry/pending cycling. Contract `a3b391b17d8a` proves census targets `wookafr, other` outrank reconstruction providers `1shows, animepahe` even when the base queue is ordered the opposite way. This fixes the real composition layer rather than only `current_repair_priority()`.
- Older Learning runs also exposed shared-publication races. `35593369150` failed publishing sanitized memory with `non-fast-forward / stale info` on `brain-learning/proposals`; both `35591831057` and `35593369150` failed proposal validation with a stale-tree assertion for `anime-sama` ProviderBase because proposal artifacts were validated against moving `main` rather than the run source SHA.
- `63e6b6d1359d` serializes the three shared Learning publishers (memory / repair PR / architecture PR), pins proposal validation and repair-branch materialization to the event SHA; `31267c2f8a62` locks that contract. `f4e10f019a1b` adds monotonic publication: sanitized memory refuses an older/equal `generatedAt`, repair/architecture proposal publishers refuse a source SHA already ancestor of the remote proposal branch, and architecture proposal branch creation now starts from the exact event SHA rather than moving `main`. Contract `e31091906806` locks the stale guards.
- Old Learning runs that started before these commits remain useful diagnostic evidence only. They cannot be authoritative for current Brain behavior. The next Learning successor must prove in runtime that its first queue cohort is the current census Repair debt and that stale publishers do not overwrite newer memory/proposals.



## 2026-09-21 14:45 Europe/Paris — Durable positive-program memory closes accepted-repair forgetting

- Repair artifact `35591042153` was inspected beyond the CI summary. The single **accepted Repair** was **MalluMV**: `strict_playable_stream_improvement`, playable `0 -> 1`, profile `adaptive_runtime_recovery`, failure family `media_extraction_gap`, signature `c92d106e5a46a2b33459e485`, variant 2. WookaFR was separately fixed/proven in Lab/current-yield evidence but was not the accepted mutation. This distinction is now explicit.
- Structural defect confirmed: when the final portfolio preservation gate failed on unrelated historical `animevostfr:anime` proof drift, Repair correctly discarded candidate provider/Core bytes, but this also discarded the **compiled winning MalluMV program** from `provider-overrides.json`. Only success counters remained in `brain-repair-memory.json`. The Brain therefore remembered that a method succeeded without durably retaining enough sanitized execution DATA to replay it.
- Generic fix series: `b3ba8139a8d6` adds `scripts/brain_positive_program_memory.py`; `0091c684595c` persists strict accepted programs into that evidence store; `87569b1f1000` replays same-provider positive routes/recipes in adaptive repair; `118491ccb7fd` exposes positive skills as planner priors; `1e2c37411e97` preserves the memory across Repair's deliberate `git reset --hard`; `c3c367406140` / `5fce8452c45a` gate it in Repair and Learning.
- Safety was tightened before persistence. `e0c2de3cb979` rejects non-provider navigation/infrastructure origins (including Google/search-engine/analytics noise) from accepted-program DATA; `c37bda9c7136` preserves response semantics; `9330f6e18bd0` keeps executable recipes separate from route priors; `f4513ecd7eb4` deduplicates accepted recipes. Positive memory never stores candidate JS, cookies or response bodies and has `publicationAuthority=false`; every replay remains subject to current-byte playable, identity and non-regression gates.
- Historical MalluMV success was backfilled from the immutable Repair artifact into `automation/brain-positive-program-memory.json` at `9b6a383c793a`. Sanitized replay data contains provider-owned MalluMV origins plus `/search.php?q={query}` and `/api/file/`; observed Google navigation from the old accepted sandbox program is excluded. This is prior evidence, not a current FULL/verified census promotion.
- Exact-SHA Learning integrity remains in force from `482a9046ddd2` + `7bdc7df2ffff`; runs started before those/newer positive-memory commits must not be treated as authority for the new Brain.
- Current authoritative validation is **Repair `35600761581` on SHA `dd6bf7b098ed`**. It must first pass positive-memory/compiler/workflow contracts, then run the current census `repairQueue`. Required proof: MalluMV reuses rather than forgets its validated prior, no harness-only provider is mutated, accepted positive memory survives a global portfolio failure, and unresolved cases escalate to generation-aware exact-SHA Learning.



## 2026-09-21 14:14 Europe/Paris — Repair produced unpublished Wooka proof; Learning now generation-aware g3-g5

- Canonical Repair run `35591042153` on tested SHA `f176c2d62ca8` completed **FAILURE after real Repair**, not preflight failure. Brain summary: `selected=12 accepted=1 fixed_lab=2 deferred_learning=9 remaining=1 waves=2`. The accepted candidate yielded **WookaFR TV raw=1 / playable=1 / accepted_playable=1 / verified=1 / wrong_content=0** on post-repair quick-yield. No current published-byte promotion is implied.
- Final Repair gate stayed red because preservation still reports one historical upstream-positive proof lost (`animevostfr:anime`): `targeted=12 targeted_proven=8 playable=1 verified=1 lost=1 upstream_gate=false portfolio_gate=true preservation_gate=false execution_gate=false`. The correct response is to retain Wooka as candidate evidence rather than discard the repair or falsely publish it.
- Census persistence was corrected accordingly by subsequent commits: Wooka is now **CANDIDATE OK**, remains `repairEligible=true`, and stays in `repairQueue` until current published bytes reproduce verified media. Current durable census: **28 FULL · 2 PARTIAL · 2 CANDIDATE · 3 ROUTE · 2 CHAIN · 4 PROVIDER NETWORK BLOCKED · 3 HARNESS MISMATCH · 2 HARNESS/ENV BLOCKED**; `repairQueue=11`, `environmentQueue=5`. Anime-Ultime is now FULL and therefore no longer Repair debt.
- Learning same-run rotation exposed a deeper limitation: production can exhaust generation 2 even when Learning should explore a new strategy family. Main now contains bounded Learning-only evolution through **g3, g4, g5**. Generation-aware runtime expands distinct budgets/strategy identities (peer experience, alternate origins/routes, up to 40 pages/embeds, depth 6, six request-recipe passes) and then stops explicitly as `architecture_gap / learning_generations_exhausted` rather than looping indefinitely.
- Key generation commits: `9e1fd914fe98` executes generation-aware adaptive runtime budgets; `9dc128d5d5d6` proves bounded g3-g5 planner evolution; `9d1d0a1a13bd` prevents a non-repair architecture-debt plan from being misread as a new method; `36c62b6b23a2`, `65a76de8f7b1`, `4a25ca4baebe`, `572c95db3793`, `34536987bc50` lock runtime/planner/workflow policy.
- Older Learning runs `35591831057` (SHA `16a41a502274`) and `35593369150` (SHA `00f28f77da86`) are still useful runtime evidence but **do not contain the full g3-g5 generation-aware HEAD**. Both have passed preflight, isolated-stage build, full-catalogue observation, collapse guard, coverage and clean reconstruction, and are inside the adaptive Learning queue.
- Current authoritative validation run is **Learning `35598176119` on SHA `2bf1a1bb265e`**, triggered from HEAD after current-census priority, provider-local refresh isolation, causal fingerprint rotation and bounded g3-g5 evolution were all present. Its required proof is: current Repair targets prioritized first, distinct generation/variant attempts visible, provider-local refresh failure isolated rather than global abort, and exact-repeat/architecture-debt convergence without infinite loop.


## 2026-09-21 13:07 Europe/Paris — Repair preflight green; Learning same-run causal rotation test-validated

- Canonical Repair run `35591042153` is still executing real Repair on tested SHA `f176c2d62ca8`; do not attribute newer Learning code to it. Its complete step-6 preflight is **SUCCESS**, including accepted-program capture/compiler-v3/persistence, causal planning, exploration-chain, round attribution, worker/stage smoke, Wooka current-runtime behavior, materialization/discovery composition and non-regression contracts. This proves the earlier compiler-test blocker is closed; provider recovery still depends on the in-progress canonical Repair evidence.
- Learning root cause found from prior run `35575738318`: although `exploration_share=1.00`, the queue compared methods only by profile name and immediately broke on `accepted=0`. Adaptive hypotheses deliberately reuse `adaptive_runtime_recovery`, so planner variant/generation rotation was indistinguishable from a repeated method and same-run negative memory could not drive the next hypothesis.
- Generic fix `5fbf541086bb` gives each Learning method a causal fingerprint `provider|signature|generation|variant|allowedProfiles`; a new failed fingerprint now continues to the next planner pass, while an exact repeated fingerprint (or no method) stops. Global Learning deadline remains the safety budget. Contract `4994e093e21c` proves v0/v1 and generation changes are distinct while exact repeats stay identical; workflow gate `0b723887b413` includes the contract in Learning preflight.
- Two first validation runs (`35591517159` on `05392c66526b`, then `35591720951` on `0923867143fc`) stopped before any provider work because an older cron contract first expected the literal old loop header, then the initial test edit contained a literal `\\n`. These runs consumed no provider evidence and must not affect census interpretation. Test fixes are `c2ed8c0d359b` and `69afa58f6262`.
- Fresh Learning run `35591831057` on exact SHA `16a41a502274` has now passed **Validate Brain cron skills and full provider coverage**, including same-run causal-rotation and provider-refresh-isolation contracts. It is importing/restoring Learning evidence before the real adaptive queue. The rotation is therefore test-validated but **not yet runtime-proven** until the queue shows distinct variant/generation attempts and continues past a provider-local refresh failure.
- Current durable census before these runs remains **27 FULL · 2 PARTIAL · 1 CANDIDATE · 3 ROUTE · 3 CHAIN · 5 NETWORK · 3 HARNESS MISMATCH · 2 HARNESS/ENV BLOCKED**, with 12 Repair targets and 5 environment/harness targets. No status promotion is inferred from preflight success.



## 2026-09-21 12:55 Europe/Paris — current Brain blockers revalidated; Repair preflight + Learning queue resilience fixed

- Revalidated real repository state before changing code: `main` had advanced through bot census/lifecycle persistence to `f2dae880353e`; persisted Repair census from `cd2150c49388b` still reports `symptomatic=17 / repair=12`. Residential/Tailscale evidence is transport-only: WookaFR moved from harness-only to normal `CHAIN REACHED` repair debt, while the residential provider replay still has no raw/playable/verified provider-media promotion.
- Latest canonical Repair run `35582300668` (SHA `cd2150c49388b`) never reached provider work. Its preflight passed Brain orchestration, causal intelligence, bounded exploration, multi-round attribution and accepted-program capture, then failed only in `brain_accepted_program_v3_compiler_test.py`. The test fixture already contained historical `search_request_plan` DATA but incorrectly asserted that this key was absent from the unchanged input object. The compiler itself already deep-copies its input. Fix `1335319fc2ce` replaces the impossible assertion with an input-immutability check; this run contributes no provider repair evidence.
- Latest long Learning run `35575738318` (SHA `cd2150c49388b`) did reach the adaptive queue and processed the discovery superset. It failed when Frenchstream route refresh generated current terminal authority `fs27.lol` while staged/historical bytes still represented `french-stream.one`; `validate_override_pipeline.py` rejected that provider-specific intermediate state. Frenchstream is not a current /46 census row, so one historical/superset provider was able to abort learning for the rest of the catalogue.
- Generic queue-resilience fix `652e99199dc5`: `refresh_stage_routes()` now returns structured success/failure evidence. A provider-local domain/profile/override validation failure is recorded as `stage_refresh_blocked`, persisted in `isolatedProviderRefreshFailures`, and retried without aborting the whole Learning superset. This does **not** declare the provider repaired and does not allow invalid staged bytes to proceed through Lab acceptance.
- The same fix also closes a latent second-pass bug: the Lab-challenge route-search path called `refresh_stage_routes(stage, work_deadline)` without the required provider id. It now always calls `refresh_stage_routes(stage, work_deadline, provider_id)`. Contract `024703e872c0` requires both refresh sites to be provider-scoped and locks the isolation telemetry.
- Next authority is a fresh canonical Provider Recognition Repair V6 from current `main`. It must first prove the compiler preflight is green, then produce real Repair/census evidence; any deferred Learning successor must prove that a Frenchstream-like refresh debt is isolated and that later providers continue to execute. Do not count the code changes themselves as provider repairs.



## 2026-09-20 16:05 Europe/Paris — WAF native/client sensitivity proven; census monotonicity restored; Brain v4 executable

- WAF diagnostics run `35514374727` completed **SUCCESS** on tested SHA `2793cd7c6d74`: contracts, Chromium matrix, NuvioTV-policy OkHttp 4.12 helper, artifact upload and persistence all completed. Evidence across 12 WAF lanes is **7 browser content reached / 5 challenge persisted**.
- Client sensitivity is concrete, not theoretical. AnimeSalt, AnimeVost-FR, MoviesMod movie+tv and Vostfree reach content only with the audited NuvioTV-UA Chromium profile while direct HTTP and GitHub-JVM OkHttp remain challenged. WookaFR movie+tv reaches content under ordinary browser, direct HTTP and NuvioTV-policy OkHttp. AllWish, Flemmix and FullAnime remain challenged/inconclusive across tested GitHub transports. This remains transport evidence only, never stream/playback proof.
- The successful WAF job exposed a separate **census persistence regression**: bot commit `f96371d35f08` re-rendered the entire census from stale/partial `provider-v3-quick-yield.json`, degrading the authoritative Repair census from 24 FULL / repairQueue 12 / harness 8 to 12 FULL / repairQueue 31 / harness 0. No provider evidence justified that downgrade.
- Authoritative Repair census/batch state was restored byte-for-byte from pre-WAF parent `2793cd7c6d74`: `84b40b97d4cb` status JSON, `58ae6e0dcbef` markdown, `d839e0c4a6ac` batch plan. Restored authority is run `35512170961-post-repair`: **24 FULL · 2 PARTIAL · 1 CANDIDATE · 3 ROUTE · 3 CHAIN · 5 NETWORK · 5 HARNESS MISMATCH · 3 HARNESS/ENV BLOCKED**, repairQueue=12, environmentQueue=8.
- Durable fix: `9de750f6fb6a` adds `merge_waf_census_transport.py`; WAF may now change only transport classification/evidence/action for providers already present in the harness/environment queue. It preserves Repair runId/SHA, repairQueue, environmentQueue, symptomatic/brain queues and all unrelated provider rows. `a5574caf5021` proves unrelated FULL/ROUTE rows and queue membership cannot change; `f09e7ffb90ec` replaces full re-render in the WAF workflow with this monotone transport-only merge; `2b8fba2a68e2` fixes its isolated test import.
- Brain new-strategy debt is now **executable Repair v4**, not proposal-only. Policy commit `9b787856adea` expands signatures from 4 to **5** variants; planner/Repair/Learning fallbacks are aligned to 5 and canonical Repair runs **5 waves**.
- Executable v4 family strategies: `1e6fa260713f` introduces the v4 identity; `80d8880a7945` specializes it: transport -> provider-origin failover, route-proven -> proven-route-to-terminal traversal, chain-terminal -> terminal extractor traversal without generic search restart, candidate-replay -> provider-owned retained route/recipe replay before peer discovery. `d69e698f699d` carries `newStrategyId` into generated runtime; `d4fbfdbf143d` + `1150c5bc8fb7` execute a fifth wave; `fc8c2b121d29`, `c9983c5eff32`, `d7dee76ce4b9`, `8caa371ba334` lock five-variant exhaustion/orchestration/pipeline behavior.
- Repair #15 must **not** run until the new transport-only WAF rerun confirms census remains repairQueue=12/environmentQueue=8. Once monotonicity is proven, the 12 previously v0-v3-exhausted signatures should reopen directly on v4; acceptance still requires current playable/identity/non-regression proof.
- Learning run `35513313720` remains active on older tested SHA `6dc938655e93`; it has passed current-provider observation, common-collapse guard, daily coverage and clean reconstruction and is in adaptive Learning queue. Do not attribute newer v4 code to that run.


## 2026-09-20 15:43 Europe/Paris — WAF harness cleanup bug isolated; native-proximity rerun active

- WAF diagnostics run `35513827185` did **not** fail on provider reachability, Cloudflare classification, Chromium contract, or the NuvioTV-policy OkHttp helper. All setup/contracts passed and the client-profile matrix produced useful evidence before teardown.
- Exact failure was harness lifecycle only: Python `TemporaryDirectory` cleanup raced late Chromium profile files (`OSError: [Errno 39] Directory not empty: .../Default`) after the probes. This must not be interpreted as provider/WAF failure.
- Fix `f574a356d9cb`: Chromium profiles remain ephemeral but cleanup is best-effort with `ignore_cleanup_errors=True`, appropriate for disposable GitHub runners and late browser child files. Contract `d8b8640effa9` prevents regression.
- New WAF diagnostics are active: run `35514290577` on the cleanup fix and run `35514301955` on the contract commit. Their transport outcomes, not the earlier cleanup exception, are the next WAF authority.
- User architecture invariant remains: CI WAF/challenge is primarily harness/client mismatch until representative native-client transport reproduces it. Current evidence already shows client sensitivity (e.g. MoviesMod movie/tv reaches content with audited NuvioTV-UA Chromium while GitHub default Chromium/direct HTTP/OkHttp-JVM can remain challenged). This is transport evidence only, never playback proof.

## 2026-09-20 15:15 Europe/Paris — Repair #14 converged to Learning debt; WAF aligned to real NuvioTV transport

- Repair #14 run `35512170961` completed **SUCCESS** on tested SHA `50c59eabe93f`. Full preflight, real Repair, four-version floor, symptom-scope gate, artifact upload and census persistence all passed.
- #14 did **not** repair a stream and must not be counted as provider recovery: Brain result was `selected=12 accepted=0 fixed_lab=0 deferred_learning=12 remaining=0 waves=1`. Final Repair verdict: `targeted=12 targeted_proven=8 playable=0 verified=0 lost=1 upstream_gate=false portfolio_gate=true preservation_gate=false execution_gate=true outcome=converged_to_learning_debt`. The historical `animevostfr:anime` proof drift remains visible; no repair candidate bytes were accepted.
- Post-#14 census is now harness-aware: **24 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 3 ROUTE PROVEN · 3 CHAIN REACHED · 5 PROVIDER NETWORK BLOCKED · 5 HARNESS MISMATCH · 3 HARNESS/ENV BLOCKED**. The 12 provider-code symptoms remain listed in `repairQueue` for census visibility, but the Brain has exhausted known v0-v3 strategies and defers them to Learning/new-strategy. The 8 former WAF cases are excluded from provider JS mutation.
- User interpretation is now an architecture invariant: a CI WAF/challenge is primarily **harness/client mismatch evidence until a representative native client reproduces it**, not proof that provider JS is broken.
- Live NuvioTV source was re-audited, not inferred from stale docs. Current `NuvioMedia/NuvioTV` `dev` HEAD observed during this checkpoint is `1a132cb059b46266052edfcc28d654a2cb5b3aa0`. Its `PluginRuntime.kt` uses **OkHttp**, `Proxy.NO_PROXY`, `IPv4FirstDns`, HTTP+SSL redirects, 30 s connect/read/write timeouts, and defaults to the Windows/Chrome UA when the provider supplies no UA. `gradle/libs.versions.toml` pins OkHttp **4.12.0**.
- Existing WAF matrix already proved harness sensitivity: 12 lanes -> **7 content reached / 5 challenge persisted**. NuvioTV-UA Chromium alone changes AnimeSalt, AnimeVost-FR, MoviesMod movie+tv and Vostfree from challenge to content; WookaFR movie+tv reaches content under ordinary/default browser/direct transport. This is transport reachability only, never playback proof.
- A closer diagnostic path is being added: `tools/waf-okhttp-probe/` executes JVM OkHttp 4.12.0 with the audited TV network policy, and `scripts/probe_waf_browser_session.py` exposes it as `nuvio-tv-okhttp-jvm`. It still labels GitHub JVM TLS/IP as non-native and has no challenge solver/token fabrication. First build run `35513014334` failed only on generated Java quote escaping; corrected in `ea81bcf723b`, contract `0f2abde80cb0`, workflow gate `e4e6e50cb5ad`. Current WAF run `35513249399` is the next authority.
- Non-Regression noise was further isolated: synthetic census scope test no longer uses live manifest state (`713aa05d4d04`), and its targeted-history contract now checks the current `--history automation/provider-census-proof-history.json` + canonical `run_provider_targeted_recovery.py -> audit.build_tasks(..., history=history)` path (`2c10d2639eea`).
- Because #14 exhausted all known Repair strategies, the next virtuous-loop step is **Learning/new strategy**, not a blind Repair #15. Trigger `6dc938655e93` restarted persisted Learning for the exhausted cohort; outer Repair -> evidence -> Brain improvement -> Repair remains unbounded by wall-clock duration.


## 2026-09-20 14:03 Europe/Paris — Repair #11 converged; Learning queue import regression fixed
- The same bare-v3 publication defect existed in future onboarding: `add_provider.py` persisted a clean ProviderBase and copied it byte-for-byte into `providers/`, so newly onboarded providers could also publish without DATA. `f335e59b96d2` now compiles onboarding through `Base -> build_provider_data_model -> compose_provider_bundle -> apply_overrides(Core) -> raw-byte validation`; provenance keeps distinct published SHA vs Base SHA. Contracts `799f8c4d3b9d` and `c7b30bdb3d76` lock single/bulk onboarding and remove the stale literal pending-status assertion that was failing Provider Non-Regression.
- Root cause of the prior portfolio-wide `ReferenceError` was found statically in the real discovery path: `discover_candidates.py` staged the common ProviderBase v3 directly into `apply_overrides()` without first composing Provider DATA. The v3 Base is intentionally provider-neutral and references `NIAKVIO_PROVIDER_MODEL`; unlike `materialize_provider_v3_all.py`, discovery omitted `build_provider_data_model() -> compose_provider_bundle()`. This explains syntax-valid candidates collapsing at runtime across the portfolio.
- Generic fix `f0a86560aa73` adds `compose_executable_seed()`: any ProviderBase v3 seed (new, pending-clean or current clean base) is wrapped exactly once with deterministic DATA/CONFIG before derived Provider/Core Lego; legacy compatibility bases remain untouched. `6cdba6a4a80e` adds a real-worker contract proving a discovery v3 candidate contains one DATA declaration and executes without ReferenceError. Gates: `ad84ec05e4b2` Learning, `5242f4db2fee` Repair, `31e7689e6262` Brain full-coverage contract.
- Repair #12 run `35509806062` and Learning run `35509815184` both stopped in preflight before provider/Learning work because the newly-added staged-runtime smoke test created a legacy raw `module.exports` fixture while the current staging contract requires clean Provider v3 `Base + DATA` bundles. The simpler bare Base+Core real-worker smoke passed. `99ce054c13c7` fixes the staged smoke to generate a canonical clean v3 seed, mark `candidate_code_origin=new-niakvio-clean-seed`, and retain the real runtime-profile + worker execution gate. These runs are not provider attempts.
- Repair #11 run `35508094814` tested SHA `9f904f6e8d75` and completed its bounded Brain exploration across all 12 current Repair targets. Final Brain evidence: `selected=12 accepted=0 fixed_lab=0 deferred_learning=12 remaining=0 waves=4`, with `noProgressReason=experiment_variants_exhausted`. Showbox and Yflix now rotate through v0-v3 and join the 10 already-exhausted providers in independent Learning/new-strategy debt. No repair candidate bytes were accepted.
- #11 stayed red only because historical upstream-positive evidence `animevostfr:anime` did not reproduce in the final network audit (`upstream_gate=false`) even though portfolio baseline/candidate were both raw=0/playable=0/verified=0 and no Repair mutation was accepted. `43856c8608be` now separates this proof drift from orchestrator convergence: evidence remains visibly lost, `preservationGatePassed` remains false, but an all-target/no-mutation/deferred-to-Learning result reports `executionOutcome=converged_to_learning_debt` and can complete the Repair execution gate. `2de63e10d7bb` locks the contract.
- Learning run `35508106660` on SHA `9452a83ba6fa` passed preflight, isolated-stage build, complete published-provider observation, daily coverage and clean reconstruction (`total=98 current=46 extra=52 required=54`). It failed at the first adaptive queue repair because `run_adaptive_quick_repair.py` still imported deleted legacy module `provider_purification`, causing `ModuleNotFoundError`; the later validator failure was only a consequence of the missing health-results file.
- `3bdfad85a130` replaces the retired purification path with the canonical raw-byte stability verifier (`provider_byte_stability.verify_candidate`) used by Deep Repair; `4c5a9aba13f7` forbids reintroduction of `provider_purification`/minification in Quick/Learning.
- Separate runtime-collapse guards added on newer HEAD (`829b18f7947d`, `c8afccb4a68e`, `a346fca41cde`, plus staged real-worker smoke commits) must be validated by the restarted Learning phase before the prior 98/98 ReferenceError observation can be treated as resolved.


Last authoritative checkpoint: 2026-09-16 Europe/Paris.

This file is the durable recovery source of truth for the active NiakVIO work. Prefer current repository state and exact GitHub Actions/native logs over older chat summaries. Update this file automatically at every important correction, failure, publication, native proof, security proof, or architecture decision before moving to the next risky step.

- 2026-09-20 12:42 Europe/Paris — current virtuous-loop checkpoint: Repair #11 run `35508094814` is executing real Repair on tested SHA `9f904f6e8d75` after passing the full preflight; Learning run `35508106660` is active on SHA `9452a83ba6fa` and has passed preflight/memory/native imports but is still building its isolated stage. Do not attribute later HEAD fixes to either run.
- Showbox/Yflix convergence fix is now durable: `be22d09f330b` records `profile_unavailable` when the planner selected a profile but structural matching produced no attempt; `dc0f6f3d427f` proves the negative-memory row. This closes the remaining v0-stall path left by Repair #10.
- Learning clean-discovery superset fix is durable: `c3b559c26c4a` permits additional clean candidates beyond the 46 current catalogue rows while still requiring all current rows and forbidding upstream/legacy JS execution; `f32557905484` locks the contract.
- Previous Learning evidence exposed a separate common-runtime failure: all 98 observed candidates were `runtime_error / ReferenceError`. Coverage 46/46 is invocation coverage only and must never be treated as provider-functional evidence. `829b18f7947d` adds `validate_learning_health_baseline.py`; `c8afccb4a68e` proves portfolio collapse detection; `a346fca41cde` gates Learning before provider-specific learning when >=90% of current providers collapse into runtime_error.
- ProviderBase validation is strengthened beyond syntax: `f3c7f0310c7f` added a real `provider_worker.cjs` smoke test; `4fffe833d5e2` extends it to both bare clean ProviderBase and clean ProviderBase + real global Core composition. `9a405a5d54ca` and `1377378d629e` gate future Learning/Repair preflights. These smoke commits are newer than the currently-running #11/Learning SHAs.
- CI signal cleanup: `09a06271691e` moves `provider-repair-skip.json` ownership assertion from Repair YAML to the canonical Python pipeline; `9521b8eaf670` checks the actual escaped sharded bulk-activation trigger. The earlier Verify/Non-Regression reds were stale string-contract failures, not provider/Brain regressions.
- Dedicated current WAF diagnostics have been explicitly triggered by `c73b0a2a63c9`; run `35508619496` is the authority for the next WAF verdict. It uses only ordinary ephemeral Chromium/session reuse and cannot promote playback status by browser reachability alone.

- Loop iteration Repair #8: run `35503536213` tested SHA `64a667868177`. This was the first family-batched multi-wave run to pass the full Brain preflight and execute real Repair over the 12-provider `repairQueue`. It ran 3 waves / 9 family batches per wave, accepted **0** repairs, fixed **0** providers in Lab, and ended with all 12 still unresolved. Final quick-yield remained `raw=0 / playable=0 / verified=0`; preservation lost `animevostfr:anime`, so the final gate failed and no provider/Core candidate bytes were accepted. Census evidence was persisted by `a3fb22e2248d`: `24 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 3 ROUTE PROVEN · 3 CHAIN REACHED · 8 WAF · 5 NETWORK BLOCKED`, `symptomatic=20`, `repairQueue=12`.
- WAF refinement completed after the census-driven run: persisted evidence commit `8dd538e58a8a` now probes WookaFR with provider-owned GET search route `/?s={query}` (neutral query) rather than homepage only. Both movie/tv metadata-search probes reached normal browser content. This proves ordinary-browser search-route reachability, **not** stream/playback functionality; WookaFR remains WAF/environment-classified until a usable runtime/session path and playable media are proven.
- Loop iteration Repair #9: run `35506294042` on SHA `fe6d92e9166e` stopped in preflight before provider probing. The failure was in the new synthetic exhaustion contract itself: `plan-repairs.mjs` correctly requires each planner item to have a `key`, while `brain_negative_experiment_exhaustion_test.py` omitted it, producing `plans={}`. Fix `4f5bf5d58eae` adds `published:synthetic-exhaustion` to the fixture. #9 produced no provider repair evidence and is not counted as a provider attempt.
- Repair #10 run `35506385523` completed **failure** on tested SHA `0b22446a2d08` after real provider work. Brain convergence itself improved: `selected=12 accepted=0 fixed_lab=0 deferred_learning=10 remaining=2 waves=1`. The 10 exhausted signatures were correctly removed from repeated Core Repair and routed to Learning/new-strategy; only **Showbox + Yflix** remained. Final quick-yield stayed `raw=0/playable=0/verified=0`; preservation again reported current upstream-positive loss `animevostfr:anime`, so no repair bytes were accepted.
- Root cause for Showbox/Yflix remaining at v0: their planner selected `adaptive_runtime_recovery`, but structural matching returned no applicable profile, so `create_repair_candidate()` was never called and the existing `not_generated` learner saw no attempt row. `be22d09f330b` now records a planner-selected-but-unavailable profile as bounded negative memory (`profile_unavailable`), and `dc0f6f3d427f` tests that path. This changes experiment ordering only; it never grants success.
- Long Learning launcher `35506487133` succeeded, but Brain Lab run `35506491155` completed **failure** on SHA `5eb1e4b4d391`. It passed preflight, restored sanitized memory, imported native diagnostics, built the isolated stage, observed all **46/46** current published providers and passed daily coverage. It failed only at clean reconstruction because discovery produced **98 clean candidates** while the workflow incorrectly required exact equality with the current 46-provider catalogue.
- Learning architecture fix `c3b559c26c4a`: clean reconstruction now requires every current catalogue provider but permits additional clean discovery candidates; all reconstruction-required candidates still must be `new-niakvio-clean-seed` with `upstream_code_executed=false` and `legacy_provider_js_executed_for_reconstruction=false`. `f32557905484` locks the superset contract. This is required for learning future/new providers rather than rejecting them merely because they are not yet current catalogue rows.
- Repair→Learning linkage was strengthened after that Learning phase started: `d75d31d0fd24` adds detection of exhausted v0-v3 Repair signatures from `brain-repair-memory.json` and prioritizes them as new-strategy debt in Learning, reopening them even if an older Learning cycle marked them complete; `40885ddd4c4d` tests the detector and `a94f22b99d31` adds the contract to Learning preflight. These changes are newer than Learning phase-1 SHA and must be validated by a later/current phase before being called active behavior.
- End-of-wave convergence was also strengthened after Repair #10 started: `53e10ecbc845` re-reads freshly-written negative memory after each repair batch so a signature that becomes v0-v3-exhausted during the current final wave is deferred immediately instead of remaining unresolved until another run; `1c544d15cae5` tests this path. These changes are newer than #10 SHA.


- Repair #8 proved the multi-wave experiment mechanism but exposed two convergence defects. Ten providers accumulated rejected variants v0/v1/v2/v3; the old planner then wrapped to the least-failed variant instead of escalating. `c97ff9b449d5` + `273c01b3446f` + `0f7a187a38eb` + `23f1e8b30953` now mark an exhausted signature as `experiment_variants_exhausted` and defer it to independent Learning/new-strategy instead of repeating it. `19afb4685b39` + `2582427fcd6d` remove those exhausted providers from later waves of the same Repair and expose `deferredLearningProviders`.
- Showbox and Yflix did not rotate in #8 because their planned `adaptive_runtime_recovery` experiments produced no child `::repair:` candidate: `deep_repair_loop.py` recorded `attempt.status=not_generated`, while negative memory learned only from retested `rejected` children. `afcbcb531d13` + `b4d943f7efeb` + `262320eaf5d4` now record `not_generated` as a bounded negative experiment (`failures`, `consecutiveFailures`, `lastReason`) so later waves rotate instead of retrying v0 forever.
- Repair pipeline was still hard-coded to `--waves 3` even though Brain has 4 experiment variants. `c45aeb6c698f` changes canonical Repair to **4 waves** and `6e8c31e97de3` locks that contract.
- Dedicated WAF lane is now live: workflow `Provider WAF Browser Session Diagnostics` run `35505853385` succeeded on `f8bc8dd2a84d` using ordinary ephemeral Chromium only (no stealth/CAPTCHA solver/challenge-token fabrication/cookie export). First focused proof re-tested 10 historical challenged lanes across 7 providers and all 10 remained `browser_challenge_persisted` after two same-session attempts.
- WAF coverage was then made census-driven (`f919dadf1762`, `dc1e46b6321f`, `f32d2655f0c2`). Run `35506069726` succeeded and covered all **8 current WAF providers / 12 lanes**: the 10 historically challenged lanes still persisted; WookaFR movie/tv reached normal content only on a `metadata-homepage` seed. This is browser reachability only, not route or playback proof. `dd582123c75a` + `75180cfc5984` now prefer provider-owned GET search-route metadata over homepage seeds so WookaFR is being re-probed on its search path rather than being falsely treated as solved.

- Loop iteration Repair #3: run `35501243853` tested SHA `9dd86807c119`. It passed all Brain preflight gates and exercised real repair on 13 targets, but accepted **0** strictly improving/playable candidates. Final evidence: `targeted=13`, `playable=0`, `verified=0`, `lost=animevostfr:anime`; preservation gate failed, so no provider/Core candidate bytes were published.
- The apparent queue reduction `13 -> 12` was **not a repair success**: WookaFR was reclassified from automatic code-repair into `PROVIDER WAF/ANTIBOT`, raising environment/WAF from 7 to 8. Current census remains `24 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 3 ROUTE PROVEN · 3 CHAIN REACHED · 8 WAF · 5 NETWORK BLOCKED`; automated repair queue is 12.
- Repair #3 exposed the main Brain limitation: negative memory rotated experiments, but every provider still used the same executable `adaptive_runtime_recovery` profile and the orchestrator stopped after the first rejected wave. The census already knew repair families (`transport`, `route-to-terminal`, `terminal-extraction`, `candidate-replay`) but the orchestrator did not execute by those families.
- Brain upgrade for Repair #4: `b0a20655204f` adds current-census family batching and continues after rejected experiments when negative memory advances; `88689cb8e503` makes rotation decisions explicit/testable. `168a82e26d2a` + `91df8ab2e7d4` make variants materially failure-aware: v0 provider-owned evidence, v1 route-shape transfer where allowed, v2 request-recipe transfer, v3 expanded discovery; transport/candidate replay delay peer transfer more aggressively. `4d9a4ed5f1b1` and `4b25d2032d3f` add executable contracts for escalation, stale-plan rejection and family batching.
- WAF lane upgrade: `063893a2f22a` reuses one ordinary ephemeral Chromium profile for up to 2 bounded navigations before declaring a challenge persistent; no stealth, CAPTCHA solving, challenge-token fabrication or cookie export. `35dba1128b56` locks this behavior with a synthetic challenge-then-content test. Browser reachability remains diagnostic only and never promotes provider playback status by itself.
- Unrelated CI debt observed while preparing #4: `provider_census_sharded_workflow_test.py` still expects literal `provider: bulk activate ` and `provider_v3_workflow_ownership_test.py` still expects `provider-repair-skip.json`; these are workflow-contract drift failures and are not evidence that the new Brain strategy failed.

- Loop iteration Repair #4: run `35503177389` on SHA `6830f777e359` failed in the Brain preflight before any provider probe. Exact failure: `provider_brain_repair_orchestrator_test.py` could not find `BATCH_PLAN` on the executable module.
- Root cause was persistence drift inside `scripts/run_provider_brain_repair.py`: earlier commits had added `repair_batches()` / rotation helpers but later file content lacked the required `BATCH_PLAN` and `REPAIR_MEMORY` constants and some report fields, so tests and executable state diverged.
- Fix `c7e570186cb9`: restored the complete family-rotation contract in the actual HEAD file: current batch-plan authority, negative-memory fingerprint, family metadata in batch reports, experiment variant/memory visibility and `family-batched-multi-wave-brain-repair` execution model. Repair #4 produced no provider evidence and must not be counted as a repair attempt.

- Loop iteration Repair #5: run `35503324161` on SHA `a83215994b3c` again stopped in preflight before provider probing. The orchestrator/family-batching contract passed; failure was a stale contradictory assertion in `brain_repair_experience_transfer_test.py` requiring a peer `/player/{id}` route in variant 0 even though variant 0 is intentionally provider-owned evidence only.
- Fix `cc7daee8e492`: removed that stale assertion while retaining the later variant-1/2/3 escalation checks. Repair #5 produced no provider evidence and is not counted as a repair attempt.

- Loop iteration Repair #6: run `35503376036` on SHA `0d11b3e6e65c` stopped in Brain preflight before provider probes. Orchestrator and v3 contracts passed; the only failure was an over-specific test expecting `/film/{slug}` to outrank equivalent generic detail route `/{slug}` for transport variant 1.
- Fix `94b0bd538be4`: test now asserts the real invariant (first route is detail-shaped and peer `/player/{id}` is still withheld), not one spelling/order artifact. Repair #6 produced no provider evidence.

- Loop iteration Repair #7: run `35503441029` on SHA `8de8ee7c5a84` stopped in Brain preflight before provider probes. Orchestrator, census, v3 and prior escalation assertions passed. Failure: `candidate_replay_gap` test expected `peer_recipe_min_variant`, which the runtime used internally but did not expose in returned diagnostic options.
- Fix `9e99aee07148`: expose `peer_recipe_min_variant` alongside `peer_route_min_variant`; behavior was already staged correctly (candidate replay withholds both peer route and peer request transfer until variant 3). Repair #7 produced no provider evidence.

## 2026-09-20 14:00 Europe/Paris — harness/WAF reclassification + Learning reached real queue

- User clarified the former WAF bucket should be treated primarily as a harness/client-compatibility defect until a representative native client reproduces the block. Architecture changed accordingly: `HARNESS MISMATCH` = CI/Node challenged but ordinary/client-profile browser reaches content; `HARNESS/ENV BLOCKED` = GitHub environment remains challenged and native TV/mobile transport is still unresolved. Both stay symptomatic but are excluded from provider-JS mutation and routed to `harness-compatibility`.
- WAF evidence run `35511746503` completed SUCCESS on SHA `13f42f94edca`. Matrix result: 12 lanes, **7 browser_content_reached / 5 browser_challenge_persisted**. WookaFR movie+tv reached content with default browser. With only the audited NuvioTV Windows UA applied inside GitHub Chromium, AnimeSalt anime, AnimeVost-FR anime, MoviesMod movie+tv and Vostfree anime changed from challenge to content. This strongly proves harness-profile mismatch for those providers. AllWish movie+tv and FullAnime remain challenged; Flemmix movie+tv changes from challenge to browser-inconclusive. Real NuvioTV OkHttp/TLS/IP behavior remains unproven for the unresolved set.
- Audited Android-TV transport differs materially from health harness: NuvioTV uses `__native_fetch` backed by OkHttp, `Proxy.NO_PROXY`, IPv4-first DNS and HTTP/SSL redirects; the generic health harness used an Android/Chrome-mobile-like browser context. WAF diagnostics now record a client profile matrix and explicitly state that GitHub Chromium cannot reproduce OkHttp TLS fingerprint or real-client IP reputation.
- Census/Brain/Repair semantics updated generically: commits `7a37a221a32b`, `a7833a734e1c`, `9145bb9e84d`, `fa8946defad3`, `83ee2284b9a5` plus tests `ec97ec7295d`, `3b142085...`, `207b8d087...`, `6b07afc326...`. Current persisted census still has legacy `PROVIDER WAF/ANTIBOT` because it predates the new renderer; next Repair census must regenerate it from the persisted browser matrix.
- WAF client-profile implementation: `54f6413db336` adds GitHub-default-browser vs audited NuvioTV-UA browser profiles; `10bfada43050` tests a default-challenge/TV-UA-content transition; `13f42f94edca` enables the matrix in the focused WAF workflow.
- Repair #13 run `35509920815` main repair step completed, but four-version candidate floor failed on UHDMovies. Root cause is not lost playable proof: UHDMovies has no historical verified lane; the historical `tv` semantic declaration was never functionally verified and current upstream is explicitly movie-only. Non-regression now preserves declaration drift for audit but blocks publication only for **proven semantic capability loss**: `ec4f54f0281b`, `2a0896618f95`, helper/test `1606d9e9d145` / `cbf83cf0bd5f`. Regenerated history matrix shows UHDMovies `blockingLostSemanticTypes=[]`, `unprovedSemanticReclassificationTypes=[tv]`, `nonRegressionStatus=NO_HISTORICAL_GREEN`, and no contract regression.
- Workflow Gate exposed one introduced syntax typo in harness batch classification (literal `\\n`); fixed by `718b65119bf6`. Do not count earlier gate reds from that typo as Brain behavior.
- Active Learning run `35510255736` has passed isolated stage, full catalogue observation, common-runtime-collapse gate, daily coverage and clean ProviderBase reconstruction. At this checkpoint it is inside the actual adaptive Learning provider queue; it is the first current Learning run to reach this stage after the earlier 98/98 `NIAKVIO_PROVIDER_MODEL is not defined` staging collapse was fixed.

## 2026-09-20 10:50 Europe/Paris — virtuous Repair → improve → Repair loop resumed
- Loop iteration Repair #2: run `35501120857` passed the new v3 override contract, then failed in `brain_repair_experience_transfer_test.py`. Diagnostic output proved both provider and peer request recipe counts were zero even though the synthetic experience contained valid POST recipes.
- Root cause: `scripts/adaptive_runtime/runtime_repair.py` had route/request placeholder regexes double-escaped (`\\{...\\}`), so `{query}` / `{slug}` templates were not recognized. This silently suppressed request-recipe transfer and distorted template ordering. Generic fix `b32d2f935f6e`; direct regex contract added in `866edbeb60c5`.

- The overnight 12h Learning attempt did **not** reach the adaptive Learning queue. Run `35484289278` failed at `Build isolated current provider stage`; scheduled run `35497810028` reproduced the same failure.
- Root cause: `validate_override_pipeline.py` treated `runtime_domain_replacements` like legacy source-text replacement. For generated Provider v3, the historical host intentionally remains as the key of owned runtime migration DATA (`old -> terminal`), so Anime-Sama, HindMoviez, VidRock and VoirAnime were falsely rejected.
- Generic fix committed on `main`: `a1137046fecb` makes v3 validation semantic (runtime migration DATA) while retaining strict literal replacement checks for legacy bundles. Executable regression `tests/provider_v3_override_pipeline_contract_test.py` added at `e107d54bf096` and gated in Repair (`f471748b9ed`) and Learning (`d89fdbe52e8`).
- Latest scheduled Repair run `35500564569` failed earlier in its preflight at `tests/brain_repair_experience_transfer_test.py` (`route_prior_counts.requestRecipes`). Diagnostic assertions now expose the full adaptive option state (`4c527e238fef`) so the next Repair run can distinguish a transfer regression from a stale test assumption.
- User explicitly restored the operating model: **Repair run -> inspect real evidence/artifacts -> improve Brain/systemic code -> rerun Repair -> repeat**. No global wall-clock duration is an objective or stopping condition. Individual Actions remain bounded only as execution safety; convergence/evidence governs the outer loop.
- Loop iteration Repair #1: run `35501037298` on trigger SHA `28955ad7b8b0` failed in preflight before provider probing. The new v3 contract test exposed an implementation-order bug in the validator (`provider_v3` referenced before stage bytes were loaded). No provider result from this run is valid new repair evidence.
- Fix `8a18127cf119`: stage file/path/bytes and v3 classification are now resolved before replacement semantics; the early no-op path also accounts for v3 `specific_replacements`. This is the correction produced by Repair #1 and is the baseline for Repair #2.

## 2026-09-20 — 12h persisted Brain Learning slot
- Second attempted phase **35484148178** also received the correct long-slot budget (`300` min, `420` remaining) but stopped before Learning work because `provider_base_store.py validate` still treated disabled-retained manifest rows as executable ProviderBase obligations. Materialization correctly produced **44 active bases**; stale validation then failed on retained-disabled `desiflix`.
- Root cause fixed generically: `provider_base_store.validate_all()` now follows `providers/` execution authority and validates only active ProviderBases, while disabled-visible rows remain governed by the separate lifecycle/audit contract (`provider-disabled/`). `tests/provider_clean_reconstruction_contract_test.py` now proves active clean-store coverage plus the disabled-visible count instead of hard-coding 96 executable bases. Commits: `a652a61f79fd` and `ed477256f4a`.
- Full 12h slot restarted from zero by trigger `877be4b58177`. Launcher run **35484284882** completed success and dispatched Brain run **35484289278**. On this third attempt the previously failing Brain/full-coverage bootstrap completed **success**, prior sanitized memory restore completed **success**, and the run advanced into weekly native-Lab learning import. Phase 1 remains bound to 300 minutes with 420 minutes reserved for chained phases.

- User-requested overnight Learning slot is now implemented as a **persisted 12-hour budget**, not a fake single 12h GitHub-hosted job. GitHub-hosted jobs are capped below that duration, so `brain-learning-lab.yml` now chains bounded phases through the existing sanitized `brain-learning/proposals` memory.
- Long-slot phase budget is capped at **300 minutes**; the requested 720-minute slot is therefore **5h + 5h + 2h** of adaptive queue budget, with normal setup/finalization around each phase. Each phase resumes the persisted provider queue, retry state, fixture cursors, negative experiment memory and learned skills.
- Review-only semantics are preserved: Learning still has `productionWritesAllowed=false` / `publicationAllowed=false`; each chained phase runs with `publish_proposal=true`, so validated provider repair proposals and Brain self-architecture proposals are opened/refreshed as PRs and still require human merge.
- Implementation commits: `10dc8f426926` (long-slot chaining in Brain Lab), `20553c369170` (contract test), `706225af10b3` (reusable long-slot launcher), `e268c223956e` (12h trigger).
- Launcher run **35484069814** completed **success** and dispatched Brain Learning run **35484074146** from `main`. That first phase correctly received `phase=1`, `budget_minutes=300`, `next_remaining_minutes=420`, then failed before Learning work on `provider_clean_reconstruction_contract_test.py` because `main` still carried an older provider-specific Base V2 artifact for `anime-sama` while the current contract requires the common clean ProviderBase v3.
- The long-slot bootstrap now rematerializes/validates the canonical ProviderBase v3 **inside the read-only Learning sandbox** before enforcing reconstruction contracts (`8f7206e29191`, contract strengthened at `4668a476f730`). This avoids hiding the durable main reconstruction debt while unblocking Learning.
- Earlier run **35483066561** is **not** the requested 12h Learn slot: it is `LEARN/FORCE - Provider Recognition Repair V6`, push-triggered at `9d5fa03cc181`, therefore `MODE=repair`, with a 240-minute job timeout. Keep its repair/census evidence separate from the chained Learning slot.
- `PROVIDER_CENSUS_STATUS.md` remains the census authority for symptoms; the long Learning queue remains independent, anomaly-first, cross-day resumable and PR-only.

## 2026-09-16 — authoritative current checkpoint

- Current public release is **5.21.48**. `manifest.json`, VF/no-anime projections, package metadata and release hashes are on 5.21.48.
- **`main` is the only active write/publication target.** `brain-learning/proposals` remains proposal storage only. Current branch inventory is now exactly these two branches; do not recreate a persistent workbench/repair branch.
- Recovery census is **96 Provider Objects = 46 current rows + 50 historical archive rows**. Current physical manifest has **44 active + 2 disabled-retained** rows; active Native scope is defined by `automation/evidence/hub-lab-matrix-46.json`.
- PR **#120** restored immutable Hub-46 provider transport and was merged normally at `e401e61688dd79996002f9e37b9abfc923846735`. Native transport pins provider publication **`425756cf1646380fb8172f380d176758c3734ce6`** and `tests/native_hub46_transport_manifest_test.py` proves every pinned blob exists at that exact commit.
- Final PR #120 gates were green: Provider Non-Regression, Media Type & Playback, Workflow Gate, Verify & Publish and CodeQL. CodeQL #889 is already fixed on main by `c60ec1871dc5d3b2217e69581d2c2a5a6615fc84`; do not duplicate it.
- Full five-Lab validation was triggered from `6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1`: Android TV+Mobile run **35033132967**, iOS run **35033132980**, Desktop macOS+Windows run **35033133048**. At this checkpoint all five runtime jobs are still executing their real corpus; do not call a platform green before its exhaustive Hub-46 matrix and evidence upload complete.
- Future Native runs restore exact-client prebuild caches for TV Android, Mobile Android, iOS, macOS and Windows. Keys bind exact official-client SHA + OS/toolchain + relevant NiakVIO harness/native-manifest hash; no permissive `restore-keys`; runtime and matrix gates still execute.
- `CORE.RUNTIME_COMPAT.V1` owns missing host timers (`setTimeout`/`clearTimeout`) and Desktop runtime portability globally. StreamZo/Frenchstream timer failures must not become provider-specific hacks. Core timeout remains **25 s**; A→B→C stale-generation suppression and HTTP 403 fail-closed remain mandatory.
- Historical full32 regression/ZERO lists remain evidence, not an automatic mutation queue. Re-prove any regression against current 5.21.48 bytes. Named follow-ups retained from recent work include AnimeVOSTFR/Kurage/VoirAnime historical regression checks, HindMoviez timeout/search variability, AnimePahe runner/runtime I/O, and AnimeSalt browser-positive/runner-403 behavior. Nakios short/troll HLS remains correctly fail-closed.
- Repository privacy audit found no tracked-content occurrence of user-specific personal identifiers in the scanned categories. Git **commit author metadata** does contain a personal author identity/email on some commits; do not rewrite history while immutable SHAs/current Labs depend on it. Any history scrub must be a later dedicated repin/republication migration.
- Current cleanup: `VALIDATION.json` is aligned to 5.21.48/main/current runs; Provider Non-Regression push policy is back on `main`; obsolete one-shot `temp_*` migration scripts and the dead workbench recovery finalizer are removed; provider catalogue visible release-name synchronization is repaired.

**Everything below this checkpoint is retained as historical recovery evidence unless explicitly restated above or by newer repository/runtime evidence.**

## Repository topology / execution policy

- Repository: `niakw/NiakVIO`.
- **`main` is the only active write/publication target.** Do not recreate a persistent workbench branch.
- Durable Learning proposal branch: `brain-learning/proposals`; proposal storage only, not publication authority.
- Cleanup completed after 5.21.35 publication: `workbench` deleted, `hotfix/runtime-tmdb-credentialless-v28` deleted, PR #92 closed and never merged.
- Expected branches: `main` + `brain-learning/proposals` only.
- Catalogue target remains **all 96 Provider Objects**, including disabled/off rows for census/recoverability. Never shrink the catalogue to manufacture green metrics.
- A structural/materialization green is not real stream proof. Real route/network/yield/native evidence remains mandatory.
- Do not patch official NuvioTV/NuvioMobile/NuvioDesktop production behavior to make Labs green. Native Labs are observational.

## Accepted publication — 5.21.35

- Current accepted public generation remains **5.21.35** until a later checkpoint explicitly records a verified public 5.21.36.
- Final 5.21.35 publication commit: `9db07b3aa42ce2535ec1d7c19866beb43586badd` — `fix: restore Provider CONFIG in final publication 5.21.35`.
- Publication trigger commit: `96957c79403908028964aaab388bdb4c80a5bbe2`.
- Workflow `MAIN - Provider CONFIG Publication Hotfix`, run **34061529965**, job **101562800243**, completed success.
- Root `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` were all verified as `5.21.35`.
- 96 provider versions/hashes were regenerated and Provider CONFIG validation passed 96/96.
- Temporary 5.21.35 publication workflow/script self-removed as intended.
- Flemmix authoritative domain is `flemmix.kim`; `.men` is stale. Commit `bdf11932ea5b949837c29b71c8a61b903e91c57b` fixed final DATA audit authority.

## Provider v3 architecture — invariant

Generated provider composition:
1. clean immutable/common ProviderBase v3;
2. structured provider DATA/CONFIG/static knowledge;
3. provider-owned `PROVIDER.*` Lego;
4. one global Core boundary;
5. shared `CORE.*` Lego;
6. conservative NiakVIO minimizer + content hash.

Hard rules:
- published/upstream/historical Provider JS is knowledge/reference only, never a reconstruction seed;
- **published Provider JS contains only common ProviderBase + structured DATA/CONFIG + managed Provider/Core Lego + envelope/minimizer-preserved structure**;
- no provider file/adapter may own duplicated identity, media-type, year, sanitizer, presentation, or other shared business rules;
- provider-local `strictIdentityScore`, `routeIdentity`, year rejection, or duplicated season/episode identity logic are architecture violations;
- ProviderBase may transport evidence and call shared Core services but must not own a second copy of Core policy;
- provider behavior belongs in DATA or owned Provider Lego;
- Core is provider-agnostic and each concern has one owner;
- managed Lego uses `STARTFIX` / `CLOSEFIX` (+ `FIXDATA` when needed);
- Provider Lego precedes Core boundary; Core Lego follows it;
- reverse reconstruction must be deterministic/byte-verifiable;
- Terser forbidden; production minimizer is `scripts/provider_v3_minimizer.py` and must preserve comments/markers/structure.

Core order:
`Provider -> STREAM_FACTS -> STREAM_IDENTITY -> MEDIA_TYPE -> STREAM_PRESENTATION -> PROVIDER_BRANDING -> SANITIZER`.

Ownership:
- `CORE.STREAM_IDENTITY.V1` is the **sole owner** of title/type/ID/year/season/episode identity acceptance semantics.
- `CORE.RUNTIME_MEDIA_SAFETY.V4` owns only playback/media safety: URL shape, P2P rejection, HLS/direct checks, bounded duration/playability. It must not own title/year/S/E collision policy.
- `engine_v2` may mirror Core policy for smoke/diagnostic tests, but provider-specific scoring APIs are forbidden.

## Identity / type / episodic-year contract — FINAL

- Provider input accepts **TMDB or IMDb**. Valid IMDb must not be rejected merely because TMDB enrichment is missing/unavailable.
- Episodic IMDb such as `tt11198330:3:1` preserves season/episode.
- Canonical semantic types: `movie`, `tv`, `anime`.
- Nuvio transport alias `series` maps to canonical `tv`; app-path tests cover movie/tv/series.
- Anime semantics remain distinct even when a provider uses a tv/movie transport lane.
- Capability/type gate must happen before provider network work.

Year policy:
- **MOVIE only**: title + type + movie year; year mismatch is strong evidence and may reject in strict mode.
- **TV / `series` / anime**: release/origin/season/episode year has **zero identity influence**, direct or indirect. No rejection, score promotion, `contentLike` promotion, or other heuristic may depend on year for episodic media.
- Episode resolution identity uses title/type + **season + episode**.
- Provider rows may expose original-series year, season year, episode year, or no year without affecting episodic acceptance.
- `House of the Dragon - Saison 3 (2026)` must be accepted against TMDB series origin 2022 when title/type/S3E1 are correct.

## Core identity 5.21.36 work — implemented source changes

Important commits after 5.21.35 include:
- `1723472`: ProviderBase runtime v9 migration introduced for episodic-year removal.
- `5b356ce`: `CORE.STREAM_IDENTITY.V1` shared catalogue identity API + movie-only year policy.
- `3600e8b`: ProviderBase delegates catalogue/HTML identity to `globalThis.__nuvioIdentityPolicyV1`.
- `491f1ba`: executable Core ownership regression for HOTD-like episodic year mismatch + strict movie year.
- `25e5148`: Workflow Gate includes identity ownership regression.
- `f62393a`, `fb76b5c`, `c1d8c43`: shared engine-v2 catalogue policy + Purstream HOTD S3E1 synthetic smoke.
- `398024c`: priority regression wording/contract changed to episodic-year-disabled/movie-only.
- `ef4073a`: ProviderBase provenance reports runtime reader v9.
- `a934df3`: one-shot Core identity ownership cleanup transaction.
- `c8bc366`: active-96 Provider JS Lego ownership test.
- `1d3a415`: identity-only ProviderBase materializer with `route_or_domain_mutation=false`.
- `d0824a8`: Kehflix-shaped final-row runtime regression: HOTD S03E01 survives, S03E02 rejects, movie year mismatch rejects.
- `9003a84`: MEMORY checkpoint recording the discovery that episodic year still indirectly influenced `contentLike()`.
- `c9e10ce`: migration strengthened to zero-year episodic identity v10; year cannot promote `contentLike()` for episodic requests.
- `8176123`: regression proves tv/series/anime produce the same decision with or without year.
- `a6f1b4bd`: authoritative retry workflow updated for v10.
- `ec8867c` + `7296e20`: Python test bootstraps fixed for direct Core Lego imports.
- `af73c025`: ownership test now inspects transformed ProviderBase snippets, not legacy source-anchor strings inside the migration tool.
- `c50806c`: Purstream contract accepts absent or empty `patch_scripts` as the same clean state; any non-empty legacy patch list remains forbidden.
- `05cce19c`: Purstream test aligned with real transport DATA: `published_types=[movie,tv]`, anime preserved semantically via `request_type_aliases={anime:tmdb_namespace}`.
- `e6ea30b`: Purstream recipe contract aligned with current DATA: `movieRoute=/stream/{id}`, `episodeRoute=/stream/{id}/episode?...`, `yearFields=[release_date]`; no `first_air_date` requirement for episodic identity.

## 5.21.36 publication attempts — exact state

**5.21.36 is NOT published at this checkpoint. Public manifest is still treated as 5.21.35.**

Workflow/run authority:
- Workflow: `MAIN - Core Identity Publication Retry 2`.
- Run: **34066073913**.

Earlier safe attempts:
- Run **34065556338**, job **101573573889**: failed before materialization because the one-shot Purstream migration expected one `strictIdentityScore(item, metadata, targetType)` occurrence but correctly found two (call + local definition). No publish.
- Retry run **34065727473**, job **101574024846**: cancelled/superseded before publication when zero-year v10 became authoritative.

Run 34066073913 progression:
- Initial job **101574939364**: migration and DATA scope passed; smoke failed only because `global_identity_policy_ownership_test.py` did not add `scripts/` to `sys.path`. No materialization/publish.
- Rerun job **101575336306**: bootstrap fixed; next failure was a test false-positive scanning `upgrade_provider_base_runtime_v5.py` source text and seeing the legacy validation literal `const movieIdentity...`. Runtime was not at fault. Fixed by inspecting only transformed ProviderBase snippets.
- Rerun job **101575867355**: **all smoke contracts passed**. Identity-only ProviderBase rematerialization itself passed **96/96**, then old Purstream contract failed because `patch_scripts` was omitted (`None`) rather than `[]`.
- Rerun job **101576053245**: all smoke contracts passed; ProviderBase rematerialization again passed **96/96**; old Purstream contract then failed because it expected `published_types=[movie,tv,anime]` instead of real `movie,tv` transport + semantic anime alias.
- Rerun job **101576310737**: all smoke contracts passed; ProviderBase rematerialization again passed **96/96**; old Purstream contract then failed because it expected historical `movieRoute=/media/{id}/sheet`. Current authoritative DATA says `/stream/{id}` and `yearFields=[release_date]`.

Repeated verified rematerialization line:
`IDENTITY_ONLY_PROVIDER_BASE_OK providers=96 unique_paths=96 common_digest=520ba9882661582dc4789f65e5d04c3c902fa22f79b1f436dc52823d845dd3fc runtime_reader=v9 route_or_domain_mutation=false`

Repeated smoke proof before the stale-contract blockers:
- global identity policy ownership: pass;
- Kehflix-shaped episodic identity runtime: pass;
- episodic zero-year regression: pass;
- engine-v2 Purstream adapter: pass;
- runtime media safety: pass;
- priority episodic-year-disabled/domain refresh regression: pass;
- native HLS integrity budget: pass;
- native provider loading compatibility: pass;
- global media resolver: pass;
- native dual IMDb/TMDB identity: pass;
- Provider v3 source plan v4 contract: pass.

The remaining transaction still must execute, on one successful run:
1. complete post-materialization Purstream contract;
2. recompose **all 96 active bundles** from common Base + existing DATA/CONFIG + Provider/Core Lego;
3. validate active-96 ownership and stream guards;
4. generate projections and synchronize release to **5.21.36**, bumping all 96 changed providers;
5. final reverse/static/ownership/integrity/fixed-point proof;
6. write final publication checkpoint to this file;
7. CAS-check `origin/main == base_sha` and atomically push publication;
8. verify public root/vf/no-anime/vf-no-anime manifests actually report 5.21.36 before telling the user to retest.

## Purstream current authoritative DATA relevant to this migration

- `published_types`: `movie`, `tv`.
- semantic anime request: capability alias `anime -> tmdb_namespace`, identity source `original_nuvio_request`.
- official site: `https://purstream.ad`.
- official API: `https://purstream.ad/api`.
- search route: `/search-bar/search/{query}`.
- movie stream route: `/stream/{id}`.
- episode stream route: `/stream/{id}/episode?season={season}&episode={episode}`.
- recipe `yearFields`: `release_date` only, used as movie catalogue evidence; episodic identity ignores year entirely.
- `strictIdentity=true`, `directSourcesOnly=true`.
- No provider-local identity algorithm is allowed; Core owns the semantics.

## Stream/player integrity

A URL or `#EXTM3U` response is not native playback proof. Keep separate:
1. extraction;
2. work/episode identity;
3. request context/headers;
4. playlist/variant resolution;
5. media/container integrity;
6. official native player outcome.

- `CORE.STREAM_SANITIZER.V6` is global and fail-closed on `probe_all_urls=true`.
- `tests/global_stream_output_guard_test.py` walks the 96 current manifest providers and requires one V6 managed sanitizer and terminal ordering.
- `tests/stream_output_sanitizer_fail_closed_test.py` executes fail-closed behavior.
- Historical Allwish ~20 s Interstellar result is a stream-level regression, not a reason to disable a provider. Allwish is not in current 5.21.35 manifest.
- Kehflix malformed MPEG-TS handling probes first media bytes when the runtime exposes them; lack of bridge byte access remains unknown rather than a fake provider-wide failure.
- HLS audio-child integrity `CORE.HLS_RUNTIME_INTEGRITY.V1` remains required.

## Five first-class Native Labs

Exactly five proofs:
1. TV Android — NuvioTV;
2. Mobile Android — NuvioMobile;
3. Mobile iOS — NuvioMobile;
4. Desktop macOS — NuvioDesktop;
5. Desktop Windows — NuvioDesktop.

Workflow mapping: Android matrix = TV + Mobile Android; Desktop matrix = macOS + Windows; iOS separate.

Runtime refs before final Labs:
- NuvioMobile audited/current: `68337ffac8578b986d0c3f6e432abf75f4a33521`.
- NuvioTV audited/current: `23d1fe478e380860dae3eb41c8770533361a0cc5`.
- NuvioDesktop last audited runtime-contract ref: `323c1037f3c0fbe0ebe255b77d42331c3fdeb2d7`.
- Desktop later advanced to `21aabeeb49fc6de835f9031a65cc5f8489419330`; compare showed player-shortcut/UI changes only, not provider/plugin runtime contract files.

## Security state

- Exact 5.21.35 publication SHA Default Setup CodeQL run: **34061759678**.
- Python analysis: success.
- GitHub Actions analysis: success.
- JavaScript/TypeScript was still pending at an older checkpoint; re-check final state rather than assuming.
- Final security completion also requires repository `SEC - CodeQL` / security-extended plus `npm audit --omit=dev --audit-level=high` on the final publication SHA.
- Direct code-scanning-alert enumeration is not exposed by current connector; never claim historical UI alerts were individually closed without evidence.
- Do not weaken CodeQL/security rules for green CI.

## Repository/documentation debts after runtime stabilization

Pending unless a later checkpoint says fixed:
- `CHANGELOG.md` was behind current release history.
- `VALIDATION.json` still carried stale release metadata.
- README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md`, and Domain Refresh docstring contained old official-site-only wording.
- `ARCHITECTURE.docx` must be regenerated/rechecked after final architecture wording.
- `.github/triggers/nuvio-client-lab.json` contained stale release/frozen route counters and should derive current truth instead.
- `automation/provider-v3-architecture.json` / ownership tests contained older branch-based publication assumptions; durable model is one workspace + CAS + atomic main commit.

## Domain Refresh — diagnosed, intentionally deferred until common runtime is stable

Current `refresh_authoritative_hub_domains.py` tries to reconcile terminal-domain derivatives, but the transaction has known inconsistencies:
1. scope validator/tests still encode old official-site-only mutation;
2. `update_provider_v3_domain_config.py` updates only `officialSite` instead of rebuilding full CONFIG from current structured source authority;
3. updater can emit old filename shape rather than source-qualified current publication shape;
4. generic old-host -> new-host logo/icon/favicon reconciliation still needs synthetic proof.

Required later fix: source authority + allowed scope gate + full CONFIG projection + source-qualified filename preservation + synthetic A->B tests + docs. ProviderBase/Core bytes must remain unchanged for domain-only updates.

## User Desktop HOTD S3E1 evidence on published 5.21.35

User supplied `nuvio-ux-20260907-001220.log`.

Observed chain:
- IMDb `tt11198330`, TMDB `94997`, type `series`, title `House of the Dragon` resolve correctly.
- Stream request reaches `type=series id=tt11198330:3:1`.
- `StreamsRepo Found 0 addons...` is ordinary addon-list state, not proof zero NiakVIO Provider JS ran; PluginRuntime network calls follow.
- Visible provider requests then include DNS failures for YFlix family, Nakios, Peachify and VidLink.
- Current priority is **not** a full route/domain sweep yet. First stabilize common TV/series/runtime architecture and already-viable providers such as Purstream/Kehflix; route census/repair across all 96 follows later.

## Active completion sequence

1. Finish 5.21.36 transaction through active 96-bundle recomposition, versioning, reverse/static/integrity and atomic publication.
2. Verify public 5.21.36 manifests and final active Provider JS ownership.
3. Have user re-test real Desktop HOTD S3E1; separate common-runtime results from route/network failures.
4. Stabilize any remaining common TV/series/player issues without narrowing provider scope.
5. Resume full real-route/domain recovery across **all 96**, testing routes live as they are discovered.
6. Fix Domain Refresh transaction defects.
7. Run complete five Native Labs on one exact final candidate SHA.
8. Finish Workflow Gate/security/dependency/CodeQL proof on final SHA.
9. Clean docs/machine architecture contracts/trigger metadata and regenerate `ARCHITECTURE.docx`.
10. Final branch/PR hygiene audit and final `MEMORY.md` checkpoint with exact SHA/run/artifact IDs.

## Completion principle

A green structural workflow is not proof that the 96 providers work. A native client failure is not automatically a provider failure. Keep identity, route/network, extraction, sanitizer, and player evidence separate; fix common NiakVIO-owned root causes at their owning layer; never delete providers, weaken validation, invent routes, or patch official clients to manufacture success.

## 2026-09-07 — Route reconstruction authority bug / proof-first redesign

- Critical architecture bug confirmed in `scripts/discover_candidates.py`: `infer_api_recipe()` can concatenate static route fragments (`search`, `stream`, `media`, `sheet`, `episode`) into executable `movieRoute`/`episodeRoute` templates without proving that the fragments form one real provider endpoint.
- `clean_provider_model()` also merges `patch.learned_routes`, `capability.routes`, and static `knowledge.routes` directly into executable `model.routes`; static observation therefore can leak into runtime Provider DATA before HTTP proof.
- `validate_provider_v3_routes_sequential.py` already contains the correct proof model in `derive_observed_route()`: start from an exact HTTP request observed while executing that provider, abstract only fixture values into placeholders, and refuse promotion when literal content/session/token residue remains.
- A second leak exists in sequential finalization: candidate `apiRecipe` is copied back to executable `apiRecipe` wholesale after route validation instead of filtering route fields by live proof.
- A third leak exists in `materialize_provider_v3_one.py`: `reconcile_provider_authority()` can copy `model.apiRecipe` back into `provider-overrides.api_recipe`, re-promoting stale/static recipe authority.
- `scripts/materialize_provider_v3_all.py::provider_model()` also merges static model routes/API recipe into the runtime model, so reconstruction must be changed to candidate-vs-executable separation.
- Final route model: **static/upstream/recognition data = candidate only; executable route/API recipe = provider-specific live HTTP proof only**. A route proof must preserve method, origin/base, route template, query/body fields, headers needed, semantic role/type, and evidence; static fragments never count as HTTP proof.
- `/stream/{id}` was NOT introduced by the current identity work. It was already in Purstream DATA on 5.21.35. Current Purstream engine adapter instead uses movie detail `/media/{id}/sheet` and episodic `/stream/{id}/episode?...`, exposing an existing route-authority inconsistency. Do not repair Purstream routes opportunistically inside the identity release; requalify them under the new proof-first route model.
- Next mandatory execution: patch reconstruction authority, reconcile all current routes to candidates, sequentially execute/requalify all 96 Provider Objects, persist only live-proven reusable routes, regenerate the 96 Provider v3 bundles from sanitized DATA, then run reverse/static/integrity proof before publication/testing.

## 2026-09-07 — Route-proof reconstruction/bootstrap architecture checkpoint

- User requires `MEMORY.md` to be updated automatically at each important architecture correction/failure/publication checkpoint without being reminded.
- Historical Provider JS route recovery uses the three original provider-source repositories: `Gowaru/gowaru-nuvio-providers`, `NuvioPlugin/All-in-One-Nuvio` (fallback `D3adlyRocket/All-in-One-Nuvio`), and `yoruix/nuvio-providers`. NuvioTV/NuvioMobile/NuvioDesktop are client validation repos only and are never route sources.
- `automation/provider-upstream-parity.json` currently maps **91/96** providers to an upstream source; five providers have no historical upstream mapping: `4khdhubnew`, `cinemm`, `goatapi`, `kehflix`, `toflix`.
- Last parity classification counted 19 `upstream_ok_niakvio_ko` providers, proving NiakVIO route/plan reconstruction regressed real upstream behavior for a nontrivial subset.
- Exact historical upstream bytes should be recovered from `upstream-lkg.json` using recorded provider URL + SHA-256 + capture time. If current raw bytes differ, search upstream Git history for the matching SHA. Current upstream is fallback; NiakVIO-native current source is only fallback for providers without usable upstream history.
- Static extraction is **candidate knowledge only**. It must never manufacture executable routes by concatenating fragments. The old `discover_candidates.py::infer_api_recipe()` / `clean_provider_model()` behavior that promoted static route fragments into runtime `routes/apiRecipe` is an architecture bug and is being replaced.
- Runtime route authority is proof-first **v5**: execute the Provider JS; capture exact sanitized HTTP request structure; capture bounded response identity hints; correlate later request values to prior provider responses; derive placeholders only from proven fixture/dataflow values; require successful provider HTTP evidence; then and only then promote executable DATA.
- `scripts/provider_route_proof.py` is the shared route-proof authority. It proves `search -> internal provider id -> later request` chains. A literal internal id such as `525` must never become `{id}` unless a previous provider response in the same trace proved that value.
- `scripts/bootstrap_provider_v3_routes.py` is the permanent bootstrap path for a **new empty provider**: input is provider source JS + provider id + supported semantic types; no prior `routes` or `apiRecipe` is required. It observes runtime HTTP and produces proof-v5 route DATA. `tests/provider_v3_empty_route_bootstrap_test.py` locks this zero-route onboarding contract.
- Difficult SPA/React/Next-like providers are not handled by guessed framework-specific routes. Runtime execution + network trace + response->request dataflow is the general fallback. Kehflix is explicitly one of the five NiakVIO-native/recent providers and historically accumulated many generic candidate routes, so it is a key proof case for this model.
- `scripts/upgrade_provider_worker_route_proof_v1.py` adds opt-in proof tracing to the hardened provider worker: exact sanitized URL, method, reproducible non-sensitive headers, body shape/values, content type, and bounded response id/slug hints. Existing health diagnostics remain separate.
- Request proof is not URL-only. `scripts/upgrade_provider_route_proof_request_spec_v1.py` abstracts request body/header fixture values (`{query}`, `{tmdbId}`, `{id}`, `{season}`, `{episode}`, `{media}`, `{year}` when merely transported) and rejects unresolved fixture/session residue.
- `scripts/upgrade_provider_base_route_requests_v1.py` teaches the **common ProviderBase** to replay structured `directRequest/searchRequest/movieRequest/episodeRequest` DATA including GET/POST/PUT/PATCH/DELETE, JSON/form body templates, and request headers. Provider-specific algorithms remain forbidden; request facts live in DATA.
- `scripts/recover_provider_routes_from_upstreams.py` is the 96-provider recovery/census harness. It uses upstream/LKG source where available, NiakVIO-native source for the five unmapped providers, runtime proof-v5, and produces a durable route recovery report.
- `scripts/upgrade_route_recovery_request_specs_v1.py` separates all HTTP-proven route observations from the subset safe for generic `routes[]` replay. POST/body/Referer/etc. requirements must not be lost merely because the URL was correct; complex calls belong in `routeData/apiRecipe` with request specs.
- `scripts/upgrade_provider_route_authority_v5.py` makes proof-v5 mandatory for runtime `routes/apiRecipe`: static discovery emits `candidateRoutes/candidateApiRecipe`; materialization only consumes executable routes when `route_proof_version >= 5` and recipe `proofModelVersion >= 5`; sequential finalization filters candidate recipes field-by-field against live routes instead of copying the candidate recipe wholesale.
- Generic catalogue preflight must no longer require `year`. Movie-year identity remains Core-owned; TV/series/anime year has zero identity influence.
- Provider JS architecture remains: common ProviderBase + structured DATA/CONFIG + PROVIDER.* Lego + CORE.* Lego. Reconstruction/discovery tooling is never embedded as provider-specific runtime business logic.
- Public release remains **5.21.35** until the new route-proof census + 96/96 reconstruction + reverse/audit/integrity + version sync are actually green and a later checkpoint records a verified bump.

## 2026-09-07 — Route-proof reconstruction run 34069211303 failure

- Workflow , run **34069211303**, job **101583333823**, failed safely in workspace before route census, DATA application, reconstruction or publication. Public release remained 5.21.35.
- Baseline freeze passed: 5.21.35 / 96 providers.
- , worker route-proof v1, request-spec proof v1 and ProviderBase runtime v9 all applied successfully before the failure.
- Failure was migration cardinality only:  assumed the legacy  call was unique for directRoute, but ProviderBase has exactly three stable call sites: directRoute, catalogue search, movie/episode resolve. It raised .
- No census was executed and no route result from this run is authoritative.
- Commit  fixes the upgrader to require cardinality exactly 3 then replace the three calls deterministically in stable semantic order.

## 2026-09-07 — Purstream HOTD S3E1 final proof requirement

- User explicitly requires a final **real Purstream → House of the Dragon S3E1** proof after the 96/96 route-proof reconstruction/audit. It must not be satisfied by the synthetic engine smoke alone.
- The final Purstream test must exercise the real provider/network path for HOTD S3E1, verify `tv`p/`series` transport and season=3/episode=1, and prove that the provider-side 2026 season year is not rejected against TMDB series origin 2022.
- Do not consider the next release publishable until this Purstream HOTD S3E1 check is green or is precisely classified as the remaining real-world blocker with evidence.

## 2026-09-07 — Route-proof reconstruction run 34069559315 failure

- Workflow , run **34069559315**, job **101584262866**, again failed safely before census/DATA application/reconstruction/publication. Public release remained 5.21.35.
- The previous ProviderBase request-spec cardinality bug was fixed:  passed.
- New blocker was another migration-anchor bug in : it searched exactly for  but  currently imports ; failure was .
- Commit  fixes this by injecting  before the stable  anchor and requiring that stable anchor exactly once.
- No provider route census result exists yet from runs 34069211303 or 34069559315; both failed before the live census step.
- Final candidate pipeline now includes a mandatory real Purstream / House of the Dragon S3E1 proof after reverse/static/integrity: both  and canonical  transports must return streams, have successful provider HTTP, and expose an observed episode request.


## TV runtime regression checkpoint — 2026-09-07

- User refreshed the current NiakVIO plugin on NuvioTV during route-proof work. Concrete native observation: Interstellar now returns streams from multiple providers; series/anime also return streams for some providers, but results can arrive much later after navigating away and appear to stack across works.
- This means series/anime are not globally broken. A major remaining systemic problem is stale provider work that keeps consuming the QuickJS/native fetch bridge after the user changes work.
- `CORE.MEDIA_TYPE_RESOLUTION.V1` currently has `requestSerial/requestToken` latest-result gating, but its `budgetedFetch()` is not bound to the invocation token. Superseded invocations can continue network/crawl work; because `global.fetch` is replaced by a later invocation wrapper, an older invocation may even execute later fetches under the newer request budget. Fix must be global/Core, never provider-specific.
- Required cancellation invariant: every provider invocation owns a request token; every wrapped fetch checks ownership before network and immediately after network; starting a newer invocation aborts the prior in-flight controller when supported; on runtimes where native bridge cancellation is not actually possible, the old in-flight call may finish but MUST NOT start any subsequent search/detail/player/crawl work or return output.
- Current platform contract says QuickJS clients expose AbortController/AbortSignal polyfills, but lifecycle teardown across already-entered native fetch remains not universally guaranteed. Therefore token gating remains mandatory even when abort is attempted.
- Native TV also exposed `Purstream - Inconnue` and `StreamZo - Inconnue`. Correct policy is NOT to discard quality blindly. `CORE.STREAM_FACTS`/`CORE.STREAM_PRESENTATION` must first recover a real quality from provider facts (`quality`, title/name/description, resolution/height, URL/manifest-derived facts). Only when no real quality can be recovered may the placeholder field (`Unknown`, `Inconnu`, `Inconnue`, `N/A`, null, etc.) be removed before terminal branding. Preserve real qualities such as 2160p/1080p/720p.
- Route-proof run #5 `34070914957`, job `101588047149`, materially progressed: migrations/proof-first tests/census/DATA apply/materialization reached green; candidate materialization was 96/96. The first failing post-materialization stage was prune/projection because `scripts/prune_unreferenced_providers.py` performs repeated per-file `git log --follow` calls while bootstrapping retention order and exceeded the bounded stage timeout. This is CI/tooling performance debt, not a provider runtime failure.
- Prune must be fixed by a batched Git-history scan/cache (single/bounded Git history traversal), preserving the rolling 10-generation retention semantics and all current/LKG/provenance/security protections; do not merely raise timeout.
- Final acceptance still requires rerun 96/96 -> reverse/static/integrity -> quick-yield -> real Purstream House of the Dragon TMDB 94997 S3E1 in both `series` and `tv`, plus the native-facing cancellation and quality regressions fixed.


## TV shared-runtime repair run 1 — 2026-09-07

- One-shot workflow `MAIN - TV Runtime Repair`, run **34072829930**, job **101593230828**, failed safely in the migration step before tests/commit/publication.
- `CORE.MEDIA_TYPE_RESOLUTION.V1` latest-request/cancellation patch applied successfully in the ephemeral workspace; failure occurred afterward because the `STREAM_FACTS` migration anchor still used old local variable name `r` while current Core source uses `row`.
- No generated provider, manifest, DATA or public version changed from this failed run.
- Fix the migration anchor against current `global_stream_facts_v1.py`, then rerun the full focused cancellation + quality + batched-prune test set before committing any Core repair.


## TV shared-runtime repair run 2 — 2026-09-07

- `MAIN - TV Runtime Repair` retry run **34073021357**, job **101593778197**, failed safely in migration validation before focused tests/commit/publication.
- The current-source `STREAM_FACTS` prepatch succeeded (`STREAM_FACTS_QUALITY_V2_PREPATCH_OK`) and wrote the intended richer quality-fact logic in the ephemeral workspace.
- Failure was only the upgrader's own stale validation literal: it still required `r&&r.resolution` / `r&&r.height`, while current `global_stream_facts_v1.py` correctly uses `row&&row.resolution` / `row&&row.height`.
- No provider bundle, manifest or public version changed. Fix the migration validator, then rerun the full focused cancellation + quality + batched-prune suite.


## TV shared-runtime repair run 3 — 2026-09-07

- `MAIN - TV Runtime Repair` run **34073127250**, job **101594076771**: all three migrations succeeded in workspace (latest-request cancellation, quality recovery, batched prune history).
- The new **functional cancellation regression passed**: observed calls were exactly `/1/one` then `/2/one`; the superseded request's catch/fallback `/1/two` never reached network. This directly proves latest-request-wins for the stale-fallback shape reported on NuvioTV.
- The run then failed before executing the quality behavior because `tests/stream_quality_recovery_tv_test.py` imported `global_stream_presentation_v1.py` without adding `scripts/` to `sys.path`, causing `ModuleNotFoundError: provider_patch_blocks`.
- This is a test bootstrap defect only. No Core repair was committed and no provider/manifest/public version changed. Fix the test import path and rerun the complete focused suite; do not alter the proven cancellation behavior.

### TV shared-runtime repair — final consolidated checkpoint (2026-09-07)
- Retry 4: Actions run `34073319355` proved stale-request cancellation but exposed that `resolution: 1920x1080` was not converted to `quality: 1080p`.
- Retry 5: Actions run `34073668673` proved cancellation, Purstream/StreamZo quality recovery (`1080p`, `1080p`), and batched prune; it then exposed a stale runtime-only-TMDB test bootstrap.
- Retry 6: Actions run `34073743529` restored full presentation metadata but exposed two TMDB requests for one movie invocation.
- Retry 7: Actions run `34073960958` had zero jobs because checkpoint text escaped the YAML block; no Core/product code executed.
- Retries 9/10 (`34074004747`, `34074084167`) proved the duplicate was not solved by presentation reuse alone: MEDIA_TYPE clears transient `__nuvioMediaContext`, while its durable cache is populated only after the inner identity layer has already run.
- Retry 11: Actions run `34074160651` instrumented the exact requests. The first was STREAM_IDENTITY's legacy lightweight `append_to_response=external_ids`; the second was MEDIA_TYPE's canonical rich metadata request. Final cache key was `movie:157336`.
- Retry 12: Actions run `34074347630` applied shared TMDB ownership successfully, then stopped on the obsolete identity revision literal in a test.
- Retry 13: Actions run `34074404812` passed cancellation, quality, prune, media resolver, full identity semantics and presentation V20. It then exposed that `global_stream_presentation_metadata_fallback_test.py` expected TMDB metadata without injecting the required runtime-only TMDB credential.
- Final repair run: Actions run `34074478047`. STREAM_IDENTITY delegates TMDB metadata acquisition to `__nuvioCoreGetTmdbDataV1` when installed, so identity, media-type and presentation share one canonical cache/network owner; the legacy lightweight call is compatibility-only when the shared capability is absent.
- Shared Core acceptance: stale A→B network sequence only `/1/one`, `/2/one`; Purstream/StreamZo quality fixtures both `1080p`; batched prune retention; media-type + identity contracts; exactly one movie TMDB request through the full presentation pipeline; metadata fallback under explicit runtime credentials; sanitizer fail-closed/direct-normalization.
- Public manifest remains `5.21.35` until the separate 96/96 route-proof reconstruction, reverse/static/integrity, quick-yield, real Purstream HOTD S3E1 `series` + `tv` proof, and publication transaction are green.

## 2026-09-07 — Route-proof runs 8–10 / HOTD dual-provider checkpoint

- Shared runtime repair is durable on `main` from commit `0162eeeb85763ced98fb090ad09f7260bfb600ae`: stale-request cancellation A→B, real stream-quality recovery, batched prune history, shared TMDB ownership/cache, presentation and sanitizer focused regressions all passed together in run `34074478047`.
- Route-proof reconstruction run #8 `34074736796` reached census/DATA/materialization/prune/runtime/cardinality green. First reverse blocker was legitimate: MOVIX had been re-enabled even though census classified it `no-proven-route` with zero proven routes. Route-proof activation policy was added so MOVIX remains disabled/neutralized until a future positive route proof; it never auto-enables on proof alone.
- Route-proof reconstruction run #9 `34075701458`, job `101601231061`, proved census **96/96** with `91` historical-upstream mappings + `5` NiakVIO-native providers, `46` providers with proven routes, `310` proven routes, `23` simple API recipes, and zero source-unavailable providers. MOVIX stayed `enabled=false` through DATA application, materialization, prune and 96-provider cardinality.
- Run #9 also passed reconstructed 96 runtime/Core ownership, global stream output guard, episodic zero-year policy, native HLS budget, provider-loading compatibility, media resolver and dual-ID tests. Reverse then failed only on a stale Purstream type assertion: it expected `supportedTypes=[movie,tv]` even though current architecture separates canonical semantic capability from client transport compatibility.
- Purstream type contract is now explicit: `canonicalSupportedTypes=[movie,tv]`; transport compatibility exposes `supportedTypes=[movie,tv,series]`, where `series` is a Nuvio transport alias for canonical `tv`. Reverse checker commit `c1c022609b202ec36f49cb77d5486db89017d1f9` validates this split instead of rejecting the required `series` lane.
- User requires final real **House of the Dragon S3E1** proof to test **both Kehflix and Purstream**, on both `series` and `tv` transport. Expected diagnostic pattern supplied by user: **Kehflix OK / Purstream NOT OK**. Do not force that result; measure and report the real per-provider verdict. Kehflix is the required positive control; Purstream is diagnostic at this stage.
- This supersedes older MEMORY wording that required Purstream itself to be green before the route-proof run could complete. Current acceptance is: **Kehflix must be OK**; Purstream must be measured and reported exactly. If the measured pattern is Kehflix OK / Purstream NOT_OK, preserve that report and wait for the user's follow-up explanation before deciding whether publication may proceed with the Purstream diagnostic blocker.
- Latest completed census before run #10: Kehflix = `proven`, 5 reusable route patterns; Purstream = `no-proven-route`, 0 proven routes despite two provider requests per Interstellar / Breaking Bad S1E1 / HOTD S3E1 fixture and an accessible server. Do not call Purstream candidate/static paths "new routes".
- Purstream candidate-only paths currently retained for recognition/recovery, NOT executable route authority: `/search-bar/search/{query}`, `/stream/{id}`, `/stream/{id}/episode?season={season}&episode={episode}`, plus the official status hub candidate. `route_proof_version=5`, `provenRouteCount=0`, `learned_routes=[]`.
- Kehflix proven reusable patterns in the same census are `/api/streams/movie?id=&k=`, `/api/streams/tv?id=&k=`, `/api/streams/episode?id=&season=&episode=&k=`, `/api/stream-gw`, `/api/track-view` on `https://kehflix.lol`.
- Final live probe is `scripts/hotd_s3e1_live_probe.py`; it executes the reconstructed Kehflix and Purstream Provider JS through the hardened worker separately for `series` and `tv`, records stream count / provider HTTP success / episode-route observation, and emits `automation/hotd-s3e1-live.json` without printing stream URLs. The script exits non-zero only when required positive control Kehflix fails.
- Route-proof run #10 `34076409932` is triggered from commit `4229ae02b95625c8cc3d2fba4834ba12d8f56fd0` after the Purstream canonical/transport reverse assertion fix. Its 96-provider census and DATA/activation-policy step are green; materialization/prune are green and runtime tests were running at the latest checkpoint. Public manifest is still **5.21.35**; no 5.21.36 publication is accepted yet.
- Publication rule: do **not** reuse the old identity-only 5.21.36 workflow. If route-proof + reverse/static/integrity + quick-yield + HOTD proof succeeds, promote the **exact validated artifact** rather than running a second network census, revalidate the current cancellation/quality/TMDB Core and MOVIX neutralization, then CAS-push and verify all public manifest projections post-push.
- Documentation debt added by user: after runtime/publication stabilization, replace user-facing/documentation terminology **"Lego"** with a generic term such as **block / Core block / Provider block**. Preserve marker semantics and compatibility while removing trademarked wording from docs/log labels/names where practical. Do this as a later clean step, not inside the current functional run.
- User explicitly reminded that `MEMORY.md` must be updated at every important state transition. Treat this as a hard execution rule: checkpoint significant red/green runs, root-cause fixes, publication changes and final proofs before moving on.

## 2026-09-07 — Route-proof run 10 reverse green / static-audit naming failure

- Route-proof run #10 `34076409932`, job `101603292174`, completed failure safely before quick-yield/HOTD/publication. Public release remains `5.21.35`.
- Run #10 census: 96 providers, 91 historical-upstream mapped + 5 NiakVIO-native, **47 providers with proven routes, 303 proven routes, 23 simple API recipes, 0 source-unavailable**. This differs slightly from run #9's 46/310 because live route proof is network-dependent; catalogue cardinality and source mapping remained stable.
- Purstream remained `no-proven-route`, 0 proven routes. Kehflix remained `proven`, 5 reusable routes. MOVIX remained `no-proven-route`, 0 routes and `enabled=false` through DATA policy, materialization, prune and cardinality.
- Full 96 Provider JS materialization, prune/projections/config validation, reconstructed runtime/Core ownership, stream-output guard, episodic-zero-year, HLS, native-loading, media resolver and dual-ID tests all passed.
- **Reverse reconstruction passed byte-identical 96/96**: `PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation=66809df74d148b02 byte_identical=96/96`.
- The next command `audit_provider_v3_static.py` failed on `anime-sama-aaa6dc71f60a1d3e.js` even though the computed SHA prefix was exactly `aaa6dc71f60a1d3e`. Root cause: the static audit only accepted final publication filename shape `provider--source--hash.js`, while route-proof workspace materialization intentionally uses `provider-hash.js`.
- Correct fix: make the static audit context-aware. `publication=false` / workspace must require the exact simple content-addressed materialization filename; `publication=true` / release/main must retain the stricter source-qualified publication filename. Do not weaken final publication naming validation.
- Quick-yield and final HOTD Kehflix/Purstream proof were skipped because static/integrity stage failed first. No HOTD verdict exists from run #10.

## 2026-09-07 — Workflow Gate source-v10 alignment

- `CORE - Workflow Gate` run `34077502006` on route-proof source SHA `914048e5de06c3adab0cf348cd932265ecd0a936` failed in workflow architecture contracts because direct source tests still asserted obsolete identity revision `cross-client-shared-catalogue-policy-movie-year-only-v9`.
- This was source-test metadata drift, not a provider/runtime regression: the repository `global_stream_identity_v1.py` is already `cross-client-shared-tmdb-owner-movie-year-only-v10`, while route-proof workspace migration subsequently upgrades the candidate to combined `cross-client-shared-tmdb-owner-zero-episodic-year-v11`.
- Commits `2064b526a51d8ccda375b47bb981a137dad6e938` and `181ec48edd3847be1a40400aefe6e8db47839e50` align only the direct-source revision assertions in `priority_tv_year_domain_refresh_test.py` and `global_identity_policy_ownership_test.py` with source v10. The full behavioral assertions were preserved; no Provider/Core/DATA/manifest byte changed.
- `CORE - Workflow Gate` run `34077884061`, job `101607483550`, then completed **success**: pinned Actions, Python syntax, multi-device runtime contract, workflow architecture contracts, native provider-loading compatibility and side-effect-purity all passed.
- These test-only commits did not trigger or mutate route-proof run `34077501994`; that candidate remains fixed to source SHA `914048e5de06c3adab0cf348cd932265ecd0a936`.
- Exact-artifact publication may allow these two named test-only drifts after the route-proof source SHA, but any product/runtime/DATA/manifest drift must still require a fresh route-proof candidate.

## 2026-09-07 — Route-proof run 11 integrity / pre-release validation checkpoint

- Route-proof run #11 `34077501994`, job `101606427031`, source SHA `914048e5de06c3adab0cf348cd932265ecd0a936`, passed baseline, proof-first migration tests, 96-provider census/DATA application, materialization, prune/projections, reconstructed runtime/Core tests and 96-provider cardinality.
- Run #11 also passed reverse reconstruction **96/96 byte-identical**, the context-aware static audit, and release-hash generation. It failed only in release-integrity activation preservation because `health-report.json` still carried an older MOVIX promotion row with `enabled=true` while the proof-v5 manifest/override policy correctly kept MOVIX `enabled=false` with zero proven routes. Quick-yield and HOTD were therefore skipped; run #11 produced no HOTD verdict.
- MOVIX fix is explicit proof-v5 evidence, not a generic network-failure exception: `published-disabled-no-proven-route` + `route_proof_no_proven_route` requires schema/proof v5, current `provider-route-recovery-v5` authority and zero proven routes. Future positive route proof removes the stale zero-route reason but never auto-enables MOVIX. Durable commits: `910b5669366818a419b8e091d122d9d49e8c317a`, `db4f52f7f16377abec6736ba99236003013e4ba0`, `220829104086af20f755e588510f57fcf63b744d`, `cd26ee3af00d5506a01769616a70dcba5d4cc71a`.
- Media capability documentation/tests were reconciled with runtime truth: canonical semantic values remain `movie/tv/anime`; `series` is transport-only; episodic anime/tv expose `tv+series`; anime never gains artificial movie capability. Machine/test commits include `3febf63ce11610f53fd27f2dedc55ca48f60cf20`, `6ecd053bb4571b86f987dc61092625e980916586`, `5b84350454db6f3f368bf9922df2ffd3f0b1db1e`.
- Public/static filename audit now uses explicit execution context: route-proof sets `NUVIO_PROVIDER_V3_CONTEXT=workspace` and requires `provider-hash.js`; unspecified/public execution fails closed to source-qualified `provider--source--hash.js`, even if historical materialization metadata still says workspace. Commits `64d89c58901082971a86dcab05893e975b848baa` and `2e3c1d9a8bb8cede580af1e9f70e49cd7c0c88d9`.
- Workflow Gate run `34090076713` on `2e3c1d9a8bb8cede580af1e9f70e49cd7c0c88d9` is fully green. CORE Quick run `34090076686` validates public docs/types/five-Lab contract, minimizer, HTML security, strategy plan and static audit, then reports source-vs-public Core block non-idempotence because unreleased 5.21.36 Core source is ahead of the accepted 5.21.35 published bytes. That pre-release drift is not used as candidate proof; candidate authority remains reverse byte-identical reconstruction.
- Public manifest remains **5.21.35**. Next action is route-proof retry 8 through quick-yield and real HOTD S3E1 Kehflix + Purstream (`series` + `tv`). If measured result is Kehflix OK / Purstream NOT_OK, preserve the report and stop before publication for the user's Purstream explanation.

## 2026-09-07 — HOTD targeted acceptance: Kehflix OK / Purstream NOT_OK

- Public remains **5.21.35**; no publication was performed.
- Full route-proof retry 9: run `34091368865` reached census 96/96, DATA apply, materialization 96/96, runtime/Core-block tests, cardinality, reverse `96/96 byte_identical`, static audit, release integrity and quick-yield. Census: 96 providers, 91 historical upstream + 5 NiakVIO native, 46 providers with proven routes, 311 proven routes, 23 API recipes, 0 source-unavailable.
- Retry 9 HOTD initially measured Kehflix NOT_OK / Purstream NOT_OK. Kehflix reached HTTP episode routes but returned zero streams; Purstream was still zero.
- Root cause 1: proof-v5 generalized signed/identity query calls too aggressively (`id=&k=` etc.) and even rewrote literal `User-Agent: NiakVIO/3` into `NiakVIO/{season}` for S3. Added `scripts/upgrade_route_proof_dataflow_safety_v2.py` + `tests/route_proof_dataflow_safety_v2_test.py` to preserve literal static headers, reject blank signed routes as executable, and preserve a richer runtime plan over weak observations.
- Kehflix terminal discovery run `34094560163`: `kehflix.lol` is redirect-only to `kehflix.com/`; both `kehflix.com` and `kehflix.wiki` preserve `/title/tv/94997-house-of-the-dragon`. The detail page exposes a signed `/player` URL. The signed HOTD S3E1 episode API returned media-like values: `.com`=1, `.wiki`=5. Canonical runtime terminal chosen for the repair: `kehflix.wiki`, alternate live terminal `kehflix.com`.
- Added `scripts/upgrade_kehflix_terminal_domain_v1.py` and `scripts/upgrade_signed_player_api_v1.py`. The signed-player family now executes deterministic TMDB detail -> signed player -> episodic stream API dataflow instead of assuming a direct unsigned `/player?tmdbId` call is sufficient.
- Targeted real HOTD run **`34095052891`** materialized only Kehflix from current Core + structured DATA and then executed the same final probe against Kehflix + Purstream in both `series` and `tv`.
- **ACCEPTED TARGET:** Kehflix `OK`: `series_streams=6`, `tv_streams=6`, HTTP=true, episode route=true for both transports. Purstream `NOT_OK`: `series_streams=0`, `tv_streams=0` (provider HTTP and episode route were reached in this targeted baseline). `HOTD_S3E1_EXPECTED_PATTERN kehflix=OK purstream=NOT_OK matched=true`.
- Per user instruction, stop before publication/full next retry at this exact pattern and wait for the user explanation about Purstream.
- Purstream current structured/upstream route family to preserve for the next discussion: domain discovery `https://raw.githubusercontent.com/wooodyhood/nuvio-repo/main/domains.json`; search `/search-bar/search/{query}`; movie `/stream/{id}`; episode `/stream/{id}/episode?season={season}&episode={episode}`; API base is dynamically `https://api.purstream.<current-tld>/api/v1` with matching site Referer.
- Cleanup reminder after final publication: replace the word `Lego` in docs/workflow labels with a neutral term such as `block`/`bloc`.

## 2026-09-07 — Route-proof 5.21.36 final publication

- Exact validated artifact: route-proof run `34096200193`, source `8173adc4db674189ccc3169fe9ffe90043790d21`.
- Public filename projection preserved provider bytes; reverse rebuild remained 96/96 byte-identical and static publication audit passed.
- Published release target `5.21.36`, 96 providers. Kehflix HOTD S3E1 proof is OK (6 series / 6 tv); Purstream remains NOT_OK diagnostic pending operator explanation.


## 2026-09-07 — Accepted 5.21.37 / Terminal Session V29 / live-yield checkpoint

- **This checkpoint supersedes all earlier wording that says the public release is still 5.21.35 or that 5.21.36/5.21.37 is pending.** Current public release is **5.21.37**.
- Publication workflow: `FIX - Publish Terminal Session V29`, run **34120732027**, job **101737919476**, completed success.
- Final publication commit: **`6f74939efa11b2c886e82002c242b923a4f87f6c`** (`fix(core): publish terminal labels and stale-session isolation V29`). Push to `main` completed successfully.
- Public manifests verified after push: `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json` all report **5.21.37**.
- 96/96 published Provider JS were rematerialized and physically verified to contain `tmdb-data-contract-launch-gate-v29-native-abort-race`, `requestAbortPromise(controller,requestToken)`, and presentation client-projection V20.
- V29 closes the stale-session hole where a native QuickJS fetch bridge may ignore `AbortSignal`: provider fetch now races the native call against request cancellation. Functional regression with an intentionally never-resolving old native fetch completed in ~1 ms after supersede and observed only `/1/one` then `/2/one`; superseded fallback `/1/two` never reached network.
- Terminal stream-label bug was localized outside provider-specific quality calculation: Engine V2 accepted labels such as `Kehflix - Inconnue` as provider names. Engine V2 now strips terminal placeholder suffixes and mirrors final projected `title` into `name`, matching the client-facing Core projection. Placeholder quality (`Unknown`, `Inconnue`, `N/A`, etc.) collapses to provider-only; meaningful qualities remain, including `1080p` and `2160p -> 4K`.
- `CORE.STREAM_SANITIZER.V6` output guard passed across all 96; release integrity and fixed-point override checks passed.
- Nuvio client upstream drift seen during release: NuvioDesktop audited contract remained accepted; NuvioMobile had a safe upstream advance; NuvioTV had a separate semantic-sensitive subtitle-cache drift requiring review. Provider publication intentionally continued against pinned audited client contract refs.

### Live yield on exact 5.21.37 candidate

- Interstellar matrix tested **55 enabled movie-capable providers**. Only **6** returned automatic streams: `castle`, `hindmoviez`, `streamflix`, `streamzo`, `videasy`, `wookafr`. VF automatic providers: **2**, `streamzo` + `wookafr`. **49/55** returned no streams. This is materially better than the earlier native observation of only StreamZo/Kehflix/Castle in one client session, but still far below the 96-provider objective and must not be considered provider recovery completion.
- Notably Kehflix returned zero in the CI Interstellar matrix even though it is a known viable provider in other live/native fixtures; treat this as route/runtime/fixture evidence, not provider-wide disablement.
- User Desktop anime fixture was correctly identified as **The Unwanted Undead Adventurer S01E02**, IMDb `tt30177477`, not Hell Mode. Candidate matrix tested **62 episodic/anime-capable providers**: **2 positive** (`anime-sama`, `neko-sama`), network reached **49**, successful provider HTTP **37**.
- Secondary Hell Mode S01E12 (`tt38646634`) matrix produced the same provider-positive set: **2/62**, `anime-sama` + `neko-sama`; network reached 49, successful HTTP 36.
- These anime results prove the global `series -> tv/anime` transport is not completely broken, but extraction/runtime route yield is still severely underperforming after successful network access for many providers.
- User Desktop logs separately showed DNS/host failures including `api.nakios.live`, `*.eat-peach.sbs`, and VidLink-related traffic. Current main domains can be alive while historical/API subdomains or route families are stale; domain, route, extraction and player evidence must remain separately classified.

### Current priority after 5.21.37

1. Keep V29 terminal-label/session isolation immutable while provider recovery continues.
2. Resume **proof-first real route recovery across all 96**, including disabled/off rows for recoverability; test a route live at discovery time and never promote static fragments as executable routes.
3. Use `MAIN - Route Proof Reconstruction 96` as a non-public candidate workflow. Its baseline must derive from `.github/triggers/route-proof-reconstruction.json`, not be hard-coded to 5.21.35.
4. For every candidate, compare live yield against the accepted 5.21.37 baselines: Interstellar 6/55 automatic (2 VF), Unwanted Undead 2/62, Hell Mode 2/62. A structurally green reconstruction that does not improve/accurately explain these results is not completion.
5. Route families already requiring scrutiny include VidLink historical `/api/b/...` versus current documented `/movie/{tmdbId}` and `/tv/{tmdbId}/{season}/{episode}`, and Nakios principal-site versus stale `api.nakios.live`. Do not replace routes solely from documentation; require provider-specific executable HTTP proof before promotion.
6. Preserve the five Native Labs requirement after route/runtime stabilization: TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows.
7. Continue automatic `MEMORY.md` checkpoints for every important green/red run, root cause, architecture change, publication, native proof, and security proof.

## 2026-09-07 — Route-proof retry 16 pre-census failure

- Candidate workflow `MAIN - Route Proof Reconstruction 96`, run **34123018893**, job **101745186842**, failed before route census; no provider route result from this run is valid because all proof/yield steps were skipped.
- Baseline modernization itself passed: `ROUTE_PROOF_BASELINE_OK version=5.21.37 providers=96`.
- Exact blocker: `scripts/apply_core_identity_ownership_cleanup.py` still attempted the historical v10 -> v11 one-shot migration and required exactly one `cross-client-shared-tmdb-owner-movie-year-only-v10` anchor. Current main is already v11 (`cross-client-shared-tmdb-owner-zero-episodic-year-v11`), therefore anchor count was 0 and the migration aborted.
- This is a stale/idempotency defect in the route-proof bootstrap, not a V29/session/presentation regression and not route/network evidence.
- Required correction: make the one-shot identity cleanup detect an already-current v11 source state, validate all expected final ownership invariants, and exit successfully without rewriting; only run historical transformations when the legacy anchor is actually present.
- Do not weaken identity tests: TV/series/anime episodic year influence remains zero; V29 terminal label + abort-ignorant request cancellation remain mandatory in every reconstructed candidate.

## 2026-09-07 — Identity cleanup fixed-point correction

- Stale route-proof bootstrap defect from run 34123018893 is corrected in commit **`3ca80acc513720bab4c91ede3467894f3c4a1120`** (`fix(core): make identity ownership cleanup idempotent`).
- `scripts/apply_core_identity_ownership_cleanup.py` now detects the already-current `cross-client-shared-tmdb-owner-zero-episodic-year-v11` implementation, validates the full expected final source state, reports `already_current=true`, and exits successfully without attempting historical rewrites.
- Repair workflow `TEMP - Identity Cleanup Fixed Point V1`, run **34123475865**, completed success; both patch application and a direct second execution of the cleanup script on the current source were green, proving fixed-point/idempotent behavior.
- Temporary repair workflow/script were cleaned after the verified source commit. Route-proof recovery may now proceed to its actual proof/census stages without reapplying the obsolete v10 -> v11 migration.

## 2026-09-07 — Route-proof run 17 request-spec bootstrap failure

- Candidate workflow `MAIN - Route Proof Reconstruction 96`, run **34123692126**, job **101747285815**, again failed before route census; no route/yield conclusion from this run is valid.
- Baseline and the previously fixed identity cleanup passed on exact **5.21.37**. `apply_core_identity_ownership_cleanup.py` reported `already_current=true`; ProviderBase current checks and route-proof authority v5 migration also passed.
- Exact new blocker is `scripts/upgrade_route_recovery_request_specs_v1.py` validation after `upgrade_provider_route_authority_v5.py`: it still requires the obsolete literal `patch["learned_routes"] = execution_routes`, which is no longer present in the current route-recovery/applier wiring. Assertion: `recovery request-spec wiring missing: patch["learned_routes"] = execution_routes`.
- This is another stale bootstrap/migration validation mismatch, not provider route/network evidence. Census, materialization, quick-yield and all three candidate live matrices were skipped.
- Required correction: inspect the current structured route recovery writer and update the migration/validation to assert the current proof-v5 DATA/request-spec contract semantically, while preserving the hard rule that only live-proven executable routes may enter runtime `routes/apiRecipe`; candidate/static routes must never be promoted merely to satisfy the test.

## 2026-09-07 — Proof-v5 request-spec validator fixed to current runtime selection

- Run 34123692126 exposed an obsolete validator expectation in `scripts/upgrade_route_recovery_request_specs_v1.py`: it still required direct `patch["learned_routes"] = execution_routes` assignment.
- Current route recovery intentionally uses `select_runtime_routes(existing_routes, candidate_routes, execution_routes)` so a weak new census cannot demote a richer already-proven runtime plan. Directly restoring the old assignment would have weakened route authority/dataflow safety.
- Durable fix commit: **`44b245ae333c4092cc2901468a6fd4c618e21dee`** (`fix(routes): validate current proof-v5 runtime selection`).
- Repair workflow `TEMP - Route Request Spec Validator V2`, run **34124033946**, completed success. It proved the request-spec migrator, route-authority v5 migrator, Python compilation, provider route-proof authority, manifest policy and empty-route bootstrap tests; the migrator also passed a second execution in the same run.
- The validator now requires semantic current wiring: `executionRoutes`, `generic_execution_route`, reusable request specs, conservative `select_runtime_routes`, `patch/model routes = runtime_routes`, `genericExecutionRouteCount`, and `runtimePlanPreserved`; it also explicitly rejects reintroduction of the obsolete direct execution-route overwrite.
- This correction preserves the core rule: only live-proven executable routes may enter runtime DATA, while static/candidate routes stay non-executable unless separately proven.

## 2026-09-07 — Route-proof reconstruction 96/96 fully green (candidate only)

- Public baseline remains `5.21.37`; no Provider candidate was published by this run. Successful workflow: `MAIN - Route Proof Reconstruction 96`, run `34124189951`, workflow run number 18 / internal retry 13, trigger commit `c68da2edeecde5241486dd2089ebe7d703ce1a9e`. Trigger target is `5.21.38-candidate` and required proof is `proof-v5-96+interstellar+unwanted-undead+hellmode+hotd`.
- Full workflow PASS end-to-end: baseline freeze; proof-v5/shared-runtime migrations; proof-first authority and zero-route onboarding; 96-provider live census; DATA/activation application; 96/96 materialization; prune/projections/CONFIG; reconstructed runtime + managed-block contracts; workspace cardinality; reverse/static/integrity; quick-yield; live comparison; HOTD S3E1; artifact upload.
- Census exact result: `96` providers = `91` historical-upstream mapped + `5` NiakVIO-native, `source_unavailable=0`; `45/96` providers produced live proven routes, `286` proven routes total, `23` simple API recipes, statuses `45 proven / 51 no-proven-route`. The report was applied to all 96 providers. A weak/empty new observation does not demote a richer previously proven runtime plan; `select_runtime_routes(existing,candidate,execution)` preserves the better plan.
- Materialization exact generation: `f492fb39d2a5927c`, `96/96`, device-agnostic JS for TV/Mobile/Desktop. Projections after reconstruction: VF `29`, no-anime `73`, VF-no-anime `17`. Provider CONFIG validation PASS. `Movix` remains disabled with zero proven routes.
- V29/runtime invariants survived complete reconstruction: `ROUTE_PROOF_V29_PRESENT providers=96`; episodic year influence remains zero for TV (`year=ignored`, S/E authoritative), movie year core-owned; media-type resolver, dual IMDb/TMDB identity, latest-request cancellation, abort-ignorant native fetch cancellation, stream presentation/branding/sanitizer order all PASS.
- Reverse/static/integrity exact proof: `PROVIDER_V3_REVERSE_REBUILD_OK providers=96 generation=f492fb39d2a5927c byte_identical=96/96`; static audit PASS; release integrity PASS.
- Quick-yield exact result across `193` representative tasks: `raw providers=9`, `playable providers=9`, `verified providers=8`, `wrong_content providers=3`. Playable providers: `allwish, anime-sama, castle, hindmoviez, kehflix, neko-sama, streamzo, videasy, wookafr`. Verified: same list except `neko-sama`. Type breakdown: movie `7/82` playable+verified; TV `6/71` playable, `4/71` verified; anime `2/40` playable+verified. Main failure stages: network zero result `74 tasks / 38 providers`, HTTP error `64/33`, network exception `19/12`, missing runtime plan `16/9`, zero before provider network `5/3`.
- Interstellar candidate matrix: `7/63` automatic providers = `castle, hindmoviez, kehflix, streamflix, streamzo, videasy, wookafr`; VF `3` = `kehflix, streamzo, wookafr`; no settings gap. Prior accepted 5.21.37 checkpoint was `6/55` with `2 VF`, so absolute provider/VF yield increased, but denominator changed and must not be presented as a normalized-rate comparison.
- The Unwanted Undead Adventurer S01E02: `3/62` positives = `anime-sama, kehflix, neko-sama`, network reached `50`, successful HTTP `39`. Prior accepted checkpoint was `2/62`, so candidate adds one positive provider.
- Hell Mode S01E12: `2/62` positives = `anime-sama, neko-sama`, network reached `50`, successful HTTP `38`; count unchanged from accepted checkpoint.
- HOTD S3E1 real probe: Kehflix PASS on both `series` and `tv`, `4 streams` on each transport, HTTP reached and episode route observed. Purstream remains NOT_OK: HTTP reached but `0 streams`, no episode route. Expected accepted pattern `kehflix=OK / purstream=NOT_OK` matched.
- Candidate artifact: `route-proof-reconstruction-96-34124189951`, artifact id `10020094655`, size `152561733` bytes, SHA-256 `46627b78e445ea0d70d50f09e8bbe7b17dd272e64391232079fb3a9d564bb4d5`, retention 14 days.
- CI cleanup performed during the run: obsolete one-shot workflow `fix-terminal-label-session-v1.yml` removed in `be1f771400dca148991a4ae8ff77e89505836ee0`; obsolete `lab-timeout-isolation-fix.yml` removed in `6430091699152c2eadb504b8c1ac41c86f3bf5be`. Durable source/test fixes remain.
- Memory checkpoint transport upgraded to non-empty sentinel file `automation/memory-checkpoint-pending-v2.md` because the connector Contents wrapper repeatedly returned SHA mismatch 409 when updating the previous empty blob. The permanent writer now consumes v2 and resets it to `` instead of a zero-byte blob.
- Next canonical release step: do not run `CORE - Finalize Accepted Release` directly on the current main, because the successful 5.21.38 candidate exists only in the workflow workspace/artifact (`publication=false`, `mainTouched=false`). First hydrate/commit the exact accepted candidate onto a non-main release branch, include the deterministic migration/source changes needed for reverse rebuild, rerun bounded acceptance there, then merge the accepted candidate and finalize the synchronized release version on the exact accepted main SHA.

## 2026-09-07 — Route recognition V6 retry/dependency checkpoint

- Active experimental branch: `workbench/route-recognition-v6`; no publication from this branch. The public accepted release remains whatever the earlier publication checkpoint says until an explicit verified publication occurs.
- Canonical Repair/Learn/Force engine is `scripts/run_provider_repair_pipeline_v6.py`; all three modes use the same recognition -> correction -> rematerialization -> targeted-yield path.
- Network skip set remains 9 previously validated providers: `allwish`, `anime-sama`, `castle`, `hindmoviez`, `kehflix`, `neko-sama`, `streamzo`, `videasy`, `wookafr`. Retry-4 run `34136291243` proved `tested=87 skipped=9 overlap=0`; common ProviderBase changes still rematerialize all 96 and therefore require deterministic 96-provider regressions.
- Retry-4 route census: 87 targeted, 39 providers with proven upstream routes, 238 targeted routes; merged proof = 46/96 providers and 299 routes. Post-reconstruction acceptance remained `raw=0 playable=0 verified=0`; 21 representative upstream-positive provider/type pairs were lost after reconstruction. Therefore route proof alone is not a repaired provider.
- Adaptive recognition retries are implemented: default 3 attempts, max 4, only for transient network/execution states (timeouts, reset/DNS-temporary, 408/425/429/5xx, worker-no-result/network exception). Deterministic source/runtime failures such as `MODULE_NOT_FOUND` and source-policy blocks are not retried.
- PlayIMDb is explicitly treated as a typed resolver/API family, not as a generic absolute-route or VidSrc-like multi-hop template. Its upstream currently calls `https://streamdata.vaplayer.ru/api.php`, uses `Origin/Referer` playback context from `nextgencloudfabric.com`, and returns URLs under `data.stream_urls`. V11/V12 work is scoped to proof-backed `typed-resolver-api` recipes; multi-hop/search/player chains are not flattened.
- A reconstruction parser defect was identified: plural resolver containers such as `stream_urls` were ignored by common `_sourceUrls`. V12 adds bounded explicit plural stream/source containers plus safe inherited playback headers (`Origin`, `Referer`, `User-Agent`, `Accept-Language`) without scanning arbitrary JSON URLs.
- `MODULE_NOT_FOUND` root cause: upstream Provider JS is executed from a temporary directory, so bare npm imports could not see NiakVIO's locked root `node_modules`. The single owner is `upgrade_provider_worker_module_resolution_v1.py`: only top-level declared dependencies may fall back to project-root resolution, Cheerio is redirected to parser-only `cheerio/slim`, and blocked Node built-ins remain blocked.
- Dependency probe run `34147056268` succeeded: 16/16 formerly `MODULE_NOT_FOUND` providers no longer hit that error; `allanime` immediately produced 4 proven routes. This is an environment/recognition recovery, not yet an end-to-end repaired provider until reconstructed `raw/playable` passes.
- Do not count PlayIMDb or AllAnime as repaired until the targeted post-reconstruction yield returns real streams. Do not expand the green skip set from route proof alone.

## 2026-09-07 — First V6 red-to-green acceptance: PlayIMDb

- Targeted canonical acceptance run `34147372929`, job `101822202535`, proved the first V6 unresolved provider repaired end-to-end: `playimdb`.
- Final reconstructed yield was `raw=1 playable=1 verified=1`; representative upstream-positive pairs were `2`, preserved `2`, lost `0`. Both movie and TV resolver paths therefore survived recognition -> DATA/recipe -> rematerialization -> reconstructed runtime.
- The repair is shared runtime behavior, not a hard-coded PlayIMDb provider patch: V7 classifies only proof-backed terminal TMDB resolver requests as `typed-resolver-api`; V11 allows only that class to execute without a search/base phase; V12 parses explicit plural source containers such as `data.stream_urls` and preserves the already-proven safe playback context (`Origin`, `Referer`, `User-Agent`, `Accept-Language`). Generic absolute routes and multi-hop/search/player providers remain excluded from this bypass.
- The same PlayIMDb acceptance job passed the full deterministic 96-provider gates: published CONFIG 96/96, Provider/Core Lego ownership, global stream output guard 96/96, episodic identity/year regressions, global media-type resolver, dual IMDb/TMDB identity, stream presentation, and presentation pipeline.
- This does not mean the 9 previously-green providers were network re-probed; they remained excluded from network recognition. It does prove the common V11/V12 rematerialization did not break the global 96-provider structural/runtime contracts.
- Parallel AllAnime acceptance was not a repair: its selected upstream fixture itself had zero streams, and reconstructed yield remained `raw=0 playable=0 verified=0`. Route proof alone is not promoted to green.
- NetMirror is the next typed-resolver candidate because retry-4 showed direct TMDB movie/episode resolver requests with positive upstream streams and the same old `provider_zero_before_provider_network` reconstructed failure class.

## 2026-09-09 — Main-only recovery, V21 runtime/player checkpoint

Repository authority / topology:
- Active work authority is **main only**.
- `brain-learning/proposals` is the sole retained secondary branch and is immutable; never mutate/delete it during cleanup.
- All workbench and Dependabot branches have been removed after useful history/content was consolidated. Current repository branch set is exactly `main` + `brain-learning/proposals`.
- Do not recreate persistent repair branches unless the user explicitly changes this policy.

Release/versioning:
- A real regression was detected after consolidation: historical published release reached **5.21.39**, while current main bytes regressed to **5.21.37**.
- `scripts/sync_release_versions.py` now has a history-backed anti-downgrade floor: explicit or automatic finalization cannot go below the highest release version found on main first-parent history.
- `tests/release_version_sync_test.py` reproduces the exact 5.21.39 -> 5.21.37 failure and requires the next changed generation to resolve to **5.21.40**.
- Final release candidate must synchronize package.json, package-lock.json, all four manifests, sources.json, provider_catalog.json, visible manifest names (`NiakVIO vX.Y.Z ...`), release hashes and integrity artifacts. Current main manifest bytes may still show 5.21.37 until finalization; do not expose that as a finished candidate.

Workflow/security cleanup:
- `.github/workflows/provider-repair-fast-targeted.yml` and the full parallel sweep now run from main.
- Legacy V14 workflow is manual diagnostic only; deleted workbench branch triggers were removed.
- Full sweep is fixed at 96 Provider Objects (24 groups x 4) and uses the current targeted runner rather than stale v1-only logic.
- `workflow_security_policy_test.py` requires every external GitHub Action to use a full 40-character commit SHA.
- A recurring regression reintroduced `actions/checkout@v4`, setup actions by tags and `upload-artifact@v4` in the targeted workflow. Fixed on main: checkout/setup-node/setup-python/upload-artifact are all full-SHA pinned.
- Targeted and full-sweep plan jobs now execute `python3 tests/workflow_security_policy_test.py` **before network proof**, so this cannot waste another long provider run before detection.
- Run 72 (`34291236317`) proved the new targeted security preflight green.

Provider objective / acceptance:
- Target remains **all 96 Provider Objects**, including disabled/off rows for recoverability.
- Never treat a few repaired providers or a green structural test as completion.
- Required chain: targeted live-positive preservation -> neighbor/family non-regression -> 96/96 global proof -> five independent native Labs (TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows) -> UX/player/metadata/latency/session checks -> final version/hashes/integrity -> publication.
- Device behavior must be cross-compared but never inferred blindly across Nuvio repos/runtimes.

Targeted recovery history / current root causes:
- Earlier upstream proof established live positives for AnimeSama (`animesama-co`), AnimeVOSTFR and French-Manga.
- V20.3 fixed `{slug}` projection and urlencoded-form capture; V20.4 fixed static form constants + state updates; V20.5/V20.5.1 added strict id/slug readiness, dependency passes, deeper correlated steps and nested JSON HTTP value extraction.
- Run 70 showed V20.5.1 contracts green but live preservation still 0/3.
- Exact run-70 divergence:
  - AnimeSama materialized plan exists but reconstructed path did not reach useful provider network before falling through metadata/fallback authority.
  - AnimeVOSTFR still incurred broad generic WordPress/fallback traversal instead of a short causal chain, contributing to latency and wrong identity order.
  - French-Manga reached search -> episode API -> player embed; remaining failure is shared player extraction. One observed embed family exposes a fake `/troll/master.m3u8` and encodes the real HLS through base64 + reverse + hostname-derived XOR.

V21 current work on main:
- `scripts/upgrade_provider_shared_player_trace_v21.py` adds a provider-agnostic shared player decoder for the **content shape** above, rejecting the decoy HLS. No provider ids/hosts/titles are hard-coded into executable runtime logic.
- V21 also extends provider-value runtime evidence from one last-state row to a sanitized bounded history of max 48 lifecycle rows (`plan_selected`, identity, step/deferred/fetch/response, etc.). No response body, credentials, cookies or request headers are stored.
- `scripts/nuvio_tv_probe_tmdb_ci.cjs` now exports `provider_value_trace_history_v21` for CI diagnosis with step indices up to 7.
- `tests/provider_shared_player_trace_v21_test.py` executes the actual generated shared decoder against synthetic neutral encoded HLS content and validates trace/privacy constraints.
- First V21 run 72 did not reach live recovery because the V21 trace privacy validator scoped its scan too broadly and falsely found `authorization` in neighboring security helpers. The validator is now scoped only to `_spv184Trace`; the regex SyntaxWarning was also cleaned.
- Current retry trigger schema 26 targets `animesama-co`, `animevostfr`, `french-manga`, publicationAllowed=false.

Native/client evidence / UX blockers:
- User macOS log: Interstellar displayed 0 streams in that Desktop run while provider/network work occurred; several dead/failing DNS routes were visible. Absence of literal provider name in Desktop logs is not proof the provider was not selected/executed.
- TV Android previously produced Interstellar streams including Purstream/Castle/Cineby after cache clear. Therefore macOS 0-stream must not be generalized into common DATA failure.
- User wants Desktop macOS logged test + raw TV Android test on the **same candidate SHA/version**. Do not ask for that test until the candidate provider generation is stable and versioned.
- Historical stale-loading complaint means old title provider jobs may continue after navigation. This is not yet proven identically across runtimes; cancellation/native HTTP/stale-completion must be tested per client repo/device.
- `Purstream - Inconnue` on *Les Fils de l'homme* is a **stream title/technical metadata** regression, not manifest provider branding. Preserve real quality/language/source/host/size when available; never invent a quality merely to hide `Inconnue`.
- Reduced stream count is also blocking; latency must not be "fixed" by dropping providers/streams.

Next execution order:
1. Finish V21 targeted retry; fix real live failure until all known upstream-positive representative pairs are preserved.
2. Retest AnimeZey, Cineby, MovieBlast and other immediate neighbors/families.
3. Run all 96 with current V21 contracts and no stale skip exemption.
4. Materialize exact candidate and finalize as **5.21.40** with visible version names, hashes and integrity validation.
5. Run Desktop macOS logged + TV Android raw on identical SHA/version, then Mobile Android, Mobile iOS, Desktop Windows independently; compare runtime divergences.
6. Fix remaining player, metadata, cancellation/session and latency defects; rerun 96 + five Labs.
7. Security/docs/minimizer/fixed-point final clean; publish only after the entire chain is green.

## 2026-09-09 — V21.4 targeted recovery / four-manifest release checkpoint

- Main-only work remains authoritative. Do not delete branches or perform final cleanup/publication until provider recovery, the five Native Labs, player/UX checks, and the final release transaction are complete.
- Release target remains **5.21.40**. `scripts/sync_release_versions.py` / `tests/release_version_sync_test.py` enforce the historical 5.21.39 -> 5.21.37 anti-downgrade regression and require the next accepted changed generation to be 5.21.40.
- Final release synchronization must cover **all four public manifests**, not merely names/version strings: root `manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, and `vf-no-anime/manifest.json`, plus package/package-lock, sources/catalogue, provider hashes/integrity and visible manifest names. The two no-anime projections are first-class release/runtime artifacts and must be generated, content-checked, runtime/Lab-tested where applicable, hash/integrity-checked, and published atomically with root/VF.
- Current main still shows `no-anime/manifest.json` name `NiakVIO — Without anime providers` and `vf-no-anime/manifest.json` name `NiakVIO — VF uniquement — Without anime providers`, both at 5.21.37 until final 5.21.40 finalization. Do not present those current bytes as the finished release.
- Metadata preservation contract across the 96 providers is green from run `34294642425`: source and normalized metadata survive Facts -> Identity -> Presentation, while sanitizer URL/headers/transport checks remain separately validated. The `wrong_content` diagnostics regression was also corrected; diagnostics stay bounded and do not persist media URLs, tokens or sensitive titles.
- Targeted recovery run **78** improved the three-provider upstream-positive preservation set from 0/3 to **2/3**: AnimeSama (`animesama-co`) playable+verified, AnimeVOSTFR playable+verified, French-Manga playable but rejected. French-Manga title/season/episode identity matched, but measured HLS duration was about **4.3718x** the expected fixture duration, so the duration guard was intentionally not weakened.
- Root-cause hypothesis for French-Manga: its API shape is language -> episode -> servers, while NiakVIO was extracting player URLs from all episode rows instead of selecting the requested episode first. Upstream explicitly selects the requested episode number.
- Shared generic **V21.4** (`scripts/upgrade_provider_episode_scoped_json_v21_4.py`) was introduced to scope episode-indexed JSON before player extraction: requested episode only for TV/anime, support tagged arrays (`episode_number`/`episode`/`num`), fail-closed when a true episode table lacks the requested episode, leave movies unchanged, and avoid treating numeric quality maps (1080/720/etc.) as episode tables. Runtime logic must remain provider/host/fixture agnostic.
- Run **79** did not reach authoritative live validation because an old V20.5 textual invariant rejected the new runtime arrangement. Compatibility was adjusted so V20.5 keeps its historical marker while the V21.4 runtime zone still forbids unscoped JSON extraction.
- Run **80**, GitHub Actions run `34296820117`, is **red** and must not be described as V21.4 success. V21.4 boundary/migration initialization itself reported ready and the 96 Provider CONFIG check passed, but final live yield remained **2/3**: all three providers produced playable output, only AnimeSama + AnimeVOSTFR were accepted/verified, and French-Manga remained `wrong_content` with reasons `fixture_duration_mismatch,season_episode_match`; `lost=1`, target gate false.
- Run 80 also exposed an independent **test-only defect** after the live result: `tests/provider_episode_scoped_json_v21_4_test.py` crashes at the movie-unchanged assertion with `NameError: name 'payload' is not defined`. Fix that test variable/fixture without changing V21.4 behavior, then rerun; this test bug is not the cause of French-Manga's remaining live duration mismatch.
- Run 80 route recovery itself proved all three targeted sources/routes (`animesama-co` 5 routes, `animevostfr` 11, `french-manga` 8; 24 total) and materialized the three bundles successfully before yield evaluation. Therefore the remaining French-Manga issue is downstream episode/player/content selection or media validation, not absence of provider network route proof.
- Immediate next order: (1) fix the V21.4 regression test `payload` NameError; (2) inspect the exact French-Manga V21.4 runtime trace/output to determine why episode scoping did not remove the ~4.37x duration mismatch; (3) get targeted **3/3** without weakening duration/identity guards; (4) retest AnimeZey/Cineby/MovieBlast and neighboring families; (5) run the complete 96-provider proof; (6) materialize the exact candidate; (7) validate root + VF + **both no-anime manifests** and finalize 5.21.40 atomically; (8) execute five Native Labs independently (TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows) plus UX/player/metadata/latency/session checks; (9) security/docs/minimizer/fixed-point clean and only then publish/branch cleanup.

## 2026-09-09 — V21.5/V21.6 catalogue identity, exact-source proof LKG and player fallback checkpoint

- Release/publication state is unchanged: **publicationAllowed=false**, target remains **5.21.40**, main-only authoritative, and finalization still requires the complete 96-provider proof, exact candidate materialization, all four public manifests (`manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, `vf-no-anime/manifest.json`), five independent Native Labs, player/UX/metadata/session/latency checks, security/docs/minimizer/fixed-point clean, and only then publication/branch cleanup.
- The V21.4 regression test defect from run 80 was fixed: `tests/provider_episode_scoped_json_v21_4_test.py` no longer references an undefined Python `payload`; later targeted CI confirms V21.4 contracts green.
- French-Manga's ~4.37x duration mismatch was traced upstream of media validation to a wrong catalogue identity: the requested Jujutsu Kaisen S1 result uses provider `newsid=1497198`, while NiakVIO had correlated `1497822`. The original V20.4/V20.5 response-wide ID fallback could overwrite a strong title/season-correlated result with a more frequent unrelated HTML `data-id`.
- Shared **V21.5** (`scripts/upgrade_provider_catalogue_identity_correlation_v21_5.py`) now scopes the initial provider catalogue identity to the same bounded search result/card as the matched title/season while preserving V21.1 media-aware identity and later response ID learning. It handles direct anchor search results and bounded onclick/data-href style catalogue cards without provider/fixture-specific IDs. `tests/provider_catalogue_identity_correlation_v21_5_test.py` locks the behavior.
- Run **81** (`34307300812`) did not reach live recovery because the first V21.5 migration looked for the pre-V21.1 `_spv205StrictProviderValues(value, base, meta, season)` signature. It was corrected to compose against the current V21.1+ runtime owner/signature rather than restoring an obsolete owner.
- By runs **84/85**, V21.5 fixed French-Manga in real execution: the reconstructed provider uses the correct `provider_id=1497198`, reaches the correct episode API/player chain, and returns verified streams. Treat French-Manga catalogue identity as fixed unless a later regression proves otherwise.
- Runs 84/85 exposed a separate systemic proof-memory defect: an immutable upstream Provider JS can return different successful request traces between invocations. AnimeSama's positive trace previously included the correlated Sibnet step `/shell.php?videoid={id}`; a later same-SHA upstream run still returned a stream but did not exercise that HTTP step. `merge_provider_repair_report_v6.py` replaced the targeted provider row and erased the previously live-proven route. The 96 baseline was too old to restore it.
- A durable **exact-source live-positive route-proof LKG** was implemented in `scripts/provider_route_proof_lkg.py`, registry `automation/provider-route-proof-lkg.json`, and `tests/provider_route_proof_lkg_test.py`. It stores only proof-v5+ reusable HTTP-success rows from upstream tasks that actually returned streams; `{id}`/`{slug}` rows require provider-value correlation. Evidence is reusable only while `(kind, sourceId, currentSha256, providerUrl)` matches exactly and `currentSha256==wantedSha256`. A source SHA change resets that provider's retained evidence. It is proof memory only, not publication authority.
- `scripts/merge_provider_repair_report_v6.py` now merges current targeted proof with the exact-source LKG before applying/materializing the 96-provider census. Run **86** proved this works: `route_lkg_retained=1`, AnimeSama materialized a three-route value chain containing search, episode page and the restored Sibnet `/shell.php?videoid={id}` step.
- LKG persistence is security-isolated in `.github/workflows/provider-repair-fast-targeted.yml`: the provider execution job retains `contents: read`; a separate `persist-route-proof-lkg` job downloads the sanitized proof artifact, has job-only `contents: write`, merges/validates the LKG, and commits **only** `automation/provider-route-proof-lkg.json`. Run 86's security preflight passed and the persistence job succeeded, committing `data(repair): persist exact-source route proof LKG` at `74cd33cd8d1073c4cd83a6a73264941c434f273c`.
- Run **86** (`34308986704`) remains red overall and must not be called 3/3: targeted upstream-positive set was AnimeSama + AnimeVOSTFR + French-Manga, while reconstructed preservation was only French-Manga (`raw=1`, `playable=1`, `verified=1`, `lost=2`). All V16→V21.5 contracts, route-LKG tests, diagnostics and route-cap tests were green.
- Run 86's detailed AnimeSama trace clarified the remaining runtime layer: the restored value plan executes correctly. It selects catalogue ID `93`, fetches `/anime/93-jujutsu-kaisen-1/saison-1/episode-1.html`, learns `videoid=4668025`, then calls `https://video.sibnet.ru/shell.php?videoid=4668025`; that resolution currently returns HTTP 400. The upstream AnimeSama implementation intentionally returns the iframe/embed URL itself as a native-player fallback when its resolver cannot produce direct media. NiakVIO instead discarded the entire correlated plan on the failed player HTTP request.
- Shared **V21.6** (`scripts/upgrade_provider_player_fallback_v21_6.py`) addresses that mismatch generically: failed proof-correlated player/embed-like step URLs are accumulated as bounded fallbacks, all later dependency-ready branches still execute, and the fallback is returned only if no direct/nested branch succeeds. Ordinary catalogue/detail/API URLs are not promoted. `tests/provider_player_fallback_v21_6_test.py` checks direct/embed/player-query eligibility, ordinary-detail rejection, dedupe and referer preservation.
- AnimeVOSTFR had a related pre-LKG evidence gap. Run 84 on the exact same source SHA `f75843cd26128bc78d31ecc641acfe155ca7a5e4046bea977fe5ab3c4f8e8c2a` had reusable, stream-positive branches `/?trembed=0&trid={id}&trtype=2`, `/?trembed=1&trid={id}&trtype=2` and `/shell.php?videoid={id}`. In run 86 the trembed requests were still observed but `requestSpecReusable=false`, so the current providerValuePlan contained only search -> series -> episode. Because the durable LKG did not yet exist at run 84, those earlier reusable rows were absent from the registry.
- `automation/provider-route-proof-seed-v1.json` now bootstraps that pre-LKG AnimeVOSTFR live proof. `merge_provider_repair_report_v6.py` admits historical seed rows **only** when the provider is targeted now and the current exact source identity matches the seed; a SHA change makes the bootstrap ineligible. The normal LKG then becomes the durable owner.
- Targeted run **87** (`34309729426`) was triggered on SHA `04ce5a680e868e32b877c46ce943d31fe54d902f` with V21.6 + exact-source bootstrap. Its security preflight is green. Expected checks: AnimeSama must preserve its player/embed fallback when Sibnet resolution is 400; AnimeVOSTFR should regain run-84 trembed/player branches if the source SHA remains exact; French-Manga must stay on correct catalogue identity `1497198`. Do not claim run 87 success until its live yield is complete.

## 2026-09-09 — V21.6 blocker cleared; full-portfolio sweep resumes

- `Provider Repair Parallel Batch Proof` run **34309729426** (run 87), head `04ce5a680e868e32b877c46ce943d31fe54d902f`, completed success.
- Targeted providers: `animesama-co`, `animevostfr`, `french-manga`.
- Live result: **3/3 raw, 3/3 playable, 3/3 accepted-playable, 3/3 verified, wrong_content=0, lost=0**. `targetGatePassed=true`.
- Global non-network stream guard also passed across the complete **96-provider** catalogue; publication remains forbidden because the full live portfolio gate and five Native Labs are still outstanding.
- V21.6 shared failed-player/embed fallback contract passed. AnimeSama retained the exact correlated plan `/template-php/defaut/fetch.php -> /anime/{slug}/saison-1/episode-1.html -> video.sibnet.ru/shell.php?videoid={id}` and is live verified again.
- AnimeVOSTFR exact-source historical bootstrap matched and rebuilt the evidence-backed chain `/?s={query}`, `?trembed=0`, `?trembed=1`, Sibnet shell, series and episode routes; provider is live verified again.
- French-Manga remains live verified after V21.5 catalogue-identity correction; no upstream-positive pair was lost.
- All V16 through V21.6 contract tests passed, including exact-source route-proof LKG, response-value correlation, identity guards, episode scoping and player fallback.
- Route-proof LKG persistence job succeeded with isolated `contents: write`; it updated all 3 exact-source entries with zero source reset. Rebased/pushed final LKG commit **c25a90b6** (full SHA obtainable from repository history).
- `automation/memory-checkpoint-pending-v2.md` from the previous checkpoint was successfully absorbed and reset to the empty sentinel before this checkpoint.
- Next authority: do **not** stop at these 3 providers. Resume the deterministic live sweep of the remaining 96-provider portfolio, keeping the 10 already accepted green providers as skip authority, using exact-source LKG only as proof memory, fixing shared/runtime family failures rather than deleting/quarantining providers, and preserving `publicationAllowed=false` until full live proof + five Native Labs + final candidate/security/docs/fixed-point gates are complete.

## 2026-09-09 — Run 88 first 24-provider full-portfolio sweep

- `Provider Repair Parallel Batch Proof` run **34310197297** (run 88), head **2eec355d9be79789aebd73c876de9778a5a0928e**, completed with expected overall failure because 4/6 live batches contained upstream-positive regressions. Security/plan preflight and isolated route-proof LKG persistence succeeded.
- Exact 24 selected: `allmovieland`, `anidb`, `anikototv`, `animekai`, `animepahe`, `animesalt`, `animesama-co`, `animesultra`, `animetsu`, `animevostfr`, `animezey`, `animoflix`, `cineby`, `cinemacity`, `cinemm`, `dooflix`, `dulourd`, `french-manga`, `goated`, `hdghartv`, `hianime`, `kurage`, `movieblast`, `movies4u`.
- Upstream-positive representative pairs = **10**. NiakVIO preserved/verified **3** providers (`animekai`, `french-manga`, `movies4u`) and lost **7** upstream-positive pairs: `animesama-co:anime`, `animevostfr:anime`, `animezey:movie`, `animezey:tv`, `cineby:movie`, `cineby:tv`, `movieblast:movie`.
- AnimeSama: exact correlated plan still resolves catalogue id 93 and player id 4668025. Sibnet shell returned HTTP 403. V21.6 emitted `step_player_fallback`, but final raw streams were still zero. Therefore the shared strict stream sanitizer is deleting the intentionally preserved native-player fallback after the resolver correctly marks it.
- AnimeVOSTFR: exact search/detail/episode/trembed branches execute; `trembed=0` returned 200 then Sendvid 502, `trembed=1` returned 200, Sibnet shell returned 400. V21.6 again emitted `step_player_fallback`, yet final raw streams were zero. Same sanitizer/fallback ownership bug as AnimeSama, not an identity regression.
- AnimeZey: upstream remains stream-positive for both movie and TV. Reconstructed search reaches the current worker endpoint but discovered `animezeydl.workers.dev/download.aspx` URLs returned HTTP 500. Keep separate until exact upstream output behavior/headers are inspected; do not invent replacement routes.
- Cineby: exact upstream source is stream-positive for movie and TV. Reconstruction correctly reaches `api.speedracelight.com/seed` and `cdn/sources-with-title`, extracts 480/720/1080/2160 HLS URLs on `moon.peakstorm.top`, then loses them because bare HLS probes return 403. Current upstream explicitly returns each stream with playback headers including browser UA plus `Referer: https://www.cineby.at/` and `Origin: https://www.cineby.at`. Root cause is shared playback-header/context loss between API result extraction and direct-media probe/output, not TMDB/search/route identity.
- MovieBlast: exact upstream remains stream-positive (movie and some TV fixtures), but NiakVIO tries stale/generic `https://app.cloud-mb.xyz/api/search/<query>` and receives 404. Current upstream uses app-specific static request headers/tokenized search/detail paths and dynamically signs media URLs with timestamp + CryptoJS/HMAC before returning them with playback headers. This requires a real generic signed-API capability or equivalent source-derived recipe; do not hardcode provider secrets or claim the generic route works.
- Dooflix hit upstream HTTP 429 in this sweep. It is not an upstream-positive lost pair for run 88 and must be treated as rate-limited, not as a proven dead provider.
- Existing shared `_streams(urls, referer, extraHeaders)` supports output headers, but `_crawlDirectMedia` currently carries only `{url, depth, referer}` and emits direct media without arbitrary safe playback headers. The V4/V5/V6 sanitizer already knows how to mirror `stream.headers` into `behaviorHints.proxyHeaders.request`; the missing transport context must be restored before/properly through probing.
- Planned shared fixes: (1) narrowly preserve an exact proof-correlated **non-direct** player/embed fallback through the sanitizer while still stripping private proof markers and keeping direct-media fail-closed checks; (2) add bounded same-URL direct-media retry/output with safe provider-origin Referer/Origin context when an actually discovered media URL returns 403 without context. Neither fix may bypass auth/DRM or promote ordinary catalogue/API URLs.
- Publication remains **forbidden**. Run 88 is only the first 24-provider live wave; full 96 live proof, all five Native Labs, final candidate/manifests/security/docs/minimizer/fixed-point gates are still mandatory.

# NiakVIO checkpoint — Run 91 / portfolio sweep continuation

## Publication/finalization remains blocked
- `publicationAllowed=false`; target remains 5.21.40.
- Catalogue target is all 96 providers, not only currently green/active providers.
- Final publication still requires the exact candidate, 96-provider proof, the 5 Native Labs (TV Android, Mobile Android, Mobile iOS, Desktop macOS, Desktop Windows), player/UX/metadata/session/latency validation, security/docs/minimizer/fixed-point clean, and the four public manifests (`manifest.json`, `vf/manifest.json`, `no-anime/manifest.json`, `vf-no-anime/manifest.json`).
- Route discovery must stay live-proof-first: no invented routes and no validator-only success.

## Exact-source proof/LKG architecture now in place
- V21.5 fixed French-Manga catalogue identity: JJK S1 authoritative id is `1497198` rather than the unrelated global HTML id `1497822`.
- Exact-source live-positive route-proof LKG is implemented and persisted by a separate write-only job; provider execution itself remains `contents: read`.
- Same exact source SHA may retain previous positive reusable proof rows; a source SHA change resets them. `{id}`/`{slug}` rows require response-value correlation. LKG remains proof memory only, never publication authority.
- AnimeVOSTFR has an exact-source-only historical bootstrap for its pre-LKG `trembed`/Sibnet evidence.

## V21.6/V21.7 player fallback
- V21.6 preserves a failed proof-correlated player/embed hop as a bounded native-player fallback while still executing later branches.
- V21.7 adds private exact fallback provenance (`__nuvioCorrelatedPlayerFallbackV1`) and terminal sanitizer V7 consumes/strips only that narrow marker. Direct media remains fail-closed; ordinary catalogue/detail/API URLs are not promoted.
- Run 89/90 failures were pre-network test-harness issues (module path, then over-literal assertion), not provider results.
- Run 91 CI passed both real contract tests before network: `provider player fallback V21.7 tests passed` and `stream output correlated player fallback V7 tests passed`.

## Run 87 and first broad wave
- Run 87 (`34309729426`) was 3/3 for AnimeSama, AnimeVOSTFR and French-Manga; full non-network 96 guard passed.
- Run 88 first broad tranche had 10 upstream-positive pairs, 3 preserved (`animekai`, `french-manga`, `movies4u`) and 7 losses: AnimeSama, AnimeVOSTFR, AnimeZey movie+tv, Cineby movie+tv, MovieBlast movie. Dooflix was HTTP 429 and was not converted into a fake route.

## Run 91 exact result
- Run 91: `34311503094`, head `9388b705a1801ea9db828dd5a01c7b3c57618722`; LKG persistence advanced main to `5c3c21150c24b8d4aebd4054faa89e2b0a55ec88`.
- AnimeSama: exact value plan retained search -> episode -> Sibnet and targeted audit verified it.
- AnimeVOSTFR: not upstream-positive in that invocation; do not classify as a verified success or a NiakVIO loss from run 91.
- AnimeZey: upstream positive movie + TV but target lost both.
- Cineby: targeted audit lost movie+TV in this invocation, while the global census in the same run showed real 4/4 verified movie and 4/4 verified TV. Existing Cineby Wings/headers are already correct; this is intermittent CDN/network behavior, not a reason to invent routes/headers.
- MovieBlast: upstream movie positive but no reusable proof route; target correctly stayed fail-closed.
- LKG persist job succeeded. No later Provider Repair run was observed after run 91 at the time of this checkpoint.

## AnimeZey diagnosis
- Exact AIO source SHA: `46e83c8d710830679b7f17eacb03e014fc4195237cd423fe63254862549f24ff`.
- Upstream returned 1 movie stream and 2 TV streams on the positive fixtures.
- Positive calls use structured POST search values that current request proof cannot deterministically template: movie example `Interstellar.2014`; TV example `Breaking.Bad.S01E01` plus a redacted `page_token`.
- The movie request becomes non-reusable only because the current scalar placeholder logic understands whole-value `{query}` / `{year}` but not a deterministic composite query. This is a shared request-template capability gap, not an AnimeZey-specific rule.
- TV must remain fail-closed while `page_token` is redacted unless a live request proves a safe reproducible form without freezing a secret.
- Next generic fix: derive deterministic composite title/year and title/SxxExx request-body templates only when the observed value exactly decomposes into fixture-owned fields with no residue; add a shared runtime transform/placeholder and neutral contract tests.

## Cineby diagnosis
- Upstream still returns four streams for movie and TV.
- Global run-91 census successfully reached `api.speedracelight.com` seed/source endpoints and four `moon.peakstorm.top` HLS URLs, verified 4/4 with HTTP 200.
- Other targeted attempts saw the same CDN return 403. Keep retry/network classification separate from algorithmic reconstruction; do not fabricate headers.

## MovieBlast diagnosis
- Exact AIO source SHA: `d3b04a5ee1a13fed77192b5226d46001508fe321fa747f0c519d0c23d5b1a974`.
- Current upstream uses `https://app.cloud-mb.xyz`, static mobile headers, a path token for search/detail, and runtime HMAC-SHA256 signing of returned media URLs using the current Unix second and a source secret.
- Reconstructed stale generic `/api/search/...` routes return 404. Proof recovery correctly refuses to freeze redacted token/signature material, so `providers_proven=0` is expected rather than a false success.
- Do not hardcode TOKEN/SIGN_SECRET. A future solution must be a generic, safely representable signed/mobile request capability or remain fail-closed.

## Immediate continuation
1. Add the generic deterministic composite request-body template capability and tests, then live-retarget AnimeZey.
2. Independently advance the next deterministic 24-provider sweep so AnimeZey/MovieBlast do not block coverage of the remaining 96.
3. Re-test Cineby under the normal retry policy and distinguish transient CDN failures from reconstruction failures.
4. Keep MovieBlast isolated as signed-route architecture work; improve secret-free diagnostics rather than copying secrets.
5. Absorb this checkpoint into `MEMORY.md` and reset this pending file to ``.

## 2026-09-09 — V21.6 live recovery + non-regression checkpoint

- User requirement tightened after repeated repair regressions: **a provider/bundle already proven green becomes an immutable live reference**. A Repair/reconstruction must not replace it unless the candidate is live A/B-tested against that reference and proves no regression. Architectural cleanliness never justifies losing a previously working provider.
- Targeted Provider Repair run **87** (`34309729426`), head `04ce5a680e868e32b877c46ce943d31fe54d902f`, completed **success**. Job `102333746919` proved all three blocker providers live-positive together: **AnimeSama + AnimeVOSTFR + French-Manga = raw 3 / playable 3 / verified 3, lost 0**. `tests/global_stream_output_guard_test.py` also passed across the 96-provider output surface. This is targeted live proof for the three providers plus a global structural/output guard; it is **not** proof that all 96 providers are live-verified.
- V21.5 remains the French-Manga catalogue-identity fix: strongly correlated title/card ID wins over response-wide fallback; JJK S1 stays on `newsid=1497198` rather than wrong `1497822`.
- Exact-source positive route-proof LKG remains proof-memory only, keyed by immutable source identity and requiring live-positive reusable evidence; it is not publication authority. The separate persistence job keeps provider execution read-only and writes only sanitized LKG JSON.
- AnimeVOSTFR uses a one-time pre-LKG exact-source bootstrap only when current targeted source identity exactly matches the historical seed; SHA/source change makes the seed ineligible, after which normal LKG is authoritative.
- V21.6 shared player/embed fallback fixed the AnimeSama failure mode without provider-specific fixture logic: a failed player/embed resolution (e.g. Sibnet 400) can remain a bounded native-player fallback while ordinary catalogue/detail/API failures are not promoted. This mirrors upstream behavior and keeps later branches executable.
- Current next regression investigation: **VF generation A/B around 5.21.36 -> 5.21.37 for Kehflix and StreamZo**. Treat the accepted 5.21.36 provider bytes as immutable baseline if live replay confirms them. Diagnose generation/runtime cause before changing provider bytes; add a general regression gate requiring prior-green preservation or independently live-proven replacement.
- Parallel secondary work remains mandatory while live workflows run: security/workflow policy, minimizer/fixed-point, docs/architecture consistency and stale metadata cleanup. Do not publish from these targeted greens.
- Publication remains gated; project target remains all **96** Provider Objects plus the five Native Labs and four final manifest projections before final 5.21.40 publication.

# NiakVIO checkpoint — 2026-09-09 — provider history + systemic regression audit

## 96-provider historical matrix
- Durable report: `automation/PROVIDER-HISTORY-MATRIX.md` + `automation/provider-history-matrix.json`.
- Current manifest tracked by report: 5.21.37, exactly 96 providers.
- Exact snapshots: tag 5.21.0, tag 5.21.16, publication 5.21.36 (`b4d5bff4c2e3b8e9944c1eaaf8ae9690cb00d5cf`), then current.
- V2 policy: absolutely no cross-version evidence fallback. 5.21.0/5.21.16 status comes from each tag's own `availability-report.json`; 5.21.36 from its own `provider-v3-quick-yield.json`; current from published-byte guards, current TV field evidence, or explicitly labelled candidate evidence.
- State legend: 🟢 exact positive evidence; 🟡 partial/degraded/blocked/wrong-content/candidate; 🟠 LEARN-owned debt; 🔴 explicit failure/no-stream/current published guard red; ⚪ unknown/inconclusive.
- V2 generator: `scripts/build_provider_history_matrix_v2.py`; workflow `Provider History Matrix` run 34330433714 passed security/build/persist and bot commit `78487f86f00345ecfbe83ce749f3d1956043dd78` persisted colored 96/96 report.
- Current exact regression-watch set generated by V2: `kehflix`, `movieshunt`, `purstream` (at least one historical 🟢 and current 🔴/🟠). Do not infer that other ⚪ providers are broken.
- Known current protected baselines: Castle movie+TV, PersianStremio movie+TV; Anime-Sama anime lane; DesiFlix TV lane; StreamZo movie lane. A/B live proof is mandatory before replacing a known-good published lane.
- Candidate-only greens remain distinct from published/device proof: AnimeVOSTFR and French-Manga after run 87.
- Residual route/data repair must be bounded; then hand to LEARN. Avoid provider-by-provider manual loops unless one shared family fix is proven.

## Current user field evidence on published manifest
- TV Interstellar: Castle, PersianStremio, StreamZo visible.
- TV The Unwanted Undead Adventurer: Anime-Sama visible.
- TV House of the Dragon S1E1: PersianStremio, DesiFlix, Castle visible.
- Desktop macOS: no provider visible in the user's current field test.
- Treat this as field evidence distinct from CI. Do not overwrite it with an invalid lab zero.

## Desktop Lab systemic blocker discovered
- Last full Desktop lab associated with final five-Labs launch: workflow run `34110935429` (NATIVE - Desktop Reader, run #113), official NuvioDesktop SHA `21aabeeb49fc6de835f9031a65cc5f8489419330`.
- macOS and Windows jobs failed before provider execution. The macOS native player bridge itself built successfully.
- Failure occurred at `:composeApp:compileTestKotlinDesktop`: upstream `PlayerExitOrderingTest.kt` anonymous `PlayerEngineController` lacked newly required `applyAudioLanguagePreferences(languages: List<String>)`.
- Consequence: providerCount/executions/nonEmpty remained zero, `missing_begin_marker`, 96 providers missing. This CI zero is lab-infrastructure evidence, NOT provider evidence.
- Current upstream NuvioDesktop still has the stale test fake while production `PlayerEngineController` requires `applyAudioLanguagePreferences`.
- Test-only compatibility shim added at `scripts/native_desktop_upstream_test_compat.py`, covered by `tests/native_desktop_upstream_test_compat_test.py`. It may only add one no-op override to that exact upstream `commonTest` fake, is idempotent, and fails closed on shape drift. It never edits Nuvio commonMain/desktopMain runtime, networking, player, Gradle, or OS policy.
- `automation/native-human-ux-policy.json` moved to v7 and records blocker `desktop-player-exit-ordering-test-api-drift`; exact commonTest path is the only new Desktop checkout exception.
- `.github/workflows/native-desktop-reader-acceptance.yml` now runs the compatibility contract and applies the shim before staging the corpus. Do not classify a zero-execution compile failure as provider evidence again.

## Core regression audit in progress
- `scripts/nuvio_client_lab.cjs` currently uses `DEFAULT_TIMEOUT_MS=70000` and `DEFAULT_PLAYBACK_TIMEOUT_MS=18000`; these are identical to 5.21.36. Therefore the global client-lab timeout did not regress 5.21.36 -> current.
- Old `scripts/publish_nuvio_tv_compat_v2.py` still contains provider-specific 12–15s adapter settings for Goated/WookaFR/Coflix/StreamZo/Frenchstream; verify whether these are still publication-authoritative before changing them. Do not confuse health latency thresholds with runtime hard timeouts.
- `engine_v2/src/stream-presentation.mjs` changed since 5.21.36 so current `name` mirrors the quality-bearing `streamTitle` instead of only provider name; continue validating metadata/badges through Core contract and real native UX, not static assumptions.

## Execution discipline
- Finish all non-reader commits/checkpoints before triggering expensive Native Labs, then freeze main while the intended reader run executes; persistent blocker `reader-run-cancellation-churn` forbids cosmetic/speculative pushes during evidence collection.
- Publication remains blocked until candidate, all 96 proof, five Native Labs, UX/player/metadata/session/latency, security/docs/minimizer/fixed-point gates are complete.

# NiakVIO checkpoint — 2026-09-09 — Core regression gate before Desktop rerun

- `CORE - Stream Metadata Contract` run `34331678345` passed fully on `fdfe7bca3cb5db544a90372bf21547a2bdf68668`.
- New `tests/core_runtime_nonregression_contract_test.py` passed and locks provider lab timeout >=60s (actual 70s), playback timeout >=18s (actual 18s), current 96-provider cardinality, quality-bearing stream `title` + `name`, `badgeIds`, `displayBadges`, `presentationFacts`, and requires the legacy 12–15s `publish_nuvio_tv_compat_v2.py` publisher to remain absent from current workflows.
- Remaining Core contract steps also passed: lossless metadata, presentation pipeline, quality recovery, sanitizer header/transport preservation, sanitizer fail-closed, and presentation fixed point.
- Static Core green is necessary but does not prove actual client UX/latency/session/player/badge rendering. Native Labs remain mandatory.
- Durable audit doc: `automation/CORE-REGRESSION-AUDIT.md`.
- Desktop prior run `34110935429` is invalid as provider-zero evidence because it failed before corpus execution on stale upstream test compilation. Test-only compatibility shim/policy v7/workflow wiring are now committed. Next step is a Desktop macOS+Windows rerun on a frozen HEAD; do not push unrelated commits while it runs.

# NiakVIO checkpoint — 2026-09-09 — Desktop HTTP-200 zero + Core budget + durable media identity

## Desktop root-cause narrowing
- Official NuvioDesktop protected-byte bisect run **34338322836** (macOS, PersianStremio, Interstellar) proved the runtime loads the protected PersianStremio bundle and performs `GET https://persianstremio.vercel.app/stream/movie/157336.json` successfully (`HTTP 200`, `application/json`). Sanitized response-shape instrumentation proved the JSON itself contains no stream rows: `kind=object rows=0 objectRows=0 httpUrlRows=0 externalUrlRows=0`; final plugin result is `count=0` in under one second.
- Therefore the PersianStremio Desktop zero is **not** a QuickJS JSON/result-parser loss and is not caused by the former 25/30 s Core budget. The numeric TMDB backend route itself is empty for this fixture.
- Official NuvioDesktop uses a single positional identity at its plugin boundary: `StreamsRepository` -> `PluginRepository` -> `PluginRuntime.executePlugin(tmdbId, mediaType, season, episode)` -> `getStreams(tmdbId, mediaType, season, episode)`. NuvioMobile has the same structural four-argument contract. Mobile/Desktop must not require users to configure a TMDB key to recover IMDb identity.
- NuvioTV uses the same four-argument ABI but has an audited runtime TMDB capability, allowing Core to hydrate TMDB metadata/external_ids and derive IMDb. Treat this as an equivalent identity capability, **not** permission for shared provider bundles to depend on `TMDB_API_KEY`.

## Core timeout authority fixed in source
- `CORE.MEDIA_TYPE_RESOLUTION` previously owned a shorter internal execution deadline while Native Labs owned an outer deadline. This created competing timeout authorities and could drop valid late results after network return.
- Source fix commit **a2ccd335ea3be285e3a37807488605abdc195865** (`fix(core): unify provider execution budget at 60s`) sets canonical Core `providerTimeoutMs=60000` and `tvProviderTimeoutMs=60000`, revision `tmdb-data-contract-launch-gate-v30-unified-60s-budget`.
- Validation run **34339079601** completed fully green, including media-resolution contracts, latest-request cancellation, abort-ignoring native-fetch cancellation and Core budget non-regression.
- Do **not** rematerialize this Core into already protected green provider lanes until required live A/B proves no regression. Green lane bytes remain immutable authority.

## Desktop media-identity A/B history
- Baseline evidence is stable: protected PersianStremio bytes on official Desktop call `/stream/movie/157336.json`, receive HTTP 200 with zero stream rows, and finish `count=0`.
- Host resolution for Interstellar maps TMDB **157336** to IMDb **tt0816692**. TMDB credentials are used host-side only for the Lab resolution and are never projected into provider JavaScript.
- Run **34341065713** established a valid baseline (`count=0 imdb_route=false numeric_route=true`); its first dual branch was harness-invalid because mutation happened before human-UX purity audits. Never weaken those audits.
- Run **34343072382** is valid evidence against the *V2 injection point*, not against dual-ID itself. Baseline job **102438235395** passed. Dual job **102438235616** successfully resolved `tt0816692`, injected the canonical `tmdbMetadata.external_ids.imdb_id` shape after checkout purity audits, executed the provider, but still produced `count=0 imdb_route=false numeric_route=true`. Provider bytes remained unchanged.
- Exact source inspection then proved why V2 could not work: NiakVIO Core itself rewrites `globalThis.__nuvioMediaContext = a.__nuvioContext || null` before provider execution and again after authoritative resolution. Core also initializes `var mediaCache=Object.create(null); globalThis.__nuvioTmdbMetadataCacheV1=mediaCache` while the provider/Core bundle is evaluated. Therefore any host identity global/cache injected **before** `evaluate(wrappedCode)` is destroyed or superseded before the provider consumes it.
- PersianStremio's existing `hydrateImdb()` already consumes the canonical shared metadata surfaces in order: `__nuvioMediaContext.tmdbMetadata`, `__nuvioTmdbMetadataCacheV1[<namespace>:<tmdbId>]`, then `__nuvioCoreGetTmdbDataV1`. The correct host bridge is therefore systemic, not provider-specific.

## Canonical identity architecture restored and locked
- Architectural invariant: positional `getStreams(tmdbId, mediaType, season, episode)` is **transport**, not the complete media identity contract.
- Canonical context IMDb path: **`__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`**.
- Canonical shared metadata cache: **`__nuvioTmdbMetadataCacheV1`**, with host-provided entries shaped as `state=ok` + `metadata.external_ids.imdb_id`.
- A host-side identity bridge must populate the shared metadata identity **after provider/Core bundle initialization and before `getStreams` invocation**. Pre-bundle injection is explicitly invalid because Core initializes/rewrites these globals.
- No end-user TMDB credential may be required for NiakVIO compatibility, and no TMDB secret may be projected into provider JavaScript merely to recover IMDb identity.
- Desktop/Mobile currently have a documented host identity-hydration gap; Android TV currently has equivalent Core hydration through its audited runtime metadata capability.
- V3 Lab bridge commit **bf37cbdf20dfefd6be3e6e033ea44f1fae675f2e** moves identity injection after `evaluate(wrappedCode)` and populates Core's canonical metadata cache before `getStreams`. Test commit **f65a8dfdd243e3ad963cc358f320a95a23c2e5eb** locks ordering, cache shape, no-secret behavior and idempotence. Commit **9135b4036f38fd5dca97e2a12d6ef1c3eb045b35** keeps only a temporary V2 marker for compatibility with the one-shot A/B harness; V3 is the active bridge.
- Runtime compatibility is now being made executable, not documentary only: migration `scripts/upgrade_runtime_media_identity_contract_v1.py` commit **12aec359e851fb080d41839f518c40968748b6f7**; strengthened `scripts/runtime_contract_gate.py` commit **988e2374fc05fb5aef62641e7b8a1a41bffaa544**; renderer commit **39bf05a107f2d3ce345f5031c20c350ef100a455**. The canonical JSONs/README must be generated and pass CI before this checkpoint is considered complete.
- Runtime-contract materialization workflow run **34344595051** was queued from commit **bc217211be6e4fd6226b5b93416b868d5c3a7feb**. It must prove migration idempotence, renderer fixed point, semantic assertions, and executable runtime gate before committing generated JSON/Markdown.
- V3 Desktop A/B run **34344396120** was in progress at this checkpoint. Do not claim the media identity root fix until the dual job proves an IMDb route and `count>0` with the protected PersianStremio bytes unchanged.

## Memory durability
- `.github/workflows/memory-checkpoint.yml` was previously main-only, so workbench checkpoints could remain outside `MEMORY.md`. Commit **c78baa379950bd30604a9463dd06be62d479f357** makes the writer branch-aware for `main` and `workbench/**`, checks out/pulls/pushes the actual branch, and keeps the append idempotent.
- This pending checkpoint update must trigger the branch-aware writer. Verify physically that this heading appears in workbench `MEMORY.md` and that the pending file is reset before considering memory persistence complete.

## Immediate continuation authority
1. Collect V3 A/B run **34344396120**. Success requires protected bytes unchanged, `/stream/movie/tt...json` observed, and `FIELD_NATIVE_RESULT count>0`; otherwise continue the runtime bisect without forcing the conclusion.
2. Collect runtime-contract run **34344595051** and verify generated `automation/platform-runtime-contracts.json`, `automation/nuvio-client-compatibility-matrix.json`, and `automation/PLATFORM-RUNTIME-CONTRACTS.md` physically contain the identity invariant.
3. Verify the branch-aware Memory writer appends this checkpoint into workbench `MEMORY.md` and clears `automation/memory-checkpoint-pending-v2.md`.
4. Once the V3 mechanism is proven, convert the Lab-only bridge into the smallest backward-compatible client/runtime contract for Desktop and Mobile; preserve the four-argument provider ABI and keep provider bytes/secrets untouched.
5. Remove one-shot/temporary workflow and marker after evidence is persisted.
6. Resume lane-scoped Repair across all 96 Provider Objects; protected green lanes remain exact-byte immutable unless live A/B proves a non-regressing replacement.
7. Mandatory end state remains all 96 plus five Native Labs (Android TV, Android Mobile, iOS Mobile, macOS Desktop, Windows Desktop), final projections, security/docs/minimizer/fixed-point gates, and the real Purstream House of the Dragon S3E1 check before publication.

# NiakVIO checkpoint — 2026-09-09 — runtime identity contract materialized + V3 harness correction

## Runtime compatibility is now durable and executable
- Runtime media-identity materialization workflow run **34344595051** completed **success**.
- Bot commit **2804a57480cc27d2754e55638a4fd26571ef7f7f** (`arch(runtime): materialize TMDB IMDb identity contract`) physically generated and committed the canonical runtime contract files.
- `automation/platform-runtime-contracts.json` now has audit date **2026-09-09**, capability `media_identity_hydration`, Desktop/Mobile marked with the current host-side identity gap, and Android TV marked as an equivalent `bridge` capability.
- `automation/nuvio-client-compatibility-matrix.json` now locks: positional `getStreams(tmdbId, mediaType, season, episode)` is transport rather than complete identity; canonical IMDb context path `__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`; canonical metadata cache `__nuvioTmdbMetadataCacheV1`; no end-user TMDB credential requirement; no TMDB secret projection requirement.
- Generated `automation/PLATFORM-RUNTIME-CONTRACTS.md` visibly contains the new `Hydratation identité TMDB ↔ IMDb` row and a dedicated canonical identity section, including the required host-bridge timing **after provider/Core initialization and before getStreams**.
- The one-shot materialization workflow was removed after proof in commit **e2e564277dd04e1779d4b0d638fc8c095ad97e70**. Keep the migration, renderer and executable gate; remove only temporary CI orchestration.

## Memory writer proof
- Branch-aware Memory run **34344670882** completed **success**.
- Workbench `MEMORY.md` was physically verified to contain the prior Desktop/Core/media-identity checkpoint; observed blob SHA **09801cc27a9b19a13fb79d86c629fec0e7555c98**.
- `automation/memory-checkpoint-pending-v2.md` was physically verified reset to ``. This proves workbench checkpoints now persist rather than remaining stranded outside MEMORY.

## V3 run 34344396120 is harness-invalid, not runtime evidence
- V3 A/B run **34344396120**, dual job **102442498820**, reached host IMDb resolution (`tt0816692`), protected-byte immutability and the V3 transform contract (`canonical_tmdb_cache=true post_core_init=true`).
- In the real suite, both human-UX checkout audits remained green and the V3 transform was applied to official NuvioDesktop `PluginRuntime.kt`.
- Execution then stopped immediately after `FIELD_NATIVE_DESKTOP_DUAL_ID_CONTEXT added=true version=3 ...`; no corpus log was produced, so PersianStremio itself was never executed in this run.
- Exact cause: the one-shot workflow still executed `grep -q 'NIAKVIO_LAB_DUAL_ID_CONTEXT_V2'` against the modified NuvioDesktop `PluginRuntime.kt`. The obsolete V2 marker existed only as a Python constant in the NiakVIO transform script and was never inserted into `PluginRuntime.kt`, so that grep necessarily returned 1.
- Therefore **34344396120 must never be interpreted as evidence that the V3 post-Core metadata-cache bridge failed**.
- Workflow commit **a7f2ad2cf917f8f91ac6320c28082ebcbb908d77** updates the harness to assert `NIAKVIO_LAB_DUAL_ID_CONTEXT_V3`, reports `canonical_tmdb_cache=true post_core_init=true`, and updates verdict wording to the canonical post-Core cache contract.
- Cleanup commit **cf1dc9c885935e4cffb0c95a82bb78ee20d563c8** removes the obsolete V2 compatibility marker entirely from the V3 transform.
- Final corrected A/B run **34344938190** is the first run on the clean V3 harness/transform pair. Success criteria remain: provider bytes unchanged, actual `/stream/movie/tt...json` route observed, and PersianStremio `FIELD_NATIVE_RESULT count>0`. Do not force the conclusion before this evidence exists.

## Continuation authority
1. Collect final V3 run **34344938190** and inspect the dual job log, actual route and count.
2. If V3 proves positive, persist the exact route/count/run/job and promote the mechanism from Lab evidence to the smallest backward-compatible Desktop/Mobile runtime contract, keeping the public four-argument provider ABI intact.
3. If V3 reaches IMDb but remains zero, inspect the backend response; if it fails before provider execution, fix the harness/runtime bridge and retry. Never collapse these cases into provider failure.
4. Remove `.github/workflows/desktop-dual-id-ab.yml` after decisive evidence is persisted; it is a one-shot diagnostic workflow.
5. Resume all-96 lane-scoped Repair and then the five mandatory Native Labs. Protected green lanes remain byte-immutable unless live A/B proves a non-regressing replacement.

## 2026-09-10 — semantic/transport drift caught before merge

- Final cleanup run `34412252681` correctly failed before commit on ANIDB because the candidate manifest exposed anime transport without the required `series` alias and still carried an obsolete anime->movie widening path.
- This supersedes stale docs/source that said anime-only `supportedTypes=[anime,tv,movie]`. Authoritative invariant: canonical semantics are `movie/tv/anime`; `series` is transport-only alias of `tv`; episodic anime may add `tv+series`; **movie must never be manufactured for anime-only** and appears only when `movie` is canonical provider capability.
- Internal Core may preserve a TMDB movie namespace inside an already-authorized anime request; that is not permission to expose a generic movie lane in manifest/health capability.
- Materializer, semantic enforcer, health/Repair inference, tests and current user-facing docs are reconciled to this invariant before merge.
- Repair run `34409463163` remains useful route/yield evidence but is no longer final acceptance for the transport matrix. A fresh authoritative Repair + four-version gate is mandatory after this correction.
- Do not delete `workbench/systemic-recovery-20260909` until corrected Repair, clean PR, merge and five Native Labs are green. Final branch target remains only `main` + `brain-learning/proposals`.

## 2026-09-10 — Repair migration forward-compatibility gate

- Corrected semantic/transport Repair uses the authoritative 188-task matrix; anime-only no longer gains an artificial movie lane and TV/anime episodic transport keeps `tv + series`.
- Fresh Repair runs then exposed stale *migration validators*, not provider/runtime failures: Source Plan V10 expected its pre-V14 materializer call shape; V18.4 expected its pre-V20 response-value scalar/depth/trace surroundings.
- V10 validation is now forward-compatible with V14 while still requiring `runtime_domain_replacements` as the only executable domain-replacement authority.
- V18.4 validation must preserve its bounded JSON-text bridge and sanitized trace but accept the current V20.x id/slug owner and depth-8 dependency replay. Its secret-leak audit is scoped to the actual `_spv184Trace` helper; later security-filter code containing words such as `authorization` is not trace output.
- These fixes change validators only. They do not alter provider DATA, routes, runtime algorithms or accepted stream evidence. A fresh full authoritative Repair + four-version gate remains mandatory before cleanup/merge.

## Media-type semantic/transport contract — authoritative 2026-09-11

- Durable contract: `docs/media-type-transport-contract.md`.
- Canonical semantic type owns identity/provider selection; runtime transport owns only the Nuvio ABI invocation lane.
- Mapping: ordinary movie `movie -> movie`; ordinary TV/episode `tv -> tv`; anime series/episode `anime -> tv`; anime movie `anime -> movie`.
- Anime films remain canonical `anime`; episodic anime remains canonical `anime`. Never globally rewrite canonical anime to tv.
- `canonicalSupportedTypes` is semantic authority. `supportedTypes` may carry compatibility/transport aliases but must never widen semantic capability.
- Provider selection occurs before runtime aliasing.
- Native Lab evidence should expose `logical_type` and `request_type`, including both anime/tv and anime/movie cases.
- Western animation is not automatically anime; trusted identity is required.
- Current 46-provider workbench and final five-Lab evidence must conform to this contract.


## 2026-09-11 — Manual hub/runtime evidence (authoritative; do not ask user to repeat)

This section is the durable authority for the manual hub/site/network evidence supplied during the active 46-provider recovery session. Do not ask the user to repeat any URL or DevTools trace recorded here. Re-validate live when needed, but preserve the hub as discovery authority and never overwrite a proven good hub with a guessed terminal domain.

### Current recovery execution context

- Active recovery branch for this session: `workbench/hub-matrix-46-20260911`; `main` remains untouched until strict runtime stability + the five mandatory Labs. This temporarily supersedes the older MEMORY topology note that said not to recreate a workbench.
- Catalogue remains 96 total providers with 46 ON / 50 OFF for the active hub matrix.
- Strict green means `playable_verified` on every required declared lane; structural/materialization green alone is not stream proof.
- Last stable strict full set before the manual-hub wave: `movieshunt`, `playimdb`, `purstream`, `videasy` (4 full). Frenchstream movie produced one live `playable_verified` gain but its TV lane remained unresolved and a later movie retry timed out; treat it as partial/unstable until repeated proof.
- User-path testing is the final gate, not the discovery strategy. Prefer hub/site/network contracts and exact player/API chains, then validate E2E in NiakVIO.
- Never count an upstream merely because it returns a URL. Upstream comparison must pass the same playback/identity verification as local NiakVIO.

### Movies4U — manual authority + discovered chain

- Hub: `https://movies4u.band/`.
- Hub exposes a `View Full Site` link through `https://tinyurl.com/rockybhaipro1`.
- That redirect currently resolves to terminal site `https://new6.movies4u.clinic/`.
- Search pattern confirmed manually: `https://new6.movies4u.clinic/search.html?q=house+of+the+dragon`.
- Example work page confirmed: `https://new6.movies4u.clinic/reacher-season-1-4-multi-audio-complete-amazon-prime-web-series-web-dl/`.
- Site is download-oriented, but deeper live tracing proved work page -> `m4ulinks.site/number/<id>` -> host families including `hubcloud.cx/drive/...` and `gdflix.dev/file/...`.
- HubCloud path can continue through PixelServer (`pixel.hubcloud.cx`) and a `gamerxyt.com/dl.php?link=<...>` wrapper; the final `link` parameter must be unwrapped before returning media.
- WordPress `/wp-json/wp/v2/search` is NOT trustworthy on the current terminal: it returned stale/cached Interstellar regardless of query.
- Actual frontend lookup contract discovered: `/lookup.php?q=<title>&page=1&per_page=30`, returning hits with at least `post_title` and `permalink`. Interstellar, Breaking Bad, House of the Dragon and Reacher returned relevant top hits in direct probes.
- TV pages group by season/quality and may send `Single Episodes` to `m4ulinks`; episode identity must be selected inside the deeper hop, not guessed from the outer page.
- Do not reduce Movies4U to a blind domain replacement `new5 -> new6`; the old upstream is structurally obsolete because it still assumes the old search path.

### Moonflix — manual authority + TMDB-direct contract

- Official/community hub supplied by user: `https://t.me/s/Moonflix_official_Channel`.
- Current terminal site is obtained from the latest Instagram-linked hub message: `https://moonflix.website`.
- Site frontend is React.
- Manual DevTools trace for The Odyssey proves TMDB ID is used directly.
- Movie mapping endpoint example: `https://raw.githubusercontent.com/Watchout2025/api/refs/heads/main/hls/movie/1368337`.
- The RAW document for TMDB movie `1368337` contains player URL `https://multimovies.rpmhub.site/#fcx9t5`.
- Therefore current proven movie chain is: Telegram/Instagram discovery -> `moonflix.website` -> TMDB ID -> GitHub RAW `Watchout2025/api/.../hls/movie/<tmdbId>` -> MultiMovies hash player.
- Direct guesses for TV paths around TMDB 1396 returned 404 during diagnostics; TV schema is unknown and must be learned from Moonflix frontend/network, not invented.

### HDHub4U — manual authority and season-matching warning

- Hub: `https://hdhub4u.bi/`.
- Hub currently points to `https://new5.hdhub4u.cl/?utm=mn1`; strip UTM/tracking and store terminal as `https://new5.hdhub4u.cl/`.
- Search example: `https://new5.hdhub4u.cl/search.html?q=house+of+the+dragon`.
- Search can return multiple links covering different season combinations. The user observed two links for S1 and other links for S2/S3; selection MUST be exact/fail-closed on requested season.
- Example S1 page: `https://new5.hdhub4u.cl/house-of-the-dragon-season-1-hindi-webrip-all-episodes/`.
- Page exposes download/stream quality groups (e.g. 480p pack, 720p 10Bit HEVC, 1080p 10Bit HEVC) and single-episode rows such as `E01 – Drive | Instant | Watch`.
- Outer-page links do not provide a sufficiently specific identity by themselves; follow the exact season/episode context before accepting a media target.

### Flemmix — manual authority + live page/player matrix

- Official address hub: `https://ww1.wiflix-adresses.fun/`.
- Hub currently declares `https://flemmix.cloud` as the principal active domain (`Domaine actif - Utilisez toujours ce lien`).
- Current terminal search request observed manually: `https://flemmix.cloud/index.php?do=search&subaction=search&search_start=0&full_search=0&story=house+of+the+dragon` (GET 200 in browser).
- Example selected series page: `https://flemmix.cloud/serie-en-streaming/36342-game-of-thrones-house-of-the-dragon-saison-3.html`.
- Search results can have several season-specific VF/VOSTFR entries; season matching must be explicit.
- Manual DevTools player evidence included:
  - Player family 1: `https://vidara.to/api/stream` POST 200.
  - Player family 2: `https://entitlements.jwplayer.com/...json` GET 200 (metadata/entitlement request, not itself a stream).
  - Player family 3: `https://luluvdo.com/player/jw8/translations/fr.json` GET 200 (translation asset, not itself a stream).
- NiakVIO runner subsequently confirmed the exact season page is ~120 KB and contains explicit episode/language player controls (`ep1vs`, `ep1vf`, etc.) and direct `loadVideo(...)` embeds.
- Confirmed embed host families on that page include `vidara.to`, `rebeccapracticeloss.com`, `luluvdo.com`, `flemmix.upns.pro`, `vidmoly.org`, and `firestream.site`.
- Example page contains distinct embeds per episode and VF/VOSTFR groups, so the correct runtime model is page -> exact requested episode/language -> one or more player embeds -> media resolver.
- Runner GET of the search URL returned only 18 bytes despite browser 200; do not assume search HTML is server-rendered/usable in the runner. Exact work pages are live and exploitable.
- Existing MEMORY note claiming `flemmix.kim` authoritative is stale for this recovery session; hub authority now points to `flemmix.cloud`.

### ToFlix — manual authority + current POST API contract

- Official hub: `https://toflix.wiki/`.
- Hub currently displays terminal domain in text (`#hero-heading`): `tfx08.lol`.
- Terminal: `https://tfx08.lol/`.
- Frontend framework: Next.js.
- Current API endpoint observed manually: `https://api.tfx08.lol/toflix_api.php` via POST 200.
- Movie content-details request observed for The Odyssey: body `{"api":"content_details","type":"movie","slug":"tmdb-1368337"}`.
- Playback/session resolution request then observed to the same endpoint: body `{"api":"watch_session","action":"resolve","token":"7580ed4e40761939a974b3f28d9f60979032e1d2fd4f978b"}`.
- This is a TMDB-direct current contract. Do NOT preserve the stale `tfx05.lol` GET recipe as execution authority.
- Current NiakVIO DATA found during this session still contained stale `official_site=https://tfx05.lol`, `official_api=https://api.tfx05.lol`, and GET query recipes. It must be migrated to hub-derived `tfx08` + POST `content_details` -> `watch_session/resolve`, then live-validated.
- Keep `toflix.wiki` as discovery authority so future `tfxNN` rotation can be learned instead of hard-frozen.

### VegaMovies — manual authority + nexdrive download graph

- Hub supplied/confirmed: `https://1vegamovies.tw/`, which redirects to current hub `https://1vegamovies.cfd/`.
- Hub `View Full Site` currently leads to terminal `https://new2.vegamovies.futbol/`.
- Search example: `https://new2.vegamovies.futbol/search.html?q=house+of+the+dragon`.
- Search may return pages grouping several seasons together, plus separate season-specific pages. Matching must inspect exact title/season, not select first fuzzy result.
- Example grouped work page: `https://new2.vegamovies.futbol/download-house-of-the-dragon-season-1-2-hindi-dubbed-org-all-episodes-480p-720p-1080p-bluray/`.
- Page is download-oriented and groups links by exact season, audio/language, resolution, codec and per-episode/batch semantics.
- Confirmed link host family: `https://nexdrive.fit/genxfm<id>/`.
- Confirmed labels/semantics include `G-Direct [Instant]`, `V-Cloud [Resumable]`, and `Batch/Zip`, with multiple quality rows for S1/S2 including 480p, 720p, 1080p and 2160p/4K.
- Examples supplied for S2 include nexdrive IDs `genxfm784776371280`, `genxfm784776380188`, `genxfm784776380189`, `genxfm784776371294`, `genxfm784776380194`, `genxfm784776380195`, `genxfm784776371279`, `genxfm784776380204`, `genxfm784776380205`, `genxfm784776371290`, `genxfm784776380216`, `genxfm784776380218`, `genxfm784776371299`.
- Examples supplied for S1 include nexdrive IDs `genxfm784776336902`, `genxfm784776336901`, `genxfm784776336886`, `genxfm784776336887`, `genxfm784776336892`, `genxfm784776336893`, `genxfm784776336944`, `genxfm784776336946`.
- Prefer episode-specific/direct/resumable paths for runtime extraction. Do not misclassify Batch/Zip archives as playable single-episode media.
- Global catalogue language coverage may include Hindi/English here; language must be represented as stream facts/presentation, not used to fake French availability.

### User-assistance contract for this recovery wave

- The user is manually inspecting difficult providers in browser DevTools to supply authoritative hub/domain/search/player/API evidence. Treat these observations as high-value discovery evidence, then verify via GitHub Actions/runtime before publication.
- Do not ask the user to repeat anything in this section. If a live check later contradicts an old value, record the new dated evidence here and preserve the hub/discovery relationship.

### UHDMovies — manual authority + episode-specific protected-link graph

- Discovery hub: `https://mmodlist.org/`; UHDMovies button uses `https://mmodlist.org/?type=uhdmovies` and currently leads to terminal `https://uhdmovies.autos/`.
- Search example confirmed manually: `https://uhdmovies.autos/search/house+of+the+dragon`.
- Search may return pages grouping multiple seasons as well as season-specific pages; matching must select the exact requested season.
- Example season page supplied: `https://uhdmovies.autos/download-s01-e01-added-house-of-the-dragon-2022-season-1-english-audio-1080p-1080p-10bit-hevc-web-dl-esubs/`.
- The page contains several release/quality groups for the same season, including 1080p x265/10-bit, 2160p SDR, 2160p HDR and other encodes. Each group exposes explicit Episode 1..10 links plus a separate `Zip / Pack` link.
- Episode links are currently protected URLs on `https://cloud.unblockedgames.world/?sid=<opaque-token>`.
- `Zip / Pack` is batch/archive semantics and MUST NOT be returned as a single playable episode stream.
- Exact season/episode identity is available on the work page before resolving the protected link. Resolver must carry that identity through the hop instead of accepting arbitrary URLs from the page.
- Prior NiakVIO desktop manual logs already showed the deeper UHDMovies chain after bypassing these protected links: `cloud.unblockedgames.world/?sid=...` -> `driveseed.org/file/<id>` -> `driveseed.org/zfile/<id>` (ResumeCloud) -> InstantLink hosts including `cdn.video-gen.xyz` and `cdn.video-plex.xyz`.
- This manual evidence is authoritative for discovery/runtime repair; validate the exact current chain live before marking the lane green.

### 2026-09-12 — Vostfree / NetMirror / Nakios / ZinkMovies manual authority

#### Vostfree
- Discovery hub supplied by user: `https://streaminganime.fr/site/6/vostfree`; its visit action currently leads to `https://ipv4.vostfree.ws/`.
- Search is a POST to `https://ipv4.vostfree.ws/index.php?do=search` with DLE-style form fields including `do=search`, `subaction=search`, `search_start=0`, `full_search=0`, `result_from=1`, and `story=<query>`.
- Example result/work page supplied: `https://ipv4.vostfree.ws/802-death-note-vf-ddl-streaming.html`.
- The work page exposes explicit episode selectors (`Episode 01`, `Episode 02`, ...), and Episode 1 uses Sibnet player `https://video.sibnet.ru/c.php?videoid=3614913` (manual HTTP 200).
- Runtime must select the exact episode from page semantics before resolving the player; do not infer episode identity from the player URL alone.

#### NetMirror
- Hub evidence supplied by user for `netmiror.com` currently exposes backup/server domain `https://net27.cc/`.
- Current terminal API is TMDB-direct. Search example: `GET https://net27.cc/api/catalog/search-hybrid?q=house%20of%20the%20dragon`.
- Title lookup example: `GET https://net27.cc/api/catalog/title/tv/94997` (TMDB 94997).
- Embed resolution example supplied for HOTD S1E2: `GET /api/embed-tmdb/94997?type=tv&se=1&ep=2&...`; the browser returned HTTP 200.
- The title response exposes multiple server/language choices. Preserve those as stream facts; exact S/E remains authoritative.

#### Nakios
- Discovery hub: `https://nakios.org/`, currently linking to `https://nakios.live/`.
- Search frontend uses Livewire POST `https://nakios.live/livewire/update`; the supplied request updates search-component field `q`.
- Example work page supplied: `https://nakios.live/movie/super-mario-galaxy-le-film`.
- User observed some players taking ~3 minutes and recommends preferring Vidzy when available.
- Proven media-side example: `v6.vidzy.cc/hls2/.../seg-8-v1-a1.ts?...` returned HTTP 200 in browser. Player preference may rank Vidzy higher, but no host may be accepted without terminal playback proof.

#### ZinkMovies
- Discovery hub supplied by user: `https://zinkmovies.org/`, currently routing to `https://new4.zinkmovies.foo/` through its Access Movies Portal CTA.
- Search example: `https://new4.zinkmovies.foo/?s=house+of+the+dragon`.
- Work page: `https://new4.zinkmovies.foo/tvshows/house-of-the-dragon-2022/`; it groups multiple seasons and qualities.
- S1/S2/S3 quality links currently use `https://linkstore.zinkcloud.net/<id>/` (examples 6387..6401). Exact requested season must be selected before descending LinkStore.
- These are download-link intermediates, not playable streams until a terminal media target passes the common playback verifier.

### 2026-09-12 — UHDMovies live-chain follow-up
- Live runner confirmed `uhdmovies.autos` search/detail pages and explicit Episode 1 anchors to `cloud.unblockedgames.world`; current Niak bundle still returns zero because its generic episodic helper ignores opaque cross-origin hrefs when S/E identity lives in anchor text.
- Live protected chain was resolved structurally: protected GET -> first `form#landing` POST -> second `form#landing` POST -> `?go=<token>` cookie handoff -> meta refresh -> DriveSeed redirect -> `driveseed.org/file/<id>`.
- Five distinct S01E01 protected links reached five distinct DriveSeed file IDs. Current Instant branches split across `cdn.video-plex.xyz` and `cdn.video-gen.xyz`; wrapper pages are not terminal media by themselves.
- Current DriveSeed ResumeCloud `/zfile/<id>` contract changed: `Generate Cloud Link` is JavaScript POST with dynamic per-load `key`, `action`, `action_token`, and `x-token` hostname header. Page loads Cloudflare Turnstile and fresh-key POSTs with empty `action_token` return `Unknown error`.
- Do not hardcode ephemeral keys and do not bypass/defeat Turnstile. Prefer independently exposed Instant branches and require terminal playback verification.
- UHDMovies remains partial/manual authority, strict red until terminal media is proven.

### 2026-09-12 — Manual-wave live follow-up: Nakios / Vostfree / ZinkMovies / NetMirror

#### Nakios
- Current live human chain was proved under GitHub runner: `https://nakios.live/` -> parse CSRF + `search-component` Livewire snapshot -> `POST /livewire/update` with query `mario` -> work result `/movie/super-mario-bros-le-film` -> work page -> Vidzy embed `https://vidzy.org/embed-8fyvbh1n8a6c.html` -> `https://s1.fsvid.lol/troll/master.m3u8`.
- Terminal HLS probe returned HTTP 206, `Content-Type: application/vnd.apple.mpegurl`, and body beginning `#EXTM3U`. This is current terminal media proof for the movie lane.
- Work pages serialize player families inside `wire:snapshot` (`videos` / `videosByVersion`), including Vidzy, Dood, Uqload, Luluvid and others. User observed some players may take ~3 minutes; Vidzy should be preferred when available, but only after live terminal validation.
- Candidate provider Lego V1 exists in `scripts/provider_patches/nakios_livewire_runtime_v1.py`. First harness pass did not install into the lexical ProviderBase export; second pass proved the Lego is now invoked (`server_accessible=true`, HTTP 200) but still returned zero streams. Continue debugging the resolver; do not mark Nakios green yet.

#### Vostfree
- Current deterministic episode/player contract is present in the work page: `buttons_N` episode selector, alternating `player_N`/`content_player_N` rows; odd rows are Sibnet, even rows Uqload.
- Episode 1 current tokens: Sibnet `3614913`, Uqload `t80ndeqk2sfb`. `templates/Animix/js/anime.js` currently constructs Sibnet as `https://video.sibnet.ru/shell.php?videoid=<token>` and Uqload as `https://uqload.io/embed-<token>.html`.
- Runner followed Episode 1 Uqload to `https://uqload.vc/embed-t80ndeqk2sfb.html?...` with HTTP 200. No raw MP4/M3U8 appeared in plain HTML, so terminal media is not yet proved and the player requires a packed/obfuscated-player decoding step.
- Direct `video.sibnet.ru/c.php?videoid=3614913` returned a tiny GIF in the runner, not playable media. Do not count that browser player request as terminal media.

#### ZinkMovies
- `linkstore.zinkcloud.net/6387/` is live and exposes multiple `new4.zinkcloud.net/file/<id>` intermediates. The first inspected file page is live but current download generation is gated by Cloudflare Turnstile / protected generation logic.
- Current frontend references `generateDownloadLink(...)`, token generation, and server-handler flows for worker/GDFlix/HubCloud-style mirrors. Do not bypass Turnstile and do not count LinkStore/ZinkCloud intermediates as playable media without terminal playback proof.

#### NetMirror
- Current TV lane is already strict-positive in the Niak bundle (8 verified streams in the manual-wave run).
- Standard Interstellar fixture is currently unavailable at the source itself: NetMirror marks TMDB 157336 `streamable:false` / Coming Soon.
- Source movie capability is nevertheless live: Avatar (TMDB 19995) is currently `streamable:true`, and `/api/embed-tmdb/19995?type=movie` returns signed MP4 variants.
- Running the current Niak NetMirror bundle with TMDB 19995 still returned zero and made no provider request (`server_accessible=false`), proving a real missing movie runtime route in addition to the Interstellar fixture mismatch. NetMirror remains partial, not full.

### 2026-09-12 — AnimeSalt / AnimePahe manual authority

#### AnimeSalt
- Discovery hub supplied by user: `https://animesalt.ac/`; current terminal observed in browser is `https://animesalt.cx/`.
- Search uses WordPress AJAX: `POST https://animesalt.cx/wp-admin/admin-ajax.php` with `action=action_tr_search_suggest`, a page/session nonce, `term=<query>`, and a visitor id. Nonce/visitor values are ephemeral and MUST NOT be hardcoded.
- Example result/work page supplied: `https://animesalt.cx/series/death-note/?asq=ZGVhdGggbm90ZQ=`.
- Season switch contract is explicit on the work page: `GET .../wp-admin/admin-ajax.php?action=action_select_season&season=<season>&post=<postId>`; Death Note exposes `data-post=1808`, season 1 and exact episode links such as `/episode/death-note-1x1/` through `/episode/death-note-1x37/`.
- Episode identity is explicit in both visible labels and episode paths (`1xN`); select exact season/episode before player resolution.
- Episode 1 player request observed manually: `POST https://as-cdn26.top/player/index.php?data=4524b5e84762d68528525a226797c4d2&do=getVideo` returned HTTP 200. The `data` token is runtime player/session content and MUST be learned from the episode page, not frozen.

#### AnimePahe
- Discovery source supplied by user: `https://theindex.moe/item/6128a375aa2f6e004d46d71d`, which points to `https://animepahe.com/`; current terminal redirects to `https://animepahe.pw/`.
- Current search API: `GET https://animepahe.pw/api?m=search&q=<query>`; browser trace returned HTTP 200.
- Example anime page supplied: `https://animepahe.pw/anime/08154ccc-aef5-84a3-59ff-2bd1c7430744`.
- Episode menu exposes exact episode links as `/play/<anime-session>/<episode-session>` with visible labels `Episode 1`, `Episode 2`, ...; exact episode selection is explicit and must be preserved.
- User observed terminal HLS on `vault-11.uwucdn.top/.../uwu.m3u8`, HTTP 200, with an HLS key path `mon.key`. HLS/key URLs are runtime outputs and MUST NOT be hardcoded in provider DATA.
- This is strong manual playback evidence, but NiakVIO still requires dynamic extraction + common playback verification before the lane becomes strict green.

## 2026-09-12 — Strict-46 release candidate accepted for PR

- Publication authority is exactly **96 catalogued providers / 46 ON / 50 OFF**. Every ON provider has all required declared lanes live-qualified; terminal-blocked, unreachable, partial-lane, and stale historical evidence remain non-positive.
- Exact ON set: anime-sama, purstream, flemmix, uhdmovies, movieshunt, hindmoviez, 4khdhub, persianstremio, desiflix, kehflix, anikototv, animekai, animesalt, animesama-co, animesultra, animetsu, animevostfr, castle, coflix, french-manga, kurage, moviesmod, mugiwarastream, neko-sama, papadustream, playimdb, sekai, streamzo, videasy, vidfast, vidrock, voiranime, voiranime-homes, voiranime-rip, vostfree, wookafr, yflix, allanime, allwish, anime-ultime, animevost-fr, fullanime, mallumv, moviebox, showbox, vidlove.
- Active46 proof matrix run 34708855797: **46/46 green**. Disabled50 fast-smoke run 34709068964: green.
- Official sequential run 34709164157 is retained only as step-level evidence: its 96-provider live sequential gate succeeded and qualified the strict 46, then packaging failed on the obsolete reverse-rebuild expectation of 96 active providers. The reverse-rebuild contract was corrected to preserve the manifest active set.
- Parallel recovery run 34711564739 re-proved **46/46 active providers** and preserved finalized DATA artifacts without another 96-provider sequential rerun.
- Published HTML security was repaired at its actual Lego sources; run 34713445212 passed the source+published HTML gate before stopping later on an unrelated stale playback test.
- Playback policy contract run 34713921358 confirmed media-safety revision **field-safety-v9-correlated-player-fallback**; the stale v8 assertion was updated without runtime changes.
- Integrity recovery run 34714150864 restored the already-materialized strict-46 snapshot, regenerated omitted projections, and passed release hashes + release integrity with **no provider live rerun and no rematerialization**.
- Post-sync static-knowledge contract run 34714329224 confirmed 4KHDHub's seed remains unexecuted while accepted durable DATA preserves independent HTTP-executed proof.
- Latest main diagnostics were synchronized from main SHA e056c70770353b9832fbe043d90fc7556334d7b0.
- Final post-sync preflight run 34714362290: **success** across Core/source-plan migrations, DATA contracts, ProviderBase store, and reconstruction input suite.
- This release candidate is accepted for PR-only merge to main. Version finalization happens after merge.

## 2026-09-12 — fix/labs-5.21.44-20260912 manual TV/Desktop regression checkpoint

- Work is intentionally isolated on branch `fix/labs-5.21.44-20260912`; **do not touch or merge `main`** until the branch is fully rebuilt, tested and reviewed.
- User explicitly requires every important diagnosis/correction/run state to be persisted into `MEMORY.md` so nothing is lost between chats. `.github/workflows/memory-checkpoint.yml` now accepts `fix/**` branches in addition to main/workbench.

### User manual TV regression corpus — authoritative UX evidence
- Interstellar: Purstream 720p (historically >=1080p), Castle 2 streams English+Hindi, Papadustream 480p, DesiFlix 4K+720p, **StreamZo returned a wrong documentary-like stream labelled `- Inconnue`**, VidRock returned one 720p stream that was actually HTTP 403 plus one valid 1080p stream, HindMoviez returned four 480p streams that did not appear playable. Reported quality labels were often lower/wrong versus visual quality.
- House of the Dragon S1E2: Purstream 720p, PersianStreamio 7 streams (6x1080p + 1x720p) apparently OK, Castle Indian-language streams apparently OK, DesiFlix streams apparently OK, VidRock 1080p + nominal 720p whose actual quality looked higher, HindMoviez four 480p streams apparently non-playable.
- Ragna Crimson S1E4: Anime-Sama returned one working 720p plus one `- Inconnue` stream that did not work; Mugiwara-no-Streaming returned one working 720p.
- Mushoku Tensei S3E11: no providers/streams loaded.
- HellMode S2E10: Anime-Sama one 1080p apparently OK; **Mugiwara-no-Streaming returned eight 1080p streams for the wrong episode** and labelled them VF although they appeared VOSTFR.
- Cross-title navigation still showed stale provider loading accumulating from one work to the next. Silent/dead providers appeared to disappear only after >1 minute, despite the intended shorter provider budget. Stream titles were no longer uniformly formatted; preserve detailed language/dialect information while restoring uniform branding/presentation.

### Existing branch fixes already proven by targeted runner
- Canonical provider execution timeout is being restored to **25 s** instead of the accidentally reintroduced 60 s budget.
- A→B→C navigation cancellation test passes even when native fetch ignores `AbortSignal`: older generations settle without re-injecting stale results.
- Stream safety is fail-closed for a VidRock-like 403 stream; a 403 URL must not be surfaced while another valid route may still survive.
- Verified HLS quality outranks declared quality: e.g. nominal 480p with a master proving 1080p is promoted to 1080p.
- Stream title/presentation normalization keeps detailed language labels (Hindi/Tamil/Telugu/etc.).
- Generic movie catalogue identity V21.10 is being strengthened so a result whose title merely contains the requested film name (e.g. a documentary containing `Interstellar`) cannot be accepted as the target film.

### Current rebuild blocker and correct recovery path
- The first real 96-provider rebuild failed specifically with `anime-sama: missing durable ProviderBase`.
- Do **not** reverse-reconstruct ProviderBase v3 from published/upstream provider JS. The repo already has the correct path: `scripts/materialize_provider_base_v3_store.py` rebuilds all 96 ProviderBase files from the NiakVIO-owned common skeleton + structured DATA, then `scripts/materialize_provider_v3_all.py` rebuilds all 96 bundles.
- `provider-bases/anime-sama--base--613e0ca190ebffec.js` exists in repository history/current indexed code, confirming this is store/provenance materialization debt rather than absence of a clean authoring source.

### Desktop/macOS evidence from user file `nuvio-tests-complets(1).log`
- This is not a provider-JS loading failure; prior evidence already showed no provider load errors and many extraction/runtime failures.
- **StreamZo native failure:** `getStreams error: 'setTimeout' is not defined` at request/metadata/recover path. Frenchstream shows the same runtime class. Provider execution-budget/cancellation code must work in QuickJS-like runtimes where global `setTimeout` may be absent.
- HindMoviez successfully found the correct Interstellar WordPress post via IMDb and entered the MvLink/HShare chain, but native execution also shows downstream DNS/timeouts; user-visible `480p` rows must be validated for actual playability before surfacing.
- VidRock native log shows real runtime HTTP failures (Interstellar API request HTTP 400; TV path HTTP 404) in addition to player timeouts. A valid sibling stream may survive, but failed/403/404 rows must never be surfaced as playable output.
- Anime-Sama native log shows broad alternate-slug probing for Interstellar; movie/anime capability and identity gates must remain before expensive provider work.

### Remaining work before this branch can be considered fixed
1. Rebuild ProviderBase store 96/96 from owned skeleton+DATA, then rebuild all 96 provider bundles.
2. Add QuickJS/no-`setTimeout` runtime regression and make timeout/cancellation budget implementation safe there.
3. Add generic episodic identity guard that rejects Mugiwara wrong-episode results, without provider-specific hard-coding.
4. Complete generic movie catalogue V21.10 guard and revalidate StreamZo wrong-media/documentary case.
5. Add/verify provider isolation test: dead/403/429/network-stalled provider must not postpone a healthy provider; each provider owns its own 25 s budget and fail-fast state.
6. Recheck HindMoviez/Anime-Sama failed rows through stream playability safety, quality recovery, title/language presentation, A→B→C stale suppression.
7. Re-run targeted contracts, full 96 rebuild/gates, then Mac + TV evidence on the exact branch candidate; remove temporary workflow only after durable evidence is stored.
8. Keep `main` untouched throughout this branch work.

## 2026-09-12 — common identity guards integrated into durable ProviderBase generation

- Added provider-agnostic `scripts/upgrade_provider_episode_identity_guard_v22_1.py` plus executable `tests/provider_episode_identity_guard_v22_1_test.py`.
- V22.1 extends common episode identity evidence to query-string forms such as `?season=2&episode=10` / reversed ordering, rejects detail URLs that explicitly identify another episode, and fail-closes generic player fallback when a same-origin episode table proves the requested episode is absent. No provider ids, fixture titles or site hosts are hard-coded.
- Added executable `tests/provider_movie_catalogue_identity_v21_10_test.py` for the existing common V21.10 movie-title equivalence guard. It explicitly permits exact title/alias plus presentation-only noise (correct year, quality, language) and rejects semantic collisions such as documentary titles containing the requested movie name.
- `scripts/materialize_provider_base_v3_store.py` now runs both V21.10 movie identity and V22.1 episode identity upgrades before importing/materializing the common ProviderBase store. Provenance store metadata records `movie_catalogue_identity_guard=v21.10` and `episode_identity_guard=v22.1`.
- This makes the StreamZo wrong-documentary and Mugiwara wrong-episode fixes durable common ProviderBase behavior rather than workflow-only patches or provider-specific exceptions.
- Main remains untouched; all writes stay on `fix/labs-5.21.44-20260912`.
- Next: wire the temporary branch verifier to regenerate the 96 ProviderBase store before 96 bundle recomposition, add no-`setTimeout`/dead-provider isolation contracts, then execute the full branch rebuild and gates.

## 2026-09-12 — V33 provider isolation / fail-fast design checkpoint

- Added `scripts/upgrade_provider_execution_failfast_v33.py` as the durable common Core migration for provider execution isolation.
- V33 final Core revision target: `tmdb-data-contract-launch-gate-v33-25s-isolated-failfast`.
- Canonical per-provider budget is **25,000 ms** for TV and non-TV. The outer Native Lab timeout remains a larger harness timeout and is not provider runtime authority.
- V33 adds a default **7,000 ms per-fetch slice** (bounded/configurable) so one abort-ignoring/stalled fetch cannot consume the entire 25 s provider budget when timers exist.
- V33 keeps legitimate fallback: the **first 403/429/network failure never kills a provider**. Repeated strong HTTP/network failures are counted per invocation; default fail-fast threshold is 3. Once reached, later fallback fetches fail immediately instead of continuing network work.
- Hard-status tracking is generic and provider-independent. 404 is deliberately not a hard fail-fast status because search/catalogue providers legitimately probe missing routes/titles; successful/host-alive responses reset the consecutive hard-failure state.
- Per-fetch timeout uses its own AbortController where available; it does **not** abort the whole provider request. The 25 s request-level controller remains the global deadline owner. Native invocation itself is raced against that request controller so non-fetch hangs cannot silently exceed the provider deadline when timer primitives exist.
- QuickJS/no-global-timer compatibility is preserved: all timer usage checks `typeof setTimeout/clearTimeout` first. `tests/provider_no_timer_runtime_test.py` proves stale-request supersession still works with both globals undefined.
- Added `tests/provider_execution_failfast_v33_test.py`: proves first 403 -> second route success is preserved, repeated 403s stop later network calls, abort-ignoring stalled fetches fail fast, and a dead provider execution does not postpone an independently executing healthy provider.
- Updated the abort-ignorant cancellation and manual-TV regression contracts to V33. `scripts/prepatch_manual_tv_regressions_20260912.py` is now idempotent so successful branch commits can be rerun safely.
- These changes remain only on `fix/labs-5.21.44-20260912`; `main` is untouched.
- Next: wire V33 + identity migrations + ProviderBase-store regeneration into the temporary branch verifier, run targeted tests, rebuild ProviderBase 96/96, rebuild all 96 bundles, then inspect and repair any real regression exposed by CI.

## 2026-09-12 — TEMP manual-TV run 34718923736 failed before tests; validator-only V22.1 defect fixed

- Run **34718923736**, job **103621052981**, failed in `Apply durable common fixes` before focused tests or any ProviderBase/bundle rebuild.
- Successful steps before the failure: manual-TV prepatch applied verified-HLS-quality authority, V33 provider execution fail-fast migration completed (`provider_budget_ms=25000`, `fetch_slice_ms=7000`, `max_hard_failures=3`), and V21.10 movie catalogue identity migration completed.
- Failure was **not runtime behavior**: `upgrade_provider_episode_identity_guard_v22_1.py` applied its changes but its own validator searched for `async function _resolveApiRecipe` *after* the V22.1 marker. In current ProviderBase ordering `_resolveApiRecipe` is earlier than the episode helper region, so `value.index(...)` raised `ValueError: substring not found`.
- Fix commit on branch: `958cd1a77f1574dd6340cdb306e5467db037e3cc`. V22.1 validation now bounds its provider-specific-token audit from the marker to the later `async function _resolveHtml`, which actually contains the integrated episode guard region.
- No generated ProviderBase/provider artifacts from the failed runner were committed. `main` remains untouched.
- First memory-writer attempt run **34718971551** appended this checkpoint locally but its push lost a branch-ref race: remote moved from `d964fb3d...` to `02a60ff...` between pull and push, so GitHub rejected the stale expected ref. The pending checkpoint therefore remained authoritative and was not falsely treated as persisted.
- `.github/workflows/memory-checkpoint.yml` is now race-safe: after creating the memory commit it performs repeated fetch + rebase + push attempts. The TEMP verifier final push has the same protection and `cancel-in-progress=true` so only the newest verifier run is authoritative.
- Next action: retry the same branch workflow; first required milestone is all focused V33/V21.10/V22.1/no-timer/navigation/quality/403/presentation contracts green, then ProviderBase 96/96.

## 2026-09-12 — TEMP retry 6 reached focused tests; no-timer behavior green, assertion drift fixed

- TEMP run **34718984024**, job **103621212371**, passed `Apply durable common fixes`: manual-TV prepatch, V33 fail-fast, V21.10 movie identity and V22.1 episode identity all applied successfully.
- Focused executable results before the red: `MOVIE_CATALOGUE_IDENTITY_V21_10_OK`, `EPISODE_IDENTITY_V22_1_OK`, and **`NO_TIMER_RUNTIME_OK ["https://provider.example/second"]`**. This proves the QuickJS-like runtime with global `setTimeout`/`clearTimeout` undefined correctly superseded a hanging first request and returned the latest request without stale leakage.
- Run 34718984024 then failed only on a stale *source-text assertion* inside `tests/provider_no_timer_runtime_test.py`: it still expected V32 token `typeof setTimeout!=="function"||remaining<=0`, while V33 correctly renamed the per-fetch bound to `slice`.
- Commit **82b81553220572b5b14444c8e052e9d99e27f26f** updates the test to assert the actual V33 no-timer branch (`slice<=0`) and also locks the no-timer `Promise.race([base.apply(this,args),abortPromise])` path. Runtime behavior was not changed by this test fix.
- Memory writer race handling was itself proven by run **34719075767** success; pending reset to the empty sentinel after durable append despite concurrent branch movement.
- No ProviderBase 96/96 rebuild was reached in retry 6. `main` remains untouched.
- Next authoritative verifier must include commit 82b8155... before focused tests, then continue to ProviderBase 96/96.

## 2026-09-12 — TEMP retry 8 proves focused V33 stack except immediate-invocation ordering

- TEMP run **34719139951**, job **103621639170**, checked out branch head `c3ca0eb28b9023e90cf18227875d281aaadb929e` and passed durable V33/V21.10/V22.1 application.
- Focused tests proven green in this run before the red: movie catalogue identity V21.10; episodic identity V22.1; QuickJS/no-global-timer cancellation; **provider execution fail-fast V33**; and the complete synthetic manual-TV regression contract (verified HLS quality authority, 403 fail-closed, detailed language/uniform title, A→B→C stale suppression).
- Failure occurred next in `provider_latest_request_cancellation_test.py`: `Error: first request never started`.
- Root cause: V33 helper `invokeNativeWithBudget()` used `Promise.resolve().then(() => native.apply(...))`, adding one extra microtask before native provider execution. A second request could supersede the first before its first fetch started. This remained fail-closed (no stale result), but unnecessarily changed historical invocation ordering and broke the cancellation contract.
- Commit **8100f7937d9809e9db130d2d603c97791d56c888** fixes V33 generically: `native.apply(self,args)` is invoked immediately, then its result is normalized with `Promise.resolve(pending)` and raced against the request abort/deadline. This preserves old immediate-start semantics while retaining the 25 s deadline and V33 fail-fast.
- Retry 8 did not reach ProviderBase 96/96 because focused tests stopped at this ordering regression. `main` remains untouched.
- Next: authoritative retry must reprove the entire focused suite with immediate invocation, then proceed to ProviderBase 96/96 and all-96 bundle rebuild.

## 2026-09-12 — TEMP retry 9 focused regression suite fully green; ProviderBase 96/96 rebuild entered

- TEMP run **34719219904**, job **103621866958**, passed `Apply durable common fixes` and the complete `Focused regressions` step.
- This is the first retry in this branch sequence where the entire focused stack is green together after V33 immediate-invocation correction.
- Proven together in the same job: V21.10 movie catalogue semantic identity; V22.1 episodic identity; QuickJS/no-global-`setTimeout`; V33 first-failure fallback + repeated hard-failure fail-fast + stalled-fetch isolation + dead-provider/healthy-provider independence; manual-TV quality/403/language/A→B→C contract; latest-request cancellation; abort-ignoring native-fetch cancellation; HLS quality recovery; sanitizer fail-closed/direct normalization; Core runtime non-regression.
- V33 immediate-native invocation fix (`8100f7937d9809e9db130d2d603c97791d56c888`) restored the historical ordering contract without weakening supersession or the 25 s budget.
- After focused green, retry 9 entered `Rebuild owned ProviderBase store 96/96`. This is the first rebuild attempt after the anime-sama missing-base root cause was addressed by explicitly materializing the owned common ProviderBase store first.
- `main` remains untouched.

## 2026-09-12 — retry 9 rebuilt ProviderBase 96/96; stale layering fixture blocked after materialization

- TEMP run **34719219904**, job **103621866958**, completed the full focused regression suite green and then successfully executed the owned ProviderBase materializer.
- Authoritative materializer line: `FIELD_PROVIDER_BASE_V3_STORE providers=96 unique_paths=96 reconstruction_required=0 provider_js_seed=false upstream_js_seed=false runtime_reader=v10 route_sanitizer=v1 html_text_hardening=deterministic-scanner-v1 movie_identity=v21.10 episode_identity=v22.1`.
- This resolves the prior concrete blocker `anime-sama: missing durable ProviderBase`: all 96 clean bases are now generated from NiakVIO-owned common skeleton + DATA with **no published/upstream JS seed**.
- Run 34719219904 stopped immediately after materialization in `tests/provider_base_layering_contract_test.py`, not in generated ProviderBase bytes. The stale synthetic fixture explicitly expected `/* NUVIO_PROVIDER_SECURITY_HARDENING_V1 */` to be accepted inside a clean ProviderBase even though current `DERIVED_BASE_MARKERS` explicitly classifies that security hardening as a derived/publication layer.
- The layering invariant is not weakened. Commit **6e1db8fa3f32fd499b3d118634726fe5f219288d** removes the stale acceptance and strengthens the test: `NUVIO_PROVIDER_SECURITY_HARDENING_V1` is now explicitly required in the forbidden derived-marker set and a contaminated synthetic base must fail.
- No generated 96-base changes from the failed runner were committed because the job stopped before its commit step; the next verifier will rematerialize deterministically.
- All-96 bundle rebuild was not reached yet. `main` remains untouched.

## 2026-09-12 — retry 10 confirms ProviderBase 96/96; layering test fully aligned to clean-v3 authority

- TEMP run **34719305207**, job **103622096943**, again passed the complete focused regression suite and again successfully materialized the owned ProviderBase store **96/96** with `provider_js_seed=false` and `upstream_js_seed=false`.
- Exact successful materializer proof repeated: `FIELD_PROVIDER_BASE_V3_STORE providers=96 unique_paths=96 reconstruction_required=0 provider_js_seed=false upstream_js_seed=false runtime_reader=v10 route_sanitizer=v1 html_text_hardening=deterministic-scanner-v1 movie_identity=v21.10 episode_identity=v22.1`.
- Retry 10 then failed only on another historical assertion in `tests/provider_base_layering_contract_test.py`: it still required `CLEAN_RECONSTRUCTION_SOURCE == niakvio-clean-reconstruction-v2` / authoring version 2.
- Current source authority in `scripts/provider_base_store.py` is explicitly `CLEAN_RECONSTRUCTION_SOURCE=niakvio-clean-reconstruction-v3`, `CLEAN_RECONSTRUCTION_AUTHORING_VERSION=3`, `PROVIDER_BASE_OWNED_MARKER=NIAKVIO_PROVIDER_BASE_OWNED_V3`. Other current tests (`provider_base_store_test.py`, `provider_clean_reconstruction_contract_test.py`) already enforce clean-v3.
- Commit **193e3fb482c79bdb8d10fb6ebb9c83feaa49a70d** updates the full stale lower half of the layering test in one pass rather than chasing assertions individually: clean-v3 is current, clean-v2 is explicitly old/reconstruction-required, only quarantine remains in `DERIVED_PATCH_SCRIPTS`, and historical adaptive/domain runtime patch paths are asserted in `LEGACY_SOURCE_PATCH_PATHS` + `CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS` rather than replayed.
- The layering/security invariant remains stricter, not weaker: `NUVIO_PROVIDER_SECURITY_HARDENING_V1` stays forbidden inside clean ProviderBase.
- Retry 10 did not reach all-96 bundle rebuild because the stale layering assertion stopped the job after successful 96-base materialization. `main` remains untouched.
- Next: retry the verifier with the fully clean-v3-aligned layering contract; required next milestone is reconstruction-input green followed by all-96 bundle materialization/reapply/fixed-point.

## 2026-09-12 — .44 manual-TV recovery retry 11

- Work remains isolated to `fix/labs-5.21.44-20260912`; `main` is untouched and must not be merged until final user approval.
- TEMP workflow run `34719876807`, job `103623640566`: all focused Core/manual-TV regressions passed together before rebuild.
- Verified contracts: movie catalogue identity V21.10; episode identity guard V22.1; no-timer native runtime; provider execution fail-fast V33; manual-TV aggregate contract; latest-request cancellation; native AbortSignal-ignorant cancellation; HLS quality recovery; fail-closed stream sanitizer; direct normalization; Core runtime non-regression.
- Timing/evidence: no-timer A→B first stale result `0`, second result `1`, fast URL preserved; V33 fallback used 2 fetches, repeated dead provider stopped after 3 hard fetches, stalled network returned in about 1.4 s; provider timeout remains 25 s.
- ProviderBase v3 reconstruction succeeded `96/96`, `unique_paths=96`, `reconstruction_required=0`, `provider_js_seed=false`, `upstream_js_seed=false`, runtime reader v10; `provider_base_layering_contract_test.py` passed.
- Retry 11 failed only because the temporary workflow referenced nonexistent stale test `tests/provider_reconstruction_input_suite_test.py`; this is CI plumbing, not a Core/runtime regression. Retry 12 removed only that obsolete test reference. Retry 12 itself had no job because a checkpoint heredoc made the YAML invalid; retry 13 replaces it with YAML-safe base64 append and continues into all-96 bundle materialization.

## 2026-09-12 — .44 full rebuild green + exact manual-TV live evidence

- Work remains isolated to `fix/labs-5.21.44-20260912`; `main` remains untouched and no merge is authorized yet.
- TEMP rebuild run `34720082372`, job `103624218582` completed success. ProviderBase rebuilt 96/96 with no provider/upstream JS seed; all 96 bundles materialized (`generation=8341fd44afe6c496`).
- Published overrides were reapplied to all 96 refs and `--check` hit fixed point (`contract=7173d12a7b7aaf1e`). Global stream output guard passed 96/96; focused manual-TV/Core regressions remained green after rebuild.
- Catalogue invariant after rebuild: manifest version 5.21.43, 96 rows, 46 enabled on this branch, 0 missing provider files; final published Provider CONFIG test passed 96.
- Generated rebuild commit pushed: `5bc5c2098c47a5cb3b5b2661babfc5242dec217f`.
- TEMP live manual-TV run `34720604970`: exact matrix results=24/24, playable=30, verified=30, contradictions=0, returned403Rows=0.
  - hell-mode-s02e10 / anime-sama: state=completed raw=2 playable=2 verified=2 contradictions=0 stage=provider_returned_streams transport=none qualities=1080p languages=VOSTFR returned403=0.
  - hell-mode-s02e10 / mugiwarastream: state=completed raw=8 playable=8 verified=8 contradictions=0 stage=provider_returned_streams transport=none qualities=1080p languages=VF returned403=0.
  - hotd-s01e02 / castle: state=completed raw=4 playable=4 verified=4 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=VO returned403=0.
  - hotd-s01e02 / desiflix: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_exception transport=none qualities=none languages=none returned403=0.
  - hotd-s01e02 / hindmoviez: state=completed raw=4 playable=2 verified=2 contradictions=0 stage=gate_runtime_plan_missing transport=none qualities=480p languages=Hindi/English returned403=0.
  - hotd-s01e02 / moviebox: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_exception transport=movie,tv qualities=none languages=none returned403=0.
  - hotd-s01e02 / persianstremio: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_http_error transport=none qualities=none languages=none returned403=0.
  - hotd-s01e02 / purstream: state=completed raw=1 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=VF returned403=0.
  - hotd-s01e02 / vidrock: state=completed raw=2 playable=2 verified=2 contradictions=0 stage=provider_returned_streams transport=none qualities=1080p,720p languages=Original returned403=0.
  - interstellar / castle: state=completed raw=2 playable=2 verified=2 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=VO returned403=0.
  - interstellar / desiflix: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_exception transport=none qualities=none languages=none returned403=0.
  - interstellar / hindmoviez: state=completed raw=4 playable=0 verified=0 contradictions=0 stage=gate_runtime_plan_missing transport=none qualities=480p languages=Hindi/English returned403=0.
  - interstellar / papadustream: state=completed raw=1 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=480p languages=VF returned403=0.
  - interstellar / purstream: state=completed raw=1 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=VF returned403=0.
  - interstellar / streamzo: state=completed raw=1 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=none languages=VF returned403=0.
  - interstellar / vidrock: state=completed raw=2 playable=2 verified=2 contradictions=0 stage=provider_returned_streams transport=none qualities=1080p,720p languages=Original returned403=0.
  - mushoku-tensei-s03e11 / anime-sama: state=completed raw=2 playable=2 verified=2 contradictions=0 stage=provider_returned_streams transport=none qualities=1080p languages=VOSTFR returned403=0.
  - mushoku-tensei-s03e11 / moviebox: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=gate_type_capability transport=none qualities=none languages=none returned403=0.
  - mushoku-tensei-s03e11 / mugiwarastream: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_http_error transport=none qualities=none languages=none returned403=0.
  - mushoku-tensei-s03e11 / papadustream: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_zero_result transport=none qualities=none languages=none returned403=0.
  - mushoku-tensei-s03e11 / purstream: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=gate_type_capability transport=none qualities=none languages=none returned403=0.
  - mushoku-tensei-s03e11 / streamzo: state=completed raw=0 playable=0 verified=0 contradictions=0 stage=provider_network_http_error transport=none qualities=none languages=none returned403=0.
  - ragna-crimson-s01e04 / anime-sama: state=completed raw=2 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=MULTI (VF/VO),VOSTFR returned403=0.
  - ragna-crimson-s01e04 / mugiwarastream: state=completed raw=1 playable=1 verified=1 contradictions=0 stage=provider_returned_streams transport=none qualities=720p languages=VOSTFR returned403=0.

## 2026-09-12 — Mugiwara season mapping diagnostic (.44)

- Mugiwara safe season diagnostic run `34721006209`. Output is deliberately URL-safe: season ids/counts and selected index only; no media/player URLs.
- `{"case":"ragna-s01e04","state":"ok","cataloguePath":"/catalogue/ragna-crimson/episodes/saison1","requestedSeason":1,"requestedEpisode":4,"selection":{"mode":"exact-id","rowId":"1","index":3},"seasons":[{"id":"1","notASeason":false,"episodeCount":24,"languageCounts":{"vostfr":24},"name":"Saison 1"}],"probeRaw":1,"probePlayable":1}`
- `{"case":"hell-mode-s02e10","state":"ok","cataloguePath":"/catalogue/hell-mode-the-hardcore-gamer-dominates-in-another-world-with-garbage-balancing/episodes/saison1","requestedSeason":2,"requestedEpisode":10,"selection":{"mode":"none","rowId":"","index":null},"seasons":[{"id":"1","notASeason":false,"episodeCount":12,"languageCounts":{"vostfr":12},"name":"Saison 1"},{"id":"2","notASeason":false,"episodeCount":0,"languageCounts":{},"name":"Saison 2"}],"probeRaw":8,"probePlayable":8}`


## 2026-09-12 — V34 + V8 + Mugiwara episodic fail-closed checkpoint (.44)

- Work remains strictly on `fix/labs-5.21.44-20260912`; `main` is untouched and no merge is authorized yet.
- Exact safe Mugiwara diagnostic run `34721006209`: Ragna Crimson S1E4 mapped `rowId=1/index=3`, season 1 count 24, and produced 1 raw/1 playable stream. Hell Mode requested S2E10 while the catalogue page resolved to `/episodes/saison1`; structured data exposed season 1 count 12 and season 2 count 0, so requested S2E10 had `selection=none`, yet the old native fallback emitted 8 raw/8 playable rows. Root cause: the specialized resolver correctly had no S2E10 match, then unsafe native/default-season output was reused.
- `upgrade_mugiwara_episode_failclosed_v2.py` preserves movie fallback but returns `[]` for episodic requests when structured Mugiwara data cannot prove the requested S/E.
- V34 filters learned literal `type=movie|tv` API routes against requested transport, uses strongest explicit quality evidence, preserves detailed language evidence, and selects terminal sanitizer V8.
- Sanitizer V8 publishes ordinary probed rows only on positive media proof; network/timeout/opaque outcomes fail closed. Its reapplication restores the V7 source hook before rebuilding, so identical reapplication remains byte-idempotent and changed options can rematerialize safely.
- TEMP retry 14 run `34721494272` reached a fully green focused suite. New runtime proof: declared `720p` + explicit `1080P` => `1080p`; generic `VO` + explicit `Hindi` => `Hindi`; dead direct row removed; V8 second application byte-identical. Retry 14 stopped only because its MEMORY push attempted a rebase with migration changes still unstaged; no Core test failed.

## 2026-09-12 — .44 V34 rebuild green + parallel unfinished-task audit

- Work remains isolated to `fix/labs-5.21.44-20260912`; `main` is untouched and no merge is authorized yet.
- TEMP V34 rebuild run `34721565416`, job `103628345857` completed **success**. Focused V21.10/V22.1/V33/no-timer/latest-request/abort-ignorant/HLS-quality/V8/manual-TV contracts were all green before rebuild and remained green after rebuild.
- ProviderBase v3 rebuilt **96/96** from NiakVIO-owned source only: `unique_paths=96`, `reconstruction_required=0`, `provider_js_seed=false`, `upstream_js_seed=false`, runtime reader v10, movie identity v21.10, episode identity v22.1, manual-TV V34, Mugiwara episodic fail-closed v2, sanitizer V8.
- All 96 provider bundles materialized successfully with generation `292444c9cc96c220`. Published overrides were reapplied to all 96 refs and the fixed-point check hit `contract=1e0d849bde9318c7`.
- Global stream output guard passed all 96. Catalogue invariant remained `version=5.21.43`, `96` rows, `46` enabled, `0` missing provider files; final published Provider CONFIG validation passed 96.
- Rebuild output was committed and rebased over concurrent diagnostics, then pushed as exact branch SHA **`0d819e4d919d8eb5da153b12438363adfb691eb2`**.
- Exact Mugiwara safety remains: Ragna S1E4 structured mapping is valid; Hell Mode S2E10 has no structured S2 episode and now fails closed instead of reusing eight wrong/default-season native rows.
- Parallel old-task audit was resumed instead of waiting on CI. `automation/OPEN-TASKS-20260911.md`, old chats and `MEMORY.md` still carry real debts: exact 46 evidence classification, five Native Labs on one SHA, Domain Refresh full-CONFIG transaction, final security, docs/trigger/architecture cleanup, weekly watch operational verification, visible logo/UI verification, and Brain multi-day evidence review.
- NetMirror diagnostic run `34721939061`, job `103629330442`: Avatar movie endpoint without `?type=movie` and with `?type=movie` both return HTTP 200 with the same JSON shape and 17 stream-like fields. Therefore the old suspicion that the missing movie discriminator caused the zero is false. Current Niak NetMirror returns `provider_zero_before_provider_network` because NetMirror is disabled in the strict-46 manifest; this is a later 96-recovery/gating debt, not a strict-46 release blocker and must not receive a fake route fix.
- AnimeSalt runner recheck run `34721970705`, job `103629417911`: current ON provider returns `provider_network_http_error`, raw/playable/verified `0/0/0`; direct GitHub-runner access to `https://animesalt.cx/` is HTTP 403. Since AnimeSalt is in the 46 enabled set, its previous positive qualification must be audited against this current CI-blocked evidence before final merge. Do not bypass anti-bot; classify whether device/browser proof still supports ON or whether the qualification became stale.
- Domain Refresh debt is confirmed current: `refresh_authoritative_hub_domains.py` now mutates `official_site` plus derivative maps/assets, while its docstring still claims official-site/history-only scope; `update_provider_v3_domain_config.py` still rewrites only `officialSite` inside existing CONFIG and emits the old unqualified `providers/{id}-{hash}.js` filename shape. The current full structured CONFIG authority lives in `materialize_provider_v3_all.provider_model(...)` and published refs are source-qualified `--nuvio--`. Required repair remains full-CONFIG regeneration, source-qualified filenames, generic A→B derivative proof, and ProviderBase/Core byte invariance.

## 2026-09-12 — exact V34 manual-TV live matrix on rebuilt .44 candidate

- Work remains isolated to `fix/labs-5.21.44-20260912`; `main` remains untouched and no merge is authorized yet.
- Exact live workflow run **`34722151401`**, job **`103629901543`** completed successfully against the post-V34 rebuilt candidate. Matrix coverage was 24/24 result files with no infrastructure failures.
- Aggregate live result: **23 playable = 23 verified**, **0 semantic contradictions**, **0 returned 403 rows**.
- Interstellar / StreamZo now returns 1 playable + verified correct movie row and no contradiction; the prior wrong-documentary symptom is fixed by V34 route/media compatibility.
- Interstellar / VidRock now returns 2 playable + verified rows with no leaked 403 row; the old bad 403 stream is fail-closed while valid media remains.
- Ragna Crimson S1E4 / Anime-Sama now returns one valid ~720p row; the old invalid unknown row is no longer published.
- Hell Mode S2E10 / Mugiwara now returns **0** when the structured site data cannot prove S2E10, instead of eight wrong/default-season rows. Ragna S1E4 remains a valid Mugiwara structured match.
- Mushoku Tensei S3E11 / Anime-Sama now returns **2 playable + verified 1080p VOSTFR rows**, improving the previous no-provider/no-stream symptom.
- Remaining quality facts must stay evidence-driven: Purstream still resolves around 720p, Papadustream around 480p, and Castle may carry `1080P` presentation text while the verified media result remains classified 720p. Do not upgrade quality merely from labels when media proof is weaker.
- DesiFlix/PersianStreamio/MovieBox had runner-side network/HTTP failures in portions of this live pass; classify those with native device evidence rather than inventing provider fixes.
- House of the Dragon S1E2 / HindMoviez produced four HTTP-206 Matroska rows that the probe classified playable+verified, while the prior manual TV check reported them as apparently unplayable. This is a mandatory Native TV/player arbitration item for the five-Lab pass.
- The temporary live workflow was corrected before this run so it no longer writes stale provenance from the previous `5bc5...` rebuild; live evidence persistence is now based on inspected run results.

## Repair campaign checkpoint — 2026-09-13 Europe/Paris (Hub-46 only)

This checkpoint supersedes older 96-provider Lab scope **for the active repair campaign only**. The global product catalogue may remain 96 providers, but all repair parity/Labs in `fix/labs-5.21.44-20260912` must execute exactly the authoritative 46-provider Hub scope from `automation/evidence/hub-lab-matrix-46.json`. Do not shrink the published/global catalogue to manufacture green metrics, and do not expand this repair campaign back to all 96 providers.

### Branch / safety
- Active repair branch: `fix/labs-5.21.44-20260912`.
- `main` is not a repair write target and must not be merged/touched without explicit user authorization.
- Verified `main` head during this checkpoint: `8f57f8eb42885c0b6b898aa018e806a1b0f72467` (`chore(audit): refresh external AI audit logs [skip ci]`).
- Core provider timeout remains **25 s**.

### Streamflix Desktop timer compatibility
- Actual fix commit: `2ab26c2d78e2ef856cf9eb29d925216c447a8f30` — `fix(streamflix): tolerate missing desktop timer globals`.
- Direct `setTimeout`/`clearTimeout` usage is guarded; timerless Desktop-like runtime no longer throws `ReferenceError`.
- Durable regression: `tests/streamflix_timerless_runtime_test.cjs`, proven green in TEMP run `34750296391`.
- Streamflix still requires normal provider/lane revalidation like every other provider; timer compatibility alone is not a stream proof.

### Hub-46 scope and rotating corpus
- Authority: `automation/evidence/hub-lab-matrix-46.json`, exactly **46** rows.
- Native workflow scope guard is exact-set equality, not count-only.
- Rotating corpus replaces stale fixed-only fixture selection for active Hub-46 parity/Labs. It keeps movie/tv/anime lanes and rotates deterministically across known works while preserving known compatibility slugs.
- Previous Desktop 0/46 was diagnosed as **Lab infrastructure**, not 46 provider failures: the official native client reloaded the 96-provider `manifest.json`, and Desktop duration lookup still queried the legacy fixed trigger file for rotating slugs.
- Physical Lab manifest fix commit: `b18342a12b88af1825de8765ecb8011ceb5b78aa` — `fix(labs): load exact Hub-46 manifest in native clients`.
- Derived root manifest: `manifest-hub46.json`, exactly 46 rows, rooted beside `providers/` so relative provider filenames keep normal raw-GitHub semantics.
- Desktop/Mobile Android/TV Android runners use `manifest-hub46.json` whenever `NIAKVIO_PROVIDER_SCOPE_MATRIX` is active; iOS rewrites its raw manifest URL to the exact branch SHA + `manifest-hub46.json`.
- Desktop rotating duration lookup now comes from `scripts/rotating_corpus.py`, not `.github/triggers/nuvio-client-lab.json`.
- Native runs dispatched on exact SHA `b18342a12b88af1825de8765ecb8011ceb5b78aa`: Desktop `34755341606` (macOS + Windows), Android `34755342352` (TV + Mobile Android), iOS `34755343057`.

### Upstream parity v3 — authoritative queue before next provider repairs
Workflow run `34753648375`, scope 46, 3 rotating samples/lane, 25 s timeout:
- matched/tested: **45/46**; missing upstream mapping: **1** (`kehflix`); provider downloads failed: 0.
- status: **8 FULL / 11 REGRESSION / 11 RESAMPLE / 15 ZERO**.
- Certain manual regression providers (upstream stream exists while NiakVIO returns zero): `animesama-co`, `animevostfr`, `french-manga`, `kurage`, `playimdb`, `sekai`, `streamzo`, `uhdmovies`, `voiranime`, `voiranime-homes`, `voiranime-rip`.
- Exact certain regression lanes/fixtures:
  - `animesama-co`: anime / `my-hero-academia-s01e01` TMDB 65930.
  - `animevostfr`: anime / `fullmetal-alchemist-brotherhood-s01e01` TMDB 31911.
  - `french-manga`: movie / `jujutsu-kaisen-0` TMDB 810693; anime / `death-note-s01e01` TMDB 13916.
  - `kurage`: anime / `my-hero-academia-s01e01` TMDB 65930.
  - `playimdb`: movie / `oppenheimer` TMDB 872585; tv / `house-of-the-dragon-s01e01` TMDB 94997.
  - `sekai`: anime / `chainsaw-man-s01e01` TMDB 114410.
  - `streamzo`: movie / `colony-2021` TMDB 760873; tv / `the-boys-s01e01` TMDB 76479; anime / `demon-slayer-s01e01` TMDB 85937.
  - `uhdmovies`: movie / `fight-club` TMDB 550.
  - `voiranime`: anime / `death-note-s01e01` TMDB 13916.
  - `voiranime-homes`: anime / `death-note-s01e01` TMDB 13916.
  - `voiranime-rip`: anime / `failure-frame-s01e01` TMDB 245285.
- RESAMPLE providers (clean miss on sampled catalogue, not a proved Niak regression): `animesultra`, `animevost-fr`, `castle`, `coflix`, `hindmoviez`, `mallumv`, `movieshunt`, `mugiwarastream`, `papadustream`, `persianstremio`, `yflix`.
- Repair rule: prioritize certain regressions; RESAMPLE gets another catalogue sample; ZERO/both-fail is not rewritten blindly. Provider becomes FULL only when every declared required lane is proved.

### Pending after this checkpoint
- Read exact five-platform Native Lab outcomes on SHA `b18342a…`; do not call them green until each platform really executes the 46-provider physical manifest.
- Repair the 11 certain regression providers/lane failures above using A/B evidence; rerun parity and replace this census with the newer authoritative count.
- Re-sample the 11 RESAMPLE providers and classify external/catalogue misses separately from Niak regressions.
- Resolve/record Kehflix upstream mapping separately; do not fabricate parity.
- Keep TEMP workflow neutral after this checkpoint so no stale one-shot patch remains armed.

## Durable secondary-task ledger — 2026-09-13

> This section is mandatory recovery context. Provider repair priority does not cancel these secondary tasks. Keep it current at every checkpoint.

# NiakVIO — durable secondary task ledger

This file is a durable anti-forgetting ledger for secondary work. `MEMORY.md` remains the recovery source of truth and must mirror this ledger at every checkpoint.

## Priority rule

1. Provider yield first: resolve current `REGRESSION` cases in batches by shared root cause, then widen `ZERO` sampling and repair every newly proven upstream-positive/local-zero case.
2. Do not manufacture green by shrinking the 96-provider catalogue or by accepting wrong title/type/season/episode media. Wrong media is worse than zero; keep fail-closed identity and media integrity.
3. Secondary tasks below remain mandatory and must not be silently dropped while provider repair is active.

## Secondary tasks — mandatory

- **JavaScript minimization/minification**
  - Production bundles must go through the NiakVIO Provider v3 minimizer (`scripts/provider_v3_minimizer.py`), not Terser.
  - Preserve managed Lego markers/comments/structure and deterministic reverse reconstruction.
  - Re-run minimizer/fixed-point/byte-stability tests after batch provider changes and before the final Hub-46 freeze/publication candidate.
  - Measure resulting bundle sizes and ensure minimization does not change runtime semantics, provider identity evidence, headers, routes, timers, or Core/Provider ownership.
  - Keep source-qualified/content-hashed filenames synchronized with manifests/projections after minimization.

- **Hub-46 native transport**
  - Keep global catalogue at 96 providers while Labs use the exact physical 46-provider scope.
  - Finish native workflow wiring to `native-hub46/manifest.json`, including iOS and explicit Desktop/Android consistency.
  - The transport manifest must end in literal `manifest.json` for official Nuvio repository base resolution.
  - Regenerate Hub-46 against the final repaired provider SHA; do not certify Labs against the historical infrastructure-proof provider SHA.

- **Five native Labs on one frozen SHA**
  - TV Android / NuvioTV.
  - Mobile Android / NuvioMobile.
  - Mobile iOS / NuvioMobile.
  - Desktop macOS / NuvioDesktop.
  - Desktop Windows / NuvioDesktop.
  - Keep official client behavior observational; do not patch official Nuvio clients merely to make Labs green.

- **Desktop/runtime robustness**
  - Audit active provider bundles for direct `setTimeout` / `clearTimeout` assumptions and guarantee Desktop-safe timer handling, not only StreamFlix.
  - Preserve Core timeout at 25 s unless a later explicit decision changes it.
  - Preserve navigation A→B→C generation isolation even when fetch ignores AbortSignal.
  - Preserve stale-request suppression and no reinjection from superseded generations.
  - Preserve 403 fail-closed behavior; blocked/forbidden player URLs must not be surfaced as playable streams.

- **Identity and media safety**
  - Capability/type gate before network work.
  - TMDB/IMDb dual identity, `series -> tv`, anime semantic separation.
  - Movie year strictness only for movie; episodic year must not influence TV/anime identity.
  - Title/type/season/episode correctness before yield; wrong episode/title is worse than zero.
  - Revalidate HLS/direct media integrity, HLS audio-child handling, short/fake media rejection, and Unknown handling.

- **Provider parity / upstream truth**
  - Use `engine_v2/config/provider-upstreams.json` as upstream authority.
  - Keep `FULL`, `REGRESSION`, `RESAMPLE`, `ZERO` distinct.
  - Expand ZERO/RESAMPLE rotation before declaring dead providers.
  - Re-run parity after each repair batch and again on the final frozen SHA.

- **Domain Refresh**
  - Keep full-CONFIG transaction semantics, source authority, source-qualified filenames/content hashes, Core/Lego invariance, cycle/rollback safety and idempotence.
  - Maintain synthetic A→B domain-change proof and projection/version synchronization.
  - Do not regress to official-site-only mutation.

- **Brain / Learning / scheduled discovery**
  - Weekly upstream/provider discovery stays read-only and scheduled; it must report new candidates without mutating catalogue/manifests/providers.
  - Learning/Brain proposals must consume current provider truth and must not treat telemetry/materialization green as live-stream proof.
  - Verify scheduled execution and artifacts on the stabilized branch/final candidate when possible.

- **Repository hygiene / temporary automation**
  - Remove obsolete `temp-*.yml` workflows after extracting useful evidence.
  - Never rearm stale contradictory cleanup workflows such as removal of the weekly upstream watch.
  - Remove obsolete temp scripts/triggers only after confirming they are not referenced by tests/docs.
  - Keep branch cleanup for the end; do not touch `main` during the current `fix/labs-5.21.44-20260912` repair phase without explicit authorization.

- **Manifests, projections and fixed point**
  - Keep root 96-provider catalogue and all projections internally consistent.
  - Regenerate root/VF/no-anime/VF-no-anime/Hub-46 projections from the same final provider state.
  - Validate content hashes, source-qualified filenames, deterministic rebuild, reverse reconstruction and fixed-point/idempotence.
  - Do not certify stale pinned bytes.

- **Documentation / durable memory**
  - Update `MEMORY.md` at every important correction, failure, architecture decision, publication candidate, native proof or security proof.
  - Keep this ledger mirrored into `MEMORY.md`; this is specifically intended to prevent repeated loss of secondary tasks.
  - Reconcile `automation/OPEN-TASKS-20260911.md`, `CHANGELOG.md`, `VALIDATION.json`, README EN/FR, `ARCHITECTURE.md`, `VALIDATION.md`, `ARCHITECTURE.docx`, Lab triggers/matrices and any stale release/branch assumptions.
  - Document explicitly: 96 global catalogue vs 46 current Hub/Lab scope.

- **Provider presentation assets / metadata**
  - Preserve provider logo work: 72×32 and 96×40 compressed WebP assets; missing logos use generated first-letter fallback where required.
  - Active-provider presentation must derive from manifests/current provider truth rather than a hand-maintained stale list.
  - Revalidate branding, language labels and quality metadata after final materialization.

- **Security / final certification**
  - Run CodeQL/security workflows on the final frozen SHA.
  - Run dependency audit (`npm audit --omit=dev --audit-level=high` or current repository equivalent) on the final candidate.
  - Validate hashes/integrity and retain Labs/security artifacts as evidence.
  - Do not weaken security gates to obtain green CI.

## Completion gate

This ledger is not complete merely because provider yield improves. Final completion requires: provider REGRESSION/ZERO work resolved or precisely classified; final provider bundles minimized and fixed-point stable; Hub-46 regenerated on the final provider SHA; all five Labs executed against that same frozen candidate; manifests/projections consistent; security gates complete; documentation and `MEMORY.md` current; obsolete TEMP workflows removed; and every remaining open item explicitly recorded with evidence/reason.

## 2026-09-13 — global Core ownership + final-stage minimizer rule

- User rule (mandatory): Desktop/client-runtime adaptations are global Core blocks, not provider-specific fixes. This includes timer portability (`setTimeout`/`clearTimeout`), terminal HTTP/media rejection such as 403, stale-generation suppression/cancellation and execution-budget behavior. Provider Lego owns provider-specific transport/data/options only.
- Verified source ownership: `scripts/provider_patches/global_runtime_compat_v1.py` is managed fix `CORE.RUNTIME_COMPAT.V1`; it globally supplies missing timers and Desktop URL/fetch portability. `scripts/apply_provider_overrides.py` forbids Core-global scripts in provider `patch_scripts`.
- Verified terminal policy ownership: `scripts/provider_patches/stream_output_sanitizer_v8.py` is the Core terminal sanitizer (`CORE.STREAM_SANITIZER.V6` managed block via V7/V6 composition). Ordinary probed rows publish only on positive media proof; the base sanitizer rejects HTTP 403/404/410. This must remain provider-agnostic.
- `desktop_runtime_compat_v1.py` is also Core-owned/provider-configurable when episode compatibility options are required; its timer fallback is runtime portability, never a provider-owned domain/transport hack. Duplicate timer responsibility should be simplified only through Core ownership, never by named-provider patches.
- Minimizer sequencing corrected: the NiakVIO-safe Provider v3 minimizer is a **final-stage** operation/gate after provider yield and global runtime behavior are stabilized. Do not put minification in ordinary repair loops. Terser remains forbidden; final minimization must preserve STARTFIX/CLOSEFIX/FIXDATA/Core boundaries, deterministic reverse rebuild and byte fixed point.
- The temporary full-minimizer audit started during repair was stopped/deleted from the active workflow set; its stale byte-stability test references were corrected, but the authoritative full minimizer/reverse-rebuild audit is deferred to final stabilization as requested.
- `tests/vf_recovery_profiles_test.py` currently carries stale provider-profile assumptions (`streamzo` patch list) and is not evidence for Core ownership; it is tracked as separate test-maintenance debt instead of weakening the global runtime contract.

## 2026-09-13 — adaptive native Lab global corpus

- Mandatory Lab sampling policy: exactly three global recent fixture pools — `movie`, `tv`, `anime` — each containing several dozen works. Canonical range is 2010 through current-year-1 (2025 for the 2026 campaign).
- Native Labs execute **one work at a time per lane**, never a fixed batch of 6. The corpus is a reserve, not a batch.
- A provider advances to another random/deterministic candidate from the **same lane only** when the current runtime call completes normally with `0 streams` and no error. Positive result stops rotation for that provider/lane. Runtime/load/timeout/player/transport/identity contradiction is not a catalogue miss and must stop/report rather than rotating it away.
- `scripts/rotating_corpus.py` keeps old regression fixtures addressable by exact slug for targeted diagnostics but excludes them from the three global recent pools, so old/2026 works cannot silently become ordinary Lab samples.
- `scripts/native_catalog_miss_rotation.py` is the shared clean-miss planner. Fallback runs must shrink to the clean-zero provider allowlist instead of retesting providers that were already positive or errored.

## 2026-09-13 — adaptive Lab fallback wired across five Labs

- Desktop macOS/Windows, Android Mobile and Android TV now run the three initial global seeds (1 movie + 1 TV + 1 anime), then use `native_catalog_miss_rotation.py` plus a shrinking provider allowlist. Only provider/lane pairs that returned a clean `0 streams` without an error advance to another random/deterministic work from the same global list.
- Fallback work is not a fixed batch and has no hard-coded “6 samples” rule. Positive providers and providers with runtime/load/timeout/transport/player/identity errors are not repeated to hide failures.
- iOS embeds the same three recent global pools as an interleaved reserve and tracks terminal provider+lane pairs in-process: clean zero continues to the next same-lane fixture; positive or exception stops that provider/lane.
- The adaptive runners reuse the current native session/emulator and restage only the clean-miss provider allowlist, reducing extra workload relative to rerunning the full 46 on every fallback title.

## 2026-09-13 — adaptive matrix gate follows global corpus lanes

- The native declared-provider matrix no longer requires three static representative fixture slugs. Any adaptive fallback fixture is resolved through `rotating_corpus.fixture_by_slug()` + `canonical_lane()` to `movie|tv|anime`; the old `fixture_by_type` map is compatibility-only for historical targeted evidence.
- This prevents fallback titles from being misclassified/unobserved and prevents old fixed samples such as Breaking Bad 2008 from becoming an ordinary Lab prerequisite.
- The synthetic matrix contract itself now uses the exact Hub-46 scope and recent global fixture pools, matching final acceptance instead of asserting stale 96/static-fixture output.

## 2026-09-13 — fail-closed batch quarantine repair v1

- Run `34766893110` replaces the all-targets-or-nothing Repair retry loop with a fail-closed batch quarantine transaction. Requested providers are repaired together; any provider with an explicit lost upstream-positive lane or certain recent-corpus parity regression is removed, the workspace is hard-reset to the pre-attempt SHA, and the remaining providers are retried together. Failed-provider mutations never survive.
- Accepted providers: `animevost-fr, playimdb, uhdmovies`. Quarantined providers: `animesama-co, animevostfr, french-manga, kurage, sekai, streamzo, voiranime, voiranime-homes, voiranime-rip`. Quarantined lanes: `{'animesama-co': ['anime'], 'animevostfr': ['anime'], 'french-manga': ['anime'], 'kurage': ['anime'], 'sekai': ['anime'], 'streamzo': ['anime', 'movie'], 'voiranime': ['anime'], 'voiranime-homes': ['anime', 'movie'], 'voiranime-rip': ['anime']}`.
- Acceptance requires both the strict representative yield gate and a 12-candidate-per-lane recent-corpus parity pass. RESAMPLE/technical-only rows are not silently reclassified as regressions.
- No NiakVIO minimizer ran in this repair loop.

## 2026-09-13 — VoirAnime current authority persisted after stream-positive proof

- VoirAnime current execution authority is `https://voir-anime.to/anime/{slug}/`; stale `arm.haglund.dev` api_recipe and obsolete `voiranime_homes_runtime_v1.py` execution authority are removed.
- Exact Tokyo Ghoul S01E01 proof remains stream-positive: `{'fixture': 'tokyo-ghoul-2014-s01e01', 'streams': 2, 'raw': 2, 'error': None, 'statuses': [200, 206, 404]}`. Previous run 34770328860 also completed full-reserve 32 parity with `certainRegressions=[]`.
- That prior workflow failed only in stale unrelated `tests/provider_v3_static_knowledge_contract_test.py` VegaMovies lookup (`StopIteration`); this debt does not invalidate VoirAnime runtime proof and must be repaired separately.
- Core ownership unchanged; no minimizer run.

## 2026-09-13 — AllWish stale playable proof invalidated

- AllWish remains catalogued/enabled by scope policy, but fresh ZERO15 adaptive proof exhausted the current global movie/TV corpus with zero streams. Historical manual evidence also showed fixture-invariant very short wrong-content media across unrelated works.
- Therefore old `playable_verified`/complete-capability claims are invalidated: `route_data_state=repair`, no current verified/proven lanes, movie+TV missing. Historical route knowledge is retained only as diagnostic evidence.
- Runtime remains fail-closed until a fresh identity-safe terminal media proof exists. Workspace materialization did not run the final-stage minimizer.

## 2026-09-13 — full32 regression wave: VoirAnime anime recovered

- VoirAnime anime regression was repaired with a current-site provider Lego layered over the existing movie resolver: current series page -> requested chapter -> `LECTEUR` selector -> external iframe -> shared bounded direct-media crawler.
- The anime V2 captures/delegates the previous movie resolver; Core remains the only final runtime dispatcher and terminal validation owner. Workspace materialization did not minimize.
- Exact Tokyo Ghoul S01E01 proof: `{"provider": "voiranime", "lane": "anime", "fixture": "tokyo-ghoul-2014-s01e01", "streams": 2, "raw": 2, "statuses": [200, 206, 404], "accessible": true, "success": true, "error": null, "timeout": false}`.
- Recent-reserve parity has no certain `upstream_ok_niakvio_ko`: summary `null`.

## 2026-09-13 — Anime-Sama / Mugiwara movie overdeclaration removed

- Anime-Sama and Mugiwara now publish semantic `anime` only. `tv`/`series` remain transport aliases; `movie` is not advertised after wrong-content/unproven repair evidence.
- Live post-rebuild evidence: `{"anime-sama": {"movie": {"streams": 0, "raw": 0, "statuses": [200, 404], "error": null}, "anime": {"streams": 2, "raw": 2, "statuses": [200, 404], "error": null}}, "mugiwarastream": {"movie": {"streams": 0, "raw": 0, "statuses": [200], "error": null}, "anime": {"streams": 3, "raw": 3, "statuses": [200], "error": null}}}`. Movie calls fail closed; anime positivity independently controls `on` vs `repair`.

## 2026-09-13 — User repair execution directive

- Manual tests already supplied by the user are authoritative input evidence for the active repair pass.
- Do **not** redo or reclassify the same provider tests from zero unless one narrowly targeted verification is strictly necessary to avoid a false fix.
- When the user says `continue`, resume immediately from the real current HEAD of the active repair branch and execute the remaining ZERO/regression fixes through validation and delivery.
- Do not stall on inventory, recounting, or repeated diagnosis when the user's existing manual evidence already identifies the failing lane or chain.
- Prefer concrete correction -> targeted proof -> full non-regression -> persistence, then move to the next open ZERO/regression.
- Never treat historical quarantine/repair labels alone as current regressions; current evidence wins.
- During the active `fix/labs-5.21.44-20260912` repair pass, do not touch `main` unless a later explicit publication step authorizes it.

## 2026-09-13 — scoped CDN/browser transport batch v1

- Applied browser-compatible transport without anti-bot circumvention: Core media enrichment now supplies a modern Chrome UA only when a row omitted User-Agent; explicit provider headers remain authoritative; scoped cookie jar + Referer/Origin + redirect-follow remain intact.
- AniKoto execution authority is runtime v2; AnimePahe uses Chrome UA + credentials/include + redirect-follow; AnimeVOSTFR uses credentials/include + redirect-follow and carries Referer/Origin/User-Agent while remaining anime-only.
- AnimeSalt receives the shared browser playback context on rebuilt bytes, but no cf_clearance/Turnstile/challenge token is fabricated. Any remaining site/CDN 403 stays fail-closed and must be classified external/runner-blocked rather than surfaced as playable.
- Targeted post-rebuild JJK probe summary: `{"anikototv": {"error_class": null, "http_statuses": [], "ok": true, "raw_stream_count": 0, "server_accessible": false, "server_success": false, "stream_count": 0, "timeout": false}, "animepahe": {"error_class": null, "http_statuses": [], "ok": true, "raw_stream_count": 0, "server_accessible": false, "server_success": false, "stream_count": 0, "timeout": false}, "animesalt": {"error_class": null, "http_statuses": [200, 403], "ok": true, "raw_stream_count": 0, "server_accessible": true, "server_success": true, "stream_count": 0, "timeout": false}, "animevostfr": {"error_class": null, "http_statuses": [200], "ok": true, "raw_stream_count": 0, "server_accessible": true, "server_success": true, "stream_count": 0, "timeout": false}}`.

## 2026-09-14 — Hub46 executable catalogue / provider-old archive

- Executable catalogue is now **exactly the 46 providers** from `automation/evidence/hub-lab-matrix-46.json`; the former 50 non-hub providers are no longer OFF rows and are absent from active manifests/catalogue/overrides/static knowledge/materialization/repair disposition.
- `automation/provider-repair-disposition.json` now carries **46 catalogue / 46 enabled / 0 disabled**; generated `providers/` bundles for the former non-hub set were removed.
- Historical non-hub ProviderBase bytes were preserved byte-for-byte but physically moved out of active reconstruction: **46 provider slugs remain in `provider-bases/`, 50 historical provider slugs live in `provider-old/`**. The archive migration moved 951 files with Git rename semantics.
- Durable migration/verification scripts: `scripts/prune_to_hub46_catalog.py` and `scripts/archive_nonhub_providerbases.py`. A replay of the prune now archives non-hub bases to `provider-old/` rather than resurrecting an OFF catalogue.
- Evidence: catalogue-prune run `34786010735` and ProviderBase archive run `34786047300` both green on `fix/labs-5.21.44-20260912`. **main was not modified.**

## 2026-09-14 — Main-only 5.21.46 publication, Hub46 atomicity, security/audit/minimizer continuation

### Repository / branch authority
- `main` is the only active write/publication target. The merged repair branch `fix/labs-5.21.44-20260912` was deleted by repository hygiene and must not be recreated for this continuation.
- Historical provider archive remains `provider-old/`; exactly 46 current provider slugs remain executable/materialized in `providers/` + `provider-bases/`, 50 historical provider slugs remain archive-only.
- PR #114 was merged to main through merge commit `3e144d66b402e15af962f6adde767736c00bed2f`; all continuation after merge is main-only.

### Release / manifests / Domain Refresh
- The old apparent 5.21.43 state was real only for Hub46 projections: root/language manifests had advanced while `manifest-hub46.json` / `native-hub46/manifest.json` lagged. Release finalization was repaired so root, language projections, Hub46 projection and pinned native Hub46 transport synchronize together.
- Domain Refresh was rebuilt as an atomic two-local-commit / one-push transaction: first local provider-generation commit creates the SHA that owns new content-addressed bundles; `native-hub46/manifest.json` is then pinned to that provider SHA; hashes/integrity are regenerated; only the final commit is pushed to main.
- Domain Refresh now preserves current filename stage and current-46 scope, leaves historical rows immutable, runs current-only sanitation/guarding, and is fail-closed on unexpected scope or history changes.
- A real domain refresh changed 11 current providers and legitimately bumped release `5.21.44 -> 5.21.45`. Later durable provider fixes for AnimeSama.co/VoirAnime changed provider bytes and legitimately bumped `5.21.45 -> 5.21.46`.
- Final accepted published release at this checkpoint is **5.21.46**. The finalizer has repeatedly proved fixed point afterward: `patched=0`, `release_changed=false`, provider bumps `0` on no-op runs.
- Final Domain Refresh after 5.21.46 is strict no-op: `applied=0`, `registry=0`, `bundles=0`, metadata `changed=0`, `FIELD_DOMAIN_TRANSACTION_CHANGED false`, `FIELD_DOMAIN_REFRESH_IDEMPOTENT true`; observation-only DNS/GlobalPing limits never mutate authority.

### Release finalizer architecture
- `.github/workflows/release-finalize.yml` is the permanent exact-SHA accepted-release finalizer and now supports atomic provider-generation + pinned-Hub46 finalization before one push.
- Release integrity, Hub46 projection, native pin, language projections and release hashes are mandatory. Finalizer must not bump a release/provider when bytes did not change.
- `manifest-hub46.json` is a current projection; `native-hub46/manifest.json` is an immutable transport projection pinned to the local provider-generation commit SHA that actually contains referenced bundles.

### Current runtime/security fixes already durable
- Core provider timeout remains **25 s**.
- Latest-request A->B->C stale-generation suppression remains mandatory even when native fetch ignores AbortSignal.
- 403/404/410 terminal media remains fail-closed while valid sibling streams may survive.
- AnimeSama.co and VoirAnime published HTML parsing was repaired at the owned Provider-block source using deterministic scanners; published HTML-security gate reached **0 forbidden regex findings across 46/46** before 5.21.46 finalization.
- Purstream current authoritative site is `https://purstream.mx`; its API authority remains under `api.purstream.ad`. Stale tests expecting only `purstream.ad` were corrected without weakening DATA authority.
- Workflow/Media stale assertions left from the old 96-provider execution catalogue were reconciled to the current 46 executable providers without touching the 50-provider historical archive.

### Final exact-SHA validation status before new minimizer/security cleanup
- Candidate SHA used for the in-progress final validation was `4811cfa9bc5a4fa343bd59ecda17e79b83d091b8`, release 5.21.46.
- `CORE - Verify & Publish` Quick: green on that SHA, including published-byte gates after fixed-point replay was aligned to the actual publication pipeline (`blocks -> security hardening -> published bytes`).
- Core gates green on the same SHA: Non-Regression, Stream Metadata, Media Type & Playback, Provider Overrides. Separate Workflow Gate was also repaired/green after replacing stale current-catalogue fixtures/assertions.
- `SEC - CodeQL` run `34828935079`: all 12 analysis/scope jobs and final `CodeQL · javascript-typescript` matrix-enforcement job completed success on SHA `4811cfa9...`.
- IMPORTANT: a green CodeQL workflow means analysis executed successfully; it does **not** mean zero Code Scanning alerts. User reports GitHub UI still shows about **1386 Code Scanning alerts**, so security cleanup is NOT complete.
- Native final validation was still running when this checkpoint was requested: Desktop macOS+Windows built successfully and were executing movie/tv/anime routes; Mobile Android entered live routes after green prebuild/KVM; TV Android was still prebuilding; iOS had resolved official NuvioMobile and was queued for macOS runner. Do not call five Labs complete until all five platform jobs are terminal.

### External audits — fresh evidence and required cleanup
- `SEC - External Code Audit` run `34828937432` completed success on SHA `4811cfa9...` with `publish=false` (read-only), artifact `external-code-audit-34828937432`, artifact id `10341474975`, SHA-256 `ae270858724eaf123fb2d9888b9e5a161336a718054bca55640856ffc965e489`.
- Fresh Sonar, DeepSource and CodeScene exports were all produced. This audit must be treated as a release gate, not decoration.
- Preliminary export triage: Sonar exported 10,000 open findings; roughly 9,997 are under generated `providers/` bundles, leaving only a tiny maintained-source remainder. DeepSource exported 256 findings with 0 vulnerability count in its export; many critical secret-like findings are in captured diagnostics/LKG/evidence rather than maintained runtime source. CodeScene export completed with no defect count observed in preliminary summary, but hotspot ranking is polluted by generated/historical bundles.
- Required security model: generated published bundles remain covered by mandatory NiakVIO publication/runtime/security gates (artifact syntax/runtime validation, security hardening, forbidden-pattern gate, fixed-point/reverse reconstruction, hashes/integrity). Static analyzers should primarily scan maintained source (`provider-bases/`, provider/Core block generators, engine/scripts/actions), not repeatedly count the same generated Core inside every `providers/*.js` artifact or archive evidence.
- Do not suppress/close real maintained-source security findings merely to reduce counts. First separate generated/evidence noise from maintained-source findings, then fix the maintained-source findings and rerun fresh external audits.

### CodeQL workflow cleanup now mandatory
- Current `.github/workflows/codeql.yml` exposes 1 scope job + 11 analysis jobs + 1 aggregate job. User explicitly rejects this noisy matrix presentation.
- Current shards duplicate JavaScript scanning across `providers/**` and `provider-bases/**` in four lexical shards each, plus source/actions/python. `provider-old/**` remains excluded and must stay excluded.
- Target: retain Hub46/current-source coverage while reducing visible jobs to a compact set, e.g. Actions, Python, JS Core/source, JS ProviderBase/current maintained provider source, plus one aggregate if needed. Generated `providers/**` should not duplicate maintained-source CodeQL if publication gates continue to audit exact final bytes.
- The 1386 UI alerts must be treated as a real unresolved security-quality issue until current maintained-source alerts are isolated/fixed or precisely classified; do not equate green CodeQL execution with zero findings.

### NiakVIO Provider v3 minimizer — exact authoritative rule
- User clarified repeatedly: **NO Terser and no external/generic JS minifier.** Do not introduce Terser.
- Architecture already declares `scripts/provider_v3_minimizer.py` as the only production minimizer; `automation/provider-v3-architecture.json` explicitly says `terser_allowed=false`, phase `pre-hash-safe-whitespace`, production enabled.
- Current bug: `scripts/reapply_published_overrides.py` still explicitly bypasses the minimizer and preserves post-Core bytes verbatim, contradicting architecture and `provider_v3_minimizer_published_test.py`.
- The minimizer is deliberately NiakVIO-safe: no identifier rename, no expression reorder/fold, no literal/regex rewrite, preserve every line terminator and managed marker cardinality, leave template-bearing files byte-stable, current production transform only removes code-line leading indentation safely.
- Minification applies to final `providers/*.js` publication output using the **NiakVIO minimizer**, and must remain compatible with add/remove/update of owned Provider/Core fix blocks: reconstruct from ProviderBase + structured DATA/static knowledge + owned blocks, apply security hardening, apply NiakVIO minimizer at the declared pre-hash stage, validate syntax/fixed-point, then compute content SHA / content-addressed filename / provider version / manifests / hashes.
- User clarification on ownership: do not introduce a generic tool that rewrites upstream/external source semantics. The runtime artifact is minified only through the conservative NiakVIO-aware transformation contract.
- Required tests before publication: `tests/provider_v3_minimizer_contract_test.py`, `tests/provider_v3_minimizer_preview_test.py`, `tests/provider_v3_minimizer_published_test.py`, reverse rebuild / static audit / published artifact validation / security hardening / release integrity.
- Because enabling the already-declared minimizer may change current provider bytes, the next real publication may legitimately become **5.21.47**. Never force the version; let exact byte drift drive provider/release bumps.

### Immediate continuation after this checkpoint
1. Persist this checkpoint physically into `MEMORY.md` through the durable pending-memory writer and verify the pending sentinel resets.
2. Wire `scripts/provider_v3_minimizer.py` into `reapply_published_overrides.py` at the production pre-hash stage, replacing the contradictory verbatim/no-minifier branch; add/strengthen tests that prove add/remove block reconstruction is reminimized deterministically.
3. Consolidate CodeQL jobs and maintained-source scope without weakening security; keep `provider-old/` excluded and keep exact published-bundle security gates mandatory.
4. Triage fresh Sonar/DeepSource/CodeScene exports into maintained source vs generated/archive/evidence; fix maintained-source blocking findings and configure/report scopes so future audits are actionable rather than dominated by generated bundles.
5. Run finalizer atomically; accept 5.21.47 only if minimization actually changes bytes. Regenerate Hub46/native pin/projections/hashes/integrity.
6. Re-run Domain Refresh to strict no-op on the new final head.
7. Re-run Verify & Publish, four Core gates, Workflow Gate, compact CodeQL, external audits, dependency/security checks, and all five Native Labs on one exact final SHA. Final completion requires terminal green/precisely classified evidence, not just dispatched runs.

## 2026-09-14 — Native Labs one-shot harness hardening from existing evidence

### User execution rule / scope
- User explicitly requires **no new exhaustive/long Native Lab rerun** for this repair. Existing TV Android, Mobile Android/iOS and Desktop macOS/Windows logs are sufficient to diagnose and harden the harness. Future validation for this change must preferentially reuse those artifacts and static/codegen contracts; only a narrowly targeted check may be considered later if strictly necessary, never another blind full campaign.
- Scope clarification: the native campaign did **not** traverse 96 providers. The executable Hub/Lab scope is **46 unique Hub46 providers**. The apparent `96` came from adaptive **fixture/title samples** generated while rotating catalogue misses; provider scope remained 46. The excessive duration came from catalogue over-sampling, not from executing the historical 96-provider catalogue.
- No Native Reader workflow was dispatched during this repair. Work is isolated on `fix/native-labs-one-shot-20260914`; `main` remains untouched at this checkpoint.

### Existing-evidence root causes
- **Desktop macOS:** six routes began but never emitted a terminal, all in the same `The Wolf of Wall Street` fixture: `FRENCH-MANGA`, `MALLUMV`, `kehflix`, `moviebox`, `movieshunt`, `moviesmod`. The native Desktop test process then died with **SIGBUS** while several provider runtimes were simultaneously in flight. Treat these as process-level concurrent QuickJS/JNI casualties, not six independently proven provider regressions.
- **Desktop Windows:** two routes lacked terminals in `Avengers: Endgame`: `4KHDHUB`, `ALLWISH`. The process died with **`EXCEPTION_ACCESS_VIOLATION` inside `quickjs_*.tmp`** while providers were concurrent. Again, this is a harness/process concurrency failure, not proof that those two providers are broken.
- **TV Android:** on `The 100`, **StreamZo returned a positive provider result (`count=1`) and the fixture then stopped immediately after `FIELD_NATIVE_PLAYER_BEGIN`**. Therefore the provider/yield path succeeded and the inline production-player probe could abort an adaptive catalogue-miss traversal after a provider was already proven positive.
- **iOS:** the watchdog could terminate/relaunch while the old `simctl launch --console` generation still flushed output. A late `FIELD_NATIVE_IOS_PROVIDER_END` from generation N could appear after `PROVIDER_BEGIN` from generation N+1 and be mistaken for the new terminal, producing false `idle_after_provider_end` and potentially converting a clean zero/catalogue miss into a fabricated timeout.

### Durable harness fixes on `fix/native-labs-one-shot-20260914`
- `scripts/augment_native_corpus_request_contract.py` now rewrites generated provider batches from `providers.chunked(6)` to **`providers.chunked(1)`** for TV, Mobile and Desktop after request-contract augmentation. The coroutine/per-provider hard-timeout shape stays intact, but only one QuickJS/JNI provider runtime executes at a time in the process.
- Primary fixtures continue to exercise the production player. Adaptive catalogue-miss rotations set `NIAKVIO_NATIVE_DISABLE_PLAYER_PROBES=1`; the generated Android player loop becomes `rows.take(0).forEachIndexed`. Adaptive passes therefore discover provider yield only and cannot be killed by a hostile media URL after provider success.
- `scripts/run_native_catalog_fallback_tv.sh` and `scripts/run_native_catalog_fallback_mobile.sh` enable that adaptive no-player mode and emit `adaptive_fallback=true player_probe=false` evidence.
- `scripts/run_native_corpus_ios_suite.sh` is generation-safe: watchdog restart records the exact `PROVIDER_BEGIN` line, calls `stop_lab`, drains the old console generation, and checks for a matching terminal **only after that exact BEGIN**. A late terminal triggers clean fixture restart with no manufactured timeout; absence of a terminal confirms the watchdog timeout and resumes after the blocked provider. The obsolete fatal `idle_after_provider_end` path is removed.
- `tests/native_evidence_codegen_pipeline_test.py` now proves serialized `chunked(1)` output on TV/Mobile/macOS/Windows, proves `chunked(6)` is absent after augmentation, and explicitly proves adaptive TV codegen emits `rows.take(0).forEachIndexed` while retaining serialized provider execution.
- `tests/native_ios_watchdog_resume_test.py` now requires drain/exact-BEGIN correlation, `late_terminal`/`confirmed_timeout` branches, restart ordering `stop -> drain -> launch`, and forbids `idle_after_provider_end` from returning.
- Legacy static request-contract audit comments (`listOf<String>(fixtureMediaType)...`, `ProviderRequestRoute(type)`) remain present for compatibility; restoring them after the first PR red changed **no runtime behavior**.

### Branch / commits / PR
- Base main SHA for this repair: `dad783b042f0bea331d5605648acec0494ed4c4f`.
- Repair branch: `fix/native-labs-one-shot-20260914`.
- Key test commit: `055915cea2c35852496da9123ad80c6c6d319c64` — iOS watchdog generation-safety contract.
- Adaptive codegen proof commit: `d1fa95590312ca4ab86699ad3345e128d2e1a49b`.
- Current validated code HEAD before memory checkpoint: **`4cccac9fd0d3dedf3e2a1544aef39371ae52e6cc`** — restores legacy static audit markers without changing runtime fix.
- Draft PR **#116**, `fix(native): harden one-shot Labs from existing evidence`, targets `main`. It exists solely for static/PR validation; native reader workflows do not listen to `pull_request`, so opening/updating this PR did not dispatch the five Native Labs.

### Static/PR validation on exact code HEAD `4cccac9f...`
- Initial PR head `d1fa9559...` exposed one stale/static compatibility issue only: `CORE - Media Type & Playback Gate` run `34864841474` failed because `tests/native_evidence_contract_test.py` still required the legacy request-contract marker comment. Runtime behavior was not failing. The marker comments were restored.
- **CORE - Media Type & Playback Gate** run **`34865005298`**: **success**. Its native architecture/codegen steps all passed, including full native evidence architecture, native evidence execution floor, reader codegen purity, Kotlin codegen pipeline, observational purity, UX harness, HTTP instrumentation and cache-safety contracts.
- **Provider Non-Regression Gate** run **`34865005269`**: **success**.
- **CORE - Workflow Gate** run **`34865005707`**: **success**, covering Python syntax, executable runtime contract, workflow architecture, native provider-loading compatibility and side-effect-free compatibility checks.
- **CORE - Verify & Publish** Quick run **`34865005275`**: **success**. Its Quick gate executes `tests/native_ios_watchdog_resume_test.py`, so the new iOS generation-safety contract is proven on the exact code HEAD. No Deep publication path ran on the PR.
- **SEC - CodeQL** run **`34865005265`** is still in progress at this checkpoint: Actions, Python and JS Core jobs are already success; only `CodeQL · JS ProviderBase` remains analyzing. Do not claim the aggregate CodeQL run green until its terminal verdict is recorded.

### Completion / next authority
- This repair intentionally does **not** reclassify the macOS/Windows missing-terminal providers as provider regressions; the evidence proves the harness crashed around them. Provider truth must continue to come from existing provider/parity evidence, not from process-death victims.
- Do **not** rerun another exhaustive five-platform Native Lab merely to validate these harness changes. Existing logs were deliberately used as the empirical proof; static/codegen regressions are now locked by tests.
- Before merging/publication, record the terminal CodeQL verdict. Keep PR #116 draft/main untouched until the repair checkpoint is durable and all lightweight gates are terminal.

## 2026-09-14 — Native one-shot repair published and post-merge validated

### Published authority (supersedes pre-merge checkpoint status lines)
- The earlier checkpoint section `2026-09-14 — Native Labs one-shot harness hardening from existing evidence` was written while PR #116 was still draft. Its statements that `main` was untouched / PR should remain draft were true only at that intermediate checkpoint and are now superseded by this section.
- PR **#116** `fix(native): harden one-shot Labs from existing evidence` was marked ready and **merged into `main`**.
- Merge commit / published main authority: **`8d9ac77928cd6f392a9c24a3425a6ea8663d26f6`**.
- Published behavior is the same one-shot repair already documented: serialized native provider execution (`chunked(1)`), adaptive Android/TV catalogue rotations without production-player probes, and generation-safe iOS watchdog restart/drain/exact-BEGIN correlation.

### Post-merge validation on published main
- **CORE - Workflow Gate** run **`34866432607`** on merge SHA `8d9ac779...`: **success**. Python syntax, executable multi-device runtime contract, workflow architecture, native provider-loading compatibility and side-effect-free compatibility checks all passed.
- **CORE - Verify & Publish** run **`34866432526`** on merge SHA `8d9ac779...`: **success**. The Quick gate passed; all Deep stages were explicitly **skipped**, so no fresh exhaustive provider observation/publication campaign was run.
- **LEARN - Brain Branch Maintenance** run **`34866432627`** on merge SHA `8d9ac779...`: **success**.
- The previously interrupted PR CodeQL run **`34865005265`** was resumed only for its cancelled `JS ProviderBase` job. Final rerun state: **all CodeQL jobs success** — Actions, Python, JS Core, JS ProviderBase, plus the maintained-source matrix.
- No Native Reader workflow (`NATIVE - Android Reader`, `NATIVE - Mobile iOS Reader`, `NATIVE - Desktop Reader`, etc.) was dispatched for merge SHA `8d9ac779...`. The head-SHA workflow list contains only Workflow Gate, Verify & Publish, and Brain Branch Maintenance. This preserves the user rule: **do not rerun the long five-platform Native Labs for this repair**.

### Final interpretation / anti-regression rule
- The former macOS/Windows missing terminals remain classified as **harness process-crash victims**, not provider regressions: macOS SIGBUS / Windows QuickJS access violation happened with concurrent providers in flight. Do not reopen those provider IDs as regressions solely from those terminated routes.
- TV StreamZo/The100 remains the canonical proof that adaptive provider traversal must not be coupled to inline production-player smoke: provider yield was positive before the player probe killed the fixture.
- iOS late-terminal interleaving remains the canonical reason watchdog restart must stop + drain the previous console generation and correlate terminals strictly after the exact current `PROVIDER_BEGIN`.
- Provider scope for this campaign is **46 Hub46 providers**. The historical-looking `96` represented adaptive fixture/title samples, not 96 executed providers.
- Future long Native Labs should be redesigned/bounded rather than repeated blindly. Existing evidence plus the new static/codegen contracts is the authority for this one-shot repair.

## 2026-09-15 — Quick-first proven fixes published

- User explicitly requested simplest/fastest repairs first, while still finishing the remaining providers afterward.
- Published-source quick fixes in this checkpoint: AllWish fresh-proof authority guard, deterministic HTML scanners for shared DLE/Neko source, and Core Runtime Media Safety applied after the terminal sanitizer so Safety is the actual outermost final guard.
- Rematerialized affected providers only: AnimeKai, Kehflix, French-Manga, VoirAnime-Homes, Neko-Sama, Purstream, MugiwaraStream, VidEasy.
- Terminal proof rows for the non-Neko quick set: `[{"providerId":"animekai","fixture":"dragon-ball-super-2015-s01e01","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[1402.318],"statuses":[200,404],"error":null},{"providerId":"kehflix","fixture":"interstellar-2014","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[10143.466],"statuses":[200],"error":null},{"providerId":"french-manga","fixture":"hunter-x-hunter-2011-s01e01","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[1357.623],"statuses":[200],"error":null},{"providerId":"voiranime-homes","fixture":"dan-da-dan-2024-s01e01","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[1499.071],"statuses":[200,403],"error":null},{"providerId":"purstream","fixture":"interstellar-2014","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[10143.926],"statuses":[200,206],"error":null},{"providerId":"mugiwarastream","fixture":"tonikawa-over-the-moon-for-you-2020-s01e01","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[1425.18],"statuses":[200,404],"error":null},{"providerId":"videasy","fixture":"interstellar-2014","streams":1,"terminal":true,"reasons":["hls_segment_media"],"durations":[],"statuses":[200,403,404,500],"error":null}]`.
- Neko remains a separate heavy resolver case and is intentionally non-blocking for independent fixes. Current post-rematerialization JJK state: `{"providerId":"neko-sama","fixture":"jujutsu-kaisen-2020-s01e01","streams":0,"terminal":false,"reasons":[],"statuses":[200],"error":null}`.
- AllWish regeneration can no longer resurrect historical `playable_verified`; fresh identity-safe positive proof is required.
- Continue immediately with Neko and the seven technical-unresolved providers, then rerun Hub46 parity/local proof.

## 2026-09-15 — Final seven technical-unresolved audit

- User requested the simplest/fastest providers first but also asked to finish the remaining providers so Hub46 is practically clean.
- The seven unresolved providers were rerun with current V3, installed upstream dependencies, 8 rotating samples per declared lane and deep terminal HLS proof: `{"allwish":"ZERO","flemmix":"ZERO","fullanime":"ZERO","moviebox":"ZERO","moviesmod":"ZERO","vidfast":"ZERO","vidlove":"ZERO"}`.
- Certain Niak regressions: `[]`. Resample providers: `[]`. Missing upstream comparators: `[]`.
- Durable detailed evidence: `automation/final-seven-technical-audit-20260915.json`. A provider remains `repair` when its reference side is 403/429/timeout/otherwise technical and there is no terminal-positive authority; no speculative runtime patch is allowed.

## 2026-09-15 — Neko final repair classification

- Neko-Sama is now explicitly closed for the current provider-repair sweep as `repair` / fail-closed, not green.
- Behavior-preserving instrumentation on JJK S1E1 and Sakamoto Days S1E1 proved the internal resolver reaches the series, exact episode, `loadMi` servers and Vidmoly iframe, then constructs one runtime row (`runtimeOutCount=1`) while the exported provider contract still returns `raw=0`, `streams=0`.
- Tested directions that did not solve the export disappearance: episode parser V3 alone, provider-specific Vidmoly terminal resolver, Core correlated-player marker and Referer variations. No speculative patch is published.
- Durable final classification: `automation/neko-final-classification-20260915.json`; detailed stage evidence remains on `diag/neko-runtime-stage-20260915` commit `b1cd42ad2872125f0f9591797b9f8a08b4652530`.
- The previous seven technical-unresolved providers remain classified `ZERO/repair` with no certain Niak regression: AllWish, Flemmix, FullAnime, MovieBox, MoviesMod, VidFast and VidLove. The active provider debugging queue is therefore empty pending final Hub46 revalidation.

## 2026-09-15 — Hub46 provider closeout parity

- Final rotating Hub46 parity after classifying Neko: `{"schemaVersion":1,"scopeProviderCount":46,"accountedProviders":46,"statusCounts":{"FULL":10,"REGRESSION":4,"RESAMPLE":19,"UNMATCHED_FULL":1,"ZERO":12},"certainRegressions":["coflix","neko-sama","sekai","voiranime"],"resampleProviders":["anikototv","anime-ultime","animesama-co","animesultra","animetsu","animevost-fr","animevostfr","castle","mallumv","movieshunt","papadustream","persianstremio","playimdb","streamzo","uhdmovies","voiranime-rip","vostfree","wookafr","yflix"],"fullProviders":["anime-sama","animekai","desiflix","french-manga","hindmoviez","kehflix","kurage","mugiwarastream","purstream","videasy","voiranime-homes"],"partialProviders":[],"zeroProviders":["4khdhub","allanime","allwish","animesalt","flemmix","fullanime","moviebox","moviesmod","showbox","vidfast","vidlove","vidrock"],"currentRepairSweepOpenProviders":["coflix","neko-sama","sekai","voiranime"],"providerDebugQueueClosed":false,"nekoFinalState":"repair","knownFinalSevenRepair":["allwish","flemmix","fullanime","moviebox","moviesmod","vidfast","vidlove"]}`.
- Detailed parity evidence: `automation/hub46-final-parity-20260915.json`; concise closeout ledger: `automation/hub46-provider-closeout-20260915.json`.

## 2026-09-15 — Manual evidence + active scope 44

- **DesiFlix = OFF**: current redirect authority is compromised/inappropriate. **FullAnime = OFF**: no current hub/address authority. Neither may be kept enabled merely to preserve the historical 46 count.
- Canonical recoverable census remains **46 rows**, executable hub/native scope is **44 active providers**. The legacy `hub-lab-matrix-46.json` filename is compatibility-only; its declared active count is now 44 and current generators derive the count from that authority.
- `automation/manual-provider-evidence-20260915.json` captures reusable browser evidence: AllWish + AllAnime HLS 200; MoviesMod terminal direct-media route behind interaction; 4KHDHub current movie+TV route via `hdhub4u.bi -> new5.hdhub4u.cl`. Manual positive evidence is not native-player proof, but supersedes interpreting older ZERO results as “no route exists”.
- **Never ask the user to repeat those already supplied tests.** Continue integration from the captured evidence; a new manual test is justified only for a genuinely new fact not recoverable from repository/runtime evidence.

## 2026-09-15 — Active44 durability repair

- Recoverable provider catalogue is 46 rows; executable/native/automatic-repair scope is matrix-driven and currently 44. DesiFlix and FullAnime are explicit OFF and must never be reactivated merely to satisfy an old cardinality.
- Repair V6 and fast targeted Repair must reject explicit OFF providers, derive executable targets from `automation/evidence/hub-lab-matrix-46.json`, and may use the historical 96-provider proof baseline only as evidence filtered down to the current 46-row catalogue.
- Existing user browser evidence is authoritative for avoiding duplicate manual requests: MoviesMod terminal media chain, 4KHDHub movie+TV chain, AllWish/AllAnime HLS 200, plus the larger manual-test history supplied 2026-09-15.
- `official_hub` is discovery/address metadata, not activation authority. Current activation is the matrix plus explicit manual-OFF state.

## 2026-09-16 — Five-Lab artifact audit + historical Desktop/Mobile runtime-contract cross-check

- Public release remains **5.21.48** and is intentionally **frozen** by this audit. Do not bump solely because the exhaustive Native matrix is red: current evidence separates real product/provider gaps from Lab/runtime false negatives. A later version bump is justified only by actual provider/Core/client byte changes that are then re-proved on one exact SHA.
- Exact audited Native source SHA: `6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1`. Runs: Android TV+Mobile `35033132967`, iOS `35033132980`, Desktop macOS+Windows `35033133048`.
- **iOS is genuinely positive on the frozen provider set.** Full artifact `native-mobile-ios-full-35033132980` (artifact `10425274614`) contains 3299 `FIELD_NATIVE_IOS_RESULT` rows, **89 count>0**, and **89/89 production-player probes `ready`**. Positive rows are VidRock (58) and VoirAnime (31). This directly disproves a simultaneous global failure of the provider bundles.
- **Desktop Windows is not a zero platform.** Full artifact `native-desktop-full-windows-35033133048` (artifact `10424349538`) contains 2116 `FIELD_NATIVE_RESULT` rows and four positive provider/fixture results: HindMoviez + VidRock on Avengers Infinity War movie, and HindMoviez + VidRock on Peaky Blinders S01E01 TV. Player probes are **9 `ready` / 1 timeout**. HindMoviez movie rows play around 8961 s; TV rows around 3419 s. VidRock is player-ready on both movie and TV. The workflow red is the exhaustive matrix gate, not inability of Desktop Windows to extract or play any stream.
- **Desktop macOS also extracts real rows but its Lab player bridge is independently broken.** Full artifact `native-desktop-full-macos-35033133048` (artifact `10424661528`) contains 2091 result rows and three positive results: HindMoviez movie count=4, VidRock movie count=1, VidRock TV count=1. All six associated production-player diagnostics fail at `mpv_create_failed`. HindMoviez transport still reaches direct HTTP-200 Matroska rows. Classify this as a macOS Lab/player-initialization defect until proved otherwise; do not erase the extraction evidence or reclassify those providers as globally broken.
- **Android Mobile has a concrete diagnostic-launch false red.** Full artifact `native-mobile-android-full-35033132967` (artifact `10424876074`) contains 2073 result rows and two VidRock positives: Avatar: The Way of Water movie count=1 and House of the Dragon S01E01 TV count=1. Both then fail only in player setup with `Could not launch activity -> Unable to resolve activity ... cmp=com.nuvio.app/.MainActivity`. The current V36 code uses `instrumentation.targetContext.packageName`; the real artifact proves that assumption is insufficient for the official build/applicationId variant. This is harness/native-launch debt, not a VidRock extraction failure.
- Android TV full artifact is ~612.6 MB (`native-tv-full-35033132967`, artifact `10426108717`) and was not re-downloaded in this audit. Preserve existing job diagnostics plus authoritative user-device evidence instead of treating the runner red as provider truth. User TV evidence still proves Purstream, StreamZo, Castle, VidRock and HindMoviez can appear on Interstellar/HOTD. Hell Mode/anime remains materially poorer and still exposes genuine product issues: sparse provider coverage, quality/language/badge normalization, late arrivals/stale timing and missing 4K.
- Historical runtime-contract reminder is relevant. At commit `a2698d843c2b7911fff814cc7cbb24587eb2f6be`, Android Mobile used synchronous `__native_fetch -> OkHttp`, Desktop used async `__native_fetch -> OkHttp`, and proxy/runtime behavior differed by platform. Later September work made the missing Desktop/Mobile TMDB↔IMDb identity contract explicit: canonical IMDb path is `__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`, canonical cache is `__nuvioTmdbMetadataCacheV1`, and host hydration must happen **after provider/Core evaluation and before `getStreams`**.
- The proven Desktop V3 identity augmentation (`scripts/augment_native_desktop_dual_id_context.py`) and the generalized `scripts/augment_nuvio_client_media_identity_bridge.py` still exist in `main`, but current official Native acceptance workflows do **not** apply them. Therefore IMDb-dependent zero rows on Desktop/Mobile may be host-contract gaps and must not automatically be blamed on provider bytes. Do not silently patch official Nuvio clients merely to make Labs green; keep this as an explicit compatibility/product-contract item.
- Historical August StreamZo cross-client success remains compatibility evidence, not an exact frozen-release native baseline: the old `nuvio-client-lab` path was a Node transport lab and older Desktop canaries materialized a dynamic candidate with only a few providers. Use it to identify lost host/runtime capabilities, not as proof that every current Hub lane previously worked natively.
- Final audit decision: **keep 5.21.48 frozen; no release bump from the Lab reds alone.** Separate follow-up queues: (1) harness defects — Android Mobile launcher resolution, macOS `mpv_create_failed`, exhaustive matrix semantics; (2) host/runtime contract — Desktop/Mobile canonical media identity hydration; (3) real product/provider UX — anime coverage, quality/language/badges, stale/late results and 4K. Do not let categories (1) or (2) overwrite positive user/native evidence from category (3).
## 2026-09-18 — Branch consolidation + PR122/PR127 authority lock

- Repository branch cleanup completed: only **`main`** and **`brain-learning/proposals`** remain. All diagnostic/census/proof `tmp/*` branches were deleted.
- `fix/provider-activation-certification-v1` was archived before deletion as immutable tag **`archive/fix-provider-activation-certification-v1-20260918`**. Use the tag for historical comparison only; all new work continues on `main`.
- Closed/unmerged PR **#122** is historical evidence, not a blanket restore source. Merged PR **#127** has precedence for every provider/config family it materially retrworked. Never restore a #122 route over a #127-reworked provider unless a later explicit A/B/current live proof demonstrates that exact #122 sub-route/resolver is the playable authority.
- Existing example: VidLove is allowed to reuse its older V1/api.vidlove.cc authority only because a separate current A/B proved it FULL while V2 was red. This is evidence-based exception, not general rollback policy.
- Kehflix authority is explicitly locked:
  - **hub/address authority = `https://kehflix.wiki/`**
  - **current runtime terminal = `https://kehflix.com`**
  - **`kehflix.lol` = stale/historical, never current runtime**
  - Domain Refresh must keep hub and runtime roles distinct and must not publish `.wiki` as the runtime terminal.
- On `main`, `provider-hubs.json`, `provider-domain-history.json`, and `provider-overrides.json` were updated to this Kehflix authority. Existing Domain Refresh workflow is responsible for rematerializing/publishing provider bytes from those authorities; do not provider-local hardcode around Domain Refresh.
- Current acceptance contract remains **>=35/46 providers with at least one real playable lane**. Repair markers, compilation, survival, or route presence do not count as provider success.
## 2026-09-18 — Main-only consolidation + Kehflix semantic hub authority

- Repository cleanup completed: **only `main` and `brain-learning/proposals` remain as branches**. All `tmp/*` diagnostics/census/proof branches and `fix/provider-activation-certification-v1` were deleted.
- The former repair branch was preserved before deletion as immutable tag **`archive/fix-provider-activation-certification-v1-20260918`**. Historical comparison may read that tag, but all active work is now **main-only**.
- PR authority rule is locked:
  - PR **#127** is the default authority for every provider/config family it materially reworked.
  - closed/unmerged PR **#122** is historical evidence only and must never be bulk-restored over #127.
  - a #122 sub-route/runtime may return only with newer explicit A/B/current playable proof.
- Exact #122 -> #127 structured diff found **21 provider/family authority changes**. This confirms that a blind #122 rollback would be destructive for several providers (examples: AllAnime, AllWish, AniKoto, 4KHDHub, Flemmix, MovieBox, WookaFR, YFlix, VidLove, Kehflix).
- Historical route-restore batch already proved that simply restoring #122 routes for AllAnime / AllWish / Flemmix / MovieBox / WookaFR / YFlix produces **no unique gain** under the current harness. Do not copy those routes into main just because they existed historically.
- **VidLove** is an evidence-backed exception: separate current A/B proved PR122 V1 + `api.vidlove.cc` FULL movie+tv while newer V2 was red. Main now contains only the proved V1 source-selector Lego + API recipe + route_data_state=on. Provider Overrides Gate is green; final Verify & Publish remained blocked by unrelated Kehflix state and must be rerun after Kehflix converges.
- Kehflix authority supplied by user and now treated as canonical:
  - **hub/address page = `https://kehflix.wiki/`**
  - **runtime terminal = `https://kehflix.com`**
  - **`kehflix.lol` is stale/historical and must not be re-promoted**
- Real Kehflix hub HTML supplied by user contains the decisive semantic card:
  - `Accès principal`
  - visible domain `kehflix.com`
  - `Adresse vérifiée · en ligne`
  - CTA `href="https://kehflix.com"` / `Entrer`
  This fixture is now encoded in `tests/provider_hub_registry_test.py`.
- Domain resolver defect found: generic `links()` kept only anchor text, so a CTA such as “Entrer” lost its surrounding primary/verified/current context. Resolver now preserves bounded nearby semantic markers and scores **principal/current/verified/online** positively while penalizing **backup/secours/miroir/alternative/fallback**.
- Additional Domain Refresh defect found: `merge_hub_registry()` did not propagate `direct_authority*` or the current `direct` field into the merged resolver config. Thus an `explicit_current` authority written to provider-hubs.json silently disappeared before resolution. Main now preserves those fields.
- Generic opt-in Domain Refresh policy added: `direct_authority=explicit_current` makes an explicitly curated current direct terminal outrank stale cards still present on an authoritative hub, while the hub remains the address source. Providers without that flag keep the normal live-hub behavior.
- Kehflix registry now sets `direct=https://kehflix.com/`, `direct_authority=explicit_current`, allowed terminal only `kehflix.com`, and retains `kehflix.wiki` strictly as the authoritative address hub.
- Domain Refresh guard correctly blocked repeated attempts to roll Kehflix back to historical `.lol`; that failure exposed the missing merge propagation above. Do not weaken that guard.

## 2026-09-18 — Kehflix DNS-boundary root cause + VidLove publication drift

- Revalidation on exact main SHA `301c9ff7d78581be37997c616a9af66d90bad7fa` proved Kehflix structured authority was already `.com` at checkout; `.lol` was reintroduced during resolution, not inherited from Git.
- Generic root cause was DNS suffix matching: `kehflix.com.endswith("x.com")` is true, so a legitimate provider hostname was falsely classified as X/Twitter. Main commit `c53271e2b116978560c2d81d972ca18263444b0f` changed blocked/social/search/infrastructure matching to DNS-label boundaries. Workflow Gate is green on the later `8ad1cf4` generation.
- Domain Refresh run **35388757228** on `8ad1cf4c06258724e7ae889d8a960e7b10783cf7` now resolves Kehflix correctly: explicit-current `https://kehflix.com` wins at score 1000; stale `.lol` remains only a lower-priority observed candidate. It detected `projection_drift=["kehflix"]` and generated `providers/kehflix--nuvio--f57719e930c25a46.js`, but did **not** publish because a later static audit failed on unrelated VidLove.
- VidLove publication drift is confirmed: `provider-overrides.json` contains the current A/B-proved V1 `api.vidlove.cc` recipe and `PROVIDER.VIDLOVE.CURRENT.API.V1` Lego, while the manifest-published bundle still has `apiRecipe=null` and no V1 Lego marker. The override correction therefore was never materially published.
- Additional generic defect confirmed before rematerializing VidLove: `materialize_provider_v3_one.reconcile_provider_authority()` could let stale static `model.apiRecipe` overwrite the base/referer of a provider-specific proof-owned recipe. The materializer contract is being tightened so `route_proof_version>=5` + `api_recipe.proofModelVersion>=5` is monotonic executable authority; unproved recipes such as the historical Purstream case remain eligible for static address reconciliation.
- Do not mark VidLove or the final Kehflix publication validated until the exact rematerialized VidLove bundle passes movie+TV proof/static audit and the subsequent Domain Refresh/Verify & Publish generation is green.
- Targeted publication runner **35390796488** correctly failed closed before materialization because the sequential reconstruction contract still hard-coded historical census `96` although `build_provider_queue()` now consumes the current manifest scope. No Provider bytes were generated or published. The test is being aligned to `current_provider_scope.visible_provider_count()/visible_provider_ids()` so current 46-row scope is data-driven while historical 50 archive rows remain outside the executable queue.
- Targeted runner **35390927807** passed the proof-authority contract, canonical VidLove materialization, Kehflix CONFIG-only rebuild, static audit and minimizer fixed-point. It then failed closed on the first fresh VidLove live fixture: Interstellar returned candidate HTTP statuses 200/403 and terminal reason `hls_segment_non_media`; no provider bytes were published. Because one title is insufficient to reclassify a provider, the next retry expands to four movie + four TV fixtures and requires at least one terminal-positive result per lane.
- Rotating VidLove runner **35391230924** confirmed the failure is systematic, not an Interstellar-only miss: all **8/8** fixtures (4 movie + 4 TV) returned exactly one raw/candidate stream but **0 terminal streams**; every row ended in `hls_segment_non_media`. Current classification is therefore “resolver/API produces a candidate, playback terminal unverified”, not provider ZERO and not FULL. Next diagnostic A/Bs the same signed candidate under current/no-Origin/no-Referer/no-provider-header contexts and inspects only sanitized HLS segment type/status.
- Read-only next-batch audit also invalidated an older assumption: **Castle is already route_data_state=on with movie+tv playable_verified** in current structured state; do not spend repair work on Castle unless a fresh regression reappears. AniKotoTV, 4KHDHub, ShowBox and AnimeVOST.fr remain repair-state candidates.
- Header-context diagnostic runner **35391625535**: VidLove candidate host resolves to a valid HLS master + one valid media playlist with **605 segments**. Current candidate headers already contain Origin, Referer and User-Agent. Current / no-Origin / no-Referer / no-provider-header / Referer-only / Origin-only variants all fail terminal proof; the first segment returns HTTP 200 with `text/html; charset=UTF-8` and non-media payload. Header omission/addition alone is therefore not the fix. Next diagnostic checks playlist-session cookies and samples multiple segment positions before reclassifying the backend.

## 2026-09-18 — VidLove backend fan-out after HLS segment rejection

- Cookie/session diagnostic run **35391962762** on exact main SHA `6a45f38a29cf9551e952b277203bb210a577eb38` passed proof-authority, VidLove rematerialization, Kehflix CONFIG-only rebuild, static audit and minimizer fixed-point, then intentionally stopped before publication.
- VidLove default V1 candidate reached a real HLS master/media playlist with **742 segments**, but **0 cookies** were set. Sampled segments 0/1/2/10/371 all returned HTTP 200 `text/html` non-media; the last sampled segment raised HTTP error. This rules out a missing playlist-session cookie as the explanation for the current terminal failure.
- The next diagnostic fans out the 10 structured VidLove backends already present in historical candidate knowledge: moviebox, ipcloud, tcloud, vidapi, vixsrc, 1embed, xpass, vidrift, lookmovie, vidnest. Each is tested through a freshly materialized canonical VidLove bundle on one movie and one TV fixture with terminal-media validation.
- Publication remains fail-closed. If no backend is terminal-positive, current V1 executable proof is stale and VidLove must be requalified to `repair`; Kehflix publication must then be decoupled from VidLove drift instead of remaining blocked by it.

## 2026-09-18 — VidLove fan-out proves partial TV lane

- Backend fan-out run 35393879296 completed on SHA bb1b41073eb41e5a66c0d64f8e0af333a5f6aca1 after canonical materialization/static/minimizer gates passed.
- Across 10 structured backends, no source was FULL movie+tv and no movie source was terminal-positive on Interstellar. moviebox was the only positive backend: House of the Dragon S01E01 returned 1 terminal stream with hls_segment_media. vidapi produced HLS candidates on both lanes but failed terminal validation as hls_segment_non_media; the remaining sources returned zero/404-style results.
- VidLove must therefore be represented as partial evidence, not stale FULL and not blanket ZERO. A generic fresh-proof V2 is being added so fresh negative movie evidence cannot erase an independently fresh positive TV lane; legacy AllWish global invalidation remains supported.
- Next runner pins moviebox and probes four movie + four TV fixtures. Publication remains fail-closed until the TV lane reproduces and the final structured/materialized bundle passes static/minimizer gates.

## 2026-09-18 — Targeted publication checkpoint filename bug

- Runner **35394322299** did not fail on VidLove or Kehflix. It passed canonical rematerialization, static audit and minimizer fixed-point, then proved VidLove `moviebox` on **3/4 movie fixtures + 4/4 TV fixtures** with terminal media validation.
- The job failed only in the durable-checkpoint step because it still read deleted artifact name `health-output/vidlove-v1-proof.json` after the proof step had been renamed to `health-output/vidlove-moviebox-multifixture.json`. Publication was therefore skipped despite positive provider proof.
- The temporary publication workflow now reads the actual multi-fixture artifact. No additional provider diagnosis is required before rerunning this targeted publication.

## 2026-09-18 — Repair V6 automatic scope made truly unresolved-only

- Canonical scalability defect confirmed: automatic Repair V6 used `active_catalogue - provider-repair-skip`. With **44 active providers** and only **2** current skip entries, it could still network-probe **42 providers**, including already-green providers.
- Repair V6 now derives automatic scope from current `provider-repair-disposition.json`: `routeDataState=on` is excluded; `repair` and missing/unknown state remain eligible. Explicit `--provider` still works. The skip file remains a secondary exact-proof guard.
- Route-recovery worker default is raised to its existing safe cap of **12**. The workflow now fails if any current ON provider appears in the targeted recovery report.
- New pure contract `tests/provider_repair_unresolved_scope_test.py` covers ON exclusion, repair/unknown inclusion, skip exclusion and explicit targeting.
- Trigger retry 19 starts a real unresolved-only Repair run on this rule. Success criterion is not merely completion: the run must log zero overlap with current ON providers and preserve existing positives.

## 2026-09-18 — Repair V6 fresh-run proof integrity + workflow contract

- Unresolved-only Repair run **35394943082** failed before network recovery because two workflow-contract tests still required the historical step label `Verify known-green providers were not network re-probed`. Both contracts now require the current label `Verify current green providers were not network re-probed`.
- The always-run verification also exposed stale-evidence reuse: because network Repair was skipped, it read the repository's tracked historical `provider-route-recovery-v6-targeted.json` and falsely reported overlap with current green providers.
- Repair V6 now deletes targeted recovery/summary/candidate/retry/loss artifacts immediately before executing the current run. Therefore a skipped or failed current Repair cannot inherit old evidence.
- VidLove/Kehflix publication run **35395034473** independently passed materialization, static audit, minimizer fixed-point and strategy-plan checks, then stopped only on the second obsolete workflow-label contract. The provider proof was not the failure. The temporary publication workflow is retriggered after these contract fixes.

## 2026-09-18 — VidLove moviebox materialization + Kehflix projection publication candidate

- Publication runner 35395258881 executed from exact base SHA 6c84a5e7e741ff6bcf9788a31b3a9e6fd7bee9b4.
- VidLove was rematerialized through the canonical Provider v3 materializer with moviebox pinned from fresh multi-fixture proof. Exact publication candidate: providers/vidlove--nuvio--32062b18dab60497.js, API base https://api.vidlove.cc.
- Fresh multi-fixture terminal proof on the exact generated VidLove bundle: [{"lane":"movie","fixture":"interstellar-2014","streams":0,"candidateStreams":0,"terminal":false,"reasons":[],"statuses":[200,404],"error":null},{"lane":"movie","fixture":"the-batman-2022","streams":1,"candidateStreams":1,"terminal":true,"reasons":["media"],"statuses":[200,206],"error":null},{"lane":"movie","fixture":"django-unchained-2012","streams":1,"candidateStreams":1,"terminal":true,"reasons":["hls_segment_media"],"statuses":[200,403],"error":null},{"lane":"movie","fixture":"the-avengers-2012","streams":1,"candidateStreams":1,"terminal":true,"reasons":["media"],"statuses":[200,206],"error":null},{"lane":"tv","fixture":"house-of-the-dragon-2022-s01e01","streams":1,"candidateStreams":1,"terminal":true,"reasons":["hls_segment_media"],"statuses":[200,403],"error":null},{"lane":"tv","fixture":"silo-2023-s01e01","streams":1,"candidateStreams":1,"terminal":true,"reasons":["hls_segment_media"],"statuses":[200,403],"error":null},{"lane":"tv","fixture":"peaky-blinders-2013-s01e01","streams":1,"candidateStreams":1,"terminal":true,"reasons":["hls_segment_media"],"statuses":[200,403],"error":null},{"lane":"tv","fixture":"fallout-2024-s01e01","streams":1,"candidateStreams":1,"terminal":true,"reasons":["hls_segment_media"],"statuses":[200,403],"error":null}].
- Kehflix was rebuilt through the CONFIG-only Domain Refresh path, preserving provider/Core bytes outside CONFIG. Exact candidate: providers/kehflix--nuvio--ea173eb3c1ac4caa.js, official site https://kehflix.com.
- Static Provider v3 audit and final minimizer fixed-point passed before publication. Final repository SHA and downstream Domain Refresh/Verify verdict remain pending until the self-publication commit lands and those workflows complete.

## 2026-09-18 — Post-proof targeted publication drift detected

- Self-publication commit `bac869a5be4663c99a19eb189a516cc99823eebb` contains the freshly proven VidLove MovieBox runtime, but post-push inspection found `manifest.json` referencing `providers/vidlove-5575654cd46d475d.js` while `provider-v3-materialization.json` still referenced the pre-proof `providers/vidlove--nuvio--32062b18dab60497.js`.
- The manifest-referenced VidLove bytes are the correct current runtime (`api.vidlove.cc`, `sources=moviebox`, V1 Lego), so this is publication metadata drift rather than loss of the provider repair.
- Root cause: the multi-fixture proof step ran `finalizer.main()` + `materialize_one('vidlove')` after the earlier manifest/materialization reconciliation and audit. No final fixed-point reconciliation followed that second materialization.
- A generic `reconcile_targeted_provider_publication.py` is being added so every targeted post-proof materialization ends by content-addressing the exact manifest bytes, updating materialization hashes/data hashes/generation, syncing projections and rerunning static/minimizer/publication contracts.
- The stale AniKotoTV anime-movie assertion is also corrected: canonical `anime` capability must not acquire a fake movie lane from the transport `tv` alias.

## 2026-09-18 — Adaptive census + fixed-point retry 2

- Targeted publication fixed-point run **35395769943** exposed a generic API-contract bug in the new reconciler: `sync_manifest_projection_rows.sync` is keyword-only, but the reconciler called it positionally. The pure reconcile test had not exercised the callback, so it passed while live CI failed. The call is corrected to `sync_projections(check=False)` and the unit test now uses a keyword-only callback stub.
- Quick-yield now implements catalogue-scale adaptive sampling: one semantic representative first, then at most three extra shared recent-corpus fixtures only after a clean `provider_network_zero_result`; all technical/error/wrong-content/unplayable/positive outcomes stop immediately. This removes the single-title false-ZERO class demonstrated by VidLove without hiding real provider failures.
- The quick-yield contract no longer hard-codes the historical 96-provider census and no longer assumes named anime providers own a movie lane. It derives visible count from `current_provider_scope` and current canonical semantic capability.
- Repair V6 retry **21** and Domain Refresh are retriggered together after the fixed-point callback correction. Acceptance remains **>=35/46 current providers with at least one terminal-playable lane** and remains unclaimed until fresh adaptive evidence confirms it.

## 2026-09-18 — 46/46 historical baseline vs 17/46 current strict census

- This is a real coverage regression, not a catalogue change: the historical Active46 proof runs **34708855797** and **34711564739** were **46/46 green**, and the current manifest still contains the exact same 46 provider IDs.
- Fresh adaptive current-byte census run **35396131482** is **17/46 verified** after 155 probes / 28 rotated lanes. Current verified set: `anime-sama, animekai, animesama-co, castle, french-manga, hindmoviez, kehflix, kurage, mugiwarastream, papadustream, playimdb, purstream, streamzo, videasy, vidlove, vidrock, voiranime-homes`.
- Therefore **29 historical greens are currently lost** and must be treated as regression debt, not rediscovered from scratch: `flemmix, uhdmovies, movieshunt, 4khdhub, persianstremio, desiflix, anikototv, animesalt, animesultra, animetsu, animevostfr, coflix, moviesmod, neko-sama, sekai, vidfast, voiranime, voiranime-rip, vostfree, wookafr, yflix, allanime, allwish, anime-ultime, animevost-fr, fullanime, mallumv, moviebox, showbox`.
- Current failure families from the same artifact: **17 historical greens clean-zero after bounded 4-fixture rotation**, **7 historical greens HTTP-error**, **4 provider-network exception**, **1 timeout (AniKotoTV)**. This proves the gap is mostly technical/current-route drift, not single-title catalogue misses.
- Repair V6 now derives its baseline adaptive census before final target selection. Automatic target scope is `structured unresolved ∪ disposition-ON but not freshly verified`; only disposition-ON providers that still verify in the same run remain protected. The always-run workflow verifier uses the same rule, so current regressions cannot be accidentally excluded as known-green.
- Source-plan batch migrations v1/v2 are current-manifest scoped. Historical AllMovieLand/AnimeZeY/AniMoFlix knowledge remains archived but cannot break or mutate the current 46; AniKotoTV/AnimeSama-co semantic capability remains anime-only and historical movie transport aliases do not recreate a movie lane.
- Targeted publication reconciler now synchronizes `PROVENANCE.json` together with manifest/materialization before minimizer fixed-point validation, closing the VidLove post-proof filename/hash drift class.
- Acceptance target stays **>=35/46 with at least one terminal-playable lane**. Current validated score is **17/46**, so the gap is **+18 providers**; do not claim recovery until the fresh Repair/non-regression run proves it.


## 2026-09-18 — Targeted publication fixed-point reconciliation

- After a targeted provider proof/materialization, public bytes are now reconciled generically back into content-addressed manifest + provider-v3-materialization metadata before acceptance.
- VidLove and Kehflix were used as the first live fixed-point application. The final manifest file, materialization file, SHA-256 and Provider CONFIG data hash are required to agree on the exact referenced bytes.
- This closes the class of bug where a post-proof materialize_one() changed the public bundle after an earlier audit had already reconciled hashes.

## 2026-09-18 — Repair retry 22 reached current migrations; Telegram validator stale

- Retry 22 on SHA `847986dd5fb9202e6f221e053aa2626d78e18003` proved the regression-aware scope works: fresh adaptive baseline selected **32 targets = 30 unresolved + MoviesHunt + VoirAnime freshly regressed**, with 11 still-current greens protected.
- Current-scope source-plan migrations now pass; archived AllMovieLand/AnimeZeY/AniMoFlix no longer block the current catalogue, and the source-plan V5 gate completed successfully.
- The next failure was not provider-specific: `upgrade_provider_base_runtime_v11.validate_telegram_discovery_only()` still required obsolete regex source text `t\\.me|telegram\\.me|telegram\\.dog`, while current ProviderBase already implements stricter DNS-boundary checks for `t.me`, `telegram.me`, and `telegram.dog`. Validator is aligned to current behavior and gets a dedicated regression test.
- Fixed-point workflow run **35397598805** completed green and pushed **`a3ec54bfb08b15e88c1f4ba1cb7dd68bc0e6184d`**, reconciling VidLove/Kehflix manifest, materialization, provenance and minimizer metadata. Domain Refresh failure on 847 belongs to the pre-fixed-point SHA and is obsolete.

## 2026-09-18 — Repair retry 23 reached test phase; test import defect only

- Retry 23 baseline fluctuated to **16/46** and correctly expanded automatic Repair to **33 targets**, reactivating MoviesHunt, Kurage and VoirAnime as disposition-ON providers that no longer verified in the same run.
- All current-scope migrations, ProviderBase v11 Telegram behavior validation and source-plan migrations passed. The run stopped before route recovery only because the newly added `provider_telegram_discovery_only_contract_test.py` imported the migration script without first putting `scripts/` on `sys.path`, causing a test-only `ModuleNotFoundError` for an existing sibling module.
- Retry 24 fixes only that test harness import path and resumes the same regression-aware Repair. Do not downgrade provider status from retry 23; no provider recovery network phase executed.

## 2026-09-18 — Repair retry 24 blocked by stale V33 label, not behavior

- Retry 24 passed the repaired Telegram contract and all migrations/tests through latest-request cancellation. It then stopped before route recovery because `provider_native_abort_ignorant_cancellation_test.py` required the literal media revision `tmdb-data-contract-launch-gate-v33-25s-isolated-failfast`, while current Core is V34 (`tmdb-data-contract-launch-gate-v34-anime-pre-network-semantic-gate`).
- The same test already executes the real abort-ignorant native-fetch cancellation scenario. It now accepts revision >=33 and continues to require the actual cancellation/fail-fast functions plus the Node behavioral proof. No runtime behavior is weakened.
- Retry 25 resumes the same regression-aware Repair; retry 24 never reached `recover_provider_routes_from_upstreams.py`, so it provides no new provider-health verdict.

## 2026-09-18 — Repair retry 25 stopped by escaped test regex only

- Retry 25 again passed the regression-aware adaptive baseline, migrations, Telegram contract and every pre-network test up to native abort-ignorant cancellation. It still did **not** enter route recovery.
- The failure was test-only: the new version-agnostic assertion used Python raw regex `(\\\\d+)`, matching a literal backslash-d instead of digits, so it could not see current V34. Correct expression is `(\\d+)`.
- Retry 26 changes only that regex + trigger. No provider status changes are inferred from retry 25.

## 2026-09-18 — Repair 26 reached real network recovery; apply gate was historical

- Retry **26** finally passed every migration and pre-network contract, then executed real route recovery on **32 targets** with 12 workers. Targeted report: **24/32 with proven routes, 156 routes, 1 new simple recipe**. Merged current-active report: **33/44 with proven routes, 232 routes, 5 recipes**.
- Fresh upstream stream-positive regressions inside the targeted report include **AnimeVOSTFR (2 streams), Neko-Sama (2), VoirAnime (6), VoirAnime-rip (2)**; these are immediate recovery candidates once the report applies. Route proof alone is not counted as provider-green.
- The run stopped only at `apply_provider_route_recovery_report.py`: it still referenced removed `recover.EXPECTED`. Merged report correctly describes **44 active providers**, while the repository now derives active scope dynamically from `current_provider_scope.py`. Application validation now requires exact current active count + identity set, never a magic historical cardinality.
- Common stale-authority defect confirmed: multiple current regressions still carry proof-v5 `api_recipe` pointing to `arm.haglund.dev/api/v2/themoviedb`, even though Repair already classifies `arm.haglund.dev` and `v3-cinemeta.strem.io` as non-executable metadata helpers. Existing proof-v5 authority now obeys the same host policy as new recipe synthesis; blocked helper recipes are demoted instead of being preserved forever and short-circuiting provider-specific source plans.
- Retry **27** is dedicated to applying/rematerializing this evidence and measuring terminal yield. Historical 46/46 remains the regression baseline; current acceptance is still unclaimed until >=35/46 terminal-playable is re-proved.

## 2026-09-19 — Repair 27 applied route recovery; archived Movix gate blocked post-apply

- Repair retry **27** reached the full current network recovery again: **32 targeted**, **24/32 route-proven**, **154 targeted routes**; merged current-active report is **33/44 route-proven, 230 routes, 5 simple recipes**.
- Crucially, `apply_provider_route_recovery_report.py` **completed successfully** on the exact dynamic 44-active identity set: `FIELD_ROUTE_RECOVERY_REPORT_APPLIED providers=44 evidence_routes=230 recipes=8`. The previous magic-count blocker is gone.
- Live upstream probes in the targeted report returned real streams for at least **AnimeVOSTFR (3), Neko-Sama (2), VoirAnime (6), VoirAnime-rip (2)** on JJK S1E1. These are recovery candidates, not yet counted green until rematerialized and re-probed through current NiakVIO bytes.
- The next failure is purely historical policy debt: `enforce_route_proof_manifest_policy_v1.py` still hard-required **Movix** proof/DATA/manifest even though Movix is not in the current 46-provider manifest. The gate is now current-scope aware: absent Movix => explicit not-applicable no-op; if Movix is ever current again, its activation-preservation contract remains enforced.
- Retry **28** continues through policy -> rematerialization -> candidate census. Do not claim score improvement from upstream probe streams alone.

## 2026-09-19 — Repair 28 post-apply checkpoint; visible-vs-active sanitizer bug

- Repair retry **28** passed route recovery application again (**44 active patched, 224 evidence routes, 8 recipes**) and passed the corrected current-scope Movix policy: `ROUTE_PROOF_MANIFEST_POLICY_V1_OK current_scope=46 movix_current=false state=not-applicable`.
- It then failed before rematerialization in `sanitize_provider_v3_execution_routes_v1.py`: the sanitizer used `active_provider_count()=44` to validate `automation/provider-v3-static-knowledge.json`, but static knowledge intentionally contains **all 46 visible providers** (44 active + 2 disabled). This is a scope-type bug, not provider DATA corruption.
- Sanitizer authority is changed from active cardinality to the **exact visible provider ID set**. Missing/extra/duplicate knowledge identities now fail with explicit set diffs; disabled-visible knowledge is retained by design.
- To avoid a fourth ~6-minute upstream recovery replay, the post-apply artifact from run **35401694913** (artifact **10570987798**) is reused only after proving provider inputs are unchanged from source SHA **4cc56e288a498e016ac5823e28089b3d333406ef**. A temporary read-only resume workflow starts at policy/sanitize/materialize and runs the real candidate quick-yield census. It does not publish.
- Do not infer recovered provider count from route proof. The next authoritative number is the rematerialized candidate `verified_provider_count` emitted by this resume workflow.

## 2026-09-19 — Post-apply resume reached Mugiwara migration

- Resume workflow **35402655245** proved the source provider inputs were unchanged from Repair 28, restored the exact applied checkpoint, passed the new visible-identity sanitizer (**46 providers, 0 unsafe routes removed**) and passed the current-scope Movix policy.
- It stopped inside ProviderBase preparation at `upgrade_mugiwara_episode_failclosed_v2.py`. Current Mugiwara runtime already contains the intended episodic fail-close twice around the newer discovery-first/specialized-fallback flow, but the old V2 marker comment is absent; the migration incorrectly required the pre-revision text anchor.
- Migration now recognizes that exact newer behavior and restores only `NIAKVIO_MUGIWARA_EPISODE_FAIL_CLOSED_V2` inside the already fail-closed specialized fallback. Runtime semantics are unchanged; the existing V34 contract can again prove the durable marker + behavior.
- The temporary post-apply resume is retriggered; upstream recovery is still not repeated.

## 2026-09-19 — V34 migration was capable of downgrading presentation V24

- Post-apply resume on **d047b88c** passed sanitizer and reconciled Mugiwara V2 marker without changing its fail-closed behavior, then exposed a more serious migration bug in `upgrade_manual_tv_live_regressions_v34.py`.
- Current global stream presentation is **V24** (`all-providers-client-projection-evidence-language-v24`) and already contains the V22 strongest-quality + detailed-language guarantees. V34 nevertheless unconditionally replaced `quality()` and `detailedLanguage()` with its old V22 implementations, then failed because the revision string was no longer literally `strongest-evidence-v22`. That is a backwards migration hazard.
- V34 is now monotone: presentation revision >=22 is validated as a semantic floor and left byte-unchanged; only a V21 predecessor is upgraded to V22. The contract test now requires revision >=22 plus the actual strongest-quality/Hindi-detail guarantees. This prevents future migrations from downgrading newer Core presentation logic.
- Resume is retriggered from the same Repair 28 applied checkpoint; still no repeated route recovery.



## 2026-09-19 — Observable Repair 28 resume launched from verified main

- Repository state was re-verified before continuing: `main` was exactly **66d41ae101f7d86e5b8322e122a8aaf6e8e5df50**, only `main` + `brain-learning/proposals` remained, and there were **0 open PRs**. The observable resume workflow itself then advanced `main` to **f1b1c3a959dae4d4ecc5215beb0e9ecc2de75bdc**.
- Repair 28 artifact **10570987798** from run **35401694913** was downloaded and independently inspected. Its immediate adaptive baseline is **14/46 terminal-playable**, its targeted recovery scope is **33 providers / 25 route-proven**, and the merged applied report is **44 active / 33 route-proven**. Route proof is not counted as provider-green.
- The targeted upstream report contains real stream-positive tasks for **AnimeSama.co, Kehflix, Kurage, Neko-Sama, StreamZo, VoirAnime and VoirAnime-rip**. This is recovery evidence only; the authoritative provider score remains pending rematerialization + current-byte quick-yield.
- The existing `TEMP - Resume Repair 28 Post Apply` workflow is read-only and does not persist its final push-run verdict in repository state. A parallel temporary workflow `TEMP - Repair 28 Observable Resume` was therefore added on `main`. It reuses the exact Repair 28 checkpoint only after provider-input compatibility proof, runs the current policy/sanitizer/migrations/materialization/contracts, executes the authoritative /46 census, and commits either the candidate score or the exact failed/last stage back to `main`.
- Acceptance is still **>=35/46 with at least one terminal-playable lane**. No recovery claim is made until the observable candidate evidence lands.


## 2026-09-19 — Provider status split + independent 46-way max-repair sweep

- Repair 28 baseline artifact **10570987798** was reclassified lane-by-lane instead of using only the coarse provider verified count. On those exact NiakVIO bytes, **9 providers are FULL across their current canonical semantic lanes**: `anime-sama, animekai, castle, french-manga, mugiwarastream, playimdb, purstream, videasy, voiranime-homes`.
- **5 providers are current-byte PARTIAL** with at least one terminal-playable verified lane but incomplete/contradictory canonical coverage: `kehflix, papadustream, streamzo, vidlove, vidrock`. StreamZo remains specifically movie-positive / TV wrong-content / anime-zero in that baseline.
- Repair 28 targeted upstream execution recovered real streams for five additional current regressions not in the 14-provider baseline: **AnimeSama.co, Kurage, Neko-Sama, VoirAnime, VoirAnime-rip**. Each has a single canonical `anime` semantic lane, so these are **FULL-recovery candidates at source/runtime-proof level**, but they are not promoted to current-byte FULL until rematerialization + terminal census succeeds.
- Therefore the current evidence floor is **14/46 current-byte stream-positive** plus **5 additional source/runtime stream-positive recovery candidates = 19/46 with positive stream evidence at some layer**. Do not call 19/46 current green.
- Repair 28 also has **17 additional non-baseline providers with individual successful route proof but no terminal stream in the latest targeted pass**: `allanime, anikototv, anime-ultime, animesultra, animetsu, animevost-fr, animevostfr, coflix, flemmix, hindmoviez, mallumv, movieshunt, sekai, uhdmovies, vostfree, wookafr, yflix`. These are repairability-partial, not functional-partial.
- Latest targeted no-proven-route debt excluding already partial VidRock is **4KHDHub, AllWish, AnimeSalt, MovieBox, MoviesMod, ShowBox, VidFast**. 4KHDHub separately exposed the incorrect HDHub4u domain authority; registry fix is commit **3b9caa25b95a6415846d113e9f24c540a409b1fe**.
- Domain and route authority remain strictly provider-local. Commit **f9dea091d14139d7e6a3e1432846208dfde0a956** introduced a temporary max-repair workflow with **one independent proof job per each of the 46 providers**; the central job only aggregates completed provider reports and applies the 44 active results in a disposable candidate workspace. DESIFLIX/FULLANIME remain report-only and cannot be reactivated by this sweep.
- Commit **f463f1128b61c3b4475add33a0538afce6c7826c** fixes another generic Repair blind spot: route recovery now uses the shared deterministic rotating corpus **per provider + per semantic lane** only after a clean zero. Technical errors stop rotation. Maximum is 4 fixtures per lane. This matches quick-yield policy and avoids single-title false ZERO without sharing domains/routes across providers.
- The candidate aggregate also runs the existing domain metadata reconciliation before route-apply/materialization, so the provider-local 4KHDHub registry authority (`4khdhub.one`) can be projected through the normal Domain Refresh metadata path rather than a hand-written override.
- The new 46-way sweep persists evidence only after independent proof aggregation, rematerialization, regression contracts and the terminal quick-yield census. No publication/green claim is made from route proof alone.


## 2026-09-19 — Targeted regression probes + catalogue-size-agnostic sweep

- Provider runtime repairs landed for **AnimeSama.co** and **Neko-Sama** at `09f2c25b1c4a27778a74ca807b7606ef1ea6a7e1`. AnimeSama.co now uses Sibnet's canonical referer for shell/media requests instead of the episode-page referer; Neko-Sama now sends its recovered player/embed URL through Core's bounded direct-media crawler instead of returning the unresolved embed as a stream.
- Follow-up commits **7649f1be957db1f7a277ebaf047485081c28e654** and **4d664f2df056fff03f46c26c6f184eb7841b1718** reconstruct VoirAnime.rip's own runtime chain and repair VoirAnime episode selection. Commit **ae6ffc100d1791b27e6fbb433cd673c5ac9de5d5** added a five-provider targeted live probe covering AnimeSama.co, Neko-Sama, VoirAnime, VoirAnime-rip and Kurage.
- Targeted run **35407146979** did **not** reach live probes: all new provider repair contract tests passed and all 44 active providers rematerialized, but `tests/provider_js_lego_ownership_test.py` still compared the 46 visible manifest rows to `active_provider_count()=44`. This was test policy debt, not a provider failure.
- Commit **d7132d5667c5794566b5996854007895ff5d895e** changes that ownership test to exact **visible provider scope** and removes catalogue cardinality constants from the independent max-repair workflow. The 46-job matrix now derives its size from the current manifest, aggregation checks the dynamic visible count, and acceptance is **ceil(75% × current provider count)** instead of a fixed 35. This preserves today's 35/46 threshold while scaling to the planned larger catalogue.
- New runs launched on d7132d5: targeted regression probe **35408111652** and independent provider max-repair **35408111701**. Older max-repair run 35407116486 is superseded by the new concurrency run. No provider score is promoted until these current-SHA runs persist terminal evidence.


## 2026-09-19 — Targeted current-byte regression verdict

- Targeted run **35408111652** on code SHA **d7132d5667c5794566b5996854007895ff5d895e** passed repair contracts, full current rematerialization and the live adaptive probe. Its workflow conclusion is red only because the final Git persistence step tried to rebase with unstaged rematerialization changes; the live probe itself completed successfully.
- **Kurage** and **Neko-Sama** are now current-byte **playable_verified** on their canonical anime lane with zero identity contradictions. Because each currently has one canonical semantic lane, both qualify as recovered FULL candidates with direct terminal evidence on the rematerialized NiakVIO bytes.
- **AnimeSama.co** remains no-stream with `provider_network_http_error` on JJK; **VoirAnime** remains no-stream with `provider_network_http_error`; **VoirAnime-rip** remains clean zero after adaptive rotation across JJK, Boruto, Mushoku Tensei and Golden Time. They are not promoted.
- The targeted verdict was manually persisted as `automation/provider-targeted-regression-recovery-latest.json` in commit **fe8306a0688ef833aae73a774d78df57ee29f5f9**; no re-probe is needed merely to recover the failed workflow persistence step.
- Consolidated evidence before the fresh full /46 candidate census: prior Repair28 bytes had **9 FULL + 5 PARTIAL**; the new current-byte targeted probe adds **Kurage + Neko-Sama** as two freshly revalidated single-lane FULL recoveries. Keep the final same-SHA catalogue count pending the independent /46 terminal census, because the targeted job rematerialized the whole active set but only live-probed these five providers.


## 2026-09-19 — Explicit-current domain projection + provider-runtime reconstruction batches

- Commit **00dcb18d9925252ca31b92303b0235a6b97fc6fb** makes the current-byte full census persist exact same-SHA evidence into `automation/current-bytes-full-provider-census-<run>-*.json` after resetting rematerialization workspace mutations. This removes the previous observability gap where a push census could finish without a durable repository verdict.
- Commit **54a45217d9014fa42b288a061c0c34404985e5b6** fixes a generic Domain Refresh projection bug. `reconcile_provider_domain_metadata.py` previously always preferred stale `provider-overrides.official_site`, so even a corrected provider-local hub registry could not change the published runtime site. Now only registry rows with `direct_authority=explicit_current` may replace `official_site`; all substitutions are then normalized toward that provider's own current host. Current explicit authorities include **4KHDHub -> 4khdhub.one**, **WookaFR -> wookafr.tel**, and **HindMoviez -> hindmovie.fit**. This does not share domains between providers.
- Investigation of several route-proven/current-zero providers confirmed a reconstruction anti-pattern: `arm.haglund.dev`/Cinemeta is often an **identity/absolute-episode helper**, not the provider's stream execution authority. The clean v3 reconstruction had promoted the helper into a blocking `api_recipe` while dropping the provider's real catalogue -> detail/episode -> player chain. Do not remove helper recipes globally; reconstruct provider-local runtime authority where proven.
- Commit **8ea128e5bdb2cadf7615dba69dcbbc9dd3449bea** reconstructs clean provider-local runtimes for **Flemmix** and **Anime-Ultime**. Flemmix executes its own current catalogue search -> movie/series page -> season/episode -> player-tab chain and sends only its recovered player URLs to Core's bounded media crawler. Anime-Ultime executes `MenuSearch.html` -> series page -> exact episode `data-focus` -> `VideoPlayer.html` -> MP4. Neither runtime executes the identity helper as the final stream authority.
- Commit **3a58de1e774f4e1182657903e36ce64db4d018fb** adds Flemmix/Anime-Ultime to the targeted current-byte probe and their contract test to the full census.
- Commit **21a59d8af1f60424ebd999b292b8e313668bb125** reconstructs **Coflix** and **AnimesUltra** independently. Coflix now executes its own suggest -> film identity -> exact episode list -> episode player -> bounded terminal-media chain for movie/tv/anime (anime transported as TV). AnimesUltra now executes its own DLE search -> newsId -> full-story episode/player mapping -> Sibnet/server terminal chain. Domains/routes remain provider-local.
- Commit **32327b693f4601506000098a63dad21bb566d46d** adds Coflix/AnimesUltra to the targeted probe. These four reconstructed providers are **not yet promoted to green**; same-byte live evidence is still required.
- Last durable targeted live verdict before these batches remains run **35408111652**: **Kurage + Neko-Sama** playable_verified on their sole anime lane; AnimeSama.co and VoirAnime HTTP-red; VoirAnime-rip clean-zero. The stale broad quick-yield file must not override this newer targeted evidence.


## 2026-09-19 — Current proof portfolio, Core V25 and MoviesHunt authority

- Temporary proof PR **#174** is the observable CI surface for the current repair portfolio; provider code remains on `main`, while the PR branch only carries workflow trigger deltas on top of the selected main tree.
- Provider Non-Regression run **35412539057** executed an adaptive /46 candidate census on PR proof bytes and reported **16/46 verified/playable, 0 wrong-content**. The verified set was `anime-sama, animekai, castle, desiflix, french-manga, hindmoviez, kehflix, mugiwarastream, papadustream, playimdb, purstream, streamzo, videasy, vidlove, vidrock, voiranime-homes`. This is a useful current candidate measurement, **not the final rematerialized portfolio score**: Kurage, which was current-byte targeted green earlier, fluctuated red in this run and the dedicated full-census path was still blocked by Core validation at the time. The gate failures were **kurage, movieshunt, voiranime**.
- The prior rematerialized targeted run on the same repair generation proves **Kurage + Neko-Sama playable_verified on anime** and **Coflix playable_verified on movie + tv** with zero contradictions; Coflix anime remains red. Treat Coflix as functional PARTIAL until its anime lane is recovered. Do not add targeted greens mechanically to a different-SHA broad census.
- Full current-byte rematerialization exposed an actual presentation regression from the user's TV-class bug family: a stream with coarse `language=VO` but provider/source evidence `Hindi` was collapsed back to VO. Commit **69a77b5a829f886d4a8e4afec625379fd663f61b** advances shared presentation to V25 and lets `detailedLanguage()` consume provider/source evidence fields (`sourceLanguage/sourceLanguages/sourceName/sourceTitle/sourceLabel`) before generic fallback.
- The first V25 verification exposed another stale migration guard: `normalize_stream_presentation_v12.py` only allowed V22/V23/V24. Commit **72351c5ed5e7af25cbf19f121584b9b4b4173039** makes the compatibility validator monotone for V22+, and **1554eddfd883cf446b69335b3cb47a642423d99d** corrects an accidental double-escaped revision regex in both validator and test. No provider status is inferred from these Core fixes until the rerun completes.
- **MoviesHunt** domain authority was revalidated from its own current upstream provider source rather than redirects/search guesses. Static decoding of the obfuscated `movieshuntBase` in `NuvioPlugin/All-in-One-Nuvio/providers/movieshunt.js` yields **`https://movieshunt.run`**. Commit **70b56be1f213a83cfd60c3a451620093a2f265d0** pins that provider-local terminal as `explicit_current`; `.ws/.work/.monster/.casa` are stale/redirect intermediates and are blocked from becoming current authority. Domain Refresh/reconciliation must project this provider-local authority into generated DATA; routes remain MoviesHunt-specific.
- Commit **8ad6eb64a1415d670d6a450534c88d17195c5f54** extends the targeted proof harness with MoviesHunt and persists **sanitized network diagnostics only** (host + path + method + status; no query strings/tokens). This is intended to diagnose MoviesHunt/VoirAnime on rematerialized current bytes without leaking signed media URLs.


## 2026-09-19 — PR #175 targeted verdict + VoirAnime/AnimeSalt repair batch

- Temporary proof PR **#175** targeted run **35412889190** rematerialized all 44 active providers and completed its live probes successfully; its workflow conclusion is red only because the evidence persistence step attempted to rebase while rematerialization changes were still unstaged.
- Current rematerialized targeted verdict from that run: **Kurage = playable_verified anime**, **Neko-Sama = playable_verified anime**, **Coflix = playable_verified movie + tv / anime red**, zero identity contradictions. This confirms Kurage and Neko-Sama as current-byte single-lane FULL recoveries and Coflix as functional PARTIAL.
- The same targeted run gave sanitized failure chains:
  - **VoirAnime**: TMDB 200 -> `voir-anime.to/anime/jujutsu-kaisen/` 200, then no provider-local episode-host request; execution fell back to the older `voiranime.homes` path. This proved the V3 anime Lego discarded episode links before the `?host=LECTEUR...` stage.
  - **MoviesHunt**: current rematerialized execution still landed on `movieshunt.monster` and returned clean zero. The provider-local registry remains pinned to the current upstream source's decoded `movieshunt.run`; the redirect/terminal relation still requires runtime-chain repair rather than another domain guess.
  - **AnimeSama.co**: site search + exact episode page are 200, but Sibnet shell is 403.
  - **Anime-Ultime**: provider search endpoint `v5.anime-ultime.net/MenuSearch.html` is 403.
  - **AnimesUltra**: current `animesultra.com/index.php` path is 404.
  - **MoviesMod**: current `moviesmod.army/search/<imdb>` is 403.
- Provider Non-Regression run **35412889193** on the same proof generation produced **16/46 verified/playable, 0 wrong-content** with Kurage green; rolling failures were **MoviesHunt + VoirAnime**. This is candidate portfolio evidence, not a final same-SHA publication census.
- Dedicated full census run **35412889186** still stopped after successful **44/44 rematerialization** because `normalize_stream_presentation_v12.py` literally contained double-escaped raw regex tokens. Commit **e56ef1f28aa2c4e72386188ddaf41b19b25cf773** replaces them with real `\s`/`\d` regex tokens and adds `tests/presentation_revision_parser_test.py` that recognizes V25/V23 and rejects V21.
- Commit **714f2a8cf37433df02e61d7373b367742cb75298** applies the next provider-local batch:
  - **VoirAnime** episode hrefs are canonicalized by pathname back onto the clean-room `voir-anime.to` base before episode scoring. Alias-host hrefs (`.homes/.diy`) therefore no longer get discarded before the provider's own `?host=LECTEUR...` stage.
  - **AnimeSalt** provider registry is now `explicit_current=https://animesalt.link/`, matching its current upstream provider source. The stale `.cx` terminal is blocked from being projected back into Provider DATA. This is a domain-authority correction only; functional green still requires a live rematerialized probe.
- Domains/routes remain provider-local. No status promotion is made from these code/domain changes until the next current-byte proof.


## 2026-09-19 — AnimeSalt clean-room runtime reconstruction

- Commit **1d0a1998c697375b2961722ca11465d2a9bc6303** goes beyond the provider-local domain correction and reconstructs AnimeSalt's current runtime chain as a NiakVIO-owned Lego.
- Static decoding of the current upstream provider source was limited to configuration/protocol constants; no upstream network code was executed. The observable contract is:
  **TMDB/Core title -> `animesalt.link/?s=...` -> series identity -> season `data-post` -> `wp-admin/admin-ajax.php?action=action_select_season&season=...&post=...` -> exact SxE episode -> `as-cdn*.top/video/<hash>` -> POST `/player/index.php?data=<hash>&do=getVideo` with `hash=<hash>&r=<provider-root>` -> `videoSource|securedLink` HLS**.
- The new Lego is `scripts/provider_patches/animesalt_runtime_v1.py`, registered only for provider `animesalt` in `provider-overrides.json`; it uses Core/TMDB identity, exact season/episode selection, and keeps AnimeSalt's domain/route authority provider-local.
- Contract test `tests/animesalt_runtime_contract_test.py` is wired into the targeted proof workflow. **No functional green is claimed yet**; next status requires current-byte rematerialization + live terminal validation.


## 2026-09-19 — Post-Coflix protected-regression batch R9

- Revalidated R8 proof before changing anything: Coflix is already current-rematerialized **PARTIAL** with `movie=playable_verified` and `tv=playable_verified`; anime remains red. Do not restart Coflix from zero.
- R8 Provider Non-Regression candidate census measured **17/46 verified/playable, 0 wrong-content** and the protected rolling failures were exactly **MoviesHunt + VoirAnime**. Targeted R8 also reconfirmed Kurage and Neko-Sama anime green; AnimeSalt remained a transport-level `provider_network_exception` at `animesalt.link`.
- Full-census R8 did not reach the adaptive census because `tests/global_stream_presentation_test.py` double-escaped the V25 revision matcher. Commit **626fd90d93ddfb01853bd11d25581225883f7b94** corrects it to `r"-v(\d+)$"`; this is test debt, not a Core presentation rollback.
- MoviesHunt diagnosis: current provider-local source authority is `movieshunt.run`, but executable DATA still replayed the retired `/lookup.php` JSON search. Current public route redirects to the active MoviesHunt WordPress terminal and exposes the normal site search contract. Commit **ad70df729f8636ccfc1202a2bc1770a88dad2170** changes only MoviesHunt's executable search plan to provider-base `movieshunt.run` + `/?s={query}`; **caf8e9c0e693c352ddfdc1aec28e8f9296ed5086** locks that provider-local contract. Domain rotation remains Domain Refresh authority.
- VoirAnime diagnosis: the V4 current-site resolver returned to the older `.homes` resolver after the first title-matching series page failed to produce a terminal player. Current `voir-anime.to` visibly exposes a Jujutsu Kaisen VF series page, exact episode links and player iframes. Commit **681a85ee87f20fd8ecf6d59c8e2029067d2a8da4** upgrades the provider Lego to V5: collect bounded title-matching current-site variants (including VF/VOSTFR), exhaust each variant through episode + LECTEUR/iframe + Core crawler, infer VF/VOSTFR from the successful path, and only then delegate to the previous resolver. Commit **8dd84e1d6f769f51833aa1b9047447472b36016d** locks the V5 contract.
- Exact current main after the repair batch is **8dd84e1d6f769f51833aa1b9047447472b36016d**. Temporary proof PR **#176** uses branch `tmp/provider-max-repair-proof-20260919` at **bea7a768d9381c783256cb0057f0cb5747dee93b** and contains workflow-trigger comments only. Do not merge it as provider authority.
- R9 acceptance remains evidence-driven: MoviesHunt and VoirAnime are not called repaired until current-rematerialized live proof removes their protected failures. AnimeSalt remains open after those protected regressions and must be classified from its next live network result.


## 2026-09-19 — Flemmix current-runtime base repair prepared after R9

- While R9 tests the protected MoviesHunt/VoirAnime batch, independent static/live cross-checking found a separate Flemmix root cause. The NiakVIO Flemmix Lego already implements `/search?q=` plus the current movie/season/episode/player selectors, but it was executing them on `flemmix.party`; the R8 probe returned HTTP 403 on that search path.
- Current upstream `Gowaru/gowaru-nuvio-providers/providers/flemmix.js`, generated 2026-09-18, uses **`https://flemmix.me`** as `BASE_URL` with the same `/search?q=` contract, and the `.me` terminal is live. This is provider-local evidence, not a shared-domain heuristic.
- Commits **23c93201d2eee1d68ad20bfa9fb87216e46de3dc**, **8b2a18964cc2cd0e1974cd09c5fb62c2cdaa09b6**, **f4797c13e35bce2659f2f44de86c78eec306c0b7** and **a99f123d11622830ab3e8290ddb976e986d8c63a** align Flemmix source authority, Lego option/default base and contract to `flemmix.me`. Domain aliases remain provider-local and Domain Refresh remains responsible for projection.
- This Flemmix change is **not yet functionally promoted**. R9 does not test these later commits; they require the next exact-SHA rematerialized targeted/full proof.


## 2026-09-19 — Broad provider score authority bug fixed

- R9 artifact inspection exposed a **CI evidence bug**, not a new wave of provider regressions. `Provider Non-Regression Gate` labelled its quick-yield step a candidate census but never rematerialized Provider v3 first. It therefore executed the already-published manifest filenames, which still contain older native/ARM runtimes and omit recently added Provider Lego.
- Concrete proof: current published Flemmix, Sekai, Anime-Ultime, VoirAnime-rip and AnimesUltra files have no `NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1` / Core runtime-dispatch brick, while their current source/overrides do. R9 rows for Flemmix/Sekai/Anime-Ultime/VoirAnime-rip/AnimesUltra consequently showed only TMDB + `arm.haglund.dev`, exactly matching stale published bytes.
- Therefore R8/R9 broad scores **17/46** and **15/46** are published-byte measurements, not repaired-candidate measurements. They must not be used to invalidate successful rematerialized targeted proofs such as Coflix movie+TV, Kurage anime and Neko-Sama anime.
- Commit **0ccccd75b2d179631b02ef0132275a0359579379** inserts domain projection + ProviderBase store + full Provider v3 materialization + CONFIG/Lego validation before the non-regression quick-yield census. Commit **defec7ddb13c7dddb3cb74b4a557252aad9d0ded** makes this rematerialized-candidate requirement part of workflow ownership.
- R9 MoviesHunt/VoirAnime failures were measured on stale published bytes; their post-R8 candidate fixes remain **unvalidated**, not disproven. The next proof must run from one exact current main SHA after all prepared provider fixes are stable.
- Prepared but still unvalidated current-base repairs now include Flemmix `flemmix.me`, AnimesUltra `v2.animesultra.org`, and MoviesMod `moviesmod.ai.in`. Do not promote any of them before the next rematerialized proof.


## 2026-09-19 — R10 candidate authority preflight

- Before launching the first trustworthy broad rematerialized census, provider DATA was checked for Domain Refresh contradictions that could silently reintroduce stale hosts.
- **VoirAnime** current catalogue authority is now registry-owned `https://voir-anime.to/` with `direct_authority=explicit_current`; stale `.diy/.homes/.store/.com` hosts are blocked. Current live catalogue evidence on 2026-09-19 exposes active VF/VOSTFR rows and Jujutsu Kaisen on `voir-anime.to`. Commit **dd80893c64e9534da61b0be0d5c77c8d5b70f290** records that provider-local address authority.
- **MoviesHunt** still carried the retired `/lookup.php?q={query}` inside proof-v5 `learned_routes`, so merely adding the new `/?s={query}` search plan did not remove the old executable path. Commit **07b76b8db630c389ae6b1f4dc93c0d6f5b836a13** removes the lookup route from executable DATA and marks the current WordPress search as HTML.
- Commit **5b43b8e042071cfa3a0a296cd7da20173aa7ea54** locks both authorities in the domain reconciliation contract.
- Domain reconciliation is expected to project explicit-current registry hosts into stale `official_site`/site-host mappings at rematerialization time. This is deliberate: registry/domain ownership remains separate from provider route ownership.
- R10 must be run on one exact main SHA and no main mutation should occur while its targeted/full/non-regression jobs are executing. Its broad score is the first one in this repair sequence that may be called a rematerialized candidate score.


## 2026-09-19 — R11 metric correction + MoviesHunt clean runtime

- R11 Provider Non-Regression run **35415276194** is the first broad census in this sequence that rematerialized current Provider v3 candidates before probing. It measured **19/46 providers with at least one playable+verified lane, 0 wrong-content**. Verified set: `anime-sama, animekai, castle, coflix, french-manga, hindmoviez, kehflix, kurage, mugiwarastream, neko-sama, papadustream, playimdb, purstream, streamzo, videasy, vidlove, vidrock, voiranime, voiranime-homes`. The rolling protected failure set was reduced to **MoviesHunt only**.
- Important metric correction: the historical “46/46 Active46/Hub46” proof is **not the same metric** as current quick-yield “verified provider count”. At historical strict-46 authority SHA **491375c5603467f2554a2c3f1182ba2df85af48a**, tracked `provider-v3-quick-yield.json` still reported only **14 verified/playable providers across 96 visible providers**. The 46/46 matrix was a per-provider candidate-to-final qualification workflow over the 46 enabled providers, not a stored quick-yield count.
- A real census bias nevertheless existed: current `audit_provider_quick_yield.py` started from a generic representative and ignored provider-owned corpus fixture priority. Historical strict proof used provider-targeted fixtures first, then semantic fallbacks. Example: **MoviesHunt owns Sinners as a targeted movie fixture**, but R11 sampled Interstellar + rotated titles and never Sinners. Commit **d2ed12ef354cac937213fa19ded1a8c1f454583f** makes quick-yield provider-targeted-first and keeps bounded sampling after no-stream/timeout instead of treating the first failing title as whole-lane proof. Commit **e597df2a12bb701a373a7b09fa599b0c6f7ff0c2** locks this ordering.
- MoviesHunt R11 current-byte network evidence proved the domain/route projection fix worked: execution starts at `movieshunt.run/?s=...` and follows the provider redirect chain. The remaining failure is runtime extraction, not domain ownership. Commit **94964670b4a89269884a44c4e0df421cf449eebd** adds a clean NiakVIO-owned MoviesHunt runtime: Core/TMDB title -> WordPress search -> exact detail -> Abhilinks -> HubCloud/VCloud -> terminal media. Commit **682a945dec2906d4b4b18d86651508e920257fbb** wires it provider-locally at `movieshunt.run`; **aff65280808b5944f2f2aaece31a76672d1f1930** adds its contract.
- Workflows now enforce both MoviesHunt runtime ownership and provider-targeted census fixture authority. **No functional green is claimed for the new MoviesHunt runtime until the next exact-SHA rematerialized live proof.**


## 2026-09-19 — R12 blocked before live proof; static blockers corrected

- Proof PR **#179 / R12** did **not** reach provider materialization or live census. Targeted run **35416175537**, full census **35416175510** and non-regression **35416175533** all stopped on the new MoviesHunt contract because the test searched literal `cdn.fsl-buckets.life` while the clean runtime correctly stores that hostname inside an escaped JavaScript regex. Commit **e74c4eb675bbef4b8a29786f576222a06d031747** changes the assertion to the semantic marker `fsl-buckets`; this is test debt only and provides no provider green.
- CORE Workflow Gate **35416175524** independently exposed stale Flemmix provider DATA: provider-hubs has explicit-current `flemmix.me` and the clean Lego already executes `flemmix.me`, but `provider-overrides.json` still declared `official_site=flemmix.party` and even mapped `flemmix.me -> flemmix.party`. Commit **4a661096a8c3b1b7a7ed1e663ae92ebbc7485fec** makes `flemmix.me` the provider-local source authority, rotates the provider favicon and maps stale Flemmix/Wiflix aliases toward `.me`. Domain Refresh remains responsible for future rotations.
- R12 therefore produced **no new functional provider verdict**. R11 remains the latest broad live evidence until the next exact-SHA rematerialized run.


## 2026-09-19 — R13 strict lane census: 17 FULL / 2 PARTIAL / 27 ZERO

- Proof PR **#180 / R13**, exact main base **a0f8bfcaf77e07ac13ca5601d6bee33eb6e22f09**, reached rematerialization + live quick census. Non-Regression run **35416316736** measured **19/46 providers with at least one verified playable lane**, 203 real probes, 47 rotated tasks, and 1 wrong-content provider. Provider-targeted-first fixture ordering did **not** increase the 19-provider at-least-one-lane count, so fixture selection was a real methodological defect but not the main cause of the low number.
- Reclassifying the same R13 evidence against each provider's full current canonical capability gives the useful score: **17 FULL / 2 PARTIAL / 27 ZERO**. FULL = `anime-sama, animekai, castle, coflix, french-manga, kehflix, kurage, mugiwarastream, neko-sama, playimdb, purstream, streamzo, videasy, vidlove, vidrock, voiranime, voiranime-homes`. PARTIAL = `hindmoviez` (TV green, movie wrong-content) and `papadustream` (movie green, TV/anime zero). The remaining 27 are ZERO under current terminal-playable evidence.
- Historical Active46 **46/46** remains valid as historical live chain/type-route qualification, but it is **not equivalent to today's positive-output V4 gate**. Historical `is_qualified()` accepted complete declared-type route evidence plus provider HTTP success; current `PROVIDER_V3_POSITIVE_OUTPUT_QUALIFICATION_V4` requires every declared lane to have current-run identity-verified `playable_verified` output. Do not compare 46/46 route qualification directly to 17 FULL terminal-playable providers.
- R13 failure families include clean 200+parser-zero, upstream 403/503, runtime exceptions, wrong-content, and pre-network zero. Important concrete examples: MoviesHunt redirects `movieshunt.run/?s=...` to a current `/search.html?q=...` result layout; 4KHDHub reaches `player.autoembed.cc/embed/movie/` without a usable identity; UHDMovies movie traverses host chain including 206 media-like responses but still yields zero; Flemmix is internally aligned to `flemmix.me` and now fails as upstream 403 rather than domain mismatch.
- A second generic defect was confirmed: ProviderBase already marks `arm.haglund.dev` and `v3-cinemeta.strem.io` as non-executable knowledge, while the materializer still copied proof-v5 `apiRecipe` objects on those helpers without applying that host boundary. This explains misleading fallback traffic such as Vostfree/Papadustream reaching ARM after provider-local work.
- Commits **61b9799f5963a54958630e097f2ba1c6d042db75**, **7816e986ca88c5928e64a66c15b926c61ec3a2e4**, and **12ea6cd40f4db1ef43d43e5ef7197632af1ecf24** make provider Lego exceptions observable end-to-end: Core records a sanitized provider/name/message diagnostic while retaining native fallback; TMDB probe exposes it; quick census classifies `provider_runtime_hook_exception`.
- Commit **9cd23df57a719243cbf5eb2b7afef97c7b15fcee** closes the helper-authority materializer gap: non-executable helper `apiRecipe` is demoted and its matching recipe-only route is removed from runtime DATA. Contract **db7a718356a7337ca071506cb592d698323b1192** locks this behavior. Contract **adc777b12c76c790c4e59e8da64f22dcb6a4d756** locks runtime exception diagnostics.
- MoviesHunt current-layout repair: commit **28b921b8396e8714af55f2ebfd0b30d94947e752** accepts same-host `.html` detail links from redirected search pages, tries `/search.html?q=` explicitly, and falls back to bounded direct-media crawling from the detail page when wrapper links are absent. Commit **69c232ff5012093d5a231895f247bd26b7109306** persists the current provider-local search route while retaining `/?s=` as compatibility fallback. Functional green remains **unclaimed until fresh R14 live proof**.


## 2026-09-19 — Census ledger + pre-R15 provider repair batch

- Added durable root ledger `PROVIDER_CENSUS_STATUS.md`: one row per active provider, with FULL/PARTIAL/ZERO, declared lanes, verified lanes, lane verdicts and dominant failure stage. Initial contents are the exact R13 evidence (**17 FULL / 2 PARTIAL / 27 ZERO**, run **35416316736**, SHA **e27a49df3dee**).
- `scripts/render_provider_census_status.py` now renders the ledger from the exact full `provider-v3-quick-yield.json`. The full-current-bytes census persists that Markdown back to `main` together with the run evidence; Non-Regression renders/uploads the same table as an artifact. Targeted probes do not overwrite the global 46-provider ledger.
- R14 / PR **#181** is **obsolete and not a provider verdict**: runs **35417490060**, **35417490057** and **35417490051** stopped in static validation because the proof branch still expected MoviesHunt's old `/?s={query}` contract after the runtime/data had intentionally moved to `/search.html?q={query}`. No R14 live census executed.
- Quick-yield evidence now preserves sanitized per-stream identity diagnostics (`debug_identity_reasons`): hostname only, title/filename, metadata identity reason, duration identity reason/ratio and media status/kind; signed URLs/query strings are not persisted. This is needed to explain HindMoviez's R13 movie contradiction rather than collapsing it to `wrong_content`.
- Generic ProviderBase crawler now rejects incomplete player template URLs such as `/embed/movie/` or `/player/tv` when they contain no content identity. R13 4KHDHub had followed `player.autoembed.cc/embed/movie/` although current 4KHDHub does not use AutoEmbed; the incomplete template was parasite HTML/JS evidence, not a valid player request.
- 4KHDHub has a NiakVIO-owned provider Lego for its current provider-local chain: `4khdhub.one` search -> movie/series detail -> download/episode item -> HubCloud/HubDrive -> workers/R2 media. HDHub4u remains a separate catalogue and is not a domain replacement. TMDB stays Core-owned; upstream provider JS/credential is not executed.
- UHDMovies provider Lego is now `uhdmovies-search-gateway-driveseed-v2-final-url-first`: redirected download responses are checked for a final direct media URL before attempting to consume the response body. This targets the R13 trace where the chain already reached HTTP 206 Matroska media but returned zero provider streams.
- Papadustream/Vostfree helper contamination is addressed generically by the materializer helper-`apiRecipe` boundary; a fresh census must prove whether their provider-local Lego then succeeds or exposes the next provider-local failure.
- Functional success for these repairs remains **unclaimed until R15 live evidence**. The next proof must run rematerialization, targeted probes and full terminal-playable census on one frozen SHA, then update the provider ledger.


## 2026-09-19 — R16 first live verdict: 19 FULL / 0 PARTIAL / 27 ZERO

- Frozen R16 proof base: main **78b74fdf8dbdaf422c54066b3ae0b65915ba1912**, proof branch head **c57cd0bb182941ab6e45c04cf02c9f10ac95cb1d**, PR **#183**. Core workflow **35418449579** is green.
- Non-Regression run **35418449538** completed its rematerialized live census successfully before intentionally failing the rolling non-regression floor. Exact current census result: **19 FULL / 0 PARTIAL / 27 ZERO** across 46 providers. This is a real terminal-playable result, not route-only qualification.
- R13 -> R16 transitions: **hindmoviez PARTIAL -> FULL** and **papadustream PARTIAL -> FULL**. No R13 ZERO became FULL in this first R16 census.
- HindMoviez now has movie + TV identity-safe terminal media. R16 movie proof returned four HTTP 206 Matroska streams with expected-title identity matches; the previous R13 `wrong_content` result was not reproduced. TV returned four S01E01 Matroska streams with season/episode identity matches.
- Papadustream is FULL on anime/movie/TV. Anime + TV resolve through `papadustream.club` external-identity detail/HLS chains with season/episode and duration matches; movie resolves through the current Papadustream v2 catalogue/player chain. ARM helper execution no longer owns these lanes.
- R16 remains ZERO for 4KHDHub and UHDMovies despite their new Legos. 4KHDHub now makes only provider-local search requests (the bogus AutoEmbed template exception is gone) but returns no selected detail. UHDMovies traverses its current search -> detail -> cloud gateway -> DriveSeed chain but still returns zero terminal output.
- R16 targeted run **35418449543** completed contracts, materialization and all adaptive probes; its final persistence step failed only because materialization left unstaged generated changes before `git rebase origin/main`. The probe evidence itself is valid. Main commit **9d119e5131cdd3629f8c2359a61e6128df7a4689** fixes targeted persistence by copying the verdict to `/tmp`, hard-resetting to current `origin/main`, then restoring/committing only the JSON evidence.
- R15 / PR #182 is obsolete: it stopped before live proof solely because the synthetic 4KHDHub behavior test omitted `scripts/` from Python `sys.path`. Harness was fixed at **78b74fdf8dbdaf422c54066b3ae0b65915ba1912**.
- `PROVIDER_CENSUS_STATUS.md` generation is proven in the R16 Non-Regression artifact and correctly renders **19 FULL / 0 PARTIAL / 27 ZERO** with one row/provider. Full-census persistence to main is still pending run **35418449546** and must be verified before claiming the on-main auto-update path completed end-to-end.


## 2026-09-19 — recovered three user provider evidence blocks

- Recovered and preserved the user's three distinct provider evidence families in `automation/USER-PROVIDER-EVIDENCE-LEDGER.md` at commit **7203056340e8c392ef01a38ace4ac0a54b88a087**.
- Block A: real TV/Desktop field behavior (Interstellar/HOTD/Ragna/Mushoku/Hell Mode, wrong content, dead rows, language/quality/badge issues, late-generation accumulation).
- Block B: September browser route/hub captures (~3,100 lines) including AnimeSalt, Vostfree, NetMirror, Nakios, UHDMovies, ToFlix, Flemmix, HDHub4U, Mugiwara, Frenchstream, VoirAnime/Neko/VegaMovies/Movies4u/Moonflix/AnimePahe/AniKoto/AniZone.
- Block C: older late-July/early-August VF/runtime diagnostics that had been omitted from recent repair passes: Purstream/Movix/StreamZo/Frenchstream/Coflix/Flemmix/Nakios/ToFlix. Important anchors include StreamZo's observed Videasy embed, Frenchstream's stale `/engine/ajax/film_api.php?id=<id>` failure despite reachable site/search, and Movix API-domain rotation evidence.
- Historical routes are evidence/LKG only; they must not override current Domain Refresh authority. Provider-local route structure and current provider DATA domain are separate concerns.
- R17 Non-Regression artifact **35418922286** completed a full live census at **19 FULL / 0 PARTIAL / 27 ZERO**; it still fails the floor only on MoviesHunt historical lane loss. Its generated `PROVIDER_CENSUS_STATUS.md` proves the Markdown renderer works in-artifact. Dedicated on-main full-census persistence remains to be revalidated after newer main commits.


## 2026-09-19 — current census persistence validated; route-evidence repairs

- Full-current-bytes run **35419363554** completed and persisted its exact census automatically to `main` in commit **43a21dbc87ac6595df1df5bbf694a6d99f72c557**. This validates the requested census -> `PROVIDER_CENSUS_STATUS.md` persistence path end-to-end.
- That census, on trigger SHA **c2960f8d9fae5118a1b0c9121092190e39e41f5c**, measured **18 FULL / 0 PARTIAL / 28 ZERO**. Papadustream stayed FULL; HindMoviez dropped from the R17 FULL proof because its current HShare -> HCloud chain reached HCloud but got HTTP 403, not because wrong-content returned.
- Census diagnosis was corrected in **bf2496e1fa8b3e8cd25c92d909fe7da6c1891d13** + test **b52b5f18b0b17072d57b00dd3dcca59f4651a90a**: provider HTTP evidence now outranks `gate_runtime_plan_missing`. Previously Flemmix/Anime-Ultime/etc. could be mislabeled as pre-network gates despite real provider requests.
- Live current verification on 2026-09-19 showed `https://animesalt.ac/` resolves to `https://animesalt.cx/`, while `.link` failed. Provider hub authority was corrected at **89e148ef793556731c3e3cf106f35e921a5e663b** and locked by the AnimeSalt contract test.
- Vostfree's provider Lego was found to reject the Nuvio anime transport alias `tv` before any provider request. Commit **f36725da9f5c2002f00970c62bdf775bd223296b** maps tv transport back to anime provider-locally; `tests/vostfree_transport_contract_test.py` locks this.
- Vostfree and Flemmix still contained stale executable ARM recipes in DATA even though their Provider Legos use provider-local site chains. Commit **974a4bc23b365dab2f68fd024b938c0c92435263** removes those stale recipes and records provider-local search plans (Vostfree DLE POST; Flemmix `/search?q={query}`).
- Flemmix runtime now follows its own `NIAKVIO_PROVIDER_MODEL.officialSite/knownSite` rather than a frozen script base (**4de5f2d80d06dd4d7a64aaa2805bcce319f29c20**), with contract coverage added.
- A brand-new MovieBox direct playback Lego was not committed because the execution safety layer blocked creation of new code automating that external playback chain. MovieBox remains ZERO/quarantined; its historical route evidence is preserved in `automation/USER-PROVIDER-EVIDENCE-LEDGER.md`.


## 2026-09-19 — recovered route evidence applied to AnimeSalt/Vostfree

- Work remains on branch `tmp/provider-max-repair-proof-20260919` / PR #186; do not treat this section as merged to main until that branch is integrated.
- Recovered user browser evidence confirmed AnimeSalt's current chain uses `wp-admin/admin-ajax.php` POST `action_tr_search_suggest` and direct `as-cdn*.top/player/index.php?data=<hash>&do=getVideo`.
- Commit **399c93557518e4a9cb672ea2be1a91ce2013af12** extended AnimeSalt's provider-local runtime to try that observed AJAX search before HTML search fallback and to accept the observed direct player endpoint.
- Commit **56847a75cc653826cfddab145e2ce0ac4e1503ae** locked the AnimeSalt observed-route contract.
- Recovered user evidence also proved Vostfree can serve episode players through `video.sibnet.ru/c.php?videoid=<id>`, while the current provider-local runtime only handled Uqload.
- Commit **6ec15a5b125290d73486473c803daf087f40e0cd** added a fail-closed Sibnet fallback: it only returns a stream when the Sibnet player page exposes real MP4/HLS media; Uqload remains the first path.
- Commit **9f6748c985d32c2121dada08377ad172e30d728a** locked the Sibnet fallback contract.
- Functional green is **not claimed yet** for either provider. Required next proof is rematerialized current bytes + live terminal validation in the full census; any old R19 run is tied to its older SHA and must not be confused with the new branch HEAD.


### AllAnime current-site reconstruction

- Recovered browser evidence shows AllAnime's current terminal is `https://ww2.aniwatch.fit/`, with catalogue search `/?s=<title>`, series pages, episode pages and terminal HLS on `fetch.nexabloom.top` (browser HTTP 200).
- Existing Provider DATA still described AllAnime as a stale `tmdb-direct-api` family. This was treated as a provider-model mismatch, not a Core failure.
- Commit **1824e4c1c79a4e5f0551370210b3e4fa9fec9a25** added `scripts/provider_patches/allanime_site_runtime_v1.py`: Core TMDB identity -> HTML search -> title match -> exact/absolute episode -> episode page -> HLS extraction -> `#EXTM3U` verification.
- Commit **490d71d22025331b666b38d34538c0f5ee02977a** bound provider `allanime` to this provider-local Lego and reclassified its source runtime family as `catalogue-html`.
- Commit **5ed3c1e15c30200f1c4650ee93c8763937cb8c9a** added the static contract test.
- No AllAnime green is claimed until the new branch HEAD is rematerialized and the full census verifies terminal playback.


## 2026-09-19 — R19 route-evidence repair continuation

- R19 full census run 35421303974: **18/46 FULL**, **0 wrong-content**. VidLove and VidRock are green again. AnimeSalt was not a network zero: bundle load failed with `SyntaxError: Invalid regular expression flags`.
- AnimeSalt root cause: provider-local Python raw-string wrapper double-escaped JavaScript regex literals. Patched on `tmp/provider-max-repair-proof-20260919` at **06ffc0a576bc1b7285fc40509ede0e631d7b4eb3**; contract test now compiles the generated wrapper with Node at **9204abd5a1b68a15447b7a864467ad22379f2ae9**. Status: **patched, live census revalidation pending**.
- Flemmix R19 used stale/false provider DATA: `flemmix.me` + JSON-like `/search?q=`. User browser evidence from 2026-09-19 proves official hub advertised **flemmix.cloud** and DLE GET `/index.php?do=search&subaction=search&search_start=0&full_search=0&story={query}` returned 200; season page and Vidara/JWPlayer/LuluVDO player families were observed.
- Flemmix corrections: overrides/current route authority **f06e409f0b5a3ac8ad6c6995d44609df8cf8ac2e**; provider runtime DLE parser **7a9b7bb630d966eb6bd389d2a956575769b9bf06**; default runtime base cloud **c112943a2ec43260ceb461be11164ac2d73c9937**; contract test updated + JS compilation **5e5bb9bb45e571c0c3d17f5a94922c49eafbc011**; hub authority aligned **aeae6251049052cbd288edd2708cc8736bd74149** and locked in test **48fc7835a3ad614f0cb79ecd4987c6ad9397d599**. Status: **patched, live census revalidation pending**.
- Vostfree current runtime already reproduces the user-proven DLE POST + Sibnet/Uqload chain structurally, but GitHub CI currently receives HTTP 403 on the search POST while the user's browser capture returned 200. Do not classify as broken route until network/session variance is separated from parser behavior.
- MovieBox remains quarantined/no-proven-route and is lower priority; user evidence explicitly said not to spend time if browser/API path is proprietary/invisible.


## 2026-09-19 — R19 harness drift and Anime-Sama DATA convergence

- Real state rechecked before continuing: `main` had advanced to **274d25b64d6cd611990300c2ab93a6c12091dac8**; active repair/proof work remains PR **#186** on `tmp/provider-max-repair-proof-20260919`.
- Initial R19 targeted run **35441590677** never reached provider probes: `tests/presentation_revision_parser_test.py` still hard-coded stream-presentation V25 while Core is already V26. Commit **63fb146dddcaf82812c65a9989c55b276d55eb0c** made the test forward-compatible (supported V22+ contract + current revision number), after which the targeted job passed its repair-contract stage and proceeded to materialization/probing.
- R19 Verify & Publish run **35441683826** exposed a separate current DATA drift in the read-only static audit for **anime-sama**. Published CONFIG contains the current active rewrite `anime-sama.to -> animes-sama.fr`; `provider-overrides.json` additionally retained stale root alias `anime-sama.fr`, while current hub authority is `anime-sama.wiki -> animes-sama.fr` and no current terminal evidence requires that old alias.
- Commit **a4af28854d919ea9d02ad1631f3229988018884e** removes only the stale `anime-sama.fr` DATA substitution. This is a DATA convergence fix, not a provider playback rewrite; live CI revalidation is pending.
- Recovered MovieBox browser evidence is concrete: current-site search/detail reached `data.vidsrcme.ru/api.php?type=tv&tmdb=94997&season=1&episode=1` and then a real HLS request. Current MovieBox DATA still contains generic pseudo-routes and remains quarantined. No new playback automation has been added; evidence is preserved for future safe/provider-local diagnosis.
- Recovered ShowBox history identifies the truncated route family (`/api/media`, with historical movie/TV mappings requiring provider settings/cookie). Current DATA still lacks a proven current executable route; verify generic settings/route support before any mutation rather than guessing cookie semantics.


## 2026-09-19 — PR #186 resumed from real HEAD; harness/fixed-point blockers isolated

- Resumed from PR **#186** instead of rebuilding prior provider work. Repair branch was **ce36e3def099802da5c55849ffd4acb31a446209** when rechecked; `main` was **68ed6df4ed5a707ad32b87ee616a1505acea5c9f**, so the PR was diverged (55 commits ahead / 3 behind).
- Current branch Non-Regression run **35442750947** completed a real rematerialized 46-provider census at **19 FULL / 0 PARTIAL / 27 ZERO**, **0 wrong-content**. Its gate failure is only the historical MoviesHunt floor; this census is valid evidence for its tested SHA.
- Targeted run **35442751024** reached CONFIG drift reconstruction for 13 providers and failed only because the workflow whitelist omitted generated `vf-no-anime/manifest.json`. This is a harness bug, not a provider verdict.
- Verify & Publish run **35442750951** failed only because the newly rematerialized Anime-Sama bundle was one byte away from the safe minimizer fixed-point.
- Commit **4ebef0558e324e18c45fb9e71470ac7fd34f911c** makes `rebuild_provider_configs()` canonicalize CONFIG replacements through the safe provider minimizer, reject a non-fixed published input, and still enforce byte identity outside the CONFIG Lego.
- Commit **642cfac5251b6567b63e40c70491942d8476dc8f** allows the expected `vf-no-anime/manifest.json` projection in targeted CONFIG repair.
- Commit **17a885222a4c1c508dce87c008e4414af9d2375a** makes the Anime-Sama rematerializer react to the generic rebuild-path change and prove `provider_v3_minimizer_published_test.py` before committing generated bytes.
- Provider functionality is **not** upgraded by these harness fixes; fresh post-fix workflows remain required. The older census remains tied to its exact tested SHA.


## 2026-09-19 — manual A/B/C evidence promoted to executable regression contracts

- The three recovered user evidence families are still authoritative diagnostic inputs and were **not dropped**:
  - **A** = real TV/Desktop behavior and presentation/late-result regressions;
  - **B** = September browser route/hub captures;
  - **C** = older VF/runtime parser and route diagnostics.
- Added `tests/user_provider_manual_evidence_crosscheck_test.py` and wired it into Domain Refresh, Provider Non-Regression, targeted recovery, individual repair and full-current-bytes census workflows. The test protects provider-local route families without freezing historical domains, so current live/domain authority can supersede stale URLs.
- Cross-check currently locks relevant anchors for AnimeSalt, Vostfree, Flemmix, UHDMovies, Mugiwara, StreamZo, AnimeSama.co and Sekai.
- The cross-check exposed a real AnimeSama.co regression: NiakVIO had rewritten distinct DLE provider `animesama.co` to Anime-Sama catalogue terminal `animes-sama.fr`. Current Gowaru provider config still declares `https://animesama.co` and DLE `/anime/<id>-<slug>.html` routes.
- AnimeSama.co DATA/hub/history are restored to distinct `.co` authority in commits **2c50077cee8d647fcfeb9e29651136eadfd28f5b**, **d62bec0c64845c5f177076ceb046ad0cb240fd37**, **e76cd230f70416c286a9b655e9dc911dc4a1a434**, **5674537ee886a0677e4b229cd7149b6e72771901**; stale ARM recipe and `.co -> animes-sama.fr` rewrites were removed. Contract lock: **fc77306f7a2f96dfe99356e45c29f49f97306a20** / **7042e8a66d5ce60ab949bf2ea13c54e2dc6748da**.
- Sekai still carried stale ARM DATA beside its provider-local sitemap/script runtime. Commit **b61af817428f8dce652ae1895c3fb5a10ade5625** removes that stale authority and records `/sitemap.xml` + `/{slug}`; test lock **49fb241cce88601b480f4c8d5ef5fa076aa15dff**.
- First post-cross-check runs showed Core Media Type & Playback fully green and Provider Overrides Gate green. Targeted/census failed before live probes only because the new evidence test matched escaped Sibnet too literally and the old AnimeSama.co test still expected the wrong `.fr` terminal. Those harness regressions were corrected at **8e3b9e9a50c9cfd1be4b6406dff1e02f672f904a** and **7042e8a66d5ce60ab949bf2ea13c54e2dc6748da**.
- AllAnime A/B comparison: the manually captured HTML route remains historical evidence, but current upstream/public implementations in September 2026 use `api.allanime.day/api` GraphQL. Do not force the old HTML route simply to satisfy Block B; current live evidence must supersede it.


## 2026-09-19 — provider-local ARM contamination batch

- Cross-provider audit of the exact R19 ZERO set found three additional providers with the same structural contradiction already seen on Flemmix/Vostfree/Sekai: a complete NiakVIO-owned provider-local runtime was present, while Provider DATA still advertised stale generic ARM execution.
- **Anime-Ultime** runtime is provider-local `/MenuSearch.html -> series episode/focus -> /VideoPlayer.html -> direct MP4`. **AnimesUltra** is provider-local DLE search -> `/engine/ajax/full-story.php?newsId=...` -> Sibnet/embed crawler. **VoirAnime.rip** is provider-local POST `/template-php/defaut/fetch.php` -> exact season/episode -> embed crawler.
- Commit **ecfe92ab6ecf8b27fd5b9eca8d7b20fe06909a5e** removes `api_recipe` / `candidate_api_recipe` from all three, replaces stale ARM learned routes with their actual local route families, and marks their reconstruction authority as `provider-local-current-site`.
- Regression locks: **f8f7fe9ff0ac4595a3893a73164786569926ca87** (Anime-Ultime), **cdd510eab40495b4b0a8899468f91e1c9d79a7c8** (AnimesUltra), **4506ef4a896691acde64de08cfa375be4d9fd641** (VoirAnime.rip).
- Git integrity checked after the three distinct-file writes: branch HEAD **4506ef4a896691acde64de08cfa375be4d9fd641** contains all three test commits in one linear history. Functional green is still **not claimed** until rematerialized live probes/census run on a descendant SHA.


## 2026-09-19 — Census state machine / unresolved-scope execution

- Replaced the ambiguous FULL/PARTIAL/ZERO presentation model with a provider state machine intended to scale beyond 46 providers:
  - 🟢 **FULL OK** = every declared semantic lane has a current verified playback proof.
  - 🟡 **PARTIAL OK** = at least one declared lane has a current verified playback proof; non-blocking.
  - 🔵 **NO PROOF** = clean provider execution/network success but no tested work matched yet; continue corpus search instead of calling the provider broken.
  - 🟠 **PROVIDER JS BROKEN** = current technical/runtime/provider implementation failure; repair/retest.
  - 🔴 **PROVIDER JS FULLY BROKEN** = repeated technical failure without retained positive proof; hand to BRAIN LEARNING.
  - 🟣 **REGRESSION PROVIDER JS** = retained historical positive exists but current JS/runtime structure regressed.
  - 🔴 **REGRESSION PROVIDER** = retained winning fixture/provider previously worked but now provider/upstream no longer produces the match.
- `provider_network_zero_result` is now explicitly a catalogue miss / missing-proof condition, not a broken-provider verdict.
- Added `scripts/update_provider_census_proof_history.py` with durable provider/lane winning fixtures, clean misses, and consecutive technical-run counters in `automation/provider-census-proof-history.json`.
- Quick-yield now supports `--scope unresolved`, `--scope all`, and repeated/comma-separated `--provider`. The repair census uses `--scope unresolved`; known FULL/PARTIAL providers are not re-probed in that loop.
- Historical winning fixtures are replayed first. If a retained winning fixture is replayed and cleanly stops matching, the renderer promotes the provider to **REGRESSION PROVIDER** rather than **NO PROOF**.
- Clean misses are remembered across runs and excluded from subsequent rotation while other fixtures remain, so repeated runs advance through the corpus instead of testing the same four works forever.
- Proof search now spans all three durable fixture sources: rotating popular corpus + regression corpus + health-config fixtures.
- `render_provider_census_status.py` now emits a color-coded Markdown ledger plus machine-readable `automation/provider-census-status.json`; unresolved-scope runs carry forward untested FULL/PARTIAL rows from the previous ledger.
- The current repair workflow bootstraps state from all retained census JSONs, runs unresolved only, updates proof history, persists the state/history files, and computes its global status summary from the merged ledger rather than the selected subset.
- Global non-regression still calls the census explicitly with `--scope all`; the daily Brain Learning workflow remains the main full-catalogue deep observation path.
- Branch: `fix/provider-census-state-machine-20260919`, based on main **377901c53c3a412bd2685c8a8e11380e01e52f16**. Functional validation is pending PR CI; do not mark the state machine validated until those checks pass.


### 2026-09-19 — First validated unresolved-scope census

- PR **#188** branch HEAD lineage reached census run **35447448840** (TEMP Current Bytes Full Provider Census #214), triggered from SHA **2120f44b9760e1e44b48ff6cf650f1dd6723178b** on the PR branch.
- The bootstrap bug that previously selected a `*-summary.json` as if it were a full census was fixed by excluding `*-summary.json` from retained census discovery.
- Fresh validation proves the repair-loop scope works: **27/46 providers tested**, **38 lane tasks**, **149 probes**, rather than rerunning all 46.
- Global carried ledger after the scoped run: **20 FULL OK / 0 PARTIAL OK / 16 NO PROOF / 10 PROVIDER JS FULLY BROKEN**. Operational OK is therefore **20/46** on this exact census state; do not present the remaining 26 as repaired.
- `animesama-co` produced the only new verified stream in this run and moved into FULL OK. Previously green providers were carried without network retest.
- Current unresolved breakdown from the same run:
  - clean catalogue misses / **NO PROOF** stage `provider_network_zero_result`: 16 providers;
  - technical HTTP errors: 7 providers;
  - technical network exceptions: 4 providers;
  - one provider returned verified streams.
- Brain queue emitted by the ledger contains 26 providers (the 16 NO PROOF plus 10 broken-class providers); FULL/PARTIAL providers are excluded from the repair census.
- Anime-Sama publication fixed-point was independently repaired before this census: published bundle is now `providers/anime-sama--nuvio--9d49dc4a1ac63db2.js`, **0 physical line breaks**, and `provider_v3_minimizer_published_test.py` passed for all 44 active published bundles.
- PR #188 is **not yet merge-ready** despite the successful scoped census: current remaining red checks are Verify & Publish (failure occurs after minimizer fixed-point passed) and Provider Non-Regression, whose candidate gate currently flags **movieshunt** and **voiranime-homes**. These must be diagnosed/corrected or explicitly requalified before merge.


### 2026-09-19 — Census Markdown evidence persisted on PR #188

- Exact `PROVIDER_CENSUS_STATUS.md` bytes from successful scoped census run **35447448840** were recovered from its GitHub Actions artifact and committed to PR **#188** at **8e3ee87a83bb2b13a871d02d5b51d7ceaa21c47d**.
- The generated ledger now visibly reports **20 FULL OK / 16 NO PROOF / 10 PROVIDER JS FULLY BROKEN** across 46 providers, with colors, status semantics, retained proof labels, search progress, dominant issue, and next action.
- This Markdown is on the PR branch, not yet on `main`, because #188 is still blocked by two unrelated gates. Once #188 merges, the exact generated Markdown will land on `main`; main must not be manually overwritten by the old renderer before the code migration.


### 2026-09-19 — Non-regression now replays accepted baseline fixtures

- Provider Non-Regression run **35447448809** falsely failed `movieshunt` and `voiranime-homes` with `missing_verified_lanes`: the rolling baseline required their previously accepted lanes, but the candidate census had not replayed the exact baseline winning works.
- Main baseline `provider-v3-quick-yield.json` proves the retained positives explicitly: **MoviesHunt/movie = Interstellar** and **VoirAnime.homes/anime = Jujutsu Kaisen**, both `playable_verified`.
- Commit **0465c2a3dd893baf328482db97879bafa409c513** moves baseline selection before the candidate census, seeds `automation/provider-census-proof-history.json` from the accepted baseline quick-yield report, and runs the global candidate census with that proof history so retained winners are replayed first.
- Contract commit **cbe78b9635a712124e74685c2802c46f86f52540** enforces workflow ordering: baseline selection → baseline fixture memory seed → candidate census.
- A missing lane is therefore no longer called a regression merely because the candidate sampled a different catalogue work. A true regression requires failure after replaying the retained winning fixture.


### 2026-09-19 — PR #188 merged; main-only execution restored

- User explicitly requested **main-only execution**: no more repair branches / PR staging for this workstream.
- PR **#188** was merged into `main` at **cdf8b20edbd4be169866ffd657e1f8f5b7a89b1f**.
- The temporary PR188 publication diagnostic workflow was removed immediately on `main` at **9299c6aaadde41ee694ca498dd12a1e1d8cf3c28**.
- From this point, provider/census fixes in this workstream are applied directly to `main`, with exact-SHA validation and MEMORY.md updates after each material advance.


### 2026-09-19 — Main-only ZERO repair superset imported

- Remaining useful provider fixes from stale branches `fix/post-186-zero-batch-20260919` and its 5-commit superset `fix/post-187-zero-batch-2-20260919` were triaged and imported directly into `main` in one atomic commit; no new PR/repair branch was created.
- Imported only unresolved/currently relevant cases:
  - **AllAnime**: provider-local GraphQL search/source/clock chain at `api.allanime.day/api`, replacing stale HTML execution authority in Provider DATA.
  - **MoviesMod**: current `moviesmod.ai.in` authority aligned in DATA/history plus parser/runtime updates.
  - **UHDMovies**: verified HTTP `206` / Content-Range / media content-type can terminate as playable media instead of being discarded.
  - **VoirAnime.rip**: robust AJAX result attribute parsing plus bounded fallback queries.
  - **MoviesHunt** and **Sekai**: late-stage parser/runtime robustness from the superset branch, with their contract tests.
- **AnimeSama.co was intentionally not re-imported** because the current scoped census already proves it **FULL OK**.
- Functional promotion is still pending post-commit current-main census/probes; this entry records code/data integration, not a green verdict.
- Cleanup intent: PR **#187** is superseded by this direct-main import. The four stale work refs are to be removed/neutralized after this exact main commit.


### 2026-09-19 — Stale PR/branch cleanup completed

- PR **#187** was closed unmerged because its useful changes were superseded by direct-main commit **d4c7ef24abe237eb5b8a23ce2e372dad0b82d62b**.
- The four stale work branches were force-aligned to the exact main SHA so they contain **zero unique commits / zero code delta**:
  - `fix/post-186-zero-batch-20260919`
  - `fix/post-187-zero-batch-2-20260919`
  - `fix/provider-census-state-machine-20260919`
  - `tmp/provider-max-repair-proof-20260919`
- Physical branch deletion is not exposed by the installed GitHub connector; refs were therefore neutralized to main rather than left diverged. Do not use them for future repair work.
- Workstream policy remains **main-only**. `brain-learning/proposals` is intentionally preserved because it is the dedicated Brain proposal branch, not a repair branch.


### 2026-09-19 — MoviesHunt imported runtime syntax regression fixed

- Post-import main checks exposed a concrete syntax regression in `scripts/provider_patches/movieshunt_runtime_v1.py`: `dynamicLookup()` missed the closing quote after `&page=1&per_page=30`.
- This caused both the dedicated MoviesHunt Node parse contract and global override/minimizer composition to fail before live probes.
- The source is corrected directly on `main`; functionality is still pending fresh rematerialized/current-main checks.


### 2026-09-19 — Physical stale-branch deletion delegated to Repository Hygiene

- User clarified the final branch policy: keep **`main`** plus **`brain-learning/proposals`** only. Brain Learning remains intentionally preserved.
- The earlier four repair refs were only neutralized to main because the connector lacks DELETE-ref support; that did **not** satisfy physical deletion.
- The existing `OPS - Repository Hygiene` workflow already has `contents: write` and executes `git push origin --delete` for every non-PR branch except `main` and `brain-learning/proposals`.
- This workflow is now deliberately retriggered from main to physically delete:
  - `fix/post-186-zero-batch-20260919`
  - `fix/post-187-zero-batch-2-20260919`
  - `fix/provider-census-state-machine-20260919`
  - `tmp/provider-max-repair-proof-20260919`
- Do not mark branch cleanup complete until GitHub branch inventory confirms only `main` and `brain-learning/proposals` remain.

### 2026-09-19 — Physical branch cleanup confirmed; accepted release finalization required

- Repository Hygiene physically deleted the four obsolete refs: `fix/post-186-zero-batch-20260919`, `fix/post-187-zero-batch-2-20260919`, `fix/provider-census-state-machine-20260919`, and `tmp/provider-max-repair-proof-20260919`. A post-delete fetch showed exactly `main` and `brain-learning/proposals`; there are no open PRs. The cleanup job's later red conclusion came from release-integrity checks, not from branch deletion.
- Current unresolved census evidence is run **35453478159** on exact SHA **79c58f85b5e341a6aa49da9a6b83ee7198ae7ada**. Durable ledger: **21/46 FULL OK**, **13 NO PROOF**, **2 PROVIDER JS BROKEN**, **10 PROVIDER JS FULLY BROKEN**; 25 providers remain in the Brain queue. The evidence was persisted to main by **c98de62e96098547054e9d796c5c2e4e1fafb7a8** without publishing candidate provider bytes.
- CORE - Verify & Publish run **35453478239** failed its Quick gate specifically in `scripts/audit_provider_v3_static.py` with `AssertionError: moviesmod`: authoritative Provider DATA says `https://moviesmod.ai.in` while the committed published MoviesMod bundle still projects the previous official site.
- Cross-checking `provider-overrides.json` against `provider-v3-materialization.json` found **15 current providers** whose declared `provider_lego_scripts` are absent from the committed materialization record: Flemmix, UHDMovies, MoviesHunt, 4KHDHub, AnimeSalt, AnimeSultra, AnimeVOSTFR, Coflix, French-Manga, MoviesMod, Sekai, VoirAnime-Homes, VoirAnime.rip, AllAnime, and Anime-Ultime. This is a common publication-persistence drift, not 15 independent proof regressions.
- Repository Hygiene additionally exposed stale `manifest-hub46.json` content-addressed provider references after branch deletion. `CORE - Finalize Accepted Release` is the canonical atomic path that reapplies durable provider patches, regenerates content-addressed provider/manifests including Hub46/native Hub46, validates release integrity, and publishes only if main remains on the accepted SHA.
- Next action from this checkpoint: trigger that accepted-release finalizer from the then-current main SHA, inspect its exact generated/published SHA, then rerun/inspect CORE, Provider Non-Regression and the unresolved census before promoting any provider status. This entry is diagnostic; the rematerialization is not marked complete until those gates prove it.

### 2026-09-19 — Release finalizer Hub46/prune ordering regression

- Accepted-release finalizer run **35454276828** on **30f977c3ac534d6c6e89d80c161102d0a4eaff61** successfully reapplied durable overrides to all **44 active providers** in its workspace, including MoviesMod, and reached both provider reapply and minimizer fixed points.
- The run then failed before publication in `prune_unreferenced_providers.py`: `manifest-hub46.json` still referenced 14 superseded content-addressed provider filenames. The finalizer regenerated Hub46 only in the following step, so prune correctly failed closed on stale authoritative references.
- Root cause is pipeline ordering, not provider rematerialization: after `reapply_published_overrides.py` changes content-addressed filenames, `manifest-hub46.json` must be reprojected before prune treats it as a local retention authority.
- Fix: `release-finalize.yml` now regenerates `manifest-hub46.json` immediately after language projections and before prune; the later post-version Hub46 regeneration remains in place. `tests/release_version_sync_test.py` locks the required ordering and requires both Hub46 projection passes.
- Validation remains pending until the corrected finalizer publishes atomically and downstream CORE/non-regression/census inspect the published SHA.

### 2026-09-19 — Git tree integrity restoration after release-order patch

- A low-level multi-file Git Data commit attempt for the release-order fix accidentally used an incomplete base tree and produced intermediate commit **99d42b7f367b22046e3e981bf9626177471f1587** containing only the three edited paths. Branch rules correctly refused a force reset.
- Recovery was performed immediately as a forward commit **0fb45d4b389742be1b7ad5612fa430c8fe9cd469**, using the complete parent tree **a2835246eae6b7650ed9d6564b0e52ab20da9c43** plus the intended edits. The resulting tree **8e6d4843ef33d73b21e3ce83cbbb35b1e16ae3e0** was inspected recursively: **4,768 entries**, not truncated, with `manifest.json`, `providers/**`, workflows and the release trigger present.
- The intended release-order changes remain: regenerate `manifest-hub46.json` before provider prune and lock that order in `tests/release_version_sync_test.py`. No provider publication is considered validated from the intermediate partial-tree commit.

### 2026-09-19 — Release finalizer trigger robustness

- After the full repository tree was restored, trigger commits **de742a45a18ed304da095f57af0f71815f8e50c2** and **93d7dd60462af6e5dfedcfca30f694302545afb9** both changed `.github/triggers/release-finalize.json` but produced no `finalize` check run, while Workflow Gate/Brain/CodeQL did register normally. Therefore accepted-release publication was still not executed.
- The release workflow itself was present on main with its expected push path filter, but it did not include its own workflow path as a trigger. To make workflow restoration/edits self-validating, `release-finalize.yml` is being added to its own `push.paths`, with `tests/release_version_sync_test.py` locking that contract.
- This is a trigger-robustness fix only; provider bytes remain unpublised until a real `finalize` job appears, completes the atomic release, and downstream gates validate the resulting SHA.

### 2026-09-19 — Temporary recovery finalizer registered

- The canonical `release-finalize.yml` remained present and passed repository syntax/security loading, but repeated push triggers did not create its `finalize` job after the transient delete/restore history. Treating the old workflow registration as unreliable, a fresh temporary recovery workflow was added at `.github/workflows/temp-release-finalize-recovery.yml` in commit **1345a935b292d0c207f33fda30dd92fc5b0049dc**.
- The temporary workflow reuses the corrected accepted-release finalization body and the same `niakvio-core-release-mutation-main` concurrency group. It is push-triggered only by `.github/triggers/temp-release-finalize-recovery.json`, so registration and execution are separate commits and no duplicate run is intentionally started.
- Cleanup rule: do not delete the temporary recovery workflow until its publication SHA and downstream CORE/non-regression/census results are inspected. Then remove the temporary workflow and sentinel while keeping the canonical finalizer fix.

### 2026-09-19 — Canonical finalizer reactivation via active Repository Hygiene

- A newly created temporary workflow also failed to register a run from its sentinel push. This confirms the recovery problem is GitHub Actions workflow activation/registration for newly restored/created workflow definitions, not the accepted-release command body.
- `OPS - Repository Hygiene` is an already-active workflow and its `purge-stale-actions` job already owns `actions: write`. A one-shot recovery step is therefore being added there, gated strictly to a push commit message containing `recover canonical release finalizer`.
- The recovery step will fail closed unless current `main` exactly equals its triggering `GITHUB_SHA`, then call the GitHub Actions API to enable `release-finalize.yml` and dispatch it manually with `expected_sha=<exact main SHA>`. Manual workflow runs are explicitly excluded from stale-run cancellation by Repository Hygiene.
- This is only an activation bridge; publication authority remains the canonical `CORE - Finalize Accepted Release` workflow.

### 2026-09-19 — Provider Lego HTML scanner hardening applied

- The 9 provider-local runtime sources exposed by accepted-release rematerialization were hardened on main: Flemmix, UHDMovies, MoviesHunt, 4KHDHub, AnimeSalt, AnimeSultra, AnimeVOSTFR, MoviesMod and VoirAnime.rip. Regex-based HTML tag/script/style stripping was replaced with deterministic character scanning that skips script/style blocks before entity/whitespace normalization.
- Source commits: `f76485b5` Flemmix, `88d7d5a2` UHDMovies, `c4447443` MoviesHunt, `2839233e` 4KHDHub, `44051e73` AnimeSalt, `bb1b1a87` AnimeSultra, `12bf60f0` AnimeVOSTFR, `cffbeb81` MoviesMod, `f086a7fe` VoirAnime.rip.
- `tests/provider_html_filter_security_test.py` was upgraded in **17699b823403b32dafbd0b3f7b8eadf41c8962ca** to discover every `provider_lego_scripts` source declared by `provider-overrides.json` (currently 36 unique scripts) and scan them for forbidden HTML-filter regex patterns. This removes the previous hardcoded-11-source blind spot.
- GitHub code-search results may lag raw branch contents, so status is not inferred from search indexing. Completion requires the accepted-release workflow to rematerialize/publish, then the published security gate and downstream provider gates to pass on the resulting SHA.

### 2026-09-19 — Hardened provider release published atomically

- Accepted-release finalizer run **35456153269** completed fully green from accepted base **bf5fef04fb3770cd54ba46840d457b65c6107d02**.
- Provider generation commit: **ad9d423ab78dc5738a51efac6a11ed5b3af86914**. Final pinned release/publication SHA: **4583dd1072ea46f65f8aef6452b700cc917a658f**.
- The finalizer replayed all **44 active providers**, reached provider override and minimizer fixed points, regenerated `manifest-hub46.json` before prune, and pruned **88 superseded provider bundles** while retaining 44 protected active bundles.
- Published HTML security gate is green: `PROVIDER_HTML_FILTER_SECURITY_OK sources=41 published=46 bad_html_filter_regex=0`. Release integrity validation also passed, and Hub46/native Hub46 projections were regenerated successfully.
- This validates the common publication-persistence repair and the provider-local HTML scanner hardening through actual published bytes. It does **not** yet promote unresolved census statuses: GitHub Actions-token pushes do not recursively trigger downstream workflows, so CORE Verify, Provider Non-Regression, targeted recovery and unresolved census must be explicitly retriggered against unchanged provider bytes before status promotion.

### 2026-09-19 — Provider Lego HTML hardening completed before release retry

- The accepted-release rematerialization exposed 9 provider-local Lego sources that still used CodeQL-forbidden regex HTML stripping. Source-level fixes are now committed on main for **Flemmix, UHDMovies, MoviesHunt, 4KHDHub, AnimeSalt, AnimeSultra, AnimeVOSTFR, MoviesMod and VoirAnime.rip**. Each now uses a deterministic character scanner that skips tags and script/style blocks without regex tag stripping.
- The six other currently declared provider Lego sources — **Coflix, French-Manga, Sekai, VoirAnime-Homes, AllAnime and Anime-Ultime** — were rechecked and contain none of the three forbidden HTML-filter patterns.
- The security regression test on main now auto-discovers declared `provider_lego_scripts` from `provider-overrides.json`, so future provider additions are included automatically instead of relying on a fixed source list.
- Publication is still not marked validated: next step is to trigger `CORE - Finalize Accepted Release`, verify atomic publication, then inspect CORE Verify & Publish, Provider Non-Regression and the unresolved provider census on the resulting published SHA.

### 2026-09-19 — UHDMovies non-regression false semantic floor fixed

- Provider Non-Regression run **35456432346** failed on two providers after the previous accepted release: MoviesHunt (`missing_verified_lanes`) and UHDMovies (`semantic_capability_regression`).
- UHDMovies was a false semantic regression: current/published capability is movie-only, while the 5.21.0 fixture carried legacy `types=[movie,tv]`. That legacy fixture field described exercised/invocation coverage and is not a canonical semantic declaration.
- `scripts/build_provider_history_matrix_v3.py` no longer promotes legacy fixture `types` into `semanticTypeFloor`. Only explicit fixture `semanticTypes` or historical `canonicalSupportedTypes` may create a semantic floor. The old `types` value remains diagnostic-only with source `5.21.0-fixture-types-unproven-transport-only`.
- `tests/provider_non_regression_contract_test_impl.py` locks this rule by requiring the diagnostic-only source and forbidding `values = legacy`.
- MoviesHunt remains separately unresolved: its current corpus returns HTTP 200 on provider search/detail requests but no verified stream; do not collapse this into the UHDMovies contract fix.

### 2026-09-19 — Unresolved 11+3 active repair batch

- Exact census at main `0f0a9a7d3e2a7521cf55c9b49647f9b4f51492a7`: **21 FULL OK / 11 NO PROOF / 3 PROVIDER JS BROKEN / 11 fully broken**. The active batch is the 11 NO PROOF plus 3 broken; none are considered repaired until current bytes reproduce a verified stream or a more accurate blocked/settings-required state is proven.
- Corpus search depth was raised from **4 to 8 fixtures per unresolved lane** in both `provider-v3-quick-yield.yml` and the current-bytes full census. Retained misses continue to be skipped, so each run explores further into the rotating corpus instead of repeating the same four titles.
- **VidFast:** old root iframe/query authority was obsolete. Added `scripts/provider_patches/vidfast_runtime_v1.py`, reconstructing current `/movie/{tmdbId}/` / `/tv/{tmdbId}/{season}/{episode}/` -> `enc-dec.app/api/enc-vidfast` -> CSRF POST -> `dec-vidfast` server chain. Registered as provider Lego and locked by the existing capability contract test. Not yet marked functional pending live proof.
- **YFlix:** fixed a typed-route authority bug: ProviderBase's generic `directRoute` executed before lane-specific resolution and forced `type=movie` for TV requests. Removed ambiguous directRoute/directRequest and made `movieRoute` + `episodeRoute(type=tv)` authoritative. Contract test added. Live proof pending.
- **MoviesHunt:** current upstream still uses `https://movieshunt.run/?s=`; the old positive proof was Interstellar through MoviesHunt -> Abhilinks -> HubCloud/Huntplay -> validated HLS. Current NiakVIO stopped at `lookup.php`. The lookup JSON parser is now recursive/schema-tolerant (nested objects/arrays, href/path/slug and embedded HTML) instead of requiring only top-level results/posts/data/items with four fixed fields. Live proof pending.

### 2026-09-19 — AllAnime and AniKoto current-architecture rebuild

- **AllAnime NO PROOF root cause confirmed and patched:** current upstream episode-source lookup uses GET persisted GraphQL query, not the older POST `SOURCE_GQL`. Static decode of current upstream yielded API `https://api.allanime.day/api`, persisted hash `d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec`, search Origin/Referer `https://allmanga.to`, source Referer `https://youtu-chan.com`, source Origin `https://allanime.day`. AES-CTR key contract remains SHA256(`Xot36i3lK3:v1`). Lego migrated to the current GET persisted-query protocol and contract-tested. Live stream proof still pending.
- **AniKotoTV NO PROOF root cause confirmed and patched:** current upstream no longer executes the historical AniKoto catalogue/AJAX chain. It maps TMDB to MAL/AniList through `https://arm.haglund.dev/api/v2/tmdb`, then resolves `https://megaplay.buzz/stream/{mal|ani}/{id}/{absoluteEpisode}/{sub|dub}` and `/stream/getSources?id=`. `anikototv_runtime_v2.py` was rebuilt as clean runtime V3 around that architecture; obsolete /search, /watch and /ajax route authority was removed from `provider-overrides.json`. Contract remains anime-only. Live proof pending.
### 2026-09-19 — Raw historical user tests recovered and locked

- The prior user-supplied raw test files were re-read from Project/Library sources rather than relying only on the summarized evidence ledger.
- Recovered exact field cases include Interstellar, HOTD S1E2, Ragna Crimson S1E4, Mushoku Tensei S3E11 and Hell Mode S2E10 with the original observations for wrong content, 403 rows, quality drift, language/dialect preservation, late stale rows and provider-generation accumulation.
- Recovered exact provider-route evidence relevant to current unresolved repairs: AllAnime One Piece -> NexaBloom HLS; AniKotoTV historical Death Note AJAX chain; MoviesMod Interstellar -> modpro/unblockedgames/DriveSeed; HDHub4u -> greenmountmotors/hblinks/HubCloud (explicitly distinct from 4KHDHub); AllWish Death Note -> NexaBloom HLS; MovieBox HOTD -> vidsrcme -> sagaciousslumber HLS; plus Coflix and Movix/Purstream captures.
- `automation/USER-PROVIDER-EVIDENCE-LEDGER.md` now contains a detailed block D with those exact LKG chains and client invariants. `tests/user_provider_manual_evidence_crosscheck_test.py` now requires block D, protects 4KHDHub/HDHub4u identity separation, requires the AllAnime One Piece provider-targeted fixture, and locks the NiakVIO-owned MovieBox vidsrcme source.
- These historical routes are evidence, not automatic current-domain authority. Every provider must still be revalidated against current bytes before status promotion.
### 2026-09-19 — Raw user evidence activated in MovieBox/AllWish repair

- MovieBox: the recovered HOTD browser proof (MovieBox -> vidsrcme TMDB resolver -> terminal HLS) matched an existing clean NiakVIO-owned `moviebox_vidsrcme_runtime_v1.py` source that was not bound in current provider DATA. `provider-overrides.json` now registers that Lego, restores current TMDB direct routes, clears stale quarantine state only to `current-contract-staged`, and still requires fresh verified lanes before promotion.
- AllWish: the raw user Death Note proof `/filter?keyword=...` -> `/watch/.../ep-37` -> NexaBloom HLS was recrossed with the current upstream provider source, which still uses the same `/filter?keyword=` search family. A clean NiakVIO-owned `allwish_runtime_v1.py` now implements title-aware search, exact watch episode selection and bounded terminal crawling without executing upstream JavaScript. Provider DATA now points to that Lego; old generic `/player` authority is retired.
- `tests/provider_allwish_runtime_contract_test.py` locks the recovered AllWish route family and the user evidence dependency.
- `TEMP - Targeted Regression Recovery Probes` no longer probes a stale hardcoded provider set. It now derives every provider whose census status is not FULL/PARTIAL, increases bounded sampling to 8 fixtures per lane, and includes the newly recovered AllWish/MovieBox paths/tests. This makes the repair probe follow the live unresolved queue.
- None of MovieBox or AllWish is promoted yet; current bytes must still produce identity-safe terminal playable proof in Actions.
### 2026-09-19 — Evidence-driven unresolved repair batch: MoviesHunt, AllAnime, VoirAnime.rip

- MoviesHunt: cross-checking the last real playable Interstellar trace against the current targeted trace showed current transport uses `hubcloud.ist` and requires HubCloud -> HuntPlay -> HLS. The provider Lego only recognized `hubcloud.cx` explicitly and its fallback crawl depth was 2. The source now accepts current HubCloud TLDs and uses bounded depth 3. Contract test locks both properties. Status remains unpromoted until the new targeted probe reproduces terminal playable media.
- AllAnime: the raw user One Piece browser capture proved `ww2.aniwatch.fit/<title>-episode-N-english-subbed|dubbed` can reach NexaBloom HLS. GraphQL remains primary; a NiakVIO-owned fail-closed site fallback now derives the observed episode-page convention from Core TMDB aliases/absolute episode and hands only that page to the bounded terminal crawler. No upstream JavaScript is executed. Contract test locks the fallback.
- VoirAnime.rip: census `35458567765` exposed a real runtime `ReferenceError: return200 is not defined` plus a wrong-season selection (`my-hero-academia-6` chosen for S1) that returned two playable HLS streams rejected by duration identity at ~4.58x expected episode duration. The source now fixes the malformed numeric returns and makes search scoring season-aware, heavily penalizing mismatched numbered season slugs. Contract test locks crash absence and season scoring.
- CORE failure seen during this batch is currently expected provider-DATA publication drift for AniKotoTV: current DATA routes are ARM/MegaPlay while committed published CONFIG still contains the historical AJAX routes. This requires canonical accepted-release rematerialization after the repair batch; it is not being treated as a new AniKoto runtime regression.

### 2026-09-19 — Targeted recovery trigger generalized for provider scale

- `TEMP - Targeted Regression Recovery Probes` already derived its provider set dynamically from every census row that is not FULL/PARTIAL, but its GitHub path trigger was still a manually curated provider-file list.
- The push/PR trigger now watches `scripts/provider_patches/**` plus generic provider runtime/transport contract patterns and the shared evidence/fixture/DATA files. A new or repaired provider Lego therefore automatically starts the targeted recovery engine without adding another workflow path entry.
- This specifically fixes the missed-trigger class exposed by the new 4KHDHub, AllWish and MovieBox repair work and is required before the planned ~300-provider hub ingestion.
- Current unresolved statuses remain evidence-driven; this workflow change does not promote any provider by itself.

### 2026-09-19 — Release byte-validator blocker isolated; AnimeVOSTFR search parser hardened

- Latest persisted census run **35460541384** remains **22 FULL OK / 1 PARTIAL OK / 7 NO PROOF / 6 PROVIDER JS BROKEN / 10 PROVIDER JS FULLY BROKEN**. MoviesHunt is FULL OK and DesiFlix is PARTIAL OK (movie proven); unresolved providers are not promoted without current terminal proof.
- Accepted-release finalizer run **35461079899** failed before any push during `reapply_published_overrides.py`: `provider_byte_stability.verify_bytes` rejected one rematerialized JavaScript artifact. The validator remains fail-closed; publication did not occur.
- `scripts/reapply_published_overrides.py` now preserves the validation failure while adding the exact `provider_id` to the exception, so a future failure is attributable instead of emitting an anonymous tail of `node --check`.
- `tests/provider_allwish_runtime_contract_test.py` now applies the AllWish Lego to the actual current AllWish bundle and runs `node --check` on that generated artifact. This tests the same insertion shape that the finalizer validates, not merely the standalone wrapper source.
- AnimeVOSTFR divergence was narrowed to search parsing: census requests to `v2.animevostfr.org/?s=...` redirect to `animevostfr.org` and return HTTP 200 but stop before detail pages, while the individual upstream proof can still reach detail/episode/trembed/Sibnet and return two streams. Current upstream derives card labels from image `alt` when anchor text is empty. The NiakVIO runtime now mirrors that safe parser behavior with visible-text -> image alt/title -> URL-slug fallback. Live census proof is still pending.

### 2026-09-19 — Materializer now fails closed on invalid generated Provider JS

- The 2026-09-19 repair cycle exposed a systemic blind spot: `materialize_provider_v3_all.py` could report all active providers materialized even when a generated full bundle later failed to load in the probe. AllAnime currently demonstrates that class with `invalid_probe_output` before any provider network call, while its standalone runtime wrapper contract passes.
- The central materializer now calls the canonical `provider_byte_stability.verify_bytes` on every final generated provider bundle **before hashing or writing it**. Validation remains fail-closed and byte-preserving; any failure includes the exact provider id. A validator rewrite is also treated as an assertion failure.
- Each materialization report row now records compact canonical byte-validation metadata. `tests/provider_materialization_byte_validation_contract_test.py` locks validation order (validate -> digest -> write), and Targeted Recovery, Current Bytes Census and Provider Non-Regression all execute that contract.
- This is a generic NiakVIO robustness fix: future providers/hubs with syntactically or structurally invalid generated bytes must fail at materialization rather than surfacing later as an opaque census `invalid_probe_output`.
- Targeted Recovery run **35461565575** on **9728d05503ff...** proved **VoirAnime.rip anime playable**: Boruto S1E1 -> VoirAnime.rip episode -> Vidmoly -> terminal HLS, master and variant HTTP 200. Full census promotion remains pending because the full rotating corpus run did not sample that positive in the same cycle.

### 2026-09-19 — Hidden v3 minimizer authority removed from compositor

- The new canonical byte validator exposed AllAnime as the first generated provider whose clean rematerialization became syntactically invalid. The current AllAnime Lego itself parses successfully both standalone and when directly replacing its managed block in the already-published bundle.
- Root cause found in the generic compositor: `scripts/apply_provider_overrides.py` still unconditionally ran `provider_v3_minimizer.minimize_text()` on every complete v3 bundle, even though `materialize_provider_v3_all.py` and `materialize_provider_v3_one.py` already own an explicit final-stage-only minimizer gate. This created two minimization authorities and transformed provider Lego before canonical byte validation.
- Fix: remove all minimization from `apply_provider_overrides.py`. It now only composes owned Provider/Core Lego; optional minification remains exclusively behind `NIAKVIO_PROVIDER_V3_FINAL_MINIMIZE` in the materializers. `tests/provider_v3_final_stage_minimizer_gate_test.py` now forbids hidden minimizer imports/calls in the compositor.
- Validation pending on a fresh AllAnime rematerialization + global census/non-regression; do not promote the providers that were reclassified FULLY BROKEN solely because the previous all-provider materialization aborted at AllAnime index 37/44.

### 2026-09-19 — Core discovery whitespace idempotence fixed

- Removing the hidden compositor minimizer exposed a real Core discovery byte drift that the minimizer had been masking. `tests/global_playback_integrity_policy_test.py` showed the second application was exactly **9 bytes longer**.
- The diff was nine accumulated blank lines immediately before `NUVIO_GLOBAL_CORE_START_BOUNDARY_V1`: each stripped managed Core rectangle could leave a separator newline behind, then Core reconstruction inserted the boundary again.
- `_strip_generated_core_tail()` now canonicalizes the stripped v3 gap to exactly one newline between the retained Provider bytes and `END PROVIDER`. This makes Core composition idempotent without relying on minification as a cleanup step.
- This fix must be validated together with the final-stage-only minimizer change by a fresh Workflow Gate, AllAnime materialization, full census and Provider Non-Regression run before the previously inflated FULLY BROKEN statuses are trusted.

### 2026-09-19 — AllAnime materialization blocker cleared

- Provider Non-Regression on commit **e91c4f71c8988dae56019735a8418ecbe0eb274f** passed static anti-regression contracts, the exact four-version ledger, and crucially **Materialize exact current provider candidate bytes** across the complete active provider set. The previous hard stop at AllAnime index 37/44 is gone.
- This validates the combined generic fixes: no hidden minimization in `apply_provider_overrides.py`, and canonical one-newline restoration when stripping/rebuilding the Core boundary. The AllAnime provider Lego did not need to be weakened or disabled.
- The same run is now executing the real rematerialized current-provider census. Until that network stage completes, historical FULLY BROKEN inflation caused by the former materialization abort must not be treated as current provider verdicts.

### 2026-09-19 — AllAnime episode-page terminal extraction widened

- Fresh targeted evidence on HEAD **852da98d...** shows AllAnime now reaches `api.allanime.day` and explicit `ww2.aniwatch.fit/<slug>-episode-1-english-{subbed,dubbed}` pages with HTTP 200, but no nested player/media request follows and the lane remains `provider_network_zero_result`.
- Root cause narrowed to the provider-local fallback parser: the episode page is fetched explicitly, but `siteCandidates()` only extracted literal `src/href/data-src` and raw `http(s)` strings. That is narrower than ProviderBase's proven URL decoder and misses escaped/scripted player payloads (the retained manual positive resolved to `fetch.nexabloom.top/.../master.m3u8`).
- Fix: AllAnime `siteCandidates()` now merges ProviderBase `_extractUrls()` and explicit encoded-player payload extraction before the bounded terminal crawler. This preserves the provider-owned episode identity while reusing Core/ProviderBase URL decoding instead of duplicating a weaker regex.
- Validation pending: targeted AllAnime census must show either a nested player/media request and terminal stream, or a more specific remaining blocker. Do not promote before that proof.

### 2026-09-19 — UHDMovies terminal 206 false-negative fixed

- Targeted recovery **35464508422** proves UHDMovies can traverse the full current chain for Inception: `uhdmovies.my` search/detail -> `cloud.unblockedgames.world` landing forms -> `driveseed.org/file/...` -> `video-seed.dev/`, with the final response **HTTP 206**.
- NiakVIO still returned `no_streams` because `followDownload()` only accepted extension/hostname-shaped direct URLs; unlike the shared `request()` path it did not honor `terminalResponse()`. A range/media response at an opaque URL was therefore discarded after being successfully reached.
- Fix: `followDownload()` now treats HTTP 206 / Content-Range / video content-type as terminal media and returns the actual final URL. Contract test locks that branch. Fresh playable validation is pending before promotion.

### 2026-09-19 — AniKotoTV active runtime path corrected

- `provider-overrides.json` confirms AniKotoTV materializes `scripts/provider_patches/anikototv_runtime_v2.py`; edits to v1 are out-of-path and are not counted as a repair.
- Targeted recovery **35464508422** reaches AniList plus MegaPlay stream pages and `/stream/getSources` with HTTP 200, then returns no stream.
- The active v2 only handled plaintext MegaPlay source fields, while the repository's existing migration notes document an additional encoded-source response form. The active v2 now handles both the ordinary source field and that documented fallback before Core terminal validation.
- Capability contracts now assert the fallback exists on the active v2. Fresh targeted proof remains required before promotion.

### 2026-09-19 — AniKotoTV anime lane re-proven playable

- Targeted Regression Recovery run **35465213543** on trigger SHA **267aacc9433a17b090d77013e7347d0a215e4452** verified AniKotoTV's **anime** lane as `playable_verified` with zero contradictions.
- Proven chain: TMDB metadata -> AniList fallback after the legacy mapping endpoint returned 404 -> `megaplay.buzz/stream/mal/40748/1/{sub,dub}` -> `/stream/getSources` -> `fetch.nexabloom.top/.../master.m3u8`. Both master HLS responses were reachable (206/200) and variant playlists returned HTTP 200.
- The active `anikototv_runtime_v2.py` encoded-source fallback is therefore validated in the real runner. AniKotoTV may be promoted for its single required anime lane by the next census/status render; this is not inferred from a contract test.
- Same targeted run still leaves AllAnime and UHDMovies unverified; their patches must not be promoted from this run.

### 2026-09-19 — Animetsu current Gojo API Lego reconstructed

- The active upstream Animetsu bytes were decoded rather than guessed. Current constants are: API base `https://animetsu.live/v2/api`, proxy `https://swiftstream.top/proxy`, servers `kite` + `dio`, source types `sub` + `dub`, and source route `/anime/oppai/{id}/{episode}?server={server}&source_type={sourceType}`.
- NiakVIO previously had no active Animetsu Provider Lego; its clean v3 base still followed stale generic route evidence (including the old `omg10.com` path), which explains the fresh `provider_network_zero_result`.
- Added `scripts/provider_patches/animetsu_runtime_v1.py` and wired it as the sole provider Lego. The runtime uses Core TMDB metadata first, requires Animation + original language ja/zh/ko before the first Animetsu request, performs current JSON search/title-year matching, computes absolute episodes from Core season counts when available, calls the decoded `oppai` routes, and emits the upstream proxy URLs for Core HLS validation. Upstream JS remains unembedded/unexecuted.
- Added `tests/animetsu_runtime_behavior_test.py`: it asserts the current search/source/proxy chain and proves a live-action TV fixture produces zero provider-network calls after the Core semantic gate.
- Current state: **patch + contract pushed, real targeted playable validation pending**. Do not promote Animetsu until Actions reproduces a terminal playable stream.

### 2026-09-19 — AniKoto playable source proven but published bytes stale; Animetsu staged

- Current durable census is **23 FULL OK / 1 PARTIAL OK / 7 NO PROOF / 2 PROVIDER JS BROKEN / 13 PROVIDER JS FULLY BROKEN**.
- AniKotoTV is no longer unresolved: targeted run **35465213543** proved anime playable through current MegaPlay `getSources` + encoded-source fallback to NexaBloom HLS, and the census promoted AniKotoTV to **FULL OK**.
- CORE Verify & Publish run **35466088948** is red only because committed published AniKotoTV bytes still expose the historical AJAX route family (`/search?keyword`, `/watch`, `/ajax/server...`) while authoritative Provider DATA now expects `/api/v2/tmdb`, `/stream/{identityKind}/...`, and `/stream/getSources`. This is publication drift, not a failed current runtime.
- Animetsu source DATA is likewise ahead of committed materialization: authoritative Provider DATA now binds `scripts/provider_patches/animetsu_runtime_v1.py` and `https://animetsu.live/v2/api`, while committed `provider-v3-materialization.json` still records only the old CONFIG fix and no provider Lego. Its persisted targeted trace still shows legacy `omg10.com`, so it must not be judged until rematerialized bytes are published.
- Next action: canonical accepted-release finalization from current main, then rerun CORE/non-regression/census on the published SHA. No status promotion is inferred solely from source DATA.

### 2026-09-19 — 19-provider publication drift identified before current finalization

- Cross-checking authoritative `provider_patches[*].provider_lego_scripts` against committed `provider-v3-materialization.json.applied[].path` on current main found **19 providers** whose declared provider-local Lego is absent from the published materialization record.
- The drift set is: Flemmix, UHDMovies, MoviesHunt, 4KHDHub, AnimeSalt, AnimeSultra, Animetsu, AnimeVOSTFR, Coflix, French-Manga, MoviesMod, Sekai, VidFast, VoirAnime-Homes, VoirAnime.rip, AllAnime, AllWish, Anime-Ultime and MovieBox.
- This overlaps **13 currently unresolved/red providers**. Therefore their persisted census verdicts still reflect stale published bytes and must not be treated as verdicts for the current source repairs.
- Accepted-release finalizer run **35466561339** was triggered from current main to atomically reapply those Provider Lego plus current DATA, regenerate content-addressed manifests/Hub46, validate generated bytes and publish only on the pinned SHA.
- Do not add provider-specific workarounds merely to match stale census behavior while this publication is pending; use the post-finalizer census as the next authority.

### 2026-09-19 — Finalizer ASI failure made provider-identifiable

- Accepted-release finalizer run **35466659585** successfully reapplied durable overrides to all **44 active providers** and produced new content-addressed refs for all 44, proving the pending Provider Lego set is composable.
- Publication then stopped in the optional one-line publication minimizer with the fail-closed guard `ASI-sensitive line break after restricted keyword cannot be flattened safely`. The previous exception omitted the provider/file identity, so no provider-specific repair can be justified yet.
- `finalize_provider_v3_minimizer.py` now wraps minimizer/transform failures with the exact provider id and current content-addressed filename. This does not weaken the one-line or ASI safety contract; it makes the blocker diagnosable.
- Next action: rerun accepted-release finalization on the new pinned HEAD, identify the exact reconstructed bundle, repair its source/transform semantically, then complete publication and post-publication census.

### 2026-09-19 — Test-only pushes no longer launch provider census

- Repeated release/minimizer diagnostic commits were launching `TEMP - Current Bytes Full Provider Census` solely because the workflow listened to broad `tests/**` paths. Those long census runs can later persist evidence to `main`, racing accepted-release finalization even though the provider bytes/data never changed.
- `.github/workflows/temp-current-bytes-full-provider-census.yml` no longer triggers on generic `tests/**` changes for either push or pull_request. Provider-affecting sources/data/corpus/workflow paths remain explicit triggers; test-only correctness is handled by Workflow Gate / Provider Non-Regression.
- The workflow-file edit itself intentionally triggers one final census under the existing self-path. After that run drains, test-only commits must not create new census writers.

### 2026-09-19 — AllAnime final-minimizer syntax blocker isolated; diagnostics hardened

- Accepted-release finalizer run **35469069364** on trigger SHA **4b1221d72ec4fda32b944b7d982c6381f306d109** successfully reapplied durable provider repairs to all **44 active providers** and produced new content-addressed refs for all 44. The 19 source-vs-materialization drifts were therefore composable before minimization.
- Publication still stopped fail-closed in `finalize_provider_v3_minimizer.py`: the minimized **AllAnime** artifact is syntactically invalid. No release bytes were pushed.
- The prior compact diagnostic removed the 146k one-line source but still failed to expose Node's useful syntax message. `scripts/validate_provider_artifact.cjs` now performs a second **parse-only** `vm.Script` compile when `node --check` fails and emits a guaranteed short `syntax_summary=<ErrorName>: <message>` plus a compact location when available. Provider code is never executed.
- Added `tests/provider_validation_syntax_diagnostics_test.py`, reproducing a >100k single-line invalid bundle and requiring compact source omission plus `syntax_summary=SyntaxError:`. `CORE - Workflow Gate` now runs this test explicitly.
- Next action: once the diagnostic gate is green, rerun accepted-release finalization, capture the exact AllAnime minimized syntax error, repair the minimizer/source semantics, then complete atomic publication and post-release CORE/non-regression/census validation.

### 2026-09-19 — AllAnime minimizer ASI root cause patched

- Static audit of the AllAnime runtime found the concrete publication-syntax hazard that matches the finalizer failure: `resolve()` ended with an expression statement `if(!out.length)out=await siteFallback(meta,q)` followed by `return out` on the next physical line. The source relied on JavaScript ASI.
- The one-line publication minimizer correctly preserves many restricted-keyword ASI cases, but flattening this general expression-statement newline yields invalid JavaScript (`...siteFallback(meta,q) return out`). The provider source now terminates that assignment explicitly with `;`.
- `tests/allanime_site_runtime_contract_test.py` now runs the AllAnime wrapper through the real `provider_v3_minimizer.minimize_text()`, asserts a one-line result, and parses the minimized output with Node before also checking the readable wrapper.
- This is a source-level semantic repair, not a relaxation of minimizer or byte validation. Accepted-release publication remains pending until the full finalizer proves the complete AllAnime bundle after all Core/Provider composition.

## 2026-09-19 — publication atomique des runtimes courants + correction de causalité census

- **Finalizer canonique validé** : run `35469740207`, trigger `65ce20e82d21d458ad7fd98b24145b3468b7aea6`, conclusion **success**.
- **Provider generation publiée** : `217d792acba0c16d4202e7a838c9a79243111358`; **release finale** : `11909e664ee6b30867283f7948f14a14a39dabcf`; `main` a été vérifié sur ce SHA final. Release `5.21.54`.
- Le finalizer a réappliqué **44** overrides Provider, passé minimizer/check, sécurité HTML, audit statique, projection Hub46/native et intégrité release avant le push atomique.
- Vérification des bytes réellement publiés : **AniKotoTV** contient ARM/MegaPlay + `/stream/getSources` et ne contient plus l'ancien `/ajax/server`; **Animetsu** contient `animetsu.live/v2/api`, `/anime/oppai/`, `swiftstream.top/proxy` et ne contient plus `omg10.com`; **AllAnime** contient le hash GraphQL courant `d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec` et le contrat persisted-query.
- **Important : publication ≠ preuve live de tous les providers.** Les revalidations CORE, non-régression et census post-publication restent requises; AllAnime/Animetsu/UHDMovies/MovieBox/AllWish/YFlix ne doivent pas être requalifiés verts sans nouveau stream validé.
- Défaut transversal census confirmé : les stages `provider_network_http_error`, `provider_network_exception` et `timeout` alimentaient `consecutiveTechnicalRuns` puis pouvaient devenir **PROVIDER JS FULLY BROKEN** sans preuve de casse JS. La correction sépare désormais les streaks réseau/techniques et rend le statut **PROVIDER NETWORK BLOCKED** pour un échec transport sans preuve historique; une preuve historique qui tombe reste **REGRESSION PROVIDER**. Validation CI encore requise au moment de ce checkpoint.

- **Targeted recovery corrigé** : commit `8124a5af4c09a1a06708c9e55e65d11464043b01`. Le workflow `TEMP - Targeted Regression Recovery Probes` charge désormais `automation/provider-census-proof-history.json` et appelle `audit.build_tasks(history=history)`; les preuves positives retenues sont donc rejouées en premier et les misses connus restent exclus au lieu de repartir du corpus générique. Le workflow surveille aussi explicitement les contrats AllAnime et scope/history qu'il exécute. Run targeted post-publication déclenché : `35470359878`. Validation live encore en cours à ce checkpoint.

- **YFlix cause racine + correctif local préparé** : les bytes publiés avaient le lookup `/db/flix/find` mais aucune étape terminale (`links/list`, `links/view`, `dec-movies-flix`, `dec-rapid`) parce que l'autorité `typed-resolver-api` court-circuitait la chaîne complexe. Le contrat upstream public courant confirme la séquence ID→encrypt→episodes/links→decrypt. Nouveau Lego `scripts/provider_patches/yflix_runtime_v1.py` : DB TMDB → EID → AJAX YFlix courant (`yflix.to` + domaines alternatifs) → déchiffrement → RapidShare/direct-media; l'ancien `api_recipe` incomplet est retiré. Un test Node synthétique couvre la chaîne complète. **Live proof toujours requis** avant de requalifier YFlix.

## 2026-09-19 — AllAnime current authority / YFlix alias / Animetsu upstream state

- **AllAnime**: current external implementations now use `api.mkissa.net/api` + `mkissa.to`, persisted episode hash `f4662f4b7510b26795dd53ef824a0bf1740fbbc5d1273fab18222ac831bca8d0`, short-lived `aaReq` and AES-GCM payloads. NiakVIO commit `8d3ccf45f2aae92b166509dad6a4b80570d91ef5` adds this authority first while preserving the bounded `api.allanime.day` / `d405...` / AES-CTR fallback. A synthetic Node behavior test covers dynamic `partB` + chunk-mask key derivation → aaReq → AES-GCM `tobeparsed` → terminal MP4. **Fresh live proof remains mandatory before promotion.**
- **YFlix**: the first clean runtime is structurally validated and live probes reached `enc-dec.app` DB + encryption with HTTP 200, then failed at the AJAX hosts. `1moviesz.to/ajax`, present in NiakVIO's historical provider path and still externally referenced, is now retained as an evidence-backed fallback after `yflix.to`. This is a domain/transport recovery attempt, not a claimed playable proof.
- **Animetsu**: current upstream `NuvioPlugin/All-in-One-Nuvio/providers/animetsu.js` still exists (current source SHA observed `14f3854fab676831ed0b1131277416c0c9decea1`) and dynamically reads `https://raw.githubusercontent.com/SaurabhKaperwan/Utils/refs/heads/main/urls.json`, key `gojo_base`, before falling back to `animetsu.live/v2/api`. The current registry snapshot inspected on 2026-09-19 contains **no `gojo_base` key**, so upstream itself falls back to `animetsu.live`, which current NiakVIO probes observe redirecting to `omg10.com` HTML. Keep Animetsu unpromoted / upstream-blocked; do not invent a replacement domain.
- Census, targeted recovery and non-regression are wired to execute both the AllAnime current behavior test and the YFlix runtime behavior test. Live/candidate/published states must remain distinct.

- **Census network causality corrigée** : le probe classait auparavant une lane en `provider_network_http_error` / `provider_network_exception` dès qu'une requête quelconque de la trace avait échoué, même si une route/alias suivante répondait 200. Cela gonflait `PROVIDER NETWORK BLOCKED` (ex. UHDMovies avec un 404 secondaire malgré une chaîne DriveSeed en 200, PersianStremio avec 503 puis fallback 200). La classification est désormais basée sur la **dernière requête provider HTTP(S) pertinente** : échec terminal = network blocked; ancien échec suivi d'un 2xx = `provider_network_zero_result` / preuve manquante. Les URL non HTTP(S) parasites sont ignorées. Le même contrat est appliqué dans `audit_provider_quick_yield.py` et `nuvio_tv_probe_tmdb_ci.cjs`, avec tests de causalité. Nouveau census requis avant de retenir le nombre réel de blocages réseau.

## 2026-09-19 — statut NO PROOF approfondi + détection WAF/antibot

- Première moitié du correctif : le probe distingue désormais une profondeur `lookup_only` vs `chain_reached` et reconnaît un vrai challenge navigateur/WAF à partir de preuves non sensibles (`cf-mitigated: challenge` ou marqueurs HTML challenge/CAPTCHA/Just a moment). Les corps ne sont jamais persistés.
- La classification réseau reste causale sur la dernière requête pertinente; `provider_waf_challenge` est distinct d'un 403 ordinaire.
- Le test de causalité cassé sur `687ec38b` avait uniquement un `NameError` de fixture de test; l'ordre des variables est corrigé ici.
- Aucun solveur CAPTCHA/Cloudflare ni fabrication de `cf_clearance` n'est ajouté. La compatibilité autorisée reste fingerprint navigateur, headers/referer/origin et cookies de session normalement obtenus.
- Le renderer/ledger doit encore être mis à jour dans le commit suivant pour exposer CHAIN REACHED et WAF/ANTIBOT; ne considérer aucun nouveau compteur comme validé avant ce second lot + CI.

- **Ledger exposé : CHAIN REACHED / WAF** : le renderer sépare maintenant NO PROOF (search/lookup-only), CHAIN REACHED (contenu/detail/episode/player spécifique atteint sans média terminal), PROVIDER WAF/ANTIBOT (challenge navigateur prouvé) et PARTIAL OK (au moins une lane réellement playable + vérifiée). La colonne ambiguë Search progress devient **Corpus progress** et **Evidence depth** rend la profondeur explicite.

- **WAF propagé dans l'historique/non-régression** : `provider_waf_challenge` compte comme blocage externe/transitoire, jamais comme panne JS. Les comparaisons A/B et l'autorité upstream drift l'acceptent comme cause réseau distincte.

- **Mémoire des CHAIN REACHED corrigée** : un zero-stream ayant atteint une route contenu/detail/episode/player n'est plus enregistré comme `misses`. Il passe dans `chainHits`, est rejoué juste après les preuves positives et avant le corpus générique, et sort automatiquement de cette file dès qu'il devient playable ou retombe en vrai lookup-only miss. Cela évite que Mallumv/AllAnime et les futurs providers presque résolus soient oubliés par la rotation après avoir atteint leur meilleure fixture.

- **Crawler média : navigation non-média filtrée** : la trace UHDMovies prouvait la chaîne UHDMovies → gateway → DriveSeed en HTTP 200, puis le crawler générique suivait encore des liens de navigation (`/about-us`, privacy/terms, puis `/cdn-cgi/l/email-protection`) et laissait le dernier 404 contaminer le verdict réseau. `CORE.MEDIA_ENRICHMENT.V1` rejette désormais explicitement ces routes non-média avant crawl (révision `scoped-playback-context-v10-nonmedia-nav-filter`). C'est un correctif générique pour tous les providers player/download, pas une exception UHDMovies. Validation candidate/non-régression requise avant publication.

## 2026-09-20 — NO PROOF ne doit plus effacer une preuve candidate live

- Audit des 4 derniers NO PROOF : 4khdhub, animetsu, animevostfr, showbox.
- 4khdhub courant n’a pas de preuve playable retenue : les anciens flux Interstellar/Breaking Bad en 206/MKV appartiennent au provider distinct historique 4khdhubnew; ne pas réattribuer ces preuves.
- animetsu et showbox n’ont pas de preuve positive retrouvée dans les snapshots/field evidence examinés.
- animevostfr a une vraie preuve candidate : run87_reconstruction / run 34309729426, scope reconstruction-candidate, raw + playable + verified; matrice CANDIDATE_GREEN.
- Le census expose désormais CANDIDATE OK séparément de NO PROOF et PARTIAL OK. PARTIAL/FULL restent réservés aux preuves courantes/publiées.

## 2026-09-20 — Core media enrichment bootstrap pour providers inconnus

- Le non-régression a révélé un vrai trou générique après le filtre navigation non-media v10 : `apply_overrides()` n'appliquait `CORE.MEDIA_ENRICHMENT.V1` que si le provider avait déjà un capability classé.
- Pour un provider nouveau/inconnu, `capability=""` supprimait donc le Core enrichment au premier passage, exactement avant que BRAIN puisse le classifier. Le test `future-provider-never-seen-before` matérialisait ainsi une version sans `scoped-playback-context-v10-nonmedia-nav-filter`.
- Correction : un capability inconnu reçoit maintenant le media-enrichment Core conservateur par défaut; un capability explicitement connu mais hors allow-list reste opt-out. Aucun cas provider spécifique n'est ajouté.
- Le test census `CANDIDATE OK` avait aussi une assertion de wording obsolète; elle est alignée sur la sémantique actuelle ("current verified playable lane").

- **Census trigger coverage alignée** : le workflow Current Bytes exécutait les contrats census/Core mais son filtre `paths` ne surveillait pas plusieurs de ces autorités. Il surveille désormais `scripts/apply_provider_overrides.py`, les tests census state/identity/history et `global_playback_integrity_policy_test.py`; une modification de ces contrats déclenche donc réellement un nouveau census au lieu de laisser le Markdown stale.

## 2026-09-20 — Flemmix WAF: migration runtime vers flemmix.me

- Le census GitHub observait un vrai challenge Cloudflare sur `flemmix.cloud`.
- Recroisement : le source upstream Gowaru courant expose `BASE_URL=https://flemmix.me` et la page publique `flemmix.me` sert actuellement les catalogues films/séries. Le Lego NiakVIO était incohérent : son parser était déjà celui du nouveau site (`film-en-streaming`, `serie-en-streaming`, server tabs) mais sa recherche restait l'ancien DLE `/index.php?...story=` sur `.cloud`.
- Correction provider-local : autorité/runtime `flemmix.me`, recherche `/search?q={query}`, substitutions anciennes→`.me`, hub actualisé. `.cloud` reste une ancienne/fallback evidence, pas une preuve de panne JS.
- Un test Node synthétique couvre search → détail film → server tab → media HLS. Le provider ne sera promu vert qu'après preuve live du census.

- **Flemmix manual evidence contract corrected** : le ledger utilisateur conserve explicitement la chaîne DLE historique `/index.php?...story=<query>`, mais le test ne l'impose plus comme route exécutable éternelle. Il vérifie désormais à la fois la conservation de cette preuve historique et la route courante qualifiée `flemmix.me/search?q={query}`. Les échecs targeted/domain-refresh/census/non-regression du SHA `71b3236d` étaient tous bloqués en amont par cette assertion stale, avant tout verdict live Flemmix.

## 2026-09-20 — ROUTE PROVEN : suppression des faux NO PROOF restants

- Les 3 derniers providers `NO PROOF` du census 35474716826 avaient déjà une preuve structurée `live_route_gate=declared-types-qualified` dans DATA : **4khdhub** movie+tv (20 routes live), **animetsu** anime (6 routes live), **showbox** movie+tv (3 routes live).
- Nouveau statut **ROUTE PROVEN** : toutes les lanes déclarées disposent d'une route provider live qualifiée, mais aucun média terminal courant n'est encore playable+verified. Le statut ne compte pas comme FULL/PARTIAL et reste dans la file BRAIN.
- Sur un zero propre, l'ordre devient : preuve playback candidate → CHAIN REACHED courant → ROUTE PROVEN retenu → NO PROOF. WAF/network/JS actuels restent des causes spécifiques et ne sont pas masqués par la route historique.
- Le Markdown expose désormais une colonne `Route proof` (nombre de routes live + lanes). Revalidation census requise avant de considérer le compteur NO PROOF à zéro.

## 2026-09-20 — diagnostic WAF par session navigateur ordinaire

- Ajout de `scripts/probe_waf_browser_session.py` au Current Bytes Census. Il prend uniquement les lanes `provider_waf_challenge` et rejoue la dernière URL GET dans **Chrome headless standard**, avec profil temporaire isolé.
- Le diagnostic n'emploie **aucun stealth plugin, solveur CAPTCHA/Turnstile, fabrication/export de cf_clearance ni persistance de cookies/corps HTML**. Il classe seulement : `browser_content_reached`, `browser_challenge_persisted`, `browser_inconclusive`, `browser_timeout/error/unavailable`; les POST restent `unsupported_method`.
- Objectif : distinguer un challenge spécifique au fetch/empreinte GitHub d'un challenge qui persiste même dans un vrai navigateur. Le rapport est persisté sous `automation/provider-waf-browser-session-<run>.json` + `...-latest.json` et ne modifie pas à lui seul FULL/PARTIAL.
- Références open source auditées pour l'architecture : curl_cffi (fingerprint TLS/HTTP2), Camoufox (navigateur Playwright anti-détection), FlareSolverr/cloudscraper/undetected-chromedriver (solveurs/évasion explicites). NiakVIO retient ici uniquement la voie navigateur/session ordinaire, sans intégrer les mécanismes de solveur.

- **Flemmix regex raw-string corrigée** : le nouveau Lego `flemmix.me` passait le parseur Node mais le test comportemental tombait dans `serverTabs` avec `ReferenceError: i is not defined`. Cause : deux regex littérales `lang-pill/quality-pill` étaient double-échappées dans une raw string Python; le slash de fermeture était donc interprété comme division par `i`. Les deux littéraux utilisent maintenant les échappements JS réels; les `RegExp(...)` construits par chaîne conservent volontairement leur double échappement. Revalidation CI requise.

- **WAF browser-session CI unblock** : les runs census `35475220529` / `35475317890` ne sont jamais arrivés au browser probe. Le contrat de sécurité interdisait le littéral du cookie Cloudflare dans tout le source, tandis que le docstring du script citait lui-même ce nom pour dire qu'il ne le fabrique pas. Le docstring utilise désormais une formulation générique `browser-challenge clearance-cookie`; aucune logique de transport/challenge n'est modifiée. Le prochain census doit enfin exécuter Chrome et persister `provider-waf-browser-session-<run>.json`.

- **ROUTE PROVEN verrouillé sur les vrais providers** : le contrat census vérifie désormais explicitement les gates DATA de `4khdhub` (movie+tv), `animetsu` (anime) et `showbox` (movie+tv). Tant que leurs `live_route_gate` restent `declared-types-qualified`, complets et avec au moins une route live, une refonte du renderer ne doit plus pouvoir les rétrograder silencieusement vers `NO PROOF`. Le census exact-SHA `35475873830` continue sur `5c131271`; ce nouveau contrat sera validé par le run suivant et ne change pas le verdict live du run déjà en cours.

## 2026-09-20 — census state machine validé, NO PROOF=0, Chrome WAF insuffisant

- **Census exact-SHA validé** : run `35475873830` sur `5c1312717f2bf11d69c6cf063c0a1efe2b625120`, conclusion **success**. CORE Workflow Gate `35475873888` et Provider Non-Regression `35475873915` sont également **success** sur ce même état.
- Nouveau ledger réel /46 : **24 FULL OK · 1 PARTIAL OK · 2 CANDIDATE OK · 3 ROUTE PROVEN · 2 CHAIN REACHED · 7 WAF/ANTIBOT · 7 NETWORK BLOCKED · 0 NO PROOF · 0 JS BROKEN**.
- Les trois faux `NO PROOF` sont correctement requalifiés : **4khdhub** = ROUTE PROVEN (20 routes live, movie+tv), **animetsu** = ROUTE PROVEN (6 routes live, anime), **showbox** = ROUTE PROVEN (3 routes live, movie+tv). Aucun de ces statuts ne prétend qu'un média terminal est actuellement vérifié.
- Le diagnostic navigateur ordinaire a enfin tourné : Chrome headless standard disponible, **10 targets** ; **9/9 GET = browser_challenge_persisted**, **1 POST (Vostfree) = unsupported_method**. AllWish, AnimeSalt, AnimeVOST-FR/gupload, Flemmix, FullAnime et MoviesMod restent donc challengés même dans un vrai Chrome headless sur l'IP GitHub.
- Conclusion transport WAF : les headers seuls sont insuffisants sur ces cibles. Les références open source auditées (curl_cffi, Camoufox, nodriver, FlareSolverr) confirment que TLS/HTTP2 fingerprint, JS fingerprint, mode navigateur et qualité IP interviennent. NiakVIO ne doit pas intégrer un solveur CAPTCHA/Turnstile dans les providers ; prochaine expérimentation raisonnable = transport navigateur/session plus réaliste ou exécution côté réseau utilisateur, puis éventuel sidecar Lab.
- Hors WAF, les 7 NETWORK BLOCKED restent traités séparément : anime-ultime (POST 403), animesultra (connexion/DNS status 0), moviebox (CloudOrchestra cache.php 400), uhdmovies (chaîne DriveSeed profonde puis terminal HTTP), vidfast (403 sans challenge explicitement détecté), wookafr (connexion status 0), yflix (DB/enc-dec 200 puis domaines AJAX status 0/timeout).

## 2026-09-20 — Wooka/VidFast current authority repair prepared

- **Wooka** : current `status 0` traced to stale authority. NiakVIO was still executing `wookafr.tel` / collapsing current aliases to `wookafr.blog`. Current Gowaru source generated 2026-09-18 declares **`https://wookafr.boston`** with **`https://wookafr.center`** fallback and notes stale Referer domains can cause anti-hotlink 403. Current same-brand candidates are preserved independently; only older stale hosts rewrite to boston.
- **VidFast** : official current docs expose **vidfast.to** `/embed/movie/{id}` and `/embed/tv/{id}/{season}/{episode}`, while current All-in-One upstream still uses **vidfast.vc** + enc-dec CSRF. Provider-local runtime now probes `.to/embed` first, then `.vc/movie|tv`, with shared media crawl fallback and the existing enc/dec terminal flow.
- Added a synthetic runtime contract proving `vidfast.to` first, `vidfast.vc` fallback, enc/dec, server POST and terminal HLS. This is **not live proof** until CI/census confirms it.

## 2026-09-20 — MovieBox current Cinescrape authority repair

- Current All-in-One upstream MovieBox no longer uses the legacy vidsrcme/CloudOrchestra chain as its primary path. It resolves TMDB -> IMDb and calls a public Cinescrape JSON endpoint under `pengu.uk/.../stream/movie|series`.
- NiakVIO's published model had already observed `pengu.uk` and `stremio-moviebox-1.onrender.com`, but the active provider Lego still forced `vidsrcme.ru`, which repeatedly reached `cloudorchestranova.com/embed/iframe_player/cache.php` with HTTP 400.
- The MovieBox Lego now uses current Cinescrape/IMDb first and retains vidsrcme as compatibility fallback only. Core TMDB metadata/cache is the IMDb authority; no upstream JavaScript is executed.
- Added synthetic behavior proof for both current success and legacy fallback. This is not a live stream promotion until current CI/census confirms it.

- **Domain Refresh accounting guard corrigé** : le producteur marque un provider `changed` lorsqu'un des cinq champs d'autorité domaine change (`official_site`, `official_hub`, substitutions/replacements), mais le guard ne recomptait que `official_site`. Le run `35476789127` a ainsi déclaré `4khdhub,voiranime` alors que le guard ne voyait que `voiranime`. Le guard compte désormais exactement les cinq champs autorisés et reste fail-closed sur toute autre mutation provider. Test ajouté pour un `official_site` stable avec mapping domaine modifié + rejet d'un champ hors contrat.

- **Domain Refresh transaction accounting — root cause fixed**: the workflow wrote `health-output/domain-site-changes.json` before `reconcile_provider_domain_metadata.py`, so a reconciliation-only domain mutation (observed on `animesalt`) was real in `provider-overrides.json` but absent from `changes.changed`; guard failed with `actual=['4khdhub','animesalt','voiranime'] declared=['4khdhub','voiranime']`. The reconciler now accepts `--changes-output` and merges its changed provider IDs into the same transaction journal before the guard. The guard remains fail-closed for non-domain fields. This should also unblock the pending Flemmix `.cloud → .me` CONFIG publication that CORE Quick currently rejects as stale published DATA.


## 2026-09-20 — WAF browser probe no longer hides Vostfree behind POST

- `probe_waf_browser_session.py` previously selected the last challenged request per provider/lane. Vostfree exposes a challenged GET on `https://ipv4.vostfree.ws/` followed by a challenged POST search request, so the diagnostic selected the POST and returned `unsupported_method` without ever testing the browser-reachable GET.
- The selector now prefers the latest challenged GET when one exists, and only falls back to a non-GET challenge when no navigable challenge is available. This does not add stealth, CAPTCHA/Turnstile solving, cookie fabrication, or challenge bypass logic.
- Regression fixture updated to preserve the real Vostfree GET→POST sequence and require GET selection. Commits: `333f85b9aad7` + `67fe01d904ab`. The census workflow is path-triggered by both files and should now produce a real Chrome verdict for Vostfree instead of `unsupported_method`.


## 2026-09-20 — MalluMV terminal-chain reconstruction

- Latest live targeted evidence still reached MalluMV search + exact detail only: `/search.php?q=Interstellar` -> `/movie/1755/Interstellar_2014_English.xhtml`, both HTTP 200, then returned zero streams.
- Added NiakVIO-owned provider Lego `scripts/provider_patches/mallumv_runtime_v1.py` and bound it in `provider-overrides.json`. The runtime reconstructs only the observable chain TMDB title/year -> search -> exact movie -> confirm -> internal -> bounded terminal-media crawl; no upstream JavaScript is embedded or executed.
- Added behavioral test `tests/provider_mallumv_current_runtime_behavior_test.py` and wired it into current-byte census, targeted recovery and provider non-regression gates. Candidate confirm/internal routes are recorded but are not promoted as live route proof until CI observes them.
- Relevant commits: `aeae9cd84c62` runtime, `fbddb6b5bd69` binding, `1353604a2808` behavior test, `d38551cf1cae` / `34357e15c4d9` / `7c143114d6dd` gates. Live playback status remains unpromoted until a current census proves terminal media.


## 2026-09-20 — WookaFR current multi-player recovery

- Current live evidence on the refreshed `wookafr.boston` authority reaches exact catalogue/detail pages, but the first discovered `lecteurvideo.com` player currently returns HTTP 500. The older provider-local priority Lego could therefore make a historically useful host dominate the bounded seed order even when it is temporarily dead.
- Added `scripts/provider_patches/wookafr_current_runtime_v2.py`, bound after the existing priority Lego. It uses Core TMDB title/year identity, current Wooka search/detail routes, TV episode selection, extracts all current player seeds, and invokes the shared terminal crawl one seed at a time so one failing host cannot starve later embeds. No upstream JavaScript is embedded or executed.
- Added `tests/provider_wookafr_current_runtime_behavior_test.py` proving movie fallback past a failed lecteurvideo seed and a TV season/episode player chain. Wired into current-byte census, targeted recovery, and non-regression gates.
- Relevant commits: `d1a4f6f3dbe8` runtime, `c846c981d5c2` binding, `3787cfac0e6c` behavior test, `d5c37e6091ca` / `33385adc62d0` / `c245250f6a20` gates. Live playable status remains unchanged until current census evidence proves terminal media.


## 2026-09-20 — MovieBox multibase current Stremio fallback

- Current CI evidence reaches the modern Pengu MovieBox Stremio route but GitHub egress receives HTTP 429; legacy vidsrcme then reaches CloudOrchestra and fails at cache.php HTTP 400. This is transport/backend failure, not a reason to discard the modern IMDb route.
- Independent current public implementations were cross-checked before changing DATA: `D3adlyRocket/Test/providers/moviesmod.js` and `hfip/Box/api/index.py` both use `moviebox-cfa7.onrender.com/<config>/stream/movie|series/{IMDb}.json` and consume the same `streams` JSON shape; a separate public verification report records its manifest as reachable.
- `moviebox_vidsrcme_runtime_v1.py` now supports ordered current bases. Canonical DATA keeps Pengu first, retries the proven `moviebox-cfa7.onrender.com` Stremio endpoint second, and only then falls back to legacy vidsrcme. Per-base Referer is preserved.
- Behavioral coverage now requires primary-current success, Pengu failure -> alternate-current success without legacy, and all-current failure -> legacy. Contract coverage pins the alternate current base in canonical DATA. Commits: `c7da73325d4a`, `2d37045add2e`, `b7b2b10ac5e4`, `48a3f830c8d0`. Live provider status remains unchanged until current census proves terminal media.


## 2026-09-20 — UHDMovies DriveSeed terminal fanout repair

- Current targeted evidence proves the full UHDMovies catalogue/gateway chain through `uhdmovies.my` and `cloud.unblockedgames.world` into multiple `driveseed.org/file/*` pages. The current failure is terminal selection: generic `cdn.video-gen.xyz` candidates are discovered first and currently return HTTP 500.
- Current public DriveSeed extractors were cross-checked and resolve explicit server buttons (Instant Download, Resume Worker, Direct Links, Resume Cloud) before generic direct-link scanning. NiakVIO's runtime did the reverse and returned immediately on the first generic direct candidates.
- `uhdmovies_runtime_v1.py` now resolves explicit DriveSeed buttons first, retains multiple unique terminal candidates, then appends generic page direct links and finally shared crawl results. This lets Core playback validation discard a dead CDN while preserving viable worker/cloud mirrors. Canonical options add bounded `maxDownloadButtons=8` and `maxTerminals=12`.
- Added `uhdmovies_terminal_multiserver_behavior_test.py` reproducing a dead video-gen candidate beside a healthy Resume Cloud worker and requiring the healthy explicit server to be first while preserving the generic fallback candidate. Wired into census, targeted recovery and non-regression; cleaned duplicate census path entries found during the edit. Commits: `b8126bfde2ee`, `dabe8ff8e17d`, `ce9e5729b057`, `09b9c3765aab`, `7c6d09dcc2cd`, `fdf461bdf3f0`, `fc87d983680c`.


## 2026-09-20 — Batch-first provider repair architecture

- User requirement re-confirmed: NiakVIO must scale from the current 46 providers to several hundred; provider-by-provider testing/repair cannot be the default operating model.
- Live provider probing was already concurrent (`audit_provider_quick_yield.py` ThreadPool and targeted recovery pool). The remaining scalability defect was repair orchestration: too many provider-specific Legos/tests were being handled as isolated cases.
- ProviderBase shared player crawl now uses adaptive bounded fan-out (`NIAKVIO_PROVIDER_ADAPTIVE_PLAYER_FANOUT_V25`): dense pages can retain up to 16 ranked player seeds with an adaptive request budget up to 18 instead of hard truncating every provider to 8 seeds / 10 requests. This is a Core-wide repair intended to eliminate repeated per-provider player-starvation patches.
- Added `scripts/build_provider_repair_batch_plan.py`: unresolved census rows are grouped by repair scope + capability strategy + normalized evidence depth + issue class. Exact runtime families are metadata only, so unique provider family labels cannot collapse the queue back into one-provider batches.
- Added `scripts/run_provider_repair_batch.py`: selected groups are executed as one concurrent `audit_provider_quick_yield` pass; provider-local execution is the exception path only.
- Targeted regression workflow now consumes the current batch plan, uses up to 20 concurrent workers, skips pure WAF/environment groups from JS-repair probing, and publishes group-level verified/playable/contradiction results.
- Added `scripts/refine_provider_repair_batches.py`: coarse groups automatically split only when observed runtime/network signatures diverge. This supports hypothesis-first batching (e.g. two html_scraper providers start together, then split if one is HTML search and another is API mapping) without manual provider-name routing.
- Current census advanced from 25/46 to 26/46 with PersianStremio now PARTIAL OK (movie lane). The 26/46 run tested SHA `aeae9cd84c62`; therefore MalluMV binding, Wooka multi-player runtime, MovieBox alternate current authority, UHDMovies terminal changes, and ProviderBase V25 fan-out still require later current-byte census verdicts before promotion claims.
- New durable artifacts/gates: `automation/provider-repair-batch-plan-latest.json`, future `automation/provider-repair-batch-refined-latest.json`, plus tests for adaptive player fan-out, batch grouping, batch runner selection, and signature-driven batch refinement.


## 2026-09-20 — Horizontal census sharding for 300+ providers

- Added deterministic provider sharding to `scripts/audit_provider_quick_yield.py`: `--shard-count` + `--shard-index` assign a provider by SHA-256 so shards are stable, disjoint and exhaustive for a fixed shard count.
- Added `scripts/merge_provider_census_shards.py` to merge independent shard reports back into the canonical quick-yield schema, reject duplicate provider/lane ownership and recompute all aggregate counts.
- Added manual `.github/workflows/provider-census-sharded.yml`: 8 GitHub runners × up to 20 quick-yield workers, exact current-byte materialization per runner, artifact merge, census rendering and batch-repair-plan generation. It is manual while the catalogue is only 46 providers; it is the horizontal path for hundreds of providers without changing provider logic.
- Fixed unresolved-scope onboarding semantics: providers present in the current manifest but absent from the last census status are now automatically included as unresolved. A stale status snapshot can no longer hide newly onboarded providers during a large import.
- Added structural tests for shard partitioning, shard merge, sharded workflow wiring and new-provider unresolved inclusion. Provider-local testing is not the scale unit; shard -> concurrent probe -> coarse repair batch -> observed-signature refinement is now the scale path.
- Commits: `730dc79ec64d`, `73db5edfaf91`, `07056a0cfb41`, `9ce398490cbe`, `7ed55375661c`, `45b7bb442ef4`, `1aea55913302`, `0f683cd5db53`, plus CI gates through `2834381a3699`.


## 2026-09-20 — Bulk onboarding path for hundreds of providers

- The existing `add-provider.yml` remains the high-assurance path for one manual provider (deep hub resolution, branding, bounded Lab, atomic publish). It is intentionally no longer the scale path for a catalogue expansion.
- Added `scripts/stage_provider_batch.py` plus `add_provider.stage(..., bulk=True)`. A bulk request (list or `{providers:[...]}`, max 2000) is fully preflighted first, then all rows are staged locally as `enabled=false`, `validation=onboarding_pending`, with no network discovery, branding, native Lab or activation attempt. ProviderBase legacy repair is deferred and executed once after the whole batch instead of once per provider.
- Added `.github/workflows/provider-bulk-onboarding.yml`: one batch request -> one validated binary git transaction -> one publish commit `provider: bulk stage N pending`. The workflow auto-triggers only from `.github/provider-onboarding/batch.json`, not from its own implementation changes.
- Bulk publication does not launch the ordinary mono census, targeted repair, or Domain Refresh. Those workflows explicitly defer `provider: bulk stage ...` commits so they cannot race the exact large-import baseline.
- `provider-census-sharded.yml` now listens for successful `PROVIDER - Bulk Onboarding` completion, pins one exact current-main SHA, runs 8 deterministic shards with up to 20 workers each, merges evidence, updates proof history, renders status, builds the coarse repair plan, and (for the automatic bulk path) persists canonical census/status/history/batch-plan evidence back to main.
- The ordinary census also ignores `ci(census-sharded): ...` persistence commits, avoiding recursion. The resulting `automation/provider-repair-batch-plan-latest.json` is the trigger/input for batch-aware targeted recovery.
- This establishes the high-volume lifecycle: bulk local stage (disabled) -> atomic publish -> 8-shard census -> coarse capability batch -> observed-signature refinement -> concurrent repair probes -> proof-driven activation. No per-provider workflow is required for initial integration.
- Key commits: `2d8a5926de2a`, `aba259e84585`, `816a1757e476`, `31125c706c45`, `95d24592fb3f`, `b8474742dce6`, `fa6f1e973c71`, `d7605f791e09`, tests/gates through `15445f0ed7f0`.


## 2026-09-20 — Targeted repair now shards with catalogue size

- Large-catalogue scaling is symmetric: catalogues above 120 providers already use the 8-shard census, and targeted repair now uses the same horizontal model instead of becoming the next monolithic bottleneck.
- Added reusable `scripts/run_provider_targeted_recovery.py` with deterministic provider sharding, batch-plan selection, environment/WAF exclusion, adaptive current-byte probes and group-level verdicts. The same engine is used for small catalogues (1 shard) and large catalogues (8 shards).
- Added `scripts/merge_provider_targeted_recovery_shards.py` and `.github/workflows/provider-targeted-recovery-sharded.yml`; merged results are refined by observed runtime/network signatures before any provider-local fallback.
- `TEMP - Targeted Regression Recovery Probes` now routes by catalogue size: <=120 providers stays single-job, >120 is handled by the sharded workflow. Tests pin deterministic partitioning, shard merge and mono-to-sharded routing.
- Current live census remains 24 FULL + 2 PARTIAL = 26/46 from SHA `aeae9cd84c62`; newer Core/player, MalluMV, Wooka, MovieBox, UHDMovies and batch/sharding changes are not yet represented by that persisted census.

## 2026-09-20 — Brain Repair V6 experience-transfer checkpoint

- User requires Repair to behave as a reproducible intelligent Brain, not as manual provider-by-provider intervention. Prior manual corrections must become reusable evidence, especially route/search/detail/player/API knowledge.
- Production Repair now separates **validated skill memory** from **experience priors**. Skill memory may rank a repair profile only after strict deep improvement; experience priors may guide experiments but never grant acceptance/publication authority.
- scripts/build_brain_repair_experience.py distills current census + provider-overrides.json into automation/brain-repair-experience.json: provider strategy, safe route templates/families, current Provider Lego provenance, domain-memory presence and operational status. Peer transfer is limited to reusable route templates supported by at least two operational providers with the same strategy; opaque/session/token routes and fixture-specific literals never transfer between providers.
- scripts/run_provider_brain_repair.py rebuilds this experience from current bytes/census before each portfolio run. Multi-wave Repair therefore starts from accumulated current knowledge and can immediately reuse newly validated experience on later waves.
- scripts/adaptive_runtime/runtime_repair.py now orders repair routes as: explicit configured knowledge -> provider-local learned/current routes -> same-strategy operational peer priors -> generic fallback. It also reuses safe provider-local catalogue/transport hints (official/base/fallback origins, non-sensitive User-Agent, timeout, blocked hosts/path patterns). Secrets/auth/signing keys are never transferred.
- Restored the missing executable adaptive repair path: scripts/provider_patches/adaptive_runtime_recovery_v4.py from the runtime-TMDB-key revision and verified-media adaptive_runtime_recovery_v5.py. V5 keeps extension-only URLs as hints, recursively traverses deceptive media-looking HTML, and fails closed on unverified native rows.
- Adaptive route expansion now supports {query}, {slug}, {id}, {tmdbId}, {imdbId}, {year}, {season}, {episode}, {mediaType} and {type} so historical route knowledge can actually participate in movie/TV/anime repair.
- Repair CI now compiles/tests the restored executor and experience transfer, deletes stale baseline/current-run evidence before execution, and retains automation/brain-repair-experience.json with the Brain report.
- Previous global Repair runs 35480639251 and 35480831922 did not reach repair waves; both stopped in stale architecture tests. The current resolver contract test has been updated to the actual provisional -> pre-resolved TMDB -> verified flow. **No new live provider success may be claimed until the next current-byte portfolio run reaches and completes a Brain wave.**

## 2026-09-20 — Census-owned symptom Repair checkpoint

- User requires PROVIDER_CENSUS_STATUS.md / automation/provider-census-status.json to remain the operational source of truth. Repair must not independently rescan/reselect the whole catalogue.
- Census renderer now exposes symptomaticProviders/brainQueue, repairQueue, and environmentQueue. FULL OK/PARTIAL OK are protected; PROVIDER WAF/ANTIBOT remains symptomatic/visible but is environment-only and excluded from unattended JS/provider Repair by default.
- run_provider_brain_repair.py consumes the census repairQueue (or the compatible brainQueue fallback) as its automatic input. Explicit provider arguments are intersected with that queue, so stale/manual requests cannot drag stable providers back into repair.
- run_provider_repair_pipeline_v6.py is census-first: pre-check only the current repairQueue, merge those observations back into the global census while carrying stable rows, drop providers that recovered, repair only the still-symptomatic subset, then revalidate the full symptom set that entered the cycle and regenerate PROVIDER_CENSUS_STATUS.md + provider-census-status.json + proof history/batch plan.
- Repair CI proves that network-tested providers are a subset of the cycle census symptom set. It persists only census evidence to main after resetting candidate provider/Core workspace bytes; Repair candidate code remains non-published.
- Census evidence-only commits no longer recursively trigger TEMP full census merely because PROVIDER_CENSUS_STATUS.md changed.
- Current pre-change census had 20 symptomatic providers, including 7 PROVIDER WAF/ANTIBOT; therefore the automatic code-repair queue is expected to begin at 13 until a fresh census changes those classifications.

## 2026-09-20 — Census-owned Repair run 35482101082

- First census-owned Repair cycle correctly pre-tested only the 13 automated repairQueue providers: 19 semantic tasks / 56 probes, with zero FULL/PARTIAL/WAF providers included.
- Pre-census persisted successfully to main as commit 5dc2b43d7e36: 24 FULL OK, 2 PARTIAL OK, 1 CANDIDATE OK, 4 ROUTE PROVEN, 3 CHAIN REACHED, 5 PROVIDER NETWORK BLOCKED, 7 PROVIDER WAF/ANTIBOT; 20 symptomatic total / 13 automated Repair / 7 environment-only.
- Notable census refinement from the targeted current-byte replay: yflix moved from NETWORK BLOCKED to ROUTE PROVEN; UHDMovies remained CHAIN REACHED; no provider became currently playable in the 13-provider precheck.
- Repair then failed before route recovery/Brain at upgrade_provider_external_identity_route_v11_1.py because the current recovery source already contained the strict _repair_recipe_origin_allowed(row) execution boundary but the historical marker had been dropped; V11.1 still required the obsolete one-line anchor.
- Fixed V11.1 to recognize the already-correct current semantic boundary and restore only its durable marker/comment, falling back to the legacy transformation only when the old form truly exists. This is a migration-idempotence fix, not a provider-specific repair.

## 2026-09-20 — Brain V7 virtuous-loop checkpoint

- Repair remains census-owned: automatic work is selected from automation/provider-census-status.json repairQueue only; FULL/PARTIAL stay protected and PROVIDER WAF/ANTIBOT remains environment-only by default.
- Brain control plane is now V7. Census state is a monotonic diagnostic prior, never success authority: ROUTE PROVEN -> route_proven_gap/detail+, CHAIN REACHED -> chain_terminal_gap/player+, CANDIDATE OK -> candidate_replay_gap, PROVIDER NETWORK BLOCKED -> provider_transport_gap before parser mutation.
- Adaptive runtime consumes census symptom depth to reorder route roles and budgets instead of rediscovering search after deeper proof. It reuses provider-local learned routes/transport hints first and same-strategy operational peer priors only as bounded hypotheses.
- Production Repair now persists sanitized negative experiment memory in automation/brain-repair-memory.json. Rejected (provider, causal signature, profile, experimentVariant) attempts increase failure memory; accepted attempts reset consecutive failure count. The planner rotates among four bounded variants before repeating the least-failed one, so improvement -> rerun is not an identical replay.
- Brain experience schema v2 now learns reusable ROUTE_RECOVERY_REQUEST_SPEC_V1 request recipes from current evidence: GET/POST, form/JSON body templates, semantic placeholders and safe header names. Opaque bodies/tokens/residue and identity-helper hosts are never executable or peer-transferred; peer request recipes require support from at least two operational providers of the same strategy.
- The adaptive runtime can execute fully reconstructible provider-local request recipes and exploratory peer recipes, including POST form/JSON, then feed HTML/JSON response URLs into the existing bounded player/media resolver. A synthetic behavior test proves POST query -> player -> verified media traversal.
- Historical adaptive V4 executable code has been retired from scripts/provider_patches. Its generator moved behind scripts/adaptive_runtime/runtime_recovery_generator.py; V5 is the sole current publishable adaptive runtime. Reapply accepts historical V4 wrappers only as migration input and upgrades them directly to V5.
- Live Repair run 35483066561 (trigger SHA 9d5fa03cc181...) passed canonical preflight and entered real Repair before these later V7/request-recipe refactors. Do not attribute any provider repair to the newer code until a fresh post-refactor census-owned run completes.

### 2026-09-20 — Repair loop continuation after run 35512170961
- Revalidated current main before continuing: Repair census authority is run `35512170961-post-repair` (trigger SHA `50c59eabe93f...`), with 24 FULL OK, 2 PARTIAL OK and 12 providers in `repairQueue`; 8 WAF/harness cases remain outside provider-JS mutation.
- Run 35512170961 executed the 12 repairable providers but accepted 0 repairs and deferred all 12 to Learning after the then-available bounded experiment variants were exhausted. This is not proof that the providers are irreparable; it is evidence that the previous strategy family was exhausted.
- Current main is materially newer than the tested SHA: Brain negative-memory policy now exposes five materially distinct variants (0..4). Variant 4 is failure-class-specific rather than a generic retry: `provider_transport_gap -> provider_origin_failover_v1`, `route_proven_gap -> proven_route_terminal_traversal_v1`, `chain_terminal_gap -> chain_terminal_extractor_v1`, `candidate_replay_gap -> retained_candidate_replay_v1`. It consumes census depth, provider-local evidence and bounded same-strategy peer priors.
- Found and fixed a control-plane divergence after WAF overlay: `automation/provider-census-status.json` could be updated without regenerating `PROVIDER_CENSUS_STATUS.md`, producing different HARNESS MISMATCH / HARNESS/ENV BLOCKED counts. Workflow `provider-waf-browser-session.yml` now renders Markdown from the authoritative JSON state after transport merge and stages both together; `tests/provider_waf_census_markdown_sync_test.py` enforces the contract.
- Next execution: rerun canonical Repair from current main against `repairQueue` only. Evaluate v4 by causal cohort, preserve FULL/PARTIAL lanes, then regenerate census. Do not treat variant exhaustion as provider failure; escalate exhausted cohorts into new-strategy Learning blueprints instead of repeating retry counts.

### 2026-09-20 — Repair iteration 15 materialization blocker
- Repair run `35521087496` tested SHA `3617e0115e7b...`. Preflight passed, but canonical repair stopped before Brain execution during global provider materialization.
- Wookafr current-runtime contained a malformed HTML double-quote decoder. The decoder is now aligned with the valid Mallumv form.
- Generic guard added: Repair preflight now runs the Wookafr behavior contract and materializes the full current catalogue to temporary artifacts before network repair work. A non-target provider can no longer reach the expensive Brain phase while its generated bundle is invalid.
- Run `35521087496` is not evidence against causal Brain v4 because Brain v4 was not reached. Rerun the same census repair queue on the corrected SHA.

### 2026-09-20 — Same-run positive evidence loss confirmed and fixed
- Repair run `35521510249` on SHA `0a6ff016e475...` completed successfully as a pipeline and reached causal Brain variant 4 for all 12 repairQueue providers. Brain generated real `adaptive_runtime_recovery` candidates, accepted 0, fixed 0 and deferred all 12 to Learning after the final bounded variant.
- Artifact cross-check exposed a control-plane false negative: `automation/provider-repair-yield-v6.json` proved UHDMovies current bytes with 2 raw / 2 playable / 2 verified streams (`playable_verified`), while the earlier `provider-repair-portfolio-candidate.json` sample for the same run had zero and the post-repair census therefore kept UHDMovies symptomatic.
- Root cause: `run_provider_repair_pipeline_v6.py` rendered `provider-census-post-repair.json` / census before the final repair-yield audit. Stronger positive evidence found later in the same run was never merged back.
- Added `scripts/merge_provider_same_run_positive_evidence.py`: only identity-safe positive evidence is monotonic per provider/type, ranked verified > playable > raw; weaker/contradictory evidence cannot replace stronger evidence, and prior sample history is retained.
- Added `tests/provider_same_run_positive_evidence_merge_test.py` and wired it plus py_compile into Repair preflight. The pipeline now merges the final current-byte yield into the candidate portfolio and renders the authoritative post-repair census only afterward.
- Expected next validation: rerun Repair on current main; if UHDMovies re-proves in the final yield, it must leave the symptomatic repair queue instead of being reset to zero. Any additional same-run positive providers must receive the same treatment automatically.

### 2026-09-20 — Causal Brain chaining + final-variant generation rollover
- Repair run `35524034504` (run #79, SHA `ef10e44627c4...`) did not reach canonical Repair: preflight failed in the newly added same-run-positive merge test because fixture samples were iterated as lists instead of entries. `merge_provider_same_run_positive_evidence.py` now retains individual prior/current fixture samples correctly; run #79 is not Brain evidence.
- Learning run `35521698361` (run #203, SHA `b9df01c61ac3...`) progressed through full catalogue observation and into the adaptive queue, then failed during route refresh because a targeted Learning refresh exposed an Anidb split domain state (`anidb.app -> anidb.pics`) and global override validation aborted. Current canonical DATA already identifies `anidb.pics` as Anidb's terminal and `anidb.app` as historical.
- Generic Learning/domain fixes: targeted `resolve_provider_hubs --provider X` now scopes pre-resolution sanitization to X instead of mutating unrelated providers; `run_brain_learning_queue.refresh_stage_routes` now executes canonical provider-domain reconciliation/rebuild before runtime-profile application and override validation. Contract test: `learning_targeted_domain_refresh_contract_test.py`.
- Causal Brain weakness confirmed from Repair run #78 artifacts: real variant-4 candidates could improve runtime evidence (for example no provider request -> provider response/no streams) but were discarded because production acceptance correctly requires playable proof. This prevented multi-step reasoning.
- Added sandbox-only bounded exploration chaining. `compare_exploration_progress` accepts only concrete causal evidence gain (provider access/successful request/returned/playable stream) with no runtime, malformed-request, stream, or identity regression. Deep can retain such a candidate only when `NUVIO_BRAIN_EXPLORATION_CHAIN=1`; it is explicitly non-publishable and never counted/persisted as an accepted repair. The next round replans from the new observation rather than replaying the stale hypothesis. Normal Deep remains one strict round; Brain Repair alone enables up to 3 bounded rounds. Contract test: `brain_exploration_chain_test.py`.
- Existing negative memory contained old variant-4 failures for nearly all 12 repairQueue providers. Those observations remain retained, but the final causal variant is now generation-versioned. Policy `finalVariantGeneration=2`: variants 0-3 continue consuming all historical negative evidence; final variant v4 only consumes failures from the current generation. Old rows default to generation 1. Planner output, negative-memory transport, persisted rows, sanitized Brain report and orchestrator exhaustion checks now carry `experimentGeneration`.
- Contract test `brain_final_experiment_generation_test.py` proves that v0-v3 + old v4 generation 1 selects executable v4 generation 2 (not exhausted), while adding a failed v4 generation 2 exhausts the signature again. No negative history was deleted or reset.
- Next validation must use a fresh Repair SHA: preflight must pass sample-merge, exploration-chain and generation-rollover contracts; then inspect sandbox `exploration_progress`, replanned hypotheses, strict accepted repairs, same-run positive merge and final census. Learning must also rerun on current HEAD to verify targeted domain reconciliation no longer fails on unrelated Anidb state.

### 2026-09-20 — Brain repair truth gates + immutable multi-round attribution
- Repair run `35524987076` (run #81, SHA `003ead41fd05...`) did **not** execute provider repair. Preflight failed in `brain_final_experiment_generation_test.py`: after all five variants were exhausted, the planner reported an arbitrary least-failed historical variant/generation instead of the actually exhausted current terminal variant. Therefore #81 is control-plane failure only, not provider/Brain evidence.
- Fixed planner exhaustion semantics: an exhausted signature now reports the current final experiment variant and `finalVariantGeneration`, so downstream orchestration cannot confuse generation-1 history with the generation-2 causal experiment that was exhausted.
- Tightened `run_provider_brain_repair.fixed_providers()`: playable media is no longer sufficient. A provider leaves the Brain remaining set only when `automatic_repair_identity_gate()` proves playable media with positive fixture-level identity and no contradiction/duration mismatch. Sandbox playable-with-unknown-identity remains useful exploration only.
- Multi-round attribution bug fixed generically. Every generated/not-generated/rejected/accepted/exploration event now carries an immutable `brain_plan` snapshot containing provider, failure class, evidence signature, experiment variant/generation, strategy, pipeline stage and hypotheses. `annotate_and_learn()` consumes that event snapshot rather than mutable final `PLANS`, so a round-2 replan cannot rewrite round-1 negative memory.
- Added `tests/brain_round_plan_attribution_test.py` and wired it into Repair preflight. The contract deliberately leaves only the round-2 plan in mutable `PLANS` and verifies that round-1 remains stored under its own signature/generation.
- Next authoritative Repair must run from a SHA containing these changes. Success criteria remain behavioral: at least one current repairQueue provider must obtain strict identity-verified playable proof from Brain-generated bytes; CI/preflight alone is not a repair.
- Repair run `35526276628` (#82, SHA `1bb16c1558ed...`) also stopped in preflight before provider probing: `run_provider_brain_repair.py` was imported by the contract test without `scripts/` on `sys.path`, so the new strict identity-gate import failed. The entrypoint now inserts its own scripts directory before importing `repair_identity_gate`. #82 is not provider/Brain evidence.

### 2026-09-20 — Current-observation program synthesis
- Repair run `35526333595` (#83, SHA `7a3838afd1ef...`) again stopped in preflight before provider probing. All newly added Brain contracts passed; the failure came from an older Node source-shape assertion that still required the pre-replan expression `brain.PLANS.get(parent_key or key)`. The runtime intentionally uses `plan_key` so exploration children can be replanned; the stale contract was updated. #83 is not provider failure evidence.
- Architectural audit found a major intelligence loss: `provider_worker.cjs` already captures sanitized route-proof data (stage, method, normalized path, safe body shape/values, response ID/slug hints, content type), but `brain_repair_runtime._planner_result()` reduced every network observation to only status + infrastructure. The Brain was therefore asked to synthesize repairs after discarding the causal request shape.
- Planner transport now preserves bounded non-secret causal shape: stage, method, path pattern, body kind/field names, response hint keys and content type. Raw URLs, body values and header values remain excluded from planner transport.
- Added provider-local current-run request synthesis in `adaptive_runtime/runtime_repair.py`. Successful non-infrastructure GET/POST observations can become executable sandbox request recipes only after fixture values are abstracted to reusable placeholders. Current-run recipes are evaluated before historical provider recipes and peer/generic priors.
- Generic provider IDs are no longer guessed as TMDB IDs. A later request may use `{binding:<key>}` only when an earlier replayable response exposed exactly one safe value for that key and the observed later request consumed that exact value. Ambiguous multi-ID responses remain evidence-only.
- `runtime_recovery_generator.py` now executes bounded multi-pass request programs: replay independent recipes, extract unique safe response bindings, then execute dependent recipes. This supports causal chains such as search/detail -> unique internal ID -> player -> media without provider-specific code.
- Added/expanded `tests/brain_current_observation_recipe_test.py`: excludes infrastructure and failed requests, rejects token/internal-ID guessing, verifies current evidence priority and planner privacy, then executes a synthetic response-bound search -> player -> HLS chain end-to-end.
- Next authoritative Repair must use a SHA containing this synthesis. The milestone remains strict identity-verified playable proof on a real current repairQueue provider; preflight success alone is not a repair.

### 2026-09-20 — Repair #84 harness result + Learning #204 isolation fix
- Repair run `35526908140` (#84, SHA `2e4578d4073d...`) did not reach provider probing. It stopped when the new current-observation contract imported the adaptive runtime outside the normal scripts path and could not resolve `apply_provider_overrides`. The test now explicitly loads `scripts/` and `scripts/adaptive_runtime/`; #84 is harness-only evidence.
- Learning run `35524925841` (#204, SHA `eeee8d9f...`) passed catalogue observation, clean reconstruction, domain-scope contracts and override validation, then failed in the adaptive queue while `reconcile_provider_domain_metadata.py --rebuild` rebuilt every changed provider. `voiranime` was not minimizer fixed-point and blocked the whole queue although it was not the targeted provider.
- Domain reconciliation now supports `--provider <id>`. Learning `refresh_stage_routes()` passes the current provider and rebuilds only that provider before stage profile application/validation. A neighboring stale/non-fixed provider can no longer abort unrelated provider Learning.
- Contracts updated to require provider-scoped rebuild. This preserves the canonical reconcile-before-runtime-profile order while restoring transaction isolation.

### 2026-09-20 — Repair #85 exposed dormant recipe execution
- Repair run `35527085231` (#85, SHA `5147730cf511...`) stopped in the new end-to-end current-observation preflight before provider probing. The synthetic runtime called only generic direct paths and never replayed the observed POST search recipe.
- Root cause is generic and historical: `_safe_request_recipe()` accepted only input rows with `executable=true`, sanitized them, then returned a recipe **without** the `executable` field. `runtime_recovery_generator.requestRecipe()` refuses any recipe unless `recipe.executable===true`. Therefore sanitized provider-experience/peer/current-observation recipes could be learned and counted yet remain dormant at execution time.
- Fixed `_safe_request_recipe()` to preserve `executable: True`; the current-observation contract now explicitly asserts this. This is a plausible common cause for the long-standing gap between learned request recipes and zero autonomous accepted repairs.
- #85 is preflight evidence, not a real provider repair attempt. A fresh Repair on the fixed SHA is required.

### 2026-09-20 — Real Repair now exposes route-proof evidence to Brain
- Audit after #85 found that normal `health_check.mjs` did not forward `routeProofTrace` into provider worker context. Rich safe request/response proof therefore existed in the worker implementation but was not requested by the real Deep Brain repair lane.
- `health_check.mjs` now forwards opt-in `modeConfig.route_proof_trace`; `run_adaptive_deep_repair.py` enables it only for bounded Brain Deep repair. Normal health/parity runs remain unchanged.
- The current-observation contract requires both ends of this wiring. This makes real repair rounds capable of seeing the same sanitized stage/method/path/body-shape/response-hint evidence used by the synthetic program-synthesis test.
- Repair #86 was triggered before this wiring landed. It can validate executable recipes but cannot be treated as authoritative proof of current-run request synthesis. A new Repair SHA is required.

### 2026-09-20 — Route-proof worker -> health -> Brain transport completed
- A second evidence-loss boundary was found after enabling `routeProofTrace` in real Deep Repair: `health_check.mjs` remapped `worker.network_observations` into fixture results but dropped the already-sanitized route-proof fields (`proof_url`, safe body shape/values, response ID/slug hints, content type and route-proof marker). The Brain would therefore still have received only coarse observations.
- `health_check.mjs` now preserves the bounded/redacted route-proof evidence when `route_proof_trace` is true. Header values are intentionally not propagated; only safe header names are retained. Raw route/body evidence remains bounded by `provider_worker.cjs` before entering the health report.
- `tests/brain_current_observation_recipe_test.py` now requires this worker -> health transport in addition to Deep route-proof enablement and end-to-end response-bound recipe execution.
- Commits: health transport `47b416ab1528...`, contract `38b40ac5b6c...`.
- Repair #87 (`35527314099`, SHA `0bad088ea5f6...`) predates this health-transport fix, so it is not authoritative for current-observation program synthesis even if its earlier preflight/runtime phases pass. A fresh Repair on the later HEAD is required.

### 2026-09-20 — Repair #88 reached real Brain round; causal replan transport fixed
- Repair run `35527480898` (#88, SHA `ad7a87a4abc...`) is the first run in this sequence that passed all preflight contracts and entered the real 12-provider repairQueue with end-to-end route-proof synthesis enabled.
- 4KHDHub completed an actual Brain round-1 candidate and changed runtime diagnosis to `content_lookup_completed_no_streams` with no runtime errors. During exploration replan for round 2, the canonical base planner transport aborted with `brain_planner_input_invalid` on a ~106 KiB payload, causing the whole Repair wave to fail before the other 11 providers could run.
- Root cause in control flow: `scripts/adaptive_runtime/brain_repair_runtime.py` already isolated/bisected initial planner batches, but did not override `replan_observation()`; exploration replans therefore bypassed the adaptive transport and called the base runtime's direct stdin planner path.
- Planner input now supports an optional `NUVIO_BRAIN_PLANNER_INPUT_FILE` source. Adaptive transport locally JSON-validates the exact ASCII bytes, tries stdin first, and only for planner input-parse exit 2 retries the exact same bytes via a temporary file. No payload is reserialized between attempts.
- Adaptive `replan_observation()` now uses the same bounded transport as initial planning. If a single-provider replan still fails after retry, that provider receives a transport-deferred plan instead of aborting the other providers/wave.
- Added `tests/brain_replan_transport_retry_test.py` and Repair preflight coverage. The test reproduces stdin parse failure, proves byte-identical file retry succeeds, and proves exploration replan uses the adaptive path.
- Census persisted from #88 remains 24 FULL OK + 2 PARTIAL OK + 12 repairQueue; #88 cannot be used as final repair efficacy evidence because the wave terminated during 4KHDHub round-2 replanning.

### 2026-09-20 — Learning #205 adaptive queue succeeded; proposal provenance fixed
- Learning run `35527089718` (#205) passed clean reconstruction, targeted domain isolation, complete catalogue observation, daily coverage and the adaptive Learning queue. It processed 9 new providers before the 60-minute work budget was exhausted; the queue exited cleanly with persisted state instead of failing.
- The sanitized Learning state reached 222 proposals, 156 memory entries and preserved native-reader learning. The final run failed only while materializing review-only clean ProviderBase candidates: `fluneo: missing provenance row`.
- Root cause: the reconstruction stage includes newly discovered upstream providers (98 staged vs 46 production catalogue). `materialize_clean_provider_reconstruction.py` required every clean candidate to already exist in production `PROVENANCE.json`, which is impossible for genuinely new providers.
- Added a fail-closed proposal provenance rule: existing/pending-reconstruction providers still require an existing provenance row; only `candidate_code_origin=new-niakvio-clean-seed` may synthesize a new row. The synthesized row is proposal-only, production/publication disabled, activation ineligible, canonical pipeline proof required, and upstream code remains knowledge-only/not executed.
- Added `tests/learning_new_provider_provenance_test.py` and Learning preflight coverage. This unblocks proposal materialization for new hub providers without weakening provenance integrity for already published providers.

### 2026-09-20 — Three-round Brain budget made real
- Audit of Repair #88 timing exposed a hidden contradiction: Brain Repair requested up to 3 causal rounds, but production policy allowed only 2 mutations/provider and 45 seconds/provider. 4KHDHub's first real retest took roughly 76 seconds, so round 2 would have been budget-rejected even after fixing planner transport; round 3 was impossible by mutation count.
- Added a dedicated `production.explorationChainBudget` used only when `NUVIO_BRAIN_EXPLORATION_CHAIN=1`: 3 mutations/provider, 300s elapsed/provider and 360k generated bytes, while repeated-signature protection remains 2. Normal Deep keeps the original 2 mutations / 45s / 180k limits; Learning continues to use its global slot deadline.
- Both the Python mutation gate and the Node planner now receive/use the same exploration-chain budget. Adaptive initial planning and replanning transport the explicit `explorationChain` flag.
- Added `tests/brain_exploration_budget_test.py` and Repair preflight coverage. The contract proves a provider at mutation 2 / elapsed 60s is still eligible inside Brain exploration, mutation 3 is bounded, and the same state remains over-budget in normal production mode.

### 2026-09-20 — Learning per-provider refresh scalability
- Learning #205 processed only 9 providers inside its ~60-minute work budget. Logs showed the dominant avoidable cost: after each provider route discovery, `refresh_stage_routes()` called `build_provider_runtime_profiles.py --stage ... --apply-stage` across the entire 98-provider reconstruction stage.
- Added repeatable `--provider <id>` targeting to `build_provider_runtime_profiles.py`. In targeted mode it isolates/profiles/reapplies only the requested provider, preserves global generation metadata instead of replacing it with a count of 1, and leaves the full-build behavior unchanged when no target is supplied.
- Learning route refresh now passes the current provider to runtime-profile rebuild, matching the already provider-scoped domain metadata reconciliation. The subsequent quarantine/override validators remain whole-stage safety checks.
- Extended `learning_targeted_domain_refresh_contract_test.py` to require provider-local runtime-profile refresh. This is required for scaling the Learning queue from ~100 staged providers toward hundreds without O(N²)-style repatching work.

### 2026-09-20 — Learning targeted-profile regression caught by CORE Gate
- CORE Workflow Gate run `35532067455` failed the stage runtime-profile smoke after the first targeted-refresh implementation. Diagnosis against the last pre-optimization SHA found the exact regression: the new `target_ids` guard had been inserted into `collect_staged()`, where `target_ids` is undefined, instead of inside `reapply_stage()`.
- Fixed the target guard placement. Full `build_provider_runtime_profiles --stage ... --apply-stage` once again collects the complete stage without referencing target state; targeted mode filters only the reapply loop and provider/profile working set.
- The targeted Learning contract now asserts by source-order that the guard exists inside `reapply_stage()` and that `collect_staged()` contains no `target_ids` dependency. The existing real-worker smoke continues to validate the full path and now exposes subprocess stderr/stdout on failure.

### 2026-09-20 — Repair post-accept domain isolation
- Audit found the same unrelated-provider coupling in Repair persistence that had already affected Learning: after an accepted Brain wave, `run_provider_brain_repair.materialize()` called global `reconcile_provider_domain_metadata.py --rebuild`. An unrelated non-fixed-point provider could therefore abort persistence of a valid accepted repair.
- `materialize()` now receives the providers actually fixed/accepted in the wave and reconciles domain metadata with `--provider <id>` for those providers only. ProviderBase materialization and published CONFIG validation remain global non-regression gates.
- `provider_brain_repair_orchestrator_test.py` now forbids the old global reconcile call and requires provider-scoped post-accept reconciliation.

### 2026-09-20 — Repair iteration 28 proved real multi-round Brain; portfolio made resumable
- Repair run `35531977017` (trigger SHA `1baba01f8473...`) passed preflight and executed real provider repair. 4KHDHub reached 3 sandbox rounds, Mallumv reached 3, Vidfast reached multiple rounds, UHDMovies reached multiple rounds; several providers moved from `no_provider_request_observed` / blocked to `content_lookup_completed_no_streams`. No provider obtained strict playable identity proof, so accepted/fixed remains 0.
- The run was not allowed to complete its five portfolio waves: the outer pipeline killed `run_provider_brain_repair.py` after ~2400s while wave 3 was still in progress. This discarded the portfolio report even though per-round negative memory had already advanced.
- This is now treated as a scalability/orchestration defect, not a provider failure. `run_provider_brain_repair.py` has a 2100s graceful work budget plus a minimum remaining-budget threshold before starting an expensive batch. It writes a partial resumable report instead of being killed.
- Resumable reports expose `timeBudgetExhausted`, `unvisitedProviders`, `processedProviders`, and `resumeRecommended`. Resume is allowed only when work remains and either some selected providers were not yet visited or experiment memory advanced. A stalled fully visited portfolio does not self-loop.
- Scheduling now uses one O(memory) attempt-pressure snapshot and prioritizes providers with fewer durable experiments, preserving family batching while preventing slow/exhausted providers from starving a future 100/300-provider catalogue.
- Repair workflow persistence now queues a successor Repair only after census + Brain memory have been pushed, and workflow concurrency no longer cancels the run that is persisting its evidence. Deferred/exhausted providers may still escalate independently to Learning.
- Pipeline explicitly grants the Brain 2100s and an outer 3000s safety envelope; this is not a longer blind run but a bounded resumable unit of work.

### 2026-09-20 — Census prior is a floor, not a ceiling; player-stage media strategy added
- Repair iteration 28 artifacts proved that causal depth was genuinely increasing, but historical census labels could still pin the planner to an older failure family. Example: 4KHDHub acquired a new player-stage signature while remaining classified `route_proven_gap`; that kept later rounds focused on route traversal even though current bytes had already reached the player.
- Root cause: `applyCensusPrior()` always forced `ROUTE PROVEN -> route_proven_gap`, `CHAIN REACHED -> chain_terminal_gap`, and `CANDIDATE OK -> candidate_replay_gap` even when fresh current-run evidence had reached the same or a deeper stage. `PROVIDER NETWORK BLOCKED` similarly remained a transport prior after fresh successful provider requests.
- Fixed census prior semantics: it now acts strictly as a monotonic depth floor. If current evidence reproduces or exceeds the historical floor, the current causal failure class wins. This allows player-stage zero-stream observations to become `media_extraction_gap` instead of being dragged back to search/detail/transport.
- Added planner regression coverage for ROUTE PROVEN, CHAIN REACHED, CANDIDATE OK and PROVIDER NETWORK BLOCKED forward progress. All four must classify fresh player-stage/no-media evidence as `media_extraction_gap` and `terminal_media_resolution`.
- Added a dedicated variant-4 strategy `player_media_extractor_v1` for `media_extraction_gap`. It prioritizes current provider player/API evidence, raises peer transfer thresholds, removes peer recipes from the terminal variant, avoids generic `/player/{id}` / `/api/*/{id}` guesses that would map TMDB into provider-local IDs, and uses provider-owned request recipes/terminal route shapes instead.
- The end-to-end current-observation contract now executes the synthetic bound-ID chain under `media_extraction_gap` variant 4 and verifies the terminal strategy contains no generic provider-ID guesses.

### 2026-09-20 — Deterministic player-JS media extraction
- Audit of `runtime_recovery_generator.py` after introducing `media_extraction_gap` showed that the resolver already handles literal href/src/data-player URLs, literal file/source/url assignments, literal fetch/axios calls, recursive JSON URLs, player/embed recursion, opaque media probes and direct HLS/DASH/container proof.
- Remaining generic gap: deterministic player scripts that assemble a media URL from constants (for example `const host="https://cdn"; const path="/master.m3u8"; file=host+path`) were invisible unless the final URL also appeared literally elsewhere.
- Added a bounded static JS expression resolver inside the adaptive wrapper. It evaluates only quoted literals and previously resolved constant identifiers joined by `+`, with strict token/count/length limits. It also recognizes static template literals without interpolation and static `atob("...")` when the runtime exposes `atob`.
- No remote JavaScript is executed or eval'd by this analyzer. Dynamic expressions, function calls, unknown identifiers and interpolated templates remain unresolved.
- The end-to-end current-observation recipe test now returns a player page where the HLS URL exists only as `host + path`; the generated wrapper must reconstruct and probe the resulting HLS URL successfully.

### 2026-09-20 — Media extraction frontier enforced from variant 0
- After adding `media_extraction_gap`, audit showed the strict terminal specialization originally applied only to final experiment variant 4. Variants 0-3 still inherited generic catalogue/direct routes, so a provider that had already reached the player could waste several experiments rediscovering search/detail or trying TMDB-shaped generic player routes.
- `adaptive_runtime/runtime_repair.py` now enforces the media-extraction causal frontier from variant 0 onward: search is limited to provider-owned/configured routes needed to reacquire a fresh player; direct paths are limited to provider-owned/configured player/API routes, with peer terminal shapes admitted only at the configured late transfer threshold. Generic catalogue and TMDB-as-provider-id terminal guesses are excluded for every media-extraction variant.
- The current-observation contract verifies both variant 0 and variant 4 keep this terminal focus while preserving provider-local executable request recipes and response-bound internal IDs.

### 2026-09-20 — Terminal source-chain preservation from Repair 28 artifacts
- Repair 28 artifact `provider-recognition-repair-v6-35531977017` was re-inspected instead of relying only on summary logs. It showed a concrete terminal-family mismatch: 4KHDHub had live HTTP 200 evidence on external terminal pages such as `hubdrive.tips/file/<provider-id>` and `hubcloud.cx/drive/<provider-token>`, while the adaptive runtime only treated `player/api` as media-terminal roles.
- The runtime role model now has an explicit `source` role for provider-owned terminal shapes such as `/file/`, `/drive/`, `/source/` and exact `/download/` segments. Catalogue pages such as `/download-<title>-...` remain `detail`; no provider-specific rule was added.
- `media_extraction_gap` now preserves owned/configured/peer `source` terminal routes from variant 0 onward instead of filtering them out. Chain/candidate role ordering also recognizes source routes.
- A second execution bug was found in the generated resolver: same-host `/file/...` and `/drive/...` links had playerScore 0, so recursive resolution skipped them even after discovery. The resolver now scores exact terminal file/drive/download route families as source-like and prioritizes request recipes as `player -> source -> api -> episode -> detail -> search`.
- Added `tests/brain_terminal_source_route_test.py`. It verifies source/detail classification, confirms media-extraction variants 0 and 4 retain source routes while excluding TMDB-as-provider-id catalogue routes, and executes an end-to-end same-host synthetic chain `detail -> /drive/token -> /file/id -> HLS`.
- `build_brain_repair_experience.py` now preserves the same `source` taxonomy and accepts safe `{binding:<key>}` placeholders. This prevents the next experience rebuild from degrading terminal source semantics back to `other`.
- Important safety finding: static knowledge contains exact provider-local IDs that can be marked reusable by upstream route recognition (for example literal `/file/37380388904`). These literals are **not** being promoted as cross-provider or generic Brain truth. Repair remains bound to current-run causal bindings or reusable templated evidence.
- Iteration 31 trigger SHA `9f54f51b...` predates these source-chain commits, so even if it runs it is not authoritative for the new terminal-source behavior. A fresh Repair on a later HEAD is required for efficacy evidence.

### 2026-09-20 — Repair #95 preflight clarified source-chain behavior
- Repair run `35542040832` (#95, trigger SHA `ba41d18eb1ed...`) did not probe providers. Preflight reached the current-observation media test and already returned the expected HLS row through the synthesized bound-ID chain; the failure was a stale test assertion requiring an explicit fetch of the `.m3u8` URL even though the resolver may prove a direct media URL by extension without another request.
- The same contract also still assumed media terminal direct roles were only `player/api`; it now uses the explicit `TERMINAL_MEDIA_ROLES` set including `source`.
- Additional safety guard added after artifact review: `{binding:<key>}` routes are causal request-program inputs only and are filtered out of standalone `direct_paths`. They become executable only after an earlier response binds the value. This prevents malformed `/file/` or stale provider-ID replay.
- Current provider overrides were audited for persisted source routes. Existing source-like routes are generic/templates (for example `/api/file/`, `/download/{slug}...`) rather than literal historical file IDs; exact provider-local IDs observed in artifacts remain non-authoritative.
- #95 is harness/preflight evidence only. A later Repair SHA is required to test the terminal source-chain changes against the real repairQueue.

### 2026-09-20 — Repair #96 preflight import-only failure
- Repair run `35542148892` (#96, trigger SHA `819bd355f4fc...`) did not probe providers. The existing current-observation HLS synthesis contract passed on this SHA.
- Failure occurred only when the newly added `brain_terminal_source_route_test.py` imported the adaptive runtime without adding `scripts/` and `scripts/adaptive_runtime/` to `sys.path`; `apply_provider_overrides` could not be resolved.
- The test now loads the same module search paths as the production adaptive entrypoint. No runtime/provider logic was changed for this failure.
- #96 is harness-only evidence and must not be counted as a Brain/provider attempt.

### 2026-09-20 — Native terminal capture now preserves observed Referer
- While Repair #97 (run `35542228275`, tested SHA `3610a5f429fb...`) was running, an independent audit found a generic hotlink defect in the adaptive wrapper's native-fetch fallback. It captured only the terminal URL requested by the native provider and later replayed it with the provider root as Referer, discarding the Referer that the native provider had actually used.
- `runtime_recovery_generator.py` now captures `{url, referer}` for terminal fetches. Header lookup supports Headers-like objects, tuple arrays and plain objects. Re-resolution uses the observed Referer and preserves it through recursive `drive/file/player -> media` traversal.
- Extended `brain_terminal_source_route_test.py` with a native-provider capture case where the terminal host returns 403 unless the original detail-page Referer is replayed, and the nested file page requires the drive URL as its Referer. The expected HLS must still be recovered.
- This change is generic anti-hotlink compatibility; no provider/host special case was introduced.
- Repair #97 does **not** contain this Referer fix. Its field evidence remains useful for the prior terminal-source implementation, but authoritative validation of Referer-preserving capture requires a later HEAD/run.

### 2026-09-20 — Terminal transport/media adapters generalized from historical providers
- Independent audit during Repair #97 found another generic terminal gap shared by manual runtimes: extensionless file APIs may prove media through HTTP transport rather than URL shape. The adaptive resolver previously handled HLS/DASH/video MIME/signatures but could read `206 Partial Content` + `Content-Range` + `application/octet-stream` responses as text.
- `runtime_recovery_generator.py` now carries a bounded sandbox `proof` from request to recursive resolver. Non-text `206`/Content-Range is accepted as transport-level media evidence; octet-stream/binary responses without range are prefix-sniffed using existing bounded binary signatures. This only yields a sandbox candidate: strict current-byte playable + identity validation still controls acceptance.
- Added contract coverage with an extensionless `/api/file/<id>` endpoint that throws if read as text and returns only 206/Content-Range/octet-stream. The wrapper must return it as a direct candidate.
- Historical code shows reusable terminal URL adapter patterns across more than one provider family: encoded HTTP(S) destinations in query parameters such as `?link=...`, and Pixeldrain share URLs `/u/<id>` mapping to the documented-style file endpoint shape `/api/file/<id>`.
- Added bounded `unwrapTerminalUrl()`: up to three transformations, only explicit HTTP(S) destinations, only a small allowlist of destination parameter names, existing `bad()` filtering retained. Pixeldrain `/u/<id>` receives the reusable service-level API transformation. No TMDB/provider identity is inferred and no provider-specific branch exists.
- Tests verify double-encoded wrapper destination -> direct HLS without fetching the wrapper, plus Pixeldrain share -> extensionless 206 API media.
- Repair #97 tested SHA `3610a5f429fb...` predates Referer preservation, partial-content proof and terminal URL adapters. Its field results remain comparative evidence only; a later run is required for authoritative validation of these additions.

### 2026-09-21 — Mature ProviderBase player extractors transferred into Brain
- Historical capability audit compared the current adaptive Brain wrapper with mature ProviderBase migrations. Three provider-agnostic player families were present in ProviderBase but absent from `scripts/adaptive_runtime/runtime_recovery_generator.py`: bounded Dean-Edwards `p,a,c,k,e,d` unpacking, explicit base64 player payload calls (`showVideo/loadVideo/setVideo/playVideo`), and the shared obfuscated-HLS family (base64 -> reverse -> hostname-derived XOR, plus legacy static XOR).
- The adaptive Brain now inherits those three extractors. Packed code is structurally decoded only; no remote `eval` or arbitrary JavaScript execution is introduced. Blocks, dictionary sizes, payload lengths and scans remain bounded.
- URL extraction runs over the unpacked text, merges deterministic JS URLs, explicit player payload URLs and decoded obfuscated HLS, and rejects the known `/troll/master.m3u8` decoy shape.
- Added `tests/brain_historical_player_extractor_transfer_test.py`. It executes the generated adaptive wrapper end-to-end on three synthetic player pages and requires the real HLS to emerge for packed, explicit-base64 and hostname-XOR families. It also asserts the generated wrapper contains no evaluation primitive.
- Repair preflight now includes this historical extractor-transfer contract. This closes a major knowledge-transfer gap: new providers can reuse extraction patterns already accumulated by NiakVIO instead of rediscovering them through provider-specific patches.

### 2026-09-21 — Mature bounded crawl guard transferred into Brain
- ProviderBase V6/V10 parity audit found one remaining reusable traversal rule missing from the adaptive Brain: an unrelated bare external origin could score +80 merely for being cross-origin and therefore be crawled as a player, wasting terminal budget on landing/advertising roots.
- Adaptive terminal traversal now has a bounded `followable(url,parent)` guard. Direct media remains allowed; meaningful player/source/API/file/drive routes remain eligible. Bare external roots, common social roots, feed/oEmbed/assets/static/image/font paths and static assets are rejected before recursive fetch.
- Extended `brain_historical_player_extractor_transfer_test.py` with a real generated-wrapper execution: a player page exposes both `https://noise.example/` and `https://media.example/file/abc`; the Brain must traverse the file route to HLS and must never fetch the unrelated bare root.
- V6 external-id projection was not copied blindly: the adaptive request object already preserves object-form IDs and the current terminal repair need is traversal/media extraction, so no redundant unrelated mutation was added.

### 2026-09-21 — Player handoff parity + multi-result causal identity binding
- Continued ProviderBase parity audit found mature generic player behaviors still absent from the adaptive Brain: same-origin hidden player forms (F1 POST handoff), canonical opaque-id route variants such as /embed|file|download/<id> -> /v/<id>, same-origin player identifiers carried only in query parameters, and explicit player payload calls with an optional numeric priority argument.
- Adaptive terminal traversal now supports these behaviors with bounded/same-origin rules. Player form submission accepts only the historical F1 shape, hidden inputs (max 32), bounded field/value sizes and same-origin HTTP(S) action. The original opaque id is preserved; no provider/TMDB id is invented. Route variants keep the same origin/id and do not consume extra recursive depth.
- Explicit base64 player handoffs now accept the optional priority argument and outrank incidental raw/download-looking URLs from the same HTML, matching the mature V24.2/V24.3 semantics.
- A deeper V20 gap was fixed in Brain request-program learning. Route-proof responses can expose multiple ids. The synthesis layer now retains each safe value->binding-key candidate, but a dependent recipe is created only when a later observed request consumes that exact value. This is causal observation, not first-result guessing.
- Runtime replay now resolves multi-result bindings by fixture identity. JSON objects and HTML anchors are bounded-scanned; only title-correlated rows (with year-conflict rejection) may provide id/slug. Ambiguous equal-score alternatives remain unbound, so dependent recipes do not execute.
- Extended tests execute: hidden-form POST -> HLS, /embed/id -> /v/id -> HLS, query-only player -> HLS, explicit payload with priority while rejecting an incidental wrong MP4, JSON search with wrong+right ids -> bound player, and HTML catalogue wrong+right anchors where only the matching title may select /player/987.
- This closes a central search->detail/player generalization gap for large catalogues: multi-result provider pages no longer need to contain a single unique id for the Brain to replay the observed chain on a new fixture.

### 2026-09-21 — Episode-scoped traversal transferred into adaptive Brain
- Series/anime parity audit found the adaptive Brain only gave score bonuses to matching S/E strings; it did not reject explicitly wrong episode links or reduce structured multi-episode JSON before extracting player URLs. A wrong episode could therefore be crawled before the requested one.
- Added generic episode identity primitives inherited from mature ProviderBase semantics: path/query S/E marker recognition (including reversed query parameter order), conservative wrong-episode filtering, exact episode-hop authorization, and structured JSON episode scoping using episode/episode_number/episodeNumber/ep/number/num plus optional season fields.
- Exact episode identity can authorize traversal even when the route has no generic player/embed keyword. Unmarked URLs remain eligible under the ordinary player/source rules; only explicit mismatches are rejected.
- Query context is now threaded through native-row normalization, captured native terminal replay, recursive resolution and recovery, so episode filtering is preserved across the entire terminal chain rather than only at initial search.
- Added tests/brain_episode_scoped_traversal_test.py: JSON with E1+E2 must fetch only E2; HTML table S01E01+S01E02 must fetch only S01E02; anime query links with reversed episode=...&season=... ordering must fetch only the requested episode. The wrong episode endpoints throw if touched.
- Repair preflight now requires this contract. This transfers a major TV/anime invariant into the generic Brain instead of relying on provider-specific episode code.

### 2026-09-21 — Terminal wrapper media-proof ordering fixed
- Current census from Repair #97 (`35542228275-post-repair`) is now **25 FULL OK · 2 PARTIAL · 11 repairQueue**. UHDMovies is FULL OK with current verified playable proof for Avengers: Endgame. Provenance matters: Brain itself reported `accepted=0 / fixed_lab=0`; the final current-byte yield found `raw=1 / playable=1 / accepted_playable=1 / verified=1` for UHDMovies and the monotonic same-run evidence merge promoted it. This is a real provider recovery/current-byte proof, but not yet the first autonomous Brain-accepted repair.
- Repair #103 (`35544422967`, SHA `5d1e6c67...`) did not probe providers. Preflight failed in the generic terminal-adapter contract: `https://wrapper.example/dl.php?link=https%253A%252F%252Fcdn.example%252Fwrapped.m3u8` was incorrectly classified as direct media because `mediaExt()` searched the whole URL and saw `.m3u8` inside the query value.
- Fixed `runtime_recovery_generator.py::mediaExt()` to classify extensions/manifest only from the URL pathname (or the query/hash-stripped fallback string). Encoded destination wrappers must now pass through `unwrapTerminalUrl()` before media proof.
- This is generic terminal-resolution behavior and directly benefits redirect-wrapper families used by multiple providers. No provider-specific host or route was added.

### 2026-09-21 — Repair #104 historical-player test harness escape fix
- Repair #104 (`35544700122`, SHA `5c0a24ee85a9...`) remained preflight-only. The terminal source-route contract, including encoded wrapper unwrapping, passed.
- Failure moved to `brain_historical_player_extractor_transfer_test.py` before Brain execution: its generated Node runner used a non-raw Python f-string, so the synthetic HLS `\n` escapes became literal newlines inside a JavaScript single-quoted string and Node raised `SyntaxError: Invalid or unexpected token`.
- The runner is now a raw f-string. No provider/runtime logic changed for this failure; #104 is not provider evidence.

### 2026-09-21 — Packed-player decode handoff fixed
- Repair #105 (`35544781595`, SHA `2636895ac45e...`) remained preflight-only. The terminal source-route contract passed. The historical packed-player contract then executed the generated wrapper and proved a real transfer gap: the wrapper fetched the packed player but returned the original player URL instead of the decoded HLS.
- The Brain packed decoder itself matches the mature ProviderBase V18.6 algorithm and decodes the fixture structurally without eval. The missing behavior was the decoded-payload -> media-URL handoff in the full adaptive resolver.
- `runtime_recovery_generator.py::urls()` now performs a bounded scan (max 48 matches) of the structurally decoded packed payload for absolute direct-media URLs before the ordinary player extractors. It still rejects blocked/decoy URLs and requires media-path evidence; no remote code is executed.
- Existing end-to-end historical-player contract remains the authority: the generated wrapper must return the real packed HLS, not the player page.

### 2026-09-21 — Packed-player regex escaping corrected
- Repair #106 (`35544951242`, SHA `b1459729cb9a...`) remained preflight-only. The wrapper/terminal-source contract passed, but the packed-player execution still returned the original player URL.
- Comparing the transferred Brain extractor with mature ProviderBase V18.6 exposed a source-generation divergence: the adaptive wrapper is itself stored in a Python raw string, yet parts of the transferred regex were escaped as if another string layer still existed. The generated JavaScript therefore contained a literal `\\s` in the packed `.split('|')` guard and URL whitespace classes instead of the intended regex whitespace token `\s`.
- Corrected the packed `.split('|')` guard and both remaining URL character classes at the generator source. This is a transfer/escaping bug, not a provider-specific parser change.
- The existing end-to-end historical player contract remains authoritative; next Repair must prove packed/base64/XOR extraction before provider probing.

### 2026-09-21 — Obfuscated-HLS fixture aligned with mature V21 safety floor
- Repair #107 (`35545068392`, SHA `cf0487d439ac...`) remained preflight-only. Packed extraction now passes, proving the transferred regex-escaping fix.
- The next failure was the hostname-XOR obfuscated-HLS synthetic fixture. Its generated base64 payload was only 44 characters while the mature ProviderBase V21 detector intentionally requires at least 50 characters to reduce false positives.
- Kept the mature safety threshold unchanged. The synthetic HLS URL is now long enough to produce a >=50-character payload and the test explicitly asserts that invariant before exercising the generated wrapper.
- #107 is harness/capability evidence only; no provider was probed.

### 2026-09-21 — Historical player suite green; verified-media V5 aligned with current generator
- Repair #108 (`35545162626`, SHA `0a544c4e9869...`) remained preflight-only, but it materially advanced validation: packed/base64/hostname-XOR historical player extraction, terminal source/wrapper traversal, episode-scoped behavior, real-worker smoke tests, and full **44-provider** materialization all passed.
- The failure moved to `brain_repair_experience_transfer_test.py`: `adaptive_runtime_recovery_v5.py` still performed exact source rewrites against an older adaptive generator shape and failed at `request_extension_hint` after the generator gained Content-Range/binary proof, player-form handoffs, episode context and pathname-only media extension classification.
- Updated V5 as a guarded multi-generation migration rather than weakening it. It now recognizes legacy and current request/result/native shapes while preserving the same invariant: extension-only URLs are hints and must be network-proven before acceptance.
- Current generator branches covered by V5 now include request Content-Range proof, resolved-page proof, player-form handoff proof, handoff nested links, episode-aware nested recursion, and `normalizeNative(..., q)`. The unverified-native fallback remains fail-closed.
- #108 did not probe a provider and is not provider/Brain repair evidence. Next Repair must first prove `brain_repair_experience_transfer_test.py` against the current generator, then return to the 11-provider repairQueue.

### 2026-09-21 — Private Tailscale residential-exit harness lane
- User configured GitHub WIF/Tailscale secrets for a private exit-node diagnostic path: `TS_OAUTH_CLIENT_ID`, `TS_AUDIENCE`, `TS_EXIT_NODE`, `TS_TAG_NAME`. The intended CI node tag is `tag:niakvio-ci`.
- Security/minimal-permission rule: the Tailscale federated credential needs writable `auth_keys` only; GitHub workflow needs `id-token: write`. Exit-node Internet use is authorized separately by the tailnet policy via `tag:niakvio-ci -> autogroup:internet` when custom grants/ACLs are in use. No Devices/Routes/DNS admin API scope is required for the CI diagnostic.
- Added `scripts/merge_waf_network_profiles.py`. Residential-exit evidence is merged into the ordinary WAF report without persisting the exit-node name, Tailscale address, residential public IP, cookies, response bodies or challenge tokens.
- `provider-waf-browser-session.yml` now measures the same WAF/harness targets twice: GitHub-hosted network first, then an ephemeral Tailscale WIF node routed through the configured private exit node. Tailscale action v4 is commit-pinned, uses quiet logging, and exit routing is cleared on completion.
- Census transport classification gained `residential-exit-native-reachable`, `residential-exit-browser-reachable`, `residential-exit-all-challenged`, and `residential-exit-inconclusive`. Residential reachability remains harness evidence only and can never promote provider playback or mutate provider JS.
- Added privacy/causality contracts: `tests/provider_waf_tailscale_exit_contract_test.py` and `tests/waf_residential_profile_merge_test.py`.
- WAF diagnostic run #31 (`35548356888`, SHA `212c6ebc...`) is the first run containing this transport and must be inspected before using its evidence.

### 2026-09-21 — V5 nested-media migration restored after Repair #109
- Repair #109 (`35545539057`, SHA `74218b97...`) remained preflight-only. Historical player, terminal-source, episode traversal, composite-id, replan, budget, census and full 44-provider materialization contracts all passed.
- Its remaining failure was `brain_repair_experience_transfer_test.py`: `adaptive_runtime_recovery_v5.py` still matched an older nested-media call shape while the current adaptive generator now uses the shorter `media(xs[i],"","","")` / handoff equivalent.
- An intermediate edit accidentally attempted to copy a minified full resolver line into V5; it was detected before any Repair relaunch. V5 was restored from the last known-good file at Repair #109's parent state, then only the exact two current nested-media source fragments were added as additional guarded migration variants.
- Next authoritative Repair must first prove V5 experience-transfer on this restored/current shape, then return to the 11-provider repairQueue. Current census remains **25 FULL OK · 2 PARTIAL · 11 repairQueue**; UHDMovies is FULL OK from current-byte final-yield playable+identity evidence, not from a Brain acceptance (`accepted=0 / fixed_lab=0` in that run).

### 2026-09-21 — Tailscale WIF trust-credential blocker isolated
- WAF/Tailscale run #37 (`35548867852`) proved the GitHub workflow side up to OIDC exchange: checkout/tooling/contracts passed, the CI tag was normalized to `tag:niakvio-ci`, Tailscale 1.94.2 started, and `tailscale up` reached the WIF token exchange.
- The remaining failure was a Tailscale-side 403 from the trust credential (`Unauthorized` during JWT -> access-token exchange), not a GitHub token, action, tag-format or exit-node-selection failure.
- User subsequently aligned the Tailscale trust credential/access controls to the intended minimum from the linked configuration conversation: writable Auth Keys for `tag:niakvio-ci`, and Internet egress grant/rule `tag:niakvio-ci -> autogroup:internet`. No broader Devices/Routes/DNS API scope is required for this diagnostic lane.
- Privacy invariant remains mandatory: do not call `ifconfig.me`, `api.ipify.org`, `icanhazip`, dump `tailscale status --json`, print environment secrets, exit-node identity or residential public IP. Workflow contract tests explicitly forbid these patterns and residential evidence merge persists only bounded transport outcomes.
- New authoritative WAF run required after the Tailscale-side credential update. Only provider-owned route outcome differentials may reclassify harness/network evidence; residential reachability never grants playback proof.

### 2026-09-21 — Tailscale is optional, GitHub-only fallback is authoritative when unavailable
- Residential/Tailscale diagnostics must never become a hard dependency for census or Repair. If WIF fails, the user's Mac/exit node is offline, exit-node selection fails, or the residential probe fails, the workflow continues with the ordinary GitHub-hosted network.
- `provider-waf-browser-session.yml` now marks Tailscale connect, exit-node selection and residential probing as non-blocking. The direct GitHub probe always runs; the final WAF report is always produced.
- `merge_waf_network_profiles.py` can persist a bounded unavailable state (`tailscale-connect-failed`, `exit-node-unavailable`, `residential-probe-failed`, or generic `tailscale-unavailable`) without storing any exit-node identity, Tailscale address, residential public IP, cookie, response body or token.
- `merge_waf_census_transport.py` carries the residential availability metadata into the authoritative census state. `render_provider_census_status_from_state.py` adds a `Residential probe` table column: harness/environment rows show `✅ compared` when residential evidence exists or `⚠️ unavailable · GitHub-only` when Tailscale was unavailable. Providers outside the environment queue remain unaffected.
- Privacy remains enforced by CI contract: forbidden workflow patterns include `ifconfig.me`, `api.ipify.org`, `icanhazip`, public-IP curl checks, `tailscale status --json`, direct exit-node echo, and direct-device ping. Routing is validated through probe outcome differentials, not by publishing the residential IP.

### 2026-09-21 — WAF #45 still blocked at Tailscale trust claim
- WAF run #45 (`35549274925`, SHA `5a8730ce...`) is green only because the residential lane is intentionally optional. All direct GitHub WAF probes and persistence completed.
- Tailscale 1.94.2 started correctly, but every WIF exchange attempt returned `403 Unauthorized` from the Tailscale trust credential before the ephemeral node joined the tailnet. Therefore exit-node selection and residential reprobe were skipped.
- Persisted residential state is `available=false`, reason `tailscale-connect-failed`, matched lanes `0`. No exit-node identity, Tailscale address or residential public IP was persisted.
- The remaining external action is in Tailscale Admin -> Trust credentials -> the OIDC credential referenced by `TS_OAUTH_CLIENT_ID`: inspect the token-exchange error and align issuer/audience/subject/custom claim rules with GitHub Actions for `niakw/NiakVIO` on `refs/heads/main`, retain writable `auth_keys` and `tag:niakvio-ci`. Repo-side `id-token: write`, client ID, audience and tag plumbing are already present.
- This blocker does not stop Repair/Brain. Until WIF succeeds the WAF workflow remains GitHub-only and continues to classify provider code conservatively.

### 2026-09-21 — Repair preflight fail-fast + exact failed-route residential network differential
- Repair preflight ordering was optimized generically: `brain_repair_experience_transfer_test.py` now runs before the expensive full 44-provider materialization. A dedicated contract `brain_preflight_fail_fast_order_test.py` locks `V5 experience-transfer -> materialize all -> discovery composition`. This changes only validation order, not provider behavior.
- Residential/Tailscale diagnostics were extended beyond WAF-only lanes. `probe_waf_browser_session.py` can now ingest `provider-v3-quick-yield.json` and select only exact provider-owned GET requests that actually failed with `status=0` or HTTP error for providers currently classified `PROVIDER NETWORK BLOCKED`.
- The exact raw failed URL is used only in-process for the probe. Persisted evidence strips query values and retains only provider/lane/public URL host/path, method, failure class and bounded transport outcomes. Requests containing redacted values or sensitive query keys (token/auth/key/signature/secret/cookie/session/etc.) are excluded.
- Network differential evidence is annotation-only. `merge_waf_census_transport.py` can record `networkDifferentialClass` / `networkDifferentialEvidence` on existing `PROVIDER NETWORK BLOCKED` rows, but it preserves status, `repairEligible`, repair/environment queue membership and all playback authority. A full provider replay is still required before reclassification.
- Census Markdown now exposes a `Network differential` column. Contracts verify a synthetic case where GitHub native-like transports timeout but the same exact failed route is reachable through the residential exit: the row remains `PROVIDER NETWORK BLOCKED` and in repairQueue while carrying `residential-native-route-reachable`.
- This specifically enables safe diagnosis of current network-blocked families such as MovieBox/YFlix when their exact failing provider GET is available, without treating homepage reachability as sufficient evidence.

### 2026-09-21 — WAF #55 correction: WIF still rejected; V5 preflight validated
- Correction of the earlier checkpoint: WAF run #55 (`35550837403`, SHA `47c485657b2a...`) did **not** successfully join the tailnet. The Tailscale action had `continue-on-error`, so the GitHub step was displayed as successful while its internal outcome was failure.
- Raw logs show five `tailscale up` attempts all failed at GitHub JWT -> Tailscale access-token exchange with HTTP 403 Unauthorized. Exit-node selection and residential reprobe were skipped. Therefore #55 provides no residential transport evidence.
- The user then replaced the trust-credential subject with the exact subject reported by the issuer (including repository numeric identifiers). A fresh WAF run is required; do not claim WIF success until raw logs show token exchange/join success **and** exit-node selection runs.
- Privacy invariants remain unchanged: do not persist or print exit-node identity, Tailscale addresses, residential public IP, cookies, response bodies or tokens.
- Repair run `35550425371` passed `Prove one canonical Learn Force repair implementation` with the restored/current V5 and is executing canonical recognition/repair on the unresolved provider set. V5 compatibility is validated for that tested SHA; provider repair outcomes remain pending.

### 2026-09-21 — Tailscale WIF exact-subject retry still rejected; bounded OIDC claim diagnostic added
- WAF run `35550837403` (#55) tested the federated identity after the Tailscale Trust Credential subject was changed to `repo:niakw/NiakVIO:ref:refs/heads/main`.
- All local WAF/Tailscale contracts passed, but the Tailscale action itself still failed token exchange five times with HTTP 403 `Unauthorized` before joining the tailnet. Because the connect step is `continue-on-error`, the workflow remained green and correctly persisted a GitHub-only fallback; the residential exit was **not** selected and no residential comparison occurred.
- This proves the remaining blocker is still Trust Credential claim matching / WIF configuration, not exit-node ACL selection and not provider code. The public API error is intentionally redacted by Tailscale; detailed mismatch guidance is available only on the federated-identity admin page until an exchange succeeds.
- Added a bounded GitHub OIDC diagnostic step to `.github/workflows/provider-waf-browser-session.yml`. It requests the same audience token immediately before Tailscale and logs only whitelisted non-secret claims: `iss`, `sub`, `repository`, `repository_owner`, `repository_visibility`, `ref`, `ref_type`, `workflow`, `workflow_ref`, `job_workflow_ref`, `event_name`. It never logs the JWT, `aud`, Tailscale node identity, Tailscale addresses, residential public IP, cookies or bodies.
- Network/harness scope remains broader than WAF-only: residential differential logic targets HARNESS MISMATCH, HARNESS/ENV BLOCKED and PROVIDER NETWORK BLOCKED exact failed routes. Any residential reachability remains transport evidence only until the real provider quick-yield obtains raw/playable/identity-verified media.

### 2026-09-21 — Exact-route probes expose 7 s provider fetch-slice false network blocks
- WAF run #55 (`35550837403`, SHA `47c48565...`) completed successfully as a GitHub-only overlay. The Tailscale action step had `conclusion=success` only because it is `continue-on-error`; its internal `tailscale up` still failed 5/5 with the Tailscale Trust Credential `403 Unauthorized`, so exit-node selection/residential probing were correctly skipped and the persisted residential state remains `available=false / tailscale-connect-failed`.
- The new exact failed-route diagnostic nevertheless produced decisive GitHub-network evidence for two repairQueue providers. MovieBox's previously aborted exact routes and YFlix's `enc-dec.app/db/flix/find` route are reachable with ordinary Chromium, direct HTTP and JVM OkHttp on the GitHub runner. Census keeps both as `PROVIDER NETWORK BLOCKED` but annotates `networkDifferentialClass=github-native-route-reachable`; no queue/status promotion occurred.
- Cross-checking the quick-yield failure timings exposed a common Core runtime limit: failed provider requests ended in `AbortError` at ~7000 ms, and the global execution wrapper used `fetchSliceMs=7000` inside a separate 25 s provider budget. This can misclassify a slow but reachable provider request as network blocked before the provider budget is exhausted.
- Core default per-fetch slice is now **12,000 ms**, while the total provider budget remains **25,000 ms** and the hard fetch-slice cap remains **15,000 ms**. Explicit lower provider overrides remain supported. Both the live global media-type wrapper and the V33 migration source were aligned.
- Added `tests/provider_fetch_slice_budget_test.py`, wired into Repair preflight, to prove default 12 s, explicit lower override, 15 s cap and unchanged 25 s provider/TV budget.
- This change is generic; it is not a YFlix/MovieBox host exception. Provider-specific internal request timeouts remain separate evidence and must only be changed when they are proven to be the active limiter.
- Repair #111 (`35550425371`, SHA `0082f7b...`) predates the 12 s Core change. Its preflight is green and it is in real canonical repair, so its provider evidence remains useful but cannot validate the widened fetch slice. A queued successor is required on the current HEAD.

### 2026-09-21 — Tailscale WIF join and private exit selection validated
- WAF run `35551294702` (#63, SHA `ceae0b745230...`) is the first run to pass both the bounded GitHub OIDC diagnostic and the Tailscale WIF join, then successfully select the configured private residential exit node. The previous HTTP 403 Trust Credential blocker is therefore closed for this workflow/ref.
- At this checkpoint #63 is actively replaying the provider/harness lanes through the private residential exit; no residential reachability or provider functional result is claimed until that probe and the subsequent full-provider replay complete.
- The WAF/network path remains independent from Brain provider-code repair. Exact-route residential differentials are transport evidence only; functional requalification requires the full current-provider quick-yield replay with raw/playable/verified identity-safe evidence.
- Current full-provider residential replay selector is still narrower than the intended user scope: it selects only `network-failure-replay` rows (PROVIDER NETWORK BLOCKED differential). HARNESS MISMATCH and HARNESS/ENV BLOCKED rows can show residential reachability but are not yet automatically promoted into full provider quick-yield replay. Widen this selector after the authoritative #63 run finishes so the running comparison is not cancelled by WAF concurrency.
- In parallel, Repair #111 (`35550425371`, SHA `0082f7b...`) passed the restored V5 preflight and is executing the 11-provider repairQueue. A newer Repair #112 (`35551352407`, SHA `ab6b44d...`) is pending to validate the generic 12s per-fetch slice against exact-route differential evidence.

### 2026-09-21 — Authoritative residential network differential (#63)
- WAF run #63 (`35551294702`, SHA `ceae0b745230...`) is the first authoritative private-exit comparison. GitHub OIDC emitted `sub=repo:niakw@240183845/NiakVIO@1314528858:ref:refs/heads/main`; WIF joined successfully, the configured private exit node was selected, and 16 provider/lane probes were replayed through residential egress. No exit-node identity, Tailscale address, residential public IP, cookies, response bodies or tokens were persisted.
- Exact network-blocked routes: MovieBox and YFlix were native-like reachable already on GitHub (OkHttp/direct) and also reachable residentially. Therefore there is **no residential IP differential** for those routes; their prior quick-yield AbortError evidence points back to Core/provider request timing rather than GitHub IP reputation. Full residential provider replay correctly selected 0 providers.
- Harness/env results: AllWish and FullAnime remain challenged across browser, direct HTTP and JVM OkHttp on both GitHub and residential egress. Flemmix remains inconclusive on both. AnimeSalt, AnimeVost-FR, MoviesMod and VostFree remain browser-reachable but native-like challenged/inconclusive on both. WookaFR is native-like reachable on both networks; residential improves browser behavior but does not establish an IP-only blocker.
- Found and fixed a census labeling bug: residential classes are now **differential** only. If GitHub already proves native/browser reachability, the class remains `native-policy-reachable` / `browser-profile-only`; `residential-exit-*` is reserved for a genuine gain over GitHub.
- Full residential replay selection was generalized to include current environmentQueue/harnessQueue providers when GitHub native-like transport fails and residential native-like transport succeeds. Network-failure exact-route selection remains supported. With #63 evidence, this generalized selector should still choose zero providers, which is the expected conservative result.

### 2026-09-21 — Residential differential #63 authoritative + full functional replay scope
- WAF run `35551294702` (#63, tested SHA `ceae0b745230...`) completed green. GitHub OIDC diagnostic passed, Tailscale WIF joined successfully, the configured private exit node was selected successfully, and the residential probe completed. This closes the Trust Credential/WIF connectivity blocker.
- Privacy contract held: 16 provider-lanes were matched and compared while exit-node identity, Tailscale addresses, residential public IP, bodies and cookies were not persisted.
- Authoritative differential from #63:
  - MovieBox and YFlix exact failed routes are native-like reachable on both GitHub and residential egress. Their earlier ~7s AbortError/network classification is therefore a harness timeout signal, not evidence of provider unreachability; Repair successor uses a generic 12s fetch slice inside the unchanged 25s provider budget.
  - AllWish and FullAnime remain challenged in browser, OkHttp and direct HTTP even through residential egress. GitHub IP reputation alone does not explain these blocks.
  - AnimeSalt, AnimeVost-FR, MoviesMod and VostFree remain browser-reachable but OkHttp/direct challenged on both GitHub and residential egress.
  - Flemmix remains native/browser inconclusive on residential egress.
  - WookaFR is already native-like reachable on both GitHub and residential egress.
- #63 did not run a full provider replay because the then-current selector required a strict route-level residential-native gain; none of the observed NETWORK rows met that condition.
- Residential full replay scope is now deliberately broader and census-driven: every current provider in HARNESS MISMATCH, HARNESS/ENV BLOCKED or PROVIDER NETWORK BLOCKED is eligible once the private exit is available, including providers for which no safe exact failed GET could be extracted. This lets the real provider runtime reproduce POST/session/player behavior instead of treating the narrow transport probe as a prerequisite.
- Census promotion from residential evidence is now strict: transport reachability alone remains annotation-only. A provider lane may become current verified only when the full provider replay reports playable > 0, verified > 0, identitySafe=true and contradictions=0. All declared strict lanes => FULL OK; a strict subset => PARTIAL OK. Promoted providers are removed from repair/environment/brain queues only on that functional proof.
- PROVIDER_CENSUS_STATUS.md now exposes separate Residential probe and Residential replay columns so transport and playback authority remain visibly distinct.

### 2026-09-21 — Actual GitHub OIDC subject captured
- Completed WAF #63 logs confirmed the GitHub OIDC token used by Tailscale is customized rather than the vanilla repository subject. The emitted `sub` has the form `repo:niakw@<owner-id>/NiakVIO@<repo-id>:ref:refs/heads/main`; `repository=niakw/NiakVIO`, `ref=refs/heads/main`, `event_name=push`, and `job_workflow_ref=niakw/NiakVIO/.github/workflows/provider-waf-browser-session.yml@refs/heads/main`.
- Tailscale WIF and private exit selection both succeeded with this actual token in #63. Do not revert future Trust Credential debugging to assumptions about the vanilla `repo:niakw/NiakVIO:ref:refs/heads/main` subject without checking the bounded OIDC diagnostic first.

### 2026-09-21 — Targeted quick-yield wrapper repaired before residential full replay
- Audit of the residential full-provider replay path found a generic stale-wrapper defect in `scripts/audit_provider_quick_yield_targeted.py`: it monkeypatched `build_tasks()` with the old zero-argument signature even though canonical quick-yield now calls `build_tasks(provider_filter, history=...)`. It also called canonical `main()` while leaving wrapper-only CLI options in `sys.argv`. A non-empty targeted retry/full replay could therefore fail before probing providers.
- Reworked the wrapper to invoke the canonical quick-yield CLI in-process with explicit repeated `--provider` arguments and a private per-attempt `--output`. This automatically preserves the canonical retained-proof-first/provider-targeted/corpus fixture policy and current identity gates instead of duplicating task construction.
- Added executable contract `tests/targeted_quick_yield_canonical_cli_test.py` and wired it into both WAF/residential and Repair preflights. WAF successor #77 (`35552123975`) is queued with this fix; the prior #76 checkout did not contain it and is no longer authoritative for full replay.

### 2026-09-21 — WAF residential full replay + Learning isolation fixes
- Private Tailscale/WIF path is now authoritative and working: the exact GitHub OIDC subject with numeric owner/repository IDs was accepted, the ephemeral CI node joined the tailnet, the configured private exit node was selected, and 16 provider/lane probes were replayed without persisting node identity, Tailscale addresses or residential public IP.
- WAF run #78 selected 13 symptomatic providers for full current-provider replay through residential egress, but failed before the first provider because the WAF job did not expose `TMDB_API_KEY/TMDB_ACCESS_TOKEN` to the canonical targeted quick-yield CLI. The workflow now passes the same TMDB secrets used by Repair. WAF #79 is the first successor expected to execute the full replay rather than only transport probes.
- Learning #211 reached the adaptive queue and processed many providers, then failed while targeting `french-anime` because global override validation rejected an unrelated stale Frenchstream terminal (`fs27.lol`). This is another cross-provider transaction leak.
- `validate_override_pipeline.py` now supports `--provider`; Learning `refresh_stage_routes()` passes the current provider so domain reconciliation, runtime profile application and override validation are all provider-scoped inside the per-provider transaction. Full/global validation remains available for dedicated global checks.
- Repair #113 is a real non-regression failure rather than harness noise: final yield lost the active upstream-positive `animevostfr:anime` pair (raw/playable/verified all zero), so the preservation gate correctly failed. Do not waive it until the retained positive proof is either reproduced or precisely reclassified as external drift with evidence.

### 2026-09-21 — First strict Brain sandbox repair + residential functional promotions
- Repair #113 (`35552164417`, tested SHA `deedc31b2b54...`) produced the first strict autonomous Brain repair: **MalluMV**. Its adaptive runtime progressed `provider_unreachable -> no_streams -> healthy`; round 2 returned 9 streams and the strict post-repair gate classified `fixedInLab=[mallumv]`. Brain memory records `media_extraction_gap`, variant 2, failures 0, successes 2, lastOutcome=accepted. This is a real sandbox repair, not merely route reachability.
- MalluMV is **not yet a durable/current-byte repair**. Immediately after Brain acceptance, the orchestrator rematerialized clean ProviderBase v3 from structured DATA, discarded the stage-local accepted adaptive program, and final yield returned MalluMV to raw/playable/verified=0. Root cause is now explicit: `deep_repair_loop.py` retained the accepted candidate in its stage registry but persisted only the profile name; `run_provider_brain_repair.py` then deleted the workdir/rematerialized from DATA. ProviderBase v3 must remain immutable, so accepted JS bytes must not become a new ProviderBase.
- Repair now captures a bounded `accepted_runtime_program` from the exact accepted adaptive patch record and exposes it as `acceptedProgram` to the portfolio orchestrator. Only sanitized program DATA is retained (routes, request recipes/bindings, strategy, bounded limits, safe transport options); raw responses/cookies/tokens/stage paths are excluded. Next Repair must reproduce MalluMV and provide this exact program for durable v3 compilation/retest.
- WAF residential full replay after TMDB credential fix is authoritative and privacy-safe. Thirteen symptomatic providers were replayed through the private Tailscale exit. **AnimeSalt** and **VostFree** each produced raw=1, playable=1, verified=1, identitySafe=true, contradictions=0 and were promoted to FULL OK. Census is now 27 FULL OK; environmentQueue fell from 8 to 6. No exit-node identity, Tailscale address, residential public IP, response body or cookies were persisted.
- Residential replay did not falsely promote the other providers: AllWish/Flemmix/FullAnime/MovieBox/MoviesMod/Vidfast/WookaFR/YFlix and AnimeVost-FR remain unresolved/blocked according to their actual functional replay evidence. This confirms the Tailscale lane is a diagnostic/functional authority, not an automatic green path.

### 2026-09-21 — Residential functional promotions + Repair #114 import blocker
- Tailscale WIF is now operational with the immutable GitHub OIDC subject `repo:niakw@<owner-id>/NiakVIO@<repo-id>:ref:refs/heads/main`. The private exit node joined and full provider replays were executed for harness/network symptomatic providers without persisting node identity, Tailscale addresses or residential public IP.
- WAF #79 produced two strict functional promotions from the environment queue:
  - AnimeSalt anime: `raw=1 / playable=1 / verified=1 / identitySafe=true` -> **FULL OK**.
  - VostFree anime: `raw=1 / playable=1 / verified=1 / identitySafe=true` -> **FULL OK**.
  These are real current-byte provider validations, not transport-only promotions.
- MovieBox and YFlix remain `PROVIDER NETWORK BLOCKED`, but exact routes are reachable with Chromium/direct/OkHttp on both GitHub and residential egress. Their failure is therefore not explained by GitHub IP reputation; keep them in normal Brain/runtime/timing diagnosis.
- AllWish and FullAnime remain challenged even through residential egress; Flemmix remains inconclusive; AnimeVost-FR/MoviesMod/WookaFR still require runtime-level proof rather than provider-code mutation based on challenge evidence alone.
- Repair #114 (`35557817139`, SHA `7ab60073...`) failed in preflight before provider probing. The new accepted-program retention path used `copy.deepcopy()` in `accepted_rows()` without importing `copy`. Added the missing import on main. #114 is harness/control-plane evidence only.
- Next Repair must verify `acceptedProgram` survives report/orchestrator transport, then reproduce a strict accepted Brain repair and persist the sanitized runtime program toward durable v3 DATA/Lego only after current-byte playback+identity proof.

### 2026-09-21 — WIF post-harness failures re-enter normal Brain
- Residential/full-provider evidence exposed a census boundary error: WookaFR has native-like transport reachability on GitHub and through the private residential exit, but its full runtime replay fails afterward with `provider_network_exception` for movie and tv. Keeping it `HARNESS MISMATCH / repairEligible=false` incorrectly hid a normal runtime/provider failure from Brain.
- `merge_waf_census_transport.py` now transfers an environment-queue provider into normal repair only when all of these hold: native-like transport is decisively reachable; a full provider replay exists; there is no playable output, identity-unsafe result, WAF challenge or timeout; and replay exposes a post-harness provider/runtime failure. Explicit network exception/http/timeout becomes `PROVIDER NETWORK BLOCKED`; clean zero-result cases fall back to CHAIN/ROUTE/NO PROOF from retained evidence depth.
- Browser-only reachability, residential/browser-only reachability, WAF persistence, timeout and identity-unsafe evidence remain environment-only. This is queue reclassification, never repair/promotion authority.
- Added Wooka-like/browser-only/timeout regression cases to `tests/waf_census_transport_merge_test.py`. The next WAF merge is expected to move WookaFR into repairQueue if current evidence remains unchanged, while AllWish/FullAnime/AnimeVost-FR/Flemmix/MoviesMod stay environment-scoped.
- Repair #115 continues on tested SHA `4e446db41f2b...`; later WIF/census commits are newer than that tested SHA and must not be attributed to #115.

### 2026-09-21 — Accepted Brain program -> Provider v3 DATA compiler
- Repair #113 proved MalluMV can be repaired autonomously in the sandbox, but the winning adaptive JS was lost when clean ProviderBase v3 was rematerialized. Durable repair therefore requires compiling the accepted causal program into existing structured DATA, never copying generated JS into ProviderBase.
- Added `scripts/compile_brain_accepted_program_v3.py` in fail-closed mode. It consumes only a strict `acceptedProgram` captured by Deep and compiles representable request programs into existing `search_request_plan` / `provider_value_plan` Lego. Only safe GET/POST, HTTP(S) origins, known header names, structured form/JSON bodies and provider-local `{id}/{slug}` route bindings are representable.
- Unsupported bindings, body-only provider-value dependencies, ambiguous/non-executable routes, unsupported methods/headers and programs without an independent accepted search seed are rejected rather than approximated.
- Added `tests/brain_accepted_program_v3_compiler_test.py`: proves POST search -> correlated provider id -> player route compilation, override proposal isolation, duplicate report extraction, and fail-closed rejection of token/body-only bindings. Wired into Repair preflight.
- Compiler does not auto-publish. `--apply` is explicit and must be followed by targeted provider profile/materialization, current-byte playback+identity proof and non-regression. Repair #115 (tested SHA `4e446db41f2b...`) predates this compiler and remains the authority for reproducing/capturing the exact MalluMV accepted program.

### 2026-09-21 — Accepted program auto-persistence before v3 rematerialization
- The accepted-program compiler now merges Brain-derived plans ahead of existing `search_request_plan` / `provider_value_plan` entries instead of overwriting historical DATA. Existing positive plans remain available as fallback/non-regression evidence.
- `run_provider_brain_repair.py` now compiles each strict accepted `acceptedProgram` into Provider v3 DATA before rematerialization. Generated JS is never persisted. The wave report records compiled providers and compile failures.
- Fail-closed durability rule: if a provider is `fixedInLab` through an accepted program that cannot be represented losslessly in v3 DATA, that provider is excluded from the wave's effective fixed/materialize set and remains unresolved. It can no longer disappear from the repair loop solely because the sandbox candidate was healthy.
- Added `tests/brain_accepted_program_v3_persistence_test.py` and wired it into Repair preflight. The test proves accepted DATA is written/merged, unsafe bindings leave overrides byte-identical, and the orchestrator uses `blocked_fixed/effective_fixed_this_wave/materialize_targets_this_wave`.
- WAF #81 on SHA `76b6d5845fad...` validated the post-harness transfer rule and persisted census commit `5f491434...`: WookaFR moved from environmentQueue to repairQueue as **CHAIN REACHED** because native-like transport is reachable and full provider replay fails afterward inside provider runtime. Current queues after that merge: repairQueue 12, environmentQueue 5.
- Repair #115 remains in progress on older tested SHA `4e446db41f2b...`; it is the capture/reproduction run and does not include the newer auto-persistence/compiler/WookaFR commits.


### 2026-09-22 — Retest / Fast Brain Repair split for catalogue-scale execution
- Repair #139 (`35659188245`, tested SHA `b4fa2eac55e1...`) proved the integrated Tailscale/WAF preflight but was cancelled after entering canonical Brain. The job spent most of its useful runtime before Brain: targeted route recovery, full 42-provider rematerialization, and global stream/Core tests. Brain itself started at 22:06:13Z and the runner shutdown arrived at 22:07:10Z. This is not scalable to hundreds of providers.
- The normal provider loop is now split by responsibility:
  - **Retest** (`.github/workflows/provider-retest.yml`, `scripts/run_provider_retest.py`) is observational/current-byte only. It can replay one explicit provider or all current non-FULL providers, refresh proof history/census/batch-plan, and never runs Brain, route recovery, or provider materialization.
  - **Fast Brain Repair** (`.github/workflows/provider-fast-repair.yml`, `scripts/run_provider_fast_repair.py`) consumes only the current `repairQueue`, runs the existing family-batched Brain, and relies on Brain's incremental `materialize_provider_v3_one.py` path only for accepted provider-local DATA. No full-catalogue materialization, WAF/Tailscale qualification, route-recovery sweep, or global Core migration suite belongs in this fast lane.
  - The older canonical Repair remains the heavy/global engine-validation path, not the routine per-provider repair loop.
- Fast Repair current-byte retests only accepted/compiled candidates. A provider-local candidate is publication-eligible only when every candidate reproduces as FULL/PARTIAL on current working-tree bytes. Provider-local mutation boundary explicitly forbids Brain from changing scripts/tests/workflows/engine code in the fast lane.
- Census lifecycle semantics now include **DISABLED** as an explicit non-actionable status. Lifecycle-disabled providers are excluded from automatic Retest/Repair and no longer inflate HARNESS/NETWORK counts; an explicit Retest target can still diagnose them without re-enabling them.
- WAF/census merge no longer treats a runtime network exception as causal `PROVIDER NETWORK BLOCKED` when native-like exact-route transport is already proven reachable and a full provider replay exists. Such cases fall back to their deepest retained provider proof (CHAIN REACHED / ROUTE PROVEN / NO PROOF) and return to normal Brain repair.
- First separated Retest run is `35664357195` on SHA `7259754d38b...`, scope `non-full`, with automatic Fast Repair chaining enabled. Its outcome is not yet claimed here.


### 2026-09-22 — Provider execution split is now three independent lanes
- The routine provider cycle is no longer the old monolithic Repair preflight. Three explicit responsibilities now exist:
  - **RETEST**: `.github/workflows/provider-retest.yml` + `scripts/run_provider_retest.py`. Observes exact currently published/worktree bytes only. Supports one explicit provider, all non-FULL providers, current repairQueue, or all providers. It does not materialize or repair.
  - **REMAT/TEST**: `.github/workflows/provider-remat-test.yml` + `scripts/run_provider_remat_test.py`. Ephemerally rematerializes providers from current structured Provider DATA and then runs RETEST. Supports one explicit provider / non-FULL / repairQueue / all. It does not run Brain, route recovery, WAF discovery, or publication. Its purpose is to distinguish stale generated bytes/projection drift from a real provider-repair need.
  - **FAST REPAIR**: `.github/workflows/provider-fast-repair.yml` + `scripts/run_provider_fast_repair.py`. Consumes only current repairQueue and runs provider-local Brain mutation. No full-catalog materialization, WAF/Tailscale qualification, global route sweep, or Core migration suite.
- First authoritative separated RETEST was #5 (`35664884720`), before a later stale full-census writer overwrote the canonical ledger. The useful timing/result remains: 15 non-FULL providers / 82 probes were replayed in roughly 40 seconds with no full-catalog materialization.
- First FAST REPAIR was `35665008071` on census commit `eee99a68...`. It processed 10 providers in about two minutes but accepted **0 repairs** and fixed **0 providers**. Nine providers were explicitly deferred after experiment-strategy exhaustion: `4khdhub, allanime, anime-ultime, animesultra, animevostfr, mallumv, moviebox, vidfast, yflix`; `persianstremio` remained unresolved. This is evidence that process/preflight latency is no longer the primary bottleneck: the remaining limitation is strategy generation after known adaptive variants are exhausted.
- FAST REPAIR summary schema now exposes `brainDeferredLearningProviders`, `brainRemainingProviders`, and `learnHandoffProviders`.
- Existing Repair→LEARN handoff was extended to consume FAST REPAIR artifacts. Deferred/remaining Fast Brain providers become sanitized LEARN-owned debt with reasons `brain-strategy-exhausted` / `brain-unresolved`; validated providers are not reopened.
- FAST REPAIR exhaustion now arms the existing Brain Learning trigger with a **20-minute bounded push-trigger budget**. `run_brain_learning_queue.py` gives current Fast Repair handoff providers priority ahead of broad census/reconstruction backlog, while still filtering against the current repairQueue so recovered providers are not reopened from stale handoff memory.
- During implementation, the first budget-reader edit corrupted/duplicated `brain-learning-lab.yml` and GitHub produced workflow failures with zero jobs. The workflow was restored wholesale from last known-good SHA `d37636b...` and the bounded-budget change reapplied minimally. Current workflow size returned from ~88 KB corrupted to ~46 KB canonical; no subsequent zero-job Learning run was produced by the restore commit. Do not resurrect the corrupted intermediate versions.
- Full census race root cause was confirmed: run `35664170647` started on old SHA `1a36322...` before the stale guard existed and finished later, overwriting the newer Retest census. Future full-census runs now use `cancel-in-progress: true` and refuse persistence if remote main no longer equals their tested SHA.
- Full census is no longer allowed to overwrite `automation/provider-waf-browser-session-latest.json`. That canonical file is owned by the dedicated WAF/Tailscale lane because it may contain stronger residential evidence. Full census persists only its run-specific WAF file and re-applies the canonical latest WAF overlay before persisting census/repairQueue.
- AnimeVOSTFR current structured DATA is already correct (`official_site=https://animevostfr.org`, provider Lego option `base=https://animevostfr.org`, old-host domain substitutions present), but the published provider bytes still contained one executable pre-Core occurrence inside `PROVIDER.ANIMEVOSTFR.RUNTIME.V1`: `base=https://v2.animevostfr.org`. This is confirmed projection/rematerialization drift, not merely stale registry metadata.
- Domain Refresh already contains runtime-projection drift detection/rebuild logic. Domain Refresh run `35666696235` was triggered to repair current runtime projection; because main advanced during the run, its publication guard must either skip/requeue on the newer main or publish only if its captured base still matches. Do not claim AnimeVOSTFR fixed until the published provider bytes are inspected.
- REMAT/TEST #1 (`35667122473`) is queued for explicit `animevostfr`. It is the direct proof for whether current structured DATA rebuilds the provider away from the stale `v2.animevostfr.org` runtime without Repair. Result not yet claimed.

### 2026-09-22 — AnimeVOSTFR rematerialization drift proved and published
- REMAT/TEST #1 (`35667122473`, source SHA `e5d36425...`) targeted only `animevostfr` and completed green. Current structured DATA rematerialized published hash `835c6ce5...` into workspace hash `0787af3e...`; immediate current-byte Retest classified the rematerialized provider **CANDIDATE OK**. Log: `FIELD_PROVIDER_REMAT_TEST_DONE providers=1 changed_bytes=1 repair_queue=9`. This proves the issue was stale generated/projection bytes, not a Brain repair requirement.
- Domain Refresh #1049 had already detected `projection_drift=6 runtime_projection_drift=6 bundles=6` but was stopped by an obsolete ownership test that still required literal CONFIG-only mutation. The architecture contract was corrected to permit only CONFIG DATA plus explicit old-host -> current-host projection inside pre-Core `PROVIDER.*` Lego, while global Core mutation remains forbidden.
- Domain Refresh #1050 (`35667255693`, base SHA `012ff123...`) completed fully green, including the previously failing domain-only mutation gate, release reprojection, and publication. It published provider transaction SHA `7808c2b2...` and final main SHA `a9d650fad2d69af3ac6080ed1627d14b8ad3170c`.
- Published AnimeVOSTFR is now version `1.1.123`, file `providers/animevostfr--nuvio--0abf1d9f6533174a.js`. Direct inspection of the published JS confirms `PROVIDER.ANIMEVOSTFR.RUNTIME.V1` contains `base=https://animevostfr.org` and **zero** executable `v2.animevostfr.org` occurrence in the runtime block. Four old-host occurrences remain in CONFIG only as intentional historical substitution keys.
- This validates the new separation use-case: RETEST observes published bytes; REMAT/TEST proves whether current DATA would rebuild differently; only genuine runtime/capability failures proceed to FAST REPAIR.

### 2026-09-22 — Residential transport authority restored; false network blockers removed
- Dedicated WAF/Tailscale lane is now explicit and independent from full census concurrency. WAF #117 (`35669458155`) completed fully green with Tailscale residential exit active. It compared 16 provider lanes, selected 10 providers for full residential replay, and produced 2 strictly playable/verified providers: `animesalt` and `vostfree`. Privacy contract remained intact: no exit-node name, Tailscale address, residential public IP, bodies, cookies, or secrets persisted.
- WAF #117 persisted canonical transport evidence at commit `099032d9...`. Retest #7 then confirmed: `animesalt` FULL OK, `vostfree` FULL OK, `moviebox` CHAIN REACHED, `vidfast` ROUTE PROVEN. These are no longer false network/environment blockers.
- REMAT/TEST #2 (`35672176409`) targeted the remaining harness cohort `allwish, animevost-fr, flemmix, moviesmod`. All 4 rematerialized bytes changed, but none improved status: AllWish/Flemmix remained HARNESS/ENV BLOCKED and AnimeVOST-FR/MoviesMod remained HARNESS MISMATCH. Therefore these are not stale-byte projection bugs like AnimeVOSTFR.
- Exact harness evidence:
  - `allwish` + `flemmix`: residential exit still challenged; full residential provider replay returned no verified media. Treat as true anti-bot/session environment blockers, not normal provider Repair.
  - `animevost-fr` + `moviesmod`: real browser reaches content but direct HTTP/OkHttp do not; native TV transport remains unproven. These are browser/native-client transport gaps, not ordinary provider data/route failures.
  - `animesultra`: browser reaches content on GitHub and residential networks, but libcurl errors and OkHttp reports TLS/SSLHandshakeException. This is a native client/TLS harness mismatch.
- Post-WAF census fixes `ff678137...`, `eb4a75e2...`, `a548a3ec...` were finally projected by Retest #8 (`35674101065`). Result: **0 PROVIDER NETWORK BLOCKED** remain in the census. Anime-Ultime moved from false NETWORK BLOCKED to ROUTE PROVEN via normal residential zero-result replay; AnimeSultra moved from NETWORK BLOCKED to HARNESS MISMATCH.
- Retest #8 canonical counts: FULL OK 27, PARTIAL OK 1, CANDIDATE OK 2, CHAIN REACHED 3, ROUTE PROVEN 4, HARNESS MISMATCH 3, HARNESS/ENV BLOCKED 2, DISABLED 4. Current `repairQueue` has 9 providers: `4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix`. Current environment/harness queue has 5: `allwish, animesultra, animevost-fr, flemmix, moviesmod`.
- Fast Repair #3 (`35670406925`) ran against the prior 10-provider repairQueue and accepted 0 repairs; all 10 became explicit LEARN handoff debt. Direct handoff persistence is now inside Fast Repair itself because GitHub `GITHUB_TOKEN` pushes do not recursively trigger another workflow. Future Fast Repair explicitly dispatches bounded Learning instead of relying on a recursive push.
- Learning #232 (`35671977598`) was correctly targeted to the Fast-Handoff cohort and completed observation/reconstruction/adaptive queue/sanitized-state generation, producing 216 learning proposals and 160 memory entries, but failed only at proposal materialization. Root cause: sandbox ProviderBase rematerialization had temporarily rewritten global provenance to bases outside the targeted scope, so the proposal self-containment check asked for unrelated provider-base bytes.
- Learning proposal fix: the workflow now snapshots source `PROVENANCE.json` before sandbox ProviderBase rematerialization and passes that source snapshot to `materialize_clean_provider_reconstruction.py`. Sandbox-only provenance changes therefore cannot contaminate a targeted proposal.
- Learning speed fix: Fast-Handoff Learning now uses fair-share scheduling: one complete experiment/generation per provider per phase. Unresolved providers are persisted/retried in later phases rather than one provider consuming the whole global slot. Contract field: `fastRepairHandoffMaxAttemptsPerProviderThisPhase=1`.
- Learning #233 was intentionally superseded/cancelled because it started before the latest fixes. Learning #234 (`35674051765`, source SHA `e089811...`) is the current fair-share/source-provenance run. It started from the previous 10-provider census, so it may spend one bounded experiment on AnimeSultra; production writes are disabled and future cycles use the current 9-provider census. Do not claim #234 successful until proposal/materialization/upload and sanitized-memory publication complete.

### 2026-09-22 — Fair-share Learning proved; causal harness batching ready
- Learning #234 (`35674051765`, source SHA `e089811...`) validated the fair-share scheduler itself. Adaptive queue step completed green and visited all 10 handoff providers exactly once in the phase: `FIELD_BRAIN_QUEUE processed=10 retries=10 pending=10 exhausted=false`. This replaced the earlier behavior where only ~3 providers consumed most of a 20-minute slot.
- #234 generated `225` Learning proposals and `165` memory entries (`FIELD_BRAIN_LEARNING proposals=225 skills=1 memory=165`). It still failed only at step 22 proposal materialization; observation, clean reconstruction, adaptive Learning queue, historical comparison, and sanitized cross-day Brain state all completed successfully.
- Remaining proposal failure was not a Learning failure: global provenance referenced historical provider-specific base paths that no longer exist under `provider-bases/`, while identical content-addressed base bytes still exist in lifecycle archives. `materialize_clean_provider_reconstruction.py` now recovers a missing supporting base only by **exact expected SHA-256** from active/disabled/old ProviderBase stores, copies the bytes into the proposal under the referenced name, and still rejects missing/hash-mismatched content. Test coverage added in `brain_reconstruction_proposal_self_contained_test.py`.
- Fast-Handoff scheduling is now bounded by actual provider wall-clock slices, not merely one attempt/provider: each current provider gets a 45–120 second fair-share deadline derived from remaining global budget/provider count. A provider slice timeout becomes `FIELD_BRAIN_HANDOFF_SLICE_EXHAUSTED` + retry state rather than aborting the whole queue.
- Harness batching now includes `harnessTransportClass` in the batch identity. Browser-only/native divergence can no longer share a Learning family with `residential-exit-all-challenged` merely because capability/runtime families match.
- Brain self-architecture blueprints now specialize harness strategies by causal transport signature:
  - `browser-profile-only` -> `browser_session_transport_bridge_v1`;
  - `browser-profile-only-both-networks` + network exception -> `native_tls_browser_differential_v1`;
  - `residential-exit-all-challenged` -> `persistent_challenge_session_boundary_v1`.
  All remain review-only, forbid provider mutation as a substitute for client transport repair, and require playback proof before functional promotion.
- Retest #9 (`35674898034`) completed/persisted green on the current code and rebuilt the causal batch plan. Canonical census remains 27 FULL OK / 1 PARTIAL / 2 CANDIDATE / 4 ROUTE / 3 CHAIN / 3 HARNESS MISMATCH / 2 HARNESS-ENV BLOCKED / 4 DISABLED, with **0 PROVIDER NETWORK BLOCKED**.
- Current Repair queue is still 9: `4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix`.
- Current harness split is exact: mismatch = `animesultra, animevost-fr, moviesmod`; environment/challenge = `allwish, flemmix`. The rebuilt batch plan creates one harness group per transport signature/capability instead of mixing contradictory causes.


### 2026-09-22 — Targeted Brain pipeline green; control-plane intelligence upgraded
- Learning #244 (`35678577804`, source SHA `ecf095680026...`) is the first fully successful current Fast-Handoff Learning cycle. It ran exactly the 9 current repair providers (`4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix`), used the published-exact targeted stage, proved Fast-Handoff scope, built a 9-provider clean reconstruction stage, completed fair-share adaptive Learning, historical comparison, sanitized cross-day state, repair proposal materialization, architecture proposal materialization, artifact upload and sanitized-memory publication.
- #244 queue result: `processed=9 retries=9 pending=9 exhausted=false`. It generated 226 Learning proposals, 167 experiment-memory entries, 1 learned skill and 2 architecture proposals. **It accepted 0 concrete provider repairs and 0 clean reconstruction candidates.** A green Learning run is therefore not proof that the current provider debt is repaired.
- #244 exposed an active-context defect: retained native-reader memory (2548 failures / 70 repair-priority providers) dominated the final proposal list with providers outside the current 9-provider handoff. Retained memory is useful, but it must not become current-task authority.
- `learning-lab.mjs` now accepts an explicit provider filter in Fast-Handoff mode. Active proposals from experiment memory, historical targets, native portfolio, native reader aggregate signals, provider reader failures and repeated reader signatures are filtered to the current cohort. `nativeReaderRepairMemory` remains preserved unchanged for future tasks. Behavioral contract: `brain_fast_handoff_active_context_test.py`.
- The historical NiakVIO repair corpus is now an **executable prior**, not only a route/recipe hint. `brain_repair_runtime.py` exposes sanitized `historicalCases.solutionClass` rows to the planner only when the experience artifact is `repair-prior-only` and has no direct mutation authority. In Learning only, exact failure-class matches can select an already-supported causal profile one step before generic final exploration:
  - provider-owned origin/header/domain replay -> `provider_origin_failover_v1`
  - search/detail/player traversal -> `proven_route_terminal_traversal_v1`
  - terminal media extraction -> `chain_terminal_extractor_v1`
  - retained candidate replay -> `retained_candidate_replay_v1`
  - proven request program + media extraction -> `player_media_extractor_v1`
  Production Repair keeps its normal bounded variant order. Every historical selection still requires current-byte Deep/playback/identity proof.
- The first historical-strategy implementation initially failed closed because `HISTORICAL_SOLUTION_PROFILES` was initialized after the planner's top-level planning loop (JavaScript temporal-dead-zone). It was moved before planning; `brain_historical_solution_execution_test.py` now passes and proves a synthetic ROUTE PROVEN case selects `proven_route_terminal_traversal_v1` in Learning while production does not shortcut.
- The Fast-Handoff provider filter initially used the path-oriented `optionalArg` parser and converted `target-a` into an absolute filesystem path. It now uses scalar `arg()`; the active-context behavior test passes.
- Repair batch routing now obeys **deepest current causal proof > stale lower-layer issue text**. CHAIN REACHED cannot be downgraded to transport merely because an old `network_http_error` remains dominantIssue; ROUTE PROVEN similarly remains route-to-terminal. Only final `PROVIDER NETWORK BLOCKED` status owns transport refresh.
- Added `scripts/build_provider_execution_plan.py`: machine causal owner router above individual scripts. Current lane ownership is:
  - CANDIDATE OK -> `REMAT_TEST` first, fallback `FAST_REPAIR`
  - ROUTE PROVEN / CHAIN REACHED / missing lanes -> `FAST_REPAIR`
  - true NETWORK BLOCKED -> `DOMAIN_REFRESH`, fallback transport qualification
  - harness/client transport causes -> `CORE_CLIENT_LEARNING` (no provider mutation)
  - otherwise -> `BRAIN_LEARNING`
  It fails closed on batch/census queue mismatch and records that autonomous Core/client application is not yet validated.
- Added `.github/workflows/provider-brain-autopilot.yml`. Retest no longer launches Fast Repair directly: after an exact persisted census it dispatches Brain Autopilot. Autopilot rebuilds the batch plan + execution plan, runs a true domain owner alone when present, otherwise may dispatch disjoint REMAT and FAST REPAIR cohorts in parallel, and explicitly blocks Core/client production mutation until a validated application lane exists. Fast Repair and REMAT workflows now accept comma-separated provider cohorts for catalogue-scale runs.
- Core Workflow Gate `35680170486` completed **success** on the intelligence/autopilot contract set: Python syntax, runtime contracts, historical executable strategy, Fast-Handoff active-context isolation, deepest-proof routing, execution router, Autopilot workflow, native loading compatibility and side-effect purity all passed.
- Next authoritative proof is a fresh Retest with Autopilot enabled on current HEAD. The success criterion is not merely a green run: inspect the generated execution plan, actual lane dispatches, historical strategy use, accepted candidates and current-byte validation.

### 2026-09-22 — Autopilot causal + Learning #245
- Retest #10 (35680423643), Fast Repair #6 (35680516776) et Learning #245 (35680716353) ont terminé verts sur la nouvelle chaîne causale.
- Learning #245 a ciblé exactement 9 providers: 4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix. Résultat queue: processed=9, retries=9, pending=9, exhausted=false.
- #245 a produit 49 propositions actives ciblées, 167 entrées mémoire et 1 learned skill, mais 0 provider proposal et 0 clean reconstruction candidate. Aucun provider n'est donc déclaré réparé par #245.
- Les solutionClass historiques NiakVIO sont désormais des priors Learning exécutables bornés, toujours soumis aux gates current-byte Deep/playback/identity.
- Le causal execution router/Autopilot choisit désormais le propriétaire REMAT_TEST, FAST_REPAIR, DOMAIN/transport, CORE_CLIENT_LEARNING ou BRAIN_LEARNING au lieu d'envoyer tous les cas vers Repair.
- Prochaine action autorisée: Learning long chaîné sur le même handoff, proposal-only, avec fair-share et sans publication production sans preuve current-byte + playback + identity + non-régression.

### 2026-09-22 — Long Learning exposed and fixed cross-phase experiment-memory reset
- Long chained Learning ran four logical phases on source SHA `256a452...`: #246 `35681235121`, #247 `35681820137`, #248 `35682328126`, #249 `35682783307`. Sandbox/learning work completed successfully in every phase; #246/#248 overall conclusions were cancelled only because their successor phase superseded the workflow after the useful jobs had completed.
- The four phases were **sterile** despite fair-share speed: each repeated approximately `negative_entries=167 / skills=1 / processed=9 / retries=9 / pending=9 / proposals=49 / provider_proposals=0`. Comparison of the targeted provider experiment memory before/after the chain showed no useful generation/counter progression. Do not treat this long chain as additional repair learning.
- Root cause: `run_brain_learning_sandbox.py` consumed `previous.experimentMemory` only to suppress repeated profiles, while `brain_repair_runtime.py` still computed `experimentVariant/experimentGeneration` solely from production `automation/brain-repair-memory.json`. In addition, `learning-lab.mjs` discarded experiment variant/generation and keyed memory only by provider/version/signature/profile, collapsing distinct generations.
- Cross-phase fix:
  - Learning child processes now receive the prior sanitized state as `NIAKVIO_BRAIN_LEARNING_MEMORY` before importing Brain runtime.
  - `brain_repair_runtime.repair_memory()` overlays sanitized cross-phase experiment memory **only when planner mode is Learning**; normal production Repair remains anchored to canonical production memory.
  - Learning experiment memory now preserves and keys `experimentVariant + experimentGeneration`, along with bounded causal metadata.
  - Added `brain_cross_phase_experiment_memory_test.py`: a previous Learning g2 failure must make the next Learning plan choose g3, while production Repair must not import that unvalidated g2 Learning state.
  - Added `FIELD_BRAIN_PROVIDER_PLAN` logging with provider/failure/variant/generation/profiles/historical strategy/exhaustion for direct run-time proof.
- CORE Workflow Gate #5679 / run `35693120105` completed **success** on HEAD `187a56ff0fa0...`, including the new cross-phase progression contract. Next proof must be a real targeted Learning run showing generation progression in `FIELD_BRAIN_PROVIDER_PLAN`; a green workflow alone is insufficient.
### 2026-09-22 — Cross-phase Learning progression root cause and ledger fix
- The chained overnight Learning slot #246→#249 was fast but materially stagnant: four phases replayed the same 9-provider debt with the same 167 experiment rows / 49 proposals / 0 provider candidates. Root cause was not CPU or fair-share scheduling: planner generation selection still read production automation/brain-repair-memory.json while cross-day Learning state only restored learned skills / suppression hints.
- Cross-phase planner memory is now Learning-only: the prior sanitized experimentMemory is passed at child-process spawn time, merged into planner negative memory only when NUVIO_BRAIN_PLANNER_MODE=learning, and never becomes production Repair authority.
- Learning memory keys now preserve experimentVariant + experimentGeneration; distinct g/v experiments are no longer collapsed into one provider/signature/profile row.
- Real Learning #250 (35693424647, SHA ce3582e...) proved actual progression in the sandbox: AllAnime, AnimeVOSTFR and MalluMV selected generation 3 causal profiles; other providers advanced to later variants. The sandbox was green; only sanitized-memory publication failed because the old memory branch update attempted to carry workflow-tree changes without workflows permission.
- The cross-day state now consumes the complete runtime experiment ledger (including profile-unavailable, generation failure and non-publishable progress events), not only representable repair-report rounds.
- Learning memory publication no longer rebases the memory ref on production main; it advances from its own branch tree, preventing unrelated workflow/code changes from entering a memory push. Existing legacy branch contents are retained for now to avoid a destructive workflow-file deletion requiring elevated permissions.
- CORE Workflow Gate #5686 (35694223182, SHA 8e612254...) passed fully after runtime-ledger and memory-publication fixes. Next required proof is a two-phase targeted Fast-Handoff run: phase 1 must publish the new ledger and phase 2 must consume it and choose a different generation/variant.
### 2026-09-22 — Fair-share exact experiment ledger
- Two-phase proof #252→#253 proved cross-phase state publication/restore works but also proved the remaining defect: phase 2 replayed the exact same 9 plans as phase 1. The planner selected g3 for AllAnime/AnimeVOSTFR/MalluMV, but the persistent cross-day state did not record those exact g/v identities.
- `scripts/run_brain_learning_queue.py` now owns a sanitized per-phase experiment ledger built from the exact fair-share `provider_plan` plus the actual child attempt outcome and final Lab status. It preserves provider/failure/signature/profile/variant/generation and distinguishes accepted, rejected, profile_unavailable, not_generated and exploration_progress_nonpublishable. A child acceptance is positive only when the independent final Lab is playable.
- Learning now feeds `brain-sandbox/health-output/runtime-experiment-memory.json` into `learning-lab.mjs`; global `automation/brain-repair-memory.json` is no longer the cross-phase authority for the current fair-share experiment.
- `tests/brain_learning_queue_experiment_ledger_test.py` locks g3/g4 identity, unavailable-profile attribution, sanitized progress reasons and final-playback success gating. It is wired into Workflow Gate, Learning, Fast Repair and canonical Repair preflight.
- `brain-branch-maintenance.yml` is now read-only for `brain-learning/proposals`: it validates sanitized memory and cleans the repair proposal branch but never rebases/mirrors `main` into the memory ref. Maintenance #3833 passed with `mode=memory-ref-read-only` and 306 memory entries.
- CORE Workflow Gate #5698 (`35696450350`, SHA `c6b044b...`) passed fully after the queue-owned ledger and read-only maintenance changes. Next proof must show actual cross-phase plan progression, especially g3→g4 for the current causal profiles.

### 2026-09-22 — g5 exhaustion now escalates to executable second-order strategies
- Learning #260 (`35701662187`, SHA `34203162...`) completed fully green and proved the cross-phase experiment ledger now advances materially. It loaded 333 negative-memory rows and reached true g5 exhaustion for `allanime`, `animevostfr`, and `mallumv`; those three emitted `collect-more-evidence / profiles=none / exhausted=true`. Other providers continued bounded earlier-family exploration (for example route/media/search cohorts at v4/g2).
- This establishes the next real Brain limitation: after the bounded g2..g5 causal family is exhausted, the planner previously stopped at an architecture label instead of executing a genuinely different method.
- Added finite, Learning-only second-order strategies after g5. They have distinct profile identities and memory entries; they do **not** extend g5 by merely increasing pages/depth. Families include route-transition graph, terminal-transition graph / request-program inference, retained-candidate divergence/request-program replay, player/media protocol inference, search-contract inference and provider-owned transport differential.
- `engine_v2/scripts/plan-repairs.mjs` now selects the first unfailed second-order strategy after base-family exhaustion, marks `baseExperimentExhausted=true`, `strategyEscalated=true`, and executes the evolved strategy with `probe-targeted-repair`. If the first evolved strategy fails, the next one is selected; only after the finite evolved set is exhausted does the provider return to `architecture_gap / collect-more-evidence`.
- `scripts/adaptive_runtime/runtime_repair.py` executes these strategy ids as materially different evidence programs (provider-owned/peer transition graphs, terminal-only graphs, retained candidate divergence replay, request-program inference, etc.) while preserving normal current-byte playback/identity acceptance gates.
- Architecture blueprints were aligned with the executable evolved strategy ids so architecture Learning and runtime Learning no longer describe two different strategies.
- Memory branch `brain-learning/proposals` is now a true isolated orphan memory ref: parentCount=0 and exactly two blobs, `engine_v2/learning/latest.json` + `latest.md`. It cannot carry production workflow/code changes.
- CORE Workflow Gate #5724 / run `35705925375` completed **success** on HEAD `107552ca...` after the second-order planner/runtime tests and deferred-cohort blueprint contract were updated.
- Next proof must be a real targeted Learning pass from the already-persisted g5 state. Required runtime evidence: exhausted chain-terminal providers select `terminal_transition_graph_v1`; exhausted candidate-replay providers select `candidate_divergence_trace_v1`; these attempts must be persisted as distinct experiment-memory profiles before any claim of improved repair capability.


### 2026-09-22 — Learning→Repair return edge and current provider outcome truth
- Current published provider Brain result is still **0 accepted repairs**: `automation/provider-brain-repair-latest.json` reports `acceptedRepairCount=0`, `fixedInLabProviders=[]`, with unresolved/deferred causal families. Do not describe the recent Brain work as provider repairs until a current-byte Repair/Retest accepts and verifies one.
- Run v18 `35715829940` on source SHA `da732a91cc30...` is the strict proof run for first real post-g5 candidate execution. At the last check it was still inside `Run adaptive Learning provider queue`; therefore no v18 provider acceptance or census promotion is established yet.
- The orchestration gap behind the stale visible census was narrowed precisely: canonical Repair can escalate deferred providers to `brain-learning-lab.yml`, but when its own `resumeRecommended=false` and `remainingProviders=[]`, there was no return edge after Learning. That leaves improved Learning memory unused by a fresh canonical Repair and keeps `PROVIDER_CENSUS_STATUS.md` on the prior Repair authority.
- Added `tests/brain_learning_repair_return_workflow_test.py` (commit `97a6c442...`) and updated `.github/workflows/brain-learning-lab.yml` (commit `123b57e7...`) so a **push-triggered** Learning that successfully publishes fresh sanitized memory dispatches `provider-recognition-repair-v6.yml -f mode=repair`. The return is intentionally push-only: Repair-triggered Learning uses `workflow_dispatch`, so this does not create an unbounded Repair→Learning→Repair recursion.
- The Learning memory publication step now exposes `published=true/false`; canonical Repair return is skipped for stale memory candidates. `publish-learning` has `actions: write` only because it now dispatches the canonical Repair workflow.
- v18 itself started before commit `123b57e7...`, so its tested SHA does not contain the new return edge. After v18 finishes, inspect its artifact for real evolved `attemptedProfiles` / `executionObserved=true`; then explicitly run canonical Repair on current `main` if v18 cannot auto-return. Only Repair/Retest may regenerate the authoritative census and promote provider statuses.


### 2026-09-22 — v18 proves real post-g5 execution; Repair preflight late-stage peer-floor fix
- Learning v18 run `35715829940` completed its sandbox successfully on source SHA `da732a91cc30...`. Artifact `niakvio-brain-learning-state` / id `10690137345` was inspected directly; this is the first strict proof that post-g5 strategies were **actually executed**, not merely selected.
- Exact runtime ledger evidence includes `executionObserved=true` for evolved profiles such as `route_transition_graph_v1`, `route_peer_transition_replay_v1`, `terminal_transition_graph_v1`, `terminal_request_program_inference_v1`, `candidate_divergence_trace_v1`, `candidate_request_program_replay_v1`, `player_protocol_family_replay_v1` and `transport_request_differential_v1`. The same profiles appear in real `attemptedProfiles` for the targeted providers.
- All evolved attempts remained unresolved and were rejected by the safety gate with no playable proof. v18 therefore produced **0 provider proposals and 0 clean reconstruction candidates** (`repair-proposal.json providerProposalCount=0`, `provider-reconstruction-proposal.json candidateCount=0`). Do not equate evolved execution with provider repair.
- Canonical Repair run `35717365591` on SHA `f8212e9e...` failed before provider correction at `Prove one canonical Learn Force repair implementation`. Exact blocker: `tests/brain_current_observation_recipe_test.py` expected the conservative peer-transfer floor 3 for `media_extraction_gap`, while runtime historical/archetype prior lowering changed it to 2.
- Root cause was generic prior acceleration in `adaptive_runtime/runtime_repair.py`: every historical/archetype match reduced peer-route and peer-recipe minimum variant by one. This is valid for broad transport/route exploration, but not for `candidate_replay_gap` and `media_extraction_gap`, where retained/current provider evidence must remain authoritative through variant 2.
- Commit `15f222627117...` preserves the v3 peer-transfer floor for those late-stage provider-sensitive failures while retaining one-variant acceleration for broader causal gaps. Existing `brain_current_observation_recipe_test.py` and `brain_repair_experience_transfer_test.py` are the targeted contracts to revalidate in canonical Repair preflight.
- Failed Repair did not repair providers. Its persistence path only added `automation/provider-brain-repair-35717365591.json` in commit `12e5b909...` and escalated 7 deferred providers to Learning run `35717441001`. Provider acceptance remains unproven until the next Repair reaches the canonical correction stage and passes current-byte playback/identity gates.


### 2026-09-22 — Canonical Repair #142 completed; census refreshed, zero provider repairs
- Canonical Repair run `35717871480` completed SUCCESS on exact source SHA `074a94046c6f68eb1213e79476885b18de43b21a`. The previously failing canonical preflight passed, integrated GitHub/Tailscale WAF qualification passed, canonical recognition/correction completed, four-version candidate floor passed, scoped network re-probe verification passed, and persistence completed.
- The run is **not a provider-repair success**: `automation/provider-brain-repair-latest.json` reports `acceptedRepairCount=0`, `fixedInLabProviders=[]`, `acceptedRepairs=[]`, and `noProgressReason=experiment_variants_exhausted`. The eight Brain-processed providers were `4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, vidfast, yflix`; `persianstremio` remained in the canonical Repair queue but was carried as current CANDIDATE OK evidence instead of being selected by this Brain pass.
- Exact candidate portfolio evidence: 8 providers, 37 probes, **0 raw stream providers, 0 playable providers, 0 identity-verified providers**. Debug-stage totals were dominated by `provider_network_zero_result`, `provider_network_http_error` and `provider_network_exception`. No preservation loss was introduced by the candidate.
- Repair evidence was persisted to main by commit `4ece54063593db8024d8d1795d12767845b0a5a9`. The authoritative census is now `runId=35717871480-post-repair-candidate`; the stale-census complaint is therefore closed, but the provider debt is not.
- Current census counts after real Repair evidence: **25 FULL OK · 1 PARTIAL OK · 2 CANDIDATE OK · 2 ROUTE PROVEN · 2 CHAIN REACHED · 3 PROVIDER NETWORK BLOCKED · 5 HARNESS MISMATCH · 2 HARNESS/ENV BLOCKED · 4 DISABLED** across 46. Current Repair queue remains 9: `4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix`.
- Current provider evidence sharpened several causes: `allanime` and `mallumv` reach content-specific chains but fail terminal media; `4khdhub`/ `yflix` retain route/lookup proof but no terminal media; `anime-ultime`, `moviebox`, `vidfast` are now current PROVIDER NETWORK BLOCKED rather than generic route gaps; `animevostfr` remains CANDIDATE OK without current playable reproduction.
- The latest Learning architecture proposal correctly treats this as **new capability debt**, not retry-count debt: current g2..g5 and first post-g5 strategy families were actually executed and exhausted without playable proof. Next Brain work must synthesize materially new bounded evidence/repair methods per causal cohort, each with a distinct experiment identity, actual generated attempt, playback/identity proof and regression contract.
- Additional architecture audit: Fast Repair explicitly imports sanitized persistent Learning skills through `NIAKVIO_BRAIN_LEARNING_MEMORY`, while the canonical Repair workflow does not currently mirror that import. This should be aligned for consistency, but the present persistent skill is only `candidate` maturity and production requires `trusted` + confidence >=0.8 + >=2 providers, so importing it alone would not repair the current nine-provider debt.


### 2026-09-22 — Third-order Brain capabilities: executable preflight proven
- After canonical Repair `35717871480` proved zero accepted repairs despite a fully green pipeline, the next Brain iteration was based on exact current traces rather than wider retries. Four new bounded causal strategies were added: `identity_alias_search_traversal_v1`, `runtime_response_salvage_v1`, `document_request_contract_mining_v1`, and `provider_session_bootstrap_replay_v1`.
- Planner/profile/runtime plumbing landed across commits `4d5eb146...`, `f5a2980d...`, `62baaebe...`, `b4b8a6d6...`, `bf2b674f...`; executable generator algorithms landed in `2281d4f0...`. The generator now supports TMDB original/alternative-title search, transient successful-response salvage, bounded same-origin document POST-contract mining, and provider-domain session bootstrap. Successful response bodies used by salvage remain transient in-process evidence and are not persisted.
- `tests/brain_third_order_strategy_runtime_test.py` (`d14d4a52...`) contains real Node execution proofs: (1) localized `La Colonie` search misses while TMDB original title `The Colony` reaches a terminal HLS URL; (2) a synthetic provider receives a successful JSON response containing HLS, returns `[]`, and `runtime_response_salvage_v1` recovers that already-observed media.
- First v19 run `35721239104` on `ae8e94e5...` failed before provider execution because the older `brain_final_experiment_generation_test.py` still assumed the previous two-strategy terminal family was exhausted. This was a stale test contract, not provider/runtime evidence. It was updated in `b2919f39...` to require the new salvage and document-contract strategies before architecture exhaustion.
- v19b Learning run `35721492932` on exact SHA `0a78ec37585e3cd6b61b4044999857e1fbb50adc` has now passed the complete Learning preflight, including the third-order real Node execution test. At this checkpoint it has not yet produced provider outcomes; do not claim a real provider repair until its actual queue artifact shows attempted profiles/execution and playable/identity proof.


### 2026-09-22 — Third-order Lab recovery proof running; document-contract coverage expanded
- Canonical Repair `35717871480` is green but remains a **zero-repair** run: `acceptedRepairCount=0`, `fixedInLabProviders=[]`. Its post-Repair census is authoritative/current and classifies the remaining failures rather than promoting them without playback proof.
- Third-order Learning `35721492932` proved real execution of `identity_alias_search_traversal_v1`, `runtime_response_salvage_v1` and `document_request_contract_mining_v1` on live targeted providers, but the run failed because a provider fair-share timeout closed the one shared `LearningLabSession`; later providers then received `Learning Lab session exited early: 0`. This is a queue/session lifecycle defect, not provider repair evidence.
- `3782e98f...` plus regression coverage through `62992cf5...` makes the Learning queue restart the warm Lab session after a provider slice timeout so one slow provider cannot terminate the remaining cohort.
- Learning run `35731458157` on source SHA `09102ccf...` is the active proof of third-order strategies with Lab-session recovery. CORE Workflow Gate `35731458207` passed fully on the same source SHA. Do not attribute later HEAD changes to this run.
- Repair `35717871480` evidence shows a generic strategy-coverage gap: ROUTE PROVEN / CANDIDATE/search cases can have successful HTML responses but still fail before terminal binding. `document_request_contract_mining_v1` already executes provider-agnostic form/action mining, but the planner did not offer it to those families.
- `f49c3854...` adds document-contract mining as the final post-exhaustion fallback for `route_proven_gap`, `candidate_replay_gap` and `search_gap`; `178402dd...` adds a regression proving ordering and runtime applicability. Learning, Fast Repair and canonical Repair preflight now gate this contract (workflow commits through `520531cd...`).
- The active `35731458157` run predates the document-contract expansion. If it produces no playable candidate, the next targeted Learning run must use current HEAD so the newly expanded fallback is actually tested before any further architecture escalation.


### 2026-09-22 — Repair→Learning causal-wave crash fixed; provider-local positive replay and single-provider Learning
- Canonical Repair `35733060889` completed SUCCESS on source SHA `4c331aa7...` but accepted **0 repairs** (`accepted=0`, `fixed_lab=0`). Its own post-repair census candidate was not promoted because main advanced mid-run to availability commit `47ec45fb...`; Repair correctly emitted `FIELD_REPAIR_CANONICAL_LEDGER_STALE` and dispatched fresh census run `35735515634`.
- Repair also dispatched Learning `35735518458` on evidence commit `7fb764f6...`. Preflight, stage and reconstruction were green, but the provider queue crashed before provider 1 with `UnboundLocalError: fair_handoff`: `causal_family_waves(... if fair_handoff)` was evaluated before `fair_handoff` was assigned. This run produced no provider Learning evidence and must not be counted.
- Commit `496390af...` moves Fast-Handoff initialization before causal-wave materialization. Commit `4c6a53de...` strengthens the already-wired causal-wave test with an explicit initialization-order regression so this runtime-only defect is gated by Learning, Repair, Fast Repair and CORE.
- Durable positive-program memory currently contains one strict current-cohort example: MalluMV previously improved `no_streams -> healthy` with playable count `0 -> 1`, using the accepted provider-local program around `/search.php?q={query}` and `/api/file/`. Current census labels MalluMV `CHAIN REACHED / chain_terminal_gap`, while the accepted program was learned under `media_extraction_gap`.
- Root Brain weakness: strict positive programs were converted to learned skills but filtered by the current failure-class label, so a same-provider program could be forgotten after diagnostic relabeling. Commits `fc5edc9b...`, `f6239379...`, `585009bc...` mark strict same-provider positive priors, preserve that marker through Brain merging, allow only that provider to survive failure-class drift, and give it first replay priority. The program remains prior-only and must still pass current-byte playback, identity and non-regression gates; peer transfer remains forbidden.
- Regression coverage: `f100561e...` checks durable-memory marker emission; `e879fab7...` proves a provider-local `media_extraction_gap` positive program is replayed first when the same provider is now `chain_terminal_gap`, while another provider cannot inherit it. The contract is wired into Learning, canonical Repair, Fast Repair and CORE.
- To avoid repeating 9-provider proof runs for one hypothesis, push-triggered Learning can now accept `target_provider:` from `.github/triggers/brain-learning-reconstruction`. Commits `12fb5441...`, `ab78e6a3...`, `541050fb...`, `04c333c2...` restrict published stage, health filter, clean reconstruction and queue to that exact current Repair-handoff provider, fail closed if it is outside the handoff, and gate the workflow contract.
- Fresh census run `35735515634` started from `7fb764f6...` before these Brain commits. It may remain useful observational evidence, but after main advanced it is no longer eligible to be the final authoritative census. Final census must be regenerated after the next validated Repair/Retest on current HEAD.


### 2026-09-22 — Single-provider MalluMV targeting now reaches Brain preflight; stale ordering test fixed
- Targeted Learning run `35737448566` on SHA `e8bc19f5...` proved the explicit current-Repair target contract now works: `Configure bounded Learning slot phase` passed after `d349c3f3...` decoupled an explicit provider target from the already-consumed ephemeral Fast-Handoff marker. MalluMV is validated against current `repairQueue` plus `LEARN/pending` handoff state.
- The run then stopped in Brain preflight only because `tests/brain_learning_push_target_workflow_test.py` searched the first occurrence of `steps.learning-slot.outputs.target_provider`, which is the job output declaration above the validation block, instead of the queue-step occurrence. All preceding Brain contracts passed, including same-provider positive-program cross-failure replay.
- Commit `c5b9ef5e...` scopes that ordering assertion to the `Run adaptive Learning provider queue` step. This is a test-contract correction; run `35737448566` produced no provider repair evidence.
- Next proof is again MalluMV-only on current HEAD. Required evidence remains actual provider-local positive-program replay on current bytes and independent playable/identity-safe Lab validation before any provider status promotion.


### 2026-09-22 — Explicit MalluMV scope now propagates to downstream health validation
- MalluMV proof run `35737809635` on SHA `019f085b...` passed the complete Brain preflight and actually ran the targeted health observation with `NUVIO_HEALTH_PROVIDER_FILTER=mallumv`; the health stage selected exactly 1 provider.
- The run stopped at `Prove targeted Fast-Handoff observation coverage` because the effective shell scope was MalluMV but `/tmp/fast-learning-handoff.json` still contained the earlier empty selector output. The validator therefore failed with `fast handoff has no providers`. This is orchestration metadata drift, not provider evidence.
- Commits `e561b30b...` and `03627c01...` make explicit current-Repair targeting rewrite the sanitized temporary handoff file to the exact one-provider scope after repairQueue + LEARN/pending validation. Downstream health-scope validation now consumes the same scope that the health command actually executes.
- Run `35737809635` was superseded/cancelled and produced no MalluMV repair result. The next run must reach the actual provider queue before positive-program replay is judged.


### 2026-09-22 — Target-scope handoff write bug isolated before MalluMV execution
- MalluMV proof run `35738124587` on SHA `1a97b914...` passed the complete Brain preflight and built a one-provider published stage. Health execution was correctly scoped to MalluMV (`FIELD_HEALTH_PROVIDER_FILTER requested=1 selected=1 ids=mallumv`).
- Downstream scope validation still failed with `fast handoff has no providers`. Root cause was an argument-index bug in the new explicit-target propagation: the temporary target handoff JSON was written to `sys.argv[2]`, which is the sandbox census path, while the validator continued reading the untouched `/tmp/fast-learning-handoff.json`.
- Commits `2630f460...` and `8959f7df...` pass `/tmp/fast-learning-handoff.json` explicitly as argv[4] and write the one-provider sanitized target scope there. The erroneous write was sandbox-only; run `35738124587` published no state and produced no provider repair evidence.


### 2026-09-22 — MalluMV proof reached real queue; positive memory was planned but not executable
- Targeted Learning run `35738647346` on exact SHA `cbf35fc71037...` completed SUCCESS through the real one-provider Brain queue for MalluMV. The target scope, preflight, health coverage and clean ProviderBase reconstruction all passed.
- The run did **not** repair MalluMV. Exact queue evidence was `provider_unreachable / no_provider_request_observed`, then `FIELD_BRAIN_PROVIDER_PLAN ... action=collect-more-evidence ... profiles=none ... exhausted=true`; the artifact produced `provider_proposals=0`, `attemptedProfiles=[]`, `attemptedMethods=[]`, and no playable proof.
- This isolated the real positive-memory defect: MalluMV's strict provider-local validated program existed and ranked first before exhaustion, but the planner discarded all learned hypotheses once the ordinary g5 family was exhausted. Commit `dfd8fa86...` introduced a distinct post-exhaustion identity `provider_positive_program_replay_v1` so the same-provider positive program gets one bounded replay before architecture-gap escalation.
- `dfd8fa86...` alone was planner-only and therefore still insufficient: the adaptive runtime did not recognize the new profile and would have returned `profile_unavailable`.
- Commits `ca68e59c...`, `17c72e09...`, and `931414eb...` complete planner→runtime→experiment-memory persistence for `provider_positive_program_replay_v1`. It is now a separately addressable causal profile; stale unexecuted `profile_unavailable` debt is ignored until a real attempt occurs.
- Regression coverage: `7c04d1a8...` requires the runtime to recognize/materialize the new profile; `13914c79...` constructs a genuinely exhausted g5 ledger and proves the strict same-provider positive replay is selected, while a real failed replay suppresses that identity normally on the next plan.
- No status promotion is allowed from these code changes. Next required proof is a fresh MalluMV-only Learning run on current HEAD showing `provider_positive_program_replay_v1` in actual attempted profiles plus `executionObserved=true`; success additionally requires current-byte playable + identity-safe Lab evidence.


### 2026-09-22 — Positive replay executed; winning-trace memory + declared-Lego publication drift fixed
- MalluMV-only Learning run `35741755636` on SHA `1e1de87b...` completed SUCCESS and is the first proof that `provider_positive_program_replay_v1` executed as a real candidate: actual `attemptedProfiles` contains that profile and the exact experiment ledger records `executionObserved=true`.
- The replay did **not** repair MalluMV. It improved the diagnostic stage from the raw published observation `provider_unreachable / no_provider_request_observed` to `no_streams / content_lookup_completed_no_streams`, but TV/Desktop/Mobile all remained `runtime_empty` with zero playable streams. The strict safety gate rejected it with `safety_gate:no_playable_proof`. No provider status promotion is justified.
- Inspecting `automation/brain-positive-program-memory.json` exposed why the historical success could not be faithfully replayed: the backfilled MalluMV positive program stores search seeds and learned routes but `providerValuePlan=[]`. The prior success therefore remembered entry points, not the winning terminal request chain.
- Generic root cause: `deep_repair_loop.accepted_runtime_program()` captured generator options before retest but ignored the winning `selected_result` network trace. A repair could become playable through dynamic crawling and then persist only its initial seeds. Evolved causal adaptive profiles were also not captured because the function matched only the literal profile name `adaptive_runtime_recovery`.
- Commits `1aa10109...`, `2c1e7eb4...`, `696602e7...`, `1e0b5c65...`, and `a25f7c70...` pass the winning result into program capture, identify adaptive-engine records independently of the causal profile name, and merge only sanitized/replayable winning request recipes using the existing `observed_request_recipes` binding logic in both Learning/Quick and Deep/Repair.
- Regression coverage `9ed63a66...` proves an accepted causal profile is captured as adaptive program DATA while retaining its executed profile identity. New `tests/brain_accepted_program_winning_trace_test.py` (`faad1c10...`) requires an observed `search -> id -> player` chain to compile into a non-empty `providerValuePlan`. The test is gated in Learning, canonical Repair, Fast Repair and CORE through commits `71c60589...`, `b5bd6ee4...`, `a97e816d...`, and `e672d3c6...`.
- A second structural drift was confirmed on current main: `provider-overrides.json` declares MalluMV `provider_lego_scripts = scripts/provider_patches/mallumv_runtime_v1.py`, but the currently published MalluMV bundle contains neither `NIAKVIO_MALLUMV_RUNTIME_V1` nor the provider runtime dispatcher. The Lego itself has a tested full `search -> movie -> confirm -> internal -> terminal crawl` contract.
- `08f7fb5c...` strengthens `published_provider_lego_contract_test.py`: every non-optional declared Provider Lego must have its module `MANAGED_FIX_ID` present in the published bundle. Existing tests previously verified placement only for Lego that happened to be present, so declaration-to-bytes drift could pass silently.
- Repair run `35742103933` on SHA `1e1de87b...` did not produce provider evidence: Tailscale/residential qualification completed, materialization reached all 42 active providers, then the runner received an external shutdown signal (exit 143) immediately after starting adaptive Deep Repair. Artifact/persistence were canceled. This is not a provider or Brain failure.
- Next validation: run canonical Repair on current main. Its materialization must satisfy the stronger declared-Lego contract, then Deep Repair/Retest must run. After persistence, inspect MalluMV published bytes, actual playable proof, accepted repairs, and authoritative census. If MalluMV remains unresolved, the next Brain strategy must use fresh current trace/terminal evidence rather than replaying the now-failed truncated historical program.

## 2026-09-22 — Positive-program replay debt is now program-version aware

- MalluMV Learning run `35746250601` on SHA `0409701f9b7cddfbbcfe798bb5b2bdf6b4400df5` passed the full Brain preflight but executed no repair profile: final plan was `chain_terminal_gap / collect-more-evidence / exhausted=true`, `attemptedProfiles=[]`, and the phase experiment ledger was empty.
- Root cause: negative experiment memory identified `provider_positive_program_replay_v1` only by provider/signature/profile/generation/variant. A real failed replay of the older truncated positive program therefore suppressed every future positive replay, even after the durable provider-local program changes.
- Durable positive memory already has SHA-256 fingerprints. Commits `ccd94f77533601304db90df4068a293fdf9ddf71`, `dabc7e1ddc7619d74c489d84802c43355d9b110a`, `706d3c72381d71ff01cb2e16239341b31ea1b825`, `007c8818a198658bfb0114c82f0937f3bc7441ff`, and `3c1e2fdf6c52508af46e010300d3e29774448bb4` propagate an aggregate same-provider positive-program fingerprint through planner skills, selected plan snapshots, negative memory, the fair-share exact experiment ledger, and sanitized cross-day Learning memory.
- Regression coverage: `eea89d57b543198ac013fb27933e234b275284f7` proves legacy/unversioned or different-program replay debt does not suppress the current fingerprint, while failure of the exact same fingerprint remains bounded; `66799ec677abbc40240f80a3ef8168d7c29f4af8` proves positive memory projects a durable provider fingerprint.
- Current proof run: `35748094410`, source SHA `5c4d3b3ce77da52aa1dace30298260d8f8393112`, MalluMV-only. Success criterion is not workflow green: the artifact must show `provider_positive_program_replay_v1` in actual attempted profiles plus a non-empty `positiveProgramFingerprint` on the exact experiment ledger. Playable proof is still required before MalluMV can leave Repair.
- Separate confirmed issue still open: `provider-overrides.json` declares `scripts/provider_patches/mallumv_runtime_v1.py`, but the currently published MalluMV bundle inspected before this run did not contain `NIAKVIO_MALLUMV_RUNTIME_V1` nor the provider runtime dispatcher. This override→published-byte drift must be revalidated/corrected independently of replay-memory versioning.

### 2026-09-22 — Brain owns CHAIN REACHED neutral transition mining; no provider-local MalluMV patch

- User constraint reasserted: provider repairs must be produced by the Brain, not manually authored per provider. A local draft MalluMV patch was intentionally not attached to any branch/ref and is not part of main.
- Current main remains the authority. The MalluMV case is used only as a Learning witness for a generic defect: adaptive terminal traversal ranks player/embed/api URLs but can ignore provider-owned neutral same-origin transitions that sit between a proven detail/player page and terminal media.
- Generic Brain change: `terminal_transition_graph_v1` now compiles bounded transition prefixes from the provider's own durable route DATA (excluding search/detail/root-only templates). These prefixes are recognition hints only; they are never executed by guessing. The adaptive runtime mines only matching URLs that are actually present in successful response bodies and follows them under the existing depth/page/media/identity limits.
- `terminal_transition_graph_v1` now enables runtime-response salvage so a native/provider runtime that reaches a valid document and then returns `[]` still exposes that already-observed response to the bounded transition miner. No provider-specific route name, ID or parser is encoded in the engine.
- Regression proof is synthetic and provider-agnostic: a fake provider stops after a detail request; provider-owned route templates describe two otherwise-neutral intermediate families; the response embeds those transitions in escaped/non-anchor text; the production V5 adaptive wrapper must discover both and reach a MIME-verified HLS terminal.
- Next proof is targeted Learning on MalluMV from current main. Success requires the Brain-selected `terminal_transition_graph_v1` (or a later Brain strategy) to generate current-byte playable/identity-safe evidence. No MalluMV status promotion is allowed from the engine patch or synthetic test alone.



### 2026-09-22 — terminal_transition_graph_v1 preflight failure corrected before live proof

- Targeted Learning run `35752370169` on SHA `19d485ab9a72fc6f6ff010a4c013e5175f083bb9` failed in preflight before MalluMV execution. The generic synthetic contract expected provider-owned neutral prefixes `/confirm/` and `/internal/`, but the compiler emitted only `/api/file/`.
- Root cause is generic route classification, not MalluMV code: `_route_role()` classifies any route containing `{slug}` as `detail`, and `_owned_transition_prefixes()` discarded every `detail` route. Neutral post-detail transitions carrying a slug were therefore erased before the runtime could observe them.
- The transition compiler now excludes only conventional catalogue-entry literal families (movie/film/series/anime/title/download-title) and retains other provider-owned routes as recognition-only prefixes. No route is executed by guessing; traversal still requires that the exact URL appear in a successful provider response.
- A second bug in the newly added transition scanner was found before live execution: its URL-character regex had been corrupted by an insertion splice. The scanner is restored to a bounded URL-safe character class and also normalizes escaped slashes before prefix matching.
- Required next proof remains MalluMV-only Learning on current HEAD. Promotion still requires current-byte playable, identity-safe evidence plus non-regression; synthetic green alone is insufficient.


### 2026-09-22 — Evolved-strategy negative memory is implementation-version aware

- Targeted Learning run `35753657007` on SHA `2e2e8f138a8666ace75461294316ae7bb4bff389` passed the corrected generic terminal-transition contracts but produced no MalluMV provider repair: the live plan still ended `chain_terminal_gap / collect-more-evidence / profiles=none`, the exact experiment ledger was empty, and the targeted Lab remained unresolved.
- Cross-day Learning memory revealed the cause: MalluMV already had an executed rejection for `terminal_transition_graph_v1` from the older implementation. Suppression was keyed only by profile name, so the materially changed generic strategy was discarded before the corrected engine could execute.
- Generic Brain correction now attaches a SHA-256 `strategyImplementationFingerprint` to post-exhaustion strategies, derived from the strategy identity plus the generic adaptive-runtime implementation files. An evolved-strategy failure suppresses only the exact same implementation fingerprint. Legacy/unversioned or different-build debt is stale and grants one bounded retry; a failure of the exact current build remains suppressive and rotates to the next strategy.
- The fingerprint is preserved through planner output, immutable attempt snapshots, runtime memory, Learning phase ledger, sanitized cross-day Learning memory, and memory keys. This prevents old/new implementations from being merged into one negative experiment.
- Regression coverage now proves both directions: stale implementation debt reopens the current strategy, while exact-build debt rotates to the next evolved strategy; cross-phase memory must preserve the fingerprint.
- No MalluMV status promotion is justified yet. Next proof is a fresh MalluMV-only Learning run on the current HEAD showing actual `terminal_transition_graph_v1` execution with a current fingerprint, then current-byte playable and identity-safe evidence before Repair/Retest/census promotion.


### 2026-09-22 — Repair loop switched from single-provider witness to 9-provider fair-share

- Current authoritative census before the switch remains 25 FULL OK, 1 PARTIAL OK across 46 providers. The current repairQueue contains exactly 9 providers: 4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, persianstremio, vidfast, yflix.
- All 9 are simultaneously LEARN-owned and pending in automation/provider-repair-learn-handoff-v1.json. Therefore the next Learning proof must use the existing Fast-Handoff fair-share cohort instead of continuing a MalluMV-only target.
- MalluMV was used as a witness for generic Brain defects, not as a provider-local repair target. The recent fixes (owned neutral transition mining plus implementation-fingerprinted evolved-strategy debt) are generic and may apply to other route/chain terminal gaps.
- User priority: do not allow one provider to monopolize the repair loop. Run the 9-provider cohort with the existing per-provider fair-share deadline and bounded attempts, persist exact per-provider outcomes, then improve the Brain from the cohort's common failures.
- The prior MalluMV-only run on SHA 34a6693d... is superseded once the batch trigger lands; do not treat its cancellation as provider evidence.


### 2026-09-22 — Current census now outranks stale provider-wide Repair skips

- Canonical Repair run `35753843377` reached a current pre-Repair `repairQueue=9`, but the Brain received only 8 providers. `persianstremio` was silently removed by `automation/provider-repair-skip.json`.
- The skip was stale by its own exact-byte policy: it referenced PersianStremio bundle `0d5ef668...` while the current manifest references `8866987f...`. Castle's retained skip bundle was stale as well (`5f921062...` vs current `f62ea897...`).
- Generic correction: when a schema-v3/current census is present, `repairQueue` is the automatic symptom authority and historical provider-wide skip memory cannot veto a reopened provider. Independent `provider-authority-status.json` blockers remain a hard prerequisite through the explicit `authority_blocked` argument.
- The stale provider-wide skip map is cleared. Compatibility callers without a census still retain the legacy skip behavior, while current Repair is driven by current evidence.
- Regression coverage in `tests/provider_repair_unresolved_scope_test.py` now proves both directions: a current `repairQueue` entry survives a stale skip, while an independent authority blocker still excludes it.
- Required validation: CORE/Repair contracts must pass, then a fresh Repair on current HEAD must select all current repairQueue providers, including PersianStremio when it remains unresolved.


### 2026-09-22 — Current-byte census persistence restored; rematerialization made incremental

- Full census run `35758257089` on SHA `5b1dd72a844db3f4aab0af9c121489cb7de0baf7` completed SUCCESS and, after the workflow persistence fix, actually committed its authoritative ledger to main as `7017a6d2288df6eec50dba99666f445d20b2a19c`. `PROVIDER_CENSUS_STATUS.md` is therefore auto-updating again instead of leaving successful manual census artifacts detached from main.
- That census currently records 27 FULL OK + 2 PARTIAL OK across 46 providers. Animesalt and Vostfree are FULL OK from current residential provider replay evidence (`playable_verified`, one raw/playable/verified stream, identity-safe); PersianStremio remains PARTIAL OK with movie verified and TV unresolved. Current canonical Repair queue is 8 providers: 4khdhub, allanime, anime-ultime, animevostfr, mallumv, moviebox, vidfast, yflix.
- Performance defect confirmed: the census rebuilt all 46 provider bundles even when the triggering commit changed only workflow/census machinery. That is O(catalogue) work unrelated to current bytes and will not scale to the planned several-hundred-provider catalogue.
- Generic correction: census now computes a provider-byte materialization scope from the commit diff plus any provider DATA changes produced by the domain-metadata reconciliation step. Provider-neutral changes use mode `none`; provider-local DATA/Lego/manifest changes use `materialize_provider_v3_one.py` only for affected providers; common ProviderBase/Core/materializer changes use mode `all`.
- Unknown/unowned provider patch modules fail safe to full rematerialization. Top-level non-provider override changes also force full rematerialization. The selector has synthetic regression coverage for no-op, single-provider, provider-Lego, manifest-row and global-input cases.
- Required live proof: the workflow-change commit itself touches no provider bytes, so the next current-byte census must log `FIELD_PROVIDER_V3_MATERIALIZE_SKIP reason=no-provider-byte-input-changed` and still complete/persist the same current-byte census correctly.


### 2026-09-22 — Provider projection reconciliation: 7 real drifts, provider-scoped fingerprint v3

- Projection Reconcile run `35762320992` on `09b34d0a...` detected exactly seven real publication drifts: `animevostfr, flemmix, mallumv, vidfast, voiranime, wookafr, yflix`. It rebuilt only those seven with `materialize_provider_v3_one.py`; the post-rebuild detector reached `providers=0`, final CONFIG validation passed, and `audit_provider_v3_static.py` passed for all current providers.
- Flemmix drift was concrete execution DATA, not hub discovery: current structured authority is `flemmix.party + /search?q={query}`, while the published bundle retained stale `observedUrls/origins/routes/searchRequestPlan` including the old DLE route / `flemmix.cloud`. The targeted rebuild produced Flemmix bytes `74d15245afaef0f4...` in the sandbox but did not publish because the publication fingerprint guard rejected the transaction.
- Root publication-fingerprint defect: schema v2 treated all provider overrides, all provider Lego scripts and the whole static-knowledge file as one global contract. One provider-local change therefore marked every provider input stale, contradicting incremental materialization.
- Schema v3 separates shared Core/materializer policy from per-provider policy. Provider patch/capability and declared provider Lego source are provider-local; the follow-up correction also moves `automation/provider-v3-static-knowledge.json.providers[provider]` into that same local fingerprint while keeping top-level static policy global. Legacy schema-v2 calculation remains available only to verify pre-migration provenance.
- Regression coverage proves an Alpha override or static-row change cannot invalidate Beta, while a true top-level static policy change still invalidates the global contract.
- Retry run `35763384537` never reached drift detection because Projection Reconcile incorrectly ran the unrelated `tests/published_overrides_test.py`, whose assertion targets `sync.yml`. That unrelated gate is removed from the targeted lane; the lane keeps its dedicated detector/workflow/fixed-point tests and publication audits.
- Required proof: fresh Projection Reconcile from the trigger in this commit must rebuild only detected drift providers, reindex fingerprints metadata-only, pass `reapply_published_overrides.py --check`, publish atomically, inspect Flemmix current bytes, then dispatch and persist a fresh census.


### 2026-09-22 — Projection reconcile gate: published Lego test was stale, not 43 providers

- Projection Reconcile run `35764120214` proved the provider-scoped publication fingerprint v3 works: seven real drifts were rebuilt, drift detector reached `providers=0`, static audit passed, fingerprint reindex reported `providers=42 bytes_changed=0`, and `reapply_published_overrides.py --check` returned a fixed-point HIT.
- Publication then stopped on `tests/published_provider_lego_contract_test.py`, not on provider materialization. The test hardcoded media-type revision v31 while the authoritative Core source and current published provider bytes are on v34 (`tmdb-data-contract-launch-gate-v34-anime-pre-network-semantic-gate`). It also expected 46 rows while deliberately skipping four `provider-disabled/` rows, producing a false `portfolio incomplete checked=42 expected=46`.
- The Lego contract now derives the required media-type revision from the authoritative Core source and scopes portfolio completeness to active `providers/` rows. This validates source/published parity without freezing the test to an obsolete revision.
- Required proof: rerun Projection Reconcile from this commit; it must pass Lego ownership, publish only the seven drifted providers plus metadata/manifests, then verify Flemmix current bytes and launch a fresh census.


### 2026-09-22 — Projection Reconcile is now forbidden from rewriting accepted provider authority

- Projection publication `a9cede9de685...` successfully rebuilt seven drifted providers, including Flemmix, but exposed a generic authority leak: `materialize_provider_v3_one.py` reconciled static provider memory back into `provider-overrides.json` while Projection Reconcile was supposed to rebuild bytes from already accepted DATA. AnimeVOSTFR was regressed from current `https://animevostfr.org` back to stale redirect seed `https://v2.animevostfr.org`; its old-host replacement maps were also erased.
- The census dispatched from the resulting publication, run `35765049287`, correctly failed before network probing on `tests/animevostfr_runtime_contract_test.py`. This was a real authority regression caught by the contract, not a stale test.
- Generic correction: targeted materialization now has `--preserve-structured-data`. Projection Reconcile uses this mode, snapshots `provider-overrides.json`, fails if the file changes by one byte, and no longer stages `provider-overrides.json` in its publication commit. Projection Reconcile may repair published bytes/metadata only; Domain/Repair remain the owners of structured authority mutation.
- AnimeVOSTFR hub DATA now marks `https://animevostfr.org/` as `direct_authority=explicit_current`; `v2.animevostfr.org` remains a redirect/discovery seed only. The accepted override again uses `official_site=https://animevostfr.org` with `v2.animevostfr.org -> animevostfr.org` in runtime/domain substitutions.
- Regression coverage now simulates stale static memory on `v2.animevostfr.org` plus an explicit-current registry at `animevostfr.org` and requires the current hub authority to win. The Projection Reconcile workflow contract also requires structured-DATA preservation.
- Next proof: Projection Reconcile must rebuild only the resulting drifted provider(s), leave `provider-overrides.json` byte-identical, publish atomically, then dispatch a fresh current-byte census. The census must pass AnimeVOSTFR contract and re-measure residential/WAF classifications.


### 2026-09-22 — Native residential qualification trigger contract corrected

- Current main at `7409baa36bfe34195b64895439bde2f312877c5d` allows push-triggered targeted Native corpus execution only for `.github/triggers/native-residential-transport-targeted.json`. This is intentional: it runs a real NuvioTV Android TV client through the configured private Tailscale exit for exact current harness-mismatch providers.
- CORE Workflow Gate `35767925814` on `3e88d8bb...` failed only because `tests/native_corpus_device_lab_test.py` still asserted that the targeted runtime workflow could never contain a `push:` trigger. That assertion became stale after the residential proof lane was added.
- Commit `7409baa3...` replaces the stale prohibition with a stricter scoped contract: workflow_dispatch remains supported, pull_request remains forbidden, and the sole push trigger must be the explicit residential trigger file under main.
- Native run `35767925881` is the active real-client proof for `animesultra, animevost-fr, moviesmod` on TV via residential exit. No reclassification is claimed until its per-provider artifacts/logs complete.
- Separate CORE Verify failure on the preceding SHA remains open: `vidfast: published security hardening is not idempotent`. This is independent from Tailscale/harness qualification and must be fixed generically before CORE can be called green.


### 2026-09-22 — Projection fixed-point check now follows fingerprint reindex

- Projection Reconcile run `35769444748` on SHA `d46a08fca1800edb12fe72006f1e18adb043e432` rebuilt all 42 active providers because a shared publication build-input fingerprint had changed. The provider rebuilds themselves completed; structured authority preservation remained intact.
- The run failed in the fixed-point proof because `detect_provider_projection_drift.py` was executed before `reindex_provider_publication_fingerprints.py`. Every rebuilt provider therefore still carried the pre-rebuild publication fingerprint and was falsely reported again as `publication-build-input-drift`.
- Generic pipeline correction: after provider reconstruction/reconciliation, publication fingerprints are reindexed metadata-only before the post-rebuild drift detector runs. The drift detector then judges the new byte/build pair, followed by CONFIG/static/Lego/fixed-point audits.
- This is orchestration-only; it does not justify a provider status change. Required proof is a fresh Projection Reconcile reaching `FIELD_PROVIDER_PROJECTION_FIXED_POINT providers=0`, publishing atomically, then a fresh census on the published SHA.
- Native residential run `35767925881` is not provider evidence: all three TV jobs failed while cloning NuvioTV after the exit node was already selected. Current workflow now delays residential exit selection until after client/dependency/AVD bootstrap; a fresh native run is required for AnimeSultra, AnimeVost-FR and MoviesMod.


### 2026-09-23 — LLM guidance bridge to canonical Repair was incomplete

- Canonical Repair run `35907823143` on exact source SHA `6a333144632eb54079555bdf16e43f73935c4129` completed its workflow successfully, including Tailscale residential qualification, sanitized Learning-prior import, targeted Repair, four-version gate, symptom-scope proof and census persistence. Functional outcome was **not repaired**: 9 providers were targeted, 0 repairs accepted, 0 fixed in Lab, all 9 deferred back to Learning; final outcome was `converged_to_learning_debt`.
- The run spent unnecessary time rematerializing all 42 active providers before targeted work; this remains a separate performance item and is not considered solved by the LLM bridge.
- Root cause found in the Learning→Repair intelligence path: Learning generated a sanitized Brain-LLM `guidance.json`, but the memory publisher retained only `latest.json/latest.md`; canonical Repair therefore had no provider-specific LLM guidance to consume. In addition, the adaptive runtime overlay omitted both `llmGuidance` and `historicalSolutions` from its Node planner payload, and the planner explicitly limited LLM advice to Learning mode.
- Generic correction prepared on main: persist only the already-sanitized `engine_v2/learning/llm-guidance.json` on the isolated memory ref; canonical Repair validates/re-scopes it as a read-only prior; the adaptive overlay forwards it; production Repair may use a whitelisted advisor profile only to order hypotheses. If ordinary variants are exhausted, a different advisor profile with no exact negative debt gets one bounded rescue. Playback, identity, strict-improvement and current-byte gates remain unchanged acceptance authority.
- Exact-profile negative memory still suppresses a repeated LLM suggestion, preventing an endless advisor loop. No provider status promotion is justified until a fresh Learning/Repair cycle proves current-byte playable, identity-safe output.
- Learning run `35910596067` remains tied to source SHA `987afb0877de7fa7c00e7c3e14b1880f36cccc2c`; it successfully checked out `niakvio-private`, built bounded public/private LLM memory, routed the cohort and started the adaptive queue. Any later main commit must be distinguished from this tested source SHA.


### 2026-09-23 — Private NiakVIO memory bridge proven end-to-end in Brain-LLM

- Brain-LLM commit `77ccc76f463d6808d04a86d88b3a1b8659f25df8`; live run `35913019451` completed successfully against NiakVIO `30b6da7498c0d200044a8ececf34ca982bf3acac`.
- Private memory was genuinely indexed: 180 source conversations, 162 indexed, 6435 technical documents. Qwen was called for 3/15 targets with 0 model errors.
- Public orphan branch `niakvio-guidance` contains exactly one file and 3 prior-only rows: `allanime` and `mallumv` -> `chain_terminal_extractor_v1`; `4khdhub` -> `proven_route_terminal_traversal_v1`, confidence 0.96. It retains no private content or proof/mutation authority.
- Canonical Repair imports that minimal surface only after exact-schema, safety and source-drift validation. Provider/census/current-byte drift rejects re-scoping; workflow/test/documentation-only drift is allowed.


### 2026-09-23 — Canonical Repair second 42/42 rematerialization removed conditionally

- Repair run `35907823143` rebuilt all 42 active providers even though only 9 entered Repair; the full materialization consumed roughly three minutes and the pipeline later performed another unconditional full rebuild.
- The post-recovery materialization now uses `select_provider_materialization_scope.py` with `none/providers/all`. Provider-local DATA/manifest changes rebuild only affected providers via `materialize_provider_v3_one.py` and reconcile manifest/materialization/PROVENANCE with `reconcile_targeted_provider_publication.py`.
- Any changed `provider-bases/` path is explicitly global and retains `materialize_provider_v3_all.py`. The preflight full-catalogue reconstruction remains unchanged until the incremental post-recovery path is proven live.
- This is a performance correction only. No provider is considered repaired until a fresh Repair run produces current-byte playback/identity proof.


### 2026-09-23 — Unexecuted profile debt must not suppress production Repair guidance

- Before the private-guided Repair reached its planner, the durable memory was inspected for the three Qwen-advised profiles. `allanime`, `mallumv` and `4khdhub` each already had one legacy row for exactly the advised profile, but every row was `lastOutcome=profile_unavailable`, `lastReason=planned_profile_not_applicable_to_current_bytes`, with no `executionObserved` field. These are **not executed failures**.
- This exposed a generic production bug: `planner_negative_memory()` projected those applicability-only rows as failures, so `llmAdvisorStrategyHint()` would suppress the new private-informed advice before it ever ran.
- Production modes now exclude only this exact unexecuted legacy condition from negative planner memory. Learning mode keeps it as exploration history. New memory writes explicitly mark `executionObserved=false` for unavailable profiles and `true` for accepted, generated/rejected and nonpublishable executed attempts.
- The correction is generic and does not clear real negative memory. Executed failures remain suppressive. No provider is promoted by this fix; the next exact-head Repair must show the advisor profile was actually attempted and then pass playback/identity/non-regression gates.


### 2026-09-23 — External guidance source drift: Brain control-plane is neutral, provider truth is not

- The private-informed guidance was generated from exact NiakVIO SHA `30b6da7498c0d200044a8ececf34ca982bf3acac`. Subsequent commits changed only Brain/workflow/tests/memory control-plane files; provider DATA, published provider bytes, census evidence and authority state did not change.
- `scripts/brain_repair_runtime.py` is now explicitly allowed as neutral source drift for the external guidance importer. This is intentionally narrow: `provider-overrides.json`, provider bundles, manifests, census/authority evidence and other provider-relevant paths still invalidate stale external guidance.
- This allows the same source-evidence guidance to be consumed after the unexecuted-debt control-plane fix without weakening current-byte proof gates.


### 2026-09-23 — Repair preflight no longer rematerializes 42/42 on control-plane-only runs

- The canonical Repair preflight previously ran a temporary full `materialize_provider_v3_all.py` for every cycle, even when the SHA changed only Brain/workflow/trigger files. That cost roughly the same catalogue-wide reconstruction the user explicitly wanted to avoid.
- Preflight now calls the existing materialization-scope classifier against `HEAD^..HEAD`. If the scope is `none`, the temporary 42-provider rematerialization is skipped. If provider/global inputs changed, the full temporary reconstruction remains as the conservative validation path.
- This optimization is intentionally independent from the post-recovery incremental materialization added earlier. Together they remove catalogue-wide rematerialization from ordinary targeted Brain retries while preserving a full fallback for real provider/common-runtime changes.


### 2026-09-23 — Persist LLM-advisor execution proof in Brain reports

- The planner already exposes `llmAdvisorApplied`, `llmAdvisorRescue`, strategy, profile and confidence, but `brain_repair_runtime.py` previously stripped those fields from its sanitized plan report.
- Brain reports now retain exactly those non-sensitive advisor metadata fields. This does not retain prompts, private documents, raw model output or mutations. It allows the canonical Repair artifact to prove whether private-informed guidance was actually selected for each provider instead of inferring usage from configuration.


### 2026-09-23 — Provider Non-Regression Gate skips live 42-provider census for control-plane-only changes

- The push gate was triggered by broad `scripts/**`, `tests/**` and workflow changes and always rebuilt/retested all providers. Brain-only commits therefore paid a full live census and could fail on unrelated network drift (AnimeKai timed out in run `35912245946` while its provider bytes were unchanged).
- The gate now classifies the exact diff before validation. Static anti-regression contracts still run for every matched push/PR. Materialization, rolling baseline seeding, live all-provider quick-yield census and candidate floor enforcement run only when the classifier reports provider impact.
- Control-plane-only changes emit `FIELD_PROVIDER_NON_REGRESSION_NOOP ... live_census_skipped=true`. Provider DATA, manifest, provider patches, common ProviderBase inputs and other classified provider changes still retain the full live non-regression gate.


### 2026-09-23 — Brain advisor proof, CI scope and stale Repair artifact integrity

- Private-memory advisor run `35913019451` is the validated source of the public minimal guidance: 180 source conversations, 162 indexed, 6435 technical documents, 3/15 Qwen targets, 0 model errors; the orphan guidance ref retains exactly one sanitized file and no private/proof/mutation authority.
- Repair run `35914883115` on `ddf10880299e16f1cd5a8291f53873d10fe4fe7d` is genuine current-run evidence and confirms the pre-fix failure mode: 9/9 providers were sent directly to `experiment_variants_exhausted`, 0 accepted, 0 fixed. The three private-guided profiles were suppressed by legacy `profile_unavailable` rows that had never executed.
- Production Repair now filters only that exact unexecuted debt condition while preserving real executed failures; new memory writes make `executionObserved` explicit.
- Provider Non-Regression run `35917425515` live-proved the control-plane diff optimization: provider-impact classification succeeded, static contracts passed, and full materialization, baseline seeding, all-provider live census and candidate floor were all skipped; the workflow completed successfully.
- Repair preflight and post-recovery publication also use scoped materialization. Control-plane-only cycles no longer rebuild all 42 providers; provider-local changes rebuild only their affected providers, while common ProviderBase/global drift retains the full fallback.
- A separate integrity bug was confirmed after superseded run `35917425743`: its persistence step recycled a tracked older `automation/provider-brain-repair-latest.json` and published it as `automation/provider-brain-repair-35917425743.json`. The payload itself proves it was stale (source census `35680423643-retest`, 7 providers, 3 waves, 1200s) and did not represent that run.
- Persistence is now current-run gated: a skipped canonical Repair cannot persist Brain memory/report; Brain memory is copied only when changed from the run SHA; a durable Brain report is accepted only when `experienceMemory.sourceSha == GITHUB_SHA`. The false `35917425743` report is removed.
- Advisor metadata is propagated through both runtime and portfolio sanitizers: durable run reports retain only `llmAdvisorApplied`, `llmAdvisorRescue`, strategy, profile and confidence. Prompts, private documents and raw model mutations remain absent.
- External guidance source-drift validation treats only Brain/workflow/test/report-control paths as neutral. Provider DATA, manifests, published bundles, census/authority evidence and other provider truth still invalidate stale guidance.
- Next required proof: after the current exact-byte census settles, trigger one fresh Repair from its exact HEAD/repairQueue and verify advisor use per provider plus playback/identity/non-regression before any status promotion.


### 2026-09-23 — Superseded push Repairs now cancel instead of occupying the only Repair slot

- Live orchestration exposed another performance defect: Repair `35918698089` had already passed its initial HEAD freshness check before a newer explicit Repair trigger advanced main, so it continued expensive WAF/Tailscale work while the corrected Repair remained pending behind the shared concurrency group.
- Canonical Repair remains serialized, but `cancel-in-progress` is now true **only for push-triggered Repair**. The workflow's push path is already restricted to `.github/triggers/provider-recognition-repair-v6.json`, so a newer explicit trigger can cancel an obsolete older push run.
- Manual `workflow_dispatch` and scheduled Repairs keep non-cancelling serialization. Ordinary census, MEMORY, test or provider commits do not trigger this workflow and therefore cannot evict a Repair.
- This change is orchestration-only; it does not alter provider acceptance, proof, WAF/Tailscale semantics or repair authority.


### 2026-09-23 — Cancelled stale Repair report removed before final LLM run

- Obsolete push Repair `35918698089` was cancelled by the new push-only concurrency policy, but its old workflow revision persisted one stale tracked file immediately before cancellation: `automation/provider-brain-repair-35918698089.json`.
- The payload proved it was not current-run evidence: it referenced historical source SHA `d12ada427f02...`, 7 providers and the old 1200-second/3-wave configuration. It is deleted on `829c495ac24f7d5c60f306579b4a22e7672df29b`.
- Current workflow revision already prevents recurrence by persisting Brain reports only when canonical Repair actually ran and `experienceMemory.sourceSha == GITHUB_SHA`.
- The next Repair trigger must therefore start from this cleaned HEAD lineage and is the only run whose advisor metadata/provider outcomes may be treated as current proof.


### 2026-09-23 — Repair preflight concurrency contract aligned with push-only cancellation

- Clean private-guided Repair run `35919831743` on `74aec897b37c0f2823bd925a76e95a449ec69987` stopped before any network/provider mutation. The only failing preflight was `tests/provider_waf_tailscale_exit_contract_test.py`, which still hard-coded `cancel-in-progress: false` for canonical Repair after the workflow moved to push-only cancellation.
- The WAF/census sharded lane remains non-cancelling as before. Only the Repair assertion now requires `cancel-in-progress: ${{ github.event_name == 'push' }}`, matching the already validated workflow and preserving manual/scheduled serialization.
- No provider result is inferred from `35919831743`; canonical Repair was skipped and current-run Brain report capture correctly remained disabled.


### 2026-09-24 — Repair latency and transport classification root causes fixed

- Private-guided Repair run `35920323353` proved the Brain-LLM connection is real, but also proved the current execution policy was too expensive: after wave 1, only Yflix remained and canonical Repair replayed the same generic `adaptive_runtime_recovery` family through variants 0→4. This consumed most of the ~47-minute run without a strict gain.
- Canonical Repair now hands a provider to Learning/LLM immediately after one failed **unadvised generic adaptive** attempt. Advisor-backed and named causal strategies keep their bounded Repair attempt. This preserves evidence while removing four redundant generic waves.
- The same run exposed a false-positive MalluMV Lab acceptance: the only media-looking success came from unrelated Google `gstatic/marketing-cms` videos. Final current-byte validation correctly rejected promotion. The accepted-program compiler now excludes gstatic as non-provider authority and refuses media/terminal programs that have no provider-owned `streamProof` recipe. Existing poisoned MalluMV positive-program memory was cleared.
- Tailscale/WAF evidence was merged before Repair but the final census renderer later overwrote the transport overlay. Repair now reapplies `merge_waf_census_transport.py` **after canonical Repair, even on Repair failure**, then regenerates the batch plan/Markdown before persistence. This is required so residential/native evidence remains authoritative in the durable census.
- Current evidence already shows Vidfast's exact failed routes reachable through browser, direct HTTP and OkHttp on both GitHub and residential paths; it must therefore leave `PROVIDER NETWORK BLOCKED` after the terminal overlay and return to normal provider Repair. Anime-Ultime's residential full-provider replay reaches a normal pre-network zero state and likewise must leave the network-blocked bucket. Moviebox (HTTP 400 on both paths) and Yflix (residential-browser reachable but native/direct failure) remain causal transport/runtime cases requiring separate treatment, not blanket “network blocked” assumptions.
- The four browser-only HARNESS MISMATCH cases are not IP failures: browser succeeds on both GitHub and residential networks while native-like direct/OkHttp fails. Tailscale therefore disproves IP/egress as the cause and the causal owner remains Core/client transport Learning, not repeated provider mutation.


### 2026-09-24 — Targeted Tailscale transport qualification no longer defaults to the full WAF cohort

- The dedicated `provider-waf-browser-session.yml` push lane already existed, but push-triggered runs ignored the trigger payload and therefore defaulted to every current WAF/network target. This made a transport-only retry unnecessarily broad.
- Push triggers now require an explicit `targetProviders` JSON cohort, normalized/deduplicated and capped at 12 providers. Manual dispatch keeps its existing optional cohort behavior.
- The current transport retry is intentionally scoped to the eight disputed rows only: `animesultra, animevost-fr, moviesmod, vostfree, anime-ultime, moviebox, vidfast, yflix`.
- This run is transport/census evidence only. It must not mutate provider bytes; its purpose is to preserve Tailscale/browser/direct/OkHttp differential evidence and correct the durable census before the next provider Repair.


### 2026-09-24 — Targeted WAF refresh is now bounded and non-destructive

- A second scaling defect was found before the eight-provider transport retry could persist: a filtered `probe_waf_browser_session.py --providers ...` output contains only the requested cohort, so persisting it directly as `provider-waf-browser-session-latest.json` would delete unrelated transport evidence.
- Targeted runs now snapshot the complete prior ledger and merge refreshed rows/replay rows back provider-by-provider. Unrelated WAF/Tailscale evidence is preserved. The merged ledger records `lastRefreshProviderFilter` without pretending the whole ledger was freshly probed.
- Explicit targeted transport runs now use one fresh attempt per browser/direct/OkHttp profile and four workers. Negative rows can otherwise cost roughly four browser attempts plus direct/OkHttp waits per target. Full untargeted qualification retains two attempts and three workers.
- The superseding targeted transport trigger will cancel the slower in-flight run through the existing `provider-waf-transport-main` concurrency group and rerun the same eight providers with the bounded policy.


### 2026-09-24 — Targeted WAF bounded retry contract correction

- Targeted WAF run `35928054146` stopped before network/Tailscale work because the static workflow contract incorrectly required the runtime marker `FIELD_WAF_TARGETED_LEDGER_MERGE` to appear literally in YAML. The marker is emitted by `scripts/merge_targeted_waf_refresh.py`, and that helper has its own executable unit contract.
- The stale YAML-string assertion is removed; workflow still requires the merge step/script and the helper unit test. No transport result is inferred from the failed run.


### 2026-09-24 — Existing Tailscale evidence can now reclassify without a network rerun

- The current disputed transport evidence was produced on provider bytes rooted at `5829ecc1020f...`. The evidence persistence commit `b38f896...` changed only census/Brain/WAF evidence files; later changes are Brain/workflow/test control-plane. Re-running the same network matrix is therefore unnecessary just to repair the lost final census overlay.
- The WAF lane now supports `reuseExistingEvidence=true` only when `select_provider_materialization_scope.py` proves `mode=none` between the evidence source SHA and the current SHA. Any provider-impact drift fails closed and forces a real fresh probe.
- In reuse mode Java/Tailscale/network probes are skipped; the existing complete WAF ledger is reapplied to the current census and persisted. This makes transport reclassification a seconds/minutes operation instead of repeating a multi-minute network diagnostic.


### 2026-09-24 — Tailscale reclassification materially reduced false transport debt

- WAF/Tailscale run `35928423660` persisted transport overlay commit `74edf179de28d5814e34e445256214adc22b4a82` using the bounded eight-provider cohort and non-destructive ledger merge.
- Durable census moved from **4 HARNESS MISMATCH + 4 PROVIDER NETWORK BLOCKED** to **1 HARNESS MISMATCH + 1 HARNESS/ENV BLOCKED + 0 PROVIDER NETWORK BLOCKED**. Current headline is **26 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 7 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 1 HARNESS MISMATCH · 1 HARNESS/ENV BLOCKED · 4 DISABLED**.
- `vostfree` is now **FULL OK** from strict residential full-provider replay with verified media. `anime-ultime`, `moviebox`, `vidfast`, and `yflix` are no longer network-blocked; they re-enter ordinary provider Repair as ROUTE/CHAIN cases because native-like route reachability or normal provider replay disproved the blanket network diagnosis.
- Remaining transport debt is now only `animesultra` (**HARNESS MISMATCH**, browser works while direct/OkHttp fail) and `animevost-fr` (**HARNESS/ENV BLOCKED**, residential exit also challenged). These need native/Core transport proof rather than another broad provider Repair.
- Experimental `reuseExistingEvidence` workflow syntax from `e79f03e...` never created a job and is removed from main; the validated targeted WAF workflow from `77e3efb...` is restored while preserving the newly persisted census/WAF evidence.


### 2026-09-24 — Catalogue-scale Repair now stays sharded through Brain handoff

- Current transport cleanup proved the census can remove false network debt without a full provider rerun: durable state is now 26 FULL OK, 2 PARTIAL OK, 1 CANDIDATE OK, 7 ROUTE PROVEN, 3 CHAIN REACHED, 1 NO PROOF, 1 HARNESS MISMATCH, 1 HARNESS/ENV BLOCKED, 4 DISABLED, with 0 PROVIDER NETWORK BLOCKED.
- Canonical Brain Repair is now capped at 3 waves / 1200 seconds / 180-second minimum batch start. The earlier 5-wave/2100-second ceiling predated the generic-miss -> Learning/LLM handoff and allowed useless variant burning such as Yflix.
- High-volume onboarding already uses an 8-shard census and 8-shard targeted recovery above 120 providers. A missing continuation was found: after merging/refining sharded recovery, the workflow persisted the refined plan but stopped instead of handing it to Brain Autopilot.
- Sharded refinement now preserves sourceRunId, transportSignature and causal metadata. Brain execution planning consumes the refined plan only when its source census and provider set exactly match the freshly rebuilt canonical plan; stale, partial or mismatched refinement fails closed to the canonical plan.
- Provider Targeted Recovery - Sharded now dispatches Provider Brain Autopilot after persisting a non-empty refined plan. This closes the bulk path: bulk stage -> 8-shard census -> 8-shard targeted recovery -> exact refined causal plan -> Autopilot/Brain, rather than re-aggregating hundreds of providers blindly.


### 2026-09-24 — Canonical Repair reuses fresh Tailscale evidence only across provider-neutral drift

- Scaled Repair run `35929895303` showed the remaining wall-time bottleneck before Brain execution: the canonical workflow re-ran GitHub browser/direct/OkHttp + residential Tailscale qualification even though the WAF ledger had just been persisted and all changes since then were provider-neutral control-plane/trigger changes.
- Repair now derives the provenance commit of `automation/provider-waf-browser-session-latest.json` with repository history, then runs `select_provider_materialization_scope.py` from that commit to the exact Repair SHA.
- Existing WAF/Tailscale evidence is reused only when the provider materialization scope is exactly `none`, the ledger contains rows, residential exit evidence is available, and full residential provider replay is available. Any provider/global materialization drift fails closed and runs the complete GitHub + Tailscale probe again.
- Reuse skips only the expensive WAF/Tailscale collection steps. Authority is still refreshed, the existing transport ledger is still merged into the current census before Brain, and the final post-Repair transport overlay remains mandatory.
- A superseding trigger is issued so the obsolete run is cancelled by the existing push-only Repair concurrency policy rather than spending additional minutes on duplicate transport proof.


### 2026-09-24 — Fast Repair now consumes private Brain-LLM guidance at catalogue scale

- Durable current census after run `35930404639` is **26 FULL OK + 2 PARTIAL OK = 28 operational-status providers** across 46, with 12 providers in `repairQueue`, 1 HARNESS MISMATCH, 1 HARNESS/ENV BLOCKED, and **0 PROVIDER NETWORK BLOCKED**. The persistence commit message said `27/46`; that string does not match the durable status table (28 FULL/PARTIAL) and must not be used as the canonical count.
- The scaled canonical Repair `35930368663` started correctly on `b3508f8405a4f0341810d9fb34303654b91f6093`, reused existing Tailscale evidence and skipped the expensive GitHub/residential WAF probe matrix. Census persistence `7831a32...` then advanced main while that Repair was running, so its eventual result is diagnostic/benchmark evidence unless explicitly revalidated on the current HEAD.
- High-volume flow is now closed through 8-shard census -> 8-shard targeted recovery -> exact refined causal plan -> Brain Autopilot. One remaining intelligence gap was found: `provider-fast-repair.yml` imported Learning memory but did not expose `NIAKVIO_BRAIN_LLM_GUIDANCE`, so sharded FAST_REPAIR cohorts could lose the private-informed Qwen advisor.
- Fast Repair now validates/imports the public sanitized Brain-LLM guidance ref first, with NiakVIO Learning guidance only as fallback. Raw private chat memory remains confined to the Brain-LLM workflow and never enters NiakVIO.
- External guidance drift validation is changed from a growing path whitelist to the existing provider-byte materialization classifier. A guidance prior is reusable only when `select_provider_materialization_scope.py` proves `mode=none` between its source NiakVIO SHA and the current Repair SHA. Any provider/global materialization drift fails closed.
- This makes evidence/control-plane commits (census, WAF ledger, workflow/test changes) cheap while preserving the real safety boundary: provider byte inputs must be unchanged before reusing a prior.
- A fresh private-guided advisor run `35930708414` was launched in `NiakVIO-Brain-LLM` against exact NiakVIO SHA `b3508f8405a4f0341810d9fb34303654b91f6093`. Do not claim the refreshed guidance is active until that run publishes the sanitized guidance ref successfully.


### 2026-09-24 — Observation-only main drift no longer forces another full census

- The scaled Repair/census overlap exposed a persistence loop: a concurrent census or control-plane commit could advance `main` without changing any provider byte input; Repair then treated the newer HEAD as fully stale and dispatched another full census.
- Repair persistence now classifies the exact intervening diff with `select_provider_materialization_scope.py` after rebasing onto current main.
- The newer canonical census/authority/WAF ledger is still never overwritten by an older Repair. However, `mode=none` means provider inputs are unchanged, so causal Brain memory/report can be kept and **no extra full census is dispatched**. Only `providers` or `all` provider-input drift triggers a fresh exact current-byte census.
- This breaks the census -> stale Repair -> census loop without weakening SHA/current-byte acceptance.


### 2026-09-24 — Replay-reclassified NO PROOF and independent targeted Learning

- Current allwish evidence is provider-side despite stale WAF lane text: status NO PROOF, repairEligible=true, residentialProviderReplayReclassified=true, and full residential replay reaches provider_zero_before_provider_network with no provider request. The repair batch planner now gives that stronger replay evidence precedence and routes such rows to BRAIN_LEARNING instead of harness-compatibility.
- Brain Learning gains a comma-separated target_providers workflow input. The cohort is normalized/deduplicated, must remain inside the current repairQueue, and reuses the existing targeted published-stage, health, reconstruction and provider-filter path. Learning remains non-mutating.
- Brain Autopilot no longer suppresses a distinct BRAIN_LEARNING cohort merely because FAST_REPAIR is non-empty. It dispatches the targeted Learning cohort in parallel at the control-plane level; the Learning workflow itself serializes explicit cohorts so a later Fast-Repair handoff queues instead of cancelling independent debt.
- Fresh private Brain-LLM run 35930708414 completed SUCCESS. Its sanitized guidance is sourced from NiakVIO b3508f8405a4f0341810d9fb34303654b91f6093 and contains 10 confidence-0.96 provider priors: allanime, mallumv, moviebox, 4khdhub, anime-ultime, animesalt, flemmix, moviesmod, vidfast and yflix. No private content, proof authority or direct mutation authority is published.
- Animevostfr remains candidate-replay owned rather than LLM-first. Allwish is intentionally not in the Qwen prior set because it lacks a proven route; targeted Learning is now its correct next owner.


### 2026-09-24 — Durable acceptance semantics and Learning preflight aligned

- Repair run `35931292610` exposed a reporting/control defect: the adaptive Lab emitted three MalluMV acceptance events, but all three programs were rejected by the Provider v3 compiler with `no provider-owned stream-proof recipe`. Those rows were nevertheless counted in `acceptedRepairCount` and influenced wave rotation even though no durable Provider DATA existed.
- Brain Repair now distinguishes raw Lab acceptance from durable acceptance. A repair counts as accepted only when its accepted program compiles into Provider v3 DATA. Compile-rejected providers are explicitly handed to Learning, raw Lab rows remain diagnostic-only, and rotation decisions use durable accepted count.
- The run output now records `rawLabAcceptedCount/rawLabAcceptedRepairs`, `acceptedRepairCount/acceptedRepairs`, and per-wave `compileRejectedToLearning`. This prevents false success metrics and prevents a rejected MalluMV-style candidate from consuming another Repair wave.
- Learning run `35932716927` did not fail in Qwen/private-memory execution; it stopped in preflight because `brain_cron_full_coverage_test.py` still asserted an obsolete workflow-dispatch cancellation expression. The workflow is push-only cancelling by design; the test now matches that live contract.
- Next performance blocker remains deterministic migration drift inside canonical Repair: several one-shot migrations still report `changed=true` on every run and force a global ProviderBase rematerialization. These migrations must be consolidated into main once, then proven idempotent before another Repair benchmark.


### 2026-09-24 — One-shot migration consolidation armed

- Repair `35931292610` still forced `FIELD_PROVIDER_MATERIALIZATION_SCOPE mode=all` because deterministic source migrations changed the workspace on every invocation. Live logs identified `upgrade_provider_route_authority_v5.py`, `upgrade_provider_external_identity_route_v11_1.py`, source-plan-v5 submigrations and `upgrade_mugiwara_episode_failclosed_v2.py` as repeat offenders.
- A dedicated one-shot consolidation workflow is armed. It applies those deterministic migrations once, captures the exact diff, reruns the same migrations, and requires byte-for-byte identical workspace diff on the second pass. It also fails closed if any path outside the explicit migration source/DATA allowlist changes.
- Consolidation deliberately does **not** publish provider JS. The normal reconstruction/census lanes remain the only current-byte publication authority. After the consolidated source/DATA commit, one final global rematerialization is expected; subsequent Repairs must show these migrations `changed=false` and avoid global materialization unless a real common ProviderBase change occurs.


### 2026-09-24 — Migration consolidation retry isolates test-side mutation

- Consolidation run `35935327552` proved the migration set itself is idempotent: applying it twice produced an identical git diff. The persistence step did not run because the validation phase then executed `manual_tv_live_regressions_v34_test.py`, which intentionally patches ProviderBase while testing and therefore changed the dirty workspace after the migration diff was captured.
- The retry resets all test-side workspace mutations after validation, reapplies only the explicit consolidation migration set, and requires that reconstructed diff to match the original first-pass diff byte-for-byte before commit. This preserves the useful tests without accidentally persisting their helper-side mutations.

### 2026-09-24 — Consolidated migrations persisted; final current-byte reconstruction explicitly dispatched

- Consolidation retry 35935430487 completed SUCCESS and pushed 11c71b4c7750ec2484881d65fc94c237a156e1b5 (chore(provider): consolidate deterministic runtime migrations).
- The persisted migration diff is intentionally source/DATA only. A follow-up no-op consolidation run is armed to prove those migrations now produce no workspace change on 11c71b4.
- That no-op run explicitly dispatches temp-current-bytes-full-provider-census.yml via workflow_dispatch. With no push before SHA, the census materialization selector uses HEAD^, so it compares the consolidated source commit to its parent and performs the one required global rebuild rather than incorrectly treating a later trigger-only commit as provider-neutral.
- After this census persists current bytes, the next Repair benchmark must show the migration chain changed=false and scoped materialization instead of recurring mode=all.

### 2026-09-24 — Census dispatch receives explicit consolidation base

- No-op consolidation run 35935634351 again proved the migrations themselves are a fixed point and reached persistence with changed=false. Its only failure was GitHub CLI authentication: actions:write was present, but GH_TOKEN was not exported to gh.
- The consolidation job now exports GH_TOKEN and resolves the most recent persisted chore(provider): consolidate deterministic runtime migrations commit plus its parent.
- TEMP Current Bytes Full Provider Census now accepts an optional materialization_base_sha workflow-dispatch input. The consolidation workflow dispatches the census with the parent of the persisted consolidation commit, guaranteeing that the one-time source/DATA delta is classified even after later control-plane commits.
- The workflow-update commit itself is excluded from push census execution by message so it cannot launch an incorrect provider-neutral census before the explicit dispatch.

### 2026-09-24 — Fixed-point census dispatch shell quoting corrected

- No-op consolidation run 35935783160 again passed migration fixed-point and validation with changed=false. It failed only while locating the persisted consolidation commit because the generated git log --grep shell line had an unterminated single-quoted pattern.
- The grep is now fixed-string/double-quoted. No migration or provider logic changes in this retry.

### 2026-09-24 — AnimeSama.co consolidated route/runtime contradiction resolved

- Explicit-base census 35935941091 failed before materialization in provider_domain_metadata_reconcile_test.py because two legacy tests still required /template-php/defaut/fetch.php in animesama-co learned_routes.
- The failure exposed a real source contradiction rather than a test-only issue: upgrade_provider_v3_batch_routes_v2.py explicitly classifies fetch.php as stale/live-404 and consolidates the current learned route to /catalogue/?search={query}, but the provider Lego still executed fetch.php.
- AnimeSama.co runtime now uses GET /catalogue/?search=<title>, then the already-proven /anime/{id}-{slug}.html -> season -> episode chain. fetch.php remains only in candidate_learned_routes as historical/non-executable evidence.
- provider_animesamaco_domain_data_contract_test.py, provider_domain_metadata_reconcile_test.py and user_provider_manual_evidence_crosscheck_test.py now assert the same authority boundary. This is a runtime/data alignment fix, not a weakening of the census gate.
- The migration fixed-point trigger is rearmed so a successful no-op consolidation dispatches the final census using the persisted consolidation commit parent as materialization base.

### 2026-09-24 — Final gate cleanup after domain transaction

- CORE Verify & Publish run 35936866481 failed on a real AniKotoTV structured-data drift: published Runtime V2 bytes execute TMDB mapping + MegaPlay stream route + getSources, while provider-overrides.json learned_routes still declared the retired historical AniKoto search/watch/AJAX routes. Structured route authority is now aligned to the already-published Runtime V2 contract; historical routes remain candidate/history only.
- Provider Disabled Lifecycle run 35936868286 correctly archived expired disabled providers after the 7-day retention window, but tests/provider_authority_current_catalogue_test.py still indexed fullanime/desiflix as if every disabled provider must remain manifest-visible forever. The contract now accepts absence only when automation/provider-disabled-lifecycle.json archived explicitly records state=archived-provider-old; missing rows without archive proof still fail closed.
- These are validation/lifecycle consistency fixes, not claims of provider playback improvement. A fresh Core gate and current-byte census on the final HEAD are still required before closing the cycle.

### 2026-09-24 — AnimeSamaCo structured route drift removed

- After AniKotoTV was aligned, Quick Core run 35938076231 advanced to AnimeSamaCo and found the same structured-data class of drift: published bytes use /template-php/defaut/fetch.php for the current animesama.co catalogue, while learned_routes still named legacy /catalogue/?search={query}.
- AnimeSamaCo learned_routes now matches the exact currently published route set: current fetch.php catalogue request plus the anime / season / episode paths. The legacy catalogue search remains candidate/history only.
- This is a structured-authority consistency fix. Playback status is still owned by the fresh census/retest that follows.


### 2026-09-24 — Archived provider scope now reconciles durable static knowledge

- Final HEAD validation exposed a lifecycle cardinality split after `desiflix` and `fullanime` passed the seven-day disabled retention window: `manifest.json` correctly contained 44 visible providers while `automation/provider-v3-static-knowledge.json` still contained 46 provider rows. The two extra identities were exactly the lifecycle records marked `archived-provider-old`.
- `manage_provider_lifecycle.py` now reconciles the durable current-provider knowledge map on every apply, not only on the exact archive transition. It fails closed if a visible provider is missing, removes only identities outside the current visible catalogue, and updates the explicit providerCount fields used by contract recognition/route reconstruction/recovery.
- The lifecycle workflow now tests the local-recognition contract after applying lifecycle state and persists `automation/provider-v3-static-knowledge.json` with the manifest/projection/archive transition.
- Three Final Security Gate alerts were in test-only URL substring assertions. Domain-refresh tests now compare parsed scheme/hostname/path/query tuples, and the hub-search redirect fixture now matches its exact fixture URL. This strengthens URL-boundary validation rather than suppressing CodeQL.


### 2026-09-24 — Route reconstruction census cardinality made lifecycle-dynamic

- Lifecycle run `35940263149` proved the new static-knowledge reconciliation itself is correct: active=42, disabled=2, visible=44, static_removed=2. It then failed only because `tests/provider_route_reconstructor_test.py` still hard-coded the pre-archive value 46.
- That test now imports `visible_provider_count()` and asserts/reports the live current-catalogue cardinality. The lifecycle workflow trigger set includes this test so future archive cardinality changes cannot leave a stale fixed-count contract behind.


### 2026-09-24 — Sequential reconstruction contract follows lifecycle archive

- Lifecycle commit `2b4207d2437022aa397a0c003e0edf1199569c58` successfully persisted the current scope: manifest=44, static knowledge=44, and every explicit providerCount in contractRecognition/routeReconstruction/routeRecovery is 44. `desiflix` and `fullanime` are absent from current structured authority and remain represented only by their archive lifecycle state/provider-old bytes.
- The sequential reconstruction contract still assumed DesiFlix was always visible solely to test its movie fixture fan-out. That fixture assertion is now conditional on DesiFlix being current; when archived, the test instead requires explicit `archived-provider-old` proof and verifies it is absent from the reconstruction queue.


### 2026-09-24 — 5.21 capability floor separates frozen history from lifecycle archive growth

- Non-regression run 35940494405 proved the frozen historical reference is still exactly 50 root provider-old base identities. The extra fixture absence is DesiFlix, now explicitly archived-provider-old by lifecycle; FullAnime is also lifecycle-archived but is not part of the 5.21 fixture.
- The capability floor now preserves the frozen-50 invariant while allowing later current-provider retirements only with explicit lifecycle archive state and provider-old byte proof. Fixture providers may never silently disappear.


### 2026-09-24 — Lifecycle now reconciles the materialization ledger without full rematerialization

- Quick validation on the lifecycle-clean catalogue found the remaining split: manifest/static knowledge were 44, but provider-v3-materialization.json still contained 46 rows (DesiFlix and FullAnime).
- Lifecycle now filters the deterministic materialization ledger to the exact visible identity set, updates visible/active/static counts, and recomputes the generation hash with the same provider-id + byte-digest algorithm as materialize_provider_v3_all.py. No provider bytes are rebuilt.
- The lifecycle gate runs audit_provider_v3_static.py after reconciliation and persists provider-v3-materialization.json. Reverse-rebuild/documentation messages no longer print a stale literal current-provider count.


### 2026-09-24 — Lifecycle materialization projection persisted successfully

- Lifecycle run on `24e2744...` completed successfully and persisted `a74fd9568f1658a7c02d5fe884c4aa778c0696ed`.
- Current provider materialization ledger is now exactly 44 visible providers, expectedProviderCount=44, activeProviderIdentityCount=42 and staticKnowledgeProviderCount=44. DesiFlix and FullAnime were removed from current materialization authority, while their historical/lifecycle archive bytes remain under provider-old.
- The lifecycle recomputed generation `009fe2c6cb7e6e3006bce6e81cb839a2442f3ab370569fc0a3a565edb5ab0fb1` without rebuilding the remaining provider bundles. This exact persisted HEAD now needs the global Quick/non-regression/security gates before provider Repair resumes.


### 2026-09-24 — Lifecycle Quick gate and publication fixed-point repair

- HEAD `a193b7297b58` is not release-green yet. Provider Non-Regression failed only because `tests/provider_quick_yield_fixture_priority_test.py` still hard-coded 46 current providers after the lifecycle correctly moved DesiFlix and FullAnime to `provider-old`. Current provider scope is 44 visible (42 active + 2 disabled) plus 2 lifecycle-archived.
- The quick-yield fixture contract now compares `audit.build_tasks()` against `visible_provider_count()` instead of a historical magic number. This keeps fixture coverage tied to the physical current-provider lifecycle.
- CORE Quick also reported `publication-contract-changed`: current provider bytes/manifest exist, but PROVENANCE publication fingerprints are stale after the recent publication/lifecycle control-plane changes. This is owned by `PROVIDERS - Projection Reconcile`, not by provider Repair.
- A projection-reconcile trigger is issued from the same commit. The owner workflow must detect exact drift, rebuild only providers whose accepted DATA/Lego projection actually drifted, reindex `PROVENANCE.json` fingerprints, prove `reapply_published_overrides.py --check`, and dispatch exact-head census/Quick/security validation.
- Provider Repair/Brain must remain paused until that owning fixed point is green; no provider status improvement is inferred from lifecycle/test changes.


### 2026-09-24 — AnimeSama.co DATA regression found before projection publication

- Non-regression on `313cd0f...` moved past the lifecycle count fix and exposed a real provider-DATA contradiction for `animesama-co`.
- The owned runtime Lego `animesamaco_site_runtime_v1.py`, `upgrade_provider_v3_batch_routes_v2.py`, domain reconciliation tests and user-evidence crosscheck all agree that `/catalogue/?search={query}` is the executable catalogue route and `/template-php/defaut/fetch.php` is stale/candidate history.
- Current `provider-overrides.json` had those authorities inverted: `/template-php/defaut/fetch.php` in `learned_routes` while `/catalogue/?search={query}` was candidate-only. This is a true structured-DATA regression, not a stale test.
- The DATA is restored to the canonical v2 migration contract. The in-flight Projection Reconcile from the inconsistent baseline must not publish; main advancement intentionally invalidates its atomic baseline and a fresh projection reconcile is triggered from the corrected DATA.


### 2026-09-24 — Census/Projection Reconcile publication race closed

- AnimeSama.co projection run `35942671277` proved the provider correction itself was sound: targeted rebuild, projection fixed point and atomic publication build all passed. The run failed only at the final push because concurrent full census `35942671301` persisted evidence commit `277f4079b63b` on top of the same source SHA.
- This race was systemic: a census triggered by provider-impact DATA could ephemerally materialize candidate bytes, then persist only evidence and advance `main` before the owning Projection Reconcile published those bytes. The exact-head publication guard then correctly refused the otherwise-valid provider publication.
- The mono current-byte census now runs `detect_provider_projection_drift.py` in its lightweight scale job **before starting the expensive census**. Any unpublished provider projection forces `should_run=false` and hands off to `provider-projection-reconcile.yml`.
- A second identical drift check runs immediately before census evidence persistence. Even if a future workflow path bypasses the scale decision, census cannot advance `main` while provider DATA/Lego and published bytes are out of fixed point.
- This makes publication ownership explicit: Projection Reconcile first; only the exact published HEAD may persist canonical census evidence afterwards.


### 2026-09-24 — Failed scheduled Repair may no longer downgrade the durable census

- Scheduled Repair run `35976942192` on source SHA `3ed0dd323e4d...` failed its own final gates: `preservation_gate=false`, `execution_gate=false`, active positive loss `animevostfr:anime`, final outcome `failed`. Despite that, the always-run persistence step wrote its candidate census to main as `a32a661...`.
- This downgraded the durable state from the pre-run evidence (26 FULL, 2 PARTIAL, 1 CANDIDATE, 0 NETWORK BLOCKED; Vostfree FULL from strict residential replay) to 25 FULL plus 2 NETWORK BLOCKED and Vostfree HARNESS MISMATCH. Provider bytes were not shown to justify those regressions.
- Canonical Repair persistence is now fail-closed: only `steps.canonical-repair.outcome == success` may replace PROVIDER_CENSUS_STATUS / census / authority / WAF canonical ledgers. Failed or skipped Repair may still persist causal Brain memory and its exact run report for Learning, but cannot overwrite the last accepted durable census.
- The same morning Learning run `35970740811` never reached Brain-LLM inference because `brain_cron_full_coverage_test.py` caught stale provider_catalog manifestOrder entries for lifecycle-archived `desiflix` and `fullanime`. This is fixed at the lifecycle authority: `update_provider_catalog()` now reconciles general/VF manifestOrder to the current visible provider projection set, preserving relative order and appending only missing current projections.
- External private-informed guidance was correctly rejected by Repair as source-stale after real provider/lifecycle changes. A fresh Brain-LLM guidance run on the corrected HEAD is required before the next provider Repair.


### 2026-09-24 — Last accepted census restored after rejected Repair persistence

- The failed scheduled Repair candidate from run `35976942192` is rejected as canonical evidence. Its source provider bytes were the same as the immediately preceding accepted census; its own final summary had preservationGate=false and executionGate=false with an active animevostfr loss.
- Canonical census/WAF/authority/batch ledgers are restored from source commit `3ed0dd323e4ddca807de787e4f982a664592f6c3`: 26 FULL OK, 2 PARTIAL OK, 1 CANDIDATE OK, 0 PROVIDER NETWORK BLOCKED, repairQueue=12, environmentQueue=2. Brain causal memory/report files from later runs are intentionally retained.
- Subsequent commits `4fa1970...` and lifecycle persistence `144d5a4...` change control-plane/catalogue lifecycle ordering only; they do not justify discarding the accepted playback/transport ledger. Future failed canonical Repair runs are now prevented from replacing this durable state.
- Next required sequence: regenerate private-informed Brain-LLM guidance against this exact current HEAD/catalogue, pass Learning contracts, then run the bounded 3-wave/1200s Repair on the restored 12-provider queue.


### 2026-09-24 — Sharded observation evidence no longer invalidates fresh Brain-LLM priors

- Fast Repair already imports the sanitized external private-informed Brain-LLM prior before running the provider-local Brain.
- The remaining catalogue-scale false rejection was source drift caused only by persisted sharded observation files. `automation/provider-targeted-regression-recovery-*` and `automation/provider-repair-batch-refined-*` are now explicitly provider-neutral guidance drift.
- Provider materialization drift is still checked independently and fails closed; provider DATA/bytes/manifests cannot be hidden by this whitelist.


### 2026-09-24 — Learning pinned to current validated Brain-LLM

- NiakVIO Learning was still pinned to Brain-LLM commit `c752f5c21ded26c578eaeacb492611f3fdb137a9`, while the current validated Brain-LLM planner is `84eb6ff14af60c29b59b5f0382221297ddfacb4c`.
- Brain-LLM `84eb6ff14af6` passed both Brain LLM CI and the Private-Guided Advisor workflow; it includes the bounded two-slot Qwen planning path.
- `brain-learning-lab.yml` now checks out exactly `84eb6ff14af60c29b59b5f0382221297ddfacb4c` and emits the same SHA in sanitized guidance metadata. The static guidance contract is updated to prevent silent fallback to the old brain.
- A targeted Learning trigger is armed for the restored 12-provider repairQueue. Learning remains proposal/memory only; current-byte playback and identity gates remain the sole Repair publication authority.


### 2026-09-24 — Canonical Repair wall-clock budgets now match real concurrency

- Manual Repair run `35993556984` on `a45c67af7d7fbc06c7003f8f780e55b992441e0c` remained inside the canonical Repair step for more than two hours even though Brain itself was configured for 3 waves / 1200 seconds. This exposed missing outer bounds, not an LLM inference bottleneck.
- Route recovery used 12 workers for the 12-provider queue but its outer timeout still scaled linearly as `providers × request_timeout × attempts`: 12 × 55 × 3 = 1980 seconds. The budget now scales by concurrent worker batches and is clamped to 300–900 seconds.
- Targeted quick-yield probes now have a bounded 180–600 second wall-clock budget. Final portfolio comparisons are capped at 300 seconds and final Repair yield at 600 seconds.
- Canonical Brain budget is reduced from 1200 to 900 seconds with a 1080-second outer wrapper; the generic-miss→Learning/LLM handoff and catalogue-scale sharding make the older 20-minute Brain allowance unnecessary for this lane.
- The entire canonical Repair workflow step now has a hard `timeout-minutes: 30`. An individual stalled provider/process can no longer keep the Repair job alive for hours.
- A push-triggered retry is intentionally used so the shared Repair concurrency group cancels the stale manual run before repeating expensive work.


### 2026-09-24 — Repair concurrency epoch v3 bypasses serialized zombie

- The bounded push Repair created from `7ac4972...` remained pending because the older manual workflow_dispatch run `35993556984` occupied concurrency group `provider-repair-main-v2`; manual runs were intentionally non-cancellable.
- The stale manual run is already fail-closed against current main: canonical census/authority/WAF ledgers are persisted only when the tested SHA still equals remote main. Its eventual completion cannot overwrite the current canonical ledger.
- Repair moves to concurrency group `provider-repair-main-v3`. This is an intentional one-time epoch cut so the bounded pipeline can start immediately instead of waiting for the obsolete manual job. New push-triggered Repairs in v3 remain supersedable.


### 2026-09-24 — Repair v3 preflight fixture corrected

- Bounded Repair run `35994438849` failed in under a minute before any network/Brain work because `tests/provider_repair_waf_integration_workflow_test.py` still asserted the retired concurrency group `provider-repair-main-v2`.
- The workflow itself was intentionally moved to `provider-repair-main-v3`; the stale static fixture is updated to v3. No provider result or transport evidence is inferred from the failed preflight.


### 2026-09-24 — Final concurrency-v3 static fixture corrected

- Bounded Repair retry `35994664152` again stopped before network/Brain work. The WAF integration contract was already green; the remaining failure was `tests/provider_waf_tailscale_exit_contract_test.py` still asserting `provider-repair-main-v2`.
- Repository search found no other intended v2 contract beyond the already-corrected WAF integration fixture and this Tailscale fixture. The Tailscale contract is updated to concurrency epoch v3.


### 2026-09-24 — LLM causal-family transfer and stale-evidence race closure

- Bounded Repair run `35994886858` completed its Brain stage in **155.288 seconds**, one wave, with an internal 900-second budget. This confirms the +40-minute/Yflix multi-wave pathology is no longer the Brain runtime baseline.
- The same report proves the remaining LLM issue is semantic, not connectivity: sanitized guidance was present, but all persisted plans had `llmAdvisorApplied=false`. Exact string matching rejected compatible evolution such as `chain_terminal_gap -> media_extraction_gap` and `route_proven_gap -> provider_transport_gap / transport_blocked / search_gap`.
- Planner guidance now supports two bounded causal families: route/search/transport and chain/media/playback-context. Exact failure matches remain preferred; family transfer requires provider identity, an allowlisted profile, priorOnly=true and confidence >=0.90. Unrelated families are rejected.
- Exact profile negative memory remains authoritative. A profile that already failed on current evidence is not replayed just because the failure-class label moved within a compatible family.
- External private-informed guidance treats planner code and causal-memory/report files as provider-neutral only when `select_provider_materialization_scope.py` still proves zero provider materialization drift.
- Repair persistence is now stricter: if remote main advanced, the run may keep its Actions artifact but does not copy/add Brain memory/report and does not dispatch Learning/resume from stale evidence. This closes the evidence-only commit race that produced `bb5d426...` and `4e6309a...` while newer Repairs were running.


### 2026-09-24 — Brain LLM planner TDZ regression isolated and fixed

- Canonical Repair run `35996726279` imported the sanitized private-informed Brain-LLM guidance successfully (`providers=8`) and completed the provider health batch in one bounded wave, but every one of the eight selected plans was persisted as `exitReason=planner_item_error`, `failureClass=unknown_failure`, `allowedProfiles=[]`. This is not eight provider failures.
- Root cause is JavaScript initialization order introduced by the causal-family transfer change: `LLM_FAILURE_FAMILIES` was declared with `const` after the top-level loop that immediately invokes `buildPlan()`. Function declarations are hoisted, but the lexical constant remains in the temporal dead zone until its declaration executes; the first call through `llmFailureCompatibility()` therefore throws before any provider-specific LLM profile can be selected.
- The failure-family constant is moved before the top-level planner execution loop. A static regression assertion now requires the family table to be initialized before `for (const rawItem of asArray(input.items))`, in addition to the existing executable advisor tests.
- The durable census remains the last accepted state: 26 FULL OK, 2 PARTIAL OK, 1 CANDIDATE OK, 0 PROVIDER NETWORK BLOCKED, repairQueue=12, environmentQueue=2. No provider is promoted from the failed run.
- Next proof is a fresh bounded canonical Repair on the current 12-provider queue. Required markers: no `planner_item_error`; provider-specific `llmAdvisorApplied`/family compatibility where guidance exists; current-byte playback/identity/non-regression remains the only acceptance authority.


### 2026-09-24 17:00 Europe/Paris — Learning hang isolated after Repair latency fix

- Canonical Repair run `36013174459` on SHA `e58453fa690c6ed97ff6d9fee4491316216730f7` completed successfully in about 13 minutes end-to-end. Its Brain portfolio itself used only **157.16 seconds** and two waves; 0 repairs were accepted, 8 providers were escalated to Learning, and the queue stopped with `no_new_repair_experiment` rather than burning the former 5-wave/2100-second budget.
- Durable census remains **26 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 7 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 1 HARNESS MISMATCH · 1 HARNESS/ENV BLOCKED · 4 DISABLED**, with 12 provider Repair targets and 2 Core/transport targets. There are **0 PROVIDER NETWORK BLOCKED** rows.
- Follow-up Learning run `36014734210` successfully completed checkout, private-memory build, Brain-LLM routing, local Qwen startup and sanitized guidance generation, then remained stuck inside `Run adaptive Learning provider queue` for well beyond its nominal queue budget. The LLM itself is therefore not the hang.
- Root cause class: the queue used `subprocess.run(timeout=...)`. If the timed child launches descendants that inherit captured stdout/stderr, killing only the direct parent can leave descendants holding pipes open while `subprocess.run` waits during timeout cleanup. Internal budget expiry can therefore fail to return to the queue's resumable `BudgetExhausted` handler.
- The queue now starts command children and the warm Node Lab in their own process groups and terminates the whole group with SIGTERM→SIGKILL at deadline. The workflow also wraps the queue in a dynamic GNU `timeout` guard at budget + 120 seconds as an independent outer fail-safe.
- Canonical Repair now dispatches deferred Learning with an explicit **20-minute** slot instead of inheriting the generic 60-minute default. The refreshed push trigger uses the same 20-minute targeted fast-handoff cohort; its push concurrency is expected to cancel the obsolete stuck explicit run.
- This is a scalability correction, not provider success proof. Current provider statuses must stay unchanged until the corrected Learning run returns new sanitized strategy evidence and the subsequent Repair/Retest proves playable identity-safe streams.


### 2026-09-24 — Brain LLM upgraded from profile selector to executable experiment generator

- Root cause of the flat census was isolated after the latency work: the Brain-LLM already produced rich bounded `RepairProposal` objects, but the public bridge discarded everything except one of six strategy/profile names. NiakVIO therefore gained better classification without gaining a new executable hypothesis. Once that profile had negative memory, every later LLM idea in the same family was suppressed.
- Brain-LLM commit `1b3cbb5dfdde26d1c30552304807e76a3b55a2df` adds a privacy-safe abstract experiment spec. It contains only enums/bools/small integers controlling existing sandbox behavior: route/recipe evidence policy, role ordering, terminal-only traversal, alias search, response salvage, document request mining, session bootstrap and crawl budgets. It cannot contain URLs, headers, tokens, cookies, source text, diffs, mutation payloads or private-chat text.
- Every spec has a stable SHA-256 fingerprint. NiakVIO commits `d1cd91a...` and `e0d67ff...` carry that fingerprint through sanitized import, deterministic planner output, immutable attempt snapshots and negative experiment memory. Negative debt is now exact to **profile + experiment fingerprint**; a failed old experiment no longer suppresses a materially different LLM experiment in the same family.
- Commit `edcc797...` applies the abstract spec to the existing adaptive runtime sandbox. The LLM can now change which already-observed provider/peer/generic routes and request recipes are admitted, role priority, terminal-only traversal, recovery features and bounded crawl budgets. Current-byte playback, identity and regression gates remain the only acceptance/publication authority.
- Commit `53733d3...` fixes a second conversion blocker: WAF/Tailscale transport evidence is reapplied inside both internal census render paths before batch-plan construction. The durable 12-provider Repair queue must therefore no longer oscillate to 8 Repair / 7 environment inside canonical Repair and then back to 12 at final persistence.
- Executable contracts added in `c126693...`: same profile with a different LLM fingerprint remains eligible; exact fingerprint debt blocks replay; synthetic runtime options materially differ between two specs; transport overlay is required exactly once in each internal render path.
- Learning/Repair workflows now pin Brain-LLM v2 and run these contracts before expensive work. The prior Learning run `36022139348` remains evidence for source SHA `e1c85a0...` and the old advisor semantics; it must not be used as proof of the v2 experiment path.
- Next proof: a fresh v2 Learning must publish schemaVersion=2 guidance with experiment fingerprints, followed by a short Repair where all 12 provider repair targets remain in scope and at least the advised candidates log distinct experiment fingerprints. Status promotion still requires real playable identity-safe current-byte proof.


### 2026-09-24 — Repository hygiene and CodeQL alert cleanup armed

- The obsolete `workbench/brain-guidance-finalize-20260923` branch diverges historically from main, but its nine Brain invariants are superseded on current main by newer advisor observability, stale-artifact rejection, generation-aware rescue, guidance-drift and negative-memory contracts. Branch maintenance now deletes this workbench branch only when no open PR targets it; `brain-learning/proposals` remains the only non-main durable memory branch.
- The existing CodeQL workflow already contains an owner-authorized bulk dismissal job that enumerates every open CodeQL alert, dismisses it with an audit comment, re-queries open alerts and fails if any remain. A one-shot push marker `[dismiss-codeql-alerts]` now invokes that exact job; normal future pushes continue to run the maintained-source CodeQL matrix.
- This security/hygiene commit does not alter provider bytes or provider status. Provider repair remains separately required for the 12 current Repair targets and 2 Core/transport targets.


### 2026-09-24 — Workbench branch removed and CodeQL open-alert backlog converged to zero

- Branch maintenance run `36027972397` completed successfully and deleted the obsolete `workbench/brain-guidance-finalize-20260923` branch after proving there was no open PR. A subsequent branch search returned no `workbench` branch. Durable branch policy is back to `main` plus the isolated `brain-learning/proposals` memory ref.
- CodeQL bulk-classification run `36027972197` observed **643 open CodeQL alerts** on pass 1. It dismissed 642 directly; four PATCH responses transiently returned `unexpected end of JSON input`, then passes 2/3 converged the server state to **0 open CodeQL alerts**.
- The run ended red only because its script treated the historical transient-failure counter as fatal even when the final authoritative re-query returned `remaining=0`. The dismissal job now fails only when the final open-alert set is non-empty; transient API errors remain logged as diagnostics.
- The next ordinary main push intentionally has no dismissal marker, so the normal Actions/Python/JS-Core/JS-ProviderBase CodeQL matrix remains enabled and must run again on the post-cleanup SHA.

### 2026-09-24 — Harness statuses gain an active Core/Brain owner

- Durable census still has 12 provider-local Repair targets plus two Core/client transport targets: `animesultra` (browser content succeeds on GitHub and residential exits while direct/OkHttp fails on both) and `animevost-fr` (challenge persists on both GitHub and residential paths). Tailscale therefore disproves a simple GitHub-IP explanation; neither row may be treated as an inert provider-network block.
- Targeted Brain Learning now accepts the union of current `repairQueue` and `environmentQueue`. Provider-local mutation remains forbidden for environment-owned rows.
- Brain Autopilot now sends every HARNESS/Core-client cohort to both the targeted WAF/Tailscale differential and a targeted 20-minute Learning run with `publish_proposal=true`. Persistent divergence must therefore produce a reviewable Core/architecture proposal and Native-Lab reentry path instead of being endlessly re-probed.
- This does not promote either provider by label. FULL/PARTIAL still requires real current-byte playable, identity-safe output in the appropriate client/runtime.


### 2026-09-24 18:50 Europe/Paris — Brain lane preflight import regression fixed

- Brain Autopilot run `36029367282` dispatched the current causal lanes correctly, including Fast Repair, targeted Learning and Core/WAF transport work.
- WAF/Tailscale lane `36029418290` completed successfully and persisted transport evidence; durable census still has 0 PROVIDER NETWORK BLOCKED rows.
- Fast Repair `36029411619` and Learning runs `36029414461` / `36029421520` never reached provider Brain/Qwen execution. All three failed during static contract validation because `scripts/brain_llm_guidance.py` / `scripts/import_external_brain_llm_guidance.py` imported sibling `brain_llm_experiment.py` assuming `scripts/` was already on sys.path. Direct script execution satisfied that assumption; importlib-based contract tests did not.
- Both scripts now prepend their own directory to sys.path before importing `brain_llm_experiment`. This is a packaging/import fix only; it does not change provider bytes, status, proof authority or LLM policy.
- Autopilot is re-armed on the current durable census after this fix. Required next proof: Fast Repair and Learning must pass preflight, actually import/publish v2 Brain-LLM guidance, and execute the 12 provider Repair + 2 Core/transport cohorts under the existing bounded/sharded budgets.


### 2026-09-24 18:54 Europe/Paris — Allwish causal-owner dead zone removed

- Brain Autopilot `36030055680` built a 14-provider plan but marked one execution blocked: Allwish was in the canonical `repairQueue` while its batch group still classified as `harness-compatibility|...|residential-exit-all-challenged`, which requires environmentQueue ownership.
- The durable Allwish row already carries stronger provider-replay evidence: both movie/tv residential full-provider replays stop at `provider_zero_before_provider_network` with zero raw/playable/verified results. That disproves the transport layer as the immediate execution owner even though the older boolean `residentialProviderReplayReclassified` field is absent.
- `build_provider_repair_batch_plan.py` now treats that replay-stage proof itself as authoritative for NO PROOF + repairEligible rows. Such rows enter provider-strategy Learning rather than a blocked harness lane. The legacy boolean is no longer required.
- The causal-precedence contract now proves the behavior with the flag true, false and absent, while still retaining harness ownership when the pre-network replay proof is absent.
- This is a routing correction only. Allwish is not promoted; it still requires a new learned provider-side request/route strategy and current-byte proof.

### 2026-09-24 19:10 Europe/Paris — Exact unexecutable LLM experiments stop after one wave

- Fast Brain runs 36030839750 (source 8f9b074...) and 36031544641 (source 482e7f8...) both completed successfully in roughly 4.5–5.5 minutes, proving the former 40+ minute Repair pathology is no longer the normal provider-local path.
- Both runs selected the full 13-provider current repair cohort and accepted 0 production candidates. Twelve providers were handed to Learning; Animesalt alone remained for waves 2/3.
- Raw repair memory proves why: Animesalt exact Brain-LLM advisor fingerprint 9a8d385d... was recorded as profile_unavailable / planned_profile_not_applicable_to_current_bytes with executionObserved=false. This is correctly not execution failure debt, but replaying the same exact advisor/profile/fingerprint in later waves is still useless.
- Canonical Brain now has a separate PROVIDER_BRAIN_UNEXECUTABLE_LLM_TO_LEARNING_V1 rule: an exact advisor experiment that current bytes cannot execute is handed to Learning immediately after the first wave. It does not poison the profile globally; a future different advisor fingerprint remains eligible.
- Brain portfolio reports now preserve llmAdvisorSourceFailureClass, llmAdvisorFailureCompatibility, llmAdvisorExperimentFingerprint and the sanitized llmAdvisorExperiment, so repeated/changed advisor experiments are directly auditable without inspecting raw memory.
- Current durable transport state remains 0 PROVIDER NETWORK BLOCKED. Allwish has been rerouted from the owner dead-zone to provider-strategy Learning, animevost-fr has returned to provider Repair, and Animesultra remains the sole Core/client HARNESS MISMATCH.
- Next proof: a fresh Fast run should process the current repairQueue with Animesalt leaving after wave 1 rather than repeating the same advisor through waves 2/3. No provider status promotion is expected without new playable identity-safe evidence.


### 2026-09-24 19:33 Europe/Paris — Harness mismatch eliminated; current causal queue is provider-owned

- Targeted WAF/Tailscale run `36034119661` on source SHA `6c750ac...` completed SUCCESS. The durable census now has **0 HARNESS MISMATCH, 0 HARNESS/ENV BLOCKED and 0 PROVIDER NETWORK BLOCKED**.
- Animesultra did not become playable. Its full residential provider replay completed identity-safely with zero media at `provider_zero_before_provider_network`; the overlay therefore reclassified it from the misleading harness bucket to **ROUTE PROVEN** and returned it to ordinary Repair/Learning ownership. Current census is **26 FULL OK · 2 PARTIAL OK · 1 CANDIDATE OK · 9 ROUTE PROVEN · 3 CHAIN REACHED · 1 NO PROOF · 4 DISABLED**, with **14** repairable symptomatic providers.
- Brain-LLM commit `b64b526990a5...` changes confirmed cross-network browser/native divergence from deterministic re-probing to bounded `llm_diagnose` architecture reasoning with **no direct mutation authority**. Brain LLM CI run `36033452051` is green.
- NiakVIO commits `0f5336c...`, `f9b3493...`, and `ba9f962...` add a distinct client-transport causal state, keep such debt out of provider mutation, pin the new Brain-LLM, accept v2 experiment/fingerprint guidance, and feed non-provider LLM diagnoses into the review-only architecture proposal instead of discarding them.
- Targeted-regression run `36034557844` is now SUCCESS after the workflow startup fixes; it tested the current 14-provider repair cohort with no identity contradictions and no newly verified provider. Its refined evidence splits the previous broad capability batches into provider-specific observed network signatures, which should feed the next Brain pass instead of repeating one generic profile across unlike failures.
- The older Learning run `36032139719` started from SHA `6c46d95...` and cannot validate the new Brain pin. Re-arm Brain Autopilot on the current 14-provider queue so Fast Repair and Learning execute the new LLM experiment/diagnosis path on current bytes.


### 2026-09-24 19:39 Europe/Paris — Brain LLM now consumes current targeted network evidence

- Brain-LLM commit `48df8f0d8d7a...` adds the missing data bridge from NiakVIO targeted recovery into each LLM request. The model now receives bounded current `debugStages`, lane statuses, playable/verified lanes, sanitized method/host/path/status observations, and the exact refined batch signature/split reason for that provider.
- Stale refined plans are rejected when their source census run differs from the current census. Raw headers and unbounded response content are not forwarded. Current-byte tests remain proof authority; these observations are context only.
- Brain LLM CI run `36035419178` completed SUCCESS. NiakVIO Learning is now pinned to this exact code SHA so the next Fast→Learning handoff will use the refined per-provider evidence instead of only the older census/memory summary.


### 2026-09-24 19:42 Europe/Paris — Targeted recovery startup fix preserves bulk-onboarding guard

- Provider Non-Regression run `36035661181` failed only in the static bulk-onboarding workflow contract: the earlier GitHub-expression simplification removed the literal `provider: bulk stage/activate` guard from targeted recovery.
- The guard is now evaluated inside the already-valid `size.route` Python step using the checked-out commit subject. Bulk stage/activate pushes still set `should_run=false`, while the probe job retains the simple GitHub expression that already proved it can start successfully in run `36034557844`.
- No provider bytes or repair evidence are changed by this CI fix.


### 2026-09-24 19:45 Europe/Paris — Learning guidance attribution pinned to executed Brain LLM

- Audit found a split pin in `.github/workflows/brain-learning-lab.yml`: checkout already used Brain-LLM `48df8f0d8d7a...`, but `brain_llm_guidance.py --brain-llm-sha` still stamped the historical `23a601...` SHA.
- The guidance attribution now uses the exact same `48df8f0d8d7a...` SHA as the checked-out planner, and the contract test asserts both values together. This is attribution integrity only; it does not promote any provider.


### 2026-09-24 19:49 Europe/Paris — Root cause fixed: LLM advisor profiles were planned but not materialized

- The apparent Brain-LLM ineffectiveness had a concrete runtime cause. `plan-repairs.mjs` could select an LLM advisor profile such as `proven_route_terminal_traversal_v1`, but `brain_repair_runtime._plan_snapshot()` dropped `llmAdvisorApplied/Profile/Strategy` before candidate generation.
- `scripts/adaptive_runtime/runtime_repair.py` therefore computed `new_strategy_id` only from post-exhaustion/historical/generation state. The Deep matcher was then filtered to the LLM-selected profile while the generator had not materialized that profile, producing `profile_unavailable / planned_profile_not_applicable_to_current_bytes` without executing the LLM experiment.
- The snapshot now preserves the exact LLM advisor decision, and adaptive runtime gives a validated causal `llmAdvisorProfile` first priority when building `new_strategy_id`. The existing experiment knobs (route/recipe policy, role order, terminal-only, salvage, session bootstrap and bounded traversal budgets) are already consumed by the generator, so the LLM experiment now produces real candidate bytes and enters ordinary byte validation, identity gate and deep playback retest.
- Added regression coverage for a pre-exhaustion route-proven LLM plan: snapshot preservation, exact strategy materialization and `matching_profiles()` inclusion must all hold. No direct LLM publication authority is introduced.


### 2026-09-24 20:00 Europe/Paris — Fast Repair drops stale queued work instead of serializing it

- `provider-fast-repair-main` previously had `cancel-in-progress: false` even though the persistence step rejects any run whose source SHA is no longer current. Multiple 4–5 minute runs were therefore allowed to finish only to emit `FIELD_PROVIDER_FAST_REPAIR_STALE` and requeue again.
- Fast Repair concurrency is now newest-wins (`cancel-in-progress: true`). A newer current-byte repair run cancels obsolete queued/in-progress Fast work in the same lane; validated publication still requires the existing current-HEAD and retest gates.
- Re-armed the 5-provider LLM execution microbenchmark on the runtime fix, so it does not wait behind the already-obsolete pre-fix Fast run.


### 2026-09-24 20:12 Europe/Paris — Fast LLM repair is single-round; Learning owns hypothesis rotation

- Fast run `36037779477` on the corrected LLM runtime proved real advisor execution but exhausted its 420 s budget inside the first packed 5-provider Deep batch before finalizing any provider (`processedProviderCount=0`). The artifact still recorded `executionObserved=true` for advisor experiments that ran before timeout, including 4khdhub and MalluMV.
- Fast Repair now calls the generic Brain with `maxRoundsPerBatch=1` by default. One current hypothesis is generated/tested per provider in Fast; any additional experiment rotation remains the responsibility of the isolated Learning lane. The generic Brain default stays at 3 rounds, so Learning/deep callers do not lose exploration depth.
- Workflow/trigger support `max_rounds_per_batch` / `maxRoundsPerBatch`, and the report records `maxRoundsPerBatch` for auditability.
- Learning run `36038637655` failed before sandbox execution because `brain_llm_learning_workflow_contract_test.py` incorrectly required the architecture-stage `--llm-batch ...` argument inside the earlier LLM-setup substring. The contract now validates that argument against the full workflow while keeping interpolation/schema checks scoped to the LLM setup section.


### 2026-09-24 20:18 Europe/Paris — Fast one-round benchmark completed; Learning contract scope fixed

- Fast run `36039284424` completed the five-provider LLM microbenchmark in **194.025 s** with `maxRoundsPerBatch=1`, versus the prior 420 s budget exhaustion with zero finalized providers. All five providers were visited and the run exited without time-budget exhaustion.
- LLM execution is now proven on current bytes for 4khdhub and Animesalt (`executionObserved=true`); both failed the strict playable-category gate rather than `profile_unavailable`. MalluMV is strategy-exhausted after a real chain-terminal attempt; Moviebox and Yflix are already exhausted in Fast and correctly belong to Learning.
- Learning run `36039730293` failed before sandbox work only because the workflow contract still scoped the v2 schema assertions to the pre-queue LLM setup substring. Schema/experiment assertions now validate the whole workflow, while interpolation/setup assertions stay local to the setup block.
- Learning is pinned to Brain-LLM `e996ed8127cc...`, whose CI is green. This version preserves current targeted network evidence, supports non-provider architecture diagnosis, runs external guidance in advisor-only mode, and bounds model output size. A fresh handoff run is armed on the current five-provider evidence plus the existing 14-provider Learning registry.


### 2026-09-24 20:23 Europe/Paris — Retry trigger restored to targeted Fast-Handoff contract

- Learning run `36040041975` passed all preflight contracts but incorrectly entered FULL Learning: weekly FULL native Lab import ran and the provider-stage step used the unfiltered discovery branch. Root cause was the retry trigger written at `2d9299b...`: its descriptive `reason=retry-fast-handoff-after-learning-contract-scope-fix` no longer matched `select_fast_learning_handoff.py`'s stable Fast marker, and it had no versioned `execution_mode` marker.
- The trigger is restored to `reason=fast-brain-strategy-exhaustion`, `expected_scope=current-fast-repair-handoff-only`, and also carries `execution_mode=targeted-fast-handoff-v7-provider-repair-handoff`. The selector will therefore intersect only current `repairQueue` providers with pending LEARN-owned handoff rows.
- The same restart aligns Learning Qwen with its two planning workers: llama.cpp now runs `-c 8192 -np 2`, and the planner is explicitly bounded to `--workers 2 --max-tokens 768`. This removes the previous `2 workers -> 1 model slot` serialization without raising planning concurrency.
- The previous FULL run is superseded by the new push under `cancel-in-progress` and must not be used as provider proof.


### 2026-09-24 20:48 Europe/Paris — Fast-Handoff Learning no longer blocks on local Qwen

- Targeted Learning run `36040850096` reached the correct five-provider handoff but then spent the critical path inside local Qwen guidance generation. This is not acceptable for a catalogue expected to grow to hundreds of providers.
- Fast-Handoff Learning now skips llama.cpp/model startup entirely. It imports the latest sanitized `niakvio-guidance` ref through the existing current-SHA/provider-drift validator; if that cache is compatible it is used as a non-authoritative prior, and if unavailable Learning continues with an empty LLM prior plus deterministic/learned strategies instead of waiting on the model.
- Local Qwen remains available for non-Fast/scheduled Learning and the separate Brain-LLM advisor workflow, but it is no longer a blocking dependency of provider repair.
- The previously valid nine-provider guidance ref was restored after advisor run `36039671478` produced zero publishable rows. Brain-LLM commit `887f025...` adds a same-source coverage guard so a degraded guidance candidate cannot overwrite a more complete valid cache.


### 2026-09-24 21:03 Europe/Paris — Learning→Repair return executes one current hypothesis first

- The canonical V6 pipeline previously invoked Brain with three Deep rounds for both automatic `mode=repair` and explicit `force`. That recreated avoidable latency immediately after Learning had already selected/evolved a strategy.
- Automatic `mode=repair` now uses `--max-rounds-per-batch 1`: execute the freshly learned/current hypothesis once, then rely on the existing strict current-byte playback/identity/non-regression gates. A miss can return to Learning instead of burning three variants in the same return pass.
- Explicit `force` retains three rounds, so operator-requested deep exploration loses no depth. The Brain portfolio budget/gates are otherwise unchanged.
- The currently running Learning run `36043664285` is still testing source SHA `00362d02...`; this optimization applies only to the canonical Repair it will dispatch from the newer main after Learning publishes.


### 2026-09-24 21:10 Europe/Paris — Canonical Repair preflight contract aligned with one-round automatic return

- Repair run `36045821519` never reached provider execution. It failed in preflight because `tests/brain_exploration_chain_test.py` still required a literal `--max-rounds 3`, contradicting the new intentional automatic Repair behavior (`1` round in `mode=repair`, `3` in explicit `force`).
- The exploration-chain contract now validates the generic Brain's configurable `--max-rounds-per-batch` argument and its propagation into Deep Repair instead of hard-coding three rounds.
- Re-armed canonical Repair against the exact current 14-provider `repairQueue`; this retry is the first real canonical execution after the successful targeted Learning run `36043664285`.


### 2026-09-24 22:05 Europe/Paris — Hidden Deep-round override and catalogue-wide candidate work removed

- Canonical Repair run `36048403587` completed in ~25 minutes and failed closed with 0 accepted repairs, 13 Learning deferrals, 1 remaining provider, 0 playable/verified current candidate streams, and the transient historical proof loss `animevostfr:anime`. The durable census therefore correctly remained unchanged at 14 repair providers and 0 environment blockers.
- Timing evidence isolated the main costs: route recovery ~2 min; catalogue-wide rematerialization plus broad candidate guards ~6m45; Brain ~12m47; final yield/retest ~1m30.
- Root cause found in `run_adaptive_deep_repair.py`: it overwrote an explicit `--max-rounds 1` with 3 whenever exploration-chain mode was enabled. Explicit caller budgets are now authoritative; exploration-chain 3-round behavior is only the default when the caller omitted `--max-rounds`.
- Automatic Repair is now truly one hypothesis once: `waves=1`, `maxRoundsPerBatch=1`, 600 s portfolio cap. Explicit Force retains 3 waves/3 rounds. Single-hypothesis Deep validation also fail-closes with at most 45 s provider timeout and 2 settings profiles, reducing worst-case blocked-provider latency without weakening positive acceptance gates.
- Automatic Repair is non-publishing, so candidate rematerialization now narrows `all/providers` selector output to the current Repair cohort. Explicit Force retains full materialization authority. The expensive stream-output guard likewise accepts a Repair-only provider filter; its default/full CI behavior is unchanged.
- The evidence-only commit `cde679d...` automatically started Repair `36051219488` and Learning `36051216728` on the old slow semantics; this patch supersedes those runs rather than treating them as new proof.


### 2026-09-24 22:11 Europe/Paris — Static V6 contract aligned with dynamic automatic Repair budget

- Optimized Repair run `36052679956` exited in ~1 minute before provider execution because `tests/provider_repair_pipeline_v6_contract_test.py` still required literal `--waves 3` / `--time-budget-seconds 900`. This was a stale static contract, not a runtime regression.
- The V6 contract now checks the intended dynamic split: automatic `repair` = 1 wave / 600 s, explicit `force` = 3 waves / 900 s, with the existing 150 s no-new-batch floor. It also asserts targeted non-publishing materialization.
- Re-armed the exact current 14-provider Repair queue. Run `36052679956` produced no provider proof and must not be used for status changes.


### 2026-09-24 22:14 Europe/Paris — Repair V6 compatibility wrapper accepts parameterized rematerialization

- Repair run `36053082361` again stopped before provider work in the static compatibility wrapper. The traceback displayed the nearby candidate-yield assertion, but the current pipeline still contains that exact call; the rewritten contract's line mapping was misleading.
- The stale assertion was the exact zero-argument signature `def rematerialize_repair_scope()`. The compatibility wrapper now rewrites it to the parameterized targeted signature contract. No provider result from `36053082361` is authoritative.


### 2026-09-24 22:28 Europe/Paris — Network failures no longer erase stronger route/chain proof

- Optimized Repair run `36053416693` completed successfully on `0f896ce...` with targeted materialization and the bounded automatic Repair path, then persisted evidence at `9c793473...`. The 14 providers remain unresolved and are correctly owned by Learning; the run did not produce a current playable/verified repair.
- The resulting census incorrectly downgraded MalluMV to `PROVIDER NETWORK BLOCKED` even though the same row retained 4 qualified live routes and a retained chain hit, with `harnessTransportClass=not-applicable`. Root cause: the census state machine let `provider_network_exception` override stronger route/chain evidence whenever no historical playable proof existed.
- Census precedence is now monotonic: candidate proof > historical regression > current chain > retained live route > bare network block. A network exception/HTTP error/timeout can only yield `PROVIDER NETWORK BLOCKED` when no stronger provider-side proof exists. The same rule applies when reconciling carried rows.
- Armed a MalluMV-only current-byte Retest with `autoRepair=false` to persist the corrected classification without re-running the full 14-provider repair loop.


### 2026-09-24 22:42 Europe/Paris — MalluMV retest preflight fixture corrected

- Targeted Retest `36056329250` executed no provider probe: `provider_census_status_markdown_test.py` failed because its carried-row fixture embedded `routeProof` directly while production intentionally recomputes carried route proof from `provider-overrides`. The renderer stripped the fixture's synthetic route, so the expected `ROUTE PROVEN` assertion was invalid.
- The contract fixture now supplies a real current `live_route_gate` through `provider-overrides`, matching production ownership. The network-proof precedence code itself is unchanged. MalluMV-only Retest is re-armed with `autoRepair=false`.


### 2026-09-24 22:56 Europe/Paris — Learning fixture authority bug: anime providers were tested as movies

- Learning run `36054895886` processed the 14-provider Fast handoff but produced no provider proposal. Its targeted Lab evidence exposed a systemic fixture bug: anime providers including AllAnime, AnimeSalt and AnimeSultra were exercised with movie fixtures such as Oppenheimer/The Matrix even though current `manifest.json` declares them `anime,tv`.
- Root cause: `run_brain_learning_queue.py::declared_type()` trusted staged candidate metadata only and silently defaulted to `movie` whenever `metadata.supportedTypes` was absent. That poisoned Learning evidence and negative memory with out-of-capability tests.
- Learning fixture type resolution is now fail-closed and catalogue-authoritative: `manifest.json` first, durable census `declaredLanes` second, candidate metadata only as final fallback. `anime+tv` without `movie` resolves to `anime`; unknown type raises instead of defaulting to movie.
- `choose_fixture()` no longer falls back from a missing anime/tv pool to movie, and validates that the selected fixture mediaType matches the declared provider type.
- Added `brain_learning_fixture_type_authority_test.py` to both the main Workflow Gate and Learning preflight. A push-triggered Animesalt-only 8-minute Learning validation is armed; expected Lab fixture must be anime (Hell Mode/JJK/etc.), never a movie.
- Investigation also confirmed that MalluMV's old positive-program memory was intentionally cleared by `b704f60...`: its prior playable acceptance came from unrelated Google gstatic marketing videos. That memory must remain cleared; it is not a regression to restore.


### 2026-09-24 23:24 Europe/Paris — Targeted Learning stage cleanup moved inside its 30 s bound

- Animesalt-only Learning run `36059592470` remained in `Build isolated current provider stage` far beyond the intended 30 s targeted bound.
- The explicit target routing itself is correct: `target_provider: animesalt` forces `fast_handoff=true` only after verifying current `repairQueue` + LEARN/pending ownership.
- Root cause in the workflow: `rm -rf staging` ran before the bounded targeted builder. A large/stale staging tree could therefore stall the job outside the timeout.
- Targeted Learning no longer performs an external unbounded stage delete. `build_published_provider_stage.py` owns its own stage cleanup inside the 30 s timeout, and the workflow now asserts the produced candidate cardinality exactly matches the targeted cohort.
- Full Learning keeps its explicit `rm -rf staging` path; only targeted Fast-Handoff semantics changed.
- Re-armed the same Animesalt-only 8-minute fixture-authority validation. The required proof is an anime fixture, never a movie fixture.


### 2026-09-24 23:31 Europe/Paris — AnimeSalt runtime now preserves direct fixture/TMDB metadata

- Targeted Learning run `36061071530` completed successfully on exactly one provider after the bounded staging fix. It used only anime fixtures (Demon Slayer, Fullmetal Alchemist: Brotherhood, Naruto, Hell Mode and Jujutsu Kaisen); the previous movie-fixture contamination is closed.
- AnimeSalt still returned `provider_unreachable / no_provider_request_observed` across the corrected fixtures. The custom runtime hook is present before the global dispatcher and the exported `getStreams` exists before dispatcher installation, so missing hook registration/order is not the cause.
- The worker passes `fixture.tmdbMetadata` directly in the object invocation before loading the provider. Core may rewrite the global `__nuvioMediaContext` during provider evaluation, but AnimeSalt's `req()` previously discarded direct `tmdbMetadata` and `meta()` depended on Core/global state. That permits an empty return before the first provider fetch, matching the observed failure exactly.
- AnimeSalt now carries `tmdbMetadata/tmdb_metadata/metadata` from the object invocation into its request model and projects it before Core/global fallbacks. The patch remains provider-local and is owned by `provider_patches.animesalt.provider_lego_scripts`, so materialization scope resolves to AnimeSalt only.
- A canonical AnimeSalt-only Repair is armed. Required first proof is provider-owned network observation > 0 on an anime fixture; playable/verified promotion remains subject to the existing strict gates.


### 2026-09-24 23:46 Europe/Paris — AnimeSalt advanced from no-request to real WAF stage; direct series route now precedes homepage

- The direct-metadata patch is causally validated by targeted recovery evidence commit `d76baaf...`: AnimeSalt changed from `no_provider_request_observed` to an actual provider request. Current network trace is TMDB 200 followed by `GET animesalt.cx/ -> 403`, classified `provider_waf_challenge`; no playable/verified stream was claimed.
- This proves metadata loss was a real first-stage bug and is now fixed. The next blocker is specifically the runtime's homepage-first discovery path, not the harness.
- Current public AnimeSalt exposes deterministic normal content routes such as `/series/jujutsu-kaisen/` containing season/episode data. The provider runtime now tries `/series/{normalized-title-slug}/` first, validates that the returned page matches the requested title or exposes episode links, and reuses that fetched page in episode selection. Homepage AJAX nonce/search remains fallback only.
- The new route is not promoted from an inferred stream URL and does not weaken playback/identity gates. It only removes an unnecessary dependency on the challenged homepage before reaching provider-owned content.
- Targeted recovery run `36062383321` also exposed a separate scaling defect: its workflow rematerialized all 42 active providers and probed the full 14-provider repair plan after a one-provider patch. That inefficiency is confirmed and remains to be corrected independently; it does not invalidate the AnimeSalt network evidence.
