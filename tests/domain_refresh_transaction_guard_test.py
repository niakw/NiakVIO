#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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

print("domain refresh transaction guard tests passed")
