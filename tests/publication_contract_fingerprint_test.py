#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "reapply_published_overrides.py"

spec = importlib.util.spec_from_file_location("reapply_publication_fingerprint", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.PUBLICATION_CONTRACT_SCHEMA == 4
assert module.LEGACY_PUBLICATION_CONTRACT_SCHEMA == 2

# The stored per-provider build fingerprint must describe the final provenance
# row, not an intermediate state that is mutated again later in publication.
# Otherwise the immediate fixed-point --check reports provider-input-changed
# even though the just-generated artifacts are current.
source = SCRIPT.read_text(encoding="utf-8")
fingerprint_write = source.index('row["build_input_sha256"] = provider_build_input_sha(')
for mutation in (
    'row["activation_mode"] = "strict_current"',
    'row["activation_mode"] = AUDIT_QUARANTINE_MODE',
    'row["activation_mode"] = "configured_safety_quarantine"',
):
    assert source.index(mutation) < fingerprint_write, mutation
assert source.index('row.pop("catalogue_audit_quarantine_scopes", None)') < fingerprint_write

config_a = {
    "schema_version": 7,
    "blocked_domains": ["localhost"],
    "provider_patches": {
        "alpha": {"official_site": "https://alpha.example"},
        "beta": {"official_site": "https://beta.example"},
    },
    "provider_capabilities": {
        "alpha": {"strategy": "html_scraper"},
        "beta": {"strategy": "direct_media"},
    },
}
config_b = json.loads(json.dumps(config_a))
config_b["provider_patches"]["alpha"]["official_site"] = "https://alpha-new.example"

global_a = module.publication_contract_sha(config_a)
global_b = module.publication_contract_sha(config_b)
assert global_a == global_b, (global_a, global_b)
assert module.legacy_publication_contract_sha(config_a) != module.legacy_publication_contract_sha(config_b)

alpha_a = module.provider_policy_sha(config_a, "alpha")
alpha_b = module.provider_policy_sha(config_b, "alpha")
beta_a = module.provider_policy_sha(config_a, "beta")
beta_b = module.provider_policy_sha(config_b, "beta")
assert alpha_a != alpha_b, (alpha_a, alpha_b)
assert beta_a == beta_b, (beta_a, beta_b)

fingerprint_a = module.provider_build_input_sha("alpha", "a"*64, global_a, alpha_a, {})
fingerprint_b = module.provider_build_input_sha("alpha", "a"*64, global_a, alpha_b, {})
assert fingerprint_a != fingerprint_b

static_a = {
    "legacyProviderJsExecuted": False,
    "upstreamJsExecuted": False,
    "providers": {
        "alpha": {"model": {"knownSite": "https://alpha.example"}},
        "beta": {"model": {"knownSite": "https://beta.example"}},
    },
}
static_alpha_changed = json.loads(json.dumps(static_a))
static_alpha_changed["providers"]["alpha"]["model"]["knownSite"] = "https://alpha-new.example"

static_global_a = module.publication_contract_sha(config_a, static_a)
static_global_b = module.publication_contract_sha(config_a, static_alpha_changed)
assert static_global_a == static_global_b, (static_global_a, static_global_b)

alpha_static_a = module.provider_policy_sha(config_a, "alpha", static_a)
alpha_static_b = module.provider_policy_sha(config_a, "alpha", static_alpha_changed)
beta_static_a = module.provider_policy_sha(config_a, "beta", static_a)
beta_static_b = module.provider_policy_sha(config_a, "beta", static_alpha_changed)
assert alpha_static_a != alpha_static_b, (alpha_static_a, alpha_static_b)
assert beta_static_a == beta_static_b, (beta_static_a, beta_static_b)

static_global_changed = json.loads(json.dumps(static_a))
static_global_changed["upstreamJsExecuted"] = True
assert (
    module.publication_contract_sha(config_a, static_a)
    != module.publication_contract_sha(config_a, static_global_changed)
)

# Shared Core Lego source is part of the global publication fingerprint.
# A Core source change must invalidate already-published provider bytes instead
# of passing projection reconcile as a false fixed point.
captured_contract_files = []
original_contract_file_hashes = module._contract_file_hashes
try:
    def capture_contract_files(relatives):
        relatives = set(relatives)
        captured_contract_files.append(relatives)
        return {relative: "0" * 64 for relative in relatives}

    module._contract_file_hashes = capture_contract_files
    config_global_hook = json.loads(json.dumps(config_a))
    config_global_hook["global_fixture_policy"] = {
        "global_discovery_hook": "scripts/provider_patches/global_media_enrichment_v1.py"
    }
    module.publication_contract_sha(config_global_hook, static_a)
finally:
    module._contract_file_hashes = original_contract_file_hashes

assert captured_contract_files
contract_files = captured_contract_files[-1]
assert module.GLOBAL_STREAM_PRESENTATION in contract_files, contract_files
assert module.GLOBAL_STREAM_FACTS in contract_files, contract_files
assert module.GLOBAL_STREAM_SANITIZER in contract_files, contract_files
assert "scripts/provider_patches/global_media_enrichment_v1.py" in contract_files, contract_files

base = {
    "name": "fixture",
    "version": "5.21.8",
    "lockfileVersion": 3,
    "requires": True,
    "packages": {
        "": {
            "name": "fixture",
            "version": "5.21.8",
            "dependencies": {"alpha": "1.0.0"},
        },
        "node_modules/alpha": {
            "version": "1.0.0",
            "resolved": "https://registry.npmjs.org/alpha/-/alpha-1.0.0.tgz",
            "integrity": "sha512-original",
        },
    },
}

with tempfile.TemporaryDirectory() as raw:
    path = Path(raw) / "package-lock.json"

    path.write_text(json.dumps(base), encoding="utf-8")
    first = module._publication_file_sha("package-lock.json", path)

    release_only = json.loads(json.dumps(base))
    release_only["version"] = "9.99.1"
    release_only["packages"][""]["version"] = "9.99.1"
    path.write_text(json.dumps(release_only), encoding="utf-8")
    second = module._publication_file_sha("package-lock.json", path)
    assert second == first, (first, second)

    dependency_changed = json.loads(json.dumps(release_only))
    dependency_changed["packages"]["node_modules/alpha"]["version"] = "1.0.1"
    dependency_changed["packages"]["node_modules/alpha"]["integrity"] = "sha512-changed"
    path.write_text(json.dumps(dependency_changed), encoding="utf-8")
    third = module._publication_file_sha("package-lock.json", path)
    assert third != first, (first, third)

print("publication contract fingerprint v4 shared-core + provider-scoped tests passed")
