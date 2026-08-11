#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_release_hashes.py"
spec = importlib.util.spec_from_file_location("release_hashes_under_test", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert "availability-history.json" in module.IGNORED_FILES
assert "availability-report.json" in module.IGNORED_FILES
assert ".github/ci-status/" in module.IGNORED_PREFIXES
assert ".github/triggers/" in module.IGNORED_PREFIXES
assert "automation/platform-runtime-contracts.json" in module.CORE_FILES
assert "automation/nuvio-tv-runtime-contract.json" in module.CORE_FILES
assert "automation/nuvio-client-upstreams.json" in module.CORE_FILES
assert "scripts/check_nuvio_client_upstreams.py" in module.CORE_FILES
assert "scripts/sync_release_versions.py" in module.CORE_FILES
assert "scripts/validate_platform_runtime_policy.py" in module.CORE_FILES
assert "scripts/validate_nuvio_tv_runtime_policy.py" in module.CORE_FILES
assert "scripts/apply_provider_overrides.py" in module.CORE_FILES
assert "scripts/reapply_published_overrides.py" in module.CORE_FILES
assert "scripts/provider_patches/vf_catalogue_recovery.py" in module.CORE_FILES
assert "scripts/provider_patches/stream_output_sanitizer_v5.py" in module.CORE_FILES
assert "scripts/provider_patches/nuvio_tv_target_media_v3.py" in module.CORE_FILES
assert "scripts/provider_patches/nuvio_tv_target_media_v4.py" in module.CORE_FILES
assert "scripts/provider_patches/expose_strict_wrapper_original.py" in module.CORE_FILES
assert "scripts/provider_patches/target_media_host_filter_v4.py" in module.CORE_FILES
assert "automation/platform-runtime-matrix.json" in module.OPTIONAL_CORE_FILES
assert "automation/platform-runtime-policy.json" in module.OPTIONAL_CORE_FILES

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "durable.txt").write_text("release-input\n", encoding="utf-8")
    (root / "availability-history.json").write_text('{"value":1}\n', encoding="utf-8")
    (root / "availability-report.json").write_text('{"value":1}\n', encoding="utf-8")
    (root / ".github/ci-status").mkdir(parents=True)
    (root / ".github/triggers").mkdir(parents=True)
    (root / ".github/workflows").mkdir(parents=True)
    (root / ".github/ci-status/current-runs.json").write_text('{"run":1}\n', encoding="utf-8")
    (root / ".github/triggers/query-current-actions-main").write_text("probe-1\n", encoding="utf-8")
    (root / ".github/workflows/release.yml").write_text("name: durable\n", encoding="utf-8")
    module.ROOT = root

    before = module.inventory(include_file_hashes=False)
    assert "durable.txt" in before
    assert "availability-history.json" not in before
    assert "availability-report.json" not in before
    assert ".github/ci-status/current-runs.json" not in before
    assert ".github/triggers/query-current-actions-main" not in before
    assert ".github/workflows/release.yml" in before

    # Independent operational telemetry may change without changing the release
    # checksum inventory. A durable release input still changes its hash.
    (root / "availability-history.json").write_text('{"value":2}\n', encoding="utf-8")
    (root / "availability-report.json").write_text('{"value":2}\n', encoding="utf-8")
    (root / ".github/ci-status/current-runs.json").write_text('{"run":2}\n', encoding="utf-8")
    (root / ".github/triggers/query-current-actions-main").write_text("probe-2\n", encoding="utf-8")
    assert module.inventory(include_file_hashes=False) == before

    (root / "durable.txt").write_text("changed-release-input\n", encoding="utf-8")
    after = module.inventory(include_file_hashes=False)
    assert after["durable.txt"] != before["durable.txt"]

print("release hash scope tests passed")
