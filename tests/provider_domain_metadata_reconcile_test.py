#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_provider_domain_metadata import reconcile_patch

patch = {
    "official_site": "https://flemmix.cloud",
    "manifest_overrides": {
        "logo": "https://flemmix.kim/favicon.ico",
        "icon": "https://cdn.example/flemmix.png",
    },
    "domain_substitutions": {
        "flemmix.men": "flemmix.kim",
        "api.flemmix.men": "api.flemmix.kim",
    },
    "runtime_domain_replacements": {
        "flemmix.kim": "flemmix.cloud",
    },
}
registry = {
    "direct": "https://flemmix.cloud/",
    "direct_candidates": [
        "https://flemmix.cloud/",
        "https://flemmix.kim/",
        "https://flemmix.men/",
    ],
    "allowed_terminal_hosts": ["flemmix.cloud", "flemmix.kim", "flemmix.men"],
}
history = {
    "current": {"url": "https://flemmix.cloud"},
    "previous": [{"url": "https://flemmix.kim"}],
}

changed = reconcile_patch("flemmix", patch, registry, history)
assert "manifest_overrides.logo" in changed
assert patch["manifest_overrides"]["logo"] == "https://flemmix.cloud/favicon.ico"
# External/CDN assets are not provider-domain metadata and must stay untouched.
assert patch["manifest_overrides"]["icon"] == "https://cdn.example/flemmix.png"
assert patch["domain_substitutions"]["flemmix.men"] == "flemmix.cloud"
# API hosts retain independent API authority.
assert patch["domain_substitutions"]["api.flemmix.men"] == "api.flemmix.kim"
assert "flemmix.cloud" not in patch["runtime_domain_replacements"]


# An explicit-current registry terminal is authoritative over stale Provider DATA.
patch2 = {
    "official_site": "https://old.example",
    "domain_substitutions": {"new.example": "old.example", "older.example": "old.example"},
    "runtime_domain_replacements": {"old.example": "old.example"},
}
registry2 = {
    "direct": "https://new.example/",
    "direct_authority": "explicit_current",
    "direct_candidates": ["https://new.example/", "https://old.example/"],
    "allowed_terminal_hosts": ["new.example", "old.example", "older.example"],
}
changed2 = reconcile_patch("demo", patch2, registry2, {})
assert "official_site" in changed2, changed2
assert patch2["official_site"] == "https://new.example", patch2
assert "new.example" not in patch2["domain_substitutions"], patch2
assert patch2["domain_substitutions"]["older.example"] == "new.example", patch2
assert "new.example" not in patch2["runtime_domain_replacements"], patch2

# Current provider registry authorities must remain provider-local and explicit.
import json
hubs = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))["providers"]
assert hubs["4khdhub"]["direct"] == "https://4khdhub.one/"
assert hubs["4khdhub"]["direct_authority"] == "explicit_current"
assert hubs["wookafr"]["direct"] == "https://wookafr.tel/"
assert hubs["wookafr"]["direct_authority"] == "explicit_current"
assert hubs["hindmoviez"]["direct"] == "https://hindmovie.fit/"
assert hubs["hindmoviez"]["direct_authority"] == "explicit_current"
assert hubs["movieshunt"]["direct"] == "https://movieshunt.run/"
assert hubs["movieshunt"]["direct_authority"] == "explicit_current"
assert hubs["animesalt"]["direct"] == "https://animesalt.cx/"
assert hubs["animesalt"]["direct_authority"] == "explicit_current"
assert hubs["animesalt"]["allowed_terminal_hosts"] == ["animesalt.cx"]
assert "animesalt.link" in hubs["animesalt"]["blocked_hosts"]

# AnimeSama.co is a distinct DLE provider and must never inherit the
# Anime-Sama catalogue terminal through broad alias/domain reconciliation.
assert hubs["animesama-co"]["direct"] == "https://animesama.co/"
assert hubs["animesama-co"]["direct_authority"] == "explicit_current"
assert hubs["animesama-co"]["allowed_terminal_hosts"] == ["animesama.co"]
assert set(hubs["animesama-co"]["aliases"]) == {"animesama-co", "animesama.co"}
assert "animes-sama.fr" in hubs["animesama-co"]["blocked_hosts"]

assert hubs["movieshunt"]["allowed_terminal_hosts"] == ["movieshunt.run"]
assert "movieshunt.ws" in hubs["movieshunt"]["blocked_hosts"]
assert "movieshunt.monster" not in hubs["movieshunt"]["blocked_hosts"]

# Current MoviesHunt executable search must follow the provider's WordPress
# catalogue contract instead of the retired lookup.php JSON endpoint.
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]

asco = overrides["animesama-co"]
assert asco["official_site"] == "https://animesama.co"
assert "api_recipe" not in asco
assert "candidate_api_recipe" not in asco
assert asco["domain_substitutions"].get("animesama.co") is None
assert asco.get("runtime_domain_replacements", {}).get("animesama.co") is None
assert "/template-php/defaut/fetch.php" in asco["learned_routes"]
assert "/anime/{id}-{slug}.html" in asco["learned_routes"]

movieshunt_plan = overrides["movieshunt"]["search_request_plan"]
assert len(movieshunt_plan) == 1, movieshunt_plan
assert movieshunt_plan[0]["base"] == "https://movieshunt.run", movieshunt_plan
assert movieshunt_plan[0]["route"] == "/search.html?q={query}", movieshunt_plan
assert overrides["movieshunt"]["learned_routes"] == ["/search.html?q={query}", "/?s={query}"], overrides["movieshunt"]["learned_routes"]
assert movieshunt_plan[0]["requestSpec"]["headers"]["Accept"].startswith("text/html"), movieshunt_plan
assert movieshunt_plan[0]["requestSpec"]["headers"]["Referer"] == "https://movieshunt.run/", movieshunt_plan
assert overrides["movieshunt"]["proof_protected_hosts"] == ["movieshunt.run"], overrides["movieshunt"]

assert hubs["voiranime"]["direct"] == "https://voir-anime.to/"
assert hubs["voiranime"]["direct_authority"] == "explicit_current"
assert hubs["voiranime"]["allowed_terminal_hosts"] == ["voir-anime.to"]
assert "voiranime.diy" in hubs["voiranime"]["blocked_hosts"]

print("provider domain metadata reconciliation tests passed")
