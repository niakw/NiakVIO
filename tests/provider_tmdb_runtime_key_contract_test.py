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

# All code that can author a future ProviderBase/provider is clean immediately.
patch_root = ROOT / "scripts" / "provider_patches"
for path in patch_root.rglob("*.py"):
    scan(path, failures)

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
