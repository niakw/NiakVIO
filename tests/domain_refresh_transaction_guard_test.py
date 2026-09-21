#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import domain_refresh_transaction_v2 as module
from validate_domain_refresh_transaction import validate


def docs():
    before_overrides = {
        "provider_patches": {
            "demo": {"official_site": "https://demo-new.example"},
        }
    }
    before_hubs = {
        "providers": {
            "demo": {
                "id": "demo",
                "hub": "https://hub.example/",
                "direct": "https://demo-new.example/",
                "direct_candidates": ["https://demo-new.example/", "https://demo-old.example/"],
                "allowed_terminal_hosts": ["demo-new.example", "demo-old.example"],
            }
        }
    }
    before_history = {
        "providers": {
            "demo": {
                "current": {"url": "https://demo-new.example"},
                "previous": [{"url": "https://demo-old.example"}],
            }
        }
    }
    return before_overrides, before_hubs, before_history


# Idempotent second pass is explicitly valid.
before_overrides, before_hubs, before_history = docs()
result = validate(
    before_overrides,
    copy.deepcopy(before_overrides),
    before_hubs,
    copy.deepcopy(before_hubs),
    before_history,
    {"providers": {"demo": {"status": "hub_unresolved"}}},
    {"changed": [], "registry_changed": []},
)
assert result["idempotent"] is True

# A provider config may catch up to a terminal the registry already contains.
# That is a valid reconciliation no-op: registry_changed stays empty because no
# registry bytes need changing, but the final registry/config terminals match.
before_overrides_lagging = copy.deepcopy(before_overrides)
before_overrides_lagging["provider_patches"]["demo"]["official_site"] = "https://demo-old.example"
after_overrides_synced = copy.deepcopy(before_overrides)
report_synced = {
    "providers": {
        "demo": {
            "status": "site_authoritative",
            "official_site": "https://demo-new.example",
            "selected_source_type": "hub",
            "site_candidates": [{
                "url": "https://demo-new.example",
                "label": "Demo homepage",
                "source_type": "hub",
            }],
        }
    }
}
result = validate(
    before_overrides_lagging,
    after_overrides_synced,
    before_hubs,
    copy.deepcopy(before_hubs),
    before_history,
    report_synced,
    {"changed": ["demo"], "registry_changed": []},
)
assert result["changed"] == ["demo"]
assert result["registry_changed"] == []

# A matching no-op is only valid when the final registry terminal really equals
# the provider terminal.
bad_hubs = copy.deepcopy(before_hubs)
bad_hubs["providers"]["demo"]["direct"] = "https://different.example/"
try:
    validate(
        before_overrides_lagging,
        after_overrides_synced,
        before_hubs,
        bad_hubs,
        before_history,
        report_synced,
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError:
    pass
else:
    raise AssertionError("registry/config divergence must fail closed")


# Stable official_site with a changed execution-domain mapping is still a real
# Domain Refresh mutation and must be accounted as changed. This is the exact
# shape that previously made 4khdhub appear as declared-but-not-actual.
mapping_before = copy.deepcopy(before_overrides)
mapping_before["provider_patches"]["demo"]["domain_substitutions"] = {"demo-old.example": "demo-new.example"}
mapping_after = copy.deepcopy(mapping_before)
mapping_after["provider_patches"]["demo"]["domain_substitutions"]["demo-alias.example"] = "demo-new.example"
result = validate(
    mapping_before,
    mapping_after,
    before_hubs,
    copy.deepcopy(before_hubs),
    before_history,
    report_synced,
    {"changed": ["demo"], "registry_changed": []},
)
assert result["changed"] == ["demo"]

# Domain Refresh is still fail-closed for any provider field outside its five
# explicit domain-authority fields.
forbidden_after = copy.deepcopy(before_overrides)
forbidden_after["provider_patches"]["demo"]["capability"] = "should-not-change"
try:
    validate(
        before_overrides,
        forbidden_after,
        before_hubs,
        copy.deepcopy(before_hubs),
        before_history,
        report_synced,
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError as exc:
    assert "non-domain fields" in str(exc)
else:
    raise AssertionError("non-domain provider mutation must fail closed")

# Provider-owned manifest asset URLs are domain metadata when and only when
# they rotate to the exact authoritative terminal. Other nested manifest fields
# remain outside Domain Refresh ownership.
asset_before = copy.deepcopy(before_overrides)
asset_before["provider_patches"]["demo"]["manifest_overrides"] = {
    "logo": "https://demo-old.example/favicon.ico",
    "enabled": True,
}
asset_after = copy.deepcopy(asset_before)
asset_after["provider_patches"]["demo"]["manifest_overrides"]["logo"] = "https://demo-new.example/favicon.ico"
asset_result = validate(
    asset_before,
    asset_after,
    before_hubs,
    copy.deepcopy(before_hubs),
    before_history,
    report_synced,
    {"changed": ["demo"], "registry_changed": []},
)
assert asset_result["changed"] == ["demo"]

asset_bad_field = copy.deepcopy(asset_after)
asset_bad_field["provider_patches"]["demo"]["manifest_overrides"]["enabled"] = False
try:
    validate(
        asset_before,
        asset_bad_field,
        before_hubs,
        copy.deepcopy(before_hubs),
        before_history,
        report_synced,
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError as exc:
    assert "non-domain manifest_overrides fields" in str(exc)
else:
    raise AssertionError("non-domain manifest override mutation must fail closed")

asset_wrong_host = copy.deepcopy(asset_before)
asset_wrong_host["provider_patches"]["demo"]["manifest_overrides"]["logo"] = "https://cdn.example/favicon.ico"
try:
    validate(
        asset_before,
        asset_wrong_host,
        before_hubs,
        copy.deepcopy(before_hubs),
        before_history,
        report_synced,
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError as exc:
    assert "does not follow terminal" in str(exc)
else:
    raise AssertionError("manifest asset rotation to unrelated host must fail closed")

# A configured redirect is authoritative only when the exact registry source
# declares address authority. Arbitrary redirects remain rejected.
redirect_before = copy.deepcopy(before_overrides)
redirect_after = copy.deepcopy(before_overrides)
redirect_after["provider_patches"]["demo"]["official_site"] = "https://demo-new.example"
redirect_registry = copy.deepcopy(before_hubs)
redirect_registry["providers"]["demo"]["sources"] = [{
    "type": "redirect",
    "url": "https://demo-old.example/",
    "purpose": "Authoritative current terminal redirect seed",
}]
redirect_report = {
    "providers": {
        "demo": {
            "status": "site_authoritative",
            "official_site": "https://demo-new.example",
            "selected_source_type": "redirect",
            "selected_source": "https://demo-old.example/",
            "site_candidates": [{
                "url": "https://demo-new.example",
                "label": "validated redirect destination",
                "source_type": "redirect",
                "source": "https://demo-old.example/",
            }],
        }
    }
}
result = validate(
    redirect_before,
    redirect_after,
    redirect_registry,
    copy.deepcopy(redirect_registry),
    before_history,
    redirect_report,
    {"changed": ["demo"], "registry_changed": []},
)
assert result["changed"] == ["demo"]

untrusted_redirect_registry = copy.deepcopy(redirect_registry)
untrusted_redirect_registry["providers"]["demo"]["sources"][0]["purpose"] = "Fallback redirect"
try:
    validate(
        redirect_before,
        redirect_after,
        untrusted_redirect_registry,
        copy.deepcopy(untrusted_redirect_registry),
        before_history,
        redirect_report,
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError as exc:
    assert "non-authoritative source" in str(exc)
else:
    raise AssertionError("untrusted configured redirect must fail closed")

# Unresolved discovery may never mutate the published terminal.
after_overrides = copy.deepcopy(before_overrides)
after_overrides["provider_patches"]["demo"]["official_site"] = "https://other.example"
try:
    validate(
        before_overrides,
        after_overrides,
        before_hubs,
        copy.deepcopy(before_hubs),
        before_history,
        {"providers": {"demo": {"status": "hub_unresolved"}}},
        {"changed": ["demo"], "registry_changed": []},
    )
except AssertionError:
    pass
else:
    raise AssertionError("unresolved domain mutation must fail closed")

# JS/template constructors can never become registry terminals.
after_hubs = copy.deepcopy(before_hubs)
after_hubs["providers"]["demo"]["direct_candidates"].insert(0, "https://${esc(s.domain)}/")
try:
    validate(
        before_overrides,
        copy.deepcopy(before_overrides),
        before_hubs,
        after_hubs,
        before_history,
        {"providers": {"demo": {"status": "hub_unresolved"}}},
        {"changed": [], "registry_changed": ["demo"]},
    )
except AssertionError:
    pass
else:
    raise AssertionError("template URL must fail closed")

# A historical rollback advertised ambiguously by a hub must not replace current.
after_overrides = copy.deepcopy(before_overrides)
after_hubs = copy.deepcopy(before_hubs)
after_overrides["provider_patches"]["demo"]["official_site"] = "https://demo-old.example"
after_hubs["providers"]["demo"]["direct"] = "https://demo-old.example/"
report = {
    "providers": {
        "demo": {
            "status": "site_authoritative",
            "official_site": "https://demo-old.example",
            "selected_source_type": "hub",
            "site_candidates": [{
                "url": "https://demo-old.example",
                "label": "Visit",
                "source_type": "hub",
            }],
        }
    }
}
try:
    validate(
        before_overrides,
        after_overrides,
        before_hubs,
        after_hubs,
        before_history,
        report,
        {"changed": ["demo"], "registry_changed": ["demo"]},
    )
except AssertionError:
    pass
else:
    raise AssertionError("ambiguous historical rollback must fail closed")

# Explicit fresh hub wording is sufficient evidence for a legitimate rotation/reuse.
report["providers"]["demo"]["site_candidates"][0]["label"] = "Nouvelle adresse officielle"
result = validate(
    before_overrides,
    after_overrides,
    before_hubs,
    after_hubs,
    before_history,
    report,
    {"changed": ["demo"], "registry_changed": ["demo"]},
)
assert result["changed"] == ["demo"]

# A current authoritative hub may explicitly identify a historical domain as its
# homepage/principal target without date wording. This is fresh reuse evidence,
# unlike a generic "Visit" link.
report["providers"]["demo"]["site_candidates"][0]["label"] = "Demo homepage"
result = validate(
    before_overrides,
    after_overrides,
    before_hubs,
    after_hubs,
    before_history,
    report,
    {"changed": ["demo"], "registry_changed": ["demo"]},
)
assert result["changed"] == ["demo"]



# Already-current domain authority must remain byte-stable when an optional
# replacement map does not exist. Observation alone is not a domain mutation.
noop_patch = {
    "official_site": "https://animesalt.cx",
    "official_hub": "https://animesalt.ac/",
    "domain_substitutions": {"animesalt.link": "animesalt.cx"},
}
noop_before = json.dumps(noop_patch, sort_keys=True)
noop_fields = module.sync_patch_domain_authority(
    noop_patch,
    {"hub": "https://animesalt.ac/"},
    "https://animesalt.cx",
)
assert noop_fields == [], noop_fields
assert json.dumps(noop_patch, sort_keys=True) == noop_before, noop_patch
assert "runtime_domain_replacements" not in noop_patch

print("domain refresh transaction guard tests passed")
