#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides


# French-Manga intentionally replaces an older generic stream wrapper with the
# stricter NuvioTV direct-media resolver. On a published artifact, a later deep
# pass can therefore add an intermediate wrapper and remove it again. The final
# bytes are unchanged, so the override transaction must not report an effective
# patch record for that pass.
source = b'''async function getStreams(){return [{url:"https://example.invalid/embed/1"}]};module.exports={getStreams};'''
first, first_records = apply_overrides("french-manga", source)
assert first != source
assert b"NUVIO_TV_DIRECT_MEDIA_V2" in first
assert any(
    isinstance(row, dict)
    and row.get("type") == "patch_script"
    and row.get("path") == "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
    for row in first_records
), first_records

second, second_records = apply_overrides("french-manga", first)
if second != first:
    markers = (
        b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD",
        b"NUVIO_STREAM_OUTPUT_SANITIZER",
        b"NUVIO_TV_DIRECT_MEDIA_V2",
        b"NUVIO_HLS_RUNTIME_INTEGRITY",
        b"NUVIO_HLS_MASTER_AUDIO_PRESERVER",
    )
    print(
        "french-manga net-noop drift:",
        {
            "first_sha": hashlib.sha256(first).hexdigest(),
            "second_sha": hashlib.sha256(second).hexdigest(),
            "first_len": len(first),
            "second_len": len(second),
            "records": second_records,
            "markers_first": {m.decode(): first.count(m) for m in markers},
            "markers_second": {m.decode(): second.count(m) for m in markers},
        },
    )
    limit = min(len(first), len(second))
    offset = next((i for i in range(limit) if first[i] != second[i]), limit)
    print("first differing offset:", offset)
    print("first tail around diff:", first[max(0, offset - 160): offset + 240].decode("utf-8", "replace"))
    print("second tail around diff:", second[max(0, offset - 160): offset + 240].decode("utf-8", "replace"))
assert second == first
assert second_records == [], second_records

print("override net-noop regression test passed")
