#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
assert text.startswith("name: CORE - Domain Refresh")
assert "schedule:" in text and "23 3 * * *" in text
assert "contents: write" in text
assert "python scripts/resolve_provider_hubs.py" in text
assert "--apply --domain-only" in text, "daily refresh must apply primary-domain changes only"
assert "validate_domain_refresh_scope.py" in text
assert "materialize_provider_v3_domain_refresh.py" in text
assert "verify_provider_v3_reverse_rebuild.py" in text
assert "node scripts/provider_dns_preflight.mjs" in text and "--all-domains" in text
assert "git diff --exit-code -- scripts/provider_patches provider-bases provider_catalog.json provider-type-policy.json" in text
assert "git add provider-overrides.json provider-domain-history.json" in text
assert 'git commit -m "chore(domains): publish validated Provider v3 primary domains"' in text
assert "push origin HEAD:main" in text
assert "gh workflow run sync.yml --ref main -f mode=quick" in text
for forbidden in ("run_adaptive_deep_repair.py","run_adaptive_quick_repair.py","promote_candidates.py"):
    assert forbidden not in text
scope=(ROOT/"scripts/validate_domain_refresh_scope.py").read_text(encoding="utf-8")
assert 'out.pop("official_site",None)' in scope
for forbidden in ("official_api","api_recipe","runtime_domain_replacements","replacements","patch_script_options"):
    assert forbidden not in scope, f"domain scope unexpectedly allows {forbidden}"
print("CORE domain refresh official_site-only autonomous publication contract passed")
