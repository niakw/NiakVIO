#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402

SOURCE = b"""module.exports={getStreams:async()=>[{name:'Source | 4k | Dual-Audio',title:'Interstellar - 2014',description:'4k Dual-Audio HEVC E-AC3 5.1 169 min BLU-RAY',url:'https://media.example/master.m3u8',quality:'',language:'',headers:{Referer:'https://source.example/'}}]};\n"""

patched, records = apply_overrides("generic-core-test", SOURCE, phase="discovery")
text = patched.decode("utf-8")
paths = [str(row.get("path") or "") for row in records]

# Final presentation is Core-wide. No provider-specific facts/presentation fork
# may be required for a provider to receive the shared display contract.
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in text
assert "scripts/provider_patches/global_stream_presentation_v1.py" in paths
assert not [path for path in paths if "/purstream_" in path]

# Lock stable Core behavior rather than a disposable implementation-revision label.
# The facts layer and structured badge contract must be present for a generic provider.
assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in text
assert "__nuvioStreamFacts" in text
assert "badgeIds" in text

# The Core enriches presentation without replacing playback material or the
# provider's header shape.
assert "https://media.example/master.m3u8" in text
assert "headers" in text and "Referer" in text

print("provider-agnostic shared Core presentation pipeline test passed")
