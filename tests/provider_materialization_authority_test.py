#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_materialization_authority import validate


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    providers = root / "providers"
    disabled = root / "provider-disabled"
    providers.mkdir()
    disabled.mkdir()

    active_bytes = b"console.log('active');\n"
    disabled_bytes = b"console.log('disabled');\n"
    active_sha = hashlib.sha256(active_bytes).hexdigest()
    disabled_sha = hashlib.sha256(disabled_bytes).hexdigest()
    active_file = f"providers/alpha-{active_sha[:16]}.js"
    disabled_file = f"provider-disabled/beta-{disabled_sha[:16]}.js"
    (root / active_file).write_bytes(active_bytes)
    (root / disabled_file).write_bytes(disabled_bytes)

    dump(root / "manifest.json", {
        "scrapers": [
            {"id": "alpha", "filename": active_file, "enabled": True},
            {"id": "beta", "filename": disabled_file, "enabled": False},
        ]
    })
    dump(root / "provider-v3-materialization.json", {
        "providerCount": 1,
        "activeProviderIdentityCount": 1,
        "expectedProviderCount": 1,
        "providers": [
            {"provider": "alpha", "file": active_file, "sha256": active_sha}
        ],
    })

    result = validate(root)
    assert result["activeProviderCount"] == 1
    assert result["materializedProviderCount"] == 1

    broken = json.loads((root / "provider-v3-materialization.json").read_text())
    broken["providers"].append({
        "provider": "beta",
        "file": disabled_file,
        "sha256": disabled_sha,
    })
    broken["providerCount"] = 2
    broken["expectedProviderCount"] = 2
    dump(root / "provider-v3-materialization.json", broken)
    try:
        validate(root)
    except RuntimeError as exc:
        assert "extra_nonactive=['beta']" in str(exc), exc
    else:
        raise AssertionError("disabled provider materialization authority was accepted")

    dump(root / "provider-v3-materialization.json", {
        "providerCount": 1,
        "activeProviderIdentityCount": 1,
        "expectedProviderCount": 1,
        "providers": [
            {"provider": "alpha", "file": "providers/alpha-stale000000000.js", "sha256": active_sha}
        ],
    })
    try:
        validate(root)
    except RuntimeError as exc:
        assert "manifest/materialization file mismatch" in str(exc), exc
    else:
        raise AssertionError("stale manifest/materialization filename was accepted")

print("provider materialization authority invariant passed")
