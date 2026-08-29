#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADD = (ROOT / ".github/workflows/add-provider.yml").read_text(encoding="utf-8")
BRANDING = (ROOT / ".github/workflows/provider-branding-assets.yml").read_text(encoding="utf-8")
SCRIPT = (ROOT / "scripts/add_provider.py").read_text(encoding="utf-8")

for token in ("provider_id:", "hub:", "direct:", "telegram:", "api:", "search_queries:", "routes:", "types:"):
    assert token in ADD, token

dispatch_inputs = ADD.split("permissions:", 1)[0]
assert "logo_url:" not in dispatch_inputs
assert "emoji:" not in dispatch_inputs
assert "logo_url = normalized_url" not in SCRIPT
assert 'request.get("emoji")' not in SCRIPT

assert "Delegate automatic defaults to Provider branding assets engine" in ADD
assert "scripts/provider_branding_assets.py" in ADD
assert "--logo-url" not in ADD
assert "--emoji" not in ADD
assert "logo_url:" in BRANDING
assert "emoji:" in BRANDING
assert "--logo-url" in BRANDING
assert "--emoji" in BRANDING

for full_lab in (
    "native-tv-route-reader.yml",
    "native-mobile-android-reader.yml",
    "native-mobile-ios-reader.yml",
    "native-desktop-reader-acceptance.yml",
):
    assert full_lab not in ADD, full_lab
assert "Run bounded onboarding Lab on first declared type" in ADD
assert "nuvio_client_lab.cjs" in ADD

print("add provider workflow contract passed: routing=full-auto branding=dedicated full_native_labs=false")
