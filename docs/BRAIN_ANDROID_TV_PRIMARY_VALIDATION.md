## 2026-11-19 — Verified historical replay without rerunning Android TV

- **Entry point**: `.github/workflows/brain-replay-archived-tv-evidence.yml` runs on a bounded explicit historic TV run ID (and on its own workflow-file change). It first checks official run name/path, repository/branch, completed conclusion and exact NiakVIO SHA; then checks out the original source separately from the current trusted parser and current Brain router. A failed native acceptance run is allowed as a diagnostic source, **not** as proof of a working provider.
- **Replay chain**: download original TV log and original report into the runner's temporary directory; preserve the original official client SHA; parse current reason-phrase HTTP statuses and exact same signed HLS master 2xx→403; reject missing signatures or raw-log count drift; sanitize to enums, codes and original source identity; merge with 10-entry/provider bounded memory; route Brain read-only and publish only the sanitized plan; commit memory under the shared writer lock. No changes to provider JS or manifests. If a CI step fails, no Brain history write is allowed.
- **Verification**: [first run 44600402823](https://github.com/niakw/NiakVIO/actions/runs/44600402823) failed because the parser did not recognize `200 OK url=...` or `403 Forbidden url=...`; parser and a realistic native regression test fixed in f093177. [rerun 44600919814](https://github.com/niakw/NiakVIO/actions/runs/44600919814) **SUCCESS**, recovered one exact URL transition and routed French-Manga/Jujutsu S01E01 to `llm_diagnose` / `core` / `reuse_successful_hls_root_across_core_validation`, then persisted the redacted exact-source receipt in main commit 3d871b9e. Model executed: **no**. Provider fixed, materialized or decoded: **no**. Still determine the shared pre-player second-fetch owner before any fix and re-test the actual native player, decoded correct episode and French/multi-audio afterward.

## 2026-11-19 — Native QuickJS Promise control and hard timeout preservation

The test-only NuvioTV corpus exercises the accepted official `PluginRuntime` using two strictly synthetic exports (an immediate result, then an `await Promise.resolve(1)` result). They return dummy `example.invalid` URLs which never enter media/player or production manifests. `FIELD_NATIVE_TV_PROMISE_CONTROL` emits only two bounded result counts. The sanitized native reader JSON exports only `bridge_ok`, `promise_delivery_gap` or `baseline_failed`; all proof/publication/JS-mutation authorities remain false. A bridge gap is a **client runtime causality hint**, not proof that a specific provider is broken or repaired. This must be tested inside the official emulator, not merely parsed statically.

Native errors are independent from QuickJS console phases. In particular, NuvioTV can select a provider, log `QuickJS call`, and then have the *outer native harness* end after `provider_hard_timeout_ms=25000` with no JavaScript `result/error`. `engine_v2/scripts/diagnose-native-reader.mjs` reads an exact `FIELD_NATIVE_ERROR` and exports only `provider_hard_timeout` plus bounded elapsed/configured milliseconds; `scripts/ingest_brain_android_tv_emulator.py` carries this code in the exact-source/same-bundle historical ledger as `nativeHardTimeoutObserved` and `nativeHardTimeoutMs`. This is neither a returned `[]` nor a media terminal. The Brain must diagnose network/WAF vs runtime/bridge vs Core vs provider before it can assign correction authority. Historical records can inform reasoning but cannot authorize publication or mutation.

In the demonstrated [Sadisflix official TV run 44529501795](https://github.com/niakw/NiakVIO/actions/runs/44529501795), the VF provider was enabled and app-eligible; its native execution hit 25,000 ms with no player. Initial automatic [Brain feedback 44533227233](https://github.com/niakw/NiakVIO/actions/runs/44533227233) lost that terminal event and suggested a generic provider deterministic advisor. This is precisely the generic evidence-loss regression covered by new tests. No production provider JS or Nuvio client sources were changed.

# NiakVIO — Android TV first, Brain-driven repair loop

**Policy date:** 2026-11-19. **Main product:** NiakVIO + Brain-LLM, not an individual provider.

## Platform and ownership

**Android TV (official NuvioTV) is the primary execution and release-acceptance target.** Desktop macOS, Android Mobile and iOS remain compatibility/regression clients. Reuse their already implemented Core, runtime, JS ProviderBase and Lego adapters; do not fork a provider implementation for each platform. Client differences are diagnostic evidence of a common pipeline weakness, not instructions to add a provider-specific override.

The Android TV emulator itself runs in **GitHub Actions**, not inside model weights or Brain's Python package. Brain is its **controller, causal classifier and learning consumer**. One centralized service means the same official client can be replayed by repair workflows, native acceptance and Brain without reimplementing Gradle, AVD, adb or the media player.

## Existing executable components

| Layer | Owner / entry point | Responsibility |
|---|---|---|
| Request/canonical catalogue | `manifest.json`, `vf/manifest.json`, `scripts/native_manifest_projection.py` | Exact current enabled provider and four manifest variants |
| Targeted emulator trigger | `.github/triggers/native-residential-transport-targeted.json` | TV first; provider/fixture/exit policy; versioned on `main` |
| Device CI | `.github/workflows/native-corpus-device-targeted.yml` | Android TV API 31, x86, 1080p, official NuvioTV accepted SHA from `sources.json` |
| Client/harness | `scripts/run_native_corpus_tv_suite.sh`, `scripts/augment_native_provider_loading.py`, `scripts/augment_native_corpus_request_contract.py` | Real local enabled state + type selection, positional QuickJS, network, player, screenshots |
| Sanitized diagnostics | `engine_v2/scripts/diagnose-native-reader.mjs` | App selection, QuickJS call/result/error, result count, terminal player; no raw signed stream URLs |
| Native feedback | `.github/workflows/brain-android-tv-emulator-feedback.yml` | On native run completion, download sanitized TV reports and retain source-pinned observations |
| Experience store | `scripts/ingest_brain_android_tv_emulator.py`, `automation/brain-android-tv-emulator-history.json` | Max 10 observations/provider, SHA-256 exact JS, source commit/run ID, no authority to publish or mutate |
| Brain handoff | `brain/scripts/route_android_tv_emulator_feedback.py` (checked out from `niakw/NiakVIO-Brain-LLM`) | Read-only, exact-native-run bounded next-action plan, downloadable in TV feedback workflow |
| Brain decisions | `niakvio_adapter.py`, `routing.py` in Brain-LLM | Prefer client/Core or provider diagnosis based on evidence; never assume transport is correct media |

The four user-facing manifests **must not be merged**: Global, VF, Global no-anime, VF no-anime. A disabled/no-anime-excluded provider remains absent when the client installed that variant. A VF-only provider must not be injected into Global to mask an installation mismatch. The script `native_manifest_projection.py` selects the published Global/VF transport, not the two retired hub46 manifests.

## Closed-loop process

1. **Cheapest evidence first:** select existing positive media/short route candidate, current JS bytes, known failure family and latest observations. Do not boot Android for every trivial static question.
2. **Official TV first:** pin NiakVIO HEAD, NuvioTV accepted SHA, manifest, provider, fixture and exit mode; install the exact published JS and execute the same app-visible enabled/type selection as NuvioTV.
3. **Distinguish stages:** manifest installed → plugin enabled/selected → type matched → getStreams entered → QuickJS response/error → fetch/HTTP/WAF → media terminal → decoded player → correct title/season/episode → audio tracks, quality, headers, badges and UI.
4. **Retain sanitized evidence:** run completion triggers official TV feedback. Only whitelisted codes/counts are persisted, with current JS SHA-256 and original GitHub run/source ID. Diagnostic completeness is **not decoded playback**. A QuickJS `call` alone is **not** a returned-zero event; native extraction result `count=0` is a separate observation.
5. **Brain causal decision:** the feedback workflow checks out the current Brain and routes only observations matching the exact source/run through `route_android_tv_emulator_feedback.py`. A `probe` means gather a discriminating fact; `llm_diagnose` means reasoning is warranted. Neither grants provider/manifest mutation authority.
6. **Correction by owner:** identify client/QuickJS/Core, Brain orchestration, provider extraction, harness, network/WAF or environment. Fix Brain infrastructure/prompt/Lego/compilation/materialization when Brain is incapable; use provider mutation only after it has actually identified a provider-owned cause. Historical successful patterns are hypotheses until replayed on current bytes.
7. **Apply → rematerialize → replay TV:** compare exact executed bytes before/after, require correct work/episode in a decoded terminal player, preserve HLS audio languages/headers, and check non-regression. Only then run bounded Desktop/Mobile/iOS compatibility gates for affected shared components and persist the winning/failing experience.
8. **Publication gate:** successful CI, a valid URL, the presence of a QuickJS call, and even a `playing` state alone are insufficient for FULL. The same correct content, full terminal duration, language/audio and actual media proof must be established. No staged provider may overwrite the four prod manifests merely because an emulator could start.

## Diagnostic classification

| Observation | Initial owner / Brain action |
|---|---|
| Missing from installed manifest, or intentionally excluded in no-anime | User's chosen projection / installation; **not** provider failure |
| Manifest present but locally disabled or globally switched off | Client state; respect user choice, do not force enable |
| App selected but QuickJS `call` lacks any response/result/error and no independent result record | Harness/runtime visibility gap; capture missing terminal event |
| App selected, independent native `count=0`, Desktop user reports playing | Runtime/input/network/Core vs provider discrepancy; **causal diagnosis**, no manual JS patch |
| HTTP WAF/403 or DNS failures | Environment/network; compare runner vs residential exit and official client; do not mark provider unrepairable |
| 1+ streams returned, but wrong episode or unknown HLS duration | Source identity/validation; preserve fail-closed proof gate |
| Correct media/episode, decoded playback, missing FR/multiaudio | Core/client player projection and source HLS audio tracks; preserve native tracks |
| TV correct, other client regresses | Existing platform adapters / shared Core; selective regression, not divergent provider forks |

## Initial reproduction and limits

- Field report: French-Manga played one stream with FR audio on Desktop macOS; absent from Android TV stream list. Sadisflix not seen (installed manifest/fixture/client not yet known); VF-only by design.
- [TV run 44514660418](https://github.com/niakw/NiakVIO/actions/runs/44514660418): official NuvioTV downloaded an enabled French-Manga JS and returned zero streams for Jujutsu Kaisen S01E01; no player proof.
- [TV run 44520778916](https://github.com/niakw/NiakVIO/actions/runs/44520778916): source-pinned app-selection gate eligible=true, native extraction 0, QuickJS `call` observed, no player. The Brain evidence ingest completed in [feedback 44525039332](https://github.com/niakw/NiakVIO/actions/runs/44525039332); the historical exact-JS receipt is persisted.
- This does **not** establish which QuickJS capability, network route or content-identity step caused zero. The next targeted diagnosis must capture the actual runtime terminal event and compare source inputs to Desktop.
- The automatic Brain *routing* handoff has been implemented after that receipt. It is not a model-executed repair, and must be revalidated in a new native/feedback run before claiming an autonomous repair loop.

## Cost and acceptance strategy

The emulator is expensive (Gradle and Android system image). Reuse AVD/Gradle caches, use one representative provider + fixture per failure family, and only repeat on a changed hypothesis or executed bytes. Test Android TV **first** for functionality; retain existing cross-client Lego and run them as targeted regressions. For a complete family fix, require at least one end-to-end Brain-produced repair and one separate representative regression, never a fixture-specific exception.

**Memory:** persist stage signatures, exact JS hash, tested source SHA, native run, hypotheses attempted, causes, rejection, winning Lego, and replay result in `MEMORY.md`, the Brain's experience store, and architecture documentation. Never persist signed media URLs, cookies, authorization headers or private client data.
