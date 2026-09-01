#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import _apply_fixed_endpoint, _fixed_endpoint_fix_id
from provider_patch_blocks import (
    decode_managed_data,
    render_managed_fix,
    strip_all_managed_fixes,
    validate_managed_fixes,
)


source = (
    'const before="keep";\n'
    'function detectPurstreamDomain(){return fetch("https://registry.example/domain").then(r=>r.json());}\n'
    'const after="keep-too";\n'
)
config_v1 = {
    "fixed_endpoint": {
        "resolver_function": "detectPurstreamDomain",
        "api": "https://api.purstream.example/api/v1",
        "referer": "https://purstream.example/",
    }
}

first, record = _apply_fixed_endpoint(source, "purstream", config_v1)
assert record is not None
fix_id = _fixed_endpoint_fix_id("purstream", "detectPurstreamDomain")
assert record["fix_id"] == fix_id
assert first.count(f"/* START NIAKVIO_FIX:{fix_id} */") == 1
assert first.count(f"/* END NIAKVIO_FIX:{fix_id} */") == 1
assert validate_managed_fixes(first) == [fix_id]

data = decode_managed_data(first, fix_id)
assert data["provider_id"] == "purstream"
assert data["restore_source_kind"] == "provider_base"
assert data["restore_source"] in source
assert data["api"] == config_v1["fixed_endpoint"]["api"]

same, same_record = _apply_fixed_endpoint(first, "purstream", config_v1)
assert same == first
assert same_record is None

config_v2 = {
    "fixed_endpoint": {
        "resolver_function": "detectPurstreamDomain",
        "api": "https://api2.purstream.example/api/v2",
        "referer": "https://purstream2.example/",
    }
}
second, second_record = _apply_fixed_endpoint(first, "purstream", config_v2)
assert second_record is not None
assert second.count(f"/* START NIAKVIO_FIX:{fix_id} */") == 1
assert second.count(f"/* END NIAKVIO_FIX:{fix_id} */") == 1
second_data = decode_managed_data(second, fix_id)
assert second_data["api"] == config_v2["fixed_endpoint"]["api"]
assert second_data["referer"] == config_v2["fixed_endpoint"]["referer"]
assert second_data["restore_source"] == data["restore_source"]
assert second_data["restore_source_kind"] == "provider_base"

restored, removed = strip_all_managed_fixes(
    second,
    restore_replaced_source=True,
    require_provider_base_restore=True,
)
assert removed == [fix_id]
assert restored == source

append_only = render_managed_fix(
    "CORE.TEST.APPEND.V1",
    "globalThis.__niakvioTest=true;",
    data={"revision": 1},
)
bundle = source.rstrip() + "\n" + append_only + "\n"
clean, ids = strip_all_managed_fixes(bundle, require_provider_base_restore=True)
assert ids == ["CORE.TEST.APPEND.V1"]
assert clean.rstrip() == source.rstrip()

malformed = first + f"\n/* START NIAKVIO_FIX:{fix_id} */\n"
try:
    validate_managed_fixes(malformed)
except ValueError:
    pass
else:
    raise AssertionError("duplicate START marker must fail closed")

legacy_source = (
    'function detectPurstreamDomain(){'
    '/* NUVIO_FIXED_ENDPOINT:https://legacy.example/api */'
    'return Promise.resolve({api:"https://legacy.example/api",referer:"https://legacy.example/"});'
    '}'
)
legacy_managed, legacy_record = _apply_fixed_endpoint(legacy_source, "purstream", config_v2)
assert legacy_record is not None
legacy_data = decode_managed_data(legacy_managed, fix_id)
assert legacy_data["restore_source_kind"] == "legacy_fixed_endpoint"
try:
    strip_all_managed_fixes(
        legacy_managed,
        restore_replaced_source=True,
        require_provider_base_restore=True,
    )
except ValueError:
    pass
else:
    raise AssertionError("legacy fixed endpoint must never seed ProviderBase")

print("managed provider fix Lego contract passed")
