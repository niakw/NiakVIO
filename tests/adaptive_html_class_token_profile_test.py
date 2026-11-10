#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/adaptive_runtime/runtime_repair.py"
sys.path.insert(0, str(ROOT / "scripts/adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("adaptive_runtime_html_class_token_test", MODULE_PATH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

source = r'''
function classText(html,cls){var re=new RegExp("<div\\b[^>]*class=[\\\"'][^\\\"']*\\b"+cls+"\\b[^\\\"']*[\\\"']","i");return re.test(html)}
function classBlocks(html,cls){var esc=cls;var re=new RegExp("<li\\b[^>]*class=[\\\"'][^\\\"']*\\b"+esc+"\\b[^\\\"']*[\\\"']","gi");return re.test(html)}
'''
result = {"status": "no_streams", "tests": [{"status": "no_streams", "stream_count": 0}]}
candidate = {
    "key": "fixture:html-class-token",
    "canonical_id": "fixture-provider",
    "source": "fixture",
    "local_path": "providers/fixture-provider.js",
    "bytes": len(source.encode("utf-8")),
    "local_patches": [],
}
profiles = runtime.matching_profiles(candidate, result, source, config={})
assert runtime.HTML_CLASS_TOKEN_PROFILE in profiles, profiles

with tempfile.TemporaryDirectory(prefix="niakvio-html-class-token-") as tmp:
    stage = Path(tmp)
    provider = stage / candidate["local_path"]
    provider.parent.mkdir(parents=True, exist_ok=True)
    provider.write_text(source, encoding="utf-8")
    repaired, error = runtime.create_repair_candidate(stage, candidate, runtime.HTML_CLASS_TOKEN_PROFILE, 1)
    assert error is None, error
    assert repaired is not None
    repaired_source = (stage / repaired["local_path"]).read_text(encoding="utf-8")
    assert "NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in repaired_source
    assert "(?![-_A-Za-z0-9])" in repaired_source
    assert r'+"\\b' not in repaired_source
    records = repaired.get("local_patches") or []
    assert any(
        row.get("profile") == runtime.HTML_CLASS_TOKEN_PROFILE
        and row.get("scope") == "generic_html_class_token_contract"
        for row in records if isinstance(row, dict)
    )

print(json.dumps({"html_class_token_exact_profile": "ok"}, sort_keys=True))


# Production HTML parser oracle: replay the existing realistic nested-card
# fixture unchanged. The Brain profile must improve the *actual runtime*;
# merely emitting a marker or compiling a synthetic regex is insufficient.
# This is offline HTML/URL traversal proof, never evidence of playable media.
import ast
import subprocess

runtime_patch = ROOT / "scripts/provider_patches/4khdhub_runtime_v1.py"
runtime_spec = importlib.util.spec_from_file_location("niakvio_html_class_runtime_oracle", runtime_patch)
assert runtime_spec and runtime_spec.loader
runtime_module = importlib.util.module_from_spec(runtime_spec)
runtime_spec.loader.exec_module(runtime_module)
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
published_rows = [row for row in manifest.get("scrapers", [])
                  if str(row.get("id") or "").casefold() == "4khdhub"]
assert len(published_rows) == 1, published_rows
published_path = ROOT / published_rows[0]["filename"]
assert published_path.is_file(), "missing exact published 4KHDHub runtime bytes"
published_bytes = published_path.read_text(encoding="utf-8")
assert "NIAKVIO_4KHDHUB_RUNTIME_V1" in published_bytes
assert "function classBlocks(html,cls)" in published_bytes
assert 'classBlocks(sr.text,"movie-card")' in published_bytes
assert "NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in published_bytes, (
    str(published_path), "Brain generic HTML class parser was not persisted into published bytes"
)

fixture_path = ROOT / "tests/provider_4khdhub_runtime_behavior_test.py"
fixture_ast = ast.parse(fixture_path.read_text(encoding="utf-8"))
assignments = [
    node.value for node in fixture_ast.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "js" for target in node.targets)
]
assert len(assignments) == 1, "runtime fixture must provide exactly one JS scenario"
expression = assignments[0]
assert (
    isinstance(expression, ast.BinOp)
    and isinstance(expression.left, ast.BinOp)
    and isinstance(expression.left.left, ast.Constant)
    and isinstance(expression.left.right, ast.Name)
    and expression.left.right.id == "wrapper"
    and isinstance(expression.right, ast.Constant)
), "runtime fixture JS expression changed: review oracle before proceeding"
prefix, suffix = expression.left.left.value, expression.right.value

cfg = {"base": "https://4khdhub.one", "maxStreams": 8, "ua": "NiakVIO-Test"}
module_spec = importlib.util.spec_from_file_location(
    "niakvio_html_class_current_brain_profile",
    ROOT / "scripts/adaptive_runtime/html_class_token_exact_v1.py",
)
assert module_spec and module_spec.loader
profile = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(profile)
original_wrapper = runtime_module.WRAPPER
repaired_wrapper = profile.apply(original_wrapper)
assert repaired_wrapper != original_wrapper
assert "NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in repaired_wrapper

def run_runtime_oracle(wrapper: str) -> dict:
    js_source = (
        prefix
        + wrapper.replace("CONFIG_PLACEHOLDER", json.dumps(cfg, separators=(",", ":")))
        + suffix
    )
    with tempfile.TemporaryDirectory(prefix="niakvio-runtime-oracle-") as folder:
        script = Path(folder) / "probe.cjs"
        script.write_text(js_source, encoding="utf-8")
        result = subprocess.run(
            ["node", str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        return json.loads(result.stdout.strip().splitlines()[-1])

before = run_runtime_oracle(original_wrapper)
after = run_runtime_oracle(repaired_wrapper)
assert before["movie"] == [] and before["tv"] == [], before
assert len(after["movie"]) == 1 and len(after["tv"]) == 1, after
assert after["movie"][0]["url"] == "https://media.workers.dev/colony.mkv", after
assert after["tv"][0]["url"] == "https://media.workers.dev/bb-s01e01.mkv", after
assert after["movie"][0]["quality"] == "2160p", after
assert "S01E01" in after["tv"][0]["title"], after
assert any("/the-colony-movie-7978/" in u for u in after["fetchTrace"]), after
assert any("/breaking-bad-series-1385/" in u for u in after["fetchTrace"]), after

print(json.dumps({
    "html_class_token_runtime_oracle": "offline-parser-improved",
    "before": [len(before["movie"]), len(before["tv"])],
    "after": [len(after["movie"]), len(after["tv"])],
    "published_provider_mutated": False,
    "live_playback_proven": False,
}, sort_keys=True))
