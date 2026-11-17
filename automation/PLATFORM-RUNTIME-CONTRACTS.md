# Contrat runtime Nuvio — comparaison par device

> Généré depuis `automation/platform-runtime-contracts.json` par `scripts/render_platform_runtime_contracts.py`. Ne pas éditer la matrice à la main.

Dernier audit du contrat : **2026-11-17**.

**Lecture rapide :** 🟢 identique sur tous les clients · 🟠 implémentation/sémantique différente · 🔴 capacité absente, incompatible ou à ré-auditer sur au moins un client.

## Matrice des capacités

| Capacité | Écart | Android | iOS | macOS | Windows | Linux | Android TV |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Runtime JS | 🟢 **Identique** | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS | **native** — QuickJS |
| Signature getStreams | 🟢 **Identique** | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) | **native** — getStreams(tmdbId, mediaType, season, episode) |
| SCRAPER_ID | 🟢 **Identique** | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected | **native** — SCRAPER_ID injected |
| SCRAPER_SETTINGS | 🟢 **Identique** | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected | **native** — SCRAPER_SETTINGS injected |
| TMDB_API_KEY | 🟠 **Différence** | **bridge** — HostFunctions __get_tmdb_api_key → TmdbSettingsRepository.effectiveApiKey(); JsBindings assigns globalThis.TMDB_API_KEY with build TmdbConfig fallback | **bridge** — HostFunctions __get_tmdb_api_key → TmdbSettingsRepository.effectiveApiKey(); JsBindings assigns globalThis.TMDB_API_KEY with build TmdbConfig fallback | **bridge** — HostFunctions __get_tmdb_api_key → TmdbSettingsRepository.effectiveApiKey(); JsBindings assigns globalThis.TMDB_API_KEY with build TmdbConfig fallback | **bridge** — HostFunctions __get_tmdb_api_key → TmdbSettingsRepository.effectiveApiKey(); JsBindings assigns globalThis.TMDB_API_KEY with build TmdbConfig fallback | **bridge** — HostFunctions __get_tmdb_api_key → TmdbSettingsRepository.effectiveApiKey(); JsBindings assigns globalThis.TMDB_API_KEY with build TmdbConfig fallback | **native** — TMDB_API_KEY injected from BuildConfig |
| Hydratation identité TMDB ↔ IMDb | 🟠 **Différence** | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited runtime TMDB_API_KEY bridge; no key is embedded in published provider bytes and no end-user key is required when the build fallback is configured. | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited runtime TMDB_API_KEY bridge; no key is embedded in published provider bytes and no end-user key is required when the build fallback is configured. | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited runtime TMDB_API_KEY bridge; no key is embedded in published provider bytes and no end-user key is required when the build fallback is configured. | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited runtime TMDB_API_KEY bridge; no key is embedded in published provider bytes and no end-user key is required when the build fallback is configured. | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited runtime TMDB_API_KEY bridge; no key is embedded in published provider bytes and no end-user key is required when the build fallback is configured. | **bridge** — NiakVIO Core can hydrate its canonical __nuvioTmdbMetadataCacheV1 from the audited TV runtime TMDB_API_KEY; no key is embedded in published provider bytes. |
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
| Sous-titres stream | 🟠 **Différence** | **native** — PluginRuntimeResult.subtitles retained, including subtitle-specific headers | **native** — PluginRuntimeResult.subtitles retained, including subtitle-specific headers | **native** — PluginRuntimeResult.subtitles retained, including subtitle-specific headers | **native** — PluginRuntimeResult.subtitles retained, including subtitle-specific headers | **native** — PluginRuntimeResult.subtitles retained, including subtitle-specific headers | **native** — LocalScraperResult.subtitles retained and projected to Stream.subtitles, including subtitle-specific headers |
| seeders / peers / infoHash | 🟢 **Identique** | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained | **native** — seeders / peers / infoHash retained |
| Projection badges du flux | 🟠 **Différence** | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeMatcher re-derives badges by regex over StreamItem name/title/description and parsed fields | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeMatcher re-derives badges by regex over StreamItem name/title/description and parsed fields | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeMatcher re-derives badges by regex over StreamItem name/title/description and parsed fields | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeMatcher re-derives badges by regex over StreamItem name/title/description and parsed fields | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeMatcher re-derives badges by regex over StreamItem name/title/description and parsed fields | **shim** — badgeIds/displayBadges are not parsed from provider JSON; StreamBadgeRules re-derives badges by regex over Stream name/title/description and parsed fields |
| Projection description du flux | 🟠 **Différence** | **shim** — PluginRuntimeResult has no description field; StreamItem.description is rebuilt from quality + size + language, so NiakVIO tunnels full technical description through size | **shim** — PluginRuntimeResult has no description field; StreamItem.description is rebuilt from quality + size + language, so NiakVIO tunnels full technical description through size | **shim** — PluginRuntimeResult has no description field; StreamItem.description is rebuilt from quality + size + language, so NiakVIO tunnels full technical description through size | **shim** — PluginRuntimeResult has no description field; StreamItem.description is rebuilt from quality + size + language, so NiakVIO tunnels full technical description through size | **shim** — PluginRuntimeResult has no description field; StreamItem.description is rebuilt from quality + size + language, so NiakVIO tunnels full technical description through size | **shim** — LocalScraperResult has no description field; Stream.description is projected from LocalScraperResult.size, so NiakVIO tunnels full technical description through size |
| Projection titre / nom du flux | 🟠 **Différence** | **shim** — PluginRuntimeResult.title is parsed, but plugin StreamItem uses name ?: title; NiakVIO mirrors branded Provider - Quality into name and title | **shim** — PluginRuntimeResult.title is parsed, but plugin StreamItem uses name ?: title; NiakVIO mirrors branded Provider - Quality into name and title | **shim** — PluginRuntimeResult.title is parsed, but plugin StreamItem uses name ?: title; NiakVIO mirrors branded Provider - Quality into name and title | **shim** — PluginRuntimeResult.title is parsed, but plugin StreamItem uses name ?: title; NiakVIO mirrors branded Provider - Quality into name and title | **shim** — PluginRuntimeResult.title is parsed, but plugin StreamItem uses name ?: title; NiakVIO mirrors branded Provider - Quality into name and title | **native** — LocalScraperResult title/name/quality are retained; toStream keeps title/name and appends quality when not already present |
| Projection behaviorHints / proxyHeaders | 🔴 **Écart de capacité** — absent | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **absent** — runtime result keeps raw headers; behaviorHints is downstream | **bridge** — main stream headers → behaviorHints.proxyHeaders.request; local-plugin bingeGroup; subtitle headers remain attached to each subtitle |

## Contrat canonique d'identité média

Le paramètre positionnel `tmdbId` de `getStreams(tmdbId, mediaType, season, episode)` est un **transport d'identifiant**, pas l'identité média complète.

- Chemin IMDb canonique du contexte : `__nuvioMediaContext.tmdbMetadata.external_ids.imdb_id`.
- Cache metadata partagé canonique : `__nuvioTmdbMetadataCacheV1` avec entrée `{state:"ok",metadata:{external_ids:{imdb_id:"tt..."}}}`.
- Timing d'un bridge host : after provider/Core bundle initialization and before getStreams invocation when supplied by the host.
- Une clé/credential TMDB fournie par l'utilisateur n'est **jamais** une précondition de compatibilité NiakVIO.
- Un secret TMDB ne doit jamais être embarqué dans les octets publiés du provider uniquement pour reconstruire l'identité IMDb ; une capacité runtime officielle reste distincte du code provider.
- Un client peut fournir une capacité équivalente d'hydratation, mais la disponibilité d'un seul TMDB ID ne permet jamais de conclure que l'identité dual-ID est disponible.

## ABI portable de sortie provider

Champs consommables sur toutes les familles Nuvio officielles : `title`, `name`, `url`, `quality`, `size`, `language`, `provider`, `type`, `seeders`, `peers`, `infoHash`, `headers`, `subtitles`.

Critical provider identity, quality, language, request-header and subtitle facts must survive through fields parsed by every official Nuvio runtime. Rich NiakVIO-only fields such as badgeIds/displayBadges/presentationFacts may remain additive only; they cannot be the sole carrier of a user-visible or playback-critical fact. Technical description is mirrored through size and branded label through both name and title.

## Révisions auditées

| Device | Dépôt / branche | Révision auditée | État | Transport runtime |
| --- | --- | --- | --- | --- |
| Android | `NuvioMedia/NuvioMobile` / `cmp-rewrite` | `dd0e84704df5e4d746e28b9d6556305332ff3483` | **audited** | `composeApp/src/androidMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.android.kt` |
| iOS | `NuvioMedia/NuvioMobile` / `cmp-rewrite` | `dd0e84704df5e4d746e28b9d6556305332ff3483` | **audited** | `composeApp/src/iosMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.ios.kt` |
| macOS | `NuvioMedia/NuvioDesktop` / `Dev` | `3020193d8303c38ce88381f0a2a613b389219e62` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Windows | `NuvioMedia/NuvioDesktop` / `Dev` | `3020193d8303c38ce88381f0a2a613b389219e62` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Linux | `NuvioMedia/NuvioDesktop` / `Dev` | `3020193d8303c38ce88381f0a2a613b389219e62` | **audited** | `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt` |
| Android TV | `NuvioMedia/NuvioTV` / `dev` | `fc5c10c3d2d5def54bb21e452291cb7b281b07b3` | **audited** | `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt` |

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
- **Les trois familles officielles exposent désormais une capacité runtime `TMDB_API_KEY`.** TV l'injecte depuis BuildConfig ; Mobile/Desktop passent par `__get_tmdb_api_key` → `TmdbSettingsRepository.effectiveApiKey()` avec fallback build. NiakVIO Core peut l'utiliser pour hydrater son cache TMDB/IMDb, mais les providers partagés ne doivent jamais embarquer ni exiger directement une credential.
- **Le cache `__nuvioTmdbMetadataCacheV1` est initialisé par Core pendant l'évaluation du bundle et `__nuvioMediaContext` est réécrit pendant la résolution.** L'hydratation courante doit donc se faire dans cette frontière Core à partir d'une capacité runtime auditée (ou d'un contexte host canonique futur), avant que le provider consomme l'identité.
- **Les six clients conservent désormais les sous-titres retournés par le provider.** TV a ajouté `LocalScraperResult.subtitles` depuis l'audit précédent.
- **Mobile/Desktop ne conservent pas `description` depuis le JSON provider** : leur `StreamItem.description` est reconstruit depuis `quality + size + language`. TV projette également `Stream.description` depuis `LocalScraperResult.size`. NiakVIO utilise donc `size` comme tunnel de description technique complète.
- **Mobile/Desktop privilégient `name` à `title` pour le label plugin.** NiakVIO doit donc écrire `Provider - Qualité` dans les deux champs ; TV conserve les deux et évite de dupliquer la qualité lorsqu'elle est déjà présente.
- **Aucun client ne consomme directement `badgeIds` / `displayBadges` depuis le JSON provider.** Les moteurs de badges Mobile/Desktop/TV re-matchent des règles regex sur les champs textuels du stream (`name`, `title`, `description`, champs parsés). Les tokens techniques doivent donc survivre dans le label/description projetés.
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
- Note d'audit : Exact current-source re-audit at NuvioMobile fc05fe8e516a. Provider/runtime bridge paths remain byte-identical to the prior audit and preserve positional getStreams, full result-list mapping, stream/subtitle headers and the TMDB_API_KEY bridge. The only new Mobile diff is Android MPV player integration/dependency code.

### iOS

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/iosMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.ios.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : Exact current-source re-audit at NuvioMobile fc05fe8e516a. Provider/runtime bridge paths remain byte-identical to the prior audit and preserve positional getStreams, full result-list mapping, stream/subtitle headers and the TMDB_API_KEY bridge. The only new Mobile diff is Android MPV player integration/dependency code.

### macOS

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : 2026-11-17: exact current-source audit at Dev 3020193d8303. Since 8e779958a5f4, upstream changed only DesktopVersion.properties (0.1.37-alpha / 37) and DesktopDetailHero UI. No configured provider/plugin/streams contract path or player semantic-review path changed; positional getStreams, full result-list mapping, request/response headers, subtitles and the runtime TMDB_API_KEY bridge remain intact. macOS/Windows reader execution remains independently required.

### Windows

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : 2026-11-17: exact current-source audit at Dev 3020193d8303. Since 8e779958a5f4, upstream changed only DesktopVersion.properties (0.1.37-alpha / 37) and DesktopDetailHero UI. No configured provider/plugin/streams contract path or player semantic-review path changed; positional getStreams, full result-list mapping, request/response headers, subtitles and the runtime TMDB_API_KEY bridge remain intact. macOS/Windows reader execution remains independently required.

### Linux

- Runtime : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt`
- Repository : `composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/PluginRepository.kt`
- Transport : `composeApp/src/desktopMain/kotlin/com/nuvio/app/features/addons/AddonPlatform.desktop.kt`
- Modèle de résultat : `composeApp/src/commonMain/kotlin/com/nuvio/app/features/plugins/PluginModels.kt`
- Note d'audit : 2026-11-17: exact current-source audit at Dev 3020193d8303. Since 8e779958a5f4, upstream changed only DesktopVersion.properties (0.1.37-alpha / 37) and DesktopDetailHero UI. No configured provider/plugin/streams contract path or player semantic-review path changed; positional getStreams, full result-list mapping, request/response headers, subtitles and the runtime TMDB_API_KEY bridge remain intact. macOS/Windows reader execution remains independently required.

### Android TV

- Runtime : `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt`
- Repository : `app/src/full/java/com/nuvio/tv/core/plugin/PluginManager.kt`
- Transport : `app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt`
- Modèle de résultat : `app/src/main/java/com/nuvio/tv/domain/model/Plugin.kt`
- Note d'audit : Exact current-source re-audit at NuvioTV 2c853c178674. Positional getStreams, BuildConfig TMDB_API_KEY injection, stream/subtitle header preservation and the QuickJS runtime contract remain unchanged. The new TV commits only adjust episode-ratings alignment and bump the app to 1.2.0-beta.2; provider/plugin/runtime transport paths are unchanged.

## Évidence croisée Native + tests utilisateur

Évidence datée **2026-09-16**, NiakVIO SHA `6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1`.

| Device | Extraction provider | Player | UX / transport | Classification |
| --- | --- | --- | --- | --- |
| Android TV | User TV: Interstellar Purstream/Papadustream/Castle/StreamZo/Kehflix; HOTD S1E2 Purstream/StreamZo/Castle/VidRock/HindMoviez; Hell Mode S2E12 French-Manga/VoirAnime.homes. | User-visible streams exist; provider/player verdict must remain per-row. | Common TV defects: non-uniform title, duplicated/conflicting quality, Inconnue placeholder, language/badge mismatch, late rows without badges, no visible 4K provider. | real product UX + provider coverage work; runner red does not cancel user positives |
| Android Mobile | 2073 results; VidRock count>0 on movie + TV. | 2/2 extracted VidRock rows fail only at Activity launch: Unable to resolve cmp=com.nuvio.app/.MainActivity. | Launcher diagnostic must resolve installed applicationId independently from Kotlin namespace. | Lab launcher false red after positive extraction |
| iOS | 3299 results; 89 count>0 (VidRock 58, VoirAnime 31). | 89/89 production-player probes ready; exhaustive Hub-46 gate success. | Ktor/Darwin path is a positive control against simultaneous provider-bundle failure. | native green positive control |
| macOS | Artifact: HindMoviez movie count=4; VidRock movie=1 + TV=1. User UI: VidRock visible on Interstellar/HOTD, Hell Mode zero. | Artifact 6/6 mpv_create_failed; user log player attach -> mpv_create failed and visible VidRock does not launch. | User work-change test resets streams correctly. Logs separately show WookaFR DNS failure and MovieBox/Workers.dev timeouts. | positive extraction + real macOS player/client blocker; no evidence of current stale reset bug on macOS |
| Windows | 2116 results; HindMoviez + VidRock positive on movie and TV (4 positive result rows / 10 streams). | 9 ready / 1 timeout. | Exhaustive matrix red must not be reported as Desktop-wide zero. | native positives; matrix coverage red |

### Règles anti-régression / anti-faux-diagnostic

- Provider extraction, client projection and player readiness are independent verdicts; a player failure never erases a positive provider extraction.
- A red exhaustive matrix is not a provider-wide failure when the same platform artifact contains count>0 rows.
- TV late-result/stale symptoms must not be generalized to Desktop: the 2026-09-16 macOS user test observed correct reset after changing work.
- Quality shown to the client must be the final post-sanitizer quality; source/declaration quality cannot remain in title when media proof changes it.
- Language/badges require stream-level evidence. Provider catalogue language is a capability hint, not proof that a returned media track is French/VO/VF.
