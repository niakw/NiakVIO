#!/usr/bin/env python3
"""Executable contract for the final NiakVIO Provider v3 minimizer transaction."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/finalize_provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("finalize_provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.PRODUCTION_ENABLED is True
assert module.TERSER_ALLOWED is False
assert module.EXPECTED_PROVIDER_COUNT == 46

with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)
    providers = tmp / "providers"
    providers.mkdir()
    manifest = {"version": "9.9.9", "scrapers": []}
    provenance = {"providers": {}}

    for index in range(46):
        provider_id = f"p{index:02d}"
        filename = f"providers/{provider_id}--nuvio--old0000000000000.js"
        text = (
            "/* BEGIN NIAKVIO_PROVIDER */\n"
            f"/* NIAKVIO_PROVIDER_ID:{provider_id} */\n"
            "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
            "\n"
            f"/* STARTFIX:PROVIDER.{provider_id.upper()}.CONFIG.V1 */\n"
            "  const NIAKVIO_PROVIDER_MODEL = Object.freeze({});   \n"
            f"/* CLOSEFIX:PROVIDER.{provider_id.upper()}.CONFIG.V1 */\n"
            "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */\n"
            "  const message = `literal ${\"  keep me\"}`;\n"
            "  function getStreams(){ return []; }\n"
            "/* END NIAKVIO_PROVIDER */\n"
        )
        (tmp / filename).write_text(text, encoding="utf-8")
        manifest["scrapers"].append({
            "id": provider_id,
            "version": "1.0.0",
            "filename": filename,
        })
        provenance["providers"][provider_id] = {
            "published_filename": filename,
            "sha256": "stale",
            "final_fixed_point": {
                "schema_version": 1,
                "verified": True,
                "tool": "raw-bytes",
                "tool_version": "test",
                "mangle": False,
                "sha256": "stale",
            },
        }

    manifest_path = tmp / "manifest.json"
    provenance_path = tmp / "PROVENANCE.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    module.ROOT = tmp
    module.MANIFEST = manifest_path
    module.PROVENANCE = provenance_path
    module.PROVIDERS = providers
    module.MINIMIZER = ROOT / "scripts/provider_v3_minimizer.py"
    module.validate_artifact = lambda data, provider_id: None
    module.assert_hardened = lambda text: None
    module.load_provider_version_floors = lambda: {}

    first = module.finalize(check=False)
    assert first["changed"] == 46, first
    assert first["saved_bytes"] > 0, first

    out_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert len(out_manifest["scrapers"]) == 46
    for row in out_manifest["scrapers"]:
        provider_id = row["id"]
        assert row["version"] == "1.0.1", row
        assert row["filename"].startswith(f"providers/{provider_id}--nuvio--"), row
        assert row["filename"].endswith(".js"), row
        text = (tmp / row["filename"]).read_text(encoding="utf-8")
        assert "  const NIAKVIO_PROVIDER_MODEL" not in text
        assert "  function getStreams" not in text
        assert "`literal ${\"  keep me\"}`" in text
        assert "\n\n" not in text
        assert text.count("STARTFIX:") == 1
        assert text.count("CLOSEFIX:") == 1
        proof = out_provenance["providers"][provider_id]["final_minimizer"]
        assert proof["terser_allowed"] is False
        assert proof["production_enabled"] is True
        assert proof["sha256"] == out_provenance["providers"][provider_id]["sha256"]

    # A second application is a strict fixed point: no provider version may bump.
    second = module.finalize(check=False)
    assert second["changed"] == 0, second
    after_second = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert all(row["version"] == "1.0.1" for row in after_second["scrapers"])
    module.finalize(check=True)

print("PROVIDER_V3_MINIMIZER_PUBLICATION_PIPELINE_OK providers=46 fixed_point=1 template_safe=1 terser=0")
