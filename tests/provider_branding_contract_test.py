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
assert manifest_ids <= set(rows), sorted(manifest_ids - set(rows))
assert len(manifest_ids) > 0
for provider_id, row in rows.items():
    assert isinstance(row, dict), provider_id
    assert str(row.get("name") or "").strip(), provider_id
    emoji = str(row.get("emoji") or "").strip()
    assert emoji, provider_id
    assert emoji != "🔤", f"generic alphabet fallback is forbidden: {provider_id}"

# Providers for which no stronger semantic symbol was selected use their own
# first initial as a regional-indicator emoji rather than a generic ABC marker.
for provider_id, expected in {
    "animepahe": "🇦",
    "yflix": "🇾",
    "nakios": "🇳",
    "ctgmovies": "🇨",
}.items():
    assert rows[provider_id]["emoji"] == expected, (provider_id, rows[provider_id])

spec = importlib.util.spec_from_file_location("provider_branding_contract", PATCH_FILE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Future Core probes get the first alphabetic initial too. The committed
# registry may pre-register providers from a pending publication transaction,
# while every currently published provider remains mandatory.
future = module._load_provider("future-provider-never-seen-before")
assert future["name"] == "Future Provider Never Seen Before", future
assert future["emoji"] == "🇫", future
assert module._initial_emoji("4KHDHub Next") == "🇰"
assert module._initial_emoji("") == "🇸"

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

print(f"provider branding contract passed: providers={len(rows)} local_stream_fallback=semantic_or_initial_emoji+clean_name")
