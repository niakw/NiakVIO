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
assert revision == "cross-client-player-page-identity-v20-url-path-consistency-v21-all-coordinates", revision
assert "function exactSpecialEpisodeEvidence(row,q)" in source
assert "function keepEpisodeBoundSubtitles(row,q,m)" in source
assert "function subtitleContradictsEpisode(sub,q,m)" in source
assert "function mediaUrlEpisodeContradicts(row,q)" in source
assert "if(!exactSpecialEpisodeEvidence(row,q))return true" in source

manifests = (ROOT / "manifest.json", ROOT / "vf/manifest.json",
             ROOT / "no-anime/manifest.json", ROOT / "vf-no-anime/manifest.json")
missing = []
seen = set()
active_count = 0
disabled_count = 0
for manifest_path in manifests:
    rows = json.loads(manifest_path.read_text(encoding="utf-8")).get("scrapers")
    assert isinstance(rows, list) and rows, (manifest_path, "no providers")
    manifest_seen = set()
    for entry in rows:
        assert isinstance(entry, dict), "invalid published provider row"
        provider_id = str(entry.get("id") or "")
        filename = str(entry.get("filename") or "")
        relative = Path(filename)
        enabled = entry.get("enabled") is not False
        expected_folder = "providers/" if enabled else "provider-disabled/"
        path = (manifest_path.parent / relative).resolve()
        expected_parent = (ROOT / expected_folder).resolve()
        assert not relative.is_absolute() and path.parent == expected_parent, (
            manifest_path.name, provider_id, filename, enabled
        )
        assert path not in manifest_seen, ("duplicate visible provider artifact", filename)
        manifest_seen.add(path)
        assert path.is_file(), ("visible provider artifact missing", filename)
        key = (path, enabled)
        if key in seen:
            continue
        seen.add(key)
        if not enabled:
            disabled_count += 1
            continue
        active_count += 1
        text = path.read_text(encoding="utf-8")
        if (revision not in text
                or "function exactSpecialEpisodeEvidence(row,q)" not in text
                or "function keepEpisodeBoundSubtitles(row,q,m)" not in text
                or "function subtitleContradictsEpisode(sub,q,m)" not in text
                or "function mediaUrlEpisodeContradicts(row,q)" not in text
                or "function episodeCoordinateContradicts(v,q)" not in text
                or "function explicitQueryEpisodeContradicts(params,q)" not in text
                or text.count("STARTFIX:CORE.STREAM_IDENTITY.V1") != 1
                or text.count("CLOSEFIX:CORE.STREAM_IDENTITY.V1") != 1):
            missing.append((str(manifest_path.relative_to(ROOT)), provider_id or filename))

assert not missing, (
    f"stale S00 identity Core on {len(missing)}/{active_count} active providers: "
    f"{missing[:12]}; reapply managed Core and verify release bytes"
)
print(
    f"FIELD_S00_PUBLISHED_CORE_REVISION verified={active_count} retained_disabled={disabled_count} "
    f"revision={revision} static_parity_only=true decoded_playback_proven=false"
)
