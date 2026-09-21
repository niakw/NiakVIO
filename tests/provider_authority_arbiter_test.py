#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/classify_provider_authority.py"
spec=importlib.util.spec_from_file_location("authority",SCRIPT)
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def row(enabled=True):
    return {"id":"demo","enabled":enabled}

def reg(**kw):
    base={"sources":[],"search_queries":[],"direct":None}
    base.update(kw)
    return base

def patch(**kw):
    base={"capability":"html_scraper","manifest_overrides":{"enabled":True}}
    base.update(kw)
    return base

# Search is supplementary: a site-dependent provider with only search is not
# allowed to burn Repair cycles before address authority is established.
r=module.classify("demo",row(),reg(search_queries=["demo official"],legacy_search_refresh=True),patch(),{})
assert r["action"]=="REDISCOVER_SEARCH",r
assert r["repairEligible"] is False

# Two persisted Domain failures convert unresolved site identity to a safe off
# decision; one transient failure does not.
r=module.classify("demo",row(),reg(search_queries=["demo"]),patch(),{"authority_failures":{"consecutive":1}})
assert r["action"]=="REDISCOVER_SEARCH",r
r=module.classify("demo",row(),reg(search_queries=["demo"]),patch(),{"authority_failures":{"consecutive":2}})
assert r["action"]=="DISABLE_AUTHORITY_EXHAUSTED",r

# API/backends are independent from a homepage/hub when structured authority is
# explicit. This is the PersianStremio/YFlix class.
r=module.classify(
    "demo",row(),reg(search_queries=["demo"]),
    patch(capability="api_stream_resolver",official_api="https://api.example.test",
          learned_routes=["/stream/movie/{id}.json"]),
    {"authority_failures":{"consecutive":9}},
)
assert r["action"]=="KEEP_BACKEND",r
assert r["repairEligible"] is True

# A removed authoritative directory source is stronger negative evidence than
# search noise for a site-dependent provider.
r=module.classify(
    "demo",row(),
    reg(sources=[{"type":"hub","url":"https://directory.example/demo","source_status":"removed"}]),
    patch(),
    {},
)
assert r["action"]=="DISABLE_SOURCE_REMOVED",r

# Explicit-current direct is usable while fresh observations do not contradict
# it, but repeated failures first force rediscovery and then safe disable.
direct=reg(direct="https://demo.example/",direct_authority="explicit_current")
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":0}})
assert r["action"]=="KEEP_DIRECT",r
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":2}})
assert r["action"]=="REDISCOVER_DIRECT",r
r=module.classify("demo",row(),direct,patch(),{"authority_failures":{"consecutive":3}})
assert r["action"]=="DISABLE_AUTHORITY_EXHAUSTED",r

# Existing manual lifecycle decisions remain terminal.
r=module.classify("demo",row(False),reg(),patch(manual_off_reason="manual_off_test"),{})
assert r["action"]=="KEEP_DISABLED",r

assert module.ROOT.joinpath("scripts/manage_provider_lifecycle.py").read_text(encoding="utf-8").find("RETENTION_DAYS = 7")>=0
print("provider authority arbiter contract ok")
