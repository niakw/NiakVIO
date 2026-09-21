#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/merge_residential_provider_replay.py"
spec=importlib.util.spec_from_file_location("merge_residential_replay",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

waf={"rows":[{"provider":"yflix","lane":"movie"}]}
replay={
    "providers":["yflix"],
    "raw_providers":["yflix"],
    "playable_providers":["yflix"],
    "verified_providers":["yflix"],
    "wrong_content_providers":[],
    "rows":[{
        "provider_id":"yflix","semantic_type":"movie","status":"OK",
        "debug_stage":"provider_returned_streams","raw":2,"playable":1,"verified":1,
        "contradictions":0,"identity_safe":True,
        "debug_fetches":[{"url":"https://private.example/?token=must-not-persist"}],
    }],
    "machine":"must-not-persist",
    "publicIp":"203.0.113.99",
}
merged=mod.merge(waf,replay)
summary=merged["residentialProviderReplay"]
assert summary["verifiedProviders"]==["yflix"],summary
assert summary["rows"][0]["verified"]==1,summary
assert summary["rows"][0]["identitySafe"] is True,summary
serialized=repr(merged)
assert "must-not-persist" not in serialized
assert "203.0.113.99" not in serialized
assert "debug_fetches" not in serialized
assert summary["privacy"]["residentialPublicIpPersisted"] is False

print("residential full-provider replay privacy contract passed")
