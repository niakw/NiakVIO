#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_voiranime_homes_authority_v21_10.py"
OVERRIDES = ROOT / "provider-overrides.json"

spec = importlib.util.spec_from_file_location("v2110", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21.10 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

original = json.loads(OVERRIDES.read_text(encoding="utf-8"))
data = copy.deepcopy(original)
source_before = copy.deepcopy(data["provider_patches"]["voiranime-homes"])

module.apply_document(data)
module.validate_document(data)

canonical = data["provider_patches"]["voiranime"]
sibling = data["provider_patches"]["voiranime-homes"]
assert sibling == source_before, "sibling authority must be read-only"
assert canonical["official_hub"] == "https://voiranime.org.uk/"
assert canonical["official_site"] == "https://voiranime.homes"
assert canonical["domain_substitutions"]["voiranime.diy"] == "voiranime.homes"
assert canonical["runtime_domain_replacements"]["voiranime.diy"] == "voiranime.homes"

search = canonical["search_request_plan"][0]
assert search["base"] == "https://voiranime.homes"
assert search["route"] == "/engine/ajax/search.php"
assert search["requestSpec"]["method"] == "POST"
assert search["requestSpec"]["body"]["query"] == "{query}"
assert search["requestSpec"]["body"]["page"] == "1"
assert search["semanticTypes"] == ["anime"]

value = canonical["provider_value_plan"][0]
assert value["searchBase"] == "https://voiranime.homes"
assert value["searchRoute"] == "/engine/ajax/search.php"
assert value["semanticTypes"] == ["anime"]
assert value["steps"][0]["route"] == "/engine/ajax/manga_episodes_api.php?id={id}"
assert value["steps"][0]["role"] == "detail"

serialized = json.dumps(canonical, ensure_ascii=False)
assert "/index.php?newsid={id}" in serialized
assert "vidzy.cc" in serialized
assert "master.m3u8?" not in serialized
assert "embdmstrplayer.com/v2/" not in serialized
assert "token=" not in serialized.casefold()

# This migration must not mutate declared semantic catalogue capability. Movie
# remains visible repair debt until a fresh live proof qualifies the anime-film
# lane; only the executable structured plan is anime-scoped for now.
assert data.get("provider_capabilities", {}).get("voiranime", {}).get("catalogue_types") == original.get("provider_capabilities", {}).get("voiranime", {}).get("catalogue_types")

print("VoirAnime V21.10 tests passed: hub -> homes -> newsid -> episodes API, signed media runtime-only")
