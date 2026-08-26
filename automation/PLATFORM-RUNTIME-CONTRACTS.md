# Contrat runtime Nuvio — comparaison par device

> Généré depuis `automation/platform-runtime-contracts.json` par `scripts/render_platform_runtime_contracts.py`. Ne pas éditer la matrice à la main.

Dernier audit du contrat : **2026-08-26**.

**Lecture rapide :** 🟢 identique sur tous les clients · 🟠 implémentation/sémantique différente · 🔴 capacité absente, incompatible ou à ré-auditer sur au moins un client.

## Matrice des capacités

| Capacité | Écart | Android | iOS | macOS | Windows | Linux | Android TV |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Runtime JS | 🟢 **Identique** | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS |
| Signature getStreams | 🟢 **Identique** | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) |
| SCRAPER_ID | 🟢 **Identique** | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected |
| SCRAPER_SETTINGS | 🟢 **Identique** | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected |
| TMDB_API_KEY | 🔴 **Écart de capacité** — absent | **absent** — no TMDB_API_KEY runtime global | **absent** — no TMDB_API_KEY runtime global | **absent** — no TMDB_API_KEY runtime global | **absent** — no TMDB_API_KEY runtime global | **absent** — no TMDB_API_KEY runtime global | **native** — TMDB_API_KEY injected from BuildConfig |
| fetch / bridge natif | 🟠 **Différence** | **bridge** — synchronous __native_fetch → OkHttp | **bridge** — synchronous __native_fetch → Ktor Darwin | **bridge** — async __native_fetch → OkHttp | **bridge** — async __native_fetch → OkHttp | **bridge** — async __native_fetch → OkHttp | **bridge** — blocking native fetch behind async JS fetch → OkHttp |
| Pile HTTP | 🟠 **Différence** | **native** — OkHttp | **native** — Ktor Darwin | **native** — OkHttp | **native** — OkHttp | **native** — OkHttp | **native** — OkHttp |
| Politique proxy | 🟠 **Différence** | **native** — Proxy.NO_PROXY | **native** — Darwin/platform default | **native** — JVM/system default; no NO_PROXY override | **native** — JVM/system default; no NO_PROXY override | **native** — JVM/system default; no NO_PROXY override | **native** — Proxy.NO_PROXY |
| DNS | 🟠 **Différence** | **native** — IPv4FirstDns | **native** — Darwin/platform default | **native** — IPv4FirstDns | **native** — IPv4FirstDns | **native** — IPv4FirstDns | **native** — IPv4FirstDns |
| Redirections | 🟠 **Différence** | **native** — HTTP + SSL redirects enabled | **native** — Ktor Darwin engine policy | **native** — HTTP + SSL redirects enabled | **native** — HTTP + SSL redirects enabled | **native** — HTTP + SSL redirects enabled | **native** — HTTP + SSL redirects enabled |
| Timeouts | 🟠 **Différence** | **native** — 60s HTTP; 60s plugin runtime | **native** — 60s request/connect/socket; 60s plugin runtime | **native** — 60s HTTP; 60s plugin runtime | **native** — 60s HTTP; 60s plugin runtime | **native** — 60s HTTP; 60s plugin runtime | **native** — 30s HTTP; 60s plugin runtime; 120s outer scraper safety net |
| AbortController | 🟠 **Différence** | **polyfill** — AbortController / AbortSignal | **polyfill** — AbortController / AbortSignal | **polyfill** — AbortController / AbortSignal | **polyfill** — AbortController / AbortSignal | **polyfill** — AbortController / AbortSignal | **polyfill** — AbortController / AbortSignal; pre/post checks + coroutine cancellation of in-flight calls |
| URL / URLSearchParams | 🟢 **Identique** | **polyfill** — URL + URLSearchParams over native URL parser | **polyfill** — URL + URLSearchParams over native URL parser | **polyfill** — URL + URLSearchParams over native URL parser | **polyfill** — URL + URLSearchParams over native URL parser | **polyfill** — URL + URLSearchParams over native URL parser | **polyfill** — URL + URLSearchParams over native URL parser |
| atob / btoa | 🟢 **Identique** | **polyfill** — atob + btoa | **polyfill** — atob + btoa | **polyfill** — atob + btoa | **polyfill** — atob + btoa | **polyfill** — atob + btoa | **polyfill** — atob + btoa |
| TextEncoder / TextDecoder | 🔴 **Écart de capacité** — absent | **polyfill** — TextEncoder + TextDecoder | **polyfill** — TextEncoder + TextDecoder | **polyfill** — TextEncoder + TextDecoder | **polyfill** — TextEncoder + TextDecoder | **polyfill** — TextEncoder + TextDecoder | **absent** — TextEncoder / TextDecoder not exposed by current PluginRuntime |
| Cheerio / DOM | 🟠 **Différence** | **bridge** — Cheerio-compatible API over native parser | **bridge** — Cheerio-compatible API over native parser | **bridge** — Cheerio-compatible API over native parser | **bridge** — Cheerio-compatible API over native parser | **bridge** — Cheerio-compatible API over native parser | **bridge** — Cheerio-compatible API over Jsoup |
| require / CommonJS | 🟢 **Identique** | **polyfill** — require() / CommonJS compatibility | **polyfill** — require() / CommonJS compatibility | **polyfill** — require() / CommonJS compatibility | **polyfill** — require() / CommonJS compatibility | **polyfill** — require() / CommonJS compatibility | **polyfill** — require() / CommonJS compatibility |
| CryptoJS / crypto | 🟠 **Différence** | **bridge** — CryptoJS compatibility | **bridge** — CryptoJS compatibility | **bridge** — CryptoJS compatibility | **bridge** — CryptoJS compatibility | **bridge** — CryptoJS compatibility | **bridge** — CryptoJS source/bytecode bundle |
| WebAssembly | 🔴 **Écart de capacité** — absent | **bridge** — WebAssembly compatibility bridge | **bridge** — WebAssembly compatibility bridge | **bridge** — WebAssembly compatibility bridge | **bridge** — WebAssembly compatibility bridge | **bridge** — WebAssembly compatibility bridge | **absent** — no WebAssembly bridge in current PluginRuntime |
| Exception getStreams → [] | 🟢 **Identique** | **native** — getStreams failures are caught and surfaced as [] | **native** — getStreams failures are caught and surfaced as [] | **native** — getStreams failures are caught and surfaced as [] | **native** — getStreams failures are caught and surfaced as [] | **native** — getStreams failures are caught and surfaced as [] | **native** — getStreams failures are caught and surfaced as [] |
| Headers stream | 🟠 **Différence** | **native** — PluginRuntimeResult.headers retained | **native** — PluginRuntimeResult.headers retained | **native** — PluginRuntimeResult.headers retained | **native** — PluginRuntimeResult.headers retained | **native** — PluginRuntimeResult.headers retained | **native** — LocalScraperResult.headers retained |
| Sous-titres stream | 🔴 **Écart de capacité** — absent | **native** — PluginRuntimeResult.subtitles retained | **native** — PluginRuntimeResult.subtitles retained | **native** — PluginRuntimeResult.subtitles retained | **native** — PluginRuntimeResult.subtitles retained | **native** — PluginRuntimeResult.subtitles retained | **absent** — LocalScraperResult has no subtitles field |
| seeders / peers / infoHash | 🟢 **Identique** | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained |
| Projection behaviorHints / proxyHeaders | 🔴 **Écart de capacité** — absent | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **bridge** — headers → behaviorHints.proxyHeaders.request; local-plugin bingeGroup |

## Révisions auditées

| Device | Dépôt / branche | Révision auditée | État | Transport runtime |
| --- | --- | --- | --- | --- |
| Android | `NuvioMedia/NuvioMobile` / `cmp-rewrite` | `4e838e470055d61facab285d283d7ec8f00c0347` | **audited** | `composeApp/src/androidMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.android.kt` |
| iOS | `NuvioMedia/NuvioMobile` / `cmp-rewrite` | `4e838e470055d61facab285d283d7ec8f00c0347` | **audited** | `composeApp/src/iosMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.ios.kt` |
| macOS | `NuvioMedia/NuvioDesktop` / `Dev` | `a4fe0bf1a98ff9a8ca50e1a9dccde7ca842bd817` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Windows | `NuvioMedia/NuvioDesktop` / `Dev` | `a4fe0bf1a98ff9a8ca50e1a9dccde7ca842bd817` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Linux | `NuvioMedia/NuvioDesktop` / `Dev` | `a4fe0bf1a98ff9a8ca50e1a9dccde7ca842bd817` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Android TV | `NuvioMedia/NuvioTV` / `dev` | `0d8f99e2b92be5e2dedbbd0eaf9ccd00c78d020a` | **audited** | `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt` |

## Lecture des états

- **native** : comportement fourni directement par le client ou son modèle natif.
- **bridge** : capacité exposée à JavaScript par un pont natif.
- **polyfill** : compatibilité fournie en JavaScript au-dessus du runtime.
- **shim** : adaptation NiakVIO explicitement nécessaire pour harmoniser les clients.
- **absent** : capacité absente du contrat actuel du client.
- **incompatible** : capacité présente mais avec une sémantique incompatible entre clients.
- **audit-required** : le code upstream a changé et la valeur ne doit pas être considérée comme validée avant ré-audit.
- **n/a** : capacité sans objet pour ce client.

## Différences qui comptent pour NiakVIO

- **Android et Android TV forcent `Proxy.NO_PROXY`; Desktop ne le force pas.** C'est une différence de transport silencieuse : un provider peut attraper une erreur réseau et retourner `[]` sans exception JavaScript visible.
- **Desktop utilise un bridge `__native_fetch` asynchrone**, alors que Mobile et TV appellent leur pont natif de manière bloquante derrière l'API JavaScript `fetch`.
- **iOS utilise Ktor/Darwin**, contrairement à l'OkHttp d'Android, Desktop et TV. Les comportements réseau propres à la plateforme doivent donc rester audités séparément.
- **TV injecte `TMDB_API_KEY` dans le runtime plugin; Mobile/Desktop ne l'exposent pas comme global runtime.** Un provider portable ne doit pas dépendre de ce global sans fallback.
- **Mobile/Desktop conservent `subtitles`; TV ne possède pas ce champ dans `LocalScraperResult`.** Les sous-titres retournés uniquement par un provider JS ne sont donc pas projetables de manière identique sur TV aujourd'hui.
- **TV projette les headers dans `behaviorHints.proxyHeaders.request`** et ajoute son `bingeGroup`; Mobile/Desktop conservent d'abord les headers bruts dans `PluginRuntimeResult`.
- **TV n'expose actuellement ni TextEncoder/TextDecoder ni WebAssembly dans son PluginRuntime**, contrairement au runtime Mobile/Desktop. Un provider qui en dépend doit être adapté ou déclaré incompatible TV.

## Contrat vivant / drift upstream

Le registre `automation/nuvio-client-upstreams.json` et le checker `scripts/check_nuvio_client_upstreams.py` surveillent les HEAD officiels Mobile, Desktop et TV. Les chemins runtime, modèles de résultat, repository et transport font partie du périmètre sensible.

Règle : **un HEAD ne doit pas être avancé comme contrat audité lorsqu'un de ces chemins ou une sémantique sensible a changé sans ré-audit**. Après audit, `source_ref`, le registre upstream et cette matrice doivent pointer vers la même révision officielle.

Le check CI `python3 scripts/render_platform_runtime_contracts.py --check` garantit que ce README reste exactement synchronisé avec le JSON machine-readable.

## Sources canoniques par client

### Android

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/androidMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.android.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Runtime audited at current cmp-rewrite HEAD. The only commit after the detailed 071fc431 runtime read changes Android release workflow only.

### iOS

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/iosMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.ios.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Runtime audited at current cmp-rewrite HEAD; Darwin transport differs materially from Android OkHttp.

### macOS

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Runtime audited at current Dev HEAD. Desktop shares the Mobile runtime family but its native fetch bridge is async and its OkHttp client does not force NO_PROXY.

### Windows

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Runtime audited at current Dev HEAD. Desktop shares the Mobile runtime family but its native fetch bridge is async and its OkHttp client does not force NO_PROXY.

### Linux

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Runtime audited at current Dev HEAD. Desktop shares the Mobile runtime family but its native fetch bridge is async and its OkHttp client does not force NO_PROXY.

### Android TV

- Runtime : `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt`
- Repository : `app/src/full/java/com/nuvio/tv/core/plugin/PluginManager.kt`
- Transport : `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt`
- Modèle de résultat : `app/src/main/java/com/nuvio/tv/domain/model/Plugin.kt`
- Note d'audit : Runtime audited at current dev HEAD. PluginRuntime itself is unchanged since the previous audited ref; PluginManager changes bound scraper orchestration and avoid duplicate repository writes without changing the positional extraction contract.
