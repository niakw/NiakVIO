#!/usr/bin/env python3
"""Finalize a lightweight domain-only publication.

The resolver and reapply_published_overrides.py run before this script. This
step bumps only provider versions whose content-addressed artifact changed,
bumps the manifest patch version only when the published payload changed, and
synchronizes all release-version fields. It deliberately does not promote new
upstream provider code; that remains the responsibility of the strict deep
workflow.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump(value: str, fallback: str = "1.0.0") -> str:
    match = SEMVER.fullmatch(str(value or "")) or SEMVER.fullmatch(fallback)
    assert match is not None
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers", [])
        if isinstance(row, dict) and row.get("id")
    }


def payload_without_release_version(manifest: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(manifest))
    value.pop("version", None)
    return value


def sync_package_lock_version(release: str) -> None:
    """Keep npm's root lock metadata on the exact published release.

    Domain refreshes can bump the release without running the deep publication
    synchronizer. npm therefore needs both package-lock.json version fields
    updated in the same transaction as package.json; otherwise the next strict
    release-version check sees a split-brain release.
    """
    lock_path = ROOT / "package-lock.json"
    if not lock_path.exists():
        return
    lock = load(lock_path)
    lock["version"] = release
    packages = lock.get("packages")
    if isinstance(packages, dict):
        root_package = packages.get("")
        if isinstance(root_package, dict):
            root_package["version"] = release
    dump(lock_path, lock)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-manifest", required=True, type=Path)
    parser.add_argument("--report", default="health-output/domain-refresh-finalize.json")
    args = parser.parse_args()

    before = load(args.before_manifest)
    current_path = ROOT / "manifest.json"
    current = load(current_path)
    before_entries = by_id(before)
    current_entries = by_id(current)
    changed_providers: list[str] = []

    for provider_id, entry in current_entries.items():
        previous = before_entries.get(provider_id)
        if not previous:
            continue
        if str(entry.get("filename") or "") != str(previous.get("filename") or ""):
            entry["version"] = bump(str(previous.get("version") or entry.get("version") or "1.0.0"))
            changed_providers.append(provider_id)

    changed_payload = payload_without_release_version(before) != payload_without_release_version(current)
    old_release = str(before.get("version") or current.get("version") or "5.19.0")
    release = bump(old_release, "5.19.0") if changed_payload else old_release
    current["version"] = release
    dump(current_path, current)

    vf_path = ROOT / "vf" / "manifest.json"
    if vf_path.exists():
        vf = load(vf_path)
        primary_entries = by_id(current)
        for row in vf.get("scrapers", []):
            if not isinstance(row, dict):
                continue
            provider_id = str(row.get("id") or "").casefold()
            primary = primary_entries.get(provider_id)
            if not primary:
                continue
            row["version"] = primary.get("version", row.get("version"))
            filename = str(primary.get("filename") or "")
            if filename.startswith("providers/"):
                row["filename"] = "../" + filename
        vf["version"] = release
        dump(vf_path, vf)

    package_path = ROOT / "package.json"
    package = load(package_path)
    package["version"] = release
    dump(package_path, package)
    sync_package_lock_version(release)

    sources_path = ROOT / "sources.json"
    sources = load(sources_path)
    sources["manifest_version"] = release
    repository = sources.setdefault("repository", {})
    repository["manifest_version"] = release
    if "version" in repository:
        repository["version"] = release
    dump(sources_path, sources)

    report = {
        "schema_version": 1,
        "changed": changed_payload,
        "old_release": old_release,
        "new_release": release,
        "changed_provider_count": len(changed_providers),
        "changed_providers": sorted(changed_providers),
    }
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dump(report_path, report)
    print(
        f"domain refresh finalized: changed={str(changed_payload).lower()} "
        f"providers={len(changed_providers)} release={release}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
