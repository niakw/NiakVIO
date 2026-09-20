#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

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

source = path.read_text(encoding="utf-8")
for forbidden in ("cf_clearance", "turnstile token", "captcha solver", "undetected_chromedriver", "cloudscraper", "flaresolverr"):
    assert forbidden not in source.casefold(), forbidden

print("provider WAF ordinary-browser-session diagnostic contract passed")
