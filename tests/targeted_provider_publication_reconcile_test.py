#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_targeted_provider_publication import data_digest, reconcile

with tempfile.TemporaryDirectory() as tmp_name:
    root = Path(tmp_name)
    (root / "providers").mkdir(parents=True)
    data = {
        "providerId": "vidlove",
        "apiRecipe": {
            "base": "https://api.vidlove.cc",
            "directRoute": "/{media}?id={tmdbId}&sources=moviebox",
        },
    }
    payload = base64.b64encode(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    body = (
        "/* STARTFIX:PROVIDER.VIDLOVE.CONFIG.V1 */ "
        f"/* FIXDATA:PROVIDER.VIDLOVE.CONFIG.V1:{payload} */ "
        "const NIAKVIO_PROVIDER_MODEL = Object.freeze({}); "
        "/* CLOSEFIX:PROVIDER.VIDLOVE.CONFIG.V1 */"
    )
    current_rel = "providers/vidlove-workspace.js"
    current_path = root / current_rel
    current_path.write_text(body, encoding="utf-8")
    raw = current_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()

    (root / "manifest.json").write_text(json.dumps({
        "scrapers": [{"id": "vidlove", "filename": current_rel}]
    }), encoding="utf-8")
    (root / "provider-v3-materialization.json").write_text(json.dumps({
        "providers": [{
            "provider": "vidlove",
            "file": "providers/vidlove--nuvio--old000000000000.js",
            "sha256": "0" * 64,
            "providerDataSha256": "0" * 64,
        }]
    }), encoding="utf-8")

    updates = reconcile(root, ["vidlove"])
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    material = json.loads((root / "provider-v3-materialization.json").read_text(encoding="utf-8"))
    mrow = manifest["scrapers"][0]
    prow = material["providers"][0]

    assert mrow["filename"] == prow["file"]
    assert mrow["filename"].startswith("providers/vidlove--nuvio--")
    assert mrow["filename"].endswith(f"{digest[:16]}.js")
    assert (root / mrow["filename"]).read_bytes() == raw
    assert prow["sha256"] == digest
    assert prow["providerDataSha256"] == data_digest(data)
    assert material["providerCount"] == 1
    assert material["expectedProviderCount"] == 1
    assert material["targetedPublicationFixedPointProviders"] == ["vidlove"]
    assert updates[0]["to"] == mrow["filename"]

print("targeted provider publication reconcile passed: manifest/materialization/public bytes converge after final targeted materialization")
