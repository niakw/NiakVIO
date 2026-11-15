#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location("guard", ROOT / "scripts" / "check_direct_manifest_version_bumps.py")
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def manifest(version, rows):
    return {"name": f"NiakVIO v{version}", "version": version, "scrapers": rows}


old = manifest("5.21.10", [
    {"id": "DEMO", "version": "1.0.0", "filename": "providers/demo-old.js", "enabled": True},
])
bad = manifest("5.21.10", [
    {"id": "DEMO", "version": "1.0.0", "filename": "providers/demo-new.js", "enabled": True},
])
errors = module.validate_pair("manifest.json", old, bad)
assert any("manifest changed without release bump" in e for e in errors)
assert any("provider row changed without provider bump" in e for e in errors)

good = manifest("5.21.11", [
    {"id": "DEMO", "version": "1.0.1", "filename": "providers/demo-new.js", "enabled": True},
])
assert module.validate_pair("manifest.json", old, good) == []

old_vf = manifest("5.21.11", [
    {"id": "FRANCE-ONLY", "version": "2.3.4", "filename": "../providers/fr-old.js", "enabled": True},
])
bad_vf = manifest("5.21.11", [
    {"id": "FRANCE-ONLY", "version": "2.3.4", "filename": "../providers/fr-new.js", "enabled": True},
])
errors = module.validate_pair("vf/manifest.json", old_vf, bad_vf)
assert any("manifest changed without release bump" in e for e in errors)
assert any("provider row changed without provider bump" in e for e in errors)

good_vf = manifest("5.21.12", [
    {"id": "FRANCE-ONLY", "version": "2.3.5", "filename": "../providers/fr-new.js", "enabled": True},
])
assert module.validate_pair("vf/manifest.json", old_vf, good_vf) == []

print("direct manifest version bump guard test passed")
