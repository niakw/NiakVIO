#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "select_provider_materialization_scope.py"
spec = importlib.util.spec_from_file_location("provider_materialization_scope", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base_overrides = {
    "schema_version": 7,
    "blocked_domains": ["localhost"],
    "provider_patches": {
        "alpha": {"provider_lego_scripts": ["scripts/provider_patches/alpha_runtime_v1.py"], "x": 1},
        "beta": {"x": 1},
    },
    "provider_capabilities": {"alpha": {"x": 1}, "beta": {"x": 1}},
}
next_overrides = {
    **base_overrides,
    "provider_patches": {
        **base_overrides["provider_patches"],
        "alpha": {"provider_lego_scripts": ["scripts/provider_patches/alpha_runtime_v1.py"], "x": 2},
    },
}
blank_hubs = {"providers": {}}
blank_static = {"providers": {}}
blank_manifest = {"scrapers": []}

def docs(overrides):
    return {
        "provider-overrides.json": overrides,
        "provider-hubs.json": blank_hubs,
        "automation/provider-v3-static-knowledge.json": blank_static,
        "manifest.json": blank_manifest,
    }

mode, providers, _ = mod.classify(
    [".github/workflows/temp-current-bytes-full-provider-census.yml", "MEMORY.md"],
    docs(base_overrides),
    docs(base_overrides),
)
assert mode == "none" and providers == [], (mode, providers)

mode, providers, _ = mod.classify(
    ["provider-overrides.json"],
    docs(base_overrides),
    docs(next_overrides),
)
assert mode == "providers" and providers == ["alpha"], (mode, providers)

global_overrides = {**next_overrides, "blocked_domains": ["localhost", "example.invalid"]}
mode, providers, _ = mod.classify(
    ["provider-overrides.json"],
    docs(base_overrides),
    docs(global_overrides),
)
assert mode == "all" and providers == [], (mode, providers)

mode, providers, _ = mod.classify(
    ["scripts/provider_patches/alpha_runtime_v1.py"],
    docs(base_overrides),
    docs(base_overrides),
)
assert mode == "providers" and providers == ["alpha"], (mode, providers)

mode, providers, _ = mod.classify(
    ["scripts/provider_patches/unowned_runtime_v1.py"],
    docs(base_overrides),
    docs(base_overrides),
)
assert mode == "all" and providers == [], (mode, providers)

before_manifest = {"scrapers": [{"id": "alpha", "filename": "providers/a.js"}, {"id": "beta", "filename": "providers/b.js"}]}
after_manifest = {"scrapers": [{"id": "alpha", "filename": "providers/a2.js"}, {"id": "beta", "filename": "providers/b.js"}]}
before_docs = docs(base_overrides)
after_docs = docs(base_overrides)
before_docs["manifest.json"] = before_manifest
after_docs["manifest.json"] = after_manifest
mode, providers, _ = mod.classify(["manifest.json"], before_docs, after_docs)
assert mode == "providers" and providers == ["alpha"], (mode, providers)

mode, providers, _ = mod.classify(
    ["scripts/provider_base_store.py"],
    docs(base_overrides),
    docs(base_overrides),
)
assert mode == "all" and providers == [], (mode, providers)

mode, providers, reasons = mod.classify(
    ["provider-bases/demo--base--deadbeef.js"],
    docs(base_overrides),
    docs(base_overrides),
)
assert mode == "all" and providers == [], (mode, providers)
assert reasons == ["global-prefix:provider-bases/demo--base--deadbeef.js"], reasons

# Brain-LLM guidance must compare committed provider state, not transient
# sandbox mutations in the current checkout. Reproduce that exact failure mode
# by dirtying provider-overrides.json while base=head=HEAD.
overrides_path = ROOT / "provider-overrides.json"
original = overrides_path.read_text(encoding="utf-8")
try:
    dirty = json.loads(original)
    dirty["_transient_learning_test"] = {"sandboxOnly": True}
    overrides_path.write_text(json.dumps(dirty, indent=2) + "\n", encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="provider-scope-committed-") as td:
        out = Path(td) / "scope.json"
        subprocess.run(
            [
                "python3", str(SCRIPT),
                "--base", "HEAD",
                "--head", "HEAD",
                "--committed-only",
                "--output", str(out),
            ],
            cwd=ROOT,
            check=True,
        )
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["mode"] == "none", payload
        assert payload["changedPaths"] == [], payload
        assert payload["committedOnly"] is True, payload
finally:
    overrides_path.write_text(original, encoding="utf-8")

print("Provider census incremental materialization scope tests passed")
