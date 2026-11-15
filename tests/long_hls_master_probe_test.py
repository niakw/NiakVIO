#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_upstream_parity_v3 as parity3


class FakeHeaders:
    def get(self, key: str, default: str = "") -> str:
        return "application/vnd.apple.mpegurl" if key.casefold() == "content-type" else default


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body
        self.offset = 0
        self.headers = FakeHeaders()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getcode(self):
        return 200

    def geturl(self):
        return "https://media.example/master"

    def read(self, count: int = -1) -> bytes:
        if count is None or count < 0:
            count = len(self.body) - self.offset
        data = self.body[self.offset:self.offset + count]
        self.offset += len(data)
        return data


tail = "signed=" + ("x" * 9000)
variant = "https://media.example/variant.m3u8?" + tail
master = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000000\n" + variant + "\n").encode()

seen = {}
original_urlopen = parity3.urllib.request.urlopen
original_verify = parity3.verify_hls_terminal
try:
    def fake_urlopen(request, timeout=None):
        assert request.get_header("Range") is None
        return FakeResponse(master)

    def fake_verify(body, final_url, stream_headers, timeout, **_kwargs):
        seen["body_len"] = len(body)
        seen["has_full_variant"] = variant.encode() in body
        return {"verified": True, "kind": "hls", "status": 200, "reason": "fixture"}

    parity3.urllib.request.urlopen = fake_urlopen
    parity3.verify_hls_terminal = fake_verify
    result = parity3._probe_terminal({"url": "https://media.example/master", "headers": {}}, 12)
finally:
    parity3.urllib.request.urlopen = original_urlopen
    parity3.verify_hls_terminal = original_verify

assert result["verified"] is True
assert seen["body_len"] == len(master), (seen["body_len"], len(master))
assert seen["body_len"] > parity3.PROBE_BYTES
assert seen["has_full_variant"] is True
print(
    "LONG_HLS_MASTER_PROBE_OK "
    f"bytes={seen['body_len']} initial={parity3.PROBE_BYTES}"
)
