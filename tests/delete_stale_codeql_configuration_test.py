#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "delete_stale_codeql_config",
    ROOT / "scripts/delete_stale_codeql_2531_configuration.py",
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

key = mod.LEGACY_KEY
tool = {"name": "CodeQL"}
legacy_default = {
    "id": 11,
    "analysis_key": key,
    "category": key + "/language:javascript-typescript",
    "environment": '{"language":"javascript-typescript"}',
    "tool": tool,
    "deletable": True,
}
legacy_reconciliation = {
    "id": 12,
    "analysis_key": key,
    "category": key,
    "environment": '{"language":"javascript-typescript"}',
    "tool": tool,
    "deletable": True,
}
current_core = {
    "id": 13,
    "analysis_key": key,
    "category": "/language:javascript-typescript/scope:core",
    "environment": '{"language":"javascript-typescript"}',
    "tool": tool,
    "deletable": True,
}
provider_bases = {
    "id": 14,
    "analysis_key": key,
    "category": "/language:javascript-typescript/scope:provider-bases",
    "environment": '{"language":"javascript-typescript"}',
    "tool": tool,
    "deletable": True,
}
python_old = {
    "id": 15,
    "analysis_key": key,
    "category": key + "/language:python",
    "environment": '{"language":"python"}',
    "tool": tool,
    "deletable": True,
}

found = mod.legacy_js_categories(
    [legacy_default, legacy_reconciliation, current_core, provider_bases, python_old]
)
assert sorted(found) == [key, key + "/language:javascript-typescript"], found
assert current_core not in sum(found.values(), [])
assert provider_bases not in sum(found.values(), [])
assert python_old not in sum(found.values(), [])

sha = "a" * 40
assert mod.is_current_core_analysis({**current_core, "commit_sha": sha}, sha)
assert not mod.is_current_core_analysis({**legacy_default, "commit_sha": sha}, sha)

category = key + "/language:javascript-typescript"
first = {**legacy_default, "id": 21, "deletable": True}
older = {**legacy_default, "id": 20, "deletable": False}
calls = []

def api(path, method="GET", body=None):
    calls.append((path, method, body))
    assert method == "DELETE"
    if path.endswith("/code-scanning/analyses/21"):
        return {
            "next_analysis_url": "https://api.github.com/repos/niakw/NiakVIO/code-scanning/analyses/20",
            "confirm_delete_url": "https://api.github.com/repos/niakw/NiakVIO/code-scanning/analyses/20?confirm_delete=true",
        }
    if path.endswith("/code-scanning/analyses/20?confirm_delete=true"):
        return {}
    raise AssertionError(path)

with patch.object(mod.guard, "api", side_effect=api):
    deleted = mod.delete_category(category, [first, older])

assert deleted == 2
assert calls[0][0].endswith("/code-scanning/analyses/21")
assert "confirm_delete" not in calls[0][0]
assert calls[1][0].endswith("/code-scanning/analyses/20?confirm_delete=true")
assert all(method == "DELETE" for _, method, _ in calls)
assert mod._analysis_delete_path(
    "https://api.github.com/repos/niakw/NiakVIO/code-scanning/analyses/20?confirm_delete=true"
).endswith("/code-scanning/analyses/20?confirm_delete=true")
try:
    mod._analysis_delete_path("https://evil.example/repos/niakw/NiakVIO/code-scanning/analyses/20")
except RuntimeError:
    pass
else:
    raise AssertionError("foreign CodeQL continuation host accepted")

try:
    mod.verify_alert_identity({
        "number": 2531,
        "rule": {"id": "different"},
        "most_recent_instance": {
            "analysis_key": key,
            "location": {"path": "tests/response_structure_test.cjs"},
        },
    })
except RuntimeError:
    pass
else:
    raise AssertionError("wrong CodeQL alert identity was accepted")

print("CODEQL_STALE_CONFIGURATION_DELETE_CONTRACT_OK")
