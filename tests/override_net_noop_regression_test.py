#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides


# French-Manga now preserves the player embed before its native fallback can
# collapse it to a short troll HLS, then resolves that embed through the strict
# target-media v4 layer. Reapplying the durable override to an already-patched
# published artifact must remain a byte-level no-op.
source = b'''async function getStreams(){return [{url:"https://example.invalid/embed/1"}]};module.exports={getStreams};'''
first, first_records = apply_overrides("french-manga", source)
assert first != source
assert b"NUVIO_FRENCH_MANGA_PLAYER_CAPTURE_V1" in first
assert b"NUVIO_TV_TARGET_MEDIA_V4" in first
assert b"NUVIO_TV_DIRECT_MEDIA_V2" not in first
for path in (
    "scripts/provider_patches/french_manga_player_capture_v1.py",
    "scripts/provider_patches/nuvio_tv_target_media_v4.py",
):
    assert any(
        isinstance(row, dict)
        and row.get("type") == "patch_script"
        and row.get("path") == path
        for row in first_records
    ), first_records

second, second_records = apply_overrides("french-manga", first)
if second != first:
    markers = (
        b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD",
        b"NUVIO_STREAM_OUTPUT_SANITIZER",
        b"NUVIO_FRENCH_MANGA_PLAYER_CAPTURE_V1",
        b"NUVIO_TV_TARGET_MEDIA_V4",
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
