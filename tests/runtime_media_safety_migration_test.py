#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "scripts/provider_patches/runtime_media_safety_migration_v1.py"
SAFETY = ROOT / "scripts/provider_patches/hls_master_audio_preserver_v1.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = load("runtime_media_safety_migration", MIGRATION)
safety = load("runtime_media_safety", SAFETY)
base = "module.exports={getStreams:async()=>[{url:'https://media.example/master.m3u8',type:'hls'}]};\n"

current = safety.apply(base, context={"provider_id": "streamzo"})
assert '"implementationRevision":"field-safety-v3-native-aware"' in current
assert current.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1

legacy = current.replace(
    '"implementationRevision":"field-safety-v3-native-aware"',
    '"implementationRevision":"field-safety-v2"',
)
migrated = migration.apply(legacy, context={"provider_id": "streamzo"})
assert "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:" not in migrated
assert "NUVIO_RUNTIME_MEDIA_SAFETY_MIGRATION_V1" in migrated

reapplied = safety.apply(migrated, context={"provider_id": "streamzo"})
assert reapplied.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v3-native-aware"' in reapplied
assert '"implementationRevision":"field-safety-v2"' not in reapplied

# Re-running the configured migration + current patch must be byte-stable.
second = safety.apply(migration.apply(reapplied, context={"provider_id": "streamzo"}), context={"provider_id": "streamzo"})
assert second == reapplied

print("runtime media safety migration tests passed")
