#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import refresh_authoritative_hub_domains as refresh

identity = (ROOT / "scripts/provider_patches/global_stream_identity_v1.py").read_text(encoding="utf-8")
assert "cross-client-shared-tv-year-soft-v8" in identity
assert "q.seriesYear=Number(q.seriesYear||q.series_year||q.year||0)||0" in identity
assert "q.seasonYear=Number(q.seasonYear||q.season_year||0)||0" in identity
assert "if(!episodic(q)&&m.year&&years.length" in identity
assert "if(m.year&&years.length&&!years.some" not in identity

patch = {
    "official_site": "https://flemmix.kim",
    "notes": ["active flemmix.men mirror"],
    "domain_substitutions": {"flemmix.casa": "flemmix.men"},
    "replacements": {"flemmix.men": "flemmix.kim"},
    "runtime_domain_replacements": {"flemmix.men": "flemmix.kim"},
    "manifest_overrides": {"logo": "https://flemmix.men/favicon.ico"},
}
changes = refresh._reconcile_domain_derivatives(patch, "https://flemmix.kim", "https://flemmix.kim")
assert patch["domain_substitutions"]["flemmix.casa"] == "flemmix.kim", patch
assert patch["manifest_overrides"]["logo"] == "https://flemmix.kim/favicon.ico", patch
assert changes

data = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
flemmix = data["provider_patches"]["flemmix"]
assert flemmix["official_site"] == "https://flemmix.kim"
assert all(value != "flemmix.men" for value in flemmix.get("domain_substitutions", {}).values())
assert flemmix["domain_substitutions"].get("flemmix.men") == "flemmix.kim"
assert str(flemmix.get("manifest_overrides", {}).get("logo") or "").startswith("https://flemmix.kim/")
assert all("active domain is flemmix.men" not in str(note) for note in flemmix.get("notes", []))

print("priority TV-year/domain-refresh regression tests passed")