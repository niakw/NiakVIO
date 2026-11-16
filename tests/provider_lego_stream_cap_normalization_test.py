#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "apply_provider_overrides_stream_cap",
    ROOT / "scripts" / "apply_provider_overrides.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.PROVIDER_STREAM_OUTPUT_CAP == 40

options, changed = module._normalize_provider_stream_output_options(
    {
        "maxStreams": 8,
        "max_streams": "6",
        "max_pages": 3,
        "maxDepth": 2,
        "requestTimeoutMs": 7000,
    }
)
assert options["maxStreams"] == 40
assert options["max_streams"] == 40
assert set(changed) == {"maxStreams", "max_streams"}
assert options["max_pages"] == 3
assert options["maxDepth"] == 2
assert options["requestTimeoutMs"] == 7000

# The production cap is also a ceiling.
options, changed = module._normalize_provider_stream_output_options({"maxStreams": 80})
assert options["maxStreams"] == 40 and changed == ["maxStreams"]

# Zero/invalid values are not reinterpreted: only positive explicit output caps.
options, changed = module._normalize_provider_stream_output_options(
    {"maxStreams": 0, "max_streams": "auto"}
)
assert options == {"maxStreams": 0, "max_streams": "auto"}
assert changed == []

fix_id = "PROVIDER.DEMO.RUNTIME.V1"
source = """outside = {"maxStreams": 3};
/* STARTFIX:PROVIDER.DEMO.RUNTIME.V1 */
/* FIXDATA:PROVIDER.DEMO.RUNTIME.V1 {} */
const c = {"maxStreams": 12, "max_streams": "5", "maxDepth": 2};
async function resolve(){ return c.maxStreams; }
/* CLOSEFIX:PROVIDER.DEMO.RUNTIME.V1 */
outside2 = {"maxStreams": 2};
"""
normalized, count = module._normalize_provider_owned_stream_output_cap(source, fix_id)
assert count == 2, normalized
assert 'outside = {"maxStreams": 3};' in normalized
assert 'outside2 = {"maxStreams": 2};' in normalized
assert '{"maxStreams": 40, "max_streams": "40", "maxDepth": 2}' in normalized

print("provider Lego stream-cap normalization passed")
