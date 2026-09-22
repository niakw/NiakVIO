#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "domain-refresh.yml"
TRANSACTION = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
VALIDATOR = ROOT / "scripts" / "validate_release_integrity.py"

text = WORKFLOW.read_text(encoding="utf-8")
source = TRANSACTION.read_text(encoding="utf-8")
validator = VALIDATOR.read_text(encoding="utf-8")

assert text.startswith("name: CORE - Domain Refresh")
assert "23 3 * * *" in text
assert "contents: write" in text
assert "bulk-guard:" in text
assert "Defer domain mutation during bulk onboarding" in text
assert '"provider: bulk stage "*|"provider: bulk activate "*' in text
assert "needs: bulk-guard" in text
assert "if: needs.bulk-guard.outputs.run == 'true'" in text
assert "github.event.head_commit.message" not in text, "bulk guard must not depend on fragile job-level event expression parsing"
assert "scripts/domain_refresh_transaction_v2.py" in text
assert "--apply" in text
assert "provider-hubs.json" in text
assert "published-manifest-baseline.json" in text
assert "python scripts/generate_language_manifests.py" in text
assert "python scripts/sync_release_versions.py" in text
assert '--previous "$RUNNER_TEMP/published-manifest-baseline.json"' in text
assert "python tests/release_auto_bump_test.py" in text
assert "python scripts/generate_hub46_manifest.py" in text
assert "python scripts/build_hub46_native_manifest.py" in text
assert "python scripts/generate_release_hashes.py" in text
assert "python scripts/validate_release_integrity.py" in text
assert 'git rev-parse HEAD > "$RUNNER_TEMP/domain-base-sha"' in text
assert 'PROVIDER_SHA="$(git rev-parse HEAD)"' in text
assert 'BASE_SHA="$(cat "$RUNNER_TEMP/domain-base-sha")"' in text
assert "NUVIO_SKIP_ACTIVATION_PRESERVATION: '1'" not in text, "Domain Refresh is address authority and must preserve catalogue activation"
assert 'os.environ.get("NUVIO_SKIP_ACTIVATION_PRESERVATION") != "1"' in validator
assert "FIELD_RELEASE_INTEGRITY activation_preservation=skipped owner=domain_refresh" in validator
assert "provider_dns_preflight.mjs" in text
assert 'print(lines[0] if lines else "")' in text
assert 'splitlines()[0]' not in text
assert "python scripts/audit_provider_v3_static.py --domain-only" in text
assert "gh workflow run sync.yml --ref main -f mode=quick || echo \"FIELD_DOMAIN_POST_PUBLISH_DISPATCH_WARN workflow=sync\"" in text
assert "gh workflow run provider-disabled-lifecycle.yml --ref main || echo \"FIELD_DOMAIN_POST_PUBLISH_DISPATCH_WARN workflow=provider-disabled-lifecycle\"" in text
assert text.count("python scripts/audit_provider_v3_static.py --domain-only") == 2
assert "python scripts/audit_provider_v3_static.py\n" not in text
assert "continue-on-error: true" in text, "DNS/HTTP observation must not gate hub address authority"
assert "authoritative_hub_domain_refresh_test.py" in text
assert "provider_v3_workflow_ownership_test.py" in text
assert "git diff --exit-code -- scripts/provider_patches provider-bases provider-type-policy.json" in text
assert "update_provider_v3_domain_config.py" not in text, "partial officialSite-only updater must not own Domain Refresh"
assert "validate_domain_refresh_scope.py" not in text, "old official_site-only scope validator is obsolete"
assert "materialize_provider_v3_all.py" not in text, "domain changes must not rematerialize/rewrite the global Core"
assert "project_domain_owned_provider_legos" in source
assert "provider_domain_runtime_projection_drift_ids" in source
assert '"runtime_projection_drift"' in source
for forbidden in (
    "run_adaptive_deep_repair.py",
    "run_adaptive_quick_repair.py",
    "run_provider_repair_pipeline_v6.py",
    "promote_candidates.py",
    "promote_refresh_candidates.py",
):
    assert forbidden not in text, f"Domain Refresh must never invoke Repair: {forbidden}"

commit_lines = [line.strip() for line in text.splitlines() if "git commit -m " in line]
assert len(commit_lines) == 2, commit_lines
assert "chore(domains): stage Provider v3 domain generation" in commit_lines[0]
assert "chore(domains): finalize Provider v3 domain transaction" in commit_lines[1]
assert "push origin HEAD:main" in text
assert text.count("push origin HEAD:main") == 1, "Domain Refresh must expose only one remote publication point"
assert "gh workflow run sync.yml --ref main -f mode=quick" in text
assert text.count("gh workflow run provider-disabled-lifecycle.yml --ref main") == 1

for required in (
    "provider-hubs-authoritative-terminal",
    "sync_registry_terminal",
    "sync_patch_domain_authority",
    "rebuild_provider_configs",
    "provider_domain_projection_drift_ids",
    "has_domain_refresh_source",
    '"projection_drift"',
    "DOMAIN_REFRESH_CURRENT_SCOPE_PROJECTION_DRIFT_V1",
    "DOMAIN_CONFIG_DATA_OWNERSHIP_V1",
    "replace_provider_fix",
    "project_domain_owned_provider_legos",
    "provider_domain_runtime_projection_drift_ids",
    "domain refresh changed bytes beyond CONFIG + authorized provider host projection",
    '"core_mutation": False',
):
    assert required in source, required

# The transaction is normally executed as scripts/domain_refresh_transaction_v2.py,
# which naturally places scripts/ on sys.path. Import-based contract tests must
# reproduce that module search path explicitly rather than depending on cwd.
scripts_dir = str(ROOT / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
spec = importlib.util.spec_from_file_location("domain_refresh_transaction_v2", TRANSACTION)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Regression 0: domain projection may update an explicit old->current host inside
# provider-owned runtime Lego, while leaving Core and unrelated provider bytes
# exactly unchanged.
from provider_patch_blocks import render_managed_fix
synthetic = "\n".join([
    render_managed_fix(
        "PROVIDER.DEMO.CONFIG.V1",
        'const NIAKVIO_PROVIDER_MODEL={};',
        data={"providerId": "demo"},
    ),
    render_managed_fix(
        "PROVIDER.DEMO.RUNTIME.V1",
        'const SITE="https://old.example/path?q=1";',
        data={"runtimeFamily": "demo"},
    ),
    "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */",
    render_managed_fix(
        "CORE.DEMO.TEST.V1",
        'const CORE_SITE="https://old.example/must-stay";',
        data={"scope": "core"},
    ),
])
projected, projected_fixes = module.project_domain_owned_provider_legos(
    synthetic,
    "demo",
    "PROVIDER.DEMO.CONFIG.V1",
    {
        "official_site": "https://new.example",
        "runtime_domain_replacements": {"old.example": "new.example"},
        "domain_substitutions": {"old.example": "new.example"},
    },
)
assert projected_fixes == ["PROVIDER.DEMO.RUNTIME.V1"], projected_fixes
assert 'SITE="https://new.example/path?q=1"' in projected, projected
assert 'CORE_SITE="https://old.example/must-stay"' in projected, projected
assert module._strip_domain_owned_blocks(
    synthetic,
    ["PROVIDER.DEMO.CONFIG.V1", "PROVIDER.DEMO.RUNTIME.V1"],
) == module._strip_domain_owned_blocks(
    projected,
    ["PROVIDER.DEMO.CONFIG.V1", "PROVIDER.DEMO.RUNTIME.V1"],
)

# Historical pre-managed runtime is also domain-projectable, but only before the
# Core boundary. This is the exact AnimeVOSTFR split-brain shape found in main.
raw_synthetic = (
    synthetic.replace(
        render_managed_fix(
            "PROVIDER.DEMO.RUNTIME.V1",
            'const SITE="https://old.example/path?q=1";',
            data={"runtimeFamily": "demo"},
        ),
        'const NIAKVIO_PROVIDER_RUNTIME_LEGO_V1={"base":"https://old.example"};\n',
    )
)
raw_projected, raw_scopes = module.project_domain_owned_provider_legos(
    raw_synthetic,
    "demo",
    "PROVIDER.DEMO.CONFIG.V1",
    {
        "official_site": "https://new.example",
        "runtime_domain_replacements": {"old.example": "new.example"},
    },
)
assert "PROVIDER.DEMO.RAW.DOMAIN" in raw_scopes, raw_scopes
assert '"base":"https://new.example"' in raw_projected, raw_projected
assert 'CORE_SITE="https://old.example/must-stay"' in raw_projected, raw_projected

# Real-catalogue regression: the old AnimeVOSTFR redirect seed may remain inside
# CONFIG as substitution history, but executable provider bytes before Core must
# use the current root after Domain Refresh projection.
manifest_now = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
anime_row = next(
    row for row in manifest_now.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").casefold() == "animevostfr"
)
anime_text = (ROOT / str(anime_row["filename"])).read_text(encoding="utf-8")
anime_config = module._config_fix_id(anime_text, "animevostfr")
anime_boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
assert anime_text.count(anime_boundary) == 1, anime_row
anime_provider_region = anime_text[:anime_text.index(anime_boundary)]
anime_provider_without_config = module.strip_managed_fix(anime_provider_region, anime_config)
assert "https://v2.animevostfr.org" not in anime_provider_without_config, anime_row
assert "https://animevostfr.org" in anime_provider_without_config, anime_row

# Regression 1: stale embedded official_domain_hubs must not shadow provider-hubs.json.
legacy_config = {
    "official_domain_hubs": {
        "frenchstream": {
            "hub": "https://legacy.invalid/",
            "resolver": "redirect",
            "sources": [{"type": "redirect", "url": "https://legacy.invalid/", "priority": 999}],
        }
    },
    "provider_patches": {},
}
merged = module._authoritative_hub_configs(legacy_config)
assert merged["frenchstream"]["hub"] == "https://fstream.org/", merged["frenchstream"]
assert any(
    row.get("url") == "https://fstream.org/" and row.get("type") == "hub"
    for row in merged["frenchstream"].get("sources") or []
), merged["frenchstream"]

# Regression 2: a newly observed terminal becomes the registry current direct URL,
# while older terminals remain bounded fallback/address knowledge.
registry = {
    "providers": {
        "frenchstream": {
            "id": "frenchstream",
            "hub": "https://fstream.org/",
            "direct": "https://fs16.lol/",
            "direct_candidates": ["https://fs16.lol/", "https://fs09.lol/"],
            "allowed_terminal_hosts": ["fs16.lol", "fs09.lol"],
        }
    }
}
assert module.sync_registry_terminal(registry, "frenchstream", "https://fs27.lol") is True
row = registry["providers"]["frenchstream"]
assert row["hub"] == "https://fstream.org/"
assert row["direct"] == "https://fs27.lol/"
assert row["direct_candidates"][0] == "https://fs27.lol/"
assert "https://fs16.lol/" in row["direct_candidates"]
assert row["allowed_terminal_hosts"][0] == "fs27.lol"

pinned_registry = {
    "providers": {
        "kehflix": {
            "id": "kehflix",
            "direct": "https://kehflix.com/",
            "direct_authority": "explicit_current",
            "direct_candidates": ["https://kehflix.com/"],
            "allowed_terminal_hosts": ["kehflix.com"],
        }
    }
}
try:
    module.sync_registry_terminal(pinned_registry, "kehflix", "https://kehflix.lol")
except RuntimeError as exc:
    assert "explicit_current" in str(exc), exc
else:
    raise AssertionError("explicit_current terminal must refuse a contradictory hub observation")
assert pinned_registry["providers"]["kehflix"]["direct"] == "https://kehflix.com/"

# Regression 2a.1: a terminal observed by Domain must never resurrect a provider
# carrying an explicit manual-off lifecycle decision. The terminal remains
# bounded forensic address knowledge until a separate authority requalification
# clears manual_off_reason.
manual_off_registry = {
    "providers": {
        "showbox": {
            "id": "showbox",
            "manifest_status": "Désactivé",
            "direct": "https://www.showbox.media/",
            "direct_candidates": ["https://www.showbox.media/"],
            "allowed_terminal_hosts": ["showbox.media", "www.showbox.media"],
            "activation_eligible": False,
            "manual_off_reason": "manual_off_no_current_authority_search_only",
        }
    }
}
assert module.sync_registry_terminal(
    manual_off_registry,
    "showbox",
    "https://www.showbox.media",
) is True
manual_off_row = manual_off_registry["providers"]["showbox"]
assert manual_off_row["direct"] is None, manual_off_row
assert "https://www.showbox.media/" in manual_off_row["direct_candidates"], manual_off_row
assert manual_off_row["manual_off_reason"] == "manual_off_no_current_authority_search_only"

# Regression 2b: stale published domain CONFIG must be distinguishable from
# already-current structured authority.  This is the Kehflix state that used to
# make Domain Refresh report applied=0/bundles=0 forever.
stale_projection = {
    "officialSite": "https://kehflix.lol",
    "knownSite": "https://kehflix.lol/",
    "officialHub": "https://kehflix.wiki/",
    "domainSubstitutions": {"kehflix.wiki": "kehflix.lol"},
}
current_projection = {
    "officialSite": "https://kehflix.com/",
    "knownSite": "https://kehflix.com",
    "officialHub": "https://kehflix.wiki",
    "domainSubstitutions": {"kehflix.lol": "kehflix.com"},
}
assert module._normalized_domain_projection(stale_projection) != module._normalized_domain_projection(current_projection)
equivalent_current_projection = {
    "officialSite": "https://kehflix.com",
    "knownSite": "https://kehflix.com/",
    "officialHub": "https://kehflix.wiki/",
    "domainSubstitutions": {"KEHFLIX.LOL": "KEHFLIX.COM"},
}
assert module._normalized_domain_projection(current_projection) == module._normalized_domain_projection(equivalent_current_projection)

# Regression 2c: published domain projection drift is independent from this
# run's network-resolution verdict. A current provider whose accepted structured
# DATA is already authoritative must still be eligible for CONFIG-only repair.
assert "provider_domain_projection_drift_ids(sorted(current_provider_ids))" in source
assert "provider_domain_projection_drift_ids(resolved_provider_ids)" not in source

# Regression 2d: Domain Refresh may not publish unrelated current structured
# changes just because a provider's CONFIG bundle is being rotated for a domain.
published_data = {
    "providerId": "yflix",
    "officialSite": "https://old.example",
    "knownSite": "https://old.example",
    "officialHub": None,
    "domainSubstitutions": {"old.example": "old.example"},
    "apiRecipe": {"base": "https://enc-dec.app", "recipeKind": "typed-resolver-api"},
    "routes": ["/published-route"],
}
expected_data = {
    **published_data,
    "officialSite": "https://new.example",
    "knownSite": "https://new.example",
    "domainSubstitutions": {"old.example": "new.example"},
    "apiRecipe": None,
    "routes": ["/new-unrelated-route"],
}
domain_projected = module.project_domain_owned_config_data(published_data, expected_data)
assert domain_projected["officialSite"] == "https://new.example"
assert domain_projected["knownSite"] == "https://new.example"
assert domain_projected["domainSubstitutions"] == {"old.example": "new.example"}
assert domain_projected["apiRecipe"] == published_data["apiRecipe"]
assert domain_projected["routes"] == published_data["routes"]
assert domain_projected["providerId"] == "yflix"

# Regression 3: only domain-connected runtime maps follow a terminal rotation;
# unrelated API replacement DATA must remain untouched.
patch = {
    "official_site": "https://fs16.lol",
    "official_hub": "https://old-hub.invalid",
    "runtime_domain_replacements": {
        "fs09.lol": "fs16.lol",
        "api.example.old": "api.example.new",
        "fs27.lol": "fs16.lol",
    },
    "domain_substitutions": {"fs03.lol": "fs16.lol"},
    "replacements": {"legacy.fs.example": "fs16.lol"},
    "notes": ["must remain byte-for-byte unrelated"],
}
fields = module.sync_patch_domain_authority(
    patch,
    {"hub": "https://fstream.org/"},
    "https://fs27.lol",
)
assert "official_site" in fields and "official_hub" in fields
assert patch["official_site"] == "https://fs27.lol"
assert patch["official_hub"] == "https://fstream.org"
assert patch["runtime_domain_replacements"]["fs16.lol"] == "fs27.lol"
assert patch["runtime_domain_replacements"]["fs09.lol"] == "fs27.lol"
assert "fs27.lol" not in patch["runtime_domain_replacements"], "current host must not redirect backwards"
assert patch["runtime_domain_replacements"]["api.example.old"] == "api.example.new"
assert patch["notes"] == ["must remain byte-for-byte unrelated"]

print("CORE domain refresh v2 contract passed: hub registry authority + registry persistence + CONFIG-only rebuild + cache-safe bump + activation-neutral integrity")
