#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/native_player_diagnostics_codegen.py"
spec = importlib.util.spec_from_file_location("native_player_diagnostics_codegen", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


tv = mod.augment_android_test(source("tv"), client="tv", expected_duration_minutes=137, max_player_probes=3)
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
assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" in tv
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

mobile = mod.augment_android_test(source("mobile"), client="mobile", expected_duration_minutes=137, max_player_probes=2)
assert "com.nuvio.app.MainActivity" in mobile
assert "PlatformPlayerSurface" in mobile
assert "nuvio-mobile-production" in mobile
assert "rows.take(2)" in mobile
assert "probeNativePlayer(row.url, row.headers, row.type, 137)" in mobile
assert "ExoPlayer.Builder" not in mobile
assert "PlatformPlaybackDataSourceFactory.create" not in mobile
assert "sourceHeaders = headers.orEmpty()" in mobile
assert "Auto mode intentionally emits null" in mobile
assert mobile.index("val reader = probeNativePlayer(row.url, row.headers, row.type, 137)") < mobile.index("val transport = probeTransport(row.url, row.headers)")

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
