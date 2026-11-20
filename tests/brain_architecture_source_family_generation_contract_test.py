#!/usr/bin/env python3
"""Novel source family must leave the exhausted recoveryProgram generator."""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/brain_architecture_force_materializer.py"
spec = importlib.util.spec_from_file_location("brain_force_source_family", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

blueprint = {
    "strategyId": "catalogue_inline_token_episode_source_family_v1",
    "gapKind": "missing_source_contract_family_executable",
    "targetLayer": "brain",
    "requiresNewExecutableRepairProfile": False,
    "requiresNewSourceFamilyLego": True,
    "providers": ["source-family-representative"],
}
payload = {
    "blueprint": blueprint, "allowedPaths": [
        "scripts/brain_repair_runtime.py", "scripts/brain_layers/*", "tests/brain_*",
    ],
    "sources": {"scripts/brain_repair_runtime.py": "def update_plans():\n    pass\n"},
    "contract": {"publicationAllowed": False},
}
assert mod._requires_new_source_family_lego(payload)
assert not mod._requires_new_repair_profile(payload)
assert not mod._requires_new_source_family_lego({
    **blueprint, "requiresNewSourceFamilyLego": False,
})
assert mod._requires_new_repair_profile({
    "blueprint": {
        "strategyId": "old_exhausted_route_v24",
        "requiresNewExecutableRepairProfile": True,
    }
})
typed_program = {
    "sourceFamilyProgram": {
        "moduleCode": "def parse_episode_source(html, episode):\n    return {}\n",
        "runtimeFind": "source_text = source_bytes.decode",
        "runtimeReplace": "source_text = source_bytes.decode",
        "testCode": "assert 'eps1' and 'eps2' and 'lien:'\n",
    },
}
typed_edits = mod._model_edits(typed_program, payload)
assert [row["operation"] for row in typed_edits] == ["create", "replace", "create"]
assert typed_edits[1]["path"] == "scripts/brain_repair_runtime.py"
assert typed_edits[0]["path"].startswith("scripts/brain_layers/")
assert typed_edits[2]["path"].startswith("tests/brain_")
try:
    mod._model_edits({"edits": [
        {"operation": "create", "path": "scripts/brain_repair_runtime.py", "content": "pass"}
    ]}, payload)
except ValueError as exc:
    assert "typed sourceFamilyProgram" in str(exc)
else:
    raise AssertionError("live source-family compiler accepted untyped filesystem operations")
try:
    mod._model_edits({"recoveryProgram": {"searchSources": ["peer"]}}, payload)
except ValueError as exc:
    assert "legacy route recoveryProgram" in str(exc)
else:
    raise AssertionError("new source family accepted old route program")

class FakeHTTP(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()
        return False

captured = {}
def fake_urlopen(request, timeout):
    body = json.loads(request.data.decode("utf-8"))
    captured.update(body)
    assert timeout == 5
    return FakeHTTP(json.dumps({
        "choices": [{"message": {"content": json.dumps({
            "sourceFamilyProgram": typed_program["sourceFamilyProgram"],
        })}}]
    }).encode("utf-8"))
with patch.object(mod, "urlopen", fake_urlopen):
    response = mod._model_request(
        "http://127.0.0.1:9999", "qwen2.5-coder-7b",
        payload, max_tokens=100, timeout=5, compact=True,
    )
assert response["choices"]
schema_props = captured["response_format"]["schema"]["properties"]
assert "sourceFamilyProgram" in schema_props
assert "edits" not in schema_props and "recoveryProgram" not in schema_props
typed_fields = schema_props["sourceFamilyProgram"]["properties"]
assert set(typed_fields) == {"moduleCode", "runtimeFind", "runtimeReplace", "testCode"}
assert captured["response_format"]["schema"]["required"] == ["sourceFamilyProgram"]
assert "file paths or create/replace operations" in captured["messages"][0]["content"]
assert "NEW SOURCE FAMILY" in captured["messages"][0]["content"]
assert "The old recoveryProgram" in captured["messages"][0]["content"]
assert captured["messages"][1]["content"].find("source-family-representative") >= 0

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    layer = root / "scripts/brain_layers/source_family_sample.py"
    runtime = root / "scripts/brain_repair_runtime.py"
    test_file = root / "tests/brain_source_family_sample_test.py"
    layer.parent.mkdir(parents=True)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    test_file.parent.mkdir(parents=True)
    layer.write_text(
        "import json\nimport re\n"
        "def parse_episode_source(html, episode):\n"
        "    out = {}\n"
        "    for slot, vals in re.findall(r'var (eps[0-9]+) = (\\[[^]]+\\]);', html):\n"
        "        out[slot] = json.loads(vals)[episode - 1]\n"
        "    return out\n",
        encoding="utf-8",
    )
    runtime.write_text(
        "def _current_source_structural_repair_evidence(html, episode):\n"
        "    from brain_layers.source_family_sample import parse_episode_source\n"
        "    return parse_episode_source(html, episode)\n",
        encoding="utf-8",
    )
    test_file.write_text(
        "from brain_layers.source_family_sample import parse_episode_source\n"
        "html = '<script>var eps1 = [\"lien:a1\",\"lien:a2\"];"
        "var eps2 = [\"lien:b1\",\"lien:b2\"];</script>'\n"
        "assert parse_episode_source(html, 1) == {'eps1':'lien:a1','eps2':'lien:b1'}\n"
        "assert parse_episode_source(html, 2) == {'eps1':'lien:a2','eps2':'lien:b2'}\n",
        encoding="utf-8",
    )
    paths = [
        "scripts/brain_layers/source_family_sample.py",
        "scripts/brain_repair_runtime.py",
        "tests/brain_source_family_sample_test.py",
    ]
    mod.validate_source_family_implementation(paths, blueprint, root=root)
    # A model-authored test with no meaningful fixture must not certify an
    # incorrect parser. The Brain-owned independent two-index oracle blocks it.
    valid_layer = layer.read_text(encoding="utf-8")
    valid_test = test_file.read_text(encoding="utf-8")
    test_file.write_text("assert True\n", encoding="utf-8")
    layer.write_text(
        "def parse_episode_source(html, episode):\n"
        "    return {'eps1': 'lien:LEGOTEST_ALPHA_1', "
        "'eps2': 'lien:LEGOTEST_BETA_1'}\n",
        encoding="utf-8",
    )
    try:
        mod.validate_source_family_implementation(paths, blueprint, root=root)
    except ValueError as exc:
        assert "source-family independent episode oracle failed" in str(exc)
    else:
        raise AssertionError("vacuous Qwen test let a one-episode parser pass")
    layer.write_text(valid_layer, encoding="utf-8")
    test_file.write_text(valid_test, encoding="utf-8")
    mod.validate_source_family_implementation(paths, blueprint, root=root)
    try:
        mod.validate_source_family_implementation(paths[:2], blueprint, root=root)
    except ValueError as exc:
        assert "3 executable edits" in str(exc)
    else:
        raise AssertionError("orphan test bypassed source-family validator")
    runtime.write_text("def update_plans():\n    return {}\n", encoding="utf-8")
    try:
        mod.validate_source_family_implementation(paths, blueprint, root=root)
    except ValueError as exc:
        assert "orphaned" in str(exc)
    else:
        raise AssertionError("unwired Brain module accepted")
    runtime.write_text(
        "def update_plans(html, episode):\n"
        "    from brain_layers.source_family_sample import parse_episode_source\n"
        "    return parse_episode_source(html, episode)\n", encoding="utf-8",
    )
    layer.write_text("import subprocess\ndef parse_episode_source(html, episode): return {}\n",encoding="utf-8")
    try:
        mod.validate_source_family_implementation(paths, blueprint, root=root)
    except ValueError as exc:
        assert "pure parser primitives" in str(exc)
    else:
        raise AssertionError("network/process import bypassed validator")
    layer.write_text("def parse_episode_source(html, episode): return {}\n",encoding="utf-8")
    try:
        mod.validate_source_family_implementation(paths, blueprint, root=root)
    except ValueError as exc:
        assert "synthetic parser replay failed" in str(exc)
    else:
        raise AssertionError("fake non-parser module passed synthetic replay")

desc = mod._program_provenance({
    "edits": [
        {"operation": "create", "path": "scripts/brain_layers/a.py",
         "content": "def parse_episode_source(html, episode): return {}"},
        {"operation": "replace", "path": "scripts/brain_repair_runtime.py",
         "replace": "from brain_layers.a import parse_episode_source"},
    ]
}, blueprint)
assert desc["generatorFormat"] == "source-family-brain-allowlisted-edits"
assert desc["generatedSourceFamilyLego"] is True
assert desc["providerMutationAuthority"] is False
assert desc["nativePlaybackAuthority"] is False
assert len(desc["programFingerprint"]) == 64
assert all("contentSha256" in entry and len(entry["contentSha256"]) == 64
           for entry in desc["editDescriptors"])
assert "parse_episode_source(html" not in json.dumps(desc)
print("Source-family Brain FORCE mode: typed program compiled into 3 deterministic edits, actual wired parser test and hostile negatives passed")
