#!/usr/bin/env python3
"""Targeted publication fixed-point must support France-only catalog authority."""
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_targeted_provider_publication import reconcile  # noqa: E402


with tempfile.TemporaryDirectory(prefix="niakvio-fr-publish-") as tmp_name:
    root = Path(tmp_name)
    (root / "providers").mkdir(parents=True)

    provider = "fronly"
    data = {
        "providerId": provider,
        "apiRecipe": {"base": "https://fronly.example", "directRoute": "/{media}?id={tmdbId}"},
    }
    payload = base64.b64encode(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    body = (
        "/* STARTFIX:PROVIDER.FRONLY.CONFIG.V1 */ "
        f"/* FIXDATA:PROVIDER.FRONLY.CONFIG.V1:{payload} */ "
        "const NIAKVIO_PROVIDER_MODEL = Object.freeze({}); "
        "/* CLOSEFIX:PROVIDER.FRONLY.CONFIG.V1 */"
    )
    current_rel = "providers/fronly-workspace.js"
    (root / current_rel).write_text(body, encoding="utf-8")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()

    (root / "manifest.json").write_text(
        json.dumps(
            {
                "scrapers": [
                    {
                        "id": "global-one",
                        "enabled": True,
                        "filename": "providers/global-one.js",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "provider_catalog.json").write_text(
        json.dumps(
            {
                "providers": [
                    {
                        "canonicalId": provider,
                        "scraper": {
                            "id": provider,
                            "enabled": True,
                            "filename": current_rel,
                        },
                        "projections": {"general": False, "vf": True},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "provider-v3-materialization.json").write_text(
        json.dumps(
            {
                "providers": [
                    {
                        "provider": provider,
                        "file": current_rel,
                        "sha256": digest,
                        "providerDataSha256": "0" * 64,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    sync_calls: list[bool] = []

    def sync_stub(*, check: bool) -> None:
        sync_calls.append(check)

    updates = reconcile(root, [provider], sync_projections=sync_stub)
    assert sync_calls == [False]
    assert len(updates) == 1
    assert updates[0]["authority"] == "france-only-catalog", updates

    global_manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert [row["id"] for row in global_manifest["scrapers"]] == ["global-one"]

    catalog = json.loads((root / "provider_catalog.json").read_text(encoding="utf-8"))
    scraper = catalog["providers"][0]["scraper"]
    assert scraper["filename"].startswith("providers/fronly--")
    assert scraper["filename"].endswith(".js")
    assert (root / scraper["filename"]).is_file()

    material = json.loads((root / "provider-v3-materialization.json").read_text(encoding="utf-8"))
    row = material["providers"][0]
    assert row["provider"] == provider
    assert row["file"] == scraper["filename"]
    assert row["sha256"] == hashlib.sha256((root / scraper["filename"]).read_bytes()).hexdigest()
    assert material["activeProviderIdentityCount"] == 2
    assert material["expectedProviderCount"] == 2
    assert material["targetedPublicationFixedPointProviders"] == [provider]
    assert material["targetedPublicationComplete"] is False

print("targeted France-only publication reconciles catalog authority without Global leakage")
