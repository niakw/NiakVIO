#!/usr/bin/env python3
"""Novel source family must leave the exhausted recoveryProgram generator."""
from __future__ import annotations

import importlib.util
import io
import hashlib
import json
import subprocess
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
        "runtimeFind": mod.SOURCE_FAMILY_RUNTIME_ANCHOR,
        "runtimeReplace": (
            mod.SOURCE_FAMILY_RUNTIME_ANCHOR
            + "\n        from brain_layers.generated_source import parse_episode_source"
        ),
    },
}
typed_edits = mod._model_edits(typed_program, payload)
assert [row["operation"] for row in typed_edits] == ["create", "replace", "create"]
assert typed_edits[1]["path"] == "scripts/brain_repair_runtime.py"
assert typed_edits[0]["path"].startswith("scripts/brain_layers/")
assert typed_edits[2]["path"].startswith("tests/brain_")
assert "LEGOTEST_ALPHA_1" in typed_edits[2]["content"]
assert "LEGOTEST_BETA_2" in typed_edits[2]["content"]
compile(typed_edits[2]["content"], typed_edits[2]["path"], "exec")
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
assert set(typed_fields) == {"moduleCode", "runtimeFind", "runtimeReplace"}
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
        "    if type(episode) is not int or episode < 1: return []\n"
        "    out = []\n"
        "    for raw in re.findall(r'var eps[0-9]+\\s*=\\s*(\\[[^]]*\\])', html):\n"
        "        values = json.loads(raw)\n"
        "        if episode <= len(values) and values[episode-1]: out.append(values[episode-1])\n"
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
        "assert parse_episode_source(html, 1) == ['lien:a1','lien:b1']\n"
        "assert parse_episode_source(html, 2) == ['lien:a2','lien:b2']\n",
        encoding="utf-8",
    )
    paths = [
        "scripts/brain_layers/source_family_sample.py",
        "scripts/brain_repair_runtime.py",
        "tests/brain_source_family_sample_test.py",
    ]
    mod.validate_source_family_implementation(paths, blueprint, root=root)
    # A parser that mistakes reader rows for episodes mixes adjacent
    # episodes. The independent oracle must reject this old assumption.
    valid_layer = layer.read_text(encoding="utf-8")
    valid_test = test_file.read_text(encoding="utf-8")
    test_file.write_text("assert True\n", encoding="utf-8")
    layer.write_text(
        "import json\nimport re\n"
        "def parse_episode_source(html, episode):\n"
        "    match = re.search(r'var eps' + str(int(episode)) + r'\\s*=\\s*(\\[[^]]+\\])', html)\n"
        "    return json.loads(match.group(1)) if match else []\n",
        encoding="utf-8",
    )
    try:
        mod.validate_source_family_implementation(paths, blueprint, root=root)
    except ValueError as exc:
        assert "source-family independent episode oracle failed" in str(exc)
    else:
        raise AssertionError("vacuous test let a transposed reader-slot parser pass")
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
# Current live contract: the model emits only bounded grammar data, not Python.
matrix_blueprint = {**blueprint, "sourceCompilerContract": "reader-matrix-v2"}
matrix_payload = {**payload, "blueprint": matrix_blueprint}
grammar = {
    "slotPrefix": "eps", "declarations": ["var", "let", "const"],
    "matrixAxis": "reader-slots", "slotOrder": "numeric", "valuePrefix": "lien:",
}
schema = mod._source_family_response_format(matrix_payload)["schema"]["properties"]["sourceFamilyProgram"]
assert set(schema["required"]) == set(grammar)
assert "moduleCode" not in schema["properties"] and "runtimeReplace" not in schema["properties"]
for invalid in ({**grammar, "moduleCode": "eval('1')"},
                {**grammar, "slotPrefix": "x;open()"},
                {**grammar, "valuePrefix": "https:"},
                {**grammar, "declarations": ["import"]},
                {**grammar, "slotPrefix": "episodes"},
                {**grammar, "valuePrefix": "token:"},
                {**grammar, "matrixAxis": "episode-slots"},
                {**grammar, "declarations": ["let", "const"]},
                {**grammar, "slotOrder": "source"}):
    try:
        mod._model_edits({"sourceFamilyProgram": invalid}, matrix_payload)
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe matrix grammar accepted")

# A rejected typed grammar is fed back to the one corrective model call.
bad_axis = {**grammar, "matrixAxis": "episode-slots"}
captured_retry = {}
original_corrected_plan = mod._request_corrected_plan
def fake_corrected_plan(endpoint, model, correction):
    captured_retry.update(correction)
    return {"sourceFamilyProgram": grammar}
mod._request_corrected_plan = fake_corrected_plan
try:
    corrected_plan, corrected_edits = mod._validated_generated_edits(
        "http://127.0.0.1:1", "unused", matrix_payload,
        {"sourceFamilyProgram": bad_axis},
    )
finally:
    mod._request_corrected_plan = original_corrected_plan
assert captured_retry["rejectedSourceFamilyProgram"] == bad_axis
assert captured_retry["correctionContract"]["mustDifferFromRejectedSourceFamilyProgram"] is True
assert corrected_plan["sourceFamilyProgram"] == grammar
assert len(corrected_edits) == 3

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    real = root / mod.SOURCE_MATRIX_RUNTIME_PATH
    real.parent.mkdir(parents=True)
    real.write_text((ROOT / mod.SOURCE_MATRIX_RUNTIME_PATH).read_text(encoding="utf-8"), encoding="utf-8")
    config = root / "engine_v2/config/brain-self-evolution.json"
    config.parent.mkdir(parents=True)
    config.write_text((ROOT / "engine_v2/config/brain-self-evolution.json").read_text(encoding="utf-8"), encoding="utf-8")
    def git(*args):
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    git("init", "-q")
    git("config", "user.name", "Brain contract test")
    git("config", "user.email", "brain-test@example.invalid")
    git("add", ".")
    git("commit", "-qm", "baseline")
    edits = mod._model_edits({"sourceFamilyProgram": grammar}, matrix_payload)
    assert [x["operation"] for x in edits] == ["create", "replace", "create"]
    assert edits[1]["path"] == mod.SOURCE_MATRIX_RUNTIME_PATH
    assert "parse_episode_source(body, pos)" in edits[1]["replace"]
    mod.validate_edits(edits, [mod.SOURCE_MATRIX_RUNTIME_PATH], root=root)
    for e in edits:
        path = root / e["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if e["operation"] == "create":
            path.write_text(e["content"], encoding="utf-8")
        else:
            source = path.read_text(encoding="utf-8")
            assert source.count(e["find"]) == 1
            path.write_text(source.replace(e["find"], e["replace"], 1), encoding="utf-8")
    mod.validate_source_family_implementation([e["path"] for e in edits], matrix_blueprint, root=root)
    # Package and reapply the exact generated bytes in a real temporary Git repository.
    from brain_force_applied_profile_guard import verify, export_patch
    from brain_force_rebase_guard import patch_changed_paths
    plan = {"strategyBlueprints": [{**matrix_blueprint, "forcePromotionEligible": True}]}
    changed = [e["path"] for e in edits]
    report = {
        "strategyId": matrix_blueprint["strategyId"],
        "targetProvider": "source-family-representative",
        "editCount": 3, "changedFiles": changed, "applied": True,
        "materializedSha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in changed},
    }
    patch_path = root / "force.patch"
    assert verify(plan, report, root=root) == matrix_blueprint["strategyId"]
    export_patch(report, patch_path, root=root)
    assert patch_changed_paths(patch_path.read_text("utf-8")) == set(changed)
    git("reset", "--hard", "HEAD")
    git("apply", "--check", str(patch_path))
    git("apply", str(patch_path))
    assert verify(plan, report, root=root) == matrix_blueprint["strategyId"]
    for bad in ({**report, "changedFiles": changed[:2]}, {**report, "materializedSha256": {}}, {**report, "applied": False}):
        try:
            verify(plan, bad, root=root)
        except ValueError:
            pass
        else:
            raise AssertionError("partial or unattested source-family patch accepted")
    original = real.read_bytes()
    real.write_bytes(original + b"\n")
    try:
        verify(plan, report, root=root)
    except ValueError as exc:
        assert "byte mismatch" in str(exc)
    else:
        raise AssertionError("modified applied classifier was accepted")
    real.write_bytes(original)
    # A transposed grammar is rejected before compilation. If compiler bytes
    # are corrupted after prevalidation, the independent materialized oracle
    # still rejects the bad axis.
    layer_path = root / edits[0]["path"]
    valid_layer = layer_path.read_text(encoding="utf-8")
    layer_path.write_text(
        valid_layer.replace("AXIS = 'reader-slots'", "AXIS = 'episode-slots'", 1),
        encoding="utf-8",
    )
    try:
        mod.validate_source_family_implementation([e["path"] for e in edits], matrix_blueprint, root=root)
    except ValueError as exc:
        assert "source-family synthetic parser replay failed" in str(exc)
    else:
        raise AssertionError("tampered transposed matrix compiler bytes were accepted")

print("Source-family Brain FORCE mode: typed program compiled into 3 deterministic edits, actual wired parser test and hostile negatives passed")
