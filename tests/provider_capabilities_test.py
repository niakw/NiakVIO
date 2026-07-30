#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402
from provider_capabilities import infer_capability  # noqa: E402

config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
assert "global_stream_output" not in config

vidfast = infer_capability("vidfast", "module.exports={getStreams:function(){}}", config)
assert vidfast["strategy"] == "iframe_player"
assert vidfast["allow_html_url"] is True
assert vidfast["requires_direct_media"] is False
assert "/movie/{tmdbId}" in vidfast["movie_template"]

purstream = infer_capability("purstream", "module.exports={getStreams:function(){}}", config)
assert purstream["strategy"] == "official_domain_hub"
assert purstream["hub"] == "https://purstream.wiki"

legacy = b"module.exports={getStreams:function(){return Promise.resolve([])}};\n/* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3 */\n;(function(){throw new Error('legacy')})();\n"
patched, records = apply_overrides("synthetic", legacy)
assert b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD" not in patched
assert any(item.get("type") == "remove_legacy_global_stream_guard" for item in records)

pur_patch = (config.get("provider_patches") or {}).get("purstream") or {}
assert (pur_patch.get("replacements") or {}).get("purstream.art") != "purstream.wiki"
assert (pur_patch.get("runtime_domain_replacements") or {}).get("purstream.art") != "purstream.wiki"

print("provider capability strategy tests passed")
