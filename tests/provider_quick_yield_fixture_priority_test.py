#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

path = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("audit_provider_quick_yield", path)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

tasks, provider_count = audit.build_tasks()
current_runtime_authority = audit._current_census_provider_ids()
assert provider_count == len(current_runtime_authority), (provider_count, len(current_runtime_authority))
by = {(row["provider_id"], row["semantic_type"]): row for row in tasks}

lifecycle = json.loads(
    (ROOT / "automation/provider-disabled-lifecycle.json").read_text(encoding="utf-8")
)
archived = lifecycle.get("archived") if isinstance(lifecycle.get("archived"), dict) else {}

def current_task(provider: str, semantic: str):
    row = by.get((provider, semantic))
    if row is not None:
        return row
    record = archived.get(provider) if isinstance(archived, dict) else None
    assert isinstance(record, dict) and record.get("state") == "archived-provider-old", (
        provider, semantic, "missing-current-task-without-lifecycle-archive"
    )
    return None

movieshunt = by[("movieshunt", "movie")]
assert movieshunt["fixtures"][0]["title"] == "Sinners", movieshunt["fixtures"]
assert any(row["title"] == "Interstellar" for row in movieshunt["fixtures"]), movieshunt["fixtures"]

animesalt = by[("animesalt", "anime")]
assert animesalt["fixtures"][0]["title"] == "Death Note", animesalt["fixtures"]
assert 1 <= len(animesalt["fixtures"]) <= audit.MAX_SAMPLES, animesalt["fixtures"]
assert len({audit._fixture_identity(row) for row in animesalt["fixtures"]}) == len(animesalt["fixtures"]), animesalt["fixtures"]

vostfree = by[("vostfree", "anime")]
assert vostfree["fixtures"][0]["title"] == "Death Note", vostfree["fixtures"]

allanime = current_task("allanime", "anime")
if allanime is not None:
    assert allanime["fixtures"][0]["title"] == "One Piece", allanime["fixtures"]

moviesmod = by[("moviesmod", "movie")]
assert moviesmod["fixtures"][0]["title"] == "Interstellar", moviesmod["fixtures"]

flemmix_tv = by[("flemmix", "tv")]
assert flemmix_tv["fixtures"][0]["title"] == "House of the Dragon", flemmix_tv["fixtures"]

# Providers without corpus-owned fixtures still start from the canonical lane representative.
allwish = by[("allwish", "movie")]
assert allwish["fixtures"][0]["title"] == "Interstellar", allwish["fixtures"]

err = audit.safe_probe_error(
    "node:internal\nTypeError: fetch failed https://secret.example/path token=abc123\n"
)
assert err.startswith("TypeError:fetch failed <url>"), err
assert "secret.example" not in err and "abc123" not in err, err

print("provider quick-yield fixture priority contract passed")
