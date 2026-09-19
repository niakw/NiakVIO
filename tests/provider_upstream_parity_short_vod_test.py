#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "provider_upstream_parity_v3_short_vod",
    ROOT / "scripts/run_provider_upstream_parity_v3.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

short = b"""#EXTM3U
#EXT-X-TARGETDURATION:2
#EXTINF:2.0,
a.ts
#EXTINF:2.0,
b.ts
#EXTINF:2.0,
c.ts
#EXTINF:2.0,
d.ts
#EXTINF:2.0,
e.ts
#EXTINF:2.0,
f.ts
#EXTINF:2.0,
g.ts
#EXTINF:2.0,
h.ts
#EXTINF:2.0,
i.ts
#EXT-X-ENDLIST
"""
assert module._short_finite_hls_seconds(short) == 18.0

# A normal finite programme above the floor stays valid evidence.
long_vod = b"#EXTM3U\n" + b"".join(
    b"#EXTINF:10.0,\nseg.ts\n" for _ in range(7)
) + b"#EXT-X-ENDLIST\n"
assert module._short_finite_hls_seconds(long_vod) is None

# A live/incomplete bounded prefix is never called a short VOD.
live = b"#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6.0,\na.ts\n#EXTINF:6.0,\nb.ts\n"
assert module._short_finite_hls_seconds(live) is None

# Master playlists are judged by their children, never by stray EXTINF metadata.
master = b"""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1800000,RESOLUTION=1920x1080
1080.m3u8
#EXTINF:2.0,
preview.ts
#EXT-X-ENDLIST
"""
assert module._short_finite_hls_seconds(master) is None

# Exactly the configured floor is not a short preview.
edge = b"#EXTM3U\n#EXTINF:60.0,\nfull.ts\n#EXT-X-ENDLIST\n"
assert module._short_finite_hls_seconds(edge) is None

print("provider parity short finite VOD guard passed: 18s rejected, >=60s/live/master preserved")
