#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repair_voiranime_domain_authority_v1.py"
spec = importlib.util.spec_from_file_location("repair_voiranime_domain_authority_v1", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
changed = module.apply_document(data)
module.validate_document(data)
row = data["provider_patches"]["voiranime"]
assert row["official_site"] == "https://voir-anime.to"
assert row["proof_search_bases"] == ["https://voir-anime.to"]
for field in ("domain_substitutions", "runtime_domain_replacements"):
    mapping = row[field]
    assert "voir-anime.to" not in mapping, (field, mapping)
    assert "voiranime.homes" not in mapping, (field, mapping)
    assert mapping["voiranime.diy"] == "voir-anime.to"
    assert mapping["voiranime.com"] == "voir-anime.to"
    assert mapping["voiranime.store"] == "voir-anime.to"
# Current repository is expected to require the migration until publication;
# after publication this becomes an idempotence assertion instead.
assert isinstance(changed, bool)
print("voiranime domain authority v1 test passed: current .to preserved, stale aliases forward-only")
