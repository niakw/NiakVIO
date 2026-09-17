import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "guard",
    ROOT / "scripts" / "validate_domain_refresh_static_non_destructive.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

before = {
    "schemaVersion": 1,
    "providerCount": 2,
    "providers": {
        "flemmix": {
            "model": {
                "officialSite": "https://flemmix.cloud",
                "knownSite": "https://flemmix.cloud",
                "officialHub": "https://ww1.wiflix-adresses.fun/",
                "strategy": "mixed_embed_resolver",
                "origins": ["https://flemmix.cloud", "https://player.example"],
                "observedUrls": ["https://flemmix.cloud/search?q=x"],
                "apiRecipe": {"base": "https://api.example", "referer": "https://flemmix.cloud/", "movieRoute": "/m/{id}"},
                "routeData": [{"origin": "https://flemmix.cloud", "status": 200}],
            }
        },
        "other": {"model": {"officialSite": "https://other.example", "strategy": "x", "routeData": []}},
    },
}
after = copy.deepcopy(before)
fm = after["providers"]["flemmix"]["model"]
fm["officialSite"] = "https://flemmix.party"
fm["knownSite"] = "https://flemmix.party"
fm["origins"][0] = "https://flemmix.party"
fm["observedUrls"][0] = "https://flemmix.party/search?q=x"
fm["apiRecipe"]["referer"] = "https://flemmix.party/"
mod.validate(before, after, {"flemmix"})

bad = copy.deepcopy(after)
bad["providers"]["other"]["model"]["officialSite"] = "https://oops.example"
try:
    mod.validate(before, bad, {"flemmix"})
except AssertionError as exc:
    assert "untouched static knowledge" in str(exc)
else:
    raise AssertionError("untouched provider mutation should fail")

bad = copy.deepcopy(after)
bad["providers"]["flemmix"]["model"]["strategy"] = "changed"
try:
    mod.validate(before, bad, {"flemmix"})
except AssertionError as exc:
    assert "non-address static model" in str(exc) or "strategy" in str(exc)
else:
    raise AssertionError("strategy mutation should fail")

bad = copy.deepcopy(after)
bad["providers"]["flemmix"]["model"]["routeData"][0]["status"] = 403
try:
    mod.validate(before, bad, {"flemmix"})
except AssertionError as exc:
    assert "non-address static model" in str(exc) or "routeData" in str(exc)
else:
    raise AssertionError("route proof mutation should fail")

print("domain refresh static non-destructive guard passed")
