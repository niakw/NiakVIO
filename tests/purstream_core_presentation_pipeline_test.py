#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402

SOURCE = b"""module.exports={getStreams:async()=>[{name:'Purstream | 4k | Dual-Audio',title:'Interstellar - 2014',description:'4k Dual-Audio HEVC E-AC3 5.1 169 min BLU-RAY',url:'https://media.example/master.m3u8',quality:'',language:'',headers:{Referer:'https://purstream.example/'}}]};\n"""

patched, records = apply_overrides("purstream", SOURCE, phase="discovery")
text = patched.decode("utf-8")
paths = [str(row.get("path") or "") for row in records]

# The provider-specific adapter exposes facts; it does not own final display.
assert "NUVIO_PURSTREAM_STREAM_FACTS_V1" in text
assert "scripts/provider_patches/purstream_tv_identity_v3.py" in paths

# The same Core presentation layer is applied to Purstream and every other
# reconstructed provider after provider/media/playback hooks.
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in text
assert "scripts/provider_patches/global_stream_presentation_v1.py" in paths
assert text.index("NUVIO_PURSTREAM_STREAM_FACTS_V1") < text.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1")

# The Core normalizes facts without changing playback material or header shape.
assert "identity-first-facts-shared-display-v5" in text
assert "https://media.example/master.m3u8" in text
assert "headers" in text and "Referer" in text

print("Purstream facts -> shared Core presentation pipeline test passed")
