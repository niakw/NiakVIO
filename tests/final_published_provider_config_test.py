#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import projection_visible_provider_ids, projection_visible_provider_rows  # noqa: E402

spec = importlib.util.spec_from_file_location("final_config", ROOT / "scripts" / "validate_published_provider_config.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

# Repository-default validation must cover the full current Global+France union,
# not a frozen historical cardinality or Global manifest only.
module.validate_manifest(ROOT / "manifest.json")
rows = projection_visible_provider_rows()
assert {module.canonical_id(str(row.get("id") or "")) for row in rows} == projection_visible_provider_ids()

global_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
global_ids = {
    module.canonical_id(str(row.get("id") or ""))
    for row in global_manifest.get("scrapers") or []
    if isinstance(row, dict)
}
france_only = [row for row in rows if module.canonical_id(str(row.get("id") or "")) not in global_ids]
assert france_only, "fixture requires at least one current France-only provider"
fr_row = france_only[0]
fr_text = (ROOT / str(fr_row["filename"])).read_text(encoding="utf-8")
module.validate_bundle(fr_text, str(fr_row.get("id") or ""))

# A malformed managed CONFIG remains rejected independently of projection.
row = next(
    item for item in rows
    if isinstance(item, dict) and str(item.get("filename") or "").startswith("providers/")
)
text = (ROOT / row["filename"]).read_text(encoding="utf-8")
broken = text.replace("const NIAKVIO_PROVIDER_MODEL = Object.freeze(", "const NIAKVIO_BROKEN_MODEL = Object.freeze(", 1)
try:
    module.validate_bundle(broken, str(row.get("id") or ""))
except ValueError:
    pass
else:
    raise AssertionError("missing Provider model declaration was not rejected")

print(
    "final published Provider CONFIG regression test passed "
    f"visible={len(rows)} france_only={len(france_only)}"
)
