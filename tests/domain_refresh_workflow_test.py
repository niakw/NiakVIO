#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / ".github" / "workflows" / "domain-refresh.yml").read_text(encoding="utf-8")

assert text.startswith("name: CORE - Domain Refresh")
assert "permissions:\n  contents: write\n  actions: write" in text
assert "persist-credentials: false" in text
assert "python scripts/resolve_provider_hubs.py" in text
assert "--include-disabled" in text
assert "--apply" in text, "CORE domain refresh must apply validated route migrations"
assert "node scripts/provider_dns_preflight.mjs" in text
assert "--manifest manifest.json" in text
assert "--hub-report health-output/provider-hub-report.json" in text
assert "--all-domains" in text
assert "--config domain-observation-config.json" in text
assert "DNS is diagnostic-only and never blocks route publication" in text
assert "provider-overrides.json provider-domain-history.json" in text
assert 'git commit -m "chore(domains): publish validated provider routes"' in text
assert "push origin HEAD:main" in text
assert text.count("gh workflow run sync.yml") == 1, (
    "route publication must explicitly dispatch exactly one Provider Pipeline run because GITHUB_TOKEN pushes do not recurse"
)
assert "gh workflow run sync.yml --ref main -f mode=quick -f phase=full" in text
assert "gh workflow run domain-refresh.yml" in text
assert "steps.route-change.outputs.changed == 'true'" in text
assert "domain-route-changes.json" in text
assert "manifest.json vf/manifest.json no-anime/manifest.json vf-no-anime/manifest.json" in text
assert "provider_catalog.json provider-hubs.json providers/ provider-bases/" in text
assert "actions/upload-artifact" in text

sync = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
assert "'provider-overrides.json'" in sync, (
    "route publication on main must naturally trigger CORE - Provider Pipeline"
)

print("CORE domain refresh apply + atomic route publication contract passed")
