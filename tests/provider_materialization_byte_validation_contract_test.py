#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")
one=(ROOT/"scripts/materialize_provider_v3_one.py").read_text(encoding="utf-8")

assert "from provider_byte_stability import verify_bytes" in src
assert "verified_bundle, byte_validation = verify_bytes(bundle)" in src
assert "materialized provider artifact validation failed" in src
assert "materialized byte validator rewrote provider bytes" in src
assert '"byteValidation": {' in src

verify_at=src.index("verified_bundle, byte_validation = verify_bytes(bundle)")
digest_at=src.index("digest = hashlib.sha256(bundle).hexdigest()",verify_at)
write_at=src.index("(output_dir / filename).write_bytes(bundle)",digest_at)
assert verify_at < digest_at < write_at

print("provider materialization canonical byte-validation contract passed")

for candidate in (src, one):
    assert "verified_bundle, byte_validation =" in candidate
    assert "verify_bytes(bundle)" in candidate
    assert "materialized provider artifact validation failed" in candidate
    assert "materialized byte validator rewrote provider bytes" in candidate
    assert '"byteValidation": {' in candidate
    verify_at=candidate.index("verify_bytes(bundle)")
    digest_at=candidate.index("digest = hashlib.sha256(bundle).hexdigest()",verify_at)
    assert verify_at < digest_at
