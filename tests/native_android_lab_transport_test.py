#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from configure_native_android_lab_transport import ANDROID, configure_manifest  # noqa: E402


def assert_transport(path: Path) -> None:
    root = ET.parse(path).getroot()
    assert any(
        child.tag == "uses-permission"
        and child.get(f"{ANDROID}name") == "android.permission.INTERNET"
        for child in root
    ), path
    application = next((child for child in root if child.tag == "application"), None)
    assert application is not None, path
    assert application.get(f"{ANDROID}usesCleartextTraffic") == "true", path


with tempfile.TemporaryDirectory() as raw:
    temp = Path(raw)

    tv = temp / "nuvio-tv/app/src/androidTest/AndroidManifest.xml"
    configure_manifest(tv)
    configure_manifest(tv)  # idempotence
    assert_transport(tv)
    tv_root = ET.parse(tv).getroot()
    assert sum(
        1
        for child in tv_root
        if child.tag == "uses-permission"
        and child.get(f"{ANDROID}name") == "android.permission.INTERNET"
    ) == 1

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
    configure_manifest(mobile)
    assert_transport(mobile)
    mobile_root = ET.parse(mobile).getroot()
    application = next(child for child in mobile_root if child.tag == "application")
    assert any(
        child.tag == "meta-data" and child.get(f"{ANDROID}name") == "io.sentry.auto-init"
        for child in application
    ), "existing instrumentation metadata must be preserved"

    production = temp / "nuvio-mobile/composeApp/src/main/AndroidManifest.xml"
    production.parent.mkdir(parents=True, exist_ok=True)
    production.write_text("<manifest><application /></manifest>\n", encoding="utf-8")
    before = production.read_text(encoding="utf-8")
    try:
        configure_manifest(production)
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
assert "from configure_native_android_lab_transport import configure_manifest" in hardener
assert "configure_manifest(test_manifest)" in hardener

print("native Android lab transport contract passed: mobile=true tv=true cleartext_scope=test-only production_untouched=true")
