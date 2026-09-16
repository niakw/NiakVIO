#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "MEMORY.md"
MARKER = "<!-- MAX_REPAIR_20260916_V22_RESULT -->"
SECTION = r'''<!-- MAX_REPAIR_20260916_V22_RESULT -->
### V22 request-signature A/B + MovieBox trace
- Diagnostic workflow **35154561647** completed successfully. The earlier common-User-Agent hypothesis is **falsified** and must not be used as a blanket ProviderBase change.
- Exact A/B from the GitHub runner:
  - MovieBox `vidsrcme.ru/vs_src.php`: **200** with both `Mozilla/5.0 NiakVIO/3` and a Chrome UA.
  - AllWish `all-wish.me/filter?...`: **403 Cloudflare challenge** with both UAs.
  - Flemmix `flemmix.me/search?...`: **403 Cloudflare challenge** with both UAs.
  - AllAnime `ww2.aniwatch.fit/?s=One Piece`: **200**, identical response size with both UAs.
  - WookaFR `wookafr.boston/`: **200**, identical response size with both UAs.
- Manifest-authoritative MovieBox trace is decisive: current provider runtime requests `vidsrcme.ru` -> **200 JSON**, obtains `cloudorchestranova.com/embed/movie/...`, fetches that player -> **200 HTML**, then a downstream Core layer fetches the same player again with browser playback context + range and still finishes with **`TRACE_ROWS []`**.
- Therefore MovieBox current-provider routing is working and the residual zero is a **downstream Core filtering/enrichment problem**, not a MovieBox endpoint failure and not a ProviderBase UA failure.
- AllWish/Flemmix runner failures are currently **external Cloudflare/runner transport blocks**. Preserve their current browser-observed contracts, but do not claim CI-positive playback unless an honest alternate current backend is proved.
- Next repair target: identify why `CORE.MEDIA_ENRICHMENT.V1` / later playback layers fail to retain a row carrying exact `__nuvioCorrelatedPlayerFallbackV1` provenance. The exception must remain exact/proof-bound; never broadly allow arbitrary HTML/download pages.

'''

def main() -> None:
    text = MEMORY.read_text(encoding="utf-8")
    if MARKER in text:
        print("MEMORY_MAX_REPAIR_V22_ALREADY_PRESENT")
        return
    anchor = "<!-- MAX_REPAIR_20260916_V1 -->"
    if anchor in text:
        pos = text.find("\n## 2026-09-16 — authoritative current checkpoint", text.find(anchor))
        if pos >= 0:
            text = text[:pos] + "\n" + SECTION + text[pos:]
        else:
            text = text.rstrip() + "\n\n" + SECTION
    else:
        text = SECTION + text
    MEMORY.write_text(text, encoding="utf-8")
    print("MEMORY_MAX_REPAIR_V22_WRITTEN")

if __name__ == "__main__":
    main()
