#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "automation/evidence/hub-lab-matrix-46.json"
data = json.loads(SCOPE.read_text(encoding="utf-8"))
rows = data.get("rows") or []
ids = {
    str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
    for row in rows if isinstance(row, dict)
    if str(row.get("manifestId") or row.get("provider") or "").strip()
}
declared = int(data.get("hubCount") or 0)
assert declared > 0, declared
assert len(ids) == declared, (len(ids), declared)

os.environ["NIAKVIO_PROVIDER_SCOPE_MATRIX"] = "automation/evidence/hub-lab-matrix-46.json"
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_native_corpus_client as client  # noqa: E402
assert client.provider_scope_ids() == ids

# Historical September Hub-44 rows must not resurrect providers removed from
# the current 41-provider published manifest. Preserve historical evidence in
# the matrix while staging every current provider, with an explicit audit log.
current_manifest = json.loads((ROOT / "native-hub46/manifest.json").read_text(encoding="utf-8"))
current_ids = {
    str(row.get("id") or "").strip().casefold()
    for row in current_manifest.get("scrapers", [])
    if isinstance(row, dict) and row.get("enabled") is True
}
assert current_ids <= ids, sorted(current_ids - ids)
assert ids - current_ids == {"animetsu", "showbox", "videasy"}
staged = client.manifest_providers("native-hub46/manifest.json")
assert {row["id"].casefold() for row in staged} == current_ids
assert len(staged) == len(current_ids)

# A fixed/targeted scope remains strict; a dynamic historical scope must not
# hide a CURRENT provider absent from the allowlist.
with tempfile.TemporaryDirectory(prefix=".native-scope-contract-", dir=ROOT) as tmp:
    scope_file = Path(tmp) / "scope.json"
    selected = sorted(current_ids)[0]
    scope = {
        "hubCount": 2,
        "rows": [{"manifestId": selected}, {"manifestId": "archived-synthetic-provider"}],
    }
    try:
        os.environ["NIAKVIO_PROVIDER_SCOPE_MATRIX"] = str(scope_file)
        scope_file.write_text(json.dumps(scope), encoding="utf-8")
        try:
            client.manifest_providers("native-hub46/manifest.json")
        except SystemExit as error:
            assert "absent from manifest" in str(error), error
        else:
            raise AssertionError("fixed scope unexpectedly accepted stale provider")

        scope["scopePolicy"] = "dynamic-active-hub-authority"
        scope_file.write_text(json.dumps(scope), encoding="utf-8")
        try:
            client.manifest_providers("native-hub46/manifest.json")
        except SystemExit as error:
            assert "omits current enabled provider(s)" in str(error), error
        else:
            raise AssertionError("dynamic scope unexpectedly dropped current providers")
    finally:
        os.environ["NIAKVIO_PROVIDER_SCOPE_MATRIX"] = "automation/evidence/hub-lab-matrix-46.json"

spec = importlib.util.spec_from_file_location("native_gate", ROOT / "scripts/gate_native_declared_provider_matrix.py")
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
assert gate.load_scope_ids(SCOPE) == ids

source = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
assert "scopeProviderIds" in source
assert "provider_scope_ids()" in source
assert "scopeProviderIds.isEmpty() || it.id.lowercase() in scopeProviderIds" in source

workflow_paths = (
    ROOT / ".github/workflows/native-desktop-reader-acceptance.yml",
    ROOT / ".github/workflows/native-mobile-android-reader.yml",
    ROOT / ".github/workflows/native-mobile-ios-reader.yml",
)
legacy_fixed_trio = "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"
for workflow in workflow_paths:
    text = workflow.read_text(encoding="utf-8")
    assert "NIAKVIO_PROVIDER_SCOPE_MATRIX: automation/evidence/hub-lab-matrix-46.json" in text, workflow
    assert "--scope-matrix" in text, workflow
    assert "automation/evidence/hub-lab-matrix-46.json" in text, workflow
    assert legacy_fixed_trio not in text, workflow

assert "rotating_corpus.py" in workflow_paths[0].read_text(encoding="utf-8")
assert "FIELD_ROTATING_CORPUS client=tv" in workflow_paths[1].read_text(encoding="utf-8")
assert "FIELD_ROTATING_CORPUS client=mobile" in workflow_paths[1].read_text(encoding="utf-8")

print(f"native active-scope rotating execution contract tests passed: providers={declared} workflows=3")
