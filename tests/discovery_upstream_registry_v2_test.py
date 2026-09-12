#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "scripts/upgrade_discovery_upstream_registry_v2.py"], cwd=ROOT, check=True)

path = ROOT / "scripts" / "discover_candidates.py"
spec = importlib.util.spec_from_file_location("discover_candidates_registry_v2", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "scripts"))
spec.loader.exec_module(module)

sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "engine_v2/config/provider-upstreams.json").read_text(encoding="utf-8"))
assert "upstreams" not in sources, "sources.json must stay catalogue/policy-only"
assert isinstance(registry.get("upstreams"), list)

config = module.load_discovery_config()
assert config.get("exclusions") == sources.get("exclusions")
upstreams = config.get("upstreams")
assert isinstance(upstreams, dict)
assert list(upstreams) == ["gowaru", "aio", "yoru"]

assert upstreams["gowaru"]["manifest_urls"] == [
    "https://raw.githubusercontent.com/Gowaru/gowaru-nuvio-providers/main/manifest.json"
]
assert upstreams["aio"]["manifest_urls"] == [
    "https://raw.githubusercontent.com/NuvioPlugin/All-in-One-Nuvio/main/manifest.json",
    "https://raw.githubusercontent.com/D3adlyRocket/All-in-One-Nuvio/main/manifest.json",
]
assert upstreams["yoru"]["manifest_urls"] == [
    "https://raw.githubusercontent.com/yoruix/nuvio-providers/main/manifest.json"
]

source = path.read_text(encoding="utf-8")
assert 'config = load_discovery_config()' in source
assert 'config = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))\n    exclusions = config.get("exclusions", {})' not in source
print("discovery upstream registry V2 contract passed: policy + authoritative three-upstream registry")
