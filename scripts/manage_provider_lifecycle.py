#!/usr/bin/env python3
"""Manage NiakVIO active -> disabled -> archived provider lifecycle.

State contract:

* providers/          : executable providers only
* provider-disabled/  : disabled providers still visible in manifest.json
* provider-old/       : terminal archive, absent from current manifests

A disabled provider is retained for 28 days. If it is still disabled at the end
of that window, its published/provider-base bytes are moved under provider-old/
and it is removed from current manifests. Re-enabling it during the retention
window restores its bytes to providers/ and clears the disabled lifecycle state.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = ROOT / "providers"
DISABLED_DIR = ROOT / "provider-disabled"
ACTIVE_BASE_DIR = ROOT / "provider-bases"
DISABLED_BASE_DIR = DISABLED_DIR / "provider-bases"
ARCHIVE_DIR = ROOT / "provider-old"
ARCHIVE_PROVIDER_DIR = ARCHIVE_DIR / "providers"
ARCHIVE_BASE_DIR = ARCHIVE_DIR / "provider-bases"
STATE_PATH = ROOT / "automation/provider-disabled-lifecycle.json"
RETENTION_DAYS = 28

ROOT_MANIFEST = ROOT / "manifest.json"
PROJECTION_MANIFESTS = (
    ROOT / "vf/manifest.json",
    ROOT / "no-anime/manifest.json",
    ROOT / "vf-no-anime/manifest.json",
)
ACTIVE_ONLY_MANIFESTS = (
    ROOT / "manifest-hub46.json",
    ROOT / "native-hub46/manifest.json",
)


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def relative_filename(manifest_path: Path, target: Path) -> str:
    return target.relative_to(manifest_path.parent).as_posix() if target.is_relative_to(manifest_path.parent) else Path(
        __import__("os").path.relpath(target, manifest_path.parent)
    ).as_posix()


def move_file(source: Path, target: Path, *, apply: bool) -> None:
    if source.resolve() == target.resolve():
        return
    if target.exists():
        if source.exists() and source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"lifecycle collision with different bytes: {source} -> {target}")
        if source.exists() and apply:
            source.unlink()
        return
    if not source.exists():
        return
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


def provider_artifacts(directory: Path, pid: str) -> list[Path]:
    if not directory.exists():
        return []
    prefixes = (pid + "-", pid + "--")
    return sorted(
        path for path in directory.glob("*.js")
        if path.name.casefold().startswith(prefixes)
    )


def provider_bases(directory: Path, pid: str) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(f"{pid}--base--*.js"))


def relocate_family(pid: str, source_dir: Path, target_dir: Path, *, apply: bool) -> list[str]:
    moved: list[str] = []
    for source in provider_artifacts(source_dir, pid):
        target = target_dir / source.name
        move_file(source, target, apply=apply)
        moved.append(target.relative_to(ROOT).as_posix())
    return moved


def relocate_bases(pid: str, source_dir: Path, target_dir: Path, *, apply: bool) -> list[str]:
    moved: list[str] = []
    for source in provider_bases(source_dir, pid):
        target = target_dir / source.name
        move_file(source, target, apply=apply)
        moved.append(target.relative_to(ROOT).as_posix())
    return moved


def rows_by_id(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        cid(row.get("id")): row
        for row in doc.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }


def current_asset(row: dict[str, Any]) -> Path:
    filename = str(row.get("filename") or "").strip()
    if not filename:
        raise RuntimeError(f"{cid(row.get('id'))}: provider filename missing")
    return (ROOT / filename).resolve()


def state_doc() -> dict[str, Any]:
    doc = load_json(
        STATE_PATH,
        {
            "schemaVersion": 1,
            "authority": "provider-disabled-lifecycle-v1",
            "retentionDays": RETENTION_DAYS,
            "disabled": {},
            "archived": {},
        },
    )
    if not isinstance(doc, dict):
        raise RuntimeError("invalid provider disabled lifecycle state")
    doc["schemaVersion"] = 1
    doc["authority"] = "provider-disabled-lifecycle-v1"
    doc["retentionDays"] = RETENTION_DAYS
    doc.setdefault("disabled", {})
    doc.setdefault("archived", {})
    return doc


def update_projection(path: Path, root_rows: dict[str, dict[str, Any]], archived: set[str]) -> None:
    if not path.exists():
        return
    doc = load_json(path)
    rows = [row for row in doc.get("scrapers") or [] if isinstance(row, dict)]
    out: list[dict[str, Any]] = []
    for row in rows:
        pid = cid(row.get("id"))
        if pid in archived:
            continue
        canonical = root_rows.get(pid)
        if canonical is not None:
            row["enabled"] = canonical.get("enabled") is not False
            source = current_asset(canonical)
            row["filename"] = relative_filename(path, source)
            if canonical.get("disabledAt"):
                row["disabledAt"] = canonical["disabledAt"]
                row["purgeAfter"] = canonical.get("purgeAfter")
                row["lifecycleState"] = canonical.get("lifecycleState")
            else:
                row.pop("disabledAt", None)
                row.pop("purgeAfter", None)
                row.pop("lifecycleState", None)
        out.append(row)
    doc["scrapers"] = out
    dump_json(path, doc)


def update_active_only_manifest(path: Path, active_ids: set[str]) -> None:
    if not path.exists():
        return
    doc = load_json(path)
    rows = [row for row in doc.get("scrapers") or [] if isinstance(row, dict)]
    doc["scrapers"] = [row for row in rows if cid(row.get("id")) in active_ids]
    if isinstance(doc.get("labScope"), dict):
        doc["labScope"]["providerCount"] = len(doc["scrapers"])
    dump_json(path, doc)


def update_provider_catalog(root_rows: dict[str, dict[str, Any]], archived: set[str]) -> None:
    path = ROOT / "provider_catalog.json"
    if not path.exists():
        return
    doc = load_json(path)
    providers = []
    for entry in doc.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        scraper = entry.get("scraper") if isinstance(entry.get("scraper"), dict) else {}
        pid = cid(entry.get("canonicalId") or scraper.get("id"))
        if pid in archived:
            continue
        canonical = root_rows.get(pid)
        if canonical is not None:
            scraper["enabled"] = canonical.get("enabled") is not False
            scraper["filename"] = canonical.get("filename")
            entry["scraper"] = scraper
            if canonical.get("disabledAt"):
                entry["lifecycle"] = {
                    "state": "disabled-retained",
                    "disabledAt": canonical["disabledAt"],
                    "purgeAfter": canonical.get("purgeAfter"),
                }
            else:
                entry.pop("lifecycle", None)
        providers.append(entry)
    doc["providers"] = providers
    dump_json(path, doc)


def apply_lifecycle(root: Path = ROOT, *, day: date, apply: bool = False) -> dict[str, Any]:
    if root.resolve() != ROOT.resolve():
        raise RuntimeError("alternate root is not supported by repository lifecycle apply")

    DISABLED_DIR.mkdir(parents=True, exist_ok=True) if apply else None
    state = state_doc()
    manifest = load_json(ROOT_MANIFEST)
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    by_id = {cid(row.get("id")): row for row in rows if cid(row.get("id"))}
    if len(by_id) != len(rows):
        raise RuntimeError("manifest provider ids must be unique and non-empty")

    disabled_state = state["disabled"]
    archived_state = state["archived"]
    archived_now: set[str] = set()
    newly_disabled: set[str] = set()
    reenabled: set[str] = set()

    for pid, row in list(by_id.items()):
        enabled = row.get("enabled") is not False
        record = disabled_state.get(pid) if isinstance(disabled_state.get(pid), dict) else None

        if enabled:
            if record is not None or str(row.get("filename") or "").startswith("provider-disabled/"):
                relocate_family(pid, DISABLED_DIR, ACTIVE_DIR, apply=apply)
                relocate_bases(pid, DISABLED_BASE_DIR, ACTIVE_BASE_DIR, apply=apply)
                asset = current_asset(row)
                if DISABLED_DIR.resolve() in asset.parents:
                    row["filename"] = (ACTIVE_DIR / asset.name).relative_to(ROOT).as_posix()
                row.pop("disabledAt", None)
                row.pop("purgeAfter", None)
                row.pop("lifecycleState", None)
                disabled_state.pop(pid, None)
                reenabled.add(pid)
            continue

        disabled_at = (
            str(row.get("disabledAt") or "").strip()
            or (str(record.get("disabledAt") or "").strip() if record else "")
            or day.isoformat()
        )
        disabled_day = parse_day(disabled_at)
        purge_day = disabled_day + timedelta(days=RETENTION_DAYS)
        reason = str(row.get("disabledReason") or (record or {}).get("reason") or "disabled").strip()

        if day >= purge_day:
            relocate_family(pid, DISABLED_DIR, ARCHIVE_PROVIDER_DIR, apply=apply)
            relocate_family(pid, ACTIVE_DIR, ARCHIVE_PROVIDER_DIR, apply=apply)
            relocate_bases(pid, DISABLED_BASE_DIR, ARCHIVE_BASE_DIR, apply=apply)
            relocate_bases(pid, ACTIVE_BASE_DIR, ARCHIVE_BASE_DIR, apply=apply)
            archived_state[pid] = {
                "disabledAt": disabled_at,
                "purgeAfter": purge_day.isoformat(),
                "archivedAt": day.isoformat(),
                "reason": reason,
                "state": "archived-provider-old",
            }
            disabled_state.pop(pid, None)
            archived_now.add(pid)
            continue

        source = current_asset(row)
        relocate_family(pid, ACTIVE_DIR, DISABLED_DIR, apply=apply)
        relocate_bases(pid, ACTIVE_BASE_DIR, DISABLED_BASE_DIR, apply=apply)
        disabled_asset = DISABLED_DIR / source.name
        if source.parent == ACTIVE_DIR.resolve() or source.parent == DISABLED_DIR.resolve():
            row["filename"] = disabled_asset.relative_to(ROOT).as_posix()
        row["disabledAt"] = disabled_at
        row["purgeAfter"] = purge_day.isoformat()
        row["lifecycleState"] = "disabled-retained"
        disabled_state[pid] = {
            "disabledAt": disabled_at,
            "purgeAfter": purge_day.isoformat(),
            "reason": reason,
            "state": "disabled-retained",
            "manifestVisible": True,
        }
        if record is None:
            newly_disabled.add(pid)

    if archived_now:
        rows = [row for row in rows if cid(row.get("id")) not in archived_now]
        manifest["scrapers"] = rows
        by_id = {cid(row.get("id")): row for row in rows if cid(row.get("id"))}

    active_ids = {pid for pid, row in by_id.items() if row.get("enabled") is not False}
    disabled_ids = {pid for pid, row in by_id.items() if row.get("enabled") is False}

    if apply:
        dump_json(ROOT_MANIFEST, manifest)
        for path in PROJECTION_MANIFESTS:
            update_projection(path, by_id, archived_now)
        for path in ACTIVE_ONLY_MANIFESTS:
            update_active_only_manifest(path, active_ids)
        update_provider_catalog(by_id, archived_now)
        state["updatedAt"] = day.isoformat()
        dump_json(STATE_PATH, state)

    return {
        "day": day.isoformat(),
        "retentionDays": RETENTION_DAYS,
        "active": sorted(active_ids),
        "disabled": sorted(disabled_ids),
        "newlyDisabled": sorted(newly_disabled),
        "reenabled": sorted(reenabled),
        "archivedNow": sorted(archived_now),
        "activeCount": len(active_ids),
        "disabledCount": len(disabled_ids),
        "visibleCount": len(active_ids | disabled_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write lifecycle changes")
    parser.add_argument("--today", help="override UTC date (YYYY-MM-DD) for deterministic validation")
    args = parser.parse_args()
    day = parse_day(args.today) if args.today else today_utc()
    report = apply_lifecycle(day=day, apply=args.apply)
    print(
        "PROVIDER_LIFECYCLE_OK",
        f"active={report['activeCount']}",
        f"disabled={report['disabledCount']}",
        f"visible={report['visibleCount']}",
        f"archived_now={len(report['archivedNow'])}",
        f"retention_days={RETENTION_DAYS}",
        "mode=apply" if args.apply else "mode=dry-run",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
