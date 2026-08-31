#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / ".github" / "workflows" / "domain-refresh.yml").read_text(encoding="utf-8")

assert "permissions:\n  contents: read\n  actions: write" in text
assert "persist-credentials: false" in text
assert "python scripts/resolve_provider_hubs.py" in text
assert "node scripts/provider_dns_preflight.mjs" in text
assert "--manifest manifest.json" in text
assert "--hub-report health-output/provider-hub-report.json" in text
assert "--all-domains" in text
assert "--config domain-observation-config.json" in text
assert "domain-observation-config.json" in text
assert "health-output/dns-preflight-report.json" in text
assert "DNS is diagnostic-only and never blocks Health/Repair or publication." in text
assert "--apply" not in text, "domain observer must never apply migrations"
assert "git push" not in text and "git commit" not in text, (
    "domain observer must never publish provider state"
)
assert "provider_catalog.json" in text and "git diff --exit-code" in text, (
    "domain observation must prove that catalog/manifests/provider state remains unchanged"
)
assert "actions/upload-artifact" in text, "domain observations must be exported as CI evidence"
assert "provider-hub-report.json" in text and "dns-preflight-report.json" in text
assert "gh workflow run sync.yml" in text, (
    "daily domain observation must dispatch the canonical CORE pipeline when an authoritative route changes"
)
assert "-f mode=quick" in text and "-f phase=full" in text
assert "steps.route-change.outputs.changed == 'true'" in text
assert "domain-route-changes.json" in text

sync = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
assert "python scripts/resolve_provider_hubs.py" in sync and "--apply" in sync, (
    "only the canonical ARCHI2 pipeline applies validated hub/domain changes"
)
assert "scripts/provider_dns_preflight.mjs" not in sync
assert "dns-preflight-report.json" not in sync

print("ARCHI2 domain observation + canonical auto-refresh dispatch test passed")
