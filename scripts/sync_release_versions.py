#!/usr/bin/env python3
"""Finalize every Nuvio-visible version for one atomic publication.

The finalizer is intentionally idempotent against the currently published manifest:
- a client-visible generation change bumps the global release patch once;
- an existing provider whose client-visible row changes bumps its provider patch once,
  including France-only providers absent from the Global manifest;
- a disabled -> enabled transition still receives the case-only client-id change used
  to escape Nuvio's persisted local activation state;
- package.json, package-lock.json, sources.json and all manifest projections are
  synchronized to the same global release version;
- NiakVIO manifest names expose that same version for clients that hide the
  dedicated version field, without accumulating repeated ``vX.Y.Z`` suffixes;
- merge/recovery work can never lower the release below the highest version that
  already existed on main first-parent history.

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
VERSION_FLOORS = ROOT / "provider-version-floors.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VISIBLE_NIAKVIO_VERSION = re.compile(r"^NiakVIO(?:\s+v\d+\.\d+\.\d+)?(?=\s*(?:—|$))")


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


def sync_provider_catalog_projection_rows(manifest_path: pathlib.Path) -> None:
    """Keep provider_catalog's published scraper mirror aligned with final manifests."""
    catalog_path = ROOT / "provider_catalog.json"
    vf_path = ROOT / "vf" / "manifest.json"
    if not catalog_path.exists() or not vf_path.exists():
        return

    general = load(manifest_path)
    vf = load(vf_path)
    catalog = load(catalog_path)
    general_by_id = {
        canonical_id(row.get("id")): row
        for row in general.get("scrapers") or []
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }
    vf_by_id = {
        canonical_id(row.get("id")): row
        for row in vf.get("scrapers") or []
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }

    for record in catalog.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        projections = record.get("projections")
        if not isinstance(scraper, dict) or not isinstance(projections, dict):
            continue
        cid = canonical_id(record.get("canonicalId") or scraper.get("id"))
        if not cid:
            continue
        source = general_by_id.get(cid) if projections.get("general") is True else vf_by_id.get(cid)
        if not isinstance(source, dict):
            # Pending/non-runtime catalogue rows are intentionally not projected.
            continue

        scraper["id"] = source.get("id")
        scraper["version"] = source.get("version")
        scraper["enabled"] = source.get("enabled")
        semantic = source.get("canonicalSupportedTypes")
        if not isinstance(semantic, list) or not semantic:
            semantic = source.get("supportedTypes") or []
        scraper["supportedTypes"] = list(semantic)
        scraper.pop("canonicalSupportedTypes", None)

        filename = str(source.get("filename") or "").strip().replace("\\", "/")
        while filename.startswith("../"):
            filename = filename[3:]
        if not filename:
            raise RuntimeError(f"{cid}: projected provider filename missing during catalog sync")
        scraper["filename"] = filename
        scraper["disabledPlatforms"] = []

    dump(catalog_path, catalog)


def load_provider_version_floor_payload() -> dict[str, Any]:
    if not VERSION_FLOORS.is_file():
        return {"schema_version": 1, "providers": {}}
    payload = load(VERSION_FLOORS)
    if int(payload.get("schema_version") or 0) != 1:
        raise RuntimeError("invalid provider-version-floors.json schema")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise RuntimeError("provider-version-floors.json providers map required")
    for provider_id, version in providers.items():
        if not canonical_id(provider_id) or parse_semver(version) is None:
            raise RuntimeError(f"invalid retained provider version floor: {provider_id}={version}")
    return payload


def highest_historical_release(manifest_path: pathlib.Path) -> tuple[int, int, int] | None:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        return None
    try:
        relative = manifest_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None
    try:
        commits = subprocess.check_output(
            ["git", "rev-list", "--first-parent", "HEAD", "--", relative],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return None

    highest: tuple[int, int, int] | None = None
    for commit in commits[:2000]:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"{commit}:{relative}"],
                cwd=ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            version = parse_semver(json.loads(raw).get("version"))
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, AttributeError):
            continue
        if version is not None and (highest is None or version > highest):
            highest = version
    return highest


def normalize_visible_manifest_name(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    return VISIBLE_NIAKVIO_VERSION.sub("NiakVIO", text, count=1)


def versioned_manifest_name(value: object, version: str) -> str:
    text = normalize_visible_manifest_name(value)
    if not text.startswith("NiakVIO"):
        return text
    return f"NiakVIO v{version}{text[len('NiakVIO'):]}"


def comparable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(manifest))
    clone.pop("version", None)
    if "name" in clone:
        clone["name"] = normalize_visible_manifest_name(clone.get("name"))
    return clone


def comparable_provider(row: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(row))
    clone.pop("version", None)
    return clone


def vf_filename(value: object) -> str:
    filename = str(value or "").strip()
    if not filename or filename.startswith(("http://", "https://", "../")):
        return filename
    if filename.startswith(("providers/", "provider-disabled/")):
        return f"../{filename}"
    return filename


def auto_accept_safe_nuvio_client_heads() -> None:
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


def finalize_provider_versions(
    previous_path: pathlib.Path,
    manifest_path: pathlib.Path,
    previous_vf_path: pathlib.Path | None = None,
) -> list[str]:
    previous = load(previous_path)
    current = load(manifest_path)
    vf_path = ROOT / "vf" / "manifest.json"
    vf = load(vf_path)
    previous_vf = load(previous_vf_path) if previous_vf_path is not None else {"scrapers": []}

    floor_payload = load_provider_version_floor_payload()
    floors = floor_payload.setdefault("providers", {})
    floor_changed = False

    def retained_floor(cid: str) -> tuple[int, int, int] | None:
        return parse_semver(floors.get(cid))

    def remember_previous_exposure(cid: str, old_version: tuple[int, int, int]) -> tuple[int, int, int]:
        nonlocal floor_changed
        existing = retained_floor(cid)
        remembered = max(old_version, existing) if existing is not None else old_version
        text = format_semver(remembered)
        if str(floors.get(cid) or "") != text:
            floors[cid] = text
            floor_changed = True
        return remembered

    def enforce_retained_floor(cid: str, current_version: tuple[int, int, int] | None) -> tuple[tuple[int, int, int] | None, bool]:
        floor = retained_floor(cid)
        if floor is None:
            return current_version, False
        if current_version is None or current_version <= floor:
            return (floor[0], floor[1], floor[2] + 1), True
        return current_version, False

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
            current_version = parse_semver(row.get("version"))
            current_version, floor_recovered = enforce_retained_floor(cid, current_version)
            if current_version is None:
                current_version = (1, 0, 0)
            row["version"] = format_semver(current_version)
            if floor_recovered:
                bumped.append(cid)
            continue

        old_version = parse_semver(old.get("version")) or (1, 0, 0)
        current_version = parse_semver(row.get("version"))
        changed = comparable_provider(old) != comparable_provider(row)

        if changed:
            remembered = remember_previous_exposure(cid, old_version)
            minimum = (remembered[0], remembered[1], remembered[2] + 1)
            if current_version is None or current_version < minimum:
                current_version = minimum
            row["version"] = format_semver(current_version)
            bumped.append(cid)
        else:
            current_version, floor_recovered = enforce_retained_floor(cid, current_version)
            if current_version is None or current_version < old_version:
                current_version = old_version
            row["version"] = format_semver(current_version)
            if floor_recovered:
                bumped.append(cid)

    # France-only providers are first-class cache-visible rows even though they
    # intentionally do not exist in the Global manifest. Compare them against
    # the VF baseline and bump their own provider version exactly like Global
    # rows. This closes a client-cache hole where VF bytes could change while
    # retaining the previous provider version.
    previous_vf_rows = {
        canonical_id(row.get("id")): row
        for row in previous_vf.get("scrapers", [])
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }
    vf_seen: set[str] = set()
    for row in [item for item in vf.get("scrapers", []) if isinstance(item, dict)]:
        cid = canonical_id(row.get("id"))
        if not cid or cid in vf_seen:
            raise RuntimeError(f"VF invalid or duplicate provider id: {row.get('id')!r}")
        vf_seen.add(cid)
        if cid in current_by_id:
            continue

        old = previous_vf_rows.get(cid)
        if old is None:
            current_version = parse_semver(row.get("version"))
            current_version, floor_recovered = enforce_retained_floor(cid, current_version)
            if current_version is None:
                current_version = (1, 0, 0)
            row["version"] = format_semver(current_version)
            if floor_recovered:
                bumped.append(cid)
            continue

        old_version = parse_semver(old.get("version")) or (1, 0, 0)
        current_version = parse_semver(row.get("version"))
        changed = comparable_provider(old) != comparable_provider(row)
        if changed:
            remembered = remember_previous_exposure(cid, old_version)
            minimum = (remembered[0], remembered[1], remembered[2] + 1)
            if current_version is None or current_version < minimum:
                current_version = minimum
            row["version"] = format_semver(current_version)
            bumped.append(cid)
        else:
            current_version, floor_recovered = enforce_retained_floor(cid, current_version)
            if current_version is None or current_version < old_version:
                current_version = old_version
            row["version"] = format_semver(current_version)
            if floor_recovered:
                bumped.append(cid)

    dump(vf_path, vf)

    def sync_projection(
        path: pathlib.Path,
        source_by_id: dict[str, dict[str, Any]],
        label: str,
        *,
        allow_projection_only: bool = False,
    ) -> None:
        if not path.exists():
            return
        projection = load(path)
        seen: set[str] = set()
        for row in [item for item in projection.get("scrapers", []) if isinstance(item, dict)]:
            cid = canonical_id(row.get("id"))
            if not cid or cid in seen:
                raise RuntimeError(f"{label} invalid or duplicate provider id: {row.get('id')!r}")
            seen.add(cid)
            source = source_by_id.get(cid)
            if source is None:
                if allow_projection_only:
                    # First-class France-only identity. Its row/version/path are
                    # owned by VF/catalogue authority and must not leak into Global.
                    if parse_semver(row.get("version")) is None:
                        row["version"] = "1.0.0"
                    continue
                raise RuntimeError(f"{label} provider absent from source manifest: {cid}")
            row["id"] = source.get("id")
            row["version"] = source.get("version")
            row["filename"] = vf_filename(source.get("filename"))
        dump(path, projection)

    sync_projection(vf_path, current_by_id, "VF", allow_projection_only=True)
    vf = load(vf_path)
    vf_by_id = {
        canonical_id(row.get("id")): row
        for row in vf.get("scrapers", [])
        if isinstance(row, dict) and canonical_id(row.get("id"))
    }
    sync_projection(ROOT / "no-anime" / "manifest.json", current_by_id, "no-anime")
    sync_projection(ROOT / "vf-no-anime" / "manifest.json", vf_by_id, "VF no-anime")

    dump(manifest_path, current)
    if floor_changed:
        floor_payload["source_commit"] = os.environ.get("GITHUB_SHA") or str(floor_payload.get("source_commit") or "")
        floor_payload["source_release"] = str(previous.get("version") or floor_payload.get("source_release") or "")
        dump(VERSION_FLOORS, floor_payload)
    return sorted(set(bumped))


def resolve_release_version(
    *,
    manifest_path: pathlib.Path,
    previous_path: pathlib.Path | None,
    previous_vf_path: pathlib.Path | None,
    explicit_version: str | None,
) -> tuple[str, bool]:
    current = load(manifest_path)
    historical_floor = highest_historical_release(manifest_path)

    if explicit_version is not None:
        parsed = parse_semver(explicit_version)
        if parsed is None:
            raise SystemExit(f"invalid authoritative release version: {explicit_version!r}")
        if historical_floor is not None and parsed < historical_floor:
            raise SystemExit(
                "release downgrade rejected: "
                f"requested={format_semver(parsed)} historical_floor={format_semver(historical_floor)}"
            )
        return format_semver(parsed), False

    current_version = parse_semver(current.get("version"))
    if previous_path is None:
        if current_version is None:
            raise SystemExit(f"invalid authoritative release version: {current.get('version')!r}")
        if historical_floor is not None and current_version < historical_floor:
            return format_semver(historical_floor), False
        return format_semver(current_version), False

    previous = load(previous_path)
    previous_version = parse_semver(previous.get("version"))
    if previous_version is None:
        raise SystemExit(f"invalid previous release version: {previous.get('version')!r}")

    floor = previous_version
    if historical_floor is not None and historical_floor > floor:
        floor = historical_floor

    changed = comparable_manifest(previous) != comparable_manifest(current)
    if previous_vf_path is not None:
        vf_path = ROOT / "vf" / "manifest.json"
        if vf_path.exists():
            previous_vf = load(previous_vf_path)
            current_vf = load(vf_path)
            changed = changed or comparable_manifest(previous_vf) != comparable_manifest(current_vf)
    if changed:
        minimum = (floor[0], floor[1], floor[2] + 1)
        if current_version is None or current_version < minimum:
            return format_semver(minimum), True
        return format_semver(current_version), current_version > floor

    if current_version is None or current_version < floor:
        return format_semver(floor), False
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
            row["name"] = versioned_manifest_name(row.get("name"), version)
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
        payload["name"] = versioned_manifest_name(payload.get("name"), version)
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
    parser.add_argument(
        "--previous-vf",
        help="Previously published VF manifest. France-only provider changes are versioned from this baseline.",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    previous_path = pathlib.Path(args.previous).resolve() if args.previous else None
    previous_vf_path = pathlib.Path(args.previous_vf).resolve() if args.previous_vf else None

    activation = apply_client_activation_ids()
    bumped_providers: list[str] = []
    if previous_path is not None:
        bumped_providers = finalize_provider_versions(
            previous_path,
            manifest_path,
            previous_vf_path=previous_vf_path,
        )

    version, release_changed = resolve_release_version(
        manifest_path=manifest_path,
        previous_path=previous_path,
        previous_vf_path=previous_vf_path,
        explicit_version=args.version,
    )
    synchronize_global_version(version, manifest_path)
    sync_provider_catalog_projection_rows(manifest_path)

    auto_accept_safe_nuvio_client_heads()

    print(
        json.dumps(
            {
                "release_version": version,
                "release_changed": release_changed,
                "historical_release_floor": (
                    format_semver(highest_historical_release(manifest_path))
                    if highest_historical_release(manifest_path) is not None else None
                ),
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
