#!/usr/bin/env python3
"""TMDB credentials are runtime inputs, never public ProviderBase/provider source."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    ROOT / "scripts" / "provider_patches",
    ROOT / "provider-bases",
)
KNOWN_RETIRED_KEYS = {
    "1865f43a0549ca50d341dd9ab8b29f49",
    "8265bd1679663a7ea12ac168da84d2e8",
    "439c478a771f35c05022f9feabcca01c",
}
LITERAL_PATTERNS = (
    re.compile(r'\bTMDB(?:_API)?_?KEY\s*=\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'\btmdbKey["\']?\s*[:=]\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'\bTMDB\s*=\s*["\'][0-9a-fA-F]{24,64}["\']'),
    re.compile(r'api_key=[0-9a-fA-F]{24,64}'),
)

failures: list[str] = []
for scan_root in SCAN_ROOTS:
    if not scan_root.exists():
        continue
    for path in scan_root.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".js", ".mjs", ".cjs"}:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        rel = path.relative_to(ROOT).as_posix()
        for key in KNOWN_RETIRED_KEYS:
            if key in text:
                failures.append(f"{rel}: retired TMDB key literal {key[:8]}…")
        for pattern in LITERAL_PATTERNS:
            if pattern.search(text):
                failures.append(f"{rel}: literal TMDB credential pattern {pattern.pattern}")

for path in (
    ROOT / "scripts" / "provider_patches" / "global_stream_identity_v1.py",
    ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py",
    ROOT / "scripts" / "provider_patches" / "runtime_capability_media_safety_v4.py",
):
    text = path.read_text(encoding="utf-8")
    assert "globalThis.TMDB_API_KEY" in text or "g.TMDB_API_KEY" in text, path

if failures:
    raise AssertionError("\n".join(failures))

print("TMDB runtime-key contract passed: no literal credential in provider source layers")
