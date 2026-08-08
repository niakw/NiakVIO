#!/usr/bin/env python3
"""Generate deterministic release checksum inventories without circular hashes.

Release inventories cover code, manifests, provider artifacts and durable
configuration. Mutable operational telemetry that is intentionally updated by
an independent diagnostics workflow is excluded; otherwise a harmless
availability refresh would invalidate an otherwise immutable published release.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = {"FILE-HASHES.json", "PATCH-SHA256SUMS.txt"}
IGNORED_PARTS = {
    ".git",
    "node_modules",
    "staging",
    "health-output",
    "checked-artifact",
    "__pycache__",
}
IGNORED_FILES = {
    "availability-history.json",
    "availability-report.json",
}
CORE_FILES = [
    "package.json",
    "sources.json",
    "manifest.json",
    "vf/manifest.json",
    "provider-overrides.json",
    "automation/platform-runtime-contracts.json",
    "automation/nuvio-tv-runtime-contract.json",
    "scripts/deep_repair_loop.py",
    "scripts/runtime_repair.py",
    "scripts/reapply_published_overrides.py",
    "scripts/provider_dns_preflight.mjs",
    "scripts/prune_unreferenced_providers.py",
    "scripts/validate_platform_runtime_policy.py",
    "scripts/validate_nuvio_tv_runtime_policy.py",
    "scripts/nuvio_tv_probe_v2.cjs",
    "scripts/promote_global_nuvio_tv_candidates.py",
    "scripts/provider_patches/nuvio_tv_direct_media_v2.py",
]
# These become mandatory release inputs once the cross-platform policy is
# published, but are optional on the one transition release that creates them.
OPTIONAL_CORE_FILES = [
    "automation/platform-runtime-matrix.json",
    "automation/platform-runtime-policy.json",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inventory(*, include_file_hashes: bool) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if relative in IGNORED_FILES:
            continue
        if relative == "PATCH-SHA256SUMS.txt":
            continue
        if relative == "FILE-HASHES.json" and not include_file_hashes:
            continue
        if path.suffix in {".zip", ".sha256"}:
            continue
        files[relative] = digest(path)
    return files


def main() -> int:
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]

    core_paths = list(CORE_FILES) + [relative for relative in OPTIONAL_CORE_FILES if (ROOT / relative).is_file()]
    core = {relative: digest(ROOT / relative) for relative in core_paths}
    (ROOT / "SHA256SUMS.json").write_text(
        json.dumps(
            {
                "schema_version": 3,
                "release": version,
                "algorithm": "sha256",
                "files": core,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    files = inventory(include_file_hashes=False)
    (ROOT / "FILE-HASHES.json").write_text(
        json.dumps(
            {
                "schema_version": 74,
                "release": version,
                "algorithm": "sha256",
                "excluded_generated_files": sorted(GENERATED),
                "excluded_mutable_operational_files": sorted(IGNORED_FILES),
                "files": files,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    patch_inventory = inventory(include_file_hashes=True)
    lines = [f"{sha}  ./{relative}" for relative, sha in patch_inventory.items()]
    (ROOT / "PATCH-SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"release hashes generated: core={len(core)}, files={len(files)}, patch={len(patch_inventory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
