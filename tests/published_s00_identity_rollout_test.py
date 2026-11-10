#!/usr/bin/env python3
"""Release-only gate: no stale S00 identity Core bytes may be published.

This runs AFTER the release pipeline re-applies managed Core Lego. A source
regression test alone cannot establish that existing provider bundles contain
the corrected guard. Static parity is necessary, not decoded-playback proof.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/provider_patches/global_stream_identity_v1.py"
MANIFEST = ROOT / "manifest.json"

source = SOURCE.read_text(encoding="utf-8")
match = re.search(r'"implementationRevision":\s*"([^"]+)"', source)
assert match, "Core identity implementation revision missing"
revision = match.group(1)
assert revision == "cross-client-player-page-identity-v20-url-path-consistency", revision
assert "function exactSpecialEpisodeEvidence(row,q)" in source
assert "function keepEpisodeBoundSubtitles(row,q,m)" in source
assert "function subtitleContradictsEpisode(sub,q,m)" in source
assert "function mediaUrlEpisodeContradicts(row,q)" in source
assert "if(!exactSpecialEpisodeEvidence(row,q))return true" in source

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
rows = manifest.get("scrapers")
assert isinstance(rows, list) and rows, "release manifest has no providers"
missing = []
seen = set()
for entry in rows:
    assert isinstance(entry, dict), "invalid published provider row"
    provider_id = str(entry.get("id") or "")
    filename = str(entry.get("filename") or "")
    relative = Path(filename)
    assert (filename.startswith("providers/") and not relative.is_absolute()
            and ".." not in relative.parts and len(relative.parts) == 2), (
        provider_id, filename
    )
    assert filename not in seen, ("duplicate published provider", filename)
    seen.add(filename)
    path = ROOT / relative
    assert path.is_file(), ("published provider missing", filename)
    text = path.read_text(encoding="utf-8")
    if (revision not in text
            or "function exactSpecialEpisodeEvidence(row,q)" not in text
            or "function keepEpisodeBoundSubtitles(row,q,m)" not in text
            or "function subtitleContradictsEpisode(sub,q,m)" not in text
            or "function mediaUrlEpisodeContradicts(row,q)" not in text
            or text.count("STARTFIX:CORE.STREAM_IDENTITY.V1") != 1
            or text.count("CLOSEFIX:CORE.STREAM_IDENTITY.V1") != 1):
        missing.append(provider_id or filename)

assert not missing, (
    f"stale S00 identity Core on {len(missing)}/{len(rows)} published providers: "
    f"{missing[:12]}; reapply managed Core and verify release bytes"
)
print(
    f"FIELD_S00_PUBLISHED_CORE_REVISION verified={len(rows)} "
    "revision=v19 static_parity_only=true decoded_playback_proven=false"
)
