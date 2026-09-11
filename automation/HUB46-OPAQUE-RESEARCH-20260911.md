# Hub46 — secondary research on previously opaque providers — 2026-09-11

This pass reconciles older GPT discussions, `MEMORY.md`, current repository evidence and targeted external/runtime proof. The starting queue came from `automation/HUB46-BLOCKER-INVENTORY-20260911.md`: nine targets whose structured DATA did not demonstrate an executable mechanism.

## Current result

- Starting repository-opaque queue: **9**.
- Site mechanisms understood at a useful architectural level: **9/9**.
- Completely unanalyzable sites after this pass: **0**.
- **VidRock:** runtime integrated and **live-proven** for movie + TV.
- **AniDB:** runtime integrated and deterministic chain proven; current GitHub runner is blocked by **HTTP 403 at the first `/browse?q=...` search request**.
- Remaining providers with exact final-hop resolver/playability debt: **7**.

`Mechanism understood` is deliberately weaker than `provider repaired`. It means we know what kind of provider it is and the next execution stage. It does not claim a playable stream unless a live proof below says so.

## 1. VidRock — integrated and live-proven

The workbench now contains a dedicated clean-v3 runtime for the current VidRock contract. Public references exposed the modern API family; targeted network proof then validated the actual provider API and resulting HLS streams.

### Current contract

- provider API authority: `https://vidrock.ru`
- movie: `/api/movie/{tmdbId}`
- TV: `/api/tv/{tmdbId}/{season}/{episode}`
- per-server URLs are AES-256-GCM tokens; runtime decrypts them and accepts only HTTP(S) HLS whose manifest begins with `#EXTM3U`
- raw numeric TMDB is required; IMDb-like positional values fail closed

### Proof

GitHub Actions run **34626186214** proved both fixtures live:

- movie / Interstellar (`157336`): API 200, 5 servers returned, **3 decrypted playable HLS**
- TV / Breaking Bad S01E01 (`1396/1/1`): API 200, 5 servers returned, **3 playable HLS**

Observed playable server families included Atlas, Luna and Orion. The deterministic crypto/runtime test also verifies tamper fail-closed and IMDb no-network behavior.

**Classification:** no longer opaque and no longer theoretical. VidRock has live movie+TV provider proof. Final native acceptance still belongs to the five same-candidate Labs.

## 2. AniDB (`anidb.app`, not `anidb.net`) — integrated, live search currently 403

The target is the streaming site `anidb.app`, not the unrelated metadata database `anidb.net`.

The current public ani-cli v5 contract is:

- base: `https://anidb.app`
- search: `/browse?q={query}`
- detail: `/anime/{anime-id-or-slug}`
- episodes: `/api/frontend/anime/{anime-id}/episodes`
- language/embed resolution: `/api/frontend/episode/{episode-id}/languages`
- language response -> `embed_url` -> player page -> master HLS

NiakVIO previously carried stale structured authority pointing execution to `anidb.pics`. That has now been migrated in both `provider-overrides.json` and `automation/provider-v3-static-knowledge.json` so one-provider materialization can no longer silently resurrect the stale host.

### Integrated runtime

The workbench now contains `PROVIDER.ANIDB.RUNTIME.V1`:

1. canonical media type must be `anime` **before the first provider network request**;
2. canonical title is required;
3. search HTML resolves the AniDB numeric anime id;
4. episode API resolves the requested episode id;
5. language API resolves one or more embeds;
6. embed page resolves a master `.m3u8`;
7. the master must be a valid `#EXTM3U` manifest.

Actions run **34626987178** proved the deterministic runtime and the materialization/gates:

- `ANIDB_RUNTIME_V1_OK streams=2 sub=1 dub=1 canonical_gate_network=0 missing_title_network=0`
- materialized bundle: `providers/anidb-32a0a3f84a6c73ed.js`
- exact activation remains **46 enabled / 50 disabled**
- Provider v3 strategy plan passed for all 96
- Provider Non-Regression passed for all 96
- ProviderBase store remained **96/96 clean**

### Current live blocker

The same run attempted the real first hop and got:

- `GET https://anidb.app/browse?q=Jujutsu%20Kaisen` -> **HTTP 403**
- no provider call beyond search was attempted

**Classification:** mechanism and runtime are understood/implemented. Current live blocker is **anti-bot/network at search**, not parser uncertainty and not an unknown site. Do not claim live AniDB stream proof until this first-hop 403 is overcome or the upstream becomes reachable again.

## 3. VoirAnime — episode HTML -> host selector -> iframe

Public `BetterVoirAnime` code establishes the runtime structure:

- episode pages expose `#manga-reading-nav-head`
- navigation is in `.single-chapter-select`
- host selection is `.host-select`
- player is under `.entry-content .reading-content .chapter-video-frame`
- selected player is an `<iframe>`

**Current unresolved stage:** obtain and validate the currently live selected host iframe/media chain on the rotating VoirAnime domain family. This is a **dynamic iframe extraction** problem, not an unknown-site problem.

## 4. Coflix — catalogue/search -> detail -> server selector -> iframe

Current domain/site evidence establishes searchable film/series details, language/server variants and embedded players; address portals/Telegram remain discovery-only.

**Current unresolved stage:** live server/iframe extraction plus work-identity validation. This is a **dynamic iframe extraction** problem.

## 5. 4KHDHub — release detail -> downstream file host

Current site evidence shows release/detail pages and downstream file hosts such as HubCloud.

**Current unresolved stage:** resolve a downstream host into a directly playable media URL, if available, and prove work identity/transport.

## 6. UHDMovies — UHD detail -> drive/file-host links

Current references describe 1080p/2160p/4K/HDR/HEVC catalogue/detail pages with direct-drive/file links.

**Current unresolved stage:** downstream file-host resolution and native-playable media proof.

## 7. Movies4u — catalogue/search -> detail -> download host

Current site evidence exposes searchable movie/series posts and download-host chains.

**Current unresolved stage:** downstream host resolution and identity/playability proof.

## 8. MoviesDrive — release -> quality variant -> direct-drive/file host

Current indexed posts expose quality variants including 2160p/4K and direct-drive/download links.

**Current unresolved stage:** extract the final media-bearing host/link and prove it is playable by Nuvio.

## 9. CineFreak — index/detail -> third-party watch/download links

Current site evidence says media files are hosted on third-party services and indexed through detail pages.

**Current unresolved stage:** downstream third-party host resolution and playability/identity proof.

## What remains genuinely unresolved

There is **no longer a provider in this nine-provider queue whose overall site mechanism is unknown**.

The remaining exact final-hop queue is:

- **Dynamic iframe extraction:** `voiranime`, `coflix`
- **Download/file-host chain resolution:** `4khdhub`, `uhdmovies`, `movies4u`, `moviesdrive`, `cinefreak`

If one of these seven still cannot expose the final iframe/file URL after targeted live work, report that provider to the user by name with the exact failed stage. Never collapse it back into a generic `0 streams` bucket.

## Next execution order

1. VoirAnime and Coflix: capture the real currently selected iframe/server chain and validate identity.
2. 4KHDHub, UHDMovies, Movies4u, MoviesDrive, CineFreak: resolve their downstream host/file chains into Nuvio-playable media where technically possible.
3. Rebuild the per-provider blocker inventory from the corrected DATA.
4. Run the five native Labs on one exact candidate SHA before any functional-success publication claim.
