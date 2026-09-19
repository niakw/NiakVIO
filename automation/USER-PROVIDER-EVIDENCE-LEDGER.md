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
