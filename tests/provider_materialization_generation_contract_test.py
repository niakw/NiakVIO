#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "scripts").resolve()))
from provider_materialization_generation import materialization_generation

verify_path = ROOT / "scripts" / "verify_provider_v3_reverse_rebuild.py"
spec = importlib.util.spec_from_file_location("reverse_generation_contract", verify_path)
assert spec and spec.loader
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

a = "11" * 32
b = "22" * 32
rows = [{"provider": "beta", "sha256": b}, {"provider": "alpha", "sha256": a}]
manual = hashlib.sha256()
for provider, digest in [("alpha", a), ("beta", b)]:
    manual.update(provider.encode("utf-8"))
    manual.update(bytes.fromhex(digest))
assert materialization_generation(rows) == manual.hexdigest()
assert materialization_generation(list(reversed(rows))) == manual.hexdigest()

for bad in (
    [],
    [{"provider": "alpha", "sha256": "bad"}],
    [{"provider": "alpha", "sha256": a}, {"provider": "ALPHA", "sha256": b}],
):
    try:
        materialization_generation(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"invalid generation rows accepted: {bad!r}")

raw = b"function demo(){\n  // publication-only comment\n  return 1;\n}\n"
published = verify.final_publication_bytes(raw)
assert published != raw
assert b"publication-only comment" not in published
assert verify.final_publication_bytes(published) == published

materializer = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")
reconciler = (ROOT / "scripts" / "reconcile_provider_static_authority.py").read_text(encoding="utf-8")
reverse = verify_path.read_text(encoding="utf-8")
assert "generation = materialization_generation(report_rows)" in materializer
assert 'doc["generation"] = materialization_generation(rows)' in reconciler
assert "published_generation = materialization_generation(published_rows)" in reverse
assert "rebuilt.get(\"generation\") != expected.get(\"generation\")" not in reverse
assert "final published byte digest mismatch" in reverse

print("PROVIDER_MATERIALIZATION_GENERATION_CONTRACT_OK canonical_order=1 publication_minimizer=1")

targeted = (ROOT / "scripts" / "materialize_provider_v3_one.py").read_text(encoding="utf-8")
domain = (ROOT / "scripts" / "domain_refresh_transaction_v2.py").read_text(encoding="utf-8")
assert "from provider_materialization_generation import materialization_generation" in targeted
assert "document[\"generation\"] = materialization_generation(rows)" in targeted
assert "def _materialization_generation(" not in targeted
assert "from provider_materialization_generation import materialization_generation" in domain
assert 'materialization["generation"] = materialization_generation(material_rows)' in domain
assert "def _generation(rows:" not in domain
print("PROVIDER_MATERIALIZATION_GENERATION_SECONDARY_PATHS_OK targeted=1 domain_refresh=1")
