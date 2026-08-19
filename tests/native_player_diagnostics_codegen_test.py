#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'scripts/native_player_diagnostics_codegen.py'
spec = importlib.util.spec_from_file_location('native_player_diagnostics_codegen', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


tv = mod.augment_android_test(source('tv'), client='tv', expected_duration_minutes=137, max_player_probes=3)
assert 'PlayerPlaybackNetworking.createDataSourceFactory(context, headers)' in tv
assert 'FIELD_NATIVE_PLAYER client=tv' in tv
assert 'rows.take(3)' in tv
assert 'probeNativePlayer(row.url, row.headers, 137)' in tv
assert '401, 403, 407, 451 -> "http_access"' in tv
assert 'durationSeconds / expected < 0.55' in tv
assert 'responseHeaderNames' in tv
assert '<url>' in tv and '<redacted>' in tv
assert 'row.url' not in [line for line in tv.splitlines() if 'FIELD_NATIVE_PLAYER client=tv' in line][0]
# The official reader must be the first network consumer. A diagnostic GET before
# Media3 can consume one-shot/signed links and create a false 403.
reader_call = tv.index('val reader = probeNativePlayer(row.url, row.headers, 137)')
transport_call = tv.index('val transport = probeTransport(row.url, row.headers)')
assert reader_call < transport_call, (reader_call, transport_call)
assert 'official player must be the first' in tv

mobile = mod.augment_android_test(source('mobile'), client='mobile', expected_duration_minutes=137, max_player_probes=2)
assert 'PlatformPlaybackDataSourceFactory.create(' in mobile
assert 'FIELD_NATIVE_PLAYER client=mobile' in mobile
assert 'rows.take(2)' in mobile
assert mobile.index('val reader = probeNativePlayer(row.url, row.headers, 137)') < mobile.index('val transport = probeTransport(row.url, row.headers)')

rows = [{'id': 'A'}, {'id': 'MOVIESDRIVE'}, {'id': 'B'}]
assert [row['id'] for row in mod.filter_staged_providers(rows, 'moviesdrive')] == ['MOVIESDRIVE']
assert mod.filter_staged_providers(rows, '') == rows
try:
    mod.filter_staged_providers(rows, 'missing')
except ValueError:
    pass
else:
    raise AssertionError('unknown targeted provider must fail closed')

print('native player diagnostics codegen tests passed')
