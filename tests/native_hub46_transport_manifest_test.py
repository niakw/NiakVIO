#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_hub46_native_manifest.py"

spec = importlib.util.spec_from_file_location("build_hub46_native_manifest", BUILDER)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

scope_data = json.loads((ROOT / "automation/evidence/hub-lab-matrix-46.json").read_text(encoding="utf-8"))
scope = {
    module.cid(row.get("manifestId") or row.get("provider"))
    for row in scope_data["rows"]
}
assert len(scope) == 46

source = json.loads((ROOT / "manifest-hub46.json").read_text(encoding="utf-8"))
provider_sha = "1" * 40
payload = module.build(
    source,
    scoped=scope,
    repository="niakw/NiakVIO",
    provider_sha=provider_sha,
    verify_git=False,
)
rows = payload.get("scrapers") or []
assert len(rows) == len(scope)
assert {module.cid(row.get("id")) for row in rows} == scope
for row in rows:
    filename = str(row.get("filename") or "")
    prefix = f"https://raw.githubusercontent.com/niakw/NiakVIO/{provider_sha}/providers/"
    assert filename.startswith(prefix), (row.get("id"), filename)
    assert ".." not in filename

# A nested transport path is intentional: official Nuvio code strips the literal
# terminal '/manifest.json'. Absolute provider URLs then remain independent of the
# transport directory base.
assert Path("native-hub46/manifest.json").name == "manifest.json"

# The resolver must allow a tracked nested manifest to use pinned GitHub HTTPS.
resolver = (ROOT / "scripts/resolve_native_repository.sh").read_text(encoding="utf-8")
assert '[[ "$TARGET_MANIFEST" != */* ]]' not in resolver, "nested tracked manifests must remain SHA-pinnable"
assert 'git -C "$NIAKVIO" cat-file -e "$SOURCE_SHA:$TARGET_MANIFEST"' in resolver
assert 'mode=pinned_github' in resolver

# The three suite families and iOS workflow must point to the terminal-name-safe
# Hub-46 transport when the 46 campaign is active.
for path in (
    ROOT / "scripts/run_native_corpus_desktop_suite.sh",
    ROOT / "scripts/run_native_corpus_mobile_suite.sh",
    ROOT / "scripts/run_native_corpus_tv_suite.sh",
):
    text = path.read_text(encoding="utf-8")
    assert 'native-hub46/manifest.json' in text, path
    assert 'TARGET_MANIFEST="manifest-hub46.json"' not in text, path

# Android prebuild must resolve the same physical manifest before QEMU. Historical
# workflow env values may still say manifest.json; the shared prebuild layer owns
# the scope switch and may not resolve the 96-provider root repository instead.
prebuild = (ROOT / "scripts/prebuild_native_android_reader_suite.sh").read_text(encoding="utf-8")
assert "NATIVE_ANDROID_HUB46_PREBUILD_V1" in prebuild
assert 'TARGET_MANIFEST="native-hub46/manifest.json"' in prebuild
assert "phase=prebuild" in prebuild

ios = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
assert "/native-hub46/manifest.json" in ios
assert "/${{ github.sha }}/manifest.json" not in ios

print("NATIVE_HUB46_TRANSPORT_MANIFEST_OK providers=46 terminal=manifest.json pinned_provider_urls=true android_prebuild=nested")
