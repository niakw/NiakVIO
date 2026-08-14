#!/usr/bin/env python3
from pathlib import Path
import json
import shutil
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: prepare_nuvio_mobile.py <nuvio-mobile-dir> <niakvio-dir>")

mobile = Path(sys.argv[1]).resolve()
niakvio = Path(sys.argv[2]).resolve()
build = mobile / "composeApp/build.gradle.kts"
text = build.read_text()

compilation_needle = "        withHostTest {}\n\n        compilerOptions {"
compilation_replacement = '''        withHostTest {}
        withDeviceTest {
            instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
            execution = "HOST"
        }
        packaging {
            jniLibs {
                pickFirsts.add("lib/*/libc++_shared.so")
            }
        }

        compilerOptions {'''
if text.count(compilation_needle) != 1:
    raise SystemExit(f"expected one Android host-test compilation block, found {text.count(compilation_needle)}")
text = text.replace(compilation_needle, compilation_replacement, 1)

source_needle = "        commonMain.dependencies {"
source_replacement = '''        val androidDeviceTest by getting {
            dependencies {
                implementation("junit:junit:4.13.2")
                implementation("androidx.test.ext:junit:1.3.0")
                implementation("androidx.test:runner:1.7.0")
            }
        }
        commonMain.dependencies {'''
if text.count(source_needle) != 1:
    raise SystemExit(f"expected one commonMain dependency block, found {text.count(source_needle)}")
build.write_text(text.replace(source_needle, source_replacement, 1))

main_manifest = mobile / "composeApp/src/androidMain/AndroidManifest.xml"
main_manifest.write_text('''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
</manifest>
''')

test_root = mobile / "composeApp/src/androidDeviceTest"
(test_root / "kotlin/com/nuvio/app/features/plugins").mkdir(parents=True, exist_ok=True)
assets = test_root / "assets/niakvio"
assets.mkdir(parents=True, exist_ok=True)

# Sentry's official SentryInitProvider checks application metadata key
# io.sentry.auto-init. Disable it only for the instrumentation APK so the
# provider runtime can be tested without any external DSN/configuration.
(test_root / "AndroidManifest.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <meta-data android:name="io.sentry.auto-init" android:value="false" />
    </application>
</manifest>
''')

shutil.copy2(
    niakvio / "lab/real-client/android/NiakvioRealProviderMobileTest.kt",
    test_root / "kotlin/com/nuvio/app/features/plugins/NiakvioRealProviderMobileTest.kt",
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
        f"FIELD_ANDROID_SELECTION provider={provider_id} enabled={row.get('enabled') is True} "
        f"version={row.get('version')} filename={filename}"
    )
(assets / "selection.json").write_text(
    json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("NuvioMobile real-client instrumentation prepared from tested manifest")
