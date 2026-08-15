#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"anchor missing in {path}: {old[:140]!r}")
    write(path, text.replace(old, new, 1))


def regex_once(path: str, pattern: str, replacement: str, *, flags: int = 0) -> None:
    text = read(path)
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f"regex anchor mismatch in {path}: count={count} pattern={pattern[:120]!r}")
    write(path, updated)


def preserve_enabled(path: str) -> None:
    replace_once(path, '        row["enabled"] = True\n', '        row["enabled"] = row.get("enabled") is True\n')


def patch_shared_identity() -> None:
    path = "scripts/nuvio_client_lab.cjs"
    old = """  const metadataLabel = String(stream?.title || stream?.description || stream?.filename || stream?.name || '').trim();
  const mediaFilename = humanMediaFilename(stream?.url);
  const label = [metadataLabel, mediaFilename].filter(Boolean).join(' ');
"""
    new = """  const metadataParts = [stream?.title, stream?.description, stream?.filename]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
  if (!metadataParts.length && stream?.name) metadataParts.push(String(stream.name).trim());
  const metadataLabel = metadataParts.join(' ');
  const mediaFilename = humanMediaFilename(stream?.url);
  const label = [metadataLabel, mediaFilename].filter(Boolean).join(' ');
  const strongIdentityLabels = [stream?.title, stream?.filename, mediaFilename]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
"""
    replace_once(path, old, new)
    old = """  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const providerTokens = new Set(identityTokens(stream?.name || stream?.provider || ''));
"""
    new = """  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  const strongProviderTokens = new Set(identityTokens(stream?.name || stream?.provider || ''));
  for (const strongLabel of strongIdentityLabels) {
    const strongTokens = identityTokens(strongLabel).filter((token) => !strongProviderTokens.has(token));
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
      return { status: 'contradiction', reason: mediaFilename && strongLabel === mediaFilename ? 'media_filename_title_mismatch' : 'strong_title_mismatch' };
    }
  }
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const providerTokens = new Set(identityTokens(stream?.name || stream?.provider || ''));
"""
    replace_once(path, old, new)


def patch_tv_probe() -> None:
    path = "scripts/nuvio_tv_probe_v2.cjs"
    replace_once(path, "const { webcrypto } = require('node:crypto');\n", "const { webcrypto } = require('node:crypto');\nconst { streamIdentity } = require('./nuvio_client_lab.cjs');\n")

    # Eliminate the divergent local identity implementation. The TV/native proof
    # must use exactly the same content identity rules as the cross-client lab.
    regex_once(
        path,
        r"\nfunction normIdentity\(value\) \{.*?\n\}\n\nasync function inspectStream\(row\) \{",
        "\nasync function inspectStream(row) {",
        flags=re.S,
    )

    old = """  const variants = [];
  const externalAudio = [];
  let audioGroups = 0;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^#EXT-X-STREAM-INF\\s*:/i.test(line)) {
"""
    new = """  const variants = [];
  const externalAudio = [];
  let audioGroups = 0;
  let durationSeconds = 0;
  let durationEntryCount = 0;
  let isVod = false;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^#EXTINF\\s*:/i.test(line)) {
      const duration = Number(line.slice(line.indexOf(':') + 1).split(',')[0]);
      if (Number.isFinite(duration) && duration >= 0) {
        durationSeconds += duration;
        durationEntryCount += 1;
      }
    } else if (/^#EXT-X-ENDLIST\\s*$/i.test(line)) {
      isVod = true;
    } else if (/^#EXT-X-STREAM-INF\\s*:/i.test(line)) {
"""
    replace_once(path, old, new)
    replace_once(path, "  return { variants, externalAudio, audioGroups };\n", "  return { variants, externalAudio, audioGroups, durationSeconds: durationEntryCount ? durationSeconds : null, isVod };\n")

    old = """    const hasMedia = /#EXTINF\\s*:/i.test(text) || /#EXT-X-PART\\s*:/i.test(text) || /#EXT-X-STREAM-INF\\s*:/i.test(text) || /#EXT-X-MAP\\s*:/i.test(text);
    return { playable: hasMedia, status: response.status, error: hasMedia ? null : 'child_header_only' };
"""
    new = """    const hasMedia = /#EXTINF\\s*:/i.test(text) || /#EXT-X-PART\\s*:/i.test(text) || /#EXT-X-STREAM-INF\\s*:/i.test(text) || /#EXT-X-MAP\\s*:/i.test(text);
    const graph = hlsGraph(text, response.url || url);
    return {
      playable: hasMedia,
      status: response.status,
      error: hasMedia ? null : 'child_header_only',
      media_duration_seconds: graph.durationSeconds,
      is_vod: graph.isVod,
    };
"""
    replace_once(path, old, new)
    replace_once(path, "    hls_external_audio_playable: null,\n    error: null,\n", "    hls_external_audio_playable: null,\n    media_duration_seconds: null,\n    error: null,\n")
    replace_once(path, "      const graph = hlsGraph(text, response.url || url);\n      result.hls_master = graph.variants.length > 0 || /#EXT-X-STREAM-INF\\s*:/i.test(text);\n", "      const graph = hlsGraph(text, response.url || url);\n      result.media_duration_seconds = graph.durationSeconds;\n      result.hls_master = graph.variants.length > 0 || /#EXT-X-STREAM-INF\\s*:/i.test(text);\n")
    replace_once(path, "        const variant = await inspectHlsChild(graph.variants[0], headers);\n        result.hls_variant_playable = variant.playable;\n", "        const variant = await inspectHlsChild(graph.variants[0], headers);\n        result.hls_variant_playable = variant.playable;\n        if (Number.isFinite(variant.media_duration_seconds) && variant.media_duration_seconds > 0) {\n          result.media_duration_seconds = variant.media_duration_seconds;\n        }\n")

    old = """  const inspected = rows.map((row, index) => ({ row, media: media[index], identity: streamIdentity(row, fixture) }));
  const playable = inspected.filter((item) => item.media.playable);
  const identityContradictions = playable.filter((item) => item.identity.status === 'contradiction');
  const identityVerified = playable.filter((item) => item.identity.status === 'match');
  process.stdout.write(JSON.stringify({
    ok: !runtimeError && playable.length > 0 && identityContradictions.length === 0,
    duration_ms: Date.now() - started,
    runtime_error: runtimeError,
    raw_stream_count: rows.length,
    playable_stream_count: playable.length,
    identity_verified_count: identityVerified.length,
    identity_contradiction_count: identityContradictions.length,
    streams: inspected,
  }) + '\\n');
  process.exitCode = playable.length && identityContradictions.length === 0 ? 0 : 2;
"""
    new = """  const inspected = rows.map((row, index) => {
    const metadataIdentity = streamIdentity(row, fixture);
    const mediaResult = media[index];
    const expectedMinutes = Number(fixture?.expectedDurationMinutes || 0);
    const expectedSeconds = expectedMinutes > 0 ? expectedMinutes * 60 : null;
    const measuredSeconds = Number(mediaResult?.media_duration_seconds || 0);
    let durationIdentity = { status: 'unknown', reason: 'duration_unavailable', ratio: null };
    if (expectedSeconds && Number.isFinite(measuredSeconds) && measuredSeconds > 0) {
      const ratio = measuredSeconds / expectedSeconds;
      durationIdentity = (ratio < 0.55 || ratio > 1.8)
        ? { status: 'contradiction', reason: 'fixture_duration_mismatch', ratio }
        : { status: 'match', reason: 'fixture_duration_match', ratio };
    }
    let identity = metadataIdentity;
    if (metadataIdentity.status !== 'contradiction' && durationIdentity.status === 'contradiction') {
      identity = durationIdentity;
    } else if (metadataIdentity.status === 'unknown' && durationIdentity.status === 'match') {
      identity = durationIdentity;
    }
    return { row, media: mediaResult, identity, metadata_identity: metadataIdentity, duration_identity: durationIdentity };
  });
  const playable = inspected.filter((item) => item.media.playable);
  const identityContradictions = playable.filter((item) => item.identity.status === 'contradiction');
  const identityVerified = playable.filter((item) => item.identity.status === 'match');
  const identityUnknown = playable.filter((item) => item.identity.status === 'unknown');
  const strictComplete = playable.length > 0
    && identityVerified.length === playable.length
    && identityContradictions.length === 0
    && identityUnknown.length === 0;
  process.stdout.write(JSON.stringify({
    ok: !runtimeError && strictComplete,
    duration_ms: Date.now() - started,
    runtime_error: runtimeError,
    raw_stream_count: rows.length,
    playable_stream_count: playable.length,
    content_verified_count: identityVerified.length,
    identity_verified_count: identityVerified.length,
    identity_unverified_count: identityUnknown.length,
    identity_contradiction_count: identityContradictions.length,
    streams: inspected,
  }) + '\\n');
  process.exitCode = !runtimeError && strictComplete ? 0 : 2;
"""
    replace_once(path, old, new)


def strict_publisher(path: str, *, has_score: bool = False) -> None:
    replace_once(
        path,
        '"ok": bool(parsed and int(parsed.get("playable_stream_count") or 0) > 0),',
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),',
    )
    if has_score:
        old = """    count = int(value.get("playable_stream_count") or 0)
    return (1 if count else 0, count)
"""
        new = """    playable = int(value.get("playable_stream_count") or 0)
    verified = int(value.get("content_verified_count") or value.get("identity_verified_count") or 0)
    contradictions = int(value.get("identity_contradiction_count") or 0)
    strict = playable > 0 and verified == playable and contradictions == 0
    return (1 if strict else 0, verified if strict else 0)
"""
        replace_once(path, old, new)
    preserve_enabled(path)


def patch_publishers() -> None:
    strict_publisher("scripts/promote_global_nuvio_tv_candidates.py", has_score=True)
    strict_publisher("scripts/promote_target_media_v3.py", has_score=True)

    path = "scripts/publish_nuvio_tv_compat_v2.py"
    replace_once(path, '    "category": "movie",\n}', '    "category": "movie",\n    "expectedDurationMinutes": 169,\n}')
    replace_once(
        path,
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("playable_stream_count") or 0) > 0),',
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),',
    )
    preserve_enabled(path)

    # Desktop compatibility may transform a bundle but must not change activation.
    preserve_enabled("scripts/publish_desktop_runtime_compat.py")


def patch_audit() -> None:
    path = "scripts/audit_catalogue_identity_media.py"
    old = """        identity_verified_count = int(probe.get("identity_verified_count") or 0)
        identity_contradiction_count = int(probe.get("identity_contradiction_count") or 0)
        summary = summarize_media(probe)
        status = "wrong_content" if identity_contradiction_count > 0 else ("playable" if playable_count > 0 else ("returned_unplayable" if raw_count > 0 else "no_streams"))
"""
    new = """        identity_verified_count = int(probe.get("identity_verified_count") or 0)
        content_verified_count = int(probe.get("content_verified_count") or identity_verified_count)
        identity_contradiction_count = int(probe.get("identity_contradiction_count") or 0)
        summary = summarize_media(probe)
        status = "wrong_content" if identity_contradiction_count > 0 else ("playable" if playable_count > 0 and content_verified_count == playable_count else ("identity_unverified" if playable_count > 0 else ("returned_unplayable" if raw_count > 0 else "no_streams")))
"""
    replace_once(path, old, new)
    replace_once(path, '            "identity_verified_count": identity_verified_count,\n            "identity_contradiction_count": identity_contradiction_count,', '            "identity_verified_count": identity_verified_count,\n            "content_verified_count": content_verified_count,\n            "identity_contradiction_count": identity_contradiction_count,')


def patch_tests() -> None:
    path = "tests/nuvio_client_lab.test.cjs"
    anchor = "assert.deepEqual(streamIdentity({ name: 'Purstream 1080p Dual Audio - Inconnue', url: 'https://cdn.example/hls2/03/00026/master.m3u8' }, { title: 'Revenant', mediaType: 'tv', season: 1, episode: 1 }), { status: 'unknown', reason: 'insufficient_identity_metadata' });\n"
    extra = anchor + "assert.deepEqual(streamIdentity({ title: 'Purstream 1080p Dual Audio - Inconnue', description: 'Revenant S01E01', url: 'https://cdn.example/hls2/03/00026/master.m3u8' }, { title: 'Revenant', mediaType: 'tv', season: 1, episode: 1 }), { status: 'match', reason: 'season_episode_match' });\n" + "assert.deepEqual(streamIdentity({ title: 'Ben 10 Ultimate Alien', description: 'Breaking Bad S01E01', url: 'https://cdn.example/generic/master.m3u8' }, { title: 'Breaking Bad', mediaType: 'tv', season: 1, episode: 1 }), { status: 'contradiction', reason: 'strong_title_mismatch' });\n"
    replace_once(path, anchor, extra)

    path = "tests/media_duration_identity_test.py"
    marker = "print('global media duration identity tests passed')\n"
    block = r'''
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
'''
    replace_once(path, marker, block)


def remove_obsolete_bypasses() -> None:
    for path in (
        "scripts/publish_nuvio_tv_compat.py",
        "scripts/nuvio_tv_probe.cjs",
        "scripts/publish_targeted_vf_adapters.py",
        "scripts/reactivate_strict_main_providers.py",
        "scripts/restore_provider_activation_lkg.py",
        "scripts/finalize_nuvio_recovery.py",
    ):
        target = ROOT / path
        if target.exists():
            target.unlink()


def main() -> None:
    patch_shared_identity()
    patch_tv_probe()
    patch_publishers()
    patch_audit()
    patch_tests()
    remove_obsolete_bypasses()
    print("strict content promotion patch applied")


if __name__ == "__main__":
    main()
