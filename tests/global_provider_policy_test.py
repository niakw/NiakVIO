#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "apply_provider_overrides_global", ROOT / "scripts" / "apply_provider_overrides.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
cat = cfg["catalogue_resolution_policy"]
media = cfg["media_enrichment_policy"]
assert cat["enabled"] is True and cat["id_first"] is True
assert cat["tmdb_and_imdb_first"] is True
assert cat["version"] == 3
assert cat["provider_specific_titles_forbidden"] is True
assert set(cat["capabilities"]) == {"html_scraper", "mixed_embed_resolver"}
assert media["enabled"] is True and media["transcoding"] is False
assert media["preserve_original"] is True

cat_source = (ROOT / cat["global_discovery_hook"]).read_text(encoding="utf-8")
media_source = (ROOT / media["global_discovery_hook"]).read_text(encoding="utf-8")
for token in (
    "alternative_titles",
    "original_title",
    "external_source=imdb_id",
    "/find/",
    "language=en-US",
    "nativeIdentityReject",
    "q.tmdbId",
):
    assert token in cat_source, token
for forbidden in ("Mon ninja et moi 3", "Interstellar", "Ternet Ninja 3"):
    assert forbidden not in cat_source, forbidden
for token in ("preserveOriginal", "m3u8|mpd|mp4|m4v|mkv|webm|ts", "kindBytes", "add(row)"):
    assert token in media_source, token

# A configured HTML provider receives both global behaviours automatically.
future = b"async function getStreams(){return []};module.exports={getStreams};"
patched, records = module.apply_overrides("kurage", future, phase="discovery")
text = patched.decode("utf-8")
assert "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2" in text
assert "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1" in text
scopes = {row.get("scope") for row in records if isinstance(row, dict)}
assert "global_catalogue_resolution" in scopes
assert "global_media_enrichment" in scopes

# A slow HTML catalogue may lower the shared bounds without replacing the
# global ID-first engine or hard-coding work-specific titles.
papa, _papa_records = module.apply_overrides("papadustream", future, phase="discovery")
papa_text = papa.decode("utf-8")
assert '"timeoutMs":4000' in papa_text
assert '"budgetMs":25000' in papa_text
assert papa_text.count("NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:") == 1

# Direct-media providers remain ID-native; they may be inspected/protected but
# are never rewritten into a title-search catalogue flow.
direct, direct_records = module.apply_overrides("zinkmovies", future, phase="discovery")
assert b"NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2" not in direct
assert not any(
    row.get("scope") == "global_catalogue_resolution"
    for row in direct_records
    if isinstance(row, dict)
)

health = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))
activation = health["activation"]
assert activation["minimum_effective_height"] == 0
assert activation["minimum_bandwidth_bps_when_reported"] == 0
assert activation["require_accepted_language_evidence"] is False
assert activation["quality_auto_disable"] is False
assert health["modes"]["deep"]["fallback_fixture_limit_per_category"] == 3

audit = (ROOT / "scripts" / "audit_catalogue_identity_media.py").read_text(encoding="utf-8")
assert "Mon ninja et moi 3" in audit
assert "1215638" in audit

health_source = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")
assert "let fallbackExecuted = false;" in health_source
assert "fallbackExecuted = true;" in health_source
assert "useFallback" not in health_source

print("global ID-first catalogue/media and broad activation policy tests passed")
