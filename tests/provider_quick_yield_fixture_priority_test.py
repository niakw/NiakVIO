#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

path = ROOT / "scripts" / "audit_provider_quick_yield.py"
spec = importlib.util.spec_from_file_location("audit_provider_quick_yield", path)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

from current_provider_scope import visible_provider_count

tasks, provider_count = audit.build_tasks()
assert provider_count == visible_provider_count(), (provider_count, visible_provider_count())
by = {(row["provider_id"], row["semantic_type"]): row for row in tasks}

movieshunt = by[("movieshunt", "movie")]
assert movieshunt["fixtures"][0]["title"] == "Sinners", movieshunt["fixtures"]
assert any(row["title"] == "Interstellar" for row in movieshunt["fixtures"]), movieshunt["fixtures"]

animesalt = by[("animesalt", "anime")]
assert animesalt["fixtures"][0]["title"] == "Death Note", animesalt["fixtures"]
assert 1 <= len(animesalt["fixtures"]) <= audit.MAX_SAMPLES, animesalt["fixtures"]
assert len({audit._fixture_identity(row) for row in animesalt["fixtures"]}) == len(animesalt["fixtures"]), animesalt["fixtures"]

vostfree = by[("vostfree", "anime")]
assert vostfree["fixtures"][0]["title"] == "Death Note", vostfree["fixtures"]

allanime = by[("allanime", "anime")]
assert allanime["fixtures"][0]["title"] == "One Piece", allanime["fixtures"]

moviesmod = by[("moviesmod", "movie")]
assert moviesmod["fixtures"][0]["title"] == "Interstellar", moviesmod["fixtures"]

flemmix_tv = by[("flemmix", "tv")]
assert flemmix_tv["fixtures"][0]["title"] == "House of the Dragon", flemmix_tv["fixtures"]

# Providers without corpus-owned fixtures still start from the canonical lane representative.
allwish = by[("allwish", "movie")]
assert allwish["fixtures"][0]["title"] == "Interstellar", allwish["fixtures"]

print("provider quick-yield fixture priority contract passed")
