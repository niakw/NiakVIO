#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")
one=(ROOT/"scripts/materialize_provider_v3_one.py").read_text(encoding="utf-8")

assert "from provider_byte_stability import verify_bytes" in src
assert "PROVIDER_V3_PARALLEL_BYTE_VALIDATION_V1" in src
assert "validation_pool.submit(verify_bytes, bundle)" in src
assert "verified_bundle, byte_validation = future.result()" in src
assert "byteValidationConcurrency" in src
assert "materialized provider artifact validation failed" in src
assert "materialized byte validator rewrote provider bytes" in src
assert '"byteValidation": {' in src

submit_at=src.index("validation_pool.submit(verify_bytes, bundle)")
resolve_at=src.index("verified_bundle, byte_validation = future.result()",submit_at)
digest_at=src.index("digest = hashlib.sha256(bundle).hexdigest()",resolve_at)
write_at=src.index("(output_dir / filename).write_bytes(bundle)",digest_at)
assert submit_at < resolve_at < digest_at < write_at
assert src.index("for pending in pending_validation:",submit_at) < resolve_at

print("provider materialization canonical byte-validation contract passed")

assert "verified_bundle, byte_validation = future.result()" in src
assert "validation_pool.submit(verify_bytes, bundle)" in src
assert "verified_bundle, byte_validation = allmat.verify_bytes(bundle)" in one
for candidate in (src, one):
    assert "materialized provider artifact validation failed" in candidate
    assert "materialized byte validator rewrote provider bytes" in candidate
    assert '"byteValidation": {' in candidate
