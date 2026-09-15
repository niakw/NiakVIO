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
SYNTHETIC_ACTIVE = 3
DISABLED_ID = "disabled-demo"


spec = importlib.util.spec_from_file_location("finalize_provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

assert module.PRODUCTION_ENABLED is True
assert module.TERSER_ALLOWED is False

with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)
    providers = tmp / "providers"
    providers.mkdir()
    (tmp / "provider-disabled").mkdir()
    manifest = {"version": "9.9.9", "scrapers": []}
    provenance = {"providers": {}}

    for index in range(SYNTHETIC_ACTIVE):
        provider_id = f"p{index:02d}"
        filename = f"providers/{provider_id}--nuvio--old0000000000000.js"
        text = (
            "/* BEGIN NIAKVIO_PROVIDER */\n"
            f"/* NIAKVIO_PROVIDER_ID:{provider_id} */\n"
            "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
            "\n"
            "  // removable publication comment\n"
            f"/* STARTFIX:PROVIDER.{provider_id.upper()}.CONFIG.V1 */\n"
            "  const NIAKVIO_PROVIDER_MODEL = Object.freeze({});   \n"
            f"/* CLOSEFIX:PROVIDER.{provider_id.upper()}.CONFIG.V1 */\n"
            "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */\n"
            "  const message = `literal ${\"  keep me\"}`;\n"
            "  function getStreams(){ return []; }\n"
            "/* END NIAKVIO_PROVIDER */\n"
        )
        (tmp / filename).write_text(text, encoding="utf-8")
        # Simulate the preceding durable-reapply stage already consuming the
        # cache-safe version bump for this same accepted provider generation.
        manifest["scrapers"].append({
            "id": provider_id,
            "version": "1.0.1",
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

    disabled_filename = "provider-disabled/disabled-demo--nuvio--disabled00000000.js"
    disabled_text = "/* disabled provider retained verbatim */\n"
    (tmp / disabled_filename).write_text(disabled_text, encoding="utf-8")
    manifest["scrapers"].append({
        "id": DISABLED_ID,
        "version": "7.7.7",
        "filename": disabled_filename,
        "enabled": False,
    })
    provenance["providers"][DISABLED_ID] = {
        "published_filename": disabled_filename,
        "sha256": "disabled-stable",
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
    module.load_provider_version_floors = lambda: {
        f"p{index:02d}": "1.0.0" for index in range(SYNTHETIC_ACTIVE)
    }

    first = module.finalize(check=False)
    assert first["changed"] == SYNTHETIC_ACTIVE, first
    assert first["saved_bytes"] > 0, first
    assert first["already_versioned"] == SYNTHETIC_ACTIVE, first

    out_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert len(out_manifest["scrapers"]) == SYNTHETIC_ACTIVE + 1
    disabled_row = next(row for row in out_manifest["scrapers"] if row["id"] == DISABLED_ID)
    assert disabled_row == {
        "id": DISABLED_ID,
        "version": "7.7.7",
        "filename": disabled_filename,
        "enabled": False,
    }
    assert (tmp / disabled_filename).read_text(encoding="utf-8") == disabled_text
    assert out_provenance["providers"][DISABLED_ID] == {
        "published_filename": disabled_filename,
        "sha256": "disabled-stable",
    }
    first_proofs = {}
    for row in [row for row in out_manifest["scrapers"] if row.get("enabled") is not False]:
        provider_id = row["id"]
        assert row["version"] == "1.0.1", row
        assert row["filename"].startswith(f"providers/{provider_id}--nuvio--"), row
        assert row["filename"].endswith(".js"), row
        text = (tmp / row["filename"]).read_text(encoding="utf-8")
        assert "  const NIAKVIO_PROVIDER_MODEL" not in text
        assert "  function getStreams" not in text
        assert "removable publication comment" not in text
        assert "`literal ${\"  keep me\"}`" in text
        assert "\n\n" not in text
        assert text.count("STARTFIX:") == 1
        assert text.count("CLOSEFIX:") == 1
        proof = out_provenance["providers"][provider_id]["final_minimizer"]
        assert proof["schema_version"] == 2
        assert proof["terser_allowed"] is False
        assert proof["production_enabled"] is True
        assert proof["saved_bytes"] > 0
        assert proof["sha256"] == out_provenance["providers"][provider_id]["sha256"]
        first_proofs[provider_id] = dict(proof)

    # A second application is a strict fixed point: no provider version may
    # bump and the original transformation metrics remain the stable proof.
    second = module.finalize(check=False)
    assert second["changed"] == 0, second
    after_second = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance_second = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert all(row["version"] == "1.0.1" for row in after_second["scrapers"] if row.get("enabled") is not False)
    for provider_id, proof in first_proofs.items():
        assert provenance_second["providers"][provider_id]["final_minimizer"] == proof
    module.finalize(check=True)

print(f"PROVIDER_V3_MINIMIZER_PUBLICATION_PIPELINE_OK providers={SYNTHETIC_ACTIVE} disabled_preserved=1 fixed_point=1 no_double_bump=1 template_safe=1 terser=0")
