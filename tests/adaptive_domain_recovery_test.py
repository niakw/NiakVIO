#!/usr/bin/env python3
from pathlib import Path
import base64
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "patch", ROOT / "scripts/provider_patches/adaptive_domain_recovery.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

source = 'module.exports={getStreams:function(){return fetch("https://old.example/api/search?q=x")}};'
options = {
    "groups": [
        {
            "hosts": ["old.example"],
            "candidates": ["https://new.example", "https://backup.example"],
        }
    ]
}
out = mod.apply(source, options=options)
assert "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1" in out
assert "new.example" not in out  # configuration is encoded, not exposed as brittle literal rewrites
assert out.endswith(source)

normalized = [
    {
        "hosts": ["old.example"],
        "candidates": ["https://new.example", "https://backup.example"],
    }
]
new_payload = base64.b64encode(
    json.dumps(
        {"revision": mod.IMPLEMENTATION_REVISION, "groups": normalized},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
).decode()
legacy_payload = base64.b64encode(
    json.dumps(normalized, separators=(",", ":"), sort_keys=True).encode()
).decode()
assert new_payload in out

# Simulate an already-published V1 wrapper produced before implementation
# revisions were embedded in the payload. Reapplying the same provider config
# must replace that block instead of incorrectly treating it as current.
legacy = out.replace(new_payload, legacy_payload)
assert legacy_payload in legacy and new_payload not in legacy
migrated = mod.apply(legacy, options=options)
assert migrated.count("NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN") == 1
assert new_payload in migrated
assert legacy_payload not in migrated
assert mod.apply(migrated, options=options) == migrated

# Configuration changes still replace rather than stack the owned wrapper.
out2 = mod.apply(
    migrated,
    options={
        "groups": [
            {"hosts": ["old.example"], "candidates": ["https://new.example"]}
        ]
    },
)
assert out2.count("NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN") == 1

print("adaptive domain recovery test passed")
