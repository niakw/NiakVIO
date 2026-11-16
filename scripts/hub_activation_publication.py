#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import (  # noqa: E402
    projection_active_provider_ids,
    projection_disabled_provider_rows,
    projection_visible_provider_ids,
    projection_visible_provider_rows,
)


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def compute_scope() -> dict:
    rows = projection_visible_provider_rows()
    visible = projection_visible_provider_ids()
    active = projection_active_provider_ids()
    disabled = {
        cid(row.get("id"))
        for row in projection_disabled_provider_rows()
        if isinstance(row, dict) and cid(row.get("id"))
    }
    row_ids = {cid(row.get("id")) for row in rows if isinstance(row, dict) and cid(row.get("id"))}
    if row_ids != visible:
        raise AssertionError(
            "Global+France projection identity mismatch "
            f"missing={sorted(visible-row_ids)} extra={sorted(row_ids-visible)}"
        )
    if active | disabled != visible or active & disabled:
        raise AssertionError("Global+France activation partition is inconsistent")
    return {
        "schemaVersion": 4,
        "authority": "current Global+France projection union",
        "catalogueProviderCount": len(visible),
        "enabledProviderCount": len(active),
        "disabledProviderCount": len(disabled),
        "enabledProviders": sorted(active),
        "disabledProviders": sorted(disabled),
        "repairScope": "projection-active-only",
        "nativeLabPolicy": "current-projection-union; five-independent-labs",
    }


def write_scope(scope: dict) -> None:
    (ROOT / "automation/hub-activation-scope.json").write_text(
        json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def verify_catalog(scope: dict) -> None:
    catalog = load("provider_catalog.json")
    projected: dict[str, bool] = {}
    for row in catalog.get("providers") or []:
        if not isinstance(row, dict):
            continue
        scraper = row.get("scraper") if isinstance(row.get("scraper"), dict) else {}
        projections = row.get("projections") if isinstance(row.get("projections"), dict) else {}
        if projections.get("general") is not True and projections.get("vf") is not True:
            continue
        pid = cid(row.get("canonicalId") or scraper.get("id"))
        if not pid:
            continue
        projected[pid] = scraper.get("enabled") is not False

    expected = set(scope["enabledProviders"]) | set(scope["disabledProviders"])
    if set(projected) != expected:
        raise AssertionError(
            "provider_catalog projection membership differs from current Global+France scope "
            f"missing={sorted(expected-set(projected))} extra={sorted(set(projected)-expected)}"
        )
    active = {pid for pid, enabled in projected.items() if enabled}
    disabled = set(projected) - active
    if active != set(scope["enabledProviders"]) or disabled != set(scope["disabledProviders"]):
        raise AssertionError("provider_catalog projection activation differs from current Global+France scope")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-scope", action="store_true")
    ap.add_argument("--verify-catalog", action="store_true")
    ap.add_argument("--append-memory", action="store_true")
    args = ap.parse_args()
    scope = compute_scope()
    if args.write_scope:
        write_scope(scope)
    if args.verify_catalog:
        verify_catalog(scope)
    print(
        "HUB_ACTIVATION_SCOPE",
        f"visible={scope['catalogueProviderCount']}",
        f"enabled={scope['enabledProviderCount']}",
        f"disabled={scope['disabledProviderCount']}",
        "authority=projection-union",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
