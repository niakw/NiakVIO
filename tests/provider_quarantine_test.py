#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402


config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
policy = config["provider_patches"]["topcartoons"]
assert policy["manifest_overrides"]["enabled"] is False
assert policy["capability"] == "quarantined"

source = b"module.exports={getStreams:async function(){return [{url:'https://wrong.example/cartoon.mp4'}]}};"
patched, records = apply_overrides("TOPCARTOONS", source, phase="discovery")
text = patched.decode("utf-8")
assert "NUVIO_PROVIDER_QUARANTINE_V1" in text
assert "cross_title_content_mismatch" in text
assert any(row.get("path", "").endswith("quarantine_provider_v1.py") for row in records)

with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as handle:
    handle.write(text)
    handle.write("\nPromise.resolve(module.exports.getStreams('1396','tv',1,1)).then(r=>{if(!Array.isArray(r)||r.length)process.exit(2)}).catch(()=>process.exit(3));\n")
    path = Path(handle.name)
try:
    result = subprocess.run(["node", str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
finally:
    path.unlink(missing_ok=True)

print("provider safety quarantine tests passed")
