#!/usr/bin/env python3
"""Finalize every Nuvio-visible version for one atomic publication.

The finalizer is intentionally idempotent against the currently published manifest:
- a client-visible generation change bumps the global release patch once;
- an existing provider whose client-visible row changes bumps its provider patch once;
- a disabled -> enabled transition still receives the case-only client-id change used
  to escape Nuvio's persisted local activation state;
- package.json, package-lock.json, sources.json, manifest.json and vf/manifest.json
  are synchronized to the same global release version.

A no-op publication does not bump anything.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_semver(value: object) -> tuple[int, int, int] | None:
    match = SEMVER.fullmatch(str(value or "").strip())
    if not match:
        return None
    return tuple(map(int, match.groups()))


def format_semver(value: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in value)


def bump_patch(value: object, *, fallback: tuple[int, int, int] = (1, 0, 0)) -> str:
    parsed = parse_semver(value) or fallback
    return format_semver((parsed[0], parsed[1], parsed[2] + 1))


def canonical_id(value: object) -> str:
    return str(value or "").strip().casefold()


def comparable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(manifest))
    clone.pop("version", None)
    return clone


def comparable_provider(row: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(row))
    clone.pop("version", None)
    return clone


def vf_filename(value: object) -> str:
    filename = str(value or "").strip()
    if not filename or filename.startswith(("http://", "https://", "../")):
        return filename
    if filename.startswith("providers/"):
        return f"../{filename}"
    return filename


def auto_accept_safe_nuvio_client_heads() -> None:
    """Persist contract-safe client HEAD advances without blocking provider publication."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    if os.environ.get("NUVIO_SKIP_CLIENT_UPSTREAM_GUARD") == "1":
        print("Nuvio client safe auto-advance skipped explicitly")
        return
    guard = ROOT / "scripts" / "check_nuvio_client_upstreams.py"
    config = ROOT / "automation" / "nuvio-client-upstreams.json"
    sources = ROOT / "sources.json"
    if not guard.is_file() or not config.is_file() or not sources.is_file():
        return
    output = ROOT / "health-output" / "nuvio-client-upstream-status.json"
    process = subprocess.run(
        [
            sys.executable,
            str(guard),
            "--config",
            str(config),
            "--sources",
            str(sources),
            "--output",
            str(output),
            "--apply-safe-advance",
        ],
        cwd=ROOT,
        check=False,
    )
    if process.returncode != 0:
        print(
            "Nuvio client upstream drift requires separate review; "
            "provider publication continues against pinned audited contract refs "
            f"(guard_exit={process.returncode})",
            file=sys.stderr,
        )


def apply_client_activation_ids() -> dict[str, Any]:
    script = ROOT / "scripts" / "nuvio_client_activation_ids.py"
    state = ROOT / "nuvio-client-id-state.json"
    if not script.exists() or not state.exists():
        return {"changed_ids": [], "activation_transitions": [], "active_count": None}

    import importlib.util

    spec = importlib.util.spec_from_file_location("nuvio_client_activation_ids", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Nuvio client activation id finalizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply_policy(bootstrap_active=False)


def finalize_provider_versions(previous_path: pathlib.Path, manifest_path: pathlib.Path) -> list[str]:
    previous = load(previous_path)
    current = load(manifest_path)
    vf_path = ROOT / "vf" / "manifest.json"
    vf = load(vf_path)

    previous_rows = {
        canonical_id(row.get("id")): row
        for row in previous.get("scrapers", [])
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }
    current_rows = [row for row in current.get("scrapers", []) if isinstance(row, dict)]
    current_by_id: dict[str, dict[str, Any]] = {}
    bumped: list[str] = []

    for row in current_rows:
        cid = canonical_id(row.get("id"))
        if not cid:
            raise RuntimeError(f"provider without id in final manifest: {row!r}")
        if cid in current_by_id:
            raise RuntimeError(f"duplicate provider id in final manifest: {cid}")
        current_by_id[cid] = row

        old = previous_rows.get(cid)
        if old is None:
            if parse_semver(row.get("version")) is None:
                row["version"] = "1.0.0"
            continue

        old_version = parse_semver(old.get("version")) or (1, 0, 0)
        current_version = parse_semver(row.get("version"))
        changed = comparable_provider(old) != comparable_provider(row)

        if changed:
            minimum = (old_version[0], old_version[1], old_version[2] + 1)
            if current_version is None or current_version < minimum:
                row["version"] = format_semver(minimum)
                current_version = minimum
            bumped.append(cid)
        elif current_version is None or current_version < old_version:
            # Never regress a provider cache version even if an upstream row carries
            # an older/stale value while the client-visible payload is unchanged.
            row["version"] = format_semver(old_version)

    # VF and the no-anime manifests are projections of the principal catalogue.
    # Keep cache-visible ids, versions and hashed bundle filenames synchronized
    # without changing projection membership here.
    def sync_projection(path: pathlib.Path, source_by_id: dict[str, dict[str, Any]], label: str) -> None:
        if not path.exists():
            return
        projection = load(path)
        for row in [item for item in projection.get("scrapers", []) if isinstance(item, dict)]:
            cid = canonical_id(row.get("id"))
            source = source_by_id.get(cid)
            if source is None:
                raise RuntimeError(f"{label} provider absent from source manifest: {cid}")
            row["id"] = source.get("id")
            row["version"] = source.get("version")
            row["filename"] = vf_filename(source.get("filename"))
        dump(path, projection)

    sync_projection(vf_path, current_by_id, "VF")
    vf = load(vf_path)
    vf_by_id = {
        canonical_id(row.get("id")): row
        for row in vf.get("scrapers", [])
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }
    sync_projection(ROOT / "no-anime" / "manifest.json", current_by_id, "no-anime")
    sync_projection(ROOT / "vf-no-anime" / "manifest.json", vf_by_id, "VF no-anime")

    dump(manifest_path, current)
    return sorted(set(bumped))


def resolve_release_version(
    *,
    manifest_path: pathlib.Path,
    previous_path: pathlib.Path | None,
    explicit_version: str | None,
) -> tuple[str, bool]:
    current = load(manifest_path)

    if explicit_version is not None:
        parsed = parse_semver(explicit_version)
        if parsed is None:
            raise SystemExit(f"invalid authoritative release version: {explicit_version!r}")
        return format_semver(parsed), False

    current_version = parse_semver(current.get("version"))
    if previous_path is None:
        if current_version is None:
            raise SystemExit(f"invalid authoritative release version: {current.get('version')!r}")
        return format_semver(current_version), False

    previous = load(previous_path)
    previous_version = parse_semver(previous.get("version"))
    if previous_version is None:
        raise SystemExit(f"invalid previous release version: {previous.get('version')!r}")

    changed = comparable_manifest(previous) != comparable_manifest(current)
    if changed:
        minimum = (previous_version[0], previous_version[1], previous_version[2] + 1)
        if current_version is None or current_version < minimum:
            return format_semver(minimum), True
        return format_semver(current_version), current_version > previous_version

    if current_version is None or current_version < previous_version:
        return format_semver(previous_version), False
    return format_semver(current_version), False


def sync_npm_lockfile(version: str) -> None:
    lock_path = ROOT / "package-lock.json"
    if not lock_path.exists():
        return
    lock = load(lock_path)
    lock["version"] = version
    packages = lock.get("packages")
    if isinstance(packages, dict):
        root_package = packages.get("")
        if isinstance(root_package, dict):
            root_package["version"] = version
    dump(lock_path, lock)


def synchronize_global_version(version: str, manifest_path: pathlib.Path) -> None:
    package_path = ROOT / "package.json"
    package = load(package_path)
    package["version"] = version
    dump(package_path, package)
    sync_npm_lockfile(version)

    sources_path = ROOT / "sources.json"
    sources = load(sources_path)
    sources["manifest_version"] = version
    repository = sources.setdefault("repository", {})
    repository["manifest_version"] = version
    if "version" in repository:
        repository["version"] = version
    dump(sources_path, sources)

    catalog_path = ROOT / "provider_catalog.json"
    if catalog_path.exists():
        catalog = load(catalog_path)
        manifest_meta = catalog.setdefault("manifestMeta", {})
        for key in ("general", "vf"):
            row = manifest_meta.setdefault(key, {})
            row["version"] = version
        dump(catalog_path, catalog)

    for path in (
        manifest_path,
        ROOT / "vf" / "manifest.json",
        ROOT / "no-anime" / "manifest.json",
        ROOT / "vf-no-anime" / "manifest.json",
    ):
        if not path.exists():
            continue
        payload = load(path)
        payload["version"] = version
        dump(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Explicit authoritative version")
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Manifest containing the authoritative version",
    )
    parser.add_argument(
        "--previous",
        help="Previously published principal manifest. When supplied, all cache-visible versions are finalized automatically.",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    previous_path = pathlib.Path(args.previous).resolve() if args.previous else None

    activation = apply_client_activation_ids()
    bumped_providers: list[str] = []
    if previous_path is not None:
        bumped_providers = finalize_provider_versions(previous_path, manifest_path)

    version, release_changed = resolve_release_version(
        manifest_path=manifest_path,
        previous_path=previous_path,
        explicit_version=args.version,
    )
    synchronize_global_version(version, manifest_path)

    # Keep official-client HEAD monitoring and safe auto-advance active during
    # publication, but do not conflate unreviewed future upstream HEAD drift with
    # the pinned client contract used to validate the provider generation.
    auto_accept_safe_nuvio_client_heads()

    print(
        json.dumps(
            {
                "release_version": version,
                "release_changed": release_changed,
                "provider_versions_bumped": bumped_providers,
                "provider_version_bump_count": len(bumped_providers),
                "client_id_changes": activation.get("changed_ids", []),
                "activation_transitions": activation.get("activation_transitions", []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
