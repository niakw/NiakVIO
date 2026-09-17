import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "static_authority",
    ROOT / "scripts" / "reconcile_domain_refresh_static_authority.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

model = {
    "knownSite": "https://flemmix.cloud",
    "officialSite": "https://flemmix.cloud",
    "officialHub": "https://ww1.wiflix-adresses.fun/",
    "officialApi": None,
    "origins": [
        "https://flemmix.cloud",
        "https://arm.haglund.dev",
        "https://player.example",
    ],
    "observedUrls": ["https://flemmix.cloud/search?q=test"],
    "apiRecipe": {
        "base": "https://arm.haglund.dev",
        "referer": "https://flemmix.cloud/",
        "movieRoute": "/api/v2/themoviedb?id={tmdbId}",
    },
    "routeData": [
        {
            "origin": "https://flemmix.cloud",
            "route": "/search?q={query}",
            "status": 200,
        }
    ],
}
patch = {
    "official_site": "https://flemmix.party",
    "official_hub": "https://ww1.wiflix-adresses.fun/",
}
route_data_before = repr(model["routeData"])
fields = mod.sync_model(model, patch)

assert model["officialSite"] == "https://flemmix.party"
assert model["knownSite"] == "https://flemmix.party"
assert model["officialHub"] == "https://ww1.wiflix-adresses.fun/"
assert model["apiRecipe"]["base"] == "https://arm.haglund.dev"
assert model["apiRecipe"]["referer"] == "https://flemmix.party/"
assert model["origins"][0] == "https://flemmix.party"
assert "https://arm.haglund.dev" in model["origins"]
assert model["observedUrls"] == ["https://flemmix.party/search?q=test"]
assert repr(model["routeData"]) == route_data_before, "route proof evidence must remain untouched"
assert {"officialSite", "knownSite", "origins", "observedUrls", "apiRecipe.referer"} <= set(fields)

# Idempotence is mandatory: once aligned, a second pass must be a no-op.
assert mod.sync_model(model, patch) == []

print("domain refresh static authority test passed: current terminal wins, route proof preserved, idempotent")
