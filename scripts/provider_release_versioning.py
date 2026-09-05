#!/usr/bin/env python3
"""Cache-safe Provider v3 release version synchronization.

A provider payload change is not published safely until Nuvio sees a new
provider version. This script compares the manifest before/after deterministic
materialization, bumps only providers whose published JS filename changed, and
bumps/synchronizes the repository release version once per publication batch.

Learning-only/static candidate evidence does not cause a bump by itself: a
provider must have changed published bytes, unless --force-all is explicitly
used for a one-time backfill.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
EXPECTED_PROVIDER_COUNT = 96


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump_patch(value: object) -> str:
    match = SEMVER_RE.fullmatch(str(value or "").strip())
    if not match:
        raise ValueError(f"strict semver required, got {value!r}")
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def semver_tuple(value: object) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(str(value or "").strip())
    if not match:
        raise ValueError(f"strict semver required, got {value!r}")
    return tuple(map(int, match.groups()))


def canonical(value: object) -> str:
    return str(value or "").strip().casefold()


def rows_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("scrapers")
    if not isinstance(rows, list):
        raise ValueError("manifest.scrapers list required")
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider_id = canonical(row.get("id"))
        if not provider_id:
            continue
        if provider_id in mapped:
            raise ValueError(f"duplicate provider id: {provider_id}")
        mapped[provider_id] = row
    if len(mapped) != EXPECTED_PROVIDER_COUNT:
        raise ValueError(
            f"provider count={len(mapped)} expected={EXPECTED_PROVIDER_COUNT}"
        )
    return mapped


def changed_provider_ids(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    before = rows_by_id(baseline)
    after = rows_by_id(current)
    if set(before) != set(after):
        missing = sorted(set(before) ^ set(after))
        raise ValueError(f"provider set drift during materialization: {missing}")
    return [
        provider_id
        for provider_id in sorted(after)
        if str(before[provider_id].get("filename") or "")
        != str(after[provider_id].get("filename") or "")
    ]


def sync_release_metadata(release: str, root: Path) -> list[str]:
    touched: list[str] = []

    package_path = root / "package.json"
    if package_path.exists():
        package = load(package_path)
        package["version"] = release
        write(package_path, package)
        touched.append(package_path.relative_to(root).as_posix())

    lock_path = root / "package-lock.json"
    if lock_path.exists():
        lock = load(lock_path)
        lock["version"] = release
        packages = lock.get("packages")
        if isinstance(packages, dict) and isinstance(packages.get(""), dict):
            packages[""]["version"] = release
        write(lock_path, lock)
        touched.append(lock_path.relative_to(root).as_posix())

    catalog_path = root / "provider_catalog.json"
    if catalog_path.exists():
        catalog = load(catalog_path)
        meta = catalog.get("manifestMeta")
        if not isinstance(meta, dict):
            raise ValueError("provider_catalog.json manifestMeta object required")
        for key in ("general", "vf"):
            row = meta.get(key)
            if not isinstance(row, dict):
                raise ValueError(f"provider_catalog.json manifestMeta.{key} required")
            row["version"] = release
        write(catalog_path, catalog)
        touched.append(catalog_path.relative_to(root).as_posix())

    sources_path = root / "sources.json"
    if sources_path.exists():
        sources = load(sources_path)
        repository = sources.get("repository")
        if not isinstance(repository, dict):
            raise ValueError("sources.json repository object required")
        repository["manifest_version"] = release
        sources["manifest_version"] = release
        write(sources_path, sources)
        touched.append(sources_path.relative_to(root).as_posix())

    return touched


def apply_bump(
    manifest_path: Path,
    baseline_path: Path,
    *,
    force_all: bool,
    target_release: str | None,
) -> dict[str, Any]:
    manifest = load(manifest_path)
    baseline = load(baseline_path)
    current_rows = rows_by_id(manifest)
    baseline_rows = rows_by_id(baseline)

    selected = sorted(current_rows) if force_all else changed_provider_ids(baseline, manifest)
    if not selected:
        return {
            "changed": False,
            "release": str(manifest.get("version") or ""),
            "providers": [],
            "providerVersions": {},
            "metadata": [],
        }

    old_release = str(manifest.get("version") or "").strip()
    next_release = target_release or bump_patch(old_release)
    if target_release:
        semver_tuple(next_release)
        if semver_tuple(next_release) <= semver_tuple(old_release):
            raise ValueError(
                f"target release {next_release} must be newer than {old_release}"
            )

    versions: dict[str, str] = {}
    for provider_id in selected:
        row = current_rows[provider_id]
        baseline_row = baseline_rows[provider_id]
        # Provider versions are derived from the pre-publication baseline, never
        # from a partially bumped current file, which makes retries deterministic.
        next_provider = bump_patch(baseline_row.get("version"))
        row["version"] = next_provider
        versions[provider_id] = next_provider

    manifest["version"] = next_release
    write(manifest_path, manifest)
    metadata = sync_release_metadata(next_release, manifest_path.resolve().parent)
    return {
        "changed": True,
        "release": next_release,
        "providers": selected,
        "providerVersions": versions,
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--force-all", action="store_true")
    parser.add_argument("--target-release")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    result = apply_bump(
        args.manifest.resolve(),
        args.baseline_manifest.resolve(),
        force_all=args.force_all,
        target_release=args.target_release,
    )
    if args.summary:
        write(args.summary.resolve(), result)

    print(
        "FIELD_PROVIDER_VERSION_SYNC "
        f"changed={str(result['changed']).lower()} "
        f"release={result['release']} providers={len(result['providers'])}"
    )
    for provider_id in result["providers"]:
        print(
            "FIELD_PROVIDER_VERSION_BUMP "
            f"provider={provider_id} version={result['providerVersions'][provider_id]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
