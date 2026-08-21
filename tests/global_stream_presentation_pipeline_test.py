#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides, GLOBAL_STREAM_PRESENTATION  # noqa: E402


def apply(provider: str, source: str) -> tuple[str, list[dict]]:
    payload, records = apply_overrides(provider, source.encode("utf-8"), phase="discovery")
    return payload.decode("utf-8"), records


# The Core presentation layer is unconditional at discovery/reconstruction time;
# provider capabilities only control media/catalogue repair, never presentation.
for provider in ("purstream", "movix", "cineby", "animepahe"):
    source = "module.exports={getStreams:async()=>[{name:'X',url:'https://media.example/a.mp4',quality:'4K'}]};\n"
    output, records = apply(provider, source)
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in output, provider
    assert any(
        row.get("path") == GLOBAL_STREAM_PRESENTATION
        and row.get("scope") == "global_stream_presentation"
        for row in records
    ), (provider, records)

# Reapplication is idempotent: the wrapper is replaced, never stacked.
first, _ = apply("cineby", "module.exports={getStreams:async()=>[]};\n")
second, _ = apply("cineby", first)
assert second.count("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") == 1

source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
assert "GLOBAL_STREAM_PRESENTATION" in source
assert '"scope": "global_stream_presentation"' in source

print("global stream presentation pipeline tests passed")
