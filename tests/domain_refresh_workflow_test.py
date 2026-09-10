#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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
assert "scripts/domain_refresh_transaction_v2.py" in text
assert "--apply" in text
assert "provider-hubs.json" in text
assert "published-manifest-baseline.json" in text
assert "python scripts/generate_language_manifests.py" in text
assert "python scripts/sync_release_versions.py" in text
assert '--previous "$RUNNER_TEMP/published-manifest-baseline.json"' in text
assert "python tests/release_auto_bump_test.py" in text
assert "python scripts/generate_release_hashes.py" in text
assert "python scripts/validate_release_integrity.py" in text
assert "NUVIO_SKIP_ACTIVATION_PRESERVATION: '1'" in text
assert 'os.environ.get("NUVIO_SKIP_ACTIVATION_PRESERVATION") != "1"' in validator
assert "FIELD_RELEASE_INTEGRITY activation_preservation=skipped owner=domain_refresh" in validator
assert "provider_dns_preflight.mjs" in text
assert "continue-on-error: true" in text, "DNS/HTTP observation must not gate hub address authority"
assert "authoritative_hub_domain_refresh_test.py" in text
assert "provider_v3_workflow_ownership_test.py" in text
assert "git diff --exit-code -- scripts/provider_patches provider-bases provider-type-policy.json" in text
assert "update_provider_v3_domain_config.py" not in text, "partial officialSite-only updater must not own Domain Refresh"
assert "validate_domain_refresh_scope.py" not in text, "old official_site-only scope validator is obsolete"
assert "materialize_provider_v3_all.py" not in text, "domain changes must not rematerialize/rewrite the global Core"
for forbidden in (
    "run_adaptive_deep_repair.py",
    "run_adaptive_quick_repair.py",
    "run_provider_repair_pipeline_v6.py",
    "promote_candidates.py",
    "promote_refresh_candidates.py",
):
    assert forbidden not in text, f"Domain Refresh must never invoke Repair: {forbidden}"

commit_lines = [line.strip() for line in text.splitlines() if "git commit -m " in line]
assert len(commit_lines) == 1, commit_lines
assert "chore(domains):" in commit_lines[0]
assert "Provider v3 domain transaction" in commit_lines[0]
assert "push origin HEAD:main" in text
assert "gh workflow run sync.yml --ref main -f mode=quick" in text

for required in (
    "provider-hubs-authoritative-terminal",
    "sync_registry_terminal",
    "sync_patch_domain_authority",
    "rebuild_provider_configs",
    "replace_provider_fix",
    "domain refresh changed bytes outside CONFIG Lego",
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
