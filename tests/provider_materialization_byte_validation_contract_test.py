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

# Single-provider publication-capable materialization must mirror the mandatory
# security finalization from reapply_published_overrides before raw-byte proof.
assert "from provider_security_hardening import assert_hardened, harden_bytes" in one
assert "security_hardened, security_report = harden_bytes(bundle)" in one
assert one.index("security_hardened, security_report = harden_bytes(bundle)") < one.index("verified_bundle, byte_validation = allmat.verify_bytes(bundle)")
hardening_at = one.index("security_hardened, security_report = harden_bytes(bundle)")
minimize_at = one.index("minimized = allmat.minimize_text(hardened_text)")
final_bundle_at = one.index('bundle = hardened_text.encode("utf-8")', minimize_at)
verify_at = one.index("verified_bundle, byte_validation = allmat.verify_bytes(bundle)", final_bundle_at)
assert hardening_at < minimize_at < final_bundle_at < verify_at
assert one.count("assert_hardened(hardened_text)") >= 2
assert 'assert_hardened(bundle.decode("utf-8", errors="strict"))' in one
assert '"securityHardening": {' in one

