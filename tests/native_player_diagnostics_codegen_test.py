#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = load("native_player_diagnostics_codegen", "scripts/native_player_diagnostics_codegen.py")
finalizer = load("finalize_native_android_reader_source", "scripts/finalize_native_android_reader_source.py")
mobile_hardener = load("harden_nuvio_mobile_device_test", "scripts/harden_nuvio_mobile_device_test.py")
PLAYER_REACH_GATE = ROOT / "scripts/gate_native_player_reached.cjs"


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


tv_generated = mod.augment_android_test(source("tv"), client="tv", expected_duration_minutes=137, max_player_probes=3)
tv = finalizer.finalize_source(tv_generated, "tv")
assert "com.nuvio.tv.MainActivity" in tv
assert "NuvioNavHost" in tv
assert "Screen.Player.createRoute" in tv
assert "LastPlaybackDiagnostics" in tv
assert "PlayerSettingsDataStore" in tv
assert "nuvio-tv-production" in tv
assert "rows.take(3)" in tv
assert "probeNativePlayer(row.url, row.headers, row.type, 137)" in tv
assert "ExoPlayer.Builder" not in tv
assert "PlayerPlaybackNetworking.createDataSourceFactory" not in tv
assert "FIELD_NATIVE_PLAYER_ENTRY client=tv" in tv
assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" not in tv
assert "entry=nuvio-production-player" in tv

# Production Nuvio receives the provider output. Any sanitation/normalization after
# that belongs to Nuvio itself and is deliberately not reimplemented by the lab.
assert "headers = headers" in tv
assert 'playbackHeaders["Range"]' not in tv
assert "--add-opens" not in tv
assert "usesCleartextTraffic" not in tv

reader_call = tv.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)")
transport_call = tv.index("val transport = probeTransport(row.url, row.headers)")
assert reader_call < transport_call

mobile_generated = mod.augment_android_test(source("mobile"), client="mobile", expected_duration_minutes=137, max_player_probes=2)
mobile = finalizer.finalize_source(mobile_generated, "mobile")
assert "com.nuvio.app.MainActivity" in mobile
assert "PlatformPlayerSurface" in mobile
assert "nuvio-mobile-production" in mobile
assert "rows.take(2)" in mobile
assert "probeNativePlayer(row.url, row.headers, row.type, 137)" in mobile
assert "ExoPlayer.Builder" not in mobile
assert "PlatformPlaybackDataSourceFactory.create" not in mobile
assert "sourceHeaders = headers.orEmpty()" in mobile
assert "Auto mode intentionally emits null" in mobile
assert 'getLaunchIntentForPackage("com.nuviodebug.com")' in mobile
assert "getLaunchIntentForPackage(context.packageName)" not in mobile
assert "FIELD_NATIVE_PLAYER_ENTRY client=mobile" in mobile
assert "FIELD_NATIVE_PLAYER_BEGIN client=mobile" not in mobile
assert mobile.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)") < mobile.index("val transport = probeTransport(row.url, row.headers)")

# Android 11+ package visibility is a harness concern. The test-only manifest must
# expose the separately-installed androidApp debug package without touching the
# production application manifest.
with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    mobile_hardener._harden_test_manifest_only(repo)
    manifest = repo / "composeApp/src/androidDeviceTest/AndroidManifest.xml"
    root = ET.parse(manifest).getroot()
    android_name = "{http://schemas.android.com/apk/res/android}name"
    queries = root.find("queries")
    assert queries is not None
    assert [row.attrib.get(android_name) for row in list(queries) if row.tag == "package"] == ["com.nuviodebug.com"]
    assert not (repo / "androidApp/src/main/AndroidManifest.xml").exists()


def reach_gate(lines: list[str]):
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "reader.log"
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return subprocess.run(
            ["node", str(PLAYER_REACH_GATE), str(log)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )


# A setup attempt is not a reader reach, even if a terminal FIELD_NATIVE_PLAYER row
# exists. This locks the exact false-green that occurred on Mobile in run 32521934832.
no_launch = reach_gate([
    "FIELD_NATIVE_PLAYER client=mobile fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-mobile http_status=0 failure_stage=player_setup error_code=NO_LAUNCH_INTENT"
])
assert no_launch.returncode == 4, (no_launch.stdout, no_launch.stderr)
assert "production_player_never_reached" in no_launch.stderr
assert "setup_rejected=1" in no_launch.stderr

setup_only = reach_gate([
    "FIELD_NATIVE_PLAYER client=mobile fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-mobile-production http_status=0 failure_stage=player_setup error_code=WRONG_ACTIVITY"
])
assert setup_only.returncode == 4, (setup_only.stdout, setup_only.stderr)
assert "setup_rejected=1" in setup_only.stderr

real_player_error = reach_gate([
    "FIELD_NATIVE_PLAYER client=tv fixture=sinners provider64=x request_type=movie route_mode=declared index=0 state=error engine=nuvio-tv-production http_status=0 failure_stage=player error_code=HTTP_403"
])
assert real_player_error.returncode == 0, (real_player_error.stdout, real_player_error.stderr)
assert "status=pass" in real_player_error.stdout
assert "production=1" in real_player_error.stdout

rows = [{"id": "A"}, {"id": "MOVIESDRIVE"}, {"id": "B"}]
assert [row["id"] for row in mod.filter_staged_providers(rows, "moviesdrive")] == ["MOVIESDRIVE"]
assert mod.filter_staged_providers(rows, "") == rows
try:
    mod.filter_staged_providers(rows, "missing")
except ValueError:
    pass
else:
    raise AssertionError("unknown targeted provider must fail closed")

print("native player diagnostics codegen tests passed")
