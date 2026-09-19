#!/usr/bin/env python3
"""Make HLS duration identity authoritative only for complete VOD playlists.

Bounded probes may intentionally read only a prefix of a large HLS media
playlist. Summing EXTINF values from that prefix proves neither the total
runtime nor a duration contradiction. A duration is authoritative only when
the parsed media playlist includes EXT-X-ENDLIST (or for non-HLS media where
an independent complete duration is available).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TV = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
DIRECT = ROOT / "scripts" / "direct_media_probe.cjs"
LAB = ROOT / "scripts" / "nuvio_client_lab.cjs"
MARKER = "NIAKVIO_HLS_DURATION_COMPLETENESS_V1"


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in text:
        return text, False
    if old not in text:
        raise AssertionError(f"{label}: boundary not found")
    return text.replace(old, new, 1), True


def patch_tv() -> bool:
    text = TV.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    changed = False
    text, c = replace_once(
        text,
        "    media_duration_seconds: null,\n    error: null,",
        "    media_duration_seconds: null,\n    hls_duration_complete: null,\n    error: null,",
        "tv result completeness field",
    ); changed |= c
    text, c = replace_once(
        text,
        "      result.media_duration_seconds = graph.durationSeconds;\n      result.hls_master = graph.variants.length > 0 || /#EXT-X-STREAM-INF\\s*:/i.test(text);",
        "      result.media_duration_seconds = graph.durationSeconds;\n      result.hls_duration_complete = graph.isVod === true;\n      result.hls_master = graph.variants.length > 0 || /#EXT-X-STREAM-INF\\s*:/i.test(text);",
        "tv top hls completeness",
    ); changed |= c
    text, c = replace_once(
        text,
        "        if (Number.isFinite(variant.media_duration_seconds) && variant.media_duration_seconds > 0) {\n          result.media_duration_seconds = variant.media_duration_seconds;\n        }",
        "        if (Number.isFinite(variant.media_duration_seconds) && variant.media_duration_seconds > 0) {\n          result.media_duration_seconds = variant.media_duration_seconds;\n          result.hls_duration_complete = variant.is_vod === true;\n        }",
        "tv variant completeness",
    ); changed |= c
    text, c = replace_once(
        text,
        "    let durationIdentity = { status: 'unknown', reason: 'duration_unavailable', ratio: null };\n    if (expectedSeconds && Number.isFinite(measuredSeconds) && measuredSeconds > 0) {",
        "    const durationComplete = mediaResult?.kind !== 'hls' || mediaResult?.hls_duration_complete === true;\n    let durationIdentity = { status: 'unknown', reason: durationComplete ? 'duration_unavailable' : 'duration_incomplete_hls', ratio: null };\n    /* NIAKVIO_HLS_DURATION_COMPLETENESS_V1 */\n    if (expectedSeconds && durationComplete && Number.isFinite(measuredSeconds) && measuredSeconds > 0) {",
        "tv duration authority",
    ); changed |= c
    TV.write_text(text, encoding="utf-8")
    return changed


def patch_direct() -> bool:
    text = DIRECT.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    changed = False
    text, c = replace_once(
        text,
        "    durationSeconds: durationEntries ? durationSeconds : null,\n  };",
        "    durationSeconds: durationEntries ? durationSeconds : null,\n    complete: lines.some((line) => /^#EXT-X-ENDLIST\\s*$/i.test(line)),\n  };",
        "direct parse completeness",
    ); changed |= c
    text, c = replace_once(
        text,
        "  let videoSegment = null;\n  let mediaDurationSeconds = parsed.durationSeconds;",
        "  let videoSegment = null;\n  let mediaDurationSeconds = parsed.durationSeconds;\n  let mediaDurationComplete = parsed.complete === true;\n  /* NIAKVIO_HLS_DURATION_COMPLETENESS_V1 */",
        "direct duration state",
    ); changed |= c
    text, c = replace_once(
        text,
        "      mediaDurationSeconds = childProbe.media_duration_seconds ?? null;",
        "      mediaDurationSeconds = childProbe.media_duration_seconds ?? null;\n      mediaDurationComplete = childProbe.media_duration_complete === true;",
        "direct child completeness",
    ); changed |= c
    text, c = replace_once(
        text,
        "    media_duration_seconds: mediaDurationSeconds,\n  };",
        "    media_duration_seconds: mediaDurationSeconds,\n    media_duration_complete: mediaDurationComplete,\n  };",
        "direct probe output completeness",
    ); changed |= c
    DIRECT.write_text(text, encoding="utf-8")
    return changed


def patch_lab() -> bool:
    text = LAB.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    changed = False
    text, c = replace_once(
        text,
        "    const durationMismatch = durationRatio != null && (durationRatio < minimumDurationRatio || durationRatio > maximumDurationRatio);\n    if (durationMismatch) identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };\n    else if (identity.status === 'unknown' && durationRatio != null) identity = { status: 'match', reason: 'fixture_duration_match' };",
        "    const durationComplete = probe?.kind !== 'hls' || probe?.media_duration_complete === true;\n    /* NIAKVIO_HLS_DURATION_COMPLETENESS_V1 */\n    const durationMismatch = durationComplete && durationRatio != null && (durationRatio < minimumDurationRatio || durationRatio > maximumDurationRatio);\n    if (durationMismatch) identity = { status: 'contradiction', reason: 'fixture_duration_mismatch' };\n    else if (identity.status === 'unknown' && durationComplete && durationRatio != null) identity = { status: 'match', reason: 'fixture_duration_match' };",
        "lab duration authority",
    ); changed |= c
    text, c = replace_once(
        text,
        "      media_duration_seconds: mediaDurationSeconds,\n      expected_duration_seconds: expectedDurationSeconds,",
        "      media_duration_seconds: mediaDurationSeconds,\n      media_duration_complete: probe?.media_duration_complete ?? null,\n      expected_duration_seconds: expectedDurationSeconds,",
        "lab completeness evidence",
    ); changed |= c
    LAB.write_text(text, encoding="utf-8")
    return changed


def validate() -> None:
    tv = TV.read_text(encoding="utf-8")
    direct = DIRECT.read_text(encoding="utf-8")
    lab = LAB.read_text(encoding="utf-8")
    assert MARKER in tv and "durationComplete" in tv and "hls_duration_complete" in tv
    assert MARKER in direct and "media_duration_complete" in direct and "complete: lines.some" in direct
    assert MARKER in lab and "durationComplete" in lab and "media_duration_complete" in lab


def main() -> int:
    changed = {
        "tv": patch_tv(),
        "direct": patch_direct(),
        "lab": patch_lab(),
    }
    validate()
    print("HLS_DURATION_COMPLETENESS_V1_OK " + " ".join(f"{k}={str(v).lower()}" for k,v in changed.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
