#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
resolver=(ROOT/"scripts/resolve_provider_hubs.py").read_text(encoding="utf-8")
scope=(ROOT/"scripts/validate_domain_refresh_scope.py").read_text(encoding="utf-8")

assert text.startswith("name: CORE - Domain Refresh")
assert "23 3 * * *" in text
assert "contents: write" in text
assert "--apply" in text and "--domain-only" in text
assert "update_provider_v3_domain_config.py" in text
assert "domain-site-changes.json" in text
assert "generate_language_manifests.py" in text
assert "audit_provider_v3_static.py" in text
assert "prune_unreferenced_providers.py" in text
assert "generate_release_hashes.py" in text
assert "validate_release_integrity.py" in text
assert "provider_dns_preflight.mjs" in text
commit_lines=[line.strip() for line in text.splitlines() if "git commit -m " in line]
assert len(commit_lines) == 1, commit_lines
commit_line=commit_lines[0]
assert "chore(domains):" in commit_line
assert "validated" in commit_line
assert "Provider v3 primary domains" in commit_line
assert "push origin HEAD:main" in text
assert "gh workflow run sync.yml --ref main -f mode=quick" in text

assert 'allowed_source_types = {"hub", "telegram_public", "redirect"}' in resolver
assert "if not has_authoritative_hub_source(cfg):" in resolver
assert '"kind": "official_site"' in resolver

assert 'out.pop("official_site",None)' in scope
for forbidden in ("official_api","api_recipe","runtime_domain_replacements","replacements","patch_script_options"):
    assert forbidden not in scope, f"domain refresh scope must not allow {forbidden}"

for forbidden in ("run_adaptive_deep_repair.py","run_adaptive_quick_repair.py","promote_candidates.py","promote_refresh_candidates.py"):
    assert forbidden not in text
print("CORE domain refresh official_site-only hub-authority contract passed")
