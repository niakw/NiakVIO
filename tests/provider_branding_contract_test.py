#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANDING_FILE = ROOT / "assets/providers/emojis.json"
PATCH_FILE = ROOT / "scripts/provider_patches/global_provider_branding_v1.py"

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
branding = json.loads(BRANDING_FILE.read_text(encoding="utf-8"))
assert branding.get("policy") == "committed-provider-default-emoji"
rows = branding.get("providers")
assert isinstance(rows, dict)
manifest_ids = {
    str(row.get("id") or "").strip().casefold()
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
}
assert set(rows) == manifest_ids, (sorted(manifest_ids - set(rows)), sorted(set(rows) - manifest_ids))
assert len(rows) == len(manifest_ids) == 92, (len(rows), len(manifest_ids))
for provider_id, row in rows.items():
    assert isinstance(row, dict), provider_id
    assert str(row.get("name") or "").strip(), provider_id
    assert str(row.get("emoji") or "").strip(), provider_id

spec = importlib.util.spec_from_file_location("provider_branding_contract", PATCH_FILE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = 'globalThis.getStreams=async function(){return [{url:"https://example.com/video.m3u8",name:"old"}]};\n'
output = module.apply(source, context={"provider_id": "peachify"})
assert "NUVIO_GLOBAL_PROVIDER_BRANDING_V1" in output
assert "🍑" in output and "Peachify" in output
assert module.apply(output, context={"provider_id": "peachify"}) == output

with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
    handle.write(output)
    handle.write(
        '\nPromise.resolve(globalThis.getStreams()).then(function(rows){'
        'if(!Array.isArray(rows)||rows.length!==1||rows[0].name!=="🍑 Peachify")'
        '{console.error(JSON.stringify(rows));process.exit(2)}'
        'console.log(rows[0].name)' 
        '}).catch(function(error){console.error(error);process.exit(3)});\n'
    )
    artifact = Path(handle.name)
try:
    result = subprocess.run(
        ["node", str(artifact)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "🍑 Peachify" in result.stdout
finally:
    artifact.unlink(missing_ok=True)

print(f"provider branding contract passed: providers={len(rows)} local_stream_fallback=emoji+clean_name")
