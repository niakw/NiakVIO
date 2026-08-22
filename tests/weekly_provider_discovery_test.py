#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/report_weekly_upstream_provider_discovery.py"
spec = importlib.util.spec_from_file_location("weekly_provider_discovery", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sources = {
    "upstreams": {
        "gowaru": {"repository": "https://github.com/Gowaru/gowaru-nuvio-providers"},
        "aio": {"repository": "https://github.com/NuvioPlugin/All-in-One-Nuvio"},
        "yoru": {"repository": "https://github.com/yoruix/nuvio-providers"},
    }
}
catalog = {"manifestOrder": {"general": ["known-one"], "vf": []}, "providers": [{"id": "known-two"}]}
manifest = {"scrapers": [{"id": "KNOWN-THREE"}]}
stage = {
    "upstreams": {
        "gowaru": {"status": "loaded"},
        "aio": {"status": "loaded"},
        "yoru": {"status": "loaded_from_upstream_lkg"},
    },
    "candidates": [
        {"source": "gowaru", "manifest_origin": "live", "canonical_id": "known-one", "upstream_id": "Known One", "metadata": {}},
        {"source": "aio", "manifest_origin": "live", "canonical_id": "known-two", "upstream_id": "Known Two", "metadata": {}},
        {"source": "gowaru", "manifest_origin": "live", "canonical_id": "known-three", "upstream_id": "Known Three", "metadata": {}},
        {
            "source": "gowaru", "manifest_origin": "live", "canonical_id": "fresh-fr", "upstream_id": "Fresh FR",
            "source_repository": "https://github.com/Gowaru/gowaru-nuvio-providers",
            "metadata": {"supportedTypes": ["movie", "tv"], "contentLanguage": ["fr"], "description": "4K French provider"},
        },
        {
            "source": "aio", "manifest_origin": "live", "canonical_id": "fresh-fr", "upstream_id": "Fresh FR",
            "source_repository": "https://github.com/NuvioPlugin/All-in-One-Nuvio",
            "metadata": {"supportedTypes": ["movie"], "contentLanguage": ["fr"]},
        },
        # Snapshot-only declarations are deliberately not weekly discoveries.
        {"source": "yoru", "manifest_origin": "upstream_lkg", "canonical_id": "stale-new", "upstream_id": "Stale New", "metadata": {}},
        # Published/LKG baseline variants are not upstream declarations.
        {"source": "published-baseline", "manifest_origin": "live", "canonical_id": "baseline-only", "upstream_id": "Baseline", "metadata": {}},
    ],
}

report = module.build_report(stage, catalog, manifest, sources)
assert report["configured_upstreams"] == ["aio", "gowaru", "yoru"]
assert report["new_provider_count"] == 1, report
fresh = report["new_providers"][0]
assert fresh["canonical_id"] == "fresh-fr"
assert fresh["sources"] == ["aio", "gowaru"]
assert fresh["review_score"] >= 8
assert fresh["automatic_import_allowed"] is False
assert fresh["requires_human_review_and_native_proof"] is True
assert "stale-new" not in {row["canonical_id"] for row in report["new_providers"]}
assert report["policy"]["automatic_activation_allowed"] is False
assert report["policy"]["live_manifest_required_for_new_provider"] is True
text = module.markdown(report)
assert "fresh-fr" in text
assert "never imports, enables, disables or publishes" in text

print("weekly provider discovery tests passed")
