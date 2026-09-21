#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT/"scripts").resolve()))

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

resolver=load_module("resolver",ROOT/"scripts/resolve_provider_hubs.py")
refresh=load_module("refresh",ROOT/"scripts/refresh_authoritative_hub_domains.py")

history={}
resolver.update_history_row(history,{"status":"direct_unresolved","reason":"no terminal"})
assert history["authority_failures"]["consecutive"]==1,history
resolver.update_history_row(history,{"status":"inconclusive","reason":"timeout"})
assert history["authority_failures"]["consecutive"]==2,history
resolver.update_history_row(history,{
    "status":"site_validated",
    "official_site":"https://demo.example",
    "selected_source_type":"redirect",
    "selected_source":"https://old.demo.example",
})
assert "authority_failures" not in history,history
assert history["current"]["url"]=="https://demo.example"

assert refresh.has_domain_refresh_source(
    {"search_queries":["demo official"],"legacy_search_refresh":True},
    "quick",
) is True
assert refresh.has_domain_refresh_source(
    {"search_queries":["demo official"]},
    "quick",
) is False
assert refresh.has_domain_refresh_source(
    {"search_queries":["demo official"]},
    "deep",
) is True

removed={
    "hub":"https://directory.example/demo",
    "hub_status":"removed",
    "sources":[{
        "type":"hub",
        "url":"https://directory.example/demo",
        "source_status":"removed",
    }],
}
assert resolver.has_authoritative_hub_source(removed) is False

registry=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))
providers=registry["providers"]
assert providers["fullanime"]["legacy_search_refresh"] is True
assert providers["fullanime"]["manifest_status"]=="Désactivé"
assert providers["animetsu"]["hub_status"]=="removed"
assert providers["animetsu"]["activation_eligible"] is False
assert providers["persianstremio"]["direct_authority"]=="structured_runtime_seed"
assert providers["showbox"]["legacy_search_refresh"] is True
assert providers["animesultra"]["legacy_search_refresh"] is True

source=(ROOT/"scripts/resolve_provider_hubs.py").read_text(encoding="utf-8")
assert '"score": 22 - min(index, 10)' in source
assert '"score": 62 - min(index, 10)' in source
assert "DOMAIN_AUTHORITY_FAILURE_MEMORY_V1" in source
print("provider domain authority memory contract ok")
