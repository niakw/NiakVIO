#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import parity_hls_terminal_probe as hls

master = b"""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=1800000,RESOLUTION=1920x1080
child.m3u8
"""
parsed = hls.parse_hls(master, "https://cdn.example/master.m3u8")
assert parsed["valid"] is True
assert parsed["master"] is True
assert parsed["variants"] == ["https://cdn.example/child.m3u8"]

media = b"""#EXTM3U
#EXT-X-TARGETDURATION:70
#EXTINF:70.0,
segment.ts
#EXT-X-ENDLIST
"""
parsed_media = hls.parse_hls(media, "https://cdn.example/child.m3u8")
assert parsed_media["valid"] is True
assert parsed_media["master"] is False
assert parsed_media["segments"] == ["https://cdn.example/segment.ts"]
assert parsed_media["complete"] is True
assert parsed_media["duration"] == 70.0

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
proof = hls.verify_hls_terminal(short, "https://cdn.example/short.m3u8", {}, 5)
assert proof["verified"] is False, proof
assert proof["reason"] == "short_finite_vod", proof
assert proof["short_vod_seconds"] == 18.0, proof

assert hls._segment_media("text/html", b"<!doctype html><html>blocked</html>") is False
assert hls._segment_media("application/json", b'{"error":"blocked"}') is False
assert hls._segment_media("video/mp2t", b"x") is True
assert hls._segment_media("application/octet-stream", b"\x00\x00\x00\x18ftypisom") is True

def fake_fetch_ok(url, headers, timeout, *, playlist):
    if url.endswith("child.m3u8"):
        return 200, url, "application/vnd.apple.mpegurl", media
    if url.endswith("segment.ts"):
        body = bytearray(377)
        body[0] = 0x47
        body[188] = 0x47
        return 206, url, "application/octet-stream", bytes(body)
    raise AssertionError(url)

original_fetch = hls._fetch
hls._fetch = fake_fetch_ok
try:
    proof = hls.verify_hls_terminal(master, "https://cdn.example/master.m3u8", {}, 5)
finally:
    hls._fetch = original_fetch
assert proof["verified"] is True, proof
assert proof["reason"] == "hls_segment_media", proof
assert proof["media_duration_seconds"] == 70.0, proof

def fake_fetch_html(url, headers, timeout, *, playlist):
    if url.endswith("child.m3u8"):
        return 200, url, "application/vnd.apple.mpegurl", media
    if url.endswith("segment.ts"):
        return 200, url, "text/html", b"<!doctype html><html>not media</html>"
    raise AssertionError(url)

hls._fetch = fake_fetch_html
try:
    proof = hls.verify_hls_terminal(master, "https://cdn.example/master.m3u8", {}, 5)
finally:
    hls._fetch = original_fetch
assert proof["verified"] is False, proof
assert proof["reason"] == "hls_segment_non_media", proof

print("parity deep HLS terminal proof passed: master->variant->segment, short-VOD and HTML rejection")
