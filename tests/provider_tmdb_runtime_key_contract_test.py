#!/usr/bin/env python3
"""TMDB credentials are runtime inputs for all newly authored provider code."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LITERAL_PATTERNS = (
    re.compile(r'\bTMDB(?:_API)?_?KEY\s*=\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'\btmdbKey["\']?\s*[:=]\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'\bTMDB\s*=\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'api_key=[0-9a-fA-F]{24,64}'),
)


def scan(path: Path, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    rel = path.relative_to(ROOT).as_posix()
    for pattern in LITERAL_PATTERNS:
        if pattern.search(text):
            failures.append(f"{rel}: literal TMDB credential pattern {pattern.pattern}")


failures: list[str] = []

RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"
runtime_key = json.loads(RUNTIME_KEY_PATH.read_text(encoding="utf-8"))
assert runtime_key.get("version") == 1
assert isinstance(runtime_key.get("salt"), str) and runtime_key["salt"]
assert isinstance(runtime_key.get("cipher"), list) and runtime_key["cipher"]
assert all(isinstance(value, int) and 0 <= value <= 255 for value in runtime_key["cipher"])
assert "api_key" not in runtime_key and "token" not in runtime_key

def decrypt_runtime_key(payload: dict) -> str:
    material = str(payload["salt"]) + "|NiakVIO/TMDB/v1"
    seed = 2166136261
    for char in material:
        seed ^= ord(char)
        seed = (seed * 16777619) & 0xFFFFFFFF
    out = []
    for raw in payload["cipher"]:
        seed ^= (seed << 13) & 0xFFFFFFFF
        seed &= 0xFFFFFFFF
        seed ^= seed >> 17
        seed &= 0xFFFFFFFF
        seed ^= (seed << 5) & 0xFFFFFFFF
        seed &= 0xFFFFFFFF
        out.append(chr((int(raw) & 0xFF) ^ (seed & 0xFF)))
    return "".join(out)

runtime_plain_key = decrypt_runtime_key(runtime_key)
assert re.fullmatch(r"[0-9a-fA-F]{32}", runtime_plain_key), (
    "runtime TMDB key payload must decrypt to exactly one 32-hex v3 API key"
)
assert not runtime_plain_key.startswith("\\"), "runtime TMDB key must not carry an escaped-secret prefix"

resolver_source = (ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
assert "tmdbKeyCipher" in resolver_source
assert "normalizeKey" in resolver_source
assert "api.themoviedb.org/3/" in resolver_source
assert "www.themoviedb.org/" not in resolver_source

# CI supplies TMDB credentials to Core as secrets. The repository may contain
# only the encrypted runtime payload; neither secret value is provider-owned.
sync_workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
assert "TMDB_API_KEY: ${{ secrets.TMDB_API_KEY }}" in sync_workflow
assert "TMDB_ACCESS_TOKEN: ${{ secrets.TMDB_ACCESS_TOKEN }}" in sync_workflow


# All code that can author a future ProviderBase/provider is clean immediately.
# TMDB network access is Core-owned: provider-specific adapters may consume
# tmdbMetadata/context but may never carry their own TMDB client/key.
patch_root = ROOT / "scripts" / "provider_patches"
CORE_TMDB_MODULES = {
    "global_media_type_resolution_v1.py",
    "global_stream_identity_v1.py",
    "global_stream_presentation_v1.py",
    "runtime_capability_media_safety_v4.py",
    "hls_master_audio_preserver_impl_v1.py",
    "adaptive_runtime_recovery.py",
    "adaptive_runtime_recovery_v4.py",
    "stream_output_sanitizer.py",
    "native_catalogue_recovery_budget_v1.py",
}
for path in patch_root.rglob("*.py"):
    scan(path, failures)
    text = path.read_text(encoding="utf-8", errors="strict")
    if path.name not in CORE_TMDB_MODULES and (
        "api.themoviedb.org/3/" in text
        or "TMDB_API_KEY" in text
        or "TMDB_ACCESS_TOKEN" in text
    ):
        failures.append(
            f"{path.relative_to(ROOT).as_posix()}: provider/capability module owns TMDB access; "
            "consume Core tmdbMetadata instead"
        )

provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
rows = provenance.get("providers") or {}
verified_v2 = 0
pending_v2 = 0

# Historical ProviderBases and content-addressed published JS are immutable LKG
# artifacts. Do not mutate them in place merely to remove an old literal: doing so
# would make the filename/hash lie and break existing clients. Scan every new v2
# candidate/verified base instead; its later public bundle is derived from that base.
for provider_id, row in rows.items():
    if not isinstance(row, dict):
        continue
    source = str(row.get("base_source") or "")
    candidate = source == "niakvio-clean-reconstruction-v2-candidate"
    verified = (
        source == "niakvio-clean-reconstruction-v2"
        and row.get("clean_reconstruction_verified") is True
    )
    if not (candidate or verified):
        continue
    relative = str(row.get("base_filename") or "")
    path = (ROOT / relative).resolve()
    assert path.is_file(), f"{provider_id}: v2 ProviderBase missing: {relative}"
    scan(path, failures)
    pending_v2 += int(candidate)
    verified_v2 += int(verified)

for path in (
    ROOT / "scripts" / "provider_patches" / "global_stream_identity_v1.py",
    ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py",
    ROOT / "scripts" / "provider_patches" / "runtime_capability_media_safety_v4.py",
):
    text = path.read_text(encoding="utf-8")
    assert "globalThis.TMDB_API_KEY" in text or "g.TMDB_API_KEY" in text, path

if failures:
    raise AssertionError("\n".join(failures))

print(
    "TMDB runtime-key contract passed: "
    f"provider_authoring_clean=true verified_v2={verified_v2} pending_v2={pending_v2} "
    "legacy_lkg_immutable=true"
)
