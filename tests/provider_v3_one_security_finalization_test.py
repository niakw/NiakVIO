from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "materialize_provider_v3_one.py"
text = path.read_text(encoding="utf-8")

assert "TARGETED_MATERIALIZER_SECURITY_FINALIZATION_V61" in text
assert "from provider_security_hardening import assert_hardened, harden_bytes" in text
assert "bundle, security_report = harden_bytes(bundle)" in text
assert "assert_hardened(text)" in text
assert text.index("bundle, security_report = harden_bytes(bundle)") < text.index("# PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1")
assert '"securityFinalization"' in text

print("targeted Provider v3 materializer security finalization contract passed")
