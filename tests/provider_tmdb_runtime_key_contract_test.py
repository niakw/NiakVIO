#!/usr/bin/env python3
"""TMDB credentials are Core runtime inputs and are never embedded in provider artifacts."""
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

# The former encrypted repository payload was deliberately retired. Runtime
# credentials are supplied by CI/host context and captured once inside the Core
# closure; downstream provider logic consumes metadata only.
RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"
assert not RUNTIME_KEY_PATH.exists(), "embedded TMDB runtime-key payload must stay retired"

resolver_path = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
resolver_source = resolver_path.read_text(encoding="utf-8")
for forbidden in (
    "RUNTIME_KEY_PATH",
    "tmdbKeyCipher",
    "tmdbKeySalt",
    "function embeddedKey",
    "normalizeKey(embeddedKey())",
    "NiakVIO/TMDB/v1",
):
    assert forbidden not in resolver_source, forbidden
for required in (
    "normalizeKey",
    "function localKey()",
    "function localToken()",
    "var coreCredentialKey=localKey(),coreCredentialToken=localToken();",
    "g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData",
    "api.themoviedb.org/3/",
):
    assert required in resolver_source, required
assert "www.themoviedb.org/" not in resolver_source

# Validate ownership semantically rather than pinning one historical apiJson line:
# request-time TMDB access uses the closure-captured credentials and must never
# re-read host globals or reconstruct a repository-embedded secret.
api_start = resolver_source.index("async function apiJson(url){")
api_end = resolver_source.index("\nasync function findTmdb(", api_start)
api_body = resolver_source[api_start:api_end]
assert "coreCredentialKey" in api_body and "coreCredentialToken" in api_body
assert "localKey()" not in api_body and "localToken()" not in api_body
assert "tmdbKeyCipher" not in api_body and "tmdbKeySalt" not in api_body
assert "embeddedKey" not in api_body

# CI supplies credentials only to Core/runtime execution. No plaintext secret is
# committed and provider business logic receives metadata rather than credentials.
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

# Downstream Core/ProviderBase consumers must request metadata through the Core
# capability; they must not depend on the retired encrypted payload.
provider_base_source = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
presentation_source = (patch_root / "global_stream_presentation_v1.py").read_text(encoding="utf-8")
assert "__nuvioCoreGetTmdbDataV1" in provider_base_source
assert "__nuvioCoreGetTmdbDataV1" in presentation_source

if failures:
    raise AssertionError("\n".join(failures))

print(
    "TMDB Core credential contract passed: "
    f"embedded_runtime_key=false provider_authoring_clean=true verified_v2={verified_v2} "
    f"pending_v2={pending_v2} legacy_lkg_immutable=true"
)
