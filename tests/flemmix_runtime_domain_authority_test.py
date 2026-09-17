#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "flemmix_current_runtime_v1.py"
text = PATCH.read_text(encoding="utf-8")

assert 'BASE="https://flemmix.me"' not in text, "Flemmix runtime must not hardcode the retired .me host"
assert "NIAKVIO_PROVIDER_MODEL.officialSite" in text, "Flemmix runtime must read canonical officialSite authority"
assert "NIAKVIO_PROVIDER_MODEL.knownSite" in text, "Flemmix runtime must retain knownSite fallback"
assert "_substituteDomain(raw)" in text, "Flemmix runtime base must pass through domain substitutions"
assert '"https://flemmix.cloud"' in text, "Flemmix fallback must be the current canonical .cloud host"
assert '"domainAuthority": "provider-model-official-site"' in text
assert '"legacyHostHardcoded": False' in text

print("flemmix runtime domain authority regression passed: canonical model-owned host, no retired .me pin")
