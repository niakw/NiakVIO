#!/usr/bin/env python3
"""Run Domain Refresh with current-registry scoping and deterministic tie-breaking.

provider-hubs.json is the current executable address registry. Legacy
provider-overrides.official_domain_hubs entries remain historical knowledge but
must never recreate work for archived providers. Inside the current registry,
the authoritative hub resolver still owns trust scoring; this wrapper only
breaks equal-score ties using explicit semantic and provider-brand labels.
"""
from __future__ import annotations

import re
from typing import Any, Callable

import domain_refresh_transaction_v2 as transaction
import refresh_authoritative_hub_domains as refresh

PRIMARY_TOKENS = (
    "principal",
    "principale",
    "primary",
    "recommended",
    "recommande",
    "recommandé",
    "prioritaire",
    "preferred",
    "current",
    "actuel",
    "actuelle",
)
BACKUP_TOKENS = (
    "backup",
    "secours",
    "miroir",
    "mirror",
    "alternative",
    "fallback",
    "secondaire",
    "secondary",
)


def _fold(value: object) -> str:
    return str(value or "").strip().casefold()


def _compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", _fold(value))


def semantic_priority(row: dict[str, Any]) -> int:
    label = _fold(row.get("label"))
    primary = sum(1 for token in PRIMARY_TOKENS if token in label)
    backup = sum(1 for token in BACKUP_TOKENS if token in label)
    return primary - backup


def brand_priority(provider_id: object, row: dict[str, Any]) -> int:
    """Prefer concise provider-branded labels over anonymous equal-score links."""
    label = _fold(row.get("label"))
    if not label or len(label) > 80:
        return 0
    provider = _compact(provider_id)
    compact_label = _compact(label)
    if not provider or not compact_label:
        return 0
    return int(compact_label == provider or compact_label.startswith(provider))


def current_registry_hub_configs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return only provider-hubs.json current rows, enriched from provider patches.

    Calling merge_hub_registry with no embedded official_domain_hubs prevents
    historical legacy-only rows from being resurrected while preserving current
    registry aliases/sources and provider patch context.
    """
    clean_config = {"provider_patches": config.get("provider_patches") or {}}
    return transaction.resolver.merge_hub_registry(clean_config)


def _candidate_key(provider_id: object, row: dict[str, Any]) -> tuple[int, int, int, int, str]:
    # Trust score remains the first and strongest authority. Semantic labels only
    # break ties. A concise provider-branded label then beats an anonymous link;
    # document order remains the final conservative signal before lexical order.
    return (
        -int(row.get("score") or 0),
        -semantic_priority(row),
        -brand_priority(provider_id, row),
        int(row.get("document_index") if row.get("document_index") is not None else 10**9),
        _fold(row.get("url")),
    )


def prioritize_authoritative_item(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("status") != "site_authoritative":
        return item
    candidates = [dict(row) for row in (item.get("site_candidates") or []) if isinstance(row, dict)]
    if len(candidates) < 2:
        return item

    provider_id = item.get("provider_id")
    ordered = sorted(candidates, key=lambda row: _candidate_key(provider_id, row))
    selected = ordered[0]
    terminal = str(selected.get("url") or "").strip().rstrip("/")
    if not terminal:
        return item

    previous = str(item.get("official_site") or "").strip().rstrip("/")
    item["site_candidates"] = ordered
    item["official_site"] = terminal
    item["site_final_url"] = terminal
    item["selected_source_type"] = selected.get("source_type")
    item["selected_source"] = selected.get("source")
    item["candidate_score"] = selected.get("score")
    if terminal != previous:
        item["candidate_priority_adjusted"] = True
        item["candidate_priority_previous"] = previous
        item["candidate_priority_reason"] = "equal-score semantic/brand primary preference"
    return item


def install_priority_wrapper() -> Callable[..., dict[str, Any]]:
    original = refresh.resolve_authoritative_hub_domain

    def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return prioritize_authoritative_item(original(*args, **kwargs))

    refresh.resolve_authoritative_hub_domain = wrapped
    return original


def main() -> int:
    install_priority_wrapper()
    transaction._authoritative_hub_configs = current_registry_hub_configs
    return transaction.main()


if __name__ == "__main__":
    raise SystemExit(main())
