#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = (ROOT / "scripts" / "reconcile_domain_refresh_provenance.py").read_text(encoding="utf-8")

assert "DOMAIN_REFRESH_MINIMIZER_PROOF_V61" in script
assert "def canonical_minimizer_proof(" in script
assert '"schema_version": MINIMIZER_PROOF_SCHEMA' in script
assert '"tool": "scripts/provider_v3_minimizer.py"' in script
assert '"production_enabled": True' in script
assert '"terser_allowed": False' in script
assert "result = minimize_text(original)" in script
assert "validate_transform(original, result.text)" in script
assert "if result.text != original:" in script
assert 'provenance_row["final_minimizer"] = minimizer_proof' in script
assert "material_filename != filename" in script
assert "actual_digest != digest" in script

print("domain refresh provenance minimizer contract passed: touched asset must be fixed-point before fresh proof binding")
