#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_upstream_provider_additions.py"
WORKFLOW = ROOT / ".github/workflows/weekly-provider-discovery.yml"
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("weekly_provider_discovery", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
assert set(sources["upstreams"]) == {"gowaru", "aio", "yoru"}
assert module.known_provider_ids(catalog)

fixture_sources = {
    "upstreams": {
        "gowaru": {"name": "Gowaru", "repository": "https://example/gowaru"},
        "aio": {"name": "AIO", "repository": "https://example/aio"},
        "yoru": {"name": "Yoru", "repository": "https://example/yoru"},
    },
    "exclusions": {
        "provider_ids": ["torrentio"],
        "metadata_patterns": ["torrent", "magnet", "p2p"],
    },
}
fixture_catalog = {"manifestOrder": {"general": ["existing-provider"]}}
fixture_manifests = {
    "gowaru": {"scrapers": [
        {"id": "existing-provider", "supportedTypes": ["movie"]},
        {"id": "new-fr", "supportedTypes": ["movie", "tv"], "languages": ["fr"], "quality": ["4k"]},
    ]},
    "aio": {"scrapers": [
        {"id": "torrentio", "description": "torrent p2p", "supportedTypes": ["movie"]},
        {"id": "new-anime", "supportedTypes": ["anime"], "enabled": True},
    ]},
    "yoru": {"scrapers": [
        {"id": "new-plain", "supportedTypes": ["movie"], "enabled": False},
    ]},
}
report = module.build_report(fixture_sources, fixture_catalog, fixture_manifests)
ids = [row["canonicalId"] for row in report["candidates"]]
assert "existing-provider" not in ids
assert "torrentio" not in ids
assert ids[0] == "new-fr", report
assert set(ids) == {"new-fr", "new-anime", "new-plain"}
assert report["configuredUpstreamCount"] == 3
assert report["checkedUpstreamCount"] == 3
assert report["policy"]["readOnly"] is True
assert report["policy"]["automaticImport"] is False
assert report["policy"]["automaticEnable"] is False
assert report["policy"]["automaticPublish"] is False
assert report["policy"]["reviewRequired"] is True

workflow = WORKFLOW.read_text(encoding="utf-8")
assert "schedule:" in workflow and "cron:" in workflow
assert "workflow_dispatch:" in workflow
assert "permissions:\n  contents: read" in workflow
assert "check_upstream_provider_additions.py" in workflow
assert "upload-artifact@v4" in workflow
for forbidden in ("git push", "git commit", "create-pull-request", "contents: write"):
    assert forbidden not in workflow

print("weekly provider discovery tests passed")
