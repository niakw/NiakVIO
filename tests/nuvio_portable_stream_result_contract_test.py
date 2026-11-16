#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
contract = json.loads(
    (ROOT / "automation" / "platform-runtime-contracts.json").read_text(encoding="utf-8")
)
presentation = (ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py").read_text(
    encoding="utf-8"
)
gate = (ROOT / "scripts" / "runtime_contract_gate.py").read_text(encoding="utf-8")

expected = [
    "title", "name", "url", "quality", "size", "language", "provider",
    "type", "seeders", "peers", "infoHash", "headers", "subtitles",
]
assert contract["portable_provider_result_fields"] == expected
assert contract["portable_presentation_rule"].strip()

# Core enrichment must preserve the provider result object, then mirror critical
# presentation through fields parsed by every official Nuvio client.
for marker in (
    "var out=Object.assign({},r)",
    "out.title=provider+",
    "out.name=out.title",
    "out.quality=f.quality",
    "out.language=f.language||null",
    "out.description=lines.join",
    "if(out.description)out.size=out.description",
):
    assert marker in presentation, marker

# Rich NiakVIO fields are additive; they are not the only transport.
assert "out.badgeIds=badgeIds(f)" in presentation
assert "portable provider result ABI drift" in gate
for field in expected:
    assert f'"{field}"' in gate, field

print("NUVIO_PORTABLE_STREAM_RESULT_CONTRACT_OK fields=13 presentation_mirrored=true")
