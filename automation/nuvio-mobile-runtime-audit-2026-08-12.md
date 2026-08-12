# Nuvio Mobile runtime audit — 2026-08-12

Audited upstream: `NuvioMedia/NuvioMobile` branch `cmp-rewrite`.

Previous accepted ref: `f9ad843b14cd3be7fa3ddb800b6961233e0e5b56`.
Audited upstream head: `0d6e30e4566e6f9f2051d5f80a1e3f1e0fcb1f18`.

The upstream advance contains five commits. No production plugin runtime, plugin platform, plugin repository, positional `getStreams` invocation, provider payload schema, stream parser contract, URL construction contract, proxy/header ingestion contract, or QuickJS contract changed.

The hard-path change in `composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamsRepository.kt` replaces `httpGetText(url)` with `fetchAddonResponseText(url, forceRefresh)`. Normal requests still call `httpGetText(url)`. Forced refresh requests call the existing header-aware transport with only `Cache-Control: no-cache`. `buildAddonResourceUrl`, provider request arguments, and `StreamParser.parse` are unchanged.

`PlayerStreamsRepository.kt` receives the same transport-only refresh behavior. Other player-path changes in this upstream range concern settings/subtitles/UI and do not touch the runtime-sensitive semantic tokens used by Niakvio's drift guard.

Conclusion: the provider/runtime contract remains compatible. The audited mobile contract may be repinned to `0d6e30e4566e6f9f2051d5f80a1e3f1e0fcb1f18` for Android and iOS.
