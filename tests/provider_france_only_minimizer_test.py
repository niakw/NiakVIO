#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "frmin", ROOT / "scripts" / "finalize_france_only_provider_v3_minimizer.py"
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

global_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf_manifest = json.loads((ROOT / "vf" / "manifest.json").read_text(encoding="utf-8"))
catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
cohort = mod.active_france_only(global_manifest, vf_manifest, catalog)
assert cohort, "expected at least one active strict France-only provider"

pid, record, scraper, vf_row = cohort[0]
prov = copy.deepcopy((provenance.get("providers") or {}).get(pid))
assert isinstance(prov, dict), pid
prov.pop("final_minimizer", None)
prov.pop("final_fixed_point", None)

source_rel = str(scraper.get("filename") or "").replace("\\", "/")
assert source_rel.startswith("providers/"), (pid, source_rel)
source_file = ROOT / source_rel
assert source_file.is_file(), source_file

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "providers").mkdir(parents=True)
    (root / "vf").mkdir(parents=True)
    shutil.copy2(source_file, root / source_rel)

    (root / "manifest.json").write_text(
        json.dumps({"scrapers": []}, indent=2) + "\n", encoding="utf-8"
    )
    (root / "vf" / "manifest.json").write_text(
        json.dumps({"scrapers": [copy.deepcopy(vf_row)]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "provider_catalog.json").write_text(
        json.dumps({"providers": [copy.deepcopy(record)]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "PROVENANCE.json").write_text(
        json.dumps({"providers": {pid: prov}}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Redirect only filesystem authority; the minimizer implementation and
    # version-floor helper remain the maintained repository code under test.
    mod.ROOT = root
    mod.GLOBAL_MANIFEST = root / "manifest.json"
    mod.VF_MANIFEST = root / "vf" / "manifest.json"
    mod.CATALOG = root / "provider_catalog.json"
    mod.PROVENANCE = root / "PROVENANCE.json"
    mod.PROVIDERS = root / "providers"

    result = mod.finalize(check=False)
    assert result["providerCount"] == 1

    next_vf = json.loads((root / "vf" / "manifest.json").read_text())
    next_cat = json.loads((root / "provider_catalog.json").read_text())
    next_prov = json.loads((root / "PROVENANCE.json").read_text())["providers"][pid]
    next_vf_row = next_vf["scrapers"][0]
    next_scraper = next_cat["providers"][0]["scraper"]

    assert next_vf_row["enabled"] is not False
    assert next_scraper["enabled"] is not False
    assert next_vf_row["filename"] == "../" + next_scraper["filename"]
    final_min = next_prov.get("final_minimizer")
    final_fixed = next_prov.get("final_fixed_point")
    assert isinstance(final_min, dict) and final_min.get("production_enabled") is True
    assert final_min.get("terser_allowed") is False
    assert final_min.get("one_physical_line") is True
    assert isinstance(final_fixed, dict) and final_fixed.get("verified") is True
    assert final_fixed.get("one_physical_line") is True
    assert final_fixed.get("sha256") == final_min.get("sha256")
    assert next_prov.get("published_filename") == next_scraper["filename"]
    assert (root / next_scraper["filename"]).is_file()

    mod.finalize(check=True)

print(f"France-only minimizer exact-byte proof test passed provider={pid}")
