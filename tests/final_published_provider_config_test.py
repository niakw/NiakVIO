#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("final_config", ROOT / "scripts" / "validate_published_provider_config.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
module.validate_manifest(ROOT / "manifest.json", 96)
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
row = next(item for item in manifest["scrapers"] if isinstance(item, dict) and str(item.get("filename") or "").startswith("providers/"))
text = (ROOT / row["filename"]).read_text(encoding="utf-8")
broken = text.replace("const NIAKVIO_PROVIDER_MODEL = Object.freeze(", "const NIAKVIO_BROKEN_MODEL = Object.freeze(", 1)
try:
    module.validate_bundle(broken, str(row.get("id") or ""))
except ValueError:
    pass
else:
    raise AssertionError("missing Provider model declaration was not rejected")
print("final published Provider CONFIG regression test passed")
