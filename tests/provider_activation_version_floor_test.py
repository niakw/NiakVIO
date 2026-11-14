#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"activate_bulk_proven_providers.py"
spec=importlib.util.spec_from_file_location("activate_bulk_proven_providers_version_floor_test",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

payload={"schema_version":1,"providers":{}}
row={"id":"new-provider","version":"1.0.0"}
result=mod.ensure_activation_version_floor("new-provider",row,payload)
assert result["seeded"] is True
assert result["bumped"] is False
assert result["floor"]=="0.0.0"
assert row["version"]=="1.0.0"
assert payload["providers"]["new-provider"]=="0.0.0"

payload={"schema_version":1,"providers":{"historical":"1.2.9"}}
row={"id":"historical","version":"1.2.4"}
result=mod.ensure_activation_version_floor("historical",row,payload)
assert result["seeded"] is False
assert result["bumped"] is True
assert row["version"]=="1.2.10"

payload={"schema_version":1,"providers":{"ahead":"1.0.4"}}
row={"id":"ahead","version":"1.0.8"}
result=mod.ensure_activation_version_floor("ahead",row,payload)
assert result["bumped"] is False
assert row["version"]=="1.0.8"

offline=(ROOT/"scripts"/"activate_bulk_offline_proven_providers.py").read_text(encoding="utf-8")
assert "ensure_activation_version_floor" in offline
assert "write(VERSION_FLOORS, version_floor_payload)" in offline

print("provider activation version-floor contract passed: first exposure seeded and historical rollback bumped")
