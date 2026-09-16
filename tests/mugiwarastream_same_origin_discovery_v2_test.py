#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_MUGIWARA_SAME_ORIGIN_LOOKUP_V2" in text
assert "NIAKVIO_MUGIWARA_DISCOVERY_FIRST_V2" in text
assert '"/api/suggest/lookup?q="+encodeURIComponent(title)' in text
assert 'h["Sec-Fetch-Site"]="same-origin"' in text
assert 'h["Sec-Fetch-Mode"]="cors"' in text
assert 'h["Sec-Fetch-Dest"]="empty"' in text
assert 'q.type==="movie"?"movie":"tv"' in text
lookup = text.index("var currentPage=await discoverPage(q)")
native = text.index("ctx.native.apply(ctx.receiver,a)")
assert lookup < native, "current Mugiwara lookup must run before stale native discovery"
assert "if(currentPage){var currentRows=await fallback(currentPage,q)" in text
assert "if(!pageUrl)pageUrl=await discoverPage(q)" not in text
assert "/api/search?q=" not in text
print("Mugiwara same-origin discovery-first V2 contract passed")
