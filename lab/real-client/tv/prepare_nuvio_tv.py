#!/usr/bin/env python3
from pathlib import Path
import json
import shutil
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: prepare_nuvio_tv.py <nuvio-tv-dir> <niakvio-dir>")

tv = Path(sys.argv[1]).resolve()
niakvio = Path(sys.argv[2]).resolve()
build = tv / "app/build.gradle.kts"
text = build.read_text()

if 'testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"' not in text:
    marker = "    defaultConfig {\n"
    if text.count(marker) != 1:
        raise SystemExit(f"expected one defaultConfig block, found {text.count(marker)}")
    text = text.replace(
        marker,
        marker + '        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"\n',
        1,
    )

build_types = text.find("    buildTypes {")
if build_types < 0:
    raise SystemExit("buildTypes block not found")
debug_start = text.find("        debug {", build_types)
release_start = text.find("        release {", debug_start)
if debug_start < 0 or release_start < 0:
    raise SystemExit("debug/release build type boundaries not found")
debug_block = text[debug_start:release_start]
release_signing = 'signingConfig = signingConfigs.getByName("release")'
if release_signing not in debug_block:
    raise SystemExit("debug release-signing assignment not found")
debug_block = debug_block.replace(
    release_signing,
    'signingConfig = signingConfigs.getByName("debug")',
    1,
)
if "isDebuggable = false" not in debug_block:
    raise SystemExit("debug isDebuggable=false not found")
debug_block = debug_block.replace("isDebuggable = false", "isDebuggable = true", 1)
text = text[:debug_start] + debug_block + text[release_start:]
build.write_text(text)

# Keep Sentry out of the target/test process. This is only a lab mutation.
test_manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <meta-data android:name="io.sentry.auto-init" android:value="false" />
    </application>
</manifest>
'''
for source_set in ("debug", "androidTest"):
    path = tv / f"app/src/{source_set}/AndroidManifest.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(test_manifest)

test_root = tv / "app/src/androidTest"
(test_root / "java/com/nuvio/tv/core/plugin").mkdir(parents=True, exist_ok=True)
assets = test_root / "assets/niakvio"
assets.mkdir(parents=True, exist_ok=True)
shutil.copy2(
    niakvio / "lab/real-client/tv/NiakvioTvRealProviderTest.kt",
    test_root / "java/com/nuvio/tv/core/plugin/NiakvioTvRealProviderTest.kt",
)

manifest = json.loads((niakvio / "manifest.json").read_text(encoding="utf-8"))
rows = {
    str(row.get("id") or "").casefold(): row
    for row in manifest.get("scrapers", [])
    if isinstance(row, dict)
}
selection = []
for provider_id in ("moviebox", "netmirror", "streamzo"):
    row = rows.get(provider_id)
    if not isinstance(row, dict):
        raise SystemExit(f"missing provider in tested manifest: {provider_id}")
    filename = str(row.get("filename") or "")
    source = niakvio / filename
    if not filename.startswith("providers/") or not source.is_file():
        raise SystemExit(f"invalid published provider filename for {provider_id}: {filename}")
    asset_name = f"{provider_id}.js"
    shutil.copy2(source, assets / asset_name)
    selection.append({
        "id": provider_id,
        "enabled": row.get("enabled") is True,
        "version": str(row.get("version") or ""),
        "filename": filename,
        "asset": f"niakvio/{asset_name}",
    })
    print(
        f"FIELD_TV_SELECTION provider={provider_id} enabled={row.get('enabled') is True} "
        f"version={row.get('version')} filename={filename}"
    )
(assets / "selection.json").write_text(
    json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("NuvioTV real-client instrumentation prepared from tested manifest")
