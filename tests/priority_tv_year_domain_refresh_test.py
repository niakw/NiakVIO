#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import refresh_authoritative_hub_domains as refresh
import resolve_provider_hubs as resolver

identity = (ROOT / "scripts/provider_patches/global_stream_identity_v1.py").read_text(encoding="utf-8")
assert "cross-client-shared-tmdb-owner-zero-episodic-year-v11" in identity
assert '"catalogueYearPolicy": "movie-only"' in identity
assert "q.seriesYear=" not in identity
assert "q.seasonYear=" not in identity
assert "if(!episodic(q)&&m.year&&years.length" in identity
assert "function contentLike(candidate,q)" in identity
assert "if(!episodic(q)&&years.length&&w.length>=1)return true;" in identity
assert "function contentLike(candidate){" not in identity
assert "if(years.length&&w.length>=1)return true;" not in identity
assert "__nuvioIdentityPolicyV1" in identity
assert "catalogueScore:catalogueScore" in identity
assert 'yearPolicy:"movie-only"' in identity

# Domain derivative reconciliation is invariant-based: whatever terminal is
# currently authoritative must become the unique target of connected mappings.
patch = {
    "official_site": "https://flemmix.current",
    "notes": ["active flemmix.previous mirror"],
    "domain_substitutions": {"flemmix.casa": "flemmix.previous"},
    "replacements": {"flemmix.previous": "flemmix.current"},
    "runtime_domain_replacements": {"flemmix.previous": "flemmix.current"},
    "manifest_overrides": {"logo": "https://flemmix.previous/favicon.ico"},
}
changes = refresh._reconcile_domain_derivatives(
    patch, "https://flemmix.current", "https://flemmix.current"
)
assert patch["domain_substitutions"]["flemmix.casa"] == "flemmix.current", patch
assert patch["manifest_overrides"]["logo"] == "https://flemmix.current/favicon.ico", patch
assert changes

# The published provider patch must track provider-hubs.json current authority;
# this test deliberately does not pin a rotating domain such as .kim/.men/.cloud.
overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))["providers"]
flemmix = overrides["provider_patches"]["flemmix"]
flemmix_hub = registry["flemmix"]
expected_site = str(flemmix_hub.get("direct") or "").rstrip("/")
assert resolver.is_http_url(expected_site), flemmix_hub
assert str(flemmix["official_site"]).rstrip("/") == expected_site, (flemmix, flemmix_hub)
expected_host = resolver.host(expected_site)
assert expected_host
assert all(
    resolver.host(value) != expected_host or resolver.host(key) != expected_host
    for key, value in (flemmix.get("domain_substitutions") or {}).items()
)
for mapping_name in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
    mapping = flemmix.get(mapping_name) or {}
    assert expected_host not in mapping, (mapping_name, mapping)
    for source, target in mapping.items():
        if resolver.host(target):
            assert resolver.host(target) == expected_host, (mapping_name, source, target, expected_site)
logo = str(flemmix.get("manifest_overrides", {}).get("logo") or "")
if logo:
    assert resolver.host(logo) == expected_host, (logo, expected_site)

print("priority episodic-year-disabled/domain-refresh regression tests passed")
