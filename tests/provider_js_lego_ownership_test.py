#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
EXPECTED = 96

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
assert len(rows) == EXPECTED, len(rows)

forbidden_bundle_tokens = (
    "strictIdentityScore",
    "function routeIdentity(",
    "wrong_release_year",
    "season_episode_identity_mismatch",
    "collisionFixtures",
)

for row in rows:
    provider_id = str(row.get("id") or "").strip().casefold()
    filename = str(row.get("filename") or "").strip()
    assert provider_id and filename, row
    path = ROOT / filename
    assert path.is_file(), (provider_id, filename)
    text = path.read_text(encoding="utf-8")

    # Published Provider v3 composition is strictly:
    # common ProviderBase + structured CONFIG/DATA + Provider Lego + Core Lego.
    assert text.count("NIAKVIO_PROVIDER_BASE_OWNED_V3") == 1, provider_id
    assert text.count("const NIAKVIO_PROVIDER_MODEL = Object.freeze(") == 1, provider_id
    assert text.count("/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */") == 1, provider_id
    assert text.count("STARTFIX:CORE.STREAM_IDENTITY.V1") == 1, provider_id
    assert text.count("CLOSEFIX:CORE.STREAM_IDENTITY.V1") == 1, provider_id
    assert "__nuvioIdentityPolicyV1" in text, provider_id

    for token in forbidden_bundle_tokens:
        assert token not in text, (provider_id, token)

# Provider-specific diagnostic adapters may map provider DATA shapes, but they
# cannot own a separate title/type/year acceptance algorithm.
for path in sorted((ROOT / "engine_v2" / "providers").glob("*.mjs")):
    text = path.read_text(encoding="utf-8")
    assert "strictIdentityScore" not in text, path
    assert "routeIdentity(" not in text, path
    assert "wrong_release_year" not in text, path
    assert "season_episode_identity_mismatch" not in text, path
    assert not re.search(r"Math\.abs\([^\n]{0,100}(?:year|Year)", text), path

# Runtime media safety is media/playability-only. Identity lives in STREAM_IDENTITY.
safety = (ROOT / "scripts" / "provider_patches" / "runtime_capability_media_safety_v4.py").read_text(encoding="utf-8")
for token in (
    "routeIdentity(",
    "identityBlob(",
    "explicitYears(",
    "wrong_release_year",
    "season_episode_identity_mismatch",
    "collisionFixtures",
):
    assert token not in safety, token
assert "field-safety-v8-media-only-p2p-vod-duration" in safety

# ProviderBase can transport identity evidence, but it delegates all acceptance
# semantics to the Core policy and cannot keep year rejection/scoring locally.
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
assert "__nuvioIdentityPolicyV1" in base
assert "Math.abs(Number(year) - Number(expectedYear))" not in base
assert 'if (year && expectedYear && year !== expectedYear) return -1;' not in base

print("Provider JS Lego ownership tests passed: providers=96 identity_owner=CORE.STREAM_IDENTITY.V1")
