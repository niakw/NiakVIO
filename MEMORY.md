## 2026-10-10 — Root cause of one-provider-per-batch FORCE progress confirmed

- `niakw/NiakVIO-Brain-LLM/scripts/plan_batch_from_checkout.py` proves `--stop-after-first-mutation` stops the **entire selected provider batch** after one provider yields a candidate. Full-cohort private guidance workflow had passed this flag even with page_size=9 and max_hypotheses=4. Remaining siblings were marked `earlyPublishDeferredProviders`. This is an infrastructure reason for apparently endless single-provider cycles, independent of provider implementation, and was not a fully validated repair.
- Brain-LLM workflow fix `d3d2d901` removes early-exit for full provider pages, retaining bounded per-provider multi-hypothesis generation. Test fix `ce8beb1c` asserts no early-stop flag in full-cohort invocation. Exact **Brain LLM CI `38068914976` SUCCESS**: 264 tests and privacy audit OK.
- Initial private-guidance run `38068530840` on old Brain `cdd06f98` had reached Qwen generation with the stale early-stop. New trigger `4e779474` starts fresh **full-16** private guidance run **`38068986993`** on NiakVIO source `d06d4cf6`, now preserving every provider in each guidance page. It may cancel/supersede the old run by GitHub workflow concurrency. Independent FORCE `38066889059` remains on NiakVIO SHA `64ed44fd` and reached architecture materialization. Preserve their separate evidence authority.
- The 16-provider queue is **not yet proven resolved**; no accepted, materialized, identity-verified terminal playback was confirmed when this entry was written. Current authoritative census remains 22 FULL/46 and 16 repairQueue. Do not patch providers manually to mask a Brain failure.

## 2026-10-10 — Independent fresh Brain LLM guidance on all 16, partial-page FORCE bypass fixed

- Added Brain-LLM orchestration improvement on `niakw/NiakVIO-Brain-LLM`: partial deterministic FORCE preflight previously set `ready=true` when **one provider** yielded an executable candidate; the workflow then skipped all Qwen calls for the whole page. Fixed at `197d4efc` to bypass Qwen only if `executable==page_count`. A partial page now enters the model path, preserving existing sanitizer/current-byte publication requirements. Test commit `a5046672`; **Brain LLM CI `38068478774` SUCCESS** (264 tests, privacy OK).
- New Brain-LLM trigger `cdd06f98` dispatched **Private-Guided Advisor `38068530840`** against exact NiakVIO source `24f7a92a` and all **16 current repairQueue** provider IDs. Old obsolete anime-ultime excluded. This run is separate from NiakVIO full-16 FORCE `38066889059` on `64ed44fd` which had progressed to executable FORCE architecture materialization at the checkpoint. Check both outputs; only actual model-generated, compiled, applied, rematerialized, identity-correct playable terminal plus non-regression and persisted memory count as completed repairs.
- No provider implementation manually altered; no validated newly repaired provider claimed from either run yet. Preserve exact runner and tested SHAs, and don't interpret GitHub workflow success alone as media validation.

## 2026-10-10 — Brain LLM novel-hypothesis routing now executed in tested orchestration

- Separate `niakw/NiakVIO-Brain-LLM` main commits `f3036a03`, `4dba0502`, `6289f203` and `63d92f83` repair a systemic advisor-only stall: after >=3 **distinct, failed, executionObserved** fingerprints on the *same strategy/profile*, high-confidence deterministic guidance now escalates to the **model** rather than cycling further unproven generic knobs. No automatic provider edit permissions are opened; repeats, unexecuted and unrelated profile negatives do not exhaust the model gate.
- Brain LLM CI `38068006729` green on `6289f203`: **263 tests** and privacy audit OK. Later CI **`38068191061` SUCCESS on `63d92f83`**: **264 tests**, including a real `BrainOrchestrator` mocked backend call exactly once and no mutation, privacy audit OK. Initial `f3036a03` CI failed privacy scanning because of a 10-digit literal in hex alphabet; corrected without changing semantics.
- Important SHA authority: existing 16-provider FORCE `38066889059` started on NiakVIO `64ed44fd` and pinned the **older Brain LLM at the time of checkout**. Its workflow is still in adaptive Learning queue as of the last check; it cannot prove the new Brain LLM routing commit. A **fresh** current-SHA run must demonstrate actual Qwen calls, model-generated executable family, compile, source application, rematerialized bytes, correct-content terminal-playback evidence, non-regression, and persistent experience. Current census remains **22 FULL / 46, repairQueue 16**; new successfully repaired providers **0 proven in this intervention**.
- NiakVIO Brain-only planner novel-fingerprint fix passed CORE Gate `38066575038`, and full 16 FORCE trigger had CORE Gate `38066888986` SUCCESS at `64ed44fd`. No manual provider fixes or PR branches were created.

## 2026-10-10 — Full 16-provider FORCE dispatched; stale Learning failure classified by exact SHA

- Old Fast-handoff Learning `38064727894` on **`9da7fd424`** completed **FAILURE** in `Materialize executable Brain architecture FORCE patch`. Real job log pinpoints `tests/brain_architecture_force_materializer_test.py:141` asserting the exact `route_transition_graph_v1` guard; corrective LLM rounds exhausted, including timeout retries, with no applied executable patch. This is the **pre-`c35e00c2` / `c756a1c4` Brain context bug**, not proof of failure on new main. Its sanitized Qwen-advice step reported `llm_calls=0`, `deterministic_advisor=11`, and final guidance for 8/11 Fast targets; further causal family exhaustion requires a new executor rather than repeated same-profile advice. Do not claim old materializer passed.
- New full-cohort FORCE **`38066889059`** launched by trigger commit **`64ed44fd`** on current Brain planner, with all **16** repairQueue providers from census `38063979695`, `architecture_force=true`, strict compile/current-byte playback/identity/nonregression, and no provider manual patch or PR. Verified GitHub run exists and launched; outcome and terminal playback are still pending/unproven as of this checkpoint.
- Exact newest CORE Workflow Gate **`38066888986`** launched on `64ed44fd`; earlier **`38066575038` SUCCESS** on planner+test SHA `0478d600` with real test output. Different SHAs/runs must never be conflated. Census remains **22 FULL / 46, 16 repairQueue** until fresh current-byte terminal evidence.

## 2026-10-10 — Restore new LLM advisor strategy after exhausted Learning; CORE validated

- Root cause replayed in `engine_v2/scripts/plan-repairs.mjs`: `(!experimentExhausted || !learningMode)` globally disabled ordinary model guidance for *all* Learning-exhausted providers, despite existing fingerprint-level negative memory and per-profile 3-executed-hypotheses bounds. In Fast `38064430286`, 11/11 selected had `llmAdvisorApplied=false`, 9/11 had `collect-more-evidence`. This was a genuine Brain selection gate, not provider code. It does not explain every stalled provider independently.
- Brain-only commits `f81b1c26` and `25dce462` now allow a new, fingerprinted LLM strategy after exhausted generations only when no eligible evolved executor is selected. The existing failed-fingerprint and per-profile executed ceilings still apply; an unversioned advice row cannot reopen an exhausted label. Real planner regression commit `58d5e1b8`; CORE workflow integration `0478d600`.
- **Exact SHA `0478d600` CORE Workflow Gate `38066575038`: SUCCESS**. Job log includes `Exhausted Learning LLM novelty/negative-memory replay passed`; negative, unfingerprinted and executor-precedence cases all pass. Earlier Provider Non-Regression Gate `38066541768` SUCCESS on `58d5e1b8`, before final workflow-only change. No playable provider recovery claimed yet.
- Inspected actual public Brain-LLM guidance branch: prior source `a7de44a7`, model `2ac7ed09`, completed 17 requested but emitted advice for only 11 providers; seven provider/profile groups are already at >=3 distinct executed fingerprints in current memory (e.g. flemmix, mallumv, moviebox, moviesmod, vidfast, yflix, animesultra). The new planner guard can only help *novel* advisor hypotheses; exhausted executor families need new Brain FORCE executable strategies, not loosened memory. Existing Learning `38064727894` on old SHA `9da7fd42` remained in FORCE materializer step 35 at last check; never use that run as proof of the new planner fix.
- Real provider repair completion remains **0** this iteration; current census authority `38063979695` = 22 FULL / 46 and 16 repairQueue. Next full-cohort Learning must run against current SHA, inspect generated/compiled/applied executor bytes, identity-correct terminal playback, negative persistence, and current-SHA nonregression. No manual provider patch.

## 2026-10-10 — Repair funnel checkpoint: zero accepted programs despite complete FAST handoff

- Inspected GitHub Fast Repair run `38064430286` (source `6666cabe6`): 11 selected, 0 raw accepted, 0 accepted compiled, 0 lab fixed, 11 deferred to Learning, `no_new_repair_experiment`, publication disallowed. The run's workflow SUCCESS means handoff completed, not a provider repair. Persisted queue remains 16; latest authoritative census still 22 FULL OK / 46, 16 repairQueue at `38063979695`.
- Run log confirms all 11 were dispatched to Learning (`38064727894`); this does not establish Learning success or terminal playback. CORE Gate `38065058989` was cancelled; Provider Non-Regression `38065058915` succeeded as a control-plane-only no-op (provider rematerialization and census steps skipped). Do not call this exact SHA comprehensively validated.
- Commit `31a78f89` corrected a stale 17-provider header in the full-cohort Learning trigger (actual target list is 16). Verified updated file and main commit through GitHub. This is trigger metadata consistency only, NOT a cure for model generation/selection or proof of live playback.
- Next causal work: inspect full Learning run output and model acceptance rejection signatures, fix a demonstrated shared Brain generation/selection/materialization fault, prove one executable Brain-applied playable repair per family, then all 16 with non-regression. Remote Desktop Commander Mac was offline; GitHub file/Actions access available. Do not manually patch provider implementations.

## 2026-10-10 — Scalable FORCE preflight and exact parent/child context on 16-provider cohort

- Exact latest sharded census **38063979695** on **9a1a43e8** reports **22 FULL OK / 46, 16 repairQueue** (down from 21/17). Commit subjects containing `25/46` are aggregate census processing figures; they must NOT be interpreted as 25 FULL providers. 16 active cases: `4khdhub,allanime,allwish,animekai,animesalt,animesama-co,animesultra,animevost-fr,animevostfr,flemmix,mallumv,moviebox,moviesmod,uhdmovies,vidfast,yflix`. Five causal families `route_proven_gap,chain_terminal_gap,provider_transport_gap,candidate_replay_gap,search_gap`; do not mistake this metadata for playback.
- Real multi-provider FORCE failures **38058171516** and **38060072623** repeatedly raised `materialized contract validation failed: tests/brain_architecture_force_materializer_test.py`. Precise traceback was line 141, `assert 'new_strategy_id == "route_transition_graph_v1"' in focused_ctx`, after the Brain had expanded runtime profiles to v10+. The fuzzy `_focused_source_snippet` ranked lexical/historical-vN references and could return the wrong execution neighborhood. Later CORE Gate **38064897551** exposed a second case: evolved `v2` context failed to include its required exhausted `v1` parent (test line 186). These are **Brain context-selection/self-test faults**, not provider code failures.
- Brain-only commits **c35e00c2** then **c756a1c4** select the **unique exact executable guard** rather than overlapping names, and use the **exhausted parent first** when `requiresNewExecutableRepairProfile` is true. Real-source test includes v1/v10 collision and separate child/parent cases. For fresh FORCE evolution the Brain now executes the baseline contract tests **before** invoking 7B; a broken baseline emits `FIELD_BRAIN_ARCH_FORCE_OWNER owner=baseline-brain-contract model_calls_skipped=true` instead of paying several 7B corrective rounds for a failure Qwen cannot repair. Real materialized code remains strict, transactional and rollback-tested. Provider Non-Regression Gate **38064897612** SUCCESS on c35; CORE Gate on c35 failed at the second parent-focused assertion, which c756 corrects.
- Current-SHA **CORE Workflow Gate 38065058989** and **Provider Non-Regression 38065058915** were pending final verdict at this checkpoint. No claim of full Brain repair/terminal playback from these infrastructure changes.
- An updated full-cohort Learning trigger for **all 16**, grouped by causal failure family and retaining exact title/episode terminal-playback and multi-runtime checks, is ready; never relaunch stale `anime-ultime` (not in current repairQueue), nor repeatedly spend model retries on baseline contract failures. `MEMORY.md` records both diagnostic evidence and the exact tested SHAs. Scale to 800 hubs only after one representative **per failure family** achieves current-byte executable patch, correct identity and playable terminal and the negative experience is persisted.
- Additional architecture recommendation: record structured request attempts and precise network failure classes rather than classifying HTTP/DNS/TLS, WAF, parser, runtime and content-identity as the same provider breakage; use per-family executable Lego and strict network/content evidence. No provider manually patched.

## 2026-10-10 — Bounded planner anchor must not grow with generated siblings

- Latest exact census run `38049680394` (source `5be96b4f`): **21 FULL OK / 46, 17 repairQueue**. Fast Brain `38048175154`: **12 selected, 0 accepted, 0 compiled, all 12 deferred**. Autopilot still fans the 17 into FAST 12, REMAT 2, LEARNING 3; dispatch coverage is not the blocker.
- Live six-provider FORCE `38048466004` failed at materialization with `ValueError: architecture FORCE planner parent edit exceeds bounded unique anchor`. Cause confirmed in live `engine_v2/scripts/plan-repairs.mjs`: `route_proven_gap` family has grown to **1185 characters**, exceeding `MAX_FIND=600` because `complete_evolved_profile_wiring` copied the whole group prefix through the parent row as its replacement find string. Every new generated `vN` expanded this prefix and guaranteed eventual failure. No provider is directly at fault; retrying Qwen was not the solution.
- Generic Brain materializer update anchors the planner replacement to the **unique parent row** and widens backward only when needed to distinguish duplicates, with hard 600-character cap and fail-closed ambiguity. This makes newly installed strategies independent of number of previous siblings; new synthetic regression covers a >1KB causal-group prefix, exact 3-file wiring, source rollback and no manual provider patch.
- This is a Brain infrastructure change, NOT provider repair. Completion still requires tested SHA, actual generated strategy, selected current-byte applied executor, correct-title terminal media playback and non-regression across all repair families. Large 800-hub expansion requires fixing generation/selection and causal progress—not repeatedly scheduling the same failed 12.

## 2026-10-10 — Resolve GitHub 21k Repair workflow dispatch validation

- The V6 recognition workflow unexpectedly emitted **failed no-job dispatch checks 38017398618 and 38017634441** on infrastructure commits `6bd6d789` and `27e1837e`. A real Brain FORCE promotion run `38017039516` exposed the exact GitHub HTTP 422 cause: **`(Line: 1589, Col: 14): Exceeded max expression length 21000`**. The oversized step was `Persist Repair census state`; GitHub Actions officially caps each `run` value at 21,000 characters. This is an infrastructure blocker, not evidence of a failed provider.
- The workflow was restored to known-good content in `5f953d67`. Its compact evidence-retry integration is now budgeted at **19,894 characters after removing 15 obsolete shell comments**, leaving headroom rather than embedding another oversized inline block. The actual retry logic stays in the checked-in standalone `scripts/persist_repair_race_evidence.sh`. Provider-positive stale publications still fail closed.
- A new static regression test `tests/provider_recognition_workflow_run_limit_test.py` scans every workflow `run: |` block and enforces a 20,500 character budget (500 characters below GitHub hard limit), plus checks the safe evidence-only fallback is wired. `tests/provider_stale_repair_evidence_push_test.py` simulates real concurrent Git publishers. Both must pass Core Gate on the exact resulting SHA.
- Older Brain LLM guidance SHA `29a18686` was discarded when current Brain LLM was `2ac7ed09` (correct fail-closed); the current private-guidance generator `38015677846` is working on the newer Brain SHA, still not a proven provider repair. Last authoritative census remains 21 FULL of 46 with 17 repairQueue. Do not claim a release or real playable recovery from a workflow-only fix.

## 2026-10-10 — Compact evidence persistence invocation after workflow validation anomaly

- Initial Brain evidence-race commit `6bd6d789` introduced an 11-line inline persistence fallback inside the large V6 GitHub Actions workflow. GitHub reported a no-job failed workflow check `38017398618` at that commit, before runtime tests could run. Pending formal verdict, invocation has been reduced to one bounded shell command calling the independently unit-tested helper, with stale provider publication still fail-closed. Do not claim this is validated until the current-SHA workflows and live replay pass.
- Incident scope: GitHub action validation/integration, not provider or Brain strategy success; main reset/retry itself remains non-publishing evidence only.

## 2026-10-10 — Preserve Brain Repair experiments after concurrent main advancement

- Inspected authoritative main `f83a3894` and sharded census `38016451880` on `fbf94ed8`: **21 FULL OK / 46**, **17 RepairQueue**, no newly verified playable stream despite 17-provider Autopilot.
- Real recognition run `38016186246` generated a Repair result and rebased its ledger onto `cf2635c6`, but lost a second race at `git push origin HEAD:main` after a concurrent CI run advanced main. GitHub Actions completed FAILURE with `non-fast-forward`, and no per-run Brain memory landed on main. This is a cross-provider data/persistence defect, not an individual provider bug.
- New Brain-only `scripts/persist_repair_race_evidence.sh` is invoked if final Repair evidence-only push races; it discards **all** stale provider/census/publication mutations, fetches latest main, and commits only the immutable per-run Brain experiment report plus a separate `publicationAllowed=false`, `currentBytePlaybackAuthority=false` provenance record, retrying at most 3 times. Any real provider candidate branch still fails closed and needs fresh current-byte retest; no stale positive proof is promoted.
- `tests/provider_stale_repair_evidence_push_test.py` recreates two concurrent Git publishers with differing provider-code/census contents, then proves the winning newer code/status is preserved exactly while the older negative experiment becomes discoverable on current main. Tests are added to Core Workflow Gate.
- Separately, canonical Repair run `38016186246` rejected external Brain advice SHA `29a18686` after Brain LLM main moved to `2ac7ed09`; this was a legitimate stale-guidance safety decision, but the fallback used no current external model recommendations. The **Brain LLM private-guidance run `38015677846` is now active on the new model SHA**; wait for its complete artifact/validation rather than weakening provenance checks.
- Last archived 12-provider Fast artifact `11655853469` confirms `no_new_repair_experiment`, 0 raw accepted programs, 0 compiled programs, all 12 deferred to Learning. This is a generation/selection bottleneck; a green Fast or a larger provider batch does not constitute recovery. Keep the 17 split by repair family and test current title/season/episode playback before any promotion.

## 2026-10-10 — Stop stale Brain vN contracts and evidence-only Fast retry loops

- Repo `main` checkpoint `4230f838ffb9`, exact current census **21 FULL OK / 46, 17 RepairQueue**, source `11fb9380e8ed`. Automated 17-provider portfolio is partitioned across **12 Fast Brain**, **2 candidate Remat** (animesama-co/animevostfr) and **3 Brain Learning** (allwish/animekai/uhdmovies), with additional FULL-provider completeness issues in other lanes. Full Fast run `38009526194`: all **17 processed**, 0 raw accepted programs, 1 lab-only playback, 0 validated/published; remaining still 17. A new `terminal_transition_graph_v3` was generated/published by Brain while current stream proof remained unverified.
- Genuine **preflight regression**: Recognition V6 `38012845141` on `c2e0838f` failed because `tests/brain_final_experiment_generation_test.py:183` hardcoded direct v2 -> terminal_request_program_inference after v1,v2 observed failures, even though Brain now has installed `terminal_transition_graph_v3`. Similarly Learning `38012926019` and CORE Gate `38013028835` failed because `tests/brain_architecture_deferred_cohort_test.py:301` hardcoded v3 as always new/uninstalled. These are **test assumptions invalidated by successful Brain evolution**, not proof v3 is broken.
- Brain-only commits `d790cd3c` and `4230f838` make preflight tests enumerate and replay **all actually installed `terminal_transition_graph_vN` profiles**, demanding distinct implementation fingerprints and execution-observed negative outcomes before falling through to new strategy families or permitting the first truly new vN. This must remain valid for future Brain-generated v4/v5 without hand-editing tests after each promotion. Provider Non-Regression Gate `38013107147` SUCCESS on `4230f838`; full Core Gate `38013107207` was still running at checkpoint.
- Further generic loop guard: Fast Repair previously requeued **every** obsolete-SHA job, even when `main` moved solely for unchanged census/history metadata and **0 repairs** had been accepted. The Brain should not run identical failed work repeatedly. The Fast workflow now checks ancestor SHA, unchanged runnable/provider/Brain code, negative/positive model memories, repair batch/experience/target triggers, and semantic census repairQueue/status. If nothing causal changed and production publication was not authorized, it skips redundant requeue **after Learning debt has already been dispatched**. Any changed executable, model memory or provider status still triggers fresh attempts. It never imports stale positive proof nor disables real repair.
- Regression tests cover new preflight generation contracts, stale no-op Fast guard, and acceptance boundary (lab-only media without compiled accepted program remains Learning oracle, not a published repair). No provider source manually patched. Code changes require same-SHA CORE/Provider Gate and real current-byte playable terminal media before promoting even one of 17 as FULL.

## 2026-10-10 — Lab playback without compiled Brain repair is not a candidate

- Current `main` observed `72bebefe1f71`; latest authoritative census **21 FULL OK / 46, 17 repairQueue**. The canonical Autopilot `38011800799` correctly dispatched all **17 RepairQueue providers** across causal owner lanes: **12 FAST**, 2 REMAT (animesama-co, animevostfr), **3 BRAIN_LEARNING** (allwish, animekai, uhdmovies). Four additional completion/quality targets (coflix, hindmoviez, kehflix, vidlove) are Learning only and do not inflate 17. Autonomous jobs running on prior SHAs must not be credited to this code.
- Downloaded and inspected the **real 62.8 MB Fast Brain artifact `11653028447` from run `38009526194`**. All 17 providers processed across three waves; **0 raw Lab accepted repairs**, **0 acceptedProgramCompiledProviders**, but **`animevostfr` fixedInLab=1**, followed by retest reverting to CANDIDATE OK; **0 validated/published**. The positive came from sandbox playable health with no durable accepted/compiled provider program, so labeling it a newly fixed repair was misleading and caused no-op materialization/retest.
- Brain pipeline cause in `scripts/run_provider_brain_repair.py`: `materialize_targets_this_wave = (fixed_this_wave - accepted_program_providers) | compiled_this_wave`, so a lab healthy provider with **zero accepted program** could be materialized and sent as a candidate. `all_fixed` likewise recorded this as fixed. This is a general acceptance-to-publication leak, not an individual animevostfr fix.
- Brain-only correction: `classify_lab_playback_durability` distinguishes **(playable and accepted-program-compiled)** from **lab-only oracle**; only compiled accepted repairs may trigger materialization; lab-only positives are preserved as exploratory evidence, explicitly flagged `labOnlyWithoutCompiledRepair`, and handed to Learning for a genuinely durable generative repair. No no-op rematerialization, no false provider candidate/retest, no weakening content identity or playable gates. Representative tests replay the observed `fixed={animevostfr},compiled={}` case and durable mixed cases.
- Additional root blocker shown in the artifact: 8+ providers entered `transport_blocked` or exhausted profiles with zero accepted candidates; a green workflow or HTTP 200 search alone is never proof of playable content. Continue per-family repairs and current-byte provider replay. **Repair count remains 17** until verifiable media, not merely because the funnel now classifies honestly.
- This infrastructure change is subject to exact-SHA CORE/Provider Non-Regression Gates. Do not mark resolved before they pass, and do not count the lab-only oracle as a production candidate.

## 2026-10-10 — Unblock all 17 RepairQueue providers: stale installed-profile CI contracts

- Verified real GitHub remote main `de18799510fd1474ff02436852eb9aa78064e003` and latest census **38008325952**: **21 FULL OK /46, 17 repairQueue**. Full queue: 4khdhub,allanime,allwish,anime-ultime,animekai,animesalt,animesama-co,animesultra,animevost-fr,animevostfr,flemmix,mallumv,moviebox,moviesmod,uhdmovies,vidfast,yflix. Real failure families include candidate replay (animesama-co/animevostfr), terminal chains (allanime/mallumv), regressions (animekai/uhdmovies), WAF/HTTP/timeout route-to-terminal (remaining providers). One representative-only FORCE is insufficient coverage.
- Runs **38008819573** (Fast Repair) and **38008821362** (Learning) FAILED in preflight before any repairs. Fast: `tests/brain_final_experiment_generation_test.py:158` assumed fallback directly to terminal_request_program_inference_v1 after exhausted terminal_transition_graph_v1. But `terminal_transition_graph_v2` was subsequently generated, registered and installed: the planner correctly selected **v2** with implementation fingerprint and current-byte replay. Learning: `tests/brain_architecture_deferred_cohort_test.py:198` demanded a new FORCE v2 blueprint, even though v2 already exists as an executable; the architecture builder correctly labels it **already-installed-profile-replay-first** and refuses duplicate promotion.
- Corrected Brain contract tests at exact HEAD: v1 exhausted + v2 installed -> replay v2 first; only **executed negative** evidence for v2 then authorizes next request inference family; missing v2 -> FORCE-promotable new v2; installed v2 -> replay without duplicate FORCE; exhausted v2 -> novel v3 blueprint. Preserve playback, identity, non-regression and no-false-FULL gate.
- Both trigger pathways explicitly target all **17 provider IDs**, with Fast Brain 3 bounded waves and Learning 180-minute multi-family queue, not single-provider FORCE. The broad pass still must demonstrate per-provider bytes executed, correct TMDB title/season/episode, terminal playable URL, and preserve final positive families. Network/WAF blocked cases remain explicitly blocked, never fake success. No individual provider or Core stream implementation edited by hand.
- Pending current-SHA CI and actual coverage proof; last validated success count unchanged until full materialized playback proven.

## 2026-10-10 — Stop false Brain progress from repeat search HTTP 200

- Current evidence from canonical FORCE recognition run 37990232966 (SHA b0b87c41): 4KHDHub v3 was executed on exact provider bytes, generated requests and returned zero streams on movie and TV, with zero playable or identity-verified media. Quick-yield remained lookup_only/provider_network_zero_result. The authoritative census is still 21 FULL / 46 with 17 repairQueue.
- Independent OPS 37991013921 reported provider_unreachable/no_provider_request_observed for 4KHDHub on its one published availability fixture, while canonical quick-yield reached HTTP 200 on a provider search page. This is a harness/fixture differential, NOT proof of a universal network outage nor a functional stream.
- Root generic Brain flaw: scripts/runtime_repair.py::compare_exploration_progress previously accepted a greater count of HTTP 200 provider requests as sandbox_diagnostic_progress:provider-requests even when both parent and candidate were at the same search frontier and had zero streams. The real 4KHDHub v3 Deep decision reported exploration_ok=true for provider-requests despite production_ok=false and required_category_playable_proof:movie,tv.
- Generic Brain correction 3c4fe1a8 prevents repeated successful search page counts from promoting a new sandbox exploration parent. A parent with successful requests needs a strictly deeper observed provider-side stage (detail, episode, player, source/media); a first provider request remains initial access evidence. Infrastructure/TMDB stages and model-only labels cannot qualify. Current-byte media playback gates are unchanged. Tests cover first request, repeated lookup, observed detail and infrastructure-only false positives.
- Post-fix harness schema alignment: inspected OPS run 37991013921 health-results.json (41 provider results). Actual network_observations stages include content_lookup (81 rows), search (19), player (19), origin_probe (4) and episode (2). The Brain frontier now explicitly treats content_lookup as search (depth 1); origin_probe alone is not a detail stage. A new targeted test proves repeated HTTP 200 content_lookup pages cannot masquerade as downstream detail/media progress. This is grounded in real harness bytes, not only invented synthetic stage labels.
- OPS availability classified 4 healthy, 12 no_streams, 13 no-provider-request unreachable, 6 blocked and 6 unavailable out of 41 published providers. This is a distinct one-fixture availability snapshot, not the 46-provider census and not proof all problems share one owner.
- Next Brain-only representative cohort: animevostfr, animesama-co (candidate replay); allanime, mallumv (terminal chains); uhdmovies, animekai (regressions). Demand model-generated applied candidate, title/season/year-correct playable terminal, non-regression and persistence. Do not hand-edit providers or promote lab-only candidates. Resume 4KHDHub only after actual on-site title/detail evidence, not another identical lookup-only trial.
## 2026-10-09 — Localized TMDB alias starvation in generic Brain route recovery

- Latest current-byte 4khdhub diagnostic (run `37983399735`, artifact `11642153694`) reached TMDB and 200 HTML `movie-card` search, yet no detail follow-up and **0/8 streams**. The movie search query contained localized French `La Colonie 2021`, but the provider may index the canonical/original English title. This is a **hypothesis requiring real replay**, not proof the site carries the requested title.
- The generic adaptive V7 JavaScript already uses TMDB `original_title` and `alternative_titles`, but `recover()` consumed the entire global `searchLimit <=12` inside the *first title's* many `searchPaths`: aliases never ran. This explains why a strategy with 12+ routes could still be `lookup_only` despite the correct title alternatives in memory.
- Brain/Core infrastructure patch: for model-generated route-graph `v3+` in `search_gap`/`route_proven_gap`, enable existing strict TMDB alias recovery; inside the generic JS search loop reserve at least one query for each later title, while keeping all calls globally <=12 and preserving provider origin/identity/terminal-media checks. Test `brain_alias_search_fair_share_test.py` runs actual generated JavaScript against synthetic 200 responses and asserts localized + original title both queried, <=12 site requests, and no fabricated media.
- Prior Brain-only fix `5874a4ae` preserved provider-owned search/recipes and V2 media-response salvage in generated V3; its CORE Workflow Gate `37988669376` first failed solely because a new unit assertion omitted the legitimate terminal-media comprehension, corrected by test-only `1b50e086`. CORE Workflow Gate `37988831900` SUCCESS and Provider Non-Regression Gate `37988831857` SUCCESS on `1b50e086`.
- No individual provider touched and **no newly playable provider proven**. Latest evidence remains **21 FULL/46, 17 RepairQueue**. Next: exact-SHA CI on alias fair-share patch, single representative 4khdhub FORCE v3 execution with source-controlled search/alias order, inspect on-site title match before detail/terminal, and if still 0, do not blindly repeat fixed fixtures; switch Brain to source-catalogue coverage diagnosis.

## 2026-10-09 — Proven v3 playback failure: preserve owned search and salvage in future Brain Lego

- **Real current-byte result, not a simulated success**: FORCE run `37983399735`, tested on `bb3c6b47`, selected and EXECUTED the Brain-generated `route_transition_graph_v3` on `4khdhub`. Deep LAB health shows `no_streams`, **8 fixtures, 0 streams, 0 runtime errors**, `required_category_playable_proof:movie,tv`, `sandbox_diagnostic_progress:provider-requests` only. Canonical candidate not accepted/published; retest+census maintain **21 FULL / 46, 17 repairQueue**, `experiment_variants_exhausted`. Model-generated/published strategy v3 is real; playback is **NOT** repaired.
- Downloaded the actual current-run artifact `11642153694`, inspected `provider-v3-quick-yield.json` and `automation/provider-route-recovery-v6-targeted.json`. Two representative fixtures (`The Colony` movie and `Revenant` TV) each made exactly **2 HTTP requests** (TMDB then provider search). TMDB 200 JSON and `https://4khdhub.one/?s=...` 200 HTML with `movie-card`/links/format metadata; **0 detail/player traversal, 0 announced streams**, `debug_progress_stage=lookup_only`, `provider_network_zero_result`, zero evidence of a WAF challenge. This is a **search-to-matched-content/route-binding gap**, not a proven network transport outage or a streaming decoder error. Site inventory for those exact titles is unconfirmed: no fabricated fixture success or arbitrary card link may be promoted.
- Cross-layer Brain loss confirmed: current v3 program consists of `peer_search,generic_search` with peer/positive direct routes and excludes `configured_search,learned_search`; `scripts/adaptive_runtime/runtime_repair.py` enabled `runtime_response_salvage` for parent `route_transition_graph_v2` but NOT the generated v3. Thus a generated successor discarded two classes of prior provider-owned discovery/media-extraction Lego even though its algorithm compiled and ran.
- Brain infrastructure change (not provider manual fix): generated route v3+ now retains bounded `configured_search,learned_search`, provider-owned detail and current request recipes before LLM-selected peer/generic discovery, and inherits its route-family response salvage. The typed `recoveryProgram` compiler also enforces owned fallback for future generated profiles instead of silently replacing the current provider's search contract. All existing identity/provider-origin/terminal playable checks remain unchanged. Regression tests include v3, future v10, original v2 unchanged, and a model proposal containing only peer/generic choices.
- Next validation: exact-SHA Core contract/non-regression, one current-byte representative Brain replay, inspect whether search result yields **matched detail** then actual player/terminal media and title/season/year identity; if it stays `lookup_only`, pivot Brain to genuine catalogue-title route observation/selection instead of repeating the same 4khdhub fixture or claiming FULL. For speed and coverage also prioritize candidate lanes (`animevostfr`, `animesama-co`) with stronger live playable evidence; no provider manual hotfix. No FULL promotion without current-byte terminal playback.

## 2026-10-09 — Representative FORCE preflight fixture sequencing corrected

- Real targeted FORCE `37983048761` on `7b74a739` FAILED before any provider execution: `tests/brain_final_experiment_generation_test.py:173` referenced synthetic `second_escalation_failed` before its definition (introduced by the new preference regression test). This is a TEST/CI preflight bug, not an actual v3 stream failure. No provider bytes modified, no stream result established.
- Brain-only test fix `51963f8f` moves the already-failed-preference assertion below the executed negative fixture's definition; the earlier preferred-profile and unknown-profile checks already passed before the NameError. Re-dispatch one targeted `mode=force`, `preferredProfile=route_transition_graph_v3` 4khdhub run on exact updated SHA; do not claim playable success until selection, executed bytes and terminal correct-title media are verified. Retain `21 FULL / 17 repairQueue` until fresh census.

## 2026-10-09 — Deterministic representative execution of Brain-generated architecture

- Current census still **21 FULL / 46, 17 repairQueue**; real 4khdhub replay `37979345850` after generated/published Brain v3 yielded **0 streams**, and actually selected old `html_class_token_exact_v1`. Earlier `37980350466` and `37980458319` were contract-blocked by fake unobserved negatives; these tests are fixed on `1eabb376`. CORE Workflow Gate `37981955352` and Provider Non-Regression Gate `37981955327` passed on `1eabb376`.
- Force promotion previously dispatched representative replay with `mode=repair` (one wave) and did not set `--architecture-force`; changed `brain-learning-lab.yml` and `run_provider_repair_pipeline_v6.py` on `1eabb376` to use bounded three-wave FORCE and explicit architecture mode without accepting weak streams.
- **Second root cause**: even FORCE's three waves can retest the first historical candidates and never execute newly generated v3, because the planner's `search_gap` causal list has v3 after several older profiles. A new opt-in **Brain-generated strategy replay preference** is passed from the successful forcePromotionEligible blueprint through workflow_dispatch or the audited trigger file to the canonical FORCE only. The Brain planner reorders **only its currently installed/causal-eligible candidate set**, selects the approved strategy first **if not exhausted by execution-observed negative memory**, and ignores unknown or previously exhausted preferences. Normal Repair/Fast/Learning ordering is unchanged; no provider ID/hub bypass, manual provider patch, URL or fabricated media.
- Files: `brain-learning-lab.yml` computes the preference from the model-authored FORCE blueprint and representative provider; `provider-recognition-repair-v6.yml` passes the validated selector only in FORCE; `run_provider_brain_repair.py` strips it outside explicit `--architecture-force`; `brain_repair_runtime.py` passes a typed candidate hint; `plan-repairs.mjs` performs causal/negative gating; tests `brain_final_experiment_generation_test.py` and `brain_architecture_force_promotion_test.py` verify first selection, unknown rejection and observed-negative suppression.
- This is a generative Brain pipeline selection/validation correction. It cannot declare 4khdhub FULL until the generated v3 is actually executed on current bytes and returns title-correct playable terminal media. Run new exact-SHA CI and targeted 4khdhub FORCE; if v3 executes but produces no playable media, persist failure and pivot to causal transport/provider-authority diagnosis instead of looping over old strategies.

## 2026-10-09 — Stop false provider recovery loops: observed-negative contract and representative FORCE replay

- Authoritative latest census after Brain v3 promotion and retests (e.g. `37978493066`, plus later canonical repair commits): **21 FULL OK /46, 17 repairQueue**. Green Brain FORCE generator `37977915650` produced and promoted `route_transition_graph_v3` in `8904cc26`; current-byte 4KHDHub canonical Repair `37979345850` still ended `no_streams`, **0 validated**, with the lab trying `html_class_token_exact_v1` first. The new v3's executable presence is not real-media recovery.
- Two fresh cross-provider workflows `37980350466` (Recognition V6) and `37980458319` (Fast) FAILED before Repair on `tests/brain_final_experiment_generation_test.py:145`: test created a historical negative for `terminal_transition_graph_v1` without `executionObserved=true`. New Brain correctly refuses to treat unexecuted suggestions as exhausted, but fixture incorrectly expected it to skip the profile. Test now supplies execution proof for all genuinely executed negative rows, plus tests that an unobserved candidate does **not** suppress a profile. Never weaken the runtime guard.
- Real architectural mismatch: `.github/workflows/brain-learning-lab.yml` dispatched every newly promoted Brain architecture for representative proof with `-f mode=repair`. `scripts/run_provider_repair_pipeline_v6.py` limited Repair to **one wave**, and did not propagate `--architecture-force` into `run_provider_brain_repair.py`. Consequently a three-file Brain v3 promotion was followed by old one-shot Repair, which never demonstrated actual new-strategy selection/use on 4KHDHub. Fix uses `-f mode=force` for exactly one representative and forwards `--architecture-force`, enabling the bounded **three-wave** Brain replay with the same strict identity/current-byte/terminal playback and publication gates. No manual provider code fix, no fake fixture promotion.
- Exact HEAD before intervention: `0ded3408f9e8eb3471dce51cb8afd3129696f9c3` (already includes `81017ec9` convergence and `0ded3408` census metadata). Changes affect only Brain orchestration, tests and documentation. Pending verification: Workflow Gate and Non-Regression on new SHA, representative FORCE run exercising new profile, terminal playback evidence; maintain **21/17** until proven otherwise. Investigate route/network reality separately if all new strategies still return no_streams. Avoid repeated blind launches.

## 2026-10-09 — Root Brain selection bug: global strategy fingerprint invalidates exhausted profiles

- **Real post-harness Repair test** `37979345850` on exact `1a081808` SUCCESS as a workflow, but **4khdhub remains ROUTE PROVEN, 0 playable movie/tv, 0 accepted**. Canonical logs `113985588180` prove selected strategy was **`html_class_token_exact_v1`**, not new `route_transition_graph_v3`, followed by `required_category_playable_proof:movie,tv` and `provider_network_zero_result`. No identity-matched terminal and no provider promotion. Current census `37978493066`: **21 FULL/46, repairQueue 17**.
- Causal planner/root defect: `engine_v2/scripts/plan-repairs.mjs::strategyImplementationFingerprint(profile)` hashed the **entire `scripts/adaptive_runtime/runtime_repair.py` and unrelated profile-specific modules for EVERY strategy**. Publishing v3 therefore changed old html/v2 implementation hashes without changing their algorithms, so old **executionObserved rejected** rows on 4khdhub (`html_class_token_exact_v1` twice, `route_transition_graph_v2` once) no longer matched. Brain restarted stale strategies instead of testing newly model-generated v3. This is generic across all provider families and any novel profile addition, a severe explanation for repetitive zero-progress loops.
- Brain-only remediation: `engine_v2/src/strategy-fingerprint.mjs` builds profile-scoped fingerprints from **shared runtime code plus only the requested Python strategy branch**, ignoring selector registry membership and unrelated siblings; global shared executor/patch dependencies still contribute to correct invalidation, whereas unrelated html-specific sources don't invalidate other profiles. Production post-exhaustion selection treats **any execution-observed failure of the same versioned profile** as durable negative, including legacy whole-file hashes; new executable behavior must have distinct v3/v4 ID. Never treat unexecuted `profile_unavailable` as negative proof.
- Regression test `engine_v2/tests/brain-strategy-fingerprint.test.mjs` exercises synthetic and real runtime: adding unrelated child does not change parent/peer/html/v3 fingerprints, but parent or common helper changes do; `tests/brain_llm_advisor_execution_test.py` verifies exhausted legacy html/v2 rows **force the planner to advance to v3**. Contract runs in CORE Gate and canonical Repair preflight before expensive network/materialization. This does NOT bypass playback/identity/provider proof, only stops redundant strategy resets.
- Next: validated SHA Repair must execute actual new `route_transition_graph_v3` on representative 4khdhub and inspect sandbox requests vs WAF/network; if no playable terminal, persist its negative signature and evolve Brain Lego based on empirical diagnostic; then family representatives and all 17. Never manually patch providers to mask a Brain failure. No FULL credit without current-byte playable identity proof.

## 2026-10-09 — Model-authored v3 promoted; Repair harness must auto-scale exhaustion proof

- **Verified first genuinely model-authored Brain FORCE executable promotion:** `LEARN 37977915650` on source `cb6b5d09` completed materialization of `route_transition_graph_v3` after the registry-scoped fix. Model authored typed `recoveryProgram` (fingerprint `9bcd98df9bc2a498a3efda585577399b200eae15a1751b393364e87e8cb57fc3`), compiled and materialized all 3 Brain sources, applied the exact Git patch, and passed independent post-apply selector/planner/executor guard. Brain promoted `8904cc26a48d696c31262b6e5ad4589fc7e54462` to remote `main`, 5 files modified. Model program is retained in GitHub artifact `11639134437` and contains prioritized peer/generic search, peer/positive direct routes and current/positive/historical/provider/peer request recipes; did NOT manually edit any provider. v2 retains original code.
- **Live Repair replay** `37978457715` on *correct new v3 SHA* `8904cc26` FAILED before provider runtime playback at preflight `Prove one canonical Learn Force repair implementation`. Exact error `tests/brain_llm_advisor_execution_test.py:236: AssertionError('post-exhaustion strategies did not converge')`. Real planner had **12** valid post-exhaustion strategy candidates after Qwen inserted `route_transition_graph_v3`, but the test used hardcoded `for _attempt in range(12)`, leaving no *thirteenth* final replan to prove convergence. This is a generic **Brain harness dynamic-family growth defect**, not proof the generated v3 fails or succeeds. Older replay `37978451946` on source `cb6b5d09` without v3 was `no-proven-route`/`provider_network_zero_result`, 0 playable; do not conflate its SHA.
- Brain-only test fix `259661c3` derives loop bound from actual `postExhaustionCandidateProfiles` inventory + one final convergence probe and asserts unique observed profiles; no widening or shortcut of acceptance/exhaustion criteria. Stage further generic architecture guard: run this dynamic planner-exhaustion test on **materialized candidate bytes before Git promotion**, after every `git apply` and on core workflow gate, to reject stale hardcoded inventory tests before future novel Brain Lego publication.
- Next evidence: targeted Repair run on updated HEAD (post guard) must actually execute v3, return correct-title terminal playable media, pass identity/quality/headers and non-regression, and materialize candidate before a FULL promotion. Latest census observed **21 FULL /46, repairQueue 17**, unchanged; provider FULL remains **unvalidated** despite Brain architecture breakthrough. Main has evidence-only commits following `8904cc26`; their descendant relationship/strategy bytes were verified.
- No provider manual code patch, no PR creation. Preserve successful model program fingerprint and failed harness signature as Brain training/RAG provenance. Persist via `MEMORY.md` now; long-term report-to-memory ingestion remains an open Brain improvement.

## 2026-10-09 — FORCE runtime selector false ambiguity on real parent profile

- Re-read GitHub remote `main`, active `MEMORY.md`, census, latest sharded runs and failed/successful Labs. Main before correction `59bdadd8`, current tested Brain fix `43a2b676`. Exact census `37976366881` on `4a559cd2`: **21 FULL OK / 46**, **17 repairQueue**, no full playable provider recovery; `37972901385` Fast selected 12 and validated 0. No provider/manual Core bytes changed.
- Live 7B typed-Lego FORCE `37973552349` FAILED with three identical `architecture FORCE adaptive runtime parent anchor ambiguous` materialization errors after targeting `vidfast`; failed report blueprint artifact confirms target profile `route_transition_graph_v3` evolving installed `route_transition_graph_v2` (same family shared with 4khdhub, others). These retries asked Qwen to fix an **internal deterministic Brain bug**, not model code.
- Reproduced on actual `scripts/adaptive_runtime/runtime_repair.py`: exact parent registration line `    "route_transition_graph_v2",` appears **twice legitimately** in the full file: once inside `POST_EXHAUSTION_STRATEGY_PROFILES` and once in runtime strategy priorities. `_register_generated_runtime_profile` incorrectly required the line to occur only once **globally**, so a selectable, registered parent was rejected after compilation. Likewise `validate_blueprint_implementation` incorrectly checked global line multiplicity for the new profile. `terminal_transition_graph_v1` also has two legitimate references, proving a cross-family Brain infrastructure flaw.
- Commit `43a2b676` scopes parent and child uniqueness strictly to the actual selector set, and inserts by source span inside that set rather than global `str.replace`; preserves unrelated lists verbatim. Updated representative Brain synthetic test reproduces the extra parent reference, asserts unique child registration, idempotent registration, untouched external list and exact transactional source rollback. Fail-closed ambiguity within the actual registry remains.
- Additional generic FORCE efficiency guard: errors caused by deterministic Brain-owned registry, planner and selector anchors now emit `FIELD_BRAIN_ARCH_FORCE_OWNER owner=brain-scaffold` and **skip model correction rounds**. This prevents repeating the 37973552349 three-times-LLM cycle for errors a different LLM answer cannot change; syntax/algorithm failures remain model-correctable.
- Provider Non-Regression Gate `37977336492` SUCCESS on `43a2b676`; CORE Workflow Gate `37977336463` advanced beyond contract validation to native provider loading at this checkpoint. This is **Brain wiring validation**, not a successful provider. Next: new targeted 4khdhub typed FORCE on the final tested main SHA, inspect model program fingerprint, four selectors, applied Git patch, actual sandbox playback and current-byte census, then family representatives. No false FULL or manual provider patch.
- Independent Brain Learning `37974629444` completed workflow SUCCESS on `4a559cd2` but did not prove an executable materialized profile or a newly playable provider; do not promote from administrative workflow success. Ongoing new SHA census and Fast runs must not be credited to HEAD unless their SHA matches.

## 2026-10-09 — Replay typed FORCE program with persistent exact strategy fingerprint

- The local 7B was repeatedly unable to emit a valid novel Python `branchBody`: live run `37965988796` failed on selector references/invalid guard/no executable behavior, despite previous prompt/AST fixes. Therefore the Brain now exposes strict `recoveryProgram` Lego selectors with no direct Python/provider code generation; compiler accepts source enums, trusted routing/request helpers, observed transition modes, role order and bounded budgets, rejects tautological exhausted v2 plans and all arbitrary identifiers/URLs. Actual playback is still required to establish value.
- Persist the **model-authored structured program and deterministic SHA-256 program fingerprint** in the FORCE report as non-authoritative replay evidence. Allow the exact saved program to be replayed through the same 4-gate materializer using `--response-file`; retain legacy approved edit replay but never bypass strict validation. This addresses a separate experience gap: prior reports recorded only a changed-files list, not the strategy that produced it.
- New representative request: 4khdhub v3, exact typed model response -> bounded compiler -> unchanged v2 guard -> 4 selector gates -> materialize/patch/apply -> provider current-byte replay -> identity-correct playable terminal stream -> non-regression/census. Until then, census remains **21 FULL / 46 and 17 RepairQueue**. Do not claim success from structural syntax or GitHub workflow green.
- The current strategy compiler is committed on `fd3556a5`; Provider Non-Regression Gate `37967731629` SUCCESS; CORE Workflow Gate `37967731482` was still executing when this follow-up was prepared. Attribute fresh FORCE and CI to their actual tested SHA.

## 2026-10-09 — FORCE typed 7B Lego program replaces fragile raw Python body generation

- Revalidated current Force Lab `37965988796` on SHA `4d9c3cea`: FAILED despite successful 4-gate contract/security pipeline. Qwen 7B returned (1) executable Brain-owned strategy selector, (2) invalid guard syntax, and (3) non-executable body across the three attempts. A strict fail-closed validator correctly blocked materialization; no provider fix was generated. This establishes that the unreliable **raw Python branchBody generation contract** is the repeated bottleneck, not an individual provider bug.
- New generic Brain-only approach: the local advisor must produce a **typed declarative `recoveryProgram`** selecting prioritized route sources, direct/positive/peer evidence sources, request recipes, terminal-focused filters, causal transition strategy, role preference order and bounded search/request budgets. The Brain compiler turns those model-chosen Lego decisions into executable Python under a unique new sibling guard, then wires the JS planner, Brain registry and adaptive runtime selector. Strict source enums/limits, schema checks, v2-novelty enforcement, Python parsing, materialization transaction, actual-current-byte playback and terminal content identity remain mandatory. There are NO hard-coded individual provider fixes, no generated URLs/domains/secrets and no status upgrade from strategy creation.
- New compiler `scripts/brain_force_strategy_program.py`, associated `tests/brain_force_strategy_program_test.py`, schema and materializer adaptions in `scripts/brain_architecture_force_materializer.py`, 7B typed tests and CORE Workflow Gate integration are staged in one main change. Legacy `branchBody` only remains replayable as old memory; current Qwen output schema strictly requires `recoveryProgram`. Initial request deterministic, rejected-plan retries bounded with slight diversification, and causal observations/negative memory supplied as priors.
- This is a Brain infrastructure change requiring exact SHA CI and real FORCE proof; **21 FULL OK / 46** and **17 repairQueue** remain current. Five-provider Fast `37965551875` ended `0 accepted`, with one LAB-only animevostfr candidate that failed current-byte retest. Never claim provider recovery from generated code or green CI alone.

## 2026-10-09 — Restore bounded negative Brain experience across stale Fast retries

- Source `4d9c3cea` passed **CORE Workflow Gate 37965988915** and **SEC CodeQL 37965988953**, proving control-plane test/syntax/security contracts. Actual representative FORCE Lab `37965988796` FAILED its `route_transition_graph_v3` materializer after three Qwen 7B attempts: first still used an executable `new_strategy_id` selector, second emitted an invalid guard, third was **non-executable body**. No generated candidate was applied to a provider, no title-correct playable terminal proof. Do not interpret green Gate as provider success.
- Separate Fast Brain `37964044351` and replay `37965551875` each selected **5** (`allwish,animekai,animesama-co,animevostfr,uhdmovies`), each produced **1 animevostfr healthy LAB fixture** but **0 accepted/published repairs** and exact `animevostfr:CANDIDATE OK` after current-byte Retest, with 4 Learning handoffs. The lab result is a non-authoritative oracle only, never FULL. Automatic census remains **21/46 FULL**, **17 in repairQueue**.
- Confirmed two common Brain memory bottlenecks: (1) Fast runs that detect stale `main` after expensive Repair upload an artifact then requeue without feeding the observed negative experiments into the next run; (2) the `brain-repair-memory.json` global **1000-row failure-sorted cap** holds 19 providers with large concentration on long-running cohorts (e.g. animevost-fr 120, 4khdhub 114), while animekai/animesama-co each have only 3/2 and uhdmovies has no entry. A newly observed valid negative with 1 failure could be evicted immediately.
- Brain-only remediation: `scripts/merge_stale_fast_repair_memory.py` reads only **executed negative** fingerprints from prior exact same-repo Fast artifact. Workflow verifies ancestor SHA, Fast workflow identity, main branch and **unchanged provider/runtime/Brain executable files** before merging. No positive/playback authority, publication source or provider byte can be imported. Stale Fast requeues pass the prior run ID rather than starting blind. Invalid or unavailable artifacts skip safely, while all outcomes remain subject to fresh current-byte validation.
- Brain-only memory retention: `scripts/brain_negative_memory_retention.py` reserves up to **12 ranked signatures per observed provider** before filling the remaining bounded 1000 rows by evidence severity. It prevents new lower-count providers' failures from being erased by hot-provider history; tests cover eviction, deterministic cap, no positive promotion, schema validation and workflow replay binding. Current production provider sources remain untouched.
- This milestone is an infrastructure/persistence correction, **not** a claim that any of the 17 providers is repaired. Require an actual model-authored executable runtime branch or validated candidate replay followed by applied-current-byte terminal media, precise title match, appropriate language/quality and non-regression before status/publish. Keep testing by exact SHA and preserve cross-family negatives.

## 2026-10-09 — FORCE guard-scaffold diagnostics + animevostfr current-byte retest

- The current authoritative sharded census (run `37964931793`, source `7d9cb924`) remains **21/46 FULL**, **17 repairQueue**. Run `37963760977` on `de1c82ee` FAILED materializing the representative 4KHDHub `route_transition_graph_v3`: three Qwen-generated branchBody answers still contained executable references to Brain-owned `new_strategy_id`. First, second, third attempts were rejected; strict guard was correct, but the small model repeated forbidden selector syntax. No repair playback, no valid v3 generated/persisted.
- Brain-only fix `5422bc93` AST-flattens *only* nested child-exclusive `new_strategy_id == new child` guards (including no-else safe singleton), preserving Qwen's algorithm statements while excluding parent/else/multiple/fallback guards and any remaining executable selector reads/writes. Unit tests verify a single child wrapper, parent rejection, distinct emitted guard and identical untouched source. This is not a direct provider patch.
- Brain-only fix `9e19a270`: Qwen's bounded model prompt is fed the **unwrapped parent algorithm body** for real helper vocabulary instead of the full selector chain when uniquely recoverable, and no longer receives its own rejected `branchBody` source on correction. It retains only the rejection signature/causal negatives, avoids copying forbidden syntax, and keeps true Brain-owned guard construction/AST checks. Source bytes and rules remain untouched. Non-Regression Gate `37965598774` SUCCESS on `9e19a270`; CORE Workflow Gate `37965598764` still in progress at checkpoint.
- Independent Fast Brain `37964044351` on `7d9cb924` explicitly checked remaining **five** providers (`allwish,animekai,animesama-co,animevostfr,uhdmovies`). Observed `animevostfr` HEALTHY in **LAB** with one stream, no runtime error, **fixedInLab=1**, then exact provider retest `animevostfr:CANDIDATE OK`. **accepted=0; validated=0; candidates=1 but unresolved=1**; other four deferred to Learning. This is evidence of a promising laboratory oracle, NOT a production repair or verified current-byte terminal playback. Lab-positive outcome should inform Brain replay, never bypass retest. Five-provider rerun `37965551875` launched due stale-main SHA. Old Fast cohort also `0/12`, not repaired.
- Critical efficiency debt: stale Fast Repair runs archive JSON artifacts but requeue without promoting bounded learned evidence into `main`; e.g. `37964044351` saw new main before persistence and reran. Do not accept stale provider bytes; preserve lab-positive and negative signatures in Brain experience for subsequent current-byte replay. Additional infrastructure remedy remains to be implemented/tested.
- Branch status: `main` retains Brain changes; no provider source manual hotfix. Next: new 4KHDHub FORCE with corrected algorithm-only prompt on final tested SHA; verify model-produced algorithm, three changed files/four execution gates, actual applied Git diff, current-byte model-driven provider playback and precise content, then one representative per failure family. No FULL count promotion until those proofs complete.

## 2026-10-09 — FORCE 7B corrected failure classification and retry diversity

- Current authority: sharded census `37960829689`, exact source SHA `b5b2ef40`: **21 FULL OK / 46**, **17 RepairQueue** (3 PARTIAL, 2 CANDIDATE, 10 ROUTE, 2 CHAIN, 1 NO PROOF, 2 REGRESSION, 5 DISABLED). Green workflow is not proof of playable provider. Fast Repair `37962915079` on `c6d37ff3` accepted **0 of 12**, handed 12 to Learning and retriggered against a newer SHA.
- Real FORCE `37962219360` on `e7b107a2` still failed: `branchBody contains strategy guard or selector mutation` after two bounded model corrections. Earlier `37958096689` failed with `branchBody must contain bounded statements, not guards`; these are Brain generation/orchestration failures, not grounds to edit any provider.
- Main Brain-only sequence `19004fb6` treats harmless mentions of `new_strategy_id` in Python comments/literals as harmless while rejecting actual selector references by AST; `7f656543` unwraps an isolated child-only guard from model output; `b440fff8` adds unit tests for guarded-body normalization without allowing parent/else/multi-branch changes. Current `fe180d13` changes the local Qwen model's **rejected branch-body corrections only** from deterministic temperature 0 to 0.2, to avoid regenerating the exact same invalid structure. Initial candidate remains deterministic, correction retries remain bounded, every executable source and media/playback safety gate remains strict.
- Non-regression Gate `37963381583` SUCCESS on `b440fff8`; CORE Workflow Gate `37963381674` and new Gate `37963638596` had not finished at this checkpoint. No generated algorithm, applied-byte playback or census promotion has been validated from these latest model changes. No provider/Core/manifest manual repair.
- Next representative: 4khdhub novel `v3`, prove Qwen actual algorithm, unique untouched v2 parent, runtime/Brain/planner four gates, exact Git artifact, materialization and identity-matched playable terminal stream. Only then repeat one per failure family; if a run fails, persist specific signature rather than looping silently.

## 2026-10-09 — Recovered Brain FORCE branch-body correction before materialization

- Verified current HEAD lineage: `b5b2ef401c54` -> Brain-only `fecb8838`, `50d4ceb8`, `ae1cafde` -> census metadata commit `3b1acb8482`. No hidden Brain rollback: automatic census is a descendant of the fixes. Two remote branches (`main`, `brain-learning/proposals`), no open PR. The authoritative census `37960829689` on `b5b2ef40` is **21 FULL OK /46, 17 repairQueue**; statuses 3 partial, 2 candidate, 10 route, 2 chain, 1 no proof, 2 regression, 5 disabled. Mixed issues include zero results, HTTP/network exceptions, timeouts and WAF challenges; a successful route is not a playable stream.
- Latest Fast Brain Repair `37957494077` selected 12 and accepted **0**: no new repair experiment; 12 Learning debt. FORCE Lab `37958096689` FAILED on the exact same main SHA in `scripts/brain_force_runtime_branch_body.py` before its materialized correction loop, `ValueError: architecture FORCE branchBody must contain bounded statements, not guards`. Its following 7-provider Learning `37959128660` completed workflow SUCCESS but had **zero provider proposals and no playback recovery**.
- Root cause: small local Qwen can return a body wrapped in `elif new_strategy_id == child` even though prompted for statements only; a blanket substring test rejected the entire response before `validated_model_plan` had a chance to ask the model to correct it. Repeating autonomous retries did not learn from this failure.
- **Brain-only fix** `fecb8838`: AST-parse and unwrap precisely one child-matching `if/elif new_strategy_id == child` wrapper; reconstruct the child guard deterministically. Parent guards, multiple strategy branches, unexpected else, import/global changes and invalid/no-op code remain rejected. No provider files changed.
- **Brain-only fix** `50d4ceb8`: move invalid generated-body errors into a bounded two-round explicit Qwen correction loop, carrying the sanitized validation error and rejected body excerpt. Applies to initial, edit-validation and materialized-correction model responses. Corrected algorithm must still pass full three-file materialization, fourth runtime selector, exact-byte rollback, complete patch-artifact inclusion and post-`git apply` validation.
- **Regression test** `ae1cafde`: model-authored child-only guard normalizes to the exact previously validated algorithm edit; parent, multiple guard and fallback are rejected; Qwen corrective round is invoked on invalid body instead of aborting the whole Learning cohort. Provider Non-Regression Gate `37961595167` SUCCESS on `ae1cafde`. Exact-SHA Workflow Gate `37961595084` pending at this checkpoint; no provider has become FULL due to these infrastructure changes.
- Next required proof: fresh 4KHDHub FORCE on current revised Brain with real model output, generated child executor + all four execution gates, full patch artifact, actual applied/rematerialized bytes, identity-matched terminal playback, non-regression and canonical census. Persist every negative/positive model-output signature. Then validate a case per relevant failure family and extend the repair queue; no direct provider repairs.

## 2026-10-08 — Brain FORCE algorithm-body generation, four gates, full artifact proof

- Authoritative sharded census `37837966631` completed with **21 FULL OK / 46 and 17 repairQueue** on `1a859e3e`; Fast Brain Repair `37838824671` completed SUCCESS as a workflow but **0/12 candidates validated** and 12 Learning debts. Do not promote from green workflow status.
- Real 7B FORCE `37837758778` on `1a859e3e` FAILED its executable materializer: repeated `architecture FORCE new Repair profile must preserve evolved strategy parent guard route_transition_graph_v2 unchanged` for attempted `route_transition_graph_v3` after 3 model correction rounds. Model-led bounded text replacements still modified/merged the old branch instead of preserving it. Provider `4khdhub` remains ROUTE PROVEN without verified terminal playback.
- Earlier architectural defects fixed and now confirmed independently: generated strategies were missing the adaptive runtime's own `POST_EXHAUSTION_STRATEGY_PROFILES` selection registry; the FORCE `git diff --binary` artifact also omitted the entire generated adaptive executor file. New Brain-only deterministic runtime registration, required fourth execution gate, applied-artifact validation after every promoter `git apply` and synthetic regressions are in main through `8ce20103`. CORE Workflow Gate `37839218753` was **SUCCESS** on `8ce20103`; Provider Non-Regression Gate `37839218765` was also SUCCESS. The earlier `48bc4a59` contract Gate `37838712250` passed. This validates the infrastructure guards only, not a playable provider.
- Further Brain-only generative evolution: `4ebe4162` added `scripts/brain_force_runtime_branch_body.py`; `5e32f86c` enabled branch-body parsing in FORCE; `78283e9c` changed the local 7B Qwen prompt/schema to return **only executable Python `branchBody` statements**; `cefdc309` tests that Brain deterministically scaffolds a distinctly guarded `v3` sibling BEFORE the next unique executor guard, never edits parent `v2`, rejects no-op/import/invalid code, wires its registries/selector, and transactionally restores original sources. Old three-file LLM replacement remains a fallback only for legacy responses and must not count as proof.
- New exact SHA Workflow Gate `37840005323` for `cefdc309` is in progress at this checkpoint; no model-generated branchBody has yet been executed in the real canonical sandbox, no terminal stream is validated, and no production provider patch has been accepted. Next step: explicit `4khdhub` FORCE on the tested corrected SHA, inspect actual applied bytes/registration/selection, replay identity-correlated terminal playback, non-regression, persist the experience and update the census before extending by repair family.
- No manual provider, ProviderBase, manifests, badges, Core or publication code patch used to mask Brain failure. Source and test SHAs must be tracked separately from current census/main.

## 2026-10-08 — 7B FORCE runtime-only generation enforced, three-surface validation retained

- Revalidated `main` at `578487c8b09b406caef8653e620c47124f4f4963`, with only `main` and `brain-learning/proposals` remote branches and zero open PR/issue. Latest authoritative census `37833898552` is **21 FULL OK / 46, 17 repairQueue**, and Fast Repair `37834756199` accepted **0/12**, Learning debt 12. The later census metadata commit `d801c118` says `24/46` *processed*, not a gain to 24 FULL; do not misreport.
- FORCE Learning `37834168084` on older `46488149` FAILED in the real Qwen materializer: initial timeout, then three corrective attempts ending with `architecture FORCE new Repair profile must wire planner/runtime surfaces: scripts/brain_repair_runtime.py,engine_v2/scripts/plan-repairs.mjs`. The Brain already had conditional deterministic autowiring; its new-profile prompt still admitted planner/registry edits and the materialization-correction prompt contradicted the runtime-only plan by asking Qwen to return a complete 3-file wiring. The compact payload additionally blindly cut source snippet prefixes rather than re-focusing the exhausted parent runtime branch. These are Brain orchestration faults, not proof of a broken individual provider.
- Main `1772d040` fixes only `scripts/brain_architecture_force_materializer.py`: new Repair-profile Qwen requests and corrections can edit **only** `scripts/adaptive_runtime/runtime_repair.py`, the source excerpt is re-focused on the exhausted parent, and the correction contract no longer asks for three model-generated surfaces. `complete_evolved_profile_wiring` still injects the separate profile into the exact Brain registry + causal JS planner; all 3 surfaces must pass distinct strategy, preserved parent guard, syntax, contract tests and transactional rollback. No provider bundle, manifest, ProviderBase or release bytes manually changed.
- Main `578487c8` adds synthetic regression tests for runtime-only Qwen responses, exact allowed paths, bounded parent-source focus, automatic 3-file wiring, old parent preservation and rollback; taxonomy-only submissions remain rejected. **CORE Workflow Gate `37837288575` SUCCESS on exact SHA `578487c8`** (including the focused Brain tests); Provider Non-Regression Gate `37837288644` SUCCESS on the same SHA. These prove control-plane contracts and non-regression tests, **NOT** provider playable recovery. Later QA and FORCE evidence must be attributed to their actual SHA.
- A fresh `4khdhub` representative FORCE must now run on the corrected SHA via the persisted `.github/triggers/brain-learning-reconstruction`, with strict current-byte rematerialization, actual identity-matched terminal stream/playback, and zero green-lane regressions before Brain reports a recovered provider. Older FORCE runs `37835295860` and `37836222103` were still executing on older `17e76728` when checked and must not be credited to the corrected contract. Only after one genuine provider success advance by independent failure family; do not manually patch providers. Explicit exact subsequent run/artefact results must be added here once known.

## 2026-10-08 — FORCE autogenerated wiring: registry-boundary regression and contradictory Qwen prompt

- CORE Workflow Gate 37832621861 on 8925adff failed after adding a representative runtime-only autowire regression. Confirmed causal Brain helper defect: the registry `source[begin:end]` slice omitted the final newline of the parent entry, producing false `architecture FORCE registry parent anchor ambiguous`. Fixed Brain helper with `source[begin:end + 1]` in main `f412806e`; this preserves fail-closed global uniqueness checks and keeps the executor source unchanged.
- Identified a separate **contradictory Brain LLM prompt** in `scripts/brain_architecture_force_materializer.py`: the model system instruction simultaneously said `Return exactly 3 replace edits` and `PREFER exactly one runtime_repair.py replace edit`. Qwen 7B cannot reliably spend its bounded tokens on a novel executor under conflicting output shape requirements. Fixed to prefer a single runtime sibling implementation and let Brain wire missing registry/planner entries deterministically (main `3760ddb8`); test `a0323fe2` rejects the contradictory instruction.
- Representative FORCE run 37833367717 was launched on c4853e72 for 4khdhub (not on latest corrected prompt) and reached the architecture materializer. A fresh FORCE run on the new SHA is needed for current-byte validation; never credit old SHA runs to new changes.
- In all cases, treat parser/compiler/executable wiring only as Brain readiness. The required provider proof remains actual terminal media playable and identity-matched on rematerialized current bytes. Census authority still **21 FULL OK / 46** and 17 repairQueue; no repaired provider demonstrated by these infrastructure fixes. Preserve existing green lanes and provider code; no manual patch.
- Gate status: 37833015504 (f412806e) was cancelled by a newer main push before a definitive verdict; next new-SHA Workflow Gate must execute the synthetic autowiring and prompt tests fully.

## 2026-10-08 — Brain FORCE Qwen one-executor generation with deterministic wiring

- Confirmed repeated Fast Repair rounds through 37832001714 stay at **0 accepted / 12** even though workflows are green. Census authority remains 21 FULL OK / 46, 17 repairQueue; no new terminal playable provider proof.
- The old architecture FORCE required the constrained 7B model to produce exactly three distinct file replacements (Brain registry, JS planner, Python executor) in <=1024-1280 model tokens and would consume long corrective rounds. This is a Brain materialization/orchestration bottleneck, not a provider bug.
- Brain code commits 2918bb1b and 2028dc66 add **deterministic execution-profile scaffolding**: Qwen may now emit one Python runtime sibling implementation; the materializer automatically wires the new distinct id into the correct causal JS planner group and Brain registry. Unknown scope, absent parent, ambiguous find, changed parent guard or missing runtime implementation still fail closed; existing three-surface validation, syntax checks, per-run transaction rollback and publication playback gates are unchanged.
- Test commit 8925adff uses synthetic v2 -> v3 one-runtime-edit proposal and asserts complete 3-surface wiring, compile/static validation, unchanged parent, exact rollback, and rejection of unknown causal scope. No individual provider source manually modified.
- Automated CORE Workflow Gate 37832621861 and production tests on 8925adff are pending/in progress at this checkpoint; do not call scaffolding proven until the tests actually pass. Existing FORCE 37830016250 runs pinned to older f33e474a and cannot validate the new scaffolding. A *fresh* FORCE must execute the new SHA, materialize meaningful executor logic, replay against current provider bytes, and validate correct-content terminal playback before any census status promotion.
- Independent publication/security outcome: projection workflow 37830948298 fixed only Flemmix/WookaFR fingerprint drift with zero provider bytes changed; SEC Final Gate 37831520001 and CORE Verify & Publish 37831519929 both completed SUCCESS on 9483aa8c. Security issue #69 remains closed and no PRs are open. Full provider functionality is still separate and unproven for the 17 repairQueue entries.

## 2026-10-08 — Security final gate restored without weakening HTML decoding

- Independent SEC Final Gate 37831172570 on fa260c3 failed `tests/provider_security_hardening_test.py` with `ValueError: substring not found`. The test expected the deleted chained `/&quot;/gi` then `/&amp;/gi` form in `provider_base_store.py`.
- Actual current Brain/Core player-form code uses `_spv188DecodeAttr` single regex `/& (amp|quot|#39);/gi` (no space in executable regex) and one-pass replacement. The obsolete test did not demonstrate unsafe runtime behavior.
- On main commits 7930b1b7 and 9483aa8c, replaced the obsolete string-position check with an actual Node evaluation of the **current** source helper, including nested `&amp;lt;` staying `&lt;`, literal quote/amp/apostrophe decode and preserved form URL attribute query. Provider bundles and Core runtime were not edited.
- SEC Final Gate **37831520001 SUCCESS** on tested SHA `9483aa8c`; this validates the global security hardening tests and exact SHA security check. Open PR count verified zero; issue #69 remains closed/completed as of this check. Provider Non-Regression run 37831519913 SUCCESS on the same SHA.
- Brain repair status remains separate: latest verified Fast Repair 37830563972 accepted 0/12, deferred 12; exact current FORCE Learning run 37830016250 on f33e474a is still at `Materialize executable Brain architecture FORCE patch`, not provider success. Census 21/46 FULL and 17 repair queue until a new authoritative census proves otherwise.
- Publication integrity repair: projection run 37830948298 confirms 2 drift providers Flemmix/WookaFR, 0 after rebuild, 0 provider byte changes, reapply fixed point 41, generic publication commits 54750f5 + fa260c3. Domain Refresh prevention/test commits 959b1f2 and 9c265e9. Final CORE Verify on SHA 9483aa8c still pending at this checkpoint.

## 2026-10-08 — Domain Refresh publication input fixed point restored and guarded

- Independent CORE Verify & Publish 37829013675 on d138cd3d failed at `python scripts/reapply_published_overrides.py --check`: `FIELD_PROVIDER_FAST_FIXED_POINT status=miss reason=provider-policy-changed:flemmix`. This was a **publication metadata/projection integrity** failure, not a playable stream or a Brain provider repair.
- Proven root: Domain Refresh 0196580 changed Flemmix accepted DATA/domain (flemmix.eu -> flemmix.rip), regenerated provider bytes and PROVENANCE but the targeted `reconcile_targeted_provider_publication.py` changes only `published_filename/sha256/final_fixed_point` and does not reindex `provider_policy_sha256/build_input_sha256`. Current `provider_policy_sha` naturally differs.
- Triggered existing **generic** `PROVIDERS - Projection Reconcile` workflow 37830948298 on main using commit 7a4afb74. It completed SUCCESS and published a metadata-only targeted reconcile (stage commit 54750f512, pin commit fa260c302). No manual provider patch; the stage commit updated `PROVENANCE.json` and `provider-v3-materialization.json`; final updated release hash manifests.
- Prevent future recurrence: commit 959b1f2 updates `.github/workflows/domain-refresh.yml` to recompute publication fingerprints **after** the incremental Provider DATA/CONFIG Lego rematerialization, require `reapply_published_overrides.py --check`, detect any remaining publication DATA drift, and fail closed before publishing. Test 9c265e9 locks ordering/guard in `tests/domain_refresh_workflow_test.py`. This pipeline change does not claim stream recovery or direct manual provider repair.
- Current provider authority last observed 21 FULL OK / 46, 17 repairQueue. The independent Brain FORCE/Learning pipeline remains under live execution, and the actual provider playback verdict must be confirmed by new census. CORE Verify & Publish on fa260c3 (`37831164811`) is the relevant follow-up for the original Flemmix gate failure. The new workflow/test SHA still requires CI.

## 2026-10-08 — Fast Repair exhausted cohorts now trigger Brain architecture FORCE

- Found recurring auto-handoff contradiction: Fast Brain Repair 37827813922 completed with 12 Learning debt providers, zero accepted repairs, and `no_new_repair_experiment`, but its workflow emitted `learning_dispatch=true architecture_force=false`. LEARN therefore ran without the executable FORCE materializer even though Repair had no new strategy.
- Updated only the Brain control-plane workflow `.github/workflows/provider-fast-repair.yml` in ef0c5312: automatic handoff sets `architecture_force=true` for a genuinely stalled Repair cohort with nonempty Learning handoff, or for explicit FORCE trigger. Unrelated healthy/mere transport cases are not auto-promoted. Added source contract in `tests/brain_self_architecture_test.py` commit d138cd3d.
- This is not provider validation: next eligible current-SHA Learning must generate a genuinely novel strategy (after Repair-negative-memory reconciliation), materialize it, execute current-byte sandbox playback and prove identity/non-regression before any FULL promotion.

## 2026-10-08 — Canonical Repair negatives now inform FORCE strategy novelty

- Diagnosed a repeated Brain pipeline stall: FORCE Learning 37821330619 attempted to rematerialize route_transition_graph_v2 although v2 already existed in the Brain registry, planner and runtime. This wasted multiple long Qwen rounds and ended with a strict materialization failure, without provider gains.
- Repair memory automation/brain-repair-memory.json contains real execution failures for v2 across 4khdhub, animesultra, moviesmod, moviebox and yflix. Learning architecture selection previously consulted sandbox Learning experimentMemory only, losing these execution negatives at the orchestration boundary.
- Brain infrastructure commits 044a2119 (installed-profile three-surface novelty gate), 2e86f0b (merge actual canonical Repair negative execution records for currently deferred providers), and 6142fad8 (synthetic regression test: executed v2 forces next v3; unexecuted v99 and other providers ignored). No direct provider edits.
- Reference census: 21 FULL OK / 46 and 17 repairQueue; Fast Repair 37827813922 (older 25e443d9) completed 0/12 validated, 12 Learning handoffs. New test/CI on commit 6142fad8 remains required; these Brain changes do not prove playable provider recovery.
- Future requirement: real Brain-generated v3 must compile, apply, rematerialize, execute in a current-byte provider sandbox, pass correct-content/terminal playback and non-regression, and persist resulting signatures/experiences. No status promotion from architecture commits alone.

## 2026-10-08 — Brain FORCE novelty preflight: replay installed v2 first

- Current census 37823121498: 21 FULL, 3 PARTIAL, 2 CANDIDATE, 9 ROUTE, 3 CHAIN, 1 NO PROOF, 2 REGRESSION, 5 DISABLED; 17 repairQueue. Fast Repair 37823871921 accepted 0/12, Learning debt 12, no_new_repair_experiment.
- Learning FORCE 37821330619 spent over 20 minutes retrying stale route_transition_graph_v2; log explicitly fails with architecture FORCE new Repair profile already existed before materialization. Current Brain registry, planner, adaptive runtime all wire v2.
- Brain-only architectural novelty fix: reconcile installed strategies across all 3 executable surfaces; existing candidate is replay-first, not eligible for FORCE regeneration. Only exhausted installed strategies may evolve to the next genuinely novel id. Added partial/full registry and v2-v3 negative-memory regression tests. Current-byte provider playback remains unverified; no provider source edited.

## 2026-10-05 — Deep Repair crash fixed; disabled-provider CodeQL noise cleaned

- Fast Repair failures on current cohorts were traced to a Brain pipeline crash, not provider behavior: `scripts/deep_repair_loop.py` logged `identity_contradiction_count(...)` without importing that runtime guard. Commits `4d3152e2` + `8a066deb` import it from `runtime_repair.py` and lock the contract.
- The authoritative census before replay remains `21 FULL OK · 3 PARTIAL OK · 2 CANDIDATE OK · 10 ROUTE PROVEN · 2 CHAIN REACHED · 1 NO PROOF · 2 REGRESSION PROVIDER · 5 DISABLED` across 46, evidence run `37247456053`, with 17 providers in automated repairQueue. Do not treat the recent Fast red runs as provider regressions; they were interrupted by the NameError.
- Persistent Learning guidance on `brain-learning/proposals` currently contains 11 providers / 15 rows from NiakVIO `0865aafc`; Moviebox carries `route_proven_gap -> search_contract_inference_v1` at confidence 0.86. This remains prior-only and requires current-byte sandbox + category/identity/playback proof.
- Security-tab cleanup: the 17 open CodeQL alerts were all lifecycle-disabled VidEasy snapshots under `provider-disabled/**`. Maintained CodeQL now excludes `provider-disabled/**` from Python and JS Core; the one-shot source scan also excludes `provider-disabled/**` and `provider-old/**`. Active `providers/**` and maintained `provider-bases/**` scanning remains enabled.
- CodeQL cleanup run `37248273443` was deliberately scoped to `provider-disabled/**` only: pass 1 found 17 alerts, 17 were dismissed, pass 2 found 0, and the final state was `Dismissed=17 failed=0 remaining=0`. Blanket dismissal is forbidden by the workflow contract.
- Next authoritative step: run normal maintained CodeQL on the post-clean HEAD, then replay Fast Repair on that same current HEAD with the Deep import fix and merged Learning priors. Only accepted/rematerialized/current-byte playback proof may change provider status.

## 2026-10-03 — HindMoviez fifth negative; sixth source-frontier hypothesis

- V6 sandbox run `37081288030` executed Brain's fifth HindMoviez hypothesis, `quality_aware_global_stop`, on exact current bytes. The mutation applied and rematerialized successfully, but acceptance was correctly rejected.
- Baseline: 6 returned / 6 playable, quality 480p only, 40 announced variants, 9 explored player requests, 5 reachable hosts. Candidate: 6 returned / 6 playable, still 480p only, 27 announced variants, 8 explored requests, 6 reachable hosts. There was no verified quality/count gain, and the candidate also failed playable identity on Tenet.
- Fingerprint `3d6e7609fbafdaca45d606c2e55a7032dee839fe4b8944f92853d7a77444e27e` is now an executed negative in `automation/brain-llm-force-memory.json`. The first five mechanism families for this mutation context must not be retried.
- Brain-LLM main `e1bfde84364c4cf7ecf13cefa282c1ec2b3137cf` adds the sixth generic progression `bidirectional_source_frontier_before_global_cap`: traverse a bounded source list in order 0,last,1,last-1,... while preserving the exact source-count bound, deadline guard, routes, per-source extraction, identity logic and global stream cap.
- NiakVIO Force validation treats this family as strict variant-coverage work: publication requires measurable playable quality/language/host/fan-out gain plus identity/playback non-regression. No HindMoviez provider runtime byte is manually edited by this change.

## 2026-10-03 — HindMoviez round-robin rejected; fifth quality-aware strategy ready

- Brain guidance `17fbc280bbe97eb67b0e664dd356c5ffe38f7df9` generated the fourth distinct HindMoviez completeness hypothesis, `cross_source_round_robin_before_global_cap`, fingerprint `7b98b0b512e73a208ccb1ccee52a0d694a56dffb578838473f747346e84f7603`.
- V6 sandbox run `37079643871` executed it on exact current bytes and rejected it. Baseline and candidate both returned/playable 4 streams with qualities 480p + 1080p, max playable height 1080 and 4 reachable hosts. Candidate regressed announced variants 40 -> 27 and explored player requests 11 -> 10, with no quality/host/count gain, and failed playable identity on Inception. No provider bytes were published.
- The rejection is persisted in `automation/brain-llm-force-memory.json` as executed negative memory. Together with the earlier quota-removal, source-slice and quality-stratified failures, Brain now has four distinct causal negatives for the same mutation context.
- Architecture FORCE fallback run `37079911596` completed successfully but produced no force-promotable blueprint (`no-force-promotable-blueprint`); it changed no production provider bytes.
- Brain-LLM main `1ca9ff748582959a74359dfcfdda2d3eb7af6dfd` adds the generic fifth progression `quality_aware_global_stop`. It activates only after the prior four mutations are blocked by executed negative memory, preserves the bounded source loop/deadline/routes/identity, keeps the original quota as the preferred stop, and permits bounded continuation to a secondary aggregate hard cap only while observed quality diversity is still missing.
- Brain CI run `37080517978` is green. The next authoritative step is an exact HindMoviez-only guidance run on current NiakVIO main, followed by V6 current-byte sandbox/rematerialization. This is not a repair until that candidate proves playable quality/completeness gain with identity and playback non-regression.

## 2026-10-03 — HindMoviez quality-stratified hypothesis rejected

- Brain deterministic guidance `f78521815d981a929b7def4a9bb64c1525254028` produced `quality_stratified_variant_enumeration` after negative memory blocked the earlier global-quota and slice-3-to-4 hypotheses. V6 sandbox run `37078342189` applied and rematerialized the mutation but rejected it; no provider bytes were published.
- Baseline coverage for this run had 4 returned/playable streams with qualities 480p + 1080p and max playable height 1080. The candidate returned 5 playable streams but only 480p, max playable height fell by 600px, announced variants fell 40 -> 27, explored player requests fell 16 -> 8, and automatic identity failed on Tenet. This is a real regression, not a harness-only rejection.
- The executed fingerprint `3bfe7769283b306e37319faf7578c2ca163dc7ad8f9a77666fe966dd5a303317` is persisted as negative Force memory. Brain must not repeat global quota removal, plain slice widening, or quality-stratified first-N selection for this context.
- The evidence points to an interaction between per-page selection and the existing global `out.length>=4` stop: filling early slots faster can stop bounded link traversal before later links that previously yielded 1080p. The next Brain strategy must address termination semantics while preserving the bounded link/deadline envelope; this is a Brain capability progression, not a hand-written HindMoviez patch.
- Force sandbox validation now routes `quality-stratified-variant-enumeration` (and the next `quality-aware-global-stop` family) through the strict variant-coverage gate, requiring verified playable quality/language/host/fan-out gain plus identity/playback non-regression.
- Architecture-force fallback run `37078625123` produced no force-promotable blueprint, so nothing was auto-promoted from it.

## 2026-10-03 — CoFlix current-origin transport blockage is now real evidence

- The first targeted transport run `36987803310` was not valid CoFlix transport evidence because explicit FULL OK targets were filtered before residential replay (`FIELD_RESIDENTIAL_PROVIDER_REPLAY_SELECTION providers=0`).
- Commit `c836860d2e4e42b29abe5781f5294cd9fc4fe008` fixed both transport selectors: explicit current providers may be browser-probed and residentially full-replayed regardless of canonical FULL/PARTIAL/ROUTE status, while current provider/address authority remains mandatory.
- Corrected transport run `36988306455` then targeted `coflix` successfully. Browser evidence reported `browser_challenge_persisted` on all 3 targeted lanes; residential replay selected exactly 1 provider and returned `raw=0 playable=0 verified=0 wrong=0`.
- Therefore the live `coflix.ac` contract is currently transport/challenge-blocked even through the configured residential exit in this harness. This is distinct from the already-rejected stale-runtime cap hypothesis and distinct from the old explicit-target selection bug.
- CoFlix remains unrepaired. Current structure evidence (REST route + 10/9 fan-out) stays observation-only until a transport lane can execute/qualify the live contract; no provider runtime byte is promoted from the supplied HTML alone.

## 2026-10-03 — HindMoviez third hypothesis is quality-stratified, not another cap increase

- HindMoviez has two executed negative Force experiments on exact current bytes: global output-quota removal regressed the useful result set, then `files/source slice 3 -> 4` returned one extra playable row but stayed 480p-only, reduced announced variants/explored requests and failed the Oppenheimer playable-identity gate. Both fingerprints remain in `automation/brain-llm-force-memory.json` with causal coverage deltas.
- Brain-LLM main `1dee412b0faf2b0e146c2de6261dd81ce513e783` adds the generic third deterministic progression for quality/source completeness debt: after quota and simple slice hypotheses are both blocked by executed negative memory, choose a bounded set of upstream source/file variants by distinct currently observed quality heights before filling any remaining slots.
- The mechanism does not change routes, origins, HTTP methods, deadlines, terminal URLs or global playback guards. Current observed quality heights drive the bounded target; it is not HindMoviez-specific.
- Initial CI exposed that current runtimes encode quality classifiers as regex alternations such as `(2160|1080|720|480|360)p`, not necessarily literal `2160p` tokens. Brain `aa7b2e79d9799dc856ef4e251335c2e6080c5cf4` fixes the generic classifier detection and CI run `37075069578` is green.
- Authoritative HindMoviez cycle-3 Advisor run `37075113561`, trigger Brain SHA `99aaac8ffb178d46ae68434189b9ae898441a619`, is pinned to NiakVIO `34eb7f37c41b847b2d2317e3fa15bd877c56e6d6` and exact target `hindmoviez`. It is not a repair until an external mutation is published, sandboxed, rematerialized and proves playable quality gain with identity/non-regression gates.
- CoFlix remains unrepaired: its cap-only candidate was correctly rejected with zero verified dimension gain; live current-origin `coflix.ac` contract qualification remains transport-blocked. No CoFlix or HindMoviez provider runtime was manually edited in this sequence.

## 2026-10-02 — HindMoviez second Force hypothesis rejected with causal metrics

- External Brain source-slice hypothesis `d2c651fe...` from Brain `ef26e7dd1ed49cb3d1beaeaa7d6aaf25fdb97302` was executed in isolated current-byte sandbox run `37001140250`; it was not the earlier global-quota mutation.
- Baseline on that run: 5 returned / 5 playable, playable quality 480p, 40 announced variants, 9 explored player requests. Candidate `slice(0,3) -> slice(0,4)`: 6 returned / 6 playable but still only 480p, 27 announced variants and 8 explored requests.
- Candidate therefore produced no intended quality gain, reduced announced/explored completeness, and additionally failed `identity_gate:Oppenheimer:playable_identity_not_fully_verified`. Sandbox accepted 0 providers; no provider bytes were published.
- The exact URL-free coverage summary is persisted into `automation/brain-llm-force-memory.json` so Brain can distinguish this source-slice failure from the earlier quota-removal failure and avoid blind cap escalation.

## 2026-10-02 — Force negative memory now retains causal completeness deltas

- HindMoviez exposed that Force memory was too lossy: the sandbox knew the rejected candidate regressed returned streams and quality/exploration depth, but durable Brain memory retained only `variant_coverage_stream_regression` plus a broad mutation family. The next Brain cycle could therefore vary the same cap strategy without seeing why it failed.
- `scripts/update_brain_llm_force_memory.py` now persists a bounded, URL-free coverage snapshot for the last executed baseline and candidate: returned/playable counts, identity contradictions, observed and announced quality heights, maximum playable height, announced player/variant counts, explored player requests, reachable-host count and fan-out states. It also persists numeric deltas.
- Hostnames, stream URLs, headers, response bodies and credentials are not retained. The HindMoviez-shaped contract proves a baseline 7 returned / 720p / 16 explored versus candidate 5 returned / 480p / 8 explored becomes explicit negative causal memory.
- The memory test is now part of Workflow Gate. This is generic Force learning infrastructure; no provider runtime bytes were changed.

## 2026-10-02 — Current quality evidence reaches Brain Repair

- The current-structure observation channel now supports bounded `qualityHeights` in addition to player/server counts and language labels. Brain-LLM main `51c7adb3f42d0e695d7d1bfb434ba33938fa379f` sanitizes/sorts values into the model-visible current structure while keeping `proofAuthority=false` and `executionAuthority=false`.
- HindMoviez current observation is persisted generically as origin `hindmovie.dev` with observed qualities `480/720/1080/2160`; no route, request recipe or stream URL is invented or persisted from that observation.
- This gives Brain a causal target for the 480p-only symptom even when later qualities are truncated before dynamic network fan-out can observe them. Publication still requires a Brain-owned current-byte mutation plus real quality/playback/identity gain.
- CoFlix remains blocked on live current-origin transport; work proceeds independently on HindMoviez as the representative quality/release-truncation family.

## 2026-10-02 — Current data-cfp contract shape locked in Brain test

- The user-supplied current player markup uses a `data-cfp` JSON attribute containing a resolver URL plus `params={tmdb,type,year,pid}`, together with two indexed player menus exposing 10 + 9 choices.
- The generic current-contract execution test now uses that real structural form (sanitized demo host/ids) rather than the older `data-player` fixture. It still proves bounded UNKNOWN-method probing can discover a POST-form resolver, reach terminal HLS, and persist only placeholder/binding recipes; the literal pid is not persisted.
- This is a Brain/parser contract only. Current live transport to the real origin remains blocked by browser/direct/OkHttp/residential challenge evidence, so CoFlix is not declared repaired and no provider runtime byte was manually changed.

## 2026-10-02 — Explicit transport targets now bypass status-only filtering

- Targeted CoFlix WAF/Tailscale run `36987803310` connected the residential exit successfully, but produced `matchedProviderLanes=0` and `FIELD_RESIDENTIAL_PROVIDER_REPLAY_SELECTION providers=0`. The durable WAF ledger contained no CoFlix row at all.
- Root cause was transport-lane selection, not a negative CoFlix transport result: `probe_waf_browser_session.py` only seeded metadata probes for WAF/ENV statuses, and `select_residential_provider_replay.py` intersected explicit targets with symptomatic queues. A nominally FULL provider explicitly targeted for hidden completeness/contract debt was therefore filtered twice.
- Explicit transport qualification now seeds the named current provider from its current official metadata regardless of canonical FULL/PARTIAL/ROUTE status and full-replays it through residential transport. Current provider/address authority remains mandatory; an authority-blocked explicit target is still excluded.
- Automatic/non-explicit transport selection is unchanged and remains restricted to current WAF/ENV/NETWORK symptoms.
- Contracts cover a FULL OK explicit seed and FULL OK explicit residential replay while preserving default exclusion. CoFlix transport qualification is retriggered; no provider runtime bytes were changed.

## 2026-10-02 — V5 fully aligned with current-contract probe path

- CoFlix architecture FORCE rerun `36985798775` passed the generator revision migration but failed next in the same third-order runtime contract: V5's resolved-page hardening expected the pre-v4 `resolve()` shape where `form=playerForm(...)` immediately followed page proof.
- Generic Core v4 inserts `probeCurrentContracts(...)` before form mining. V5 now accepts both shapes and preserves its extension-is-not-proof invariant on the new contract path.
- V5 additionally hardens `contractRequest()` and returned `contractDoc` media proof: an extension-only URL is downgraded unless MIME/disposition/body independently proves media.
- Third-order contract now asserts v4 input migration plus contract-probe extension hardening. No provider runtime was manually edited.
- CoFlix architecture FORCE is retriggered; the next useful milestone is actual contract-probe execution rather than another preflight-only success.

## 2026-10-02 — Architecture FORCE unblocked for current-contract probe

- CoFlix contract-discovery Repair run `36982888748` selected no canonical provider mutation and correctly escalated `coflix` to architecture FORCE run `36983001855`.
- Architecture FORCE failed before any experiment because `adaptive_runtime_recovery_v5.py` only accepted generator revisions `generic-core-v3-census-focus` and `generic-core-v2`. The generic recovery generator is now `generic-core-v4-current-contract-probe`, so the V5 hardening layer rejected a newer valid generator before sandbox execution.
- V5 now accepts `generic-core-v4-current-contract-probe` as migration input while preserving its existing hardened output revision `generic-core-v3`. This is compatibility plumbing only; media-proof semantics and provider production bytes are unchanged.
- `brain_third_order_strategy_runtime_test.py` now locks the v4-input -> hardened-v3-output transition.
- CoFlix architecture FORCE is retriggered with the cap-only fingerprint retained as a negative experiment. The next accepted result must come from the current-contract probe path and still prove playback/identity/completeness gain before publication.

## 2026-10-02 — Brain current-contract discovery after cap-only rejection

- CoFlix external Brain mutation `919ddb5013d666b33218b3aca7b7785f9064254a` was applied in V6 sandbox run `36978793130` and correctly rejected: baseline and candidate both produced 6 playable streams, qualities 360/480/1080, language fr and the same four reachable terminal hosts. Rejection is persisted as `variant_coverage_no_verified_dimension_gain`; the cap-only fingerprint must not be retried as if it were progress.
- This proves the primary debt is upstream of the terminal cap: current structure says `coflix.ac /wp-json/coflix/v1/resolve`, while executed bytes still traverse the stale `coflix.wiki` Ajax contract.
- Repair now has a generic observation-only contract-probe layer for current routes whose method remains UNKNOWN. It never promotes UNKNOWN directly and never borrows peer GET/POST authority. The sandbox can only match a current-page embedded JSON endpoint + declared request-key set, require fixture identity agreement, and try bounded GET / POST-form / POST-json shapes.
- Embedded provider-local values are ephemeral. `pid` is a causal binding key: a successful later request may persist `{binding:pid}` only when a replayable earlier current response exposed the exact same value. The literal pid never enters durable request DATA.
- Added executable contract proving: current page embedded resolver + pid -> successful POST-form probe -> terminal HLS -> sanitized observed recipe with tmdb/type/year placeholders and `pid={binding:pid}`.
- No CoFlix production runtime bytes were manually edited.

## 2026-10-02 — Brain official completeness audit + exact witness cohort

- Completed stale diagnostic Advisor run `36970348376` (Brain `6d984d5d873c54ab68e663226e061777edaa46cc`) reported the Brain auditor's authoritative bounded counts for NiakVIO source `728bdd813e49e64276fed11082136eead0672c3e`: `providers=40 high=20 review=10 dynamic_high=5`.
- That run also exposed a cohort-selection bug: a push trigger explicitly requesting `coflix` was still auto-unioned with current repairQueue + static high-risk + dynamic debt, producing a 33-provider cohort and 5 Force LLM targets. It generated one sanitized mutation candidate, but publication was correctly skipped because Brain main had advanced; it has zero mutation/publication authority.
- Brain-LLM `43c384043dad70e4c8a137fefd843fe1e8f87731` fixes the selector: explicit workflow input or non-empty trigger `requested_repair_queue` is exact; the broad auto-union runs only when no explicit cohort exists.
- Brain-LLM `12b71b2af748ed1dd2c646c36a53e3ce81cf1e77` / `43c38404...` CI is green after the FORCE-prompt current-structure preservation contract.
- Current authoritative CoFlix witness generation is run `36973276806`, Brain trigger SHA `caca30e508a820a2a62a7c256718ecc99f4cab6a`, source NiakVIO `bdb9112fd26ec1a445769ac64e6492e784a0ea4a`. It must resolve the exact one-provider cohort before any mutation is accepted.

## 2026-10-02 — FORCE prompt now preserves current structure + dynamic fan-out

- Audit of the CoFlix 7B path found a final Brain-only information-loss bug: `request_from_checkout()` correctly attached current provider structure and sharded fan-out, but `build_force_prompt_payload()` selected only the first two generic observations. The FORCE model could therefore see static cap risk while losing `originHost=coflix.ac` and the current 7->2 fan-out proof.
- Brain-LLM main `e908b2a7597376f51e5985d2b7461b486f51753c` fixes the generic prompt boundary. FORCE now prioritizes current provider structure, current sharded fan-out, runtime variant coverage and targeted regression evidence; `current_structure_evidence` is also retained explicitly in advisor context and as `current_provider_structure` in the compact FORCE payload, including under severe prompt compaction.
- Added a prompt contract proving current origin + REST route + 10/9 (19 total) structure and dynamic 7 announced / 2 returned evidence survive into the model-visible FORCE payload.
- The earlier CoFlix guidance run `36970348376`, pinned to Brain `6d984d5d873c54ab68e663226e061777edaa46cc`, is superseded for publication even if it finishes. Only a rerun on Brain `e908b2a7...` or newer may feed the external-force sandbox.
- No provider runtime bytes were changed.

## 2026-10-02 — Registered runtime completeness audit candidate cohort

- A same-pattern scan of all 42 registered runtime Lego on NiakVIO SHA `728bdd813e49e64276fed11082136eead0672c3e` found 20 active provider registrations with high-risk static cap/first-success signatures in a nearby quality/language/server/player/source context: `allanime`, `anikototv`, `anime-sama`, `animesultra`, `animevostfr`, `coflix`, `flemmix`, `hindmoviez`, `movieshunt`, `moviesmod`, `neko-sama`, `papadustream`, `sekai`, `streamzo`, `uhdmovies`, `vidfast`, `vidrock`, `voiranime`, `voiranime-rip`, `yflix`.
- This is candidate static debt, not proof that every provider currently loses a real stream. Canonical FORCE selection uses the Brain auditor's `static-runtime-variant-coverage-debt` output (`proofAuthority=false`) plus current dynamic census evidence, and publication still requires current-byte measured gain.
- Current all-provider dynamic census run `36968430407` shows fan-out completeness debt for `animevostfr`, `coflix`, `kehflix`, `persianstremio`, and `vidlove`. Dynamic and static cohorts intentionally do not need to match: early truncation can hide later variants before the network census ever observes them.
- Representative order remains: CoFlix for current-contract/player-server traversal drift, then HindMoviez for quality/release truncation, then at least one representative per remaining failure family before any wider cohort application.

## 2026-10-02 — Canonical Repair consumes current provider structure

- Global sharded authority is restored by run `36968430407` / persistence commit `b3071d51368b1acb43f1f142adae17a6786da478`: 24/46 operational, with CoFlix still FULL OK but current-byte fan-out gaps on anime/movie/tv.
- Audit found the final handoff gap: Brain-LLM/Learning consumed `automation/provider-current-structure-evidence.json`, while canonical `scripts/brain_repair_runtime.py` did not attach that observation to V6 runtime candidates.
- Canonical Repair now sanitizes the same observation and attaches it to the in-memory candidate. Adaptive Repair may use the current origin and route path as bounded sandbox hypotheses and may raise player/embed exploration to the observed indexed fan-out.
- Unknown methods remain UNKNOWN; request-key names never become an executable request recipe. Only a request trace that actually executes in a validated winner may be persisted as replay DATA.
- Generic contract proves a synthetic current origin + `/wp-json/.../resolve` + 2 groups / 10+9 variants yields current-origin selection, bounded 19-player exploration and `variant-coverage` focus without granting proof/publication authority.
- For CoFlix this lets Brain test the current `coflix.ac` resolver structure instead of only widening the stale `coflix.wiki/ajax` traversal. No CoFlix production provider runtime was manually edited.

## 2026-10-02 — FORCE selection now includes Brain static variant debt

- Dynamic fan-out cannot detect every completeness failure. A runtime may truncate before later qualities/servers are ever requested or announced; HindMoviez's historical 480p-only symptom is the representative example.
- Canonical Repair V6 now pins current NiakVIO-Brain-LLM main at run time and executes its existing generic `audit_registered_runtime_variant_coverage()` against current registered provider runtime Lego. The resulting artifact is bounded, public-code-derived and `proofAuthority=false`.
- Only Brain rows classified `risk=high` / `highRiskProviders` may reopen a provider from this static source, and only in explicit `force` mode. Routine Repair does not mutate a nominally green provider from static suspicion alone.
- V6 FORCE selection is therefore generic: durable census repairQueue + current dynamic fan-out debt + current Brain high-risk static runtime debt. Static selection still grants no publication authority; candidates must produce current-byte playback/identity/completeness gain and pass non-regression.
- This covers caps and first-success patterns in current runtimes without hard-coding HindMoviez, CoFlix, StreamZo, PapaDuStream, MoviesMod or UHDMovies into Repair selection.

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


## 2026-10-03 — Dynamic completeness handoff proven; Coflix FORCE representative armed

- Brain control-plane fixes on main: `06068d2` preserves structured JSON quality fan-out debt; `f04b9a4` routes dynamic completeness debt through Autopilot/Learning without granting publication authority; `2caa9fd` rebuilds the durable Repair batch plan after syncing current main against the exact sharded ledger. Workflow Gate and Provider Non-Regression passed on the corrected control-plane.
- Global sharded census run `37088495401` completed 8/8 successfully from `4e3111934fa0` and persisted as `6c577318`. The durable plan now contains 6 dynamic-variant providers: animevost-fr, animevostfr, coflix, hindmoviez, kehflix, vidlove.
- HindMoviez is no longer a valid FULL completeness representative: current census reclassifies it `REGRESSION PROVIDER` with movie/tv no-stream transport/lookup failures. Its 480/720/1080/2160 announced variant evidence remains attached, but transport/lookup outranks completeness until playable output is restored.
- Coflix remains `FULL OK` on anime/movie/tv and is isolated in `variant-coverage|mixed_embed_resolver` from current sharded evidence. It is the first representative for Brain-driven completeness validation.
- Fast Brain Repair is armed for Coflix only in FORCE mode. Success requires Brain-generated change -> application -> rematerialization -> current-byte playback + identity + verified completeness gain -> non-regression -> persistence. No provider-specific manual production fix is authorized.


## 2026-10-03 — Partial census no longer erases global completeness debt

- Coflix FORCE reached canonical Brain Repair on run `37090295905`; GitHub-hosted runtime evidence was `provider_http_blocked`, so Brain correctly accepted/published zero provider mutations and handed Coflix to Learning FORCE instead of masking transport uncertainty.
- Learning FORCE runs `37090364428` and `37090899336` correctly routed Coflix as `variant_coverage_gap`, but the pinned Brain-LLM `f0a05851` made zero LLM calls because advisor prompt construction rejected its own payload as over budget. Deterministic recovery exhausted through generation 5 and produced no FORCE-promotable architecture blueprint. These runs do not prove Coflix repaired.
- Brain-LLM `7e8b4d2` fixes advisor-only prompt compaction and is CI green: advisor guidance carries no mutation-sized source authority while preserving current variant-coverage evidence.
- The post-Learning unresolved census persisted `96fd2bb` and exposed another control-plane split-brain: the all-provider fan-out ledger stayed on global run `37088495401`, but the durable Repair plan rebuilt only from the unresolved-run rows and silently dropped Coflix/Kehflix/VidLove completeness debt.
- Batch planning now merges current sharded evidence with the last global fan-out ledger. Providers actually observed in the current census supersede fallback debt (including clearing stale gaps); providers absent from a partial census retain the last global completeness debt. The plan's `sourceRunId` remains the current census run for FORCE freshness checks.
- Next proof: run a fresh unresolved census and verify Coflix/Kehflix/VidLove remain in `dynamicVariantProviders` despite not being retested, then rerun Coflix FORCE with Brain-LLM `7e8b4d2` and require a real LLM guidance row before evaluating any candidate.


## 2026-10-03 — Census iteration latency reduced

- User feedback confirmed the Brain/provider loop was too slow because representative validation repeatedly paid full-catalogue costs.
- Root causes measured: sharded census always launched 8 shards even for one representative; each shard rematerialized the whole catalogue; adaptive quick-yield timeout was per fixture, so one provider could consume several minutes across the fixture queue. Historical shard-7 evidence showed AnimeKai consuming ~357s for one lane while normal rows were ~4-10s.
- `3cee710c`: bounded census partitioning — all=8 shards, unresolved=4, explicit targetProviders <=4 => 1 shard, larger targeted cohort => 2. Merge now expects the dynamic shard count.
- `cff96dc6`: added a total per-provider quick-yield budget (90s in sharded census) on top of the per-fixture timeout; budget exhaustion is explicit evidence and prevents one slow provider from holding a shard for several fixture timeouts.
- `5a30aedc`: updated the historical workflow contract to the bounded-shard architecture.
- Targeted Coflix validation run `37092636124` proved prepare selects exactly `Census shard 0 of 1`. Its source SHA predates the targeted-materialization optimization, so that run still pays full materialization and is not evidence for the next optimization.
- `8fdee542`: targeted census now rebuilds only the explicitly requested provider(s) with `materialize_provider_v3_one.py`; unresolved/full scopes retain global materialization. This optimization is implemented but still requires a subsequent targeted run to prove runtime behavior.
- Current Coflix authority remains FULL OK with dynamic variant debt retained by census `37091625544`; completeness is not yet claimed repaired.


## 2026-10-03 — Stale FORCE/domain loop removed; VidEasy retired; current authority revalidation armed

- Autopilot was stalled by a persisted historical FORCE trigger: workflow-run convergence rebuilt the current plan but suppressed dispatch with `force-requires-new-explicit-trigger`. `bbf21dd6` scopes FORCE to the explicit push event only; later workflow-run convergence ignores stale FORCE state and continues ordinary current-census planning.
- The resumed Autopilot correctly selected transport before provider mutation, but Domain Refresh ran globally for the single VidEasy owner. The run proved a real split-brain: registry direct `player.videasy.net`, provider patch `www.vidking.net`, and GitHub observation could not validate the upstream.
- VidEasy has authoritative operator shutdown evidence effective 2026-09-15. `955f5a1b` adds generic `upstream_shutdown` lifecycle authority that outranks stale structured backend memory after its effective date, so Repair cannot waste cycles resurrecting a retired upstream or silently substitute another service.
- PurStream simultaneously exposed a Domain projection bug: current structured authority expected `purstream.tech` while published CONFIG retained `purstream.cat` in the first `origins` slot. Whole-list rewriting was too coarse because other historical origins (`purstream.ad`, `purstream.id`) must remain historical evidence. The Domain projection now rewrites only mismatched positions that are exactly explained by explicit old→current host authority.
- Projection Reconcile run `37116720382` passed and published current PurStream bytes as `8104867d` / `2c6069ca`; executed CONFIG now starts `origins=[https://purstream.tech,...]` while preserving historical API/site origins.
- Provider Disabled Lifecycle run `37116977950` passed and published `3b37df0a`: VidEasy is now `enabled=false`, bytes moved to `provider-disabled/`, reason `auto_off_upstream_shutdown`, retention until 2026-10-10. This is a lifecycle result, not a provider repair.
- Brain FORCE readiness then exposed a second split: planner classified compact census `dominantIssue=timeout` as `provider_transport_gap`, but adaptive runtime focus recognized only `provider_network_timeout`, so AnimeKai had no `transport-first` focus. Current fix aligns the runtime focus with the planner for compact `timeout`.
- The durable census/plan is still stale at run `37111537577` and therefore still lists VidEasy repair debt even though current main has disabled it. A fresh unresolved sharded census is explicitly armed now; success criteria are: current active authority excludes VidEasy from repairQueue/groups, global completeness fallback still retains Coflix/Kehflix/VidLove/HindMoviez debt, and Autopilot dispatch resumes from that fresh sourceRunId.


## 2026-10-03 — Domain transport ownership narrowed; AnimeKai no longer preempts independent Brain debt

- Fresh unresolved census `37124297614` completed 4/4 on `51f6c87b`; canonical persistence `70853e7d` removed retired VidEasy from repair authority while retaining global completeness debt for animevost-fr, animevostfr, Coflix, HindMoviez, Kehflix and VidLove.
- Autopilot `37124721950` misrouted AnimeKai to Domain even though census authority was already `KEEP_PROVEN_SITE`. Domain run `37124745647` changed no AnimeKai authority, scanned 41 active providers, hit 19 DNS API-limit observations, mutated WookaFR, and published `899c84e7` / `74fd0457`.
- Brain execution routing now sends transport debt with already-qualified address/backend authority to `BRAIN_LEARNING` via `qualified_authority_transport_learning_v1`. Only unresolved address authority remains `DOMAIN_REFRESH`.
- Autopilot passes exact provider ids to Domain and no longer lets a qualified AnimeKai transport issue preempt independent Coflix/completeness Learning. FAST publication remains deferred while a true targeted Domain transaction is in flight.
- WookaFR remains a projection-drift repair owned by the generic projection pipeline; no provider-local manual patch is authorized.


## 2026-10-03 — Domain/Native convergence validated; current Autopilot resumed

- Provider-scoped Domain ownership is now on main. Qualified transport authority no longer routes through Domain: AnimeKai (`KEEP_PROVEN_SITE`) is owned by Brain Learning via `qualified_authority_transport_learning_v1`; unresolved address authority alone may enter Domain Refresh.
- Domain Refresh accepts an exact provider cohort and scopes transaction projection drift, registry/history sanitation, provider metadata reconciliation and DNS observation to that cohort. Domain implementation/code changes no longer auto-run a catalogue-wide mutation.
- Projection Reconcile run `37128406179` detected exactly one drifted provider (`wookafr`), rematerialized it from accepted DATA/Lego, proved `FIELD_PROVIDER_PROJECTION_FIXED_POINT providers=0`, and published `6645607a` / `4faaa85a`. Current WookaFR bytes `providers/wookafr--nuvio--23ba5112dfdbfc0a.js` include `https://wookafr.boston` at the head of `origins`.
- Post-projection TEMP full census still fails on the pre-existing 4KHDHub runtime behavior witness (`movie=[]`); this is unrelated to the Domain/WookaFR repair and remains unresolved Brain/provider work.
- Core Verify exposed a separate native lifecycle split: durable Hub46 scope still listed VidEasy after lifecycle disable. `adad3b70` / `4db91579` make current `enabled=false` manifest state authoritative before durable scope evidence, so disabled providers cannot re-enter the native quality denominator.
- On HEAD `4db91579`: Workflow Gate passed, Provider Non-Regression passed, and Core Verify Quick passed. No PR is open; all changes remain on main.
- Canonical provider authority remains census `37124297614`: 21 FULL OK, 3 PARTIAL OK, 2 CANDIDATE OK, 10 ROUTE PROVEN, 2 CHAIN REACHED, 1 NO PROOF, 2 REGRESSION PROVIDER, 5 DISABLED. VidEasy is absent from repairQueue; dynamic completeness debt remains animevost-fr, animevostfr, Coflix, HindMoviez, Kehflix and VidLove.
- Autopilot is re-armed in ordinary `auto` mode from census `37124297614`. Expected proof: Domain cohort empty for AnimeKai; AnimeKai appears in Brain Learning; Coflix and other current completeness debt are not preempted by transport.


## 2026-10-03 — Learning/census convergence made main-only

- Current canonical census `37131173373` completed successfully and persisted as `fee9f004`. Counts remain 21 FULL OK / 3 PARTIAL OK / 2 CANDIDATE OK / 10 ROUTE PROVEN / 2 CHAIN REACHED / 1 NO PROOF / 2 REGRESSION PROVIDER / 5 DISABLED across 46 census identities. Dynamic completeness debt remains for animevost-fr, animevostfr, Coflix, HindMoviez, Kehflix and VidLove.
- AnimeKai is no longer Domain-owned in the current plan: it is `learning|mixed_embed_resolver` with dominant issue `timeout`, proving the qualified-authority transport routing fix survived the fresh census.
- Brain Repair Lab `37130439392` failed only in the optional proposal-publication job. The sandbox/learning state produced concrete provider/skill proposals, but the PR materialization gate re-ran the clean ProviderBase contract against source-state PROVENANCE. The durable ProviderBase history remains 96/96 while the sandbox active materializer intentionally projects current active coverage before tests; the failure was in the proposal/PR path, not the Brain experiment itself.
- Autopilot is now main-only: it always dispatches Learning with `publish_proposal=false`. It will not create/refresh provider repair proposal PRs or repair branches. Learning persists evidence/memory; canonical Repair/census consumes that state.
- A census launched through another workflow did not reliably produce the expected `workflow_run` Autopilot continuation. Sharded census persistence now explicitly dispatches `provider-brain-autopilot.yml` with `workflow_dispatch` after a successful canonical push. This removes reliance on recursive GitHub event propagation.
- No open PRs at this checkpoint. Current execution remains on `main`.


## 2026-10-04 — PR 228 closed; Brain PR creation moved behind explicit opt-in

- PR #228 (`brain: Learning architecture evolution proposal`) was still open even though its branch was 64 commits behind current `main` and contained only review-only architecture proposal JSON/Markdown. It was closed unmerged as superseded; no stale proposal bytes were copied to production.
- Root cause: `.github/workflows/brain-learning-lab.yml` still allowed proposal PR creation from Learning. Both repair-proposal and architecture-proposal PR publication now require explicit `workflow_dispatch publish_proposal=true` plus repository variable `NIAKVIO_ALLOW_BRAIN_PROPOSAL_PR=true`. Architecture FORCE direct-main promotion remains available and unchanged.
- Repository Hygiene is re-triggered to delete `brain-architecture/proposal`; persistent sanitized Learning memory remains allowed only on `brain-learning/proposals`.
- Security verification at this checkpoint: issue #69 (global provider bundle security hardening) is closed/completed; no open GitHub issues were found; no Dependabot PRs were found; scheduled CodeQL run 37156098135 completed successfully across Actions, Python, JS Core and JS ProviderBase. The available GitHub connector does not expose the Advanced Security alert-list API, so this is not claimed as a direct proof of zero private Security-tab alerts.

## 2026-10-05 — Brain FORCE contracts repaired; publication fixed point restored; disabled CodeQL debt cleanup

- Fast Repair run `37349896639` on `ba65bfb8` remained non-publishable: 12 providers selected, 0 candidates, 0 validated, and the 12 unresolved providers returned to Learning. This is not provider success and the authoritative census remains 21 FULL / 3 PARTIAL / 2 CANDIDATE / 10 ROUTE / 2 CHAIN / 1 NO PROOF / 2 REGRESSION / 5 DISABLED with 17 in repairQueue.
- Two infrastructure/test failures that blocked a fresh Architecture FORCE proof were corrected on main: `db313d65` makes `brain_force_rebase_guard.py` import-safe under both direct execution and importlib tests; `460df29a` updates the self-architecture contract to the neutral-rebase lease `promotion_base` instead of the obsolete fixed `GITHUB_SHA` lease.
- Exact pre-finalizer validation for `460df29a`: Workflow Gate `37353019923` SUCCESS, Provider Non-Regression `37353019823` SUCCESS, maintained-source CodeQL matrix SUCCESS. Verify had previously exposed publication-contract/fixed-point drift rather than provider runtime failure.
- Accepted release finalizer `37354202167` completed SUCCESS. It reapplied all 41 active provider bundles, reached `FIELD_PROVIDER_FAST_FIXED_POINT status=hit`, passed published HTML/security/static audits, bumped release `5.21.106 -> 5.21.107`, bumped 41 provider versions, validated release integrity, and atomically published provider-generation SHA `b8e4219f` then final SHA `f50a21646fa49b1cb616c7641a01caa04a380deb`.
- The 17 user-reported open CodeQL alerts are all historical/lifecycle-disabled VidEasy snapshots under `provider-disabled/**` (not maintained active provider code). Maintained CodeQL already excludes that lifecycle archive while active ProviderBase/Core scanning stays enabled. The dedicated dismissal workflow is being invoked to clear those stale Security-tab alerts without weakening maintained-source analysis.
- Next representative proof remains Moviebox Architecture FORCE only. The trigger must be refreshed against current main and may not be considered successful until Brain produces/applies/rematerializes a current-byte repair that passes strict movie+tv proof; no provider-local manual patch is authorized.


## 2026-10-06 — Architecture FORCE materializer failure reproduced; Brain correction/replay loop hardened

- Authoritative census remained 21 FULL OK / 3 PARTIAL OK / 2 CANDIDATE OK / 10 ROUTE PROVEN / 2 CHAIN REACHED / 1 NO PROOF / 2 REGRESSION PROVIDER / 5 DISABLED, with 17 providers in repairQueue. Fast Repair `37522368401` selected the exhausted 12-provider cohort again but accepted 0 repairs and persisted only more `brain-strategy-exhausted` evidence; this is not provider progress.
- Architecture FORCE run `37520931361` on source `23cf2616b2abaecaf7df8c67a6edab23f99f879e` passed preflight/Learning/proposal synthesis but failed at executable materialization. Exact failure chain: primary Qwen request timed out -> minimal retry produced a patch -> transactional contract validation rejected a duplicate `FAILURE_FAMILY_TAXONOMY` key -> corrective retry timed out/formatted -> next correction targeted candidate-relative bytes and failed `replace find must occur exactly once: scripts/brain_meta_learning.py`. No provider bytes were changed or published.
- Root Brain bug: materialized validation restores baseline before corrective Qwen turns. A valid correction may therefore reference bytes that exist only in the rejected candidate; the materializer only knew how to widen repeated baseline anchors, not rebase candidate-relative corrections onto restored bytes.
- Brain fix commit `97f5ffa00363d152809e9a2e8eb69f6daf31c5ab` reconstructs the rejected candidate in memory, applies candidate-relative correction edits there, collapses the desired result back into one bounded unique baseline replace, and remains fail-closed for ambiguous/oversized transforms. The regression test reproduces the exact rejected-candidate correction shape from run `37520931361`.
- The same audit exposed two orchestration loops. First, an already-active Architecture FORCE could re-enter `Escalate exhausted targeted Learning to Brain architecture FORCE` when the source event was `push`. Second, a normal long-slot Learning run could both escalate to FORCE and dispatch its next normal phase; run `37522371795` logged both actions. The workflow now suppresses escalation whenever `architecture_force=true`, publishes `architecture_escalated`, and blocks normal slot continuation after an escalation.
- Architecture promotion is still not considered a provider repair. After a validated direct-main FORCE promotion, the workflow now chooses exactly one current repairQueue representative, preferring the FORCE-promotable blueprint cohort, and dispatches canonical `provider-recognition-repair-v6.yml mode=repair` for that one provider before any cohort-wide retry.
- Local validation on the corrected tree passed: `brain_architecture_force_materializer_test.py`, `brain_architecture_force_promotion_test.py`, `brain_llm_learning_workflow_contract_test.py`, `brain_meta_learning_gap_synthesis_test.py`, `brain_self_architecture_test.py`, Python compile, and `git diff --check`.
- Next authority sequence: publish the Brain fix on current `main`; cancel Learning runs still executing the superseded pre-fix Brain; rerun the 12-provider exhausted cohort through Architecture FORCE; require executable Brain diff -> direct-main promotion -> one representative canonical Repair -> rematerialized current-byte category/playback proof -> then one representative per remaining failure family before wider cohort expansion.

- Follow-up validation on current HEAD `721d748c29fe845b5cf27c209e216ad2e8b0ea18` exposed one stale repository-policy constant: `enforce_main_only_repository_policy.py` still expected the pre-neutral-rebase FORCE push lease on `$GITHUB_SHA`, while the validated workflow now correctly leases on `$promotion_base`. The policy checker and its repository-hygiene contract were updated to the `promotion_base` form; `enforce_main_only_repository_policy.py --check`, `repository_hygiene_contract_test.py`, `brain_architecture_force_promotion_test.py`, and `brain_llm_learning_workflow_contract_test.py` pass locally before FORCE replay.
- A second post-fix Architecture FORCE attempt, run `37525886424` on `721d748c29fe845b5cf27c209e216ad2e8b0ea18`, reached executable materialization but failed earlier in edit-plan validation: the first model replace for `scripts/brain_repair_runtime.py` was non-unique/invalid, then the corrective model response attempted `create` on existing `scripts/brain_meta_learning.py`, causing `create target already exists`. This is Brain materializer debt, not a provider failure.
- The materializer now distinguishes existing vs genuinely new exact correction paths, requires `replace` for existing files, reserves `create` for absent Brain-layer/test paths, and allows at most two edit-validation correction rounds before failing closed. A regression test reproduces the exact invalid-replace -> create-existing -> corrected-replace sequence from run `37525886424`. The premature replay run `37530846041` was cancelled before expensive work once this second failure mode was confirmed.
- FORCE run `37531485433` on `beb66dda16fbc5abb80dc1c69e1bb1f8fa4be978` proved the edit-validation retry fix but exposed a third materializer weakness: after a valid contract-repair turn, candidate-relative syntax repair was rebased but Qwen produced two syntactically invalid replacements (`brain_meta_learning.py`, malformed `materialization_projection` tuple/string) and exhausted the two materialized correction rounds. Premature replay `37546632178` was cancelled once this already-recorded same-SHA failure was confirmed.
- Brain materializer follow-up: materialized correction targets are now restricted to the file(s) that actually failed instead of all original planning-context sources; syntax/JSON/JS failures get explicit candidate-vs-baseline parser-only guidance, and materialized correction remains single-run bounded with three rounds. Provider/publication paths remain forbidden. Local targeted contracts pass before replay.

## 2026-10-07 — FORCE promotion reached main but novelty/replay contract was false-positive

- Architecture FORCE run `37547059786` on `8a622a7130d1d86047e622ce40320c8775265d90` finally crossed executable materialization and direct-main promotion. Promotion commit `ea9319126d80d487bcad8aeaa9be4ea6926ed581` was therefore a real pipeline milestone, but **not** a provider repair.
- Inspection of the promoted bytes showed the only executable code delta was `scripts/brain_meta_learning.py` changing the `materialization_projection` taxonomy token from `materializ` to `materialization`; the rest was proposal JSON/Markdown. This did not add a new Repair capability. The promoted architecture still marked existing `route_transition_graph_v1` / `terminal_transition_graph_v1` strategies as FORCE-promotable even though negative experiment memory already contained executions of those profiles. Current persisted proposal data still demonstrates the false-positive (`vidfast` is FORCE-promotable on `route_transition_graph_v1` while durable Brain memory records a failed `vidfast route_transition_graph_v1` experiment).
- Root cause: `build_brain_architecture_proposal.py` filtered negative profile history through the latest active request signatures before deciding architecture novelty. Signature rotation could therefore hide durable negative experience and recycle an exhausted `strategyId` as if it were new.
- Representative Repair `37549504656` never reached provider execution. Its preflight failed in `tests/brain_llm_advisor_report_observability_test.py` because `scripts/run_provider_brain_repair.py` did not preserve the required sanitized `postExhaustionCandidateProfiles` list representation. Follow-up Learning `37549514541` then attempted architecture materialization again and failed on repeated non-unique `brain_repair_runtime.py` replacements. Census authority remained 21 FULL / 17 repairQueue; no provider success is claimed.
- Brain correction now makes architecture novelty durable across signature changes. If an existing template profile has negative execution memory, the proposal evolves it to the next distinct profile generation (`*_v1 -> *_v2`, then higher as needed), records `evolvesFromStrategyId` / `exhaustedStrategyIds`, and grants FORCE promotion authority only to that evolved profile. Existing non-evolved templates remain diagnostic-only.
- `engine_v2/scripts/plan-repairs.mjs` is now an explicit FORCE structural/generated surface because a genuinely new Repair profile cannot be useful unless the planner can select it. The materializer requires evolved profiles to be wired through exactly three executable surfaces: `scripts/brain_repair_runtime.py`, `engine_v2/scripts/plan-repairs.mjs`, and `scripts/adaptive_runtime/runtime_repair.py`. Taxonomy/metadata/proposal-only edits are rejected before direct-main promotion.
- Repair observability was aligned so `postExhaustionCandidateProfiles` survives the sanitized Repair report contract. Local targeted validation passes: Python compile, Node syntax, deferred-cohort novelty, FORCE materializer, FORCE promotion, LLM advisor observability, meta-learning, self-architecture, main-only policy and `git diff --check`.
- Separate current Verify/Publish run `37547043314` failed only after its earlier published/Core checks passed, on `FIELD_PROVIDER_FAST_FIXED_POINT status=miss reason=provider-policy-changed:wookafr`. Treat this as distinct WookaFR projection/fixed-point debt, not proof against the Brain FORCE correction.
- Next authority sequence: publish this Brain correction on current `main`; rerun Architecture FORCE for the exhausted cohort; require a **new** executable profile generation to be present in planner + Repair registry + adaptive runtime; direct-main promote only that complete wiring; then require the one representative canonical Repair to pass preflight, materialize current bytes and demonstrate playable/identity-safe provider improvement before expanding to another failure family.


## 2026-10-07 — FORCE repeated-anchor materialization hardened

- Architecture FORCE run `37646660891` reached executable materialization but failed twice on the same edit-validation error: `replace find must occur exactly once: scripts/adaptive_runtime/runtime_repair.py`. The provider cohort was not executed or repaired.
- Root cause: the model's bounded replace token can legitimately occur more than once inside the exact focused source snippet even when the blueprint's `strategyId` / `evolvesFromStrategyId` uniquely identifies one intended occurrence. The existing resolver only handled repeated finds when the find itself was unique inside the snippet.
- Brain materialization now keeps the fail-closed contract but may bind a repeated find to the uniquely nearest blueprint strategy anchor inside a source snippet that is itself unique in the current file, then widen unchanged neighboring bytes until the replace anchor is globally unique. Ambiguous/tied anchors are still rejected.
- Regression coverage reproduces the `runtime_repair.py` repeated-find failure family and verifies that only the anchored occurrence changes. No provider-local production code is edited by this fix.

## 2026-10-07 — Architecture FORCE concurrency isolated from routine Learning

- Explicit FORCE run `37653501632` on Brain fix `1c0caae` passed catalogue observation, ProviderBase reconstruction, Brain LLM routing and Qwen guidance, but was cancelled externally during `Run adaptive Learning provider queue` before proposal/materialization. This is not a materializer failure and not provider progress.
- Root orchestration cause: targeted Learning concurrency was keyed only by provider cohort and always used `cancel-in-progress=true`. Routine Autopilot/Fast handoff Learning on the same 12-provider cohort could therefore cancel an explicit Architecture FORCE after expensive Learning/Qwen work.
- Brain Learning now gives explicit `architecture_force=true` runs a separate `niakvio-brain-learning-force-<cohort>` concurrency lane with cancellation disabled. Routine targeted Learning retains replacement of stale routine work, but cannot cancel FORCE; a second FORCE queues behind the first.
- Contract coverage verifies the FORCE-specific concurrency key and cancellation guard. Provider bytes remain untouched; census authority is still 21 FULL / 17 repairQueue.

## 2026-10-07 — FORCE strategy-block anchoring and failure artifact persistence

- Architecture FORCE run `37655129624` on `7eebb7c` completed catalogue observation, ProviderBase reconstruction, Brain LLM routing/guidance, adaptive Learning and architecture proposal synthesis, then failed only in executable materialization. The repeated failure remained `replace find must occur exactly once: scripts/adaptive_runtime/runtime_repair.py`; no provider bytes were changed or published.
- Reconstructed current Learning memory + batch plan shows the first promotable blueprint is `route_transition_graph_v2`, evolved from exhausted `route_transition_graph_v1`, for the route-to-terminal cohort. The exact FORCE source context includes the prior `elif new_strategy_id == "route_transition_graph_v1"` implementation block.
- Root Brain materializer weakness: repeated replace text may exist in several adjacent runtime strategy branches. Generic nearest-text anchoring is not strong enough, and compact corrective payloads can truncate the original source window.
- The resolver now first binds repeated finds to the exact blueprint-owned prior `new_strategy_id == <evolvesFromStrategyId>` block, requiring exactly one occurrence inside that block. If compact source context no longer contains the block, it may use the same exact block in the complete current file. Ambiguous blocks still fail closed. Unresolved cases now emit `FIELD_BRAIN_ARCH_FORCE_ANCHOR_UNRESOLVED` with strategy/evolves-from and bounded find preview.
- Learning artifact upload now runs with `always()` and warns on absent optional files, so failed FORCE runs preserve sanitized proposal/report evidence instead of discarding the diagnostic state. Publication jobs still require successful experiment completion.
- Local validation passed: FORCE materializer, FORCE promotion, LLM Learning workflow, Brain cron coverage, deferred cohort, meta-learning, self-architecture, repository hygiene, main-only policy, Python compile and `git diff --check`.
- Separate CodeQL run `37655088396` failed only in JS ProviderBase after analysis reached SARIF upload; Python/Actions/JS Core passed. The check annotation contains only the GitHub ubuntu-latest migration notice. Treat as a scan/upload failure pending a fresh run, not as a proven new code alert.

## 2026-10-07 — FORCE new-profile fallback made three-surface and additive

- FORCE run `37662687597` on `7179614` proved the repeated-find anchor fix: `runtime_repair.py` was resolved deterministically, but transactional materialized validation rejected the candidate because Qwen replaced the existing `route_transition_graph_v1` strategy block instead of adding `route_transition_graph_v2`.
- Root cause was Brain-side prompt/context starvation, not provider code: generic compact/minimal fallbacks exposed only a small total source budget and explicitly preferred one small replace, while `requiresNewExecutableRepairProfile=true` requires a complete additive transaction across exactly three executable surfaces.
- New-profile FORCE requests now retain bounded context for all mandatory surfaces independently: `scripts/brain_repair_runtime.py`, `engine_v2/scripts/plan-repairs.mjs`, and `scripts/adaptive_runtime/runtime_repair.py`. The model contract requires exactly three replace edits, preserves `evolvesFromStrategyId`, adds the new strategy instead of renaming/removing the old one, and forbids test edits for this transaction.
- New-profile corrections use the same three-surface scope and larger bounded output/time budgets; they no longer inherit the generic `preferSingleSmallReplace` contract. Any materialized failure on a new-profile blueprint is treated as an end-to-end profile-wiring correction even if a generic contract test is the first failure surfaced.
- Targeted Brain/materializer, promotion, Learning workflow, deferred cohort, meta-learning, self-architecture, repository-hygiene and main-only tests are green locally. Census authority remains unchanged until a real provider replay proves improvement.

## 2026-10-07 — FORCE profile evolution parent-preservation gate

- FORCE `37676390597` on `630d118` reached materialized validation repeatedly. The repeated-find anchor was fixed, but Qwen still broadened/replaced the parent runtime guard for `route_transition_graph_v1`, causing `tests/brain_architecture_force_materializer_test.py` line 140 to fail on every correction round.
- Root cause: the materializer required the new strategy id on all three Repair surfaces but did not semantically require the exhausted parent runtime branch to remain a separate unchanged guard before running contract tests. The model could therefore satisfy “v2 present” by merging v1/v2 into one condition, which violates additive strategy evolution and corrupts negative-memory semantics.
- Brain validation now runs blueprint implementation checks before contract tests and rejects any candidate that removes/broadens the exact `new_strategy_id == "<evolvesFrom>"` parent guard. The model prompt explicitly requires a separate sibling v2 branch and forbids renaming/replacing/broadening the parent.
- Regression coverage rejects a shared `{v1,v2}` runtime guard and accepts a distinct additive sibling branch. Targeted materializer/promotion/Learning contracts and main-only policy pass locally. No provider bytes were edited.


## 2026-10-07 — FORCE registry/planner repeated-find fallback

- FORCE `37680228320` on `0b4241a` passed Learning/proposal generation but failed before materialization because Qwen returned a repeated replace anchor in `scripts/brain_repair_runtime.py`. The existing full-file fallback only had a dedicated exact-block resolver for adaptive runtime `if/elif new_strategy_id` branches.
- Root cause: compact/new-profile model output can legitimately target generic registry/planner text that appears more than once in the full file. The focused snippet may no longer contain the target after bounded corrective compaction, leaving registry/planner edits without a deterministic full-file anchor even though the blueprint parent strategy uniquely identifies the intended occurrence.
- Brain materialization now reuses the blueprint-aware full-file resolver for all required Repair-profile surfaces. Runtime still prefers exact strategy-block binding; registry/planner repeated finds bind only when one occurrence is uniquely nearest to `evolvesFromStrategyId` / `strategyId`. Equal-distance ambiguity remains fail-closed.
- Regression coverage reproduces the `brain_repair_runtime.py` repeated registry entry family from FORCE `37680228320` and proves only the parent-adjacent occurrence is modified. No provider bytes were edited.


## 2026-10-07 — route_transition_graph_v2 manual oracle promoted into Brain infrastructure

- FORCE `37684955291` on `a781e3f` passed catalogue observation, ProviderBase reconstruction, Brain LLM routing/guidance and adaptive Learning, but spent ~20 minutes in materialization and failed after three corrective rounds because Qwen repeatedly broadened the exhausted `route_transition_graph_v1` runtime guard instead of producing a distinct sibling `route_transition_graph_v2` executor.
- The failure is now treated as a Brain materialization capability limit, not a provider defect. Per Brain-first policy, no provider bytes were patched.
- A manual oracle was promoted into reusable Brain infrastructure: `route_transition_graph_v2` is registered in the Repair registry, planner and adaptive runtime. The strategy is intentionally distinct from v1: same-provider-first retained/current/historical request programs, provider-owned transition prefixes observed in route DATA, and runtime response salvage for terminal/player URL recovery. Peer-route mixing is not the primary program.
- Planner ordering places v2 immediately after v1 for the route-proven causal family. Existing negative-memory + implementation-fingerprint rotation will skip an exhausted v1 and select v2 when appropriate.
- Targeted validation is green: Python compile, Node syntax, second-order runtime strategy contract, Brain LLM advisor/planner execution contract, FORCE materializer/promotion contracts, Learning workflow contract, main-only policy and `git diff --check`.
- Next authority: publish this Brain infrastructure change, run one representative Repair on 4KHDHub, verify planner selected `route_transition_graph_v2`, materialize current bytes, and require real route/terminal/playback + identity-safe proof before any cohort expansion.


## 2026-10-07 — Repair preflight WookaFR harness de-staled

- Representative Repair `37690698515` on `9c8b893` never reached 4KHDHub. It failed in preflight `tests/provider_wookafr_current_runtime_behavior_test.py` with `movie fallback failed []`.
- Reproduction on current main proved the test fixture was stale: it mocked only `https://wookafr.boston`, while authoritative `provider-overrides.json` configures WookaFR runtime bases as `wookafr.blog / .center / .plus` and census authority remains FULL OK. No WookaFR provider bytes were changed.
- The harness now derives its mocked primary base dynamically from the same `provider_lego_options` used to compile `wookafr_current_runtime_v2.py`. Movie + TV multiplayer behavior passes again without hard-coded historical domains.
- Targeted validation passes: Wooka current runtime behavior, provider v3 strategy plan, Brain preflight fail-fast ordering, Brain preflight incremental materialization scope, and `git diff --check`.
- Next authority remains a targeted 4KHDHub Repair using Brain `route_transition_graph_v2`.


## 2026-10-07 — Adaptive Repair planner now preserves explorationChain

- Representative Repair `37691213661` on `0ecef5a` completed successfully as a workflow but did **not** repair 4KHDHub: current-byte audit remained raw/playable/verified = 0, Brain accepted 0 repairs, and repairQueue stayed 17.
- Artifact `automation/provider-brain-repair-latest.json` proved the new `route_transition_graph_v2` capability was visible in `postExhaustionCandidateProfiles`, but the actual plan had `explorationChainEnabled=false`, `strategyEscalated=false`, empty `postExhaustionStrategyProfile`, and deferred the provider to Learning.
- Root cause: `scripts/adaptive_runtime/brain_repair_runtime.py::update_plans()` rebuilt the bounded planner payload without the `explorationChain` field. The representative runner correctly exported `NUVIO_BRAIN_EXPLORATION_CHAIN=1`, and `replan_observation()` preserved it, but the initial adaptive planning path silently dropped it before Node.
- The adaptive planner payload now includes `"explorationChain": _BASE._exploration_chain_enabled()` in both initial planning and replanning. Production remains fail-closed unless the caller explicitly enables the exploration chain; normal production runs are not broadened.
- Regression coverage now functionally exercises adaptive `update_plans()` with the explicit chain bit and asserts two explorationChain transport sites in the overlay. Brain replan transport, exploration budget, LLM advisor execution, second-order runtime strategy, provider Brain orchestrator, main-only policy and `git diff --check` pass locally.
- Next authority: rerun only 4KHDHub Repair and require the artifact to show `explorationChainEnabled=true`, `postExhaustionStrategyProfile=route_transition_graph_v2`, actual execution, current-byte materialization, and playable/identity-safe improvement before counting a repair.


## 2026-10-07 — Post-exhaustion rotation now advances to route_transition_graph_v2

- Representative Repair `37692469203` on `b2f4802` proved the adaptive exploration-chain transport fix: the 4KHDHub plan had `explorationChainEnabled=true`, `explorationModeEnabled=true`, `strategyEscalated=true`, and executed a real post-exhaustion child candidate.
- That run still did not repair 4KHDHub. It executed `html_class_token_exact_v1`, which remained `no_streams`; production/playback proof stayed raw=0/playable=0/verified=0 and repairQueue remained 17. The failure was persisted with implementation fingerprint `199e8c91727af61828cbeffed9b0f0823aa80056b864bf9d65d4431a02ad142c`.
- Root rotation weakness: legacy negative-memory rows with no `strategyImplementationFingerprint` were treated as if the same profile id had never failed whenever the current implementation exposed a fingerprint. This can resurrect exhausted v1 strategies and force many one-hypothesis Repair runs before a newly learned v2 profile is reached.
- Negative memory is now fail-closed for legacy unversioned rows: a missing remembered fingerprint means the profile id already failed. Materially new behavior must receive a new generation/id instead of silently reopening the same v1 id.
- Generic route/search post-exhaustion ordering now prioritizes `route_transition_graph_v2` over `route_transition_graph_v1`, and places v2 immediately after the exact HTML parser in `search_gap`. A functional planner contract reproduces the representative sequence: base search variants exhausted -> html_class_token_exact_v1 current implementation fails -> legacy search-contract debt remains exhausted -> next allowed profile is exactly `route_transition_graph_v2`.
- Brain final-generation, advisor execution, negative-exhaustion, second-order runtime, exploration transport/budget, Repair orchestrator, main-only policy and `git diff --check` all pass locally. No provider-local production bytes were edited.
- Next authority: rerun only 4KHDHub Repair and require the artifact to select and execute `route_transition_graph_v2`; only current-byte playable/identity-safe improvement may count as a repair.

## 2026-10-08 — Repair client preflight et récupération prioritaire

- Census autoritatif : 21 FULL OK / 46, 17 repairQueue, 2 régressions AnimeKai et UHDMovies. AnimeKai : provider_network_exception, historique Jujutsu Kaisen. UHDMovies : provider_network_zero_result, historique Avengers Endgame. Aucun des deux n'a été testé dans le run census le plus récent.
- Repair 37694238142 sur 883cba7 interrompu avant exécution provider : timeout Git diff --name-only sur le client Desktop blobless, état verification_inconclusive.
- Correction Brain/Core : changed_tree_paths utilise git diff-tree -r --no-renames --name-only ; il lit les trees sans charger tous les blobs. Les renommages retiennent ancien et nouveau chemin sensible.
- Le test live Desktop a révélé en second un objet promisor manquant lors de la lecture des anciens patches sémantiques. Pour le seul préflight Repair, option --paths-only : exact upstream HEAD et ascendance vérifiés, fichiers sensibles énumérés, aucun patch sémantique ancien téléchargé.
- Tout chemin sémantique non inspecté est conservé dans semantic_review_unverified_files, classé contract_review_required, jamais safe_advance_available. Les Native Labs conservent leur audit complet.
- Contrôle live sur Git Apple 2.50 : Desktop, Mobile, TV ont compare_status=ahead, zéro verification_error/inconclusive. Respectivement 66, 90, 86 chemins sémantiques non inspectés ; audit natif toujours obligatoire.
- Le garde Brain accepte le cache vérifié : adaptation_pending=3, native_reader_acceptance_required=true. Tests verts : Nuvio upstream drift, Nuvio latest-HEAD Lab resolver, Brain Learning workflow, Brain strategy runtime, causal replan, main-only.
- Aucun provider publié ou réparé par cette amélioration. Prochaine autorité : Repair current-byte ciblé AnimeKai puis UHDMovies, preuves réseau/identité/terminal/playback, uniquement via Brain.

## 2026-10-08 — Brain stalled Repair must hand off real Learning debt

- Canonical UHDMovies Repair `37705963499` passed the Git/client preflight, proved its search route HTTP 200 and materialized current provider bytes but produced `acceptedRepairCount=0`, `noProgressReason=no_new_repair_experiment`, and `deferredLearningProviders=[]` despite accessible HTTP 200 detail responses and no playable output.
- Root Brain orchestration defect: `run_provider_brain_repair.py` breaks on `stalled`/`exhausted` without declaring genuinely unresolved remainder as LEARN-owned debt. This produces false convergence and repeated unchanged advisor attempts.
- Fixed in Brain only: `stalled_experiment_learning_handoff` routes remaining providers to `all_deferred` upon stalled/exhausted decisions, but excludes same-byte harness/transport differentials. It emits `FIELD_PROVIDER_BRAIN_STALLED_LEARNING_HANDOFF`; the original failure reason remains explicit. Tests lock UHDMovies-type stall and harness exclusion.
- No provider bytes were edited by this patch. Evidence still requires Brain-generated new executable strategy, sandbox, current-byte replay, identity and terminal playback verification before promotion.

