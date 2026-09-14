<!-- NIAKVIO_MEMORY_PENDING_EMPTY -->

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
