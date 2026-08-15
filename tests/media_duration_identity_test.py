#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'health_check.mjs').read_text(encoding='utf-8')

deep = config['modes']['deep']
assert deep.get('verify_fixture_duration_identity') is True
assert float(deep.get('minimum_fixture_duration_ratio')) == 0.55
assert float(deep.get('maximum_fixture_duration_ratio')) == 1.8
for mode in ('quick', 'availability', 'retry'):
    assert not config['modes'][mode].get('verify_fixture_duration_identity'), mode

fixtures = config['fixtures']
assert next(f for f in fixtures['movie'] if f['tmdbId'] == '157336')['expectedDurationMinutes'] == 169
assert next(f for f in fixtures['tv'] if f['tmdbId'] == '1396')['expectedDurationMinutes'] == 58
assert next(f for f in fixtures['anime'] if f['tmdbId'] == '95479')['expectedDurationMinutes'] == 24

assert 'function parseMp4MovieDurationSeconds(body)' in source
assert "body[index] !== 0x6d || body[index + 1] !== 0x76 || body[index + 2] !== 0x68 || body[index + 3] !== 0x64" in source
assert 'timescale = body.readUInt32BE(start + 20)' in source
assert 'duration = body.readUInt32BE(start + 24)' in source
assert 'timescale = body.readUInt32BE(start + 28)' in source
assert 'duration = readUInt64BEAsNumber(body, start + 32)' in source
assert 'async function probeStream(stream, mode, fixture = null)' in source
assert 'expectedDurationMinutes: fixture.expectedDurationMinutes ?? null' in source
assert source.count('probeStream(stream, modeConfig, normalizedFixture)') >= 2
assert 'durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds' in source
assert "durationIdentityMismatch ? 'duration_identity_mismatch'" in source
assert 'playbackVerified = false;' in source
assert 'payloadVerified = false;' in source

# The mismatch decision must be based on a measured media duration, never on a
# provider title alone, and must happen before the final playable classification.
parse_idx = source.index('function parseMp4MovieDurationSeconds(body)')
ratio_idx = source.index('durationIdentityRatio = mediaDurationSeconds / expectedDurationSeconds')
category_idx = source.index("durationIdentityMismatch ? 'duration_identity_mismatch'")
assert parse_idx < ratio_idx < category_idx


# The NuvioTV probe used by compatibility/promotion tooling must enforce the
# same identity+duration contract as deep health.
import http.server
import subprocess
import tempfile
import threading

class _ProbeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        duration = 420 if self.path.startswith('/wrong') else 3480
        body = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:{duration},\nsegment.ts\n#EXT-X-ENDLIST\n".encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _ProbeHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
fixture = {
    'tmdbId': '1396', 'mediaType': 'tv', 'season': 1, 'episode': 1,
    'title': 'Breaking Bad', 'year': 2008, 'expectedDurationMinutes': 58,
}
try:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        def run_provider(name, stream):
            provider = tmp / f'{name}.cjs'
            provider.write_text('module.exports={getStreams:async()=>[' + json.dumps(stream) + ']};\n', encoding='utf-8')
            proc = subprocess.run(
                ['node', str(ROOT / 'scripts/nuvio_tv_probe_v2.cjs'), str(provider), json.dumps(fixture), '{}'],
                cwd=ROOT, text=True, capture_output=True, timeout=25,
            )
            parsed = None
            for line in reversed(proc.stdout.splitlines()):
                try:
                    candidate = json.loads(line)
                except Exception:
                    continue
                if isinstance(candidate, dict) and 'playable_stream_count' in candidate:
                    parsed = candidate
                    break
            assert parsed is not None, (proc.returncode, proc.stdout, proc.stderr)
            return proc, parsed

        base = f'http://127.0.0.1:{server.server_port}'
        bad_proc, bad = run_provider('wrong_cartoon', {
            'url': base + '/wrong.m3u8',
            'title': 'TopCartoons - Unknown',
            'description': 'Ben 10 Ultimate Alien',
        })
        assert bad_proc.returncode != 0, bad
        assert bad['identity_contradiction_count'] == 1, bad
        assert bad['content_verified_count'] == 0, bad
        assert bad['streams'][0]['duration_identity']['reason'] == 'fixture_duration_mismatch', bad

        good_proc, good = run_provider('generic_but_described', {
            'url': base + '/good.m3u8',
            'title': 'Purstream 1080p Dual Audio - Inconnue',
            'description': 'Breaking Bad S01E01',
        })
        assert good_proc.returncode == 0, (good, good_proc.stderr)
        assert good['content_verified_count'] == 1, good
        assert good['identity_contradiction_count'] == 0, good

        duration_proc, duration_only = run_provider('duration_only', {
            'url': base + '/good.m3u8',
            'title': 'Purstream 1080p Dual Audio - Inconnue',
        })
        assert duration_proc.returncode == 0, (duration_only, duration_proc.stderr)
        assert duration_only['content_verified_count'] == 1, duration_only
        assert duration_only['streams'][0]['identity']['reason'] == 'fixture_duration_match', duration_only
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

probe_source = (ROOT / 'scripts' / 'nuvio_tv_probe_v2.cjs').read_text(encoding='utf-8')
assert "require('./nuvio_client_lab.cjs')" in probe_source
assert 'content_verified_count' in probe_source
assert 'fixture_duration_mismatch' in probe_source
for publisher in (
    'scripts/promote_global_nuvio_tv_candidates.py',
    'scripts/promote_target_media_v3.py',
    'scripts/publish_nuvio_tv_compat_v2.py',
    'scripts/publish_desktop_runtime_compat.py',
):
    source_text = (ROOT / publisher).read_text(encoding='utf-8')
    assert 'row["enabled"] = True' not in source_text, publisher

for removed in (
    'scripts/publish_nuvio_tv_compat.py',
    'scripts/nuvio_tv_probe.cjs',
    'scripts/publish_targeted_vf_adapters.py',
    'scripts/reactivate_strict_main_providers.py',
    'scripts/restore_provider_activation_lkg.py',
    'scripts/finalize_nuvio_recovery.py',
):
    assert not (ROOT / removed).exists(), removed

print('global media duration identity tests passed')
