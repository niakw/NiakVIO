#!/usr/bin/env python3
"""No-anime remains supported; Nuvio staging resolves four manifest URL bases."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("NIAKVIO_PROVIDER_SCOPE_MATRIX", None)
os.environ.pop("NIAKVIO_MATERIALIZE_NATIVE", None)
import prepare_native_corpus_client as client  # noqa: E402

counts = {}
for manifest in (
    "manifest.json", "vf/manifest.json",
    "no-anime/manifest.json", "vf-no-anime/manifest.json",
):
    path = ROOT / manifest
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = [r for r in document.get("scrapers") or [] if isinstance(r, dict)]
    sample = next(
        row for row in rows
        if str(row.get("filename") or "").startswith(("../providers/", "providers/"))
    )
    raw = str(sample["filename"])
    expected = (path.parent / raw).resolve()
    assert client._provider_source(raw, manifest_dir=path.parent) == expected
    assert expected.is_file(), (manifest, raw)
    actual = client.manifest_providers(manifest)
    declared_ids = {str(row["id"]).strip().casefold() for row in rows if row.get("id") and row.get("filename")}
    assert len(actual) == len(declared_ids), (manifest, len(actual), len(declared_ids))
    assert any(row["enabled"] for row in actual), manifest
    assert all(row["source"].is_file() for row in actual), manifest
    counts[manifest] = len(actual)

for invalid in ("../../README.md", "../manifest.json"):
    try:
        client._provider_source(invalid, manifest_dir=ROOT / "vf")
    except SystemExit:
        pass
    else:
        raise AssertionError("native staging accepted a filename outside provider lifecycle")
assert counts["no-anime/manifest.json"] > 0
assert counts["vf-no-anime/manifest.json"] > 0
print("Four manifest variants and nested native staging: PASS", counts)
