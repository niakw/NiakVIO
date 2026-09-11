#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"

data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
patches = data.setdefault("provider_patches", {})
caps = data.setdefault("provider_capabilities", {})
patch = patches.setdefault("anidb", {})
cap = caps.setdefault("anidb", {})

patch["official_site"] = "https://anidb.app"
patch["capability"] = "mixed_embed_resolver"
patch["identity_input"] = {
    "mode": "catalog_search",
    "required_fields": ["title", "mediaType"],
    "requires_tmdb_before_run": True,
}
patch["runtime_domain_replacements"] = {}
patch["domain_substitutions"] = {"anidb.pics": "anidb.app"}
legos = [str(v) for v in patch.get("provider_lego_scripts") or [] if str(v).strip()]
script = "scripts/provider_patches/anidb_runtime_v1.py"
if script not in legos:
    legos.append(script)
patch["provider_lego_scripts"] = legos
notes = [str(v) for v in patch.get("notes") or [] if str(v).strip()]
for note in (
    "AniDB.app uses canonical-anime title search -> anime id -> episodes -> languages -> embed -> HLS; do not treat it as a direct TMDB API.",
    "anidb.pics is historical/stale execution knowledge; current execution authority is https://anidb.app. The configured hub remains discovery-only.",
):
    if note not in notes:
        notes.append(note)
patch["notes"] = notes

cap["strategy"] = "mixed_embed_resolver"
cap["allow_html_url"] = True
cap["requires_direct_media"] = False
cap["validation"] = "provider_native"
origins = [
    str(v) for v in cap.get("observed_origins") or []
    if str(v).strip() and "old.invalid" not in str(v) and "anidb.pics" not in str(v)
]
if "https://anidb.app" not in origins:
    origins.insert(0, "https://anidb.app")
cap["observed_origins"] = origins
OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# The one-provider materializer treats the enriched static model as current
# authority and intentionally projects it over historical overrides. Therefore
# a reviewed domain migration must update both structured authority stores in
# the same transaction; otherwise static knowledge silently resurrects the old
# site during materialization.
knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
providers = knowledge.setdefault("providers", {})
row = providers.setdefault("anidb", {})
model = row.setdefault("model", {})
model["knownSite"] = "https://anidb.app"
model["officialSite"] = "https://anidb.app"
model["strategy"] = "mixed_embed_resolver"
model["identityInput"] = {
    "mode": "catalog_search",
    "requiredFields": ["title", "mediaType"],
    "requiresTmdbBeforeRun": True,
}
model["domainSubstitutions"] = {"anidb.pics": "anidb.app"}
model["runtimeDomainReplacements"] = {}
static_origins = [
    str(v) for v in model.get("origins") or []
    if str(v).strip() and "anidb.pics" not in str(v)
]
if "https://anidb.app" not in static_origins:
    static_origins.insert(0, "https://anidb.app")
model["origins"] = static_origins
observed = [
    str(v) for v in model.get("observedUrls") or []
    if str(v).strip() and "anidb.pics" not in str(v)
]
if "https://anidb.app/" not in observed:
    observed.insert(0, "https://anidb.app/")
model["observedUrls"] = observed
KNOWLEDGE.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(
    "ANIDB_RUNTIME_DATA_STAGED official_site=anidb.app static_authority=anidb.app "
    "strategy=mixed_embed_resolver lego=1 activation_unchanged=1"
)
