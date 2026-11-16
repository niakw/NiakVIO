#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_platform_runtime_policy.py"
spec = importlib.util.spec_from_file_location("validate_platform_runtime_policy", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

main_doc = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf_doc = json.loads((ROOT / "vf" / "manifest.json").read_text(encoding="utf-8"))
catalogue_doc = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
matrix = json.loads((ROOT / "automation" / "platform-runtime-matrix.json").read_text(encoding="utf-8"))
policy = json.loads((ROOT / "automation" / "platform-runtime-policy.json").read_text(encoding="utf-8"))

main_rows = module.rows(main_doc)
vf_rows = module.rows(vf_doc)
catalogue = module.catalog_rows(catalogue_doc)

france_only = sorted(set(vf_rows) - set(main_rows))
assert france_only, "production must retain first-class France-only identities"
for provider_id in france_only:
    record = catalogue[provider_id]
    assert record["projections"]["general"] is False, provider_id
    assert record["projections"]["vf"] is True, provider_id

errors: list[str] = []
module.validate_projection_authority(errors, main_rows, vf_rows, catalogue)
assert errors == [], errors

errors = []
module.validate_platform_evidence_authority(
    errors,
    matrix,
    policy,
    str(main_doc["version"]),
    main_rows,
)
assert errors == [], errors
assert matrix["authority"] == "historical-evidence-only"
assert policy["authority"] == "historical-evidence-only"
assert policy["managed_platform_tokens_by_provider"] == {}
assert policy["classifications"] == {}
assert str(policy["source_release"]) != str(main_doc["version"])

# Historical evidence must never regain current provider authority.
bad_policy = json.loads(json.dumps(policy))
bad_policy["managed_platform_tokens_by_provider"] = {"example": ["android"]}
errors = []
module.validate_platform_evidence_authority(
    errors,
    matrix,
    bad_policy,
    str(main_doc["version"]),
    main_rows,
)
assert any("historical platform policy cannot manage current providers" in value for value in errors), errors

print(
    "PLATFORM_RUNTIME_PROJECTION_AUTHORITY_OK "
    f"global={len(main_rows)} vf={len(vf_rows)} france_only={len(france_only)} "
    "historical_matrix_non_authoritative=true"
)
