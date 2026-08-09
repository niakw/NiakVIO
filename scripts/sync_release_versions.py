#!/usr/bin/env python3
"""Align every release-version field with the promoted manifest version."""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def auto_accept_safe_nuvio_client_heads() -> None:
    """Persist only client HEAD advances proven not to alter the tracked runtime contract.

    The exact audited contract refs remain pinned in the contract registry. The
    latest contract-safe official client HEAD is recorded separately in
    sources.json so future checks are incremental. Real contract drift still
    stops publication.
    """
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
        raise SystemExit(process.returncode)


def apply_client_activation_ids() -> None:
    script = ROOT / "scripts" / "nuvio_client_activation_ids.py"
    state = ROOT / "nuvio-client-id-state.json"
    if not script.exists() or not state.exists():
        return
    import importlib.util

    spec = importlib.util.spec_from_file_location("nuvio_client_activation_ids", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Nuvio client activation id finalizer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply_policy(bootstrap_active=False)


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Explicit authoritative version")
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Manifest containing the authoritative version",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    manifest = load(manifest_path)
    version = args.version or str(manifest.get("version", ""))
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"invalid authoritative release version: {version!r}")

    package_path = ROOT / "package.json"
    package = load(package_path)
    package["version"] = version
    dump(package_path, package)
    sync_npm_lockfile(version)

    # This is intentionally inside the write-enabled release synchronizer rather
    # than the report-only CI guard. Safe client advances therefore become
    # durable automatically on deep publication, while contract drift aborts.
    auto_accept_safe_nuvio_client_heads()

    sources_path = ROOT / "sources.json"
    sources = load(sources_path)
    sources["manifest_version"] = version
    repository = sources.setdefault("repository", {})
    repository["manifest_version"] = version
    if "version" in repository:
        repository["version"] = version
    dump(sources_path, sources)

    for relative in ("manifest.json", "vf/manifest.json"):
        path = ROOT / relative
        payload = load(path)
        payload["version"] = version
        dump(path, payload)

    apply_client_activation_ids()
    print(f"release versions synchronized to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
