#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'MEMORY.md'
MARK='<!-- MAX_REPAIR_20260916_V23_RESULT -->'
SECTION=r'''<!-- MAX_REPAIR_20260916_V23_RESULT -->
### V23 exact Core provenance-loss root cause
- Corrected trace run **35154947352**, job **104992064614**, succeeded.
- MovieBox current runtime is not the zero source: `vidsrcme.ru/vs_src.php?type=movie&id=157336` returned **200 JSON**, and its `cloudorchestranova.com/embed/movie/...` player returned **200 HTML**.
- `CORE.MEDIA_ENRICHMENT.V1` received the row with exact `__nuvioCorrelatedPlayerFallbackV1`, `preserveOriginal=true`, and logged **`correlated=true`**. The row correctly survived Media Enrichment.
- Immediately before `CORE.RUNTIME_MEDIA_SAFETY.V4`, the same URL remained but the private proof had disappeared. Runtime Safety then correctly classified it `embed_page_url` and returned zero.
- Root cause: global terminal sanitizer **V8** inherits V7 behavior `correlatedPlayerFallback(...) -> clearPrivateProofs(...)`. V7 deleted `__nuvioCorrelatedPlayerFallbackV1` before output, but Core was later reordered so Runtime Media Safety is now the outer final guard. The sanitizer destroys the proof one layer before its consumer.
- Correct architecture: sanitizer may carry the private proof forward **only on its own exact correlated-player acceptance path**; all ordinary sanitizer paths still clear it. Outer Runtime Media Safety consumes exact proof and then clears all private proof fields before client output. Never whitelist generic HTML/embed URLs.
- Effective V23 options: MovieBox Media Enrichment `preserve_original=True`; MovieBox safety `html_scraper + strict_playback=True`; Wooka/Flemmix `mixed_embed_resolver`; AllAnime `direct_media`; AllWish `html_scraper`.

'''
def main():
    t=P.read_text(encoding='utf-8')
    if MARK in t:
        print('MEMORY_MAX_REPAIR_V23_ALREADY_PRESENT'); return
    anchor='## 2026-09-16 — authoritative current checkpoint'
    t=t.replace(anchor,SECTION+anchor,1) if anchor in t else t.rstrip()+'\n\n'+SECTION
    P.write_text(t,encoding='utf-8')
    print('MEMORY_MAX_REPAIR_V23_WRITTEN')
if __name__=='__main__': main()
