#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "MEMORY.md"
MARKER = "<!-- MAX_REPAIR_20260916_V1 -->"

SECTION = r'''<!-- MAX_REPAIR_20260916_V1 -->
## 2026-09-16 late — PR #122 maximum non-display repair checkpoint

This section supersedes older branch-topology assumptions below for the active repair transaction only.

- Active repair PR: **#122**, branch **`fix/non-display-recovery-20260916`**. **Do not mutate or merge `main` until the repair/lab gates are actually green.** The public release remains **5.21.48** at this checkpoint; 5.21.49 has not been published.
- Current persisted branch head after the correlated-player survival wave is **`5972423152d4f78face33d9bc5acf00a5d4aa3c5`** (`fix: preserve correlated current provider embeds`). V21 run **35153222824** rematerialized/validated 37 provider artifacts and pushed that commit before its positive proof gate.
- Earlier current-contract materialization proved **VidLove** and **VidFast** live end-to-end in run **35147375527**, persisted by commit **`881c3ba1`**: VidLove movie + TV returned direct HLS (`application/vnd.apple.mpegurl`, `#EXTM3U`), and VidFast returned its current `/movie/{tmdbId}` and `/tv/{tmdbId}/{season}/{episode}` embeds. Do not regress these while repairing the residual queue.
- Network/current-contract evidence established before V21:
  - **WookaFR**: `wookafr.blog` is dead; current authority is `wookafr.boston` (`.center` redirects there). Interstellar reaches `lecteurvideo.com`; current player handoff is encoded in `showVideo(base64, ...)` and decodes to multiple real player embeds. Authority DATA was corrected toward `.boston`.
  - **AllWish**: `all-wish.me` is current and anime-only. Search -> watch show id -> `/ajax/episode/list/{id}` -> `/ajax/server/list?servers=...` -> `/ajax/server?get=...` yields correlated player URLs. Semantic publication must remain anime-only; generic movie support is false.
  - **Flemmix**: current authority is `flemmix.me`; `/search?q=` returns structured catalogue rows and movie detail pages expose signed `/embed/video/{id}?expires=...&signature=...` player handoffs. Historical `.cloud` authority is stale.
  - **AllAnime**: current official site is `https://ww2.aniwatch.fit`. One Piece recent episode 1178 proved live detail -> episode -> MegaPlay/Vidmoly player handoff. Episode 1 was not exposed in the current page, so archive completeness must not be fabricated.
  - **MovieBox**: current endpoint `https://vidsrcme.ru/vs_src.php` returns a JSON `src` player for movie and TV. Nested direct `stream_urls` are encrypted/WASM; preserve the correlated player embed rather than inventing a direct HLS decryption.
  - **Coflix**: current site no longer proved an anime catalogue; semantic anime lane was removed. Movie/TV remain separate proof work.
- Honest external/current-source limits already established:
  - **AnimeSalt** current domain is parked/domain-for-sale (and has TLS-chain issues): no catalogue parser can repair a dead source.
  - **Showbox** identifies content but current playable versions require external auth/cookie state; do not manufacture a green.
  - **4KHDHub** (`hdhub4u.bi`) currently serves catalogue/home shell for tested search/API candidates with no proved semantic result/hop; classify as source/catalogue drift until a real backend is evidenced.
  - **MoviesMod** currently resolves through download-oriented hosters (including urlflix/1fichier-like paths) without a reliably proved playable media route; never promote a download link as a fake stream.
  - **AnimeSamaCo / DxD** is currently `catalog_miss_both`, not a parser success; do not claim a positive lane without catalogue evidence.
- V20/V21 exposed a systemic residual failure rather than seven independent provider bugs. In V21 run **35153222824**, manifest-authoritative probes for **WookaFR, AllWish, Flemmix movie, Flemmix TV, AllAnime, MovieBox movie and MovieBox TV all returned `count=0`** despite previously proved current network contracts. The correlated-player fallback patch was persisted, but the rows disappear before a usable output reaches the probe.
- The next systemic suspect is the common ProviderBase `_fetch()` request signature: current `scripts/provider_base_store.py` injects **`User-Agent: Mozilla/5.0 NiakVIO/3`** for provider HTTP. This is a hypothesis pending A/B proof, not yet an accepted root cause. AllWish in particular was only proved current with a normal browser UA. Repair must be made at the common ProviderBase source if confirmed, then rematerialized; do not fork five provider-specific UA hacks.
- Correlated player rule: a provider with current, identity-correlated player evidence may preserve that embed via `__nuvioCorrelatedPlayerFallbackV1`; unresolved/incidental HTML/download pages must still fail closed. Do not weaken `CORE.RUNTIME_MEDIA_SAFETY` globally merely to create positive counts.
- Remaining execution order: prove/falsify the ProviderBase request-header hypothesis; repair/rematerialize if confirmed; re-probe AllWish/Flemmix/AllAnime/MovieBox/Wooka; then inspect Coflix movie/TV and residual non-loaders; finally run exact PR ledger + relevant non-regression/Labs before any merge/publication.

'''


def main() -> None:
    text = MEMORY.read_text(encoding="utf-8")
    if MARKER in text:
        print("MEMORY_MAX_REPAIR_V1_ALREADY_PRESENT")
        return
    anchor = "## 2026-09-16 — authoritative current checkpoint"
    if anchor in text:
        text = text.replace(anchor, SECTION + anchor, 1)
    else:
        text = text.rstrip() + "\n\n" + SECTION
    MEMORY.write_text(text, encoding="utf-8")
    print("MEMORY_MAX_REPAIR_V1_WRITTEN")


if __name__ == "__main__":
    main()
