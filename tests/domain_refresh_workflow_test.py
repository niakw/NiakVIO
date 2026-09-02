#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
assert text.startswith("name: CORE - Domain Refresh")
assert "schedule:" in text and "23 3 * * *" in text
assert "contents: write" in text
assert "python scripts/resolve_provider_hubs.py" in text and "--apply" in text
assert "validate_domain_refresh_scope.py" in text
assert "materialize_provider_v3_route_refresh.py" in text
assert "verify_provider_v3_reverse_rebuild.py" in text
assert "node scripts/provider_dns_preflight.mjs" in text and "--all-domains" in text
assert "git diff --exit-code -- scripts/provider_patches provider-bases provider_catalog.json provider-type-policy.json" in text
assert "git add provider-overrides.json provider-domain-history.json" in text
assert 'git commit -m "chore(domains): publish validated Provider v3 routes"' in text
assert "push origin HEAD:main" in text
assert "gh workflow run sync.yml --ref main -f mode=quick" in text
assert "run_adaptive_deep_repair.py" not in text
assert "run_adaptive_quick_repair.py" not in text
assert "promote_candidates.py" not in text
print("CORE domain refresh route-only autonomous publication contract passed")
