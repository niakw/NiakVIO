#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "scripts/provider_patches/mugiwarastream_packed_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_MUGIWARA_SAME_ORIGIN_LOOKUP_V2" in text
assert '"/api/suggest/lookup?q="+encodeURIComponent(title)' in text
assert 'h["Sec-Fetch-Site"]="same-origin"' in text
assert 'h["Sec-Fetch-Mode"]="cors"' in text
assert 'h["Sec-Fetch-Dest"]="empty"' in text
assert 'q.type==="movie"?"movie":"tv"' in text
assert 'if(!pageUrl)pageUrl=await discoverPage(q)' in text
assert '/api/search?q=' not in text
print("Mugiwara same-origin discovery V2 contract passed")
