#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from configure_native_android_lab_transport import ANDROID, validate_manifest  # noqa: E402


def application(path: Path):
    root = ET.parse(path).getroot()
    return next((child for child in root if child.tag == "application"), None)


with tempfile.TemporaryDirectory() as raw:
    temp = Path(raw)

    # Missing test overlays are valid and must remain missing: the lab inherits the
    # accepted application's production network policy instead of creating one.
    tv = temp / "nuvio-tv/app/src/androidTest/AndroidManifest.xml"
    validate_manifest(tv)
    assert not tv.exists()

    mobile = temp / "nuvio-mobile/composeApp/src/androidDeviceTest/AndroidManifest.xml"
    mobile.parent.mkdir(parents=True, exist_ok=True)
    mobile.write_text(
        '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <meta-data android:name="io.sentry.auto-init" android:value="false" />
    </application>
</manifest>
''',
        encoding="utf-8",
    )
    before = mobile.read_text(encoding="utf-8")
    validate_manifest(mobile)
    assert mobile.read_text(encoding="utf-8") == before
    app = application(mobile)
    assert app is not None
    assert app.get(f"{ANDROID}usesCleartextTraffic") is None
    assert app.get(f"{ANDROID}networkSecurityConfig") is None

    relaxed = temp / "nuvio-tv/app/src/androidTest/AndroidManifest.xml"
    relaxed.parent.mkdir(parents=True, exist_ok=True)
    relaxed.write_text(
        '''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:usesCleartextTraffic="true" />
</manifest>\n''',
        encoding="utf-8",
    )
    try:
        validate_manifest(relaxed)
    except RuntimeError as exc:
        assert "usesCleartextTraffic=true" in str(exc)
    else:
        raise AssertionError("human UX lab must reject test-only cleartext relaxation")

    production = temp / "nuvio-mobile/composeApp/src/main/AndroidManifest.xml"
    production.parent.mkdir(parents=True, exist_ok=True)
    production.write_text("<manifest><application /></manifest>\n", encoding="utf-8")
    before = production.read_text(encoding="utf-8")
    try:
        validate_manifest(production)
    except ValueError as exc:
        assert "production manifest" in str(exc)
    else:
        raise AssertionError("production manifest must be rejected")
    assert production.read_text(encoding="utf-8") == before

mobile_suite = (SCRIPTS / "run_native_corpus_mobile_suite.sh").read_text(encoding="utf-8")
tv_suite = (SCRIPTS / "run_native_corpus_tv_suite.sh").read_text(encoding="utf-8")
hardener = (SCRIPTS / "harden_nuvio_mobile_device_test.py").read_text(encoding="utf-8")
for suite in (mobile_suite, tv_suite):
    assert "configure_native_android_lab_transport.py" in suite
assert 'composeApp/src/androidDeviceTest/AndroidManifest.xml' in mobile_suite
assert 'app/src/androidTest/AndroidManifest.xml' in tv_suite
assert "from configure_native_android_lab_transport import configure_manifest" not in hardener

print("native Android lab transport contract passed: production_policy=true modified=false")
