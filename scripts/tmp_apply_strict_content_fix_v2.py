#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "tmp_apply_strict_content_fix.py"

spec = importlib.util.spec_from_file_location("strict_fix_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load base strict fix patcher")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


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
"""
    base.replace_once(path, old, new)

    old = """  const episodeOnly = /(?:^|\\D)(?:episode|ep)\\s*0*(\\d{1,4})(?:\\D|$)/i.exec(label);
  if (mediaType === 'movie' && seasonEpisode) return { status: 'contradiction', reason: 'movie_row_is_episode' };
  if (seasonEpisode && (mediaType === 'tv' || mediaType === 'anime')) {
"""
    new = """  const episodeOnly = /(?:^|\\D)(?:episode|ep)\\s*0*(\\d{1,4})(?:\\D|$)/i.exec(label);
  const providerTokens = new Set(identityTokens(stream?.name || stream?.provider || ''));
  const genericIdentityTokens = new Set([
    'unknown', 'inconnue', 'inconnu', 'source', 'stream', 'streaming', 'player', 'lecteur',
    'audio', 'dual', 'multi', 'truefrench', 'french', 'vostfr', 'vf', 'vo', 'fr', 'en',
    'hd', 'fullhd', 'uhd', '4k', '2160p', '1440p', '1080p', '720p', '480p', '360p',
    'hls', 'dash', 'm3u8', 'mp4', 'web', 'webrip', 'webdl', 'bluray', 'brrip', 'hdr', 'dv',
  ]);
  const contentTokens = (value) => identityTokens(value).filter((token) => !providerTokens.has(token) && !genericIdentityTokens.has(token));
  const strongIdentityLabels = [stream?.title, stream?.filename, mediaFilename]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
  for (const strongLabel of strongIdentityLabels) {
    const strongTokens = contentTokens(strongLabel);
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
      return { status: 'contradiction', reason: mediaFilename && strongLabel === mediaFilename ? 'media_filename_title_mismatch' : 'strong_title_mismatch' };
    }
  }
  if (mediaType === 'movie' && seasonEpisode) return { status: 'contradiction', reason: 'movie_row_is_episode' };
  if (seasonEpisode && (mediaType === 'tv' || mediaType === 'anime')) {
"""
    base.replace_once(path, old, new)

    old = """  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const providerTokens = new Set(identityTokens(stream?.name || stream?.provider || ''));
  const rowTokens = identityTokens(label).filter((token) => !providerTokens.has(token));
"""
    new = """  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };
  const rowTokens = contentTokens(label);
"""
    base.replace_once(path, old, new)


def strict_probe_gate(path: str) -> None:
    base.replace_once(
        path,
        '"ok": bool(parsed and int(parsed.get("playable_stream_count") or 0) > 0),',
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),',
    )


def patch_provenance_preserve(path: str, variable: str) -> None:
    base.replace_once(path, '            "activation_eligible": True,\n', f'            "activation_eligible": bool({variable}.get("activation_eligible", False)),\n')
    if variable == "current" and path == "scripts/publish_desktop_runtime_compat.py":
        base.replace_once(path, '            "strict_activation_eligible": bool(current.get("strict_activation_eligible", True)),\n', '            "strict_activation_eligible": bool(current.get("strict_activation_eligible", False)),\n')
    else:
        base.replace_once(path, '            "strict_activation_eligible": True,\n', f'            "strict_activation_eligible": bool({variable}.get("strict_activation_eligible", False)),\n')
    base.replace_once(path, '            "runtime_evidence_eligible": True,\n', f'            "runtime_evidence_eligible": bool({variable}.get("runtime_evidence_eligible", False)),\n')
    base.replace_once(path, '            "activation_blockers": [],\n', f'            "activation_blockers": list({variable}.get("activation_blockers") or []),\n')


def patch_publishers() -> None:
    global_path = "scripts/promote_global_nuvio_tv_candidates.py"
    strict_probe_gate(global_path)
    old = """    count = int(value.get("playable_stream_count") or 0)
    return (1 if count else 0, count)
"""
    new = """    playable = int(value.get("playable_stream_count") or 0)
    verified = int(value.get("content_verified_count") or value.get("identity_verified_count") or 0)
    contradictions = int(value.get("identity_contradiction_count") or 0)
    strict = playable > 0 and verified == playable and contradictions == 0
    return (1 if strict else 0, verified if strict else 0)
"""
    base.replace_once(global_path, old, new)
    base.preserve_enabled(global_path)
    patch_provenance_preserve(global_path, "row")

    target_path = "scripts/promote_target_media_v3.py"
    strict_probe_gate(target_path)
    old = """    result = value.get("result") or {}
    count = int(result.get("playable_stream_count") or 0)
    return (1 if count else 0, count)
"""
    new = """    result = value.get("result") or {}
    playable = int(result.get("playable_stream_count") or 0)
    verified = int(result.get("content_verified_count") or result.get("identity_verified_count") or 0)
    contradictions = int(result.get("identity_contradiction_count") or 0)
    strict = playable > 0 and verified == playable and contradictions == 0
    return (1 if strict else 0, verified if strict else 0)
"""
    base.replace_once(target_path, old, new)
    base.preserve_enabled(target_path)
    patch_provenance_preserve(target_path, "current")

    compat_path = "scripts/publish_nuvio_tv_compat_v2.py"
    base.replace_once(compat_path, '    "category": "movie",\n}', '    "category": "movie",\n    "expectedDurationMinutes": 169,\n}')
    base.replace_once(
        compat_path,
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("playable_stream_count") or 0) > 0),',
        '"ok": bool(parsed and parsed.get("ok") and int(parsed.get("content_verified_count") or 0) > 0 and int(parsed.get("content_verified_count") or 0) == int(parsed.get("playable_stream_count") or 0) and int(parsed.get("identity_contradiction_count") or 0) == 0),',
    )
    base.preserve_enabled(compat_path)
    patch_provenance_preserve(compat_path, "row")

    desktop_path = "scripts/publish_desktop_runtime_compat.py"
    base.preserve_enabled(desktop_path)
    patch_provenance_preserve(desktop_path, "current")


def main() -> None:
    patch_shared_identity()
    base.patch_tv_probe()
    patch_publishers()
    base.patch_audit()
    base.patch_tests()
    base.remove_obsolete_bypasses()
    print("strict content promotion patch v2 applied")


if __name__ == "__main__":
    main()
