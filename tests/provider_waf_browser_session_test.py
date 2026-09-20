#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "probe_waf_browser_session.py"
spec = importlib.util.spec_from_file_location("probe_waf_browser_session", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

report = {
    "rows": [
        {
            "provider_id": "allwish",
            "semantic_type": "movie",
            "debug_stage": "provider_waf_challenge",
            "debug_fetches": [
                {"url": "https://all-wish.me/filter?keyword=Interstellar", "method": "GET", "status": 403, "challenge": "cloudflare"},
            ],
        },
        {
            "provider_id": "vostfree",
            "semantic_type": "anime",
            "debug_stage": "provider_waf_challenge",
            "debug_fetches": [
                {"url": "https://ipv4.vostfree.ws/", "method": "GET", "status": 403, "challenge": "cloudflare"},
                {"url": "https://ipv4.vostfree.ws/index.php?do=search", "method": "POST", "status": 403, "challenge": "cloudflare"},
            ],
        },
        {
            "provider_id": "healthy",
            "semantic_type": "movie",
            "debug_stage": "provider_returned_streams",
            "debug_fetches": [],
        },
    ]
}


prior_targets = mod.extract_targets({
    "rows": [{
        "provider": "persisted",
        "lane": "movie",
        "publicUrl": "https://persisted.example/challenge?secret=drop",
        "method": "GET",
        "fetchStatus": 403,
        "challenge": "cloudflare",
        "outcome": "browser_challenge_persisted",
    }]
})
assert len(prior_targets) == 1, prior_targets
assert prior_targets[0]["provider"] == "persisted"
assert prior_targets[0]["publicUrl"] == "https://persisted.example/challenge"

status_targets = mod.extract_status_targets(
    {
        "providers": [
            {
                "provider": "new-waf",
                "status": "PROVIDER WAF/ANTIBOT",
                "declaredLanes": ["movie", "tv"],
            },
            {
                "provider": "healthy",
                "status": "FULL OK",
                "declaredLanes": ["movie"],
            },
        ]
    },
    {
        "provider_patches": {
            "new-waf": {"official_site": "https://new-waf.example/?tracking=drop"},
            "healthy": {"official_site": "https://healthy.example/"},
        }
    },
    [
        {
            "provider": "new-waf",
            "lane": "movie",
            "publicUrl": "https://new-waf.example/",
        }
    ],
)
assert len(status_targets) == 1, status_targets
assert status_targets[0]["provider"] == "new-waf"
assert status_targets[0]["lane"] == "tv"
assert status_targets[0]["publicUrl"] == "https://new-waf.example/"
assert status_targets[0]["seedKind"] == "metadata-homepage"

targets = mod.extract_targets(report)
assert len(targets) == 2, targets
allwish = next(row for row in targets if row["provider"] == "allwish")
assert allwish["publicUrl"] == "https://all-wish.me/filter"
assert "keyword=" not in allwish["publicUrl"]
assert mod.classify_dom("<html><title>Just a moment...</title><div>challenge-platform</div></html>") == "browser_challenge_persisted"
assert mod.classify_dom("<html><body>" + ("normal catalogue content " * 10) + "</body></html>") == "browser_content_reached"
assert mod.classify_dom("<html></html>") == "browser_inconclusive"
assert mod.probe_target(allwish, "", timeout=5, virtual_time_ms=1000)["outcome"] == "browser_unavailable"
vostfree = next(row for row in targets if row["provider"] == "vostfree")
assert vostfree["method"] == "GET", vostfree
assert vostfree["publicUrl"] == "https://ipv4.vostfree.ws/"
assert mod.probe_target(vostfree, "", timeout=5, virtual_time_ms=1000)["outcome"] == "browser_unavailable"


calls=[]
responses=[
    SimpleNamespace(returncode=0,stdout="<html><title>Just a moment...</title><div>challenge-platform</div></html>"),
    SimpleNamespace(returncode=0,stdout="<html><body>"+("normal catalogue content "*10)+"</body></html>"),
]
original_run=mod.subprocess.run
try:
    def fake_run(*args,**kwargs):
        calls.append((args,kwargs))
        return responses.pop(0)
    mod.subprocess.run=fake_run
    warmed=mod.probe_target(allwish,"chromium",timeout=5,virtual_time_ms=1000,attempts=2)
finally:
    mod.subprocess.run=original_run
assert warmed["outcome"]=="browser_content_reached",warmed
assert warmed["attemptCount"]==2,warmed
assert [row["outcome"] for row in warmed["attempts"]]==[
    "browser_challenge_persisted","browser_content_reached"
]
assert warmed["ordinarySessionReused"] is True
assert len(calls)==2
profiles=[
    next(value for value in call[0][0] if str(value).startswith("--user-data-dir="))
    for call in calls
]
assert profiles[0]==profiles[1],profiles

source = path.read_text(encoding="utf-8")
for forbidden in ("cf_clearance", "turnstile token", "captcha solver", "undetected_chromedriver", "cloudscraper", "flaresolverr"):
    assert forbidden not in source.casefold(), forbidden

print("provider WAF ordinary-browser-session diagnostic contract passed")
