#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATCHES = SCRIPTS / "provider_patches"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PATCHES))

CASES = {
    "allwish": {
        "module": "allwish_current_runtime_v2",
        "old_id": "PROVIDER.ALLWISH.CURRENT.RUNTIME.V1",
        "new_id": "PROVIDER.ALLWISH.CURRENT.RUNTIME.V2",
        "old_marker": "NIAKVIO_ALLWISH_CURRENT_RUNTIME_V1",
        "new_marker": "NIAKVIO_ALLWISH_CURRENT_RUNTIME_V2",
    },
    "vidfast": {
        "module": "vidfast_current_runtime_v2",
        "old_id": "PROVIDER.VIDFAST.CURRENT.EMBED.V1",
        "new_id": "PROVIDER.VIDFAST.CURRENT.RUNTIME.V2",
        "old_marker": "NIAKVIO_VIDFAST_CURRENT_EMBED_V1",
        "new_marker": "NIAKVIO_VIDFAST_CURRENT_RUNTIME_V2",
    },
    "vidlove": {
        "module": "vidlove_current_api_v2",
        "old_id": "PROVIDER.VIDLOVE.CURRENT.API.V1",
        "new_id": "PROVIDER.VIDLOVE.CURRENT.API.V2",
        "old_marker": "NIAKVIO_VIDLOVE_CURRENT_API_V1",
        "new_marker": "NIAKVIO_VIDLOVE_CURRENT_API_V2",
    },
}


def manifest_rows():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    return {str(row.get("id") or "").lower(): row for row in manifest.get("scrapers") or []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--published", action="store_true")
    args = parser.parse_args()

    rows = manifest_rows()
    for provider, cfg in CASES.items():
        row = rows.get(provider)
        assert row, provider
        bundle_path = ROOT / str(row["filename"])
        original = bundle_path.read_text(encoding="utf-8")
        module = importlib.import_module(cfg["module"])

        rewritten = module.apply(original)
        assert cfg["old_id"] not in rewritten, (provider, cfg["old_id"])
        assert cfg["old_marker"] not in rewritten, (provider, cfg["old_marker"])
        assert rewritten.count(cfg["new_id"]) >= 2, (provider, cfg["new_id"])
        assert rewritten.count(cfg["new_marker"]) == 1, (provider, cfg["new_marker"])

        if args.published:
            assert cfg["old_id"] not in original, (provider, "published old id", cfg["old_id"])
            assert cfg["old_marker"] not in original, (provider, "published old marker", cfg["old_marker"])
            assert cfg["new_id"] in original, (provider, "published new id", cfg["new_id"])
            assert original.count(cfg["new_marker"]) == 1, (provider, "published new marker", cfg["new_marker"])

    print("superseded provider Lego prune tests passed" + (" on published bundles" if args.published else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
