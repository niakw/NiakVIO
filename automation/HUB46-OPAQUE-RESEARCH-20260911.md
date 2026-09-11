# Hub46 — secondary research on previously opaque providers — 2026-09-11

This is the secondary research pass requested after reconciling older GPT discussions, `MEMORY.md` and current repository evidence.

The starting queue came from `automation/HUB46-BLOCKER-INVENTORY-20260911.md`: nine targets whose current NiakVIO structured DATA did not demonstrate an executable mechanism.

## Result

- Starting repository-opaque queue: **9**.
- Site mechanisms now understood at a useful architectural level: **9/9**.
- Completely unanalyzable sites after this pass: **0**.
- Exact public invocation/API shape independently documented: **2** (`vidrock`, `anidb`).
- Mechanism understood but final native-stream resolver still needs implementation/verification: **7**.

`Mechanism understood` is deliberately weaker than `provider repaired`. It means we now know what kind of site/provider it is and where NiakVIO should look next. It does **not** claim that its current bundle returns a playable stream.

## 1. VidRock — resolved invocation shape

**Previous repo state:** registry-only hub; known site but no executable route recorded.

Independent public integration documentation exposes the provider as an iframe service:

- base: `https://vidrock.ru`
- movie: `/movie/{tmdb-or-imdb-id}`
- TV: `/tv/{tmdb-or-imdb-id}/{season}/{episode}`
- accepts TMDB or IMDb IDs
- optional player parameters include `autoplay`, `autonext`, `theme`, `download`, `nextbutton`, `episodeselector`, `lang`
- content-list endpoints are also publicly documented as `/list/movie.json` and `/list/tv.json`

Source checked: `OgBek/watchers-heaven`, `streaming-providers.md`, current public GitHub revision read on 2026-09-11.

**NiakVIO classification:** `iframe-player`, exact route shape known. This should no longer be classified as opaque. Next work is to materialize/test these routes under the ProviderBase iframe contract and native clients.

## 2. AniDB (`anidb.app`, not `anidb.net`) — resolved public frontend API

The target is the streaming site `anidb.app`, not the unrelated long-running metadata database `anidb.net`.

Current ani-cli v5 publicly documents and uses these endpoints:

- base: `https://anidb.app`
- search: `/browse?q={query}`
- detail: `/anime/{anime-id-or-slug}`
- episodes: `/api/frontend/anime/{anime-id}/episodes`
- language/stream resolution: `/api/frontend/episode/{episode-id}/languages`

Recent ani-cli material confirms the move to `anidb.app` and also records a September 2026 outage/maintenance period, so a current network failure must not be confused with an unknown mechanism.

Sources checked:
- `pystardust/ani-cli` current `ani-cli` script
- ani-cli v5.0 discussion #1845
- ani-cli issue #1890 (September 2026 outage context)

**NiakVIO classification:** public JSON API + episode language/stream resolver. Not opaque. Current blocker can legitimately be upstream availability/network drift.

## 3. VoirAnime — episode HTML + host selector + iframe player

The currently indexed VoirAnime family still exposes anime/episode pages, while domains rotate (`voiranime.com`, versioned subdomains and `voir-anime.to` have all been used).

The public `BetterVoirAnime` browser-extension implementation reveals the useful runtime structure:

- episode pages expose `#manga-reading-nav-head`
- episode navigation is in `.single-chapter-select`
- host selection is a `.host-select`
- changing the host select switches the player
- the player lives under `.entry-content .reading-content .chapter-video-frame`
- the selected player is an `<iframe>`
- the extension parses an episode id and can build alternate player URLs using that id

Current indexed episode URLs also confirm an `/anime/.../<episode-slug>/` page shape.

Sources checked:
- `Dastan21/BetterVoirAnime`, `src/pages/episode.js` and parser/manifest references
- public indexed VoirAnime episode pages/current-domain references

**NiakVIO classification:** HTML episode/detail scraper -> host selector -> iframe extraction. The architecture is understood; the exact currently live host iframe URL/extraction path still requires a live DOM/network proof. This is **partial resolver debt**, not an opaque site.

## 4. Coflix — searchable catalogue -> film/series detail -> server list -> iframe

Current official-domain information points to `coflix.group` for films/series and `coflix.domains` as the address/domain portal. The Telegram channel is address discovery only and must remain outside ProviderBase runtime execution.

Current live/indexed pages establish:

- homepage text search and catalogue
- film route shape such as `/film/<slug>/`
- film/detail metadata pages
- `Serveurs disponibles`
- language/server variants such as `VF`, `VOSTFR`, `Lecteurvideo`, `Dood`, `Voe`, `Uqload`
- an embedded `iframe` player on detail pages

Sources checked on 2026-09-11:
- `https://coflix.group/`
- indexed current film pages under `coflix.group/film/.../`
- `https://coflix.domains/`
- official/public Coflix Telegram address announcements for domain correlation only

**NiakVIO classification:** catalogue/search -> detail -> server selector -> iframe. Mechanism understood. Exact iframe/server extraction and identity validation still need live implementation/testing.

## 5. 4KHDHub — release index -> release detail -> file host

Current domain evidence points to `4khdhub.one`. Public/current release references expose detail URLs such as `/disclosure-day-movie-7500/` and downstream file-host links such as HubCloud.

**NiakVIO classification:** release/download index -> detail post -> external file host. The site is not an unknown iframe streaming API. A repair must therefore resolve a playable file/host chain (if one exists) rather than inventing a TMDB direct API.

## 6. UHDMovies — UHD download index -> detail -> direct-drive/file links

Current `uhdmovies.autos` metadata and current public references identify a high-resolution movie/TV download index advertising 1080p/2160p/4K/HDR/HEVC and Google Drive/direct links.

**NiakVIO classification:** catalogue/detail/download-host chain. Mechanism understood; playable-media host resolution is the remaining integration problem.

## 7. Movies4u — searchable catalogue -> post/detail -> download-host chain

Current `movies4u.kg` exposes a searchable/category-driven movie/series catalogue, detail posts and a download workflow.

**NiakVIO classification:** catalogue/search -> detail post -> downstream host/download resolution. Not an unknown provider API. Do not model it as a direct TMDB resolver without live proof.

## 8. MoviesDrive — release post -> quality variant -> direct G-Drive/download host

Current 2026 indexed posts under the rotating MoviesDrive domain family explicitly expose film/series posts, quality variants (480p/720p/1080p/2160p/4K) and state that direct G-Drive download links are provided.

Recent examples indexed in July-September 2026 include `new2.moviesdrive.christmas` and `new3.moviesdrive.christmas`.

**NiakVIO classification:** release/detail post -> quality variant -> downstream direct-drive/file-host link. Mechanism understood; extraction to a Nuvio-playable media URL remains to be proven.

## 9. CineFreak — index/detail -> third-party watch/download file links

Current `cinefreak.net` describes itself as a movie/series/anime/K-drama download/watch index. Indexed pages explicitly state that files are not hosted locally and that the site indexes links hosted on third-party services.

**NiakVIO classification:** catalogue/search -> detail -> third-party host/file links. Mechanism understood; final host resolution/playability remains open.

## What remains genuinely unresolved

There is **no longer a 9-provider “we do not understand the site” bucket**.

The remaining research/implementation buckets are:

1. **Exact integration ready to test:** `vidrock`, `anidb`.
2. **Dynamic iframe extraction still needs live proof:** `voiranime`, `coflix`.
3. **Download/file-host chain needs resolver + playability proof:** `4khdhub`, `uhdmovies`, `movies4u`, `moviesdrive`, `cinefreak`.

If a later live attempt still cannot expose the final iframe/file URL for one of buckets 2-3, that provider should be reported to the user by name with the exact failed stage. Do not collapse it back into generic `0 streams`.

## Immediate execution consequence

The next repair work should prioritize the two strongest newly recovered contracts first:

- materialize/test VidRock's documented movie/TV iframe routes;
- replace stale AniDB domain/route assumptions with the current `anidb.app` frontend API contract and distinguish upstream outage from parser failure.

After that, attack VoirAnime/Coflix at the iframe extraction stage and the five download-index providers at their downstream host-resolution stage.
