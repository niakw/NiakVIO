#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "nuvio_client_activation_ids.py"

spec = importlib.util.spec_from_file_location("nuvio_client_activation_ids", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "vf").mkdir()
    main = {
        "version": "1.2.3",
        "scrapers": [
            {"id": "goated", "version": "1.0.0", "enabled": True, "filename": "providers/goated.js", "supportedTypes": ["movie", "tv"]},
            {"id": "streamzo", "version": "1.0.0", "enabled": False, "filename": "providers/streamzo.js", "supportedTypes": ["movie", "tv", "anime"]},
        ],
    }
    vf = {"version": "1.2.3", "scrapers": [dict(main["scrapers"][0]), dict(main["scrapers"][1])]}
    (root / "manifest.json").write_text(json.dumps(main), encoding="utf-8")
    (root / "vf" / "manifest.json").write_text(json.dumps(vf), encoding="utf-8")

    old = (module.ROOT, module.STATE_PATH, module.MAIN_PATH, module.VF_PATH)
    module.ROOT = root
    module.STATE_PATH = root / "nuvio-client-id-state.json"
    module.MAIN_PATH = root / "manifest.json"
    module.VF_PATH = root / "vf" / "manifest.json"
    try:
        first = module.apply_policy(bootstrap_active=True)
        first_main = json.loads((root / "manifest.json").read_text())
        by_id = {row["id"].casefold(): row for row in first_main["scrapers"]}
        assert by_id["goated"]["id"] == "GOATED"
        assert by_id["goated"]["version"] == "1.0.1"
        assert by_id["streamzo"]["id"] == "streamzo"
        assert first["active_count"] == 1

        # A normal code/version refresh keeps the client identity stable.
        module.apply_policy(bootstrap_active=False)
        second_main = json.loads((root / "manifest.json").read_text())
        by_id2 = {row["id"].casefold(): row for row in second_main["scrapers"]}
        assert by_id2["goated"]["id"] == "GOATED"
        assert by_id2["goated"]["version"] == "1.0.1"

        # Disabled -> enabled toggles only that provider's exact client id.
        by_id2["streamzo"]["enabled"] = True
        (root / "manifest.json").write_text(json.dumps(second_main), encoding="utf-8")
        vf2 = json.loads((root / "vf" / "manifest.json").read_text())
        next(row for row in vf2["scrapers"] if row["id"].casefold() == "streamzo")["enabled"] = True
        (root / "vf" / "manifest.json").write_text(json.dumps(vf2), encoding="utf-8")
        module.apply_policy(bootstrap_active=False)
        third_main = json.loads((root / "manifest.json").read_text())
        by_id3 = {row["id"].casefold(): row for row in third_main["scrapers"]}
        assert by_id3["streamzo"]["id"] == "STREAMZO"
        assert by_id3["streamzo"]["version"] == "1.0.1"

        third_vf = json.loads((root / "vf" / "manifest.json").read_text())
        vf_by_id = {row["id"].casefold(): row for row in third_vf["scrapers"]}
        assert vf_by_id["streamzo"]["id"] == "STREAMZO"
        assert vf_by_id["streamzo"]["version"] == "1.0.1"
    finally:
        module.ROOT, module.STATE_PATH, module.MAIN_PATH, module.VF_PATH = old

print("stable Nuvio activation refresh test passed")
