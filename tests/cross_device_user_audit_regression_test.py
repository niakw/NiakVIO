#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

presentation = load(ROOT / "scripts/provider_patches/global_stream_presentation_v1.py", "cross_presentation")
branding = load(ROOT / "scripts/provider_patches/global_provider_branding_v1.py", "cross_branding")
assert presentation.REVISION == "all-providers-client-projection-evidence-language-v24"

apply_source = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
assert apply_source.index("CORE.STREAM_PRESENTATION.V1") < apply_source.index("CORE.STREAM_SANITIZER.V6")
assert apply_source.index("CORE.STREAM_SANITIZER.V6") < apply_source.index("CORE.RUNTIME_MEDIA_SAFETY.V4")
assert apply_source.index("CORE.RUNTIME_MEDIA_SAFETY.V4") < apply_source.index("CORE.PROVIDER_BRANDING.V1")
assert apply_source.index('"scope": "global_runtime_media_safety"') < apply_source.index('"scope": "global_provider_branding"')

presentation_source = (ROOT / "scripts/provider_patches/global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert 'return s(c.languageFallback)||(vfMode?"VF":"VO")' not in presentation_source
assert 'r&&r.name,r&&r.title,r&&r.label,r&&r.sourceLabel' not in presentation_source.split('function language(r)',1)[1].split('function detailedLanguage',1)[0]
branding_source = (ROOT / "scripts/provider_patches/global_provider_branding_v1.py").read_text(encoding="utf-8")
assert "post-safety-uniform-final-label-v9" in branding_source
assert 'return q?v+" - "+q:v' in branding_source
assert 'if(placeholder(o.quality))delete o.quality' in branding_source

# A provider-level French/VF capability is not stream-level audio proof.
base = "module.exports={getStreams:async()=>[{name:'StreamZo French Dub',sourceName:'Server 1080p',url:'https://media.example/a.m3u8',quality:'720p'}]};\n"
patched = presentation.apply(base, context={"provider_id": "streamzo"})
patched = branding.apply(patched, context={"provider_id": "streamzo"})
with tempfile.TemporaryDirectory(prefix="niakvio-cross-device-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(patched, encoding="utf-8")
    runner.write_text(
        "const p=require(" + json.dumps(str(provider)) + ");p.getStreams({mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])));\n",
        encoding="utf-8",
    )
    done = subprocess.run(["node", str(runner)], text=True, encoding="utf-8", capture_output=True, timeout=15)
    assert done.returncode == 0, done.stdout + done.stderr
    row = json.loads(done.stdout.strip())
    assert row["quality"] == "720p", row
    assert row["title"].endswith(" - 720p"), row
    assert "1080p" not in row["title"] and "French Dub" not in row["title"], row
    assert "Inconnue" not in row["title"] and "Unknown" not in row["title"], row
    assert not row.get("language"), row
    assert not ({"vf", "vfq", "vo", "vostfr", "multi"} & set(row.get("badgeIds") or [])), row

# Placeholder quality is removed rather than exposed for client-side appending.
base_unknown = "module.exports={getStreams:async()=>[{name:'Kehflix - Inconnue',url:'https://media.example/a.m3u8',quality:'Inconnue'}]};\n"
unknown = branding.apply(presentation.apply(base_unknown, context={"provider_id":"kehflix"}), context={"provider_id":"kehflix"})
with tempfile.TemporaryDirectory(prefix="niakvio-cross-device-unknown-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(unknown, encoding="utf-8")
    runner.write_text("const p=require("+json.dumps(str(provider))+");p.getStreams('157336','movie').then(v=>console.log(JSON.stringify(v[0])));\n", encoding="utf-8")
    done = subprocess.run(["node", str(runner)], text=True, encoding="utf-8", capture_output=True, timeout=15)
    assert done.returncode == 0, done.stdout + done.stderr
    row = json.loads(done.stdout.strip())
    assert "quality" not in row, row
    assert not any(x in row["title"].lower() for x in ("inconnue", "unknown")), row

codegen = (ROOT / "scripts/native_player_diagnostics_codegen.py").read_text(encoding="utf-8")
assert "queryIntentActivities(launcherQuery, 0)" in codegen
assert "launchActivity.activityInfo.packageName" in codegen
assert "context.packageName,\n                MainActivity::class.java.name" not in codegen

contract = json.loads((ROOT / "automation/platform-runtime-contracts.json").read_text(encoding="utf-8"))
observed = contract.get("observed_native_differences") or {}
assert observed.get("niakvio_sha") == "6b28f3b2c53f5ca6cfb4bc11a3af139c21d6dee1"
rows = {row["device"]: row for row in observed.get("devices") or []}
assert "macOS" in rows and "mpv_create_failed" in rows["macOS"]["player"]
assert "correct reset" in rows["macOS"]["classification"] or "no evidence of current stale reset bug" in rows["macOS"]["classification"]
assert "Android Mobile" in rows and "Activity" in rows["Android Mobile"]["player"]
assert "iOS" in rows and "89/89" in rows["iOS"]["player"]
assert "Android TV" in rows and "no visible 4K" in rows["Android TV"]["ux"]

print("cross-device user/native audit regression contract passed")
