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


# Facts and presentation are Core-wide layers, never provider-specific adapters.
for provider in ("purstream", "movix", "cineby", "animepahe", "goated"):
    source = "module.exports={getStreams:async()=>[{name:'X 4K VFF HEVC E-AC3 5.1 WEB-DL',url:'https://media.example/a.m3u8'}]};\n"
    output, records = apply(provider, source)
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in output, provider
    assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in output, provider
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in output, provider
    assert output.index("NUVIO_GLOBAL_STREAM_FACTS_V1") < output.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1"), provider
    assert output.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1") < output.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1"), provider
    assert any(
        row.get("path") == GLOBAL_STREAM_PRESENTATION
        and row.get("scope") == "global_stream_presentation"
        for row in records
    ), (provider, records)

# Reapplication is idempotent: global Core wrappers are replaced/reused, never stacked.
first, _ = apply("cineby", "module.exports={getStreams:async()=>[]};\n")
second, _ = apply("cineby", first)
assert second.count("NUVIO_GLOBAL_STREAM_FACTS_V1") == 1
assert second.count("NUVIO_GLOBAL_STREAM_IDENTITY_V1") == 1
assert second.count("NUVIO_GLOBAL_STREAM_PRESENTATION_V1") == 1

apply_source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
presentation_source = (ROOT / "scripts/provider_patches/global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert "GLOBAL_STREAM_PRESENTATION" in apply_source
assert '"scope": "global_stream_presentation"' in apply_source
assert "FACTS_PATH" in presentation_source
assert "global_stream_facts_v1.py" in presentation_source
assert "purstream_stream_facts_v1.py" not in presentation_source
assert not (ROOT / "scripts/provider_patches/purstream_stream_facts_v1.py").exists()

print("global stream facts/presentation pipeline tests passed")
