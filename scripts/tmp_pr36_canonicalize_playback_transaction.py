#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFETY = ROOT / "scripts/provider_patches/hls_master_audio_preserver_v1.py"
INTEGRITY = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
REGRESSION = ROOT / "tests/scoped_playback_context_regression_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"{label}: expected source block not found")
    return text.replace(old, new, 1)


def patch_safety() -> None:
    text = SAFETY.read_text(encoding="utf-8")
    old = '''    marker = f"{SAFETY_MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    if f"/* {marker} */" in output:
        return output

    output = _strip_existing_safety_wrapper(output)
'''
    new = '''    marker = f"{SAFETY_MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    marker_comment = f"/* {marker} */"
    current = output.find(marker_comment)
    if current >= 0:
        later_global_layers = (
            output.find("/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:", current + 1),
            output.find("/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:", current + 1),
        )
        if not any(position >= 0 for position in later_global_layers):
            return output

    output = _strip_existing_safety_wrapper(output)
'''
    SAFETY.write_text(replace_once(text, old, new, "runtime safety canonicalization"), encoding="utf-8")


def patch_integrity() -> None:
    text = INTEGRITY.read_text(encoding="utf-8")
    old = '''    marker = f"{MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    if marker in text:
        return text

    old = text.find(f"/* {MARKER}:")
'''
    new = '''    marker = f"{MARKER}:{hashlib.sha256(payload.encode()).hexdigest()[:12]}"
    marker_comment = f"/* {marker} */"
    current = text.find(marker_comment)
    final_layers = [
        position
        for position in (
            text.find("/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:"),
            text.find("/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:"),
        )
        if position >= 0
    ]
    if current >= 0 and (not final_layers or current < min(final_layers)):
        return text

    old = text.find(f"/* {MARKER}:")
'''
    text = replace_once(text, old, new, "HLS integrity canonicalization")
    old_tail = '''    return text.rstrip() + "\\n" + wrapper
'''
    new_tail = '''    final_layers = [
        position
        for position in (
            text.find("/* NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1:"),
            text.find("/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:"),
        )
        if position >= 0
    ]
    if final_layers:
        insertion = min(final_layers)
        return (
            text[:insertion].rstrip()
            + "\\n"
            + wrapper.rstrip()
            + "\\n"
            + text[insertion:].lstrip()
        )
    return text.rstrip() + "\\n" + wrapper
'''
    INTEGRITY.write_text(replace_once(text, old_tail, new_tail, "HLS integrity insertion"), encoding="utf-8")


def patch_regression() -> None:
    text = REGRESSION.read_text(encoding="utf-8")
    loader = 'media_apply = load_apply("scripts/provider_patches/global_media_enrichment_v1.py")\n'
    if 'hls_runtime_apply = load_apply("scripts/provider_patches/hls_runtime_integrity_v1.py")' not in text:
        if loader not in text:
            raise SystemExit("regression loader insertion point missing")
        text = text.replace(
            loader,
            loader + 'hls_runtime_apply = load_apply("scripts/provider_patches/hls_runtime_integrity_v1.py")\n',
            1,
        )
    if "Canonical global playback order is HLS integrity" not in text:
        anchor = 'assert \'"defaultUserAgent":"UA-STREAMZO-2"\' in changed_context\n'
        if anchor not in text:
            raise SystemExit("regression canonical-order insertion point missing")
        block = r'''

# Canonical global playback order is HLS integrity -> enrichment -> final
# safety. Applying the normal discovery/playback sequence must reach that order
# in one transaction and remain byte-for-byte stable on the next application.
canonical = media_apply(base, options={"default_user_agent":"UA-STREAMZO"})
canonical = hls_apply(canonical, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
canonical = hls_runtime_apply(canonical, options={"probe_all_urls": True, "fail_closed_unknown": False})
hls_pos = canonical.index("NUVIO_HLS_RUNTIME_INTEGRITY_V1")
media_pos = canonical.index("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1")
safety_pos = canonical.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
assert hls_pos < media_pos < safety_pos, (hls_pos, media_pos, safety_pos)
canonical_again = media_apply(canonical, options={"default_user_agent":"UA-STREAMZO"})
canonical_again = hls_apply(canonical_again, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
canonical_again = hls_runtime_apply(canonical_again, options={"probe_all_urls": True, "fail_closed_unknown": False})
assert canonical_again == canonical
'''
        text = text.replace(anchor, anchor + block, 1)
    REGRESSION.write_text(text, encoding="utf-8")


def set_streamzo_version(version: str) -> None:
    for relative in ("manifest.json", "vf/manifest.json"):
        path = ROOT / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        found = False
        for row in data.get("scrapers") or []:
            if str(row.get("id") or "").casefold() == "streamzo":
                row["version"] = version
                found = True
        if not found:
            raise SystemExit(f"StreamZo missing from {relative}")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def streamzo_row() -> dict:
    data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    return next(row for row in data["scrapers"] if str(row.get("id") or "").casefold() == "streamzo")


def assert_bundle_order(filename: str) -> None:
    path = ROOT / filename
    text = path.read_text(encoding="utf-8")
    hls = text.index("NUVIO_HLS_RUNTIME_INTEGRITY_V1")
    media = text.index("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1")
    safety = text.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
    if not hls < media < safety:
        raise SystemExit(f"non-canonical wrapper order: hls={hls} media={media} safety={safety}")


def prepare() -> None:
    patch_safety()
    patch_integrity()
    patch_regression()
    set_streamzo_version("1.0.45")
    print("PR36 source canonicalization prepared; StreamZo baseline normalized to 1.0.45")


def verify_rematerialized() -> None:
    row = streamzo_row()
    if row.get("version") != "1.0.46":
        raise SystemExit(f"unexpected StreamZo version after one transaction: {row.get('version')}")
    if "37a7acf1cb409c20" in str(row.get("filename") or ""):
        raise SystemExit("stale double-rematerialized StreamZo bundle still referenced")
    assert_bundle_order(str(row["filename"]))
    print(f"canonical StreamZo generation verified: version={row['version']} file={row['filename']}")


def verify_release() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    vf = json.loads((ROOT / "vf/manifest.json").read_text(encoding="utf-8"))
    row = streamzo_row()
    expected = "5.20.57"
    versions = (package.get("version"), manifest.get("version"), vf.get("version"))
    if versions != (expected, expected, expected):
        raise SystemExit(f"release versions not synchronized to {expected}: {versions}")
    if row.get("version") != "1.0.46":
        raise SystemExit(f"unexpected final StreamZo version: {row.get('version')}")
    assert_bundle_order(str(row["filename"]))
    print(f"final release verified: global={expected} streamzo={row['version']} file={row['filename']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify-rematerialized", "verify-release"))
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "verify-rematerialized":
        verify_rematerialized()
    else:
        verify_release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
