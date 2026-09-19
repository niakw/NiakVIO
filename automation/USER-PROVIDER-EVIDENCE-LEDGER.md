# User Provider Evidence Ledger

> Durable NiakVIO ledger for provider evidence supplied manually by the user across earlier chats/files.  
> Historical URLs/routes are **evidence**, not automatic current-domain authority. Domain Refresh and current live proof remain authoritative for current terminals.

## Evidence block A — live TV/Desktop behavior (September 2026)

Purpose: preserve real client behavior that the synthetic census can miss.

Representative field cases:
- **Interstellar**: Purstream, Papadustream, Castle, DesiFlix, StreamZo, VidRock, HindMoviez; issues included wrong-content StreamZo, dead/403 VidRock row, low/incorrect displayed quality, language/badge inconsistencies.
- **House of the Dragon**: Purstream, StreamZo, Castle, VidRock, HindMoviez and other mixed-language providers; exact season/episode identity matters.
- **Ragna Crimson / Mushoku Tensei / Hell Mode**: Anime-Sama and Mugiwara episode/season identity; wrong-season/wrong-episode fallback must fail closed.
- Global field invariants: provider generations must not accumulate across navigation; stale late results must not reappear; detailed languages/dialects must survive normalization; displayed quality should follow verified media when possible.

This block is client evidence. A browser/player positive does not by itself make a provider FULL; terminal playable + identity proof is still required.

## Evidence block B — browser route/hub captures (11–15 September 2026)

Large route-capture corpus supplied manually by the user. Key provider-local chains recovered from it include:

- **AnimeSalt**: current historical capture used `animesalt.cx`; search via `/wp-admin/admin-ajax.php` with `action_tr_search_suggest`; series pages expose exact `/episode/<title>-SxE/`; player POST to `as-cdn*.top/player/index.php?...&do=getVideo`.
- **Vostfree**: DLE POST search at `/index.php?do=search`; detail pages expose episode player blocks; observed terminal player family included Sibnet/Uqload.
- **NetMirror**: `/api/catalog/search-hybrid?q=...` -> `/api/catalog/title/tv/<tmdb>` -> `/api/embed-tmdb/<tmdb>?type=tv&se=<S>&ep=<E>...`.
- **Nakios**: Livewire search via `/livewire/update`; browser-observed Vidzy terminal media.
- **UHDMovies**: search path `/search/<query>`; title page groups seasons/releases and exposes per-episode cloud gateway links.
- **ToFlix**: POST `/toflix_api.php` with `content_details`, followed by `watch_session` resolve.
- **Flemmix**: DLE-style search `/index.php?do=search&subaction=search&...&story=<query>`; title/season page -> multiple player families (Vidara, JWPlayer entitlement, LuluVDO depending on work).
- **HDHub4U**: hub -> current terminal -> search `/search.html?q=...`; title page groups seasons/releases and per-episode Drive/Instant/Watch links.
- **Mugiwara**: catalogue page -> `/api/animes/<slug>/season?index=<n>&isKai=false`; Sibnet playlist/player chain observed.
- **Frenchstream**: hub/terminal + site-native detail IDs; direct terminal media observed through provider player hosts.
- **VoirAnime / Neko-Sama / VegaMovies / Movies4u / Moonflix / AnimePahe / AnikotoTV / AniZone**: provider-local route captures also exist in the historical corpus.

These are route/LKG clues. They must be rebound to the provider's current DATA domain instead of hard-coding historical hosts.

## Evidence block C — older VF/runtime diagnostics (late July–early August 2026)

This was the missing third block in later repairs. It predates the September browser capture and records concrete runtime/parser failures.

Recovered anchors:
- **Purstream / Movix**: both contacted Movix-family APIs successfully in historical tests; later variants included `api.movix.show` / `api.movix.fun`. Historical `api.movix.cash` was treated as replaceable/stale where blocked.
- **StreamZo**: provider site could return the correct title page while the parser missed the current player. One observed Interstellar page exposed a `data-embed` Videasy player instead of the route expected by the provider.
- **Frenchstream**: site/search could be HTTP 200 while the old `/engine/ajax/film_api.php?id=<id>` route returned 404 / not-found. This is explicit evidence that "domain reachable" != "provider route valid".
- **Flemmix**: search/parser needed separate qualification; zero search results and zero resolved players are distinct failure stages.
- **Coflix / Nakios / ToFlix** were part of the same VF-provider test cohort and must be compared against their own provider-local chain rather than generic route templates.
- Historical test matrix used multiple fixtures rather than a single title; exact TMDB identity, final media, language and quality were intended to be checked separately.

### Permanent lessons from block C

1. A 200 homepage is not provider functionality.
2. Provider-local route changes must be recorded independently of domains.
3. A current provider implementation should prefer its current provider DATA/known terminal, while retaining historical route structure only as LKG evidence.
4. Search -> identity match -> detail/episode -> player/embed -> terminal playable media are separate gates.
5. Do not revive a stale endpoint simply because it existed in an older provider script.

## Census interaction

The full provider census remains the live truth for current terminal status. This evidence ledger is used to:
- choose targeted probes and fixtures;
- diagnose ZERO/PARTIAL providers;
- distinguish route regressions from domain changes;
- prevent rebuilding a provider with a generic route when a provider-specific chain is already known;
- preserve historical positive behavior without treating stale URLs as current authority.

`PROVIDER_CENSUS_STATUS.md` is generated from the latest full census and should never be manually edited.

## Evidence block D — exact user route captures recovered from prior test files

Recovered from the original manual test files/logs, not reconstructed from the current provider code. Treat these as historical LKG evidence and fixture-selection guidance; current domains still require live revalidation.

- **TV field test — Interstellar**: Purstream 720p; Castle English+Hindi; Papadustream 480p; DesiFlix 4K+720p; StreamZo returned wrong content labelled `Inconnue`; VidRock had one dead/403 720p row plus a working 1080p row; HindMoviez exposed four 480p rows that did not appear playable. This is evidence for quality correction, fail-closed 403 handling, wrong-content rejection and language preservation.
- **TV field test — House of the Dragon S1E2**: Purstream 720p; PersianStreamio seven rows; Castle multi-quality/multi-dialect rows; DesiFlix several 4K/720p rows plus one `Inconnue`; VidRock 1080p+720p; HindMoviez rows appeared non-playable. Exact season/episode identity is mandatory.
- **Anime field tests**: Ragna Crimson S1E4 had Anime-Sama playable + one dead `Inconnue` and Mugiwara 720p playable. Mushoku Tensei S3E11 loaded no providers/streams. Hell Mode S2E10: Anime-Sama 1080p appeared correct; Mugiwara returned eight 1080p rows for the wrong episode and mislabeled VOSTFR as VF. These cases remain regression fixtures for episode identity and language normalization.
- **Global client behavior**: non-answering providers could remain visible for more than a minute; provider generations accumulated across navigation; late stale rows could reappear; stream titles lost normalization. These are Core/runtime invariants, not provider-specific exceptions.

Exact provider route captures relevant to unresolved providers:
- **AllAnime manual positive**: hub `allanime.sa.com` -> `ww2.aniwatch.fit`; One Piece search exposed separate sub/dub pages; an episode page resolved to `fetch.nexabloom.top/.../master.m3u8` and variant playlist, both HTTP 200. One Piece is therefore a retained provider-targeted positive fixture even when JJK is a catalogue miss.
- **AniKotoTV historical positive**: `/ajax/anime/search?keyword=death+note` -> `/watch/death-note-.../ep-1` -> `/ajax/server?get=...`. This proves the older provider-local chain existed; it is historical evidence only after the 2026-09-19 upstream migration to ARM/MegaPlay.
- **MoviesMod manual chain**: `/search/interstellar` -> Interstellar detail -> `links.modpro.blog/archives/... ` -> `cloud.unblockedgames.world/?sid=...` / `urlflix.xyz/gets/...` -> `driveseed.org/file/...` -> Google/video-seed direct path. The browser flow includes timed/human interstitials; a provider runtime must bypass only proven deterministic steps and otherwise fail closed.
- **HDHub4u manual chain**: hub `hdhub4u.bi` -> terminal `new5.hdhub4u.cl` -> `/search.html?q=...` -> title/season page -> `greenmountmotors.com?id=...` -> `hblinks.co/archives/...` -> HubDrive/HubCDN/HubCloud -> terminal media. **This is HDHub4u evidence and must never be reassigned to 4KHDHub.**
- **AllWish manual positive**: Telegram hub `t.me/s/allwishme` -> `all-wish.me/filter?keyword=death+note` -> `/watch/death-note-.../ep-37` -> `fetch.nexabloom.top/.../master.m3u8` and variant playlist HTTP 200.
- **MovieBox manual positive**: hub `moviiebox.lol` -> `moviebox.yachts`; HOTD page -> `data.vidsrcme.ru/api.php?type=tv&tmdb=94997&season=1&episode=1` / `vidsrcme.ru/vs_src.php?... ` -> terminal `sagaciousslumber.site/.../master.m3u8` and variant playlist HTTP 200.
- **Coflix manual chain**: `coflix.domains` -> active terminal; live search -> title page -> `/wp-json/coflix/v1/resolve?tmdb=...&type=tv&season=...&episode=...&tid=...`. This remains historical cross-check evidence for provider-local identity, independent from later site implementations.
- **Movix/Purstream manual chain**: hub/terminal -> TMDB-backed title route -> watch route; observed terminal HLS through `neocine.embedseek.com`. Useful for client-quality/identity regression checks, not as generic routing for other providers.

The raw source files also preserve older desktop logs in which MoviesHunt found an Interstellar catalogue match and older global audits classified MoviesHunt/AniKotoTV as strict healthy while several other providers were partial or non-media. Those historical classifications are not current status, but they are valid regression clues when the same provider now stops earlier in the chain.
