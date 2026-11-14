#!/usr/bin/env python3
"""Current NiakVIO provider scope.

Provider cardinality is data, never policy.

* ``providers/`` contains executable/active Provider v3 artifacts only.
* ``provider-disabled/`` contains disabled artifacts still visible in manifest.json.
* ``provider-old/`` is terminal archive and is not part of the current catalogue.

The physical current folder is activation authority. ``manifest.json`` must agree
with that authority; it never invents the active count. Historical duplicate files
outside the manifest-referenced current paths do not inflate cardinality.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = (ROOT / "providers").resolve()
assert ACTIVE_DIR.name == "providers"
DISABLED_DIR = (ROOT / "provider-disabled").resolve()
OLD_DIR = (ROOT / "provider-old").resolve()
MANIFEST = ROOT / "manifest.json"


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _manifest_rows() -> list[dict[str, Any]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in data.get("scrapers") or [] if isinstance(row, dict)]
    ids = [cid(row.get("id")) for row in rows]
    if any(not value for value in ids):
        raise RuntimeError("current manifest contains provider row without id")
    if len(ids) != len(set(ids)):
        raise RuntimeError("current manifest contains duplicate provider ids")
    return rows


def _resolved_asset(row: dict[str, Any]) -> Path:
    filename = str(row.get("filename") or "").strip()
    if not filename:
        raise RuntimeError(f"{cid(row.get('id'))}: missing current provider filename")
    path = (ROOT / filename).resolve()
    if not path.is_file():
        raise RuntimeError(f"{cid(row.get('id'))}: current provider asset missing: {filename}")
    return path


def _state_for_path(path: Path) -> str:
    if ACTIVE_DIR in path.parents:
        return "active"
    if DISABLED_DIR in path.parents:
        return "disabled"
    if OLD_DIR in path.parents:
        return "old"
    return "invalid"


def _classified_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    disabled: list[dict[str, Any]] = []
    for row in _manifest_rows():
        provider = cid(row.get("id"))
        path = _resolved_asset(row)
        state = _state_for_path(path)
        enabled = row.get("enabled") is not False
        if state == "active":
            if not enabled:
                raise RuntimeError(f"{provider}: providers/ artifact cannot be enabled=false")
            active.append(row)
            continue
        if state == "disabled":
            if enabled:
                raise RuntimeError(f"{provider}: provider-disabled/ artifact must be enabled=false")
            disabled.append(row)
            continue
        if state == "old":
            raise RuntimeError(f"{provider}: provider-old/ artifact must not remain in current manifest")
        raise RuntimeError(f"{provider}: current provider artifact is outside managed folders: {path.relative_to(ROOT)}")
    return active, disabled


def active_provider_rows() -> list[dict[str, Any]]:
    active, _ = _classified_rows()
    return active


def disabled_provider_rows() -> list[dict[str, Any]]:
    _, disabled = _classified_rows()
    return disabled


def visible_provider_rows() -> list[dict[str, Any]]:
    active, disabled = _classified_rows()
    return active + disabled


def active_provider_ids() -> set[str]:
    return {cid(row.get("id")) for row in active_provider_rows()}


def disabled_provider_ids() -> set[str]:
    return {cid(row.get("id")) for row in disabled_provider_rows()}


def visible_provider_ids() -> set[str]:
    ids = active_provider_ids() | disabled_provider_ids()
    if len(ids) != len(visible_provider_rows()):
        raise RuntimeError("visible provider identity collision")
    return ids


def active_provider_count() -> int:
    return len(active_provider_ids())


def disabled_provider_count() -> int:
    return len(disabled_provider_ids())


def visible_provider_count() -> int:
    return len(visible_provider_ids())


def assert_directory_contract() -> None:
    """Prove folder/manifest identity without using a magic provider count."""
    active, disabled = _classified_rows()
    active_paths = {_resolved_asset(row) for row in active}
    disabled_paths = {_resolved_asset(row) for row in disabled}
    if active_paths & disabled_paths:
        raise RuntimeError("active/disabled provider asset collision")
    active_ids = {cid(row.get("id")) for row in active}
    disabled_ids = {cid(row.get("id")) for row in disabled}
    if active_ids & disabled_ids:
        raise RuntimeError("active/disabled provider identity collision")


def audit_projection_scope(root: Path = ROOT) -> dict[str, int]:
    """Read-only filesystem integrity/accounting for the union of both manifests.

    This is deliberately independent of the legacy Global execution scope.
    A shared ID is counted once only if both projections agree on the asset
    and enabled state. The audit never adds, enables, or executes providers.
    """
    root = root.resolve()
    def read_projection(relative: str, prefix: str) -> dict[str, tuple[str, bool]]:
        raw = json.loads((root / relative).read_text(encoding="utf-8"))
        rows = raw.get("scrapers")
        if not isinstance(rows, list):
            raise RuntimeError(f"{relative}: missing scraper list")
        found: dict[str, tuple[str, bool]] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"{relative}: invalid row")
            provider = cid(row.get("id"))
            if not provider or provider in found:
                raise RuntimeError(f"{relative}: empty or duplicate provider id: {provider}")
            filename = row.get("filename")
            enabled = row.get("enabled")
            if not isinstance(filename, str) or not isinstance(enabled, bool):
                raise RuntimeError(f"{relative}: invalid asset or enabled state: {provider}")
            if prefix and not filename.startswith(prefix):
                raise RuntimeError(f"{relative}: incorrect projection path: {provider}")
            asset = filename[len(prefix):]
            parts = asset.split("/")
            folder = "providers" if enabled else "provider-disabled"
            if (len(parts) != 2 or parts[0] != folder or
                    not parts[1].endswith(".js") or "\\" in asset or
                    "/" in parts[1] or parts[1] in {".", ".."}):
                raise RuntimeError(f"{relative}: invalid managed asset path: {provider}")
            managed = root / folder
            path = root / asset
            if (managed.is_symlink() or path.is_symlink() or
                    path.resolve().parent != managed or not path.is_file()):
                raise RuntimeError(f"{relative}: missing or escaped managed asset: {provider}")
            found[provider] = (asset, enabled)
        return found

    general = read_projection("manifest.json", "")
    france = read_projection("vf/manifest.json", "../")
    shared = general.keys() & france.keys()
    for provider in shared:
        if general[provider] != france[provider]:
            raise RuntimeError(f"projection asset or enabled state mismatch: {provider}")
    union = {**general, **france}
    if len({asset for asset, _ in union.values()}) != len(union):
        raise RuntimeError("distinct provider IDs share a managed asset")
    return {
        "global_visible": len(general),
        "global_active": sum(enabled for _, enabled in general.values()),
        "france_visible": len(france),
        "france_active": sum(enabled for _, enabled in france.values()),
        "shared": len(shared),
        "global_only": len(general.keys() - france.keys()),
        "france_only": len(france.keys() - general.keys()),
        "union_visible": len(union),
        "union_active": sum(enabled for _, enabled in union.values()),
    }
