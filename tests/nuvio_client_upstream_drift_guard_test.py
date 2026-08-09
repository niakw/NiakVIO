#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_nuvio_client_upstreams.py"

spec = importlib.util.spec_from_file_location("nuvio_client_upstream_guard", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample() -> dict:
    return {
        "repository": "NuvioMedia/NuvioMobile",
        "branch": "cmp-rewrite",
        "verified_ref": "a" * 40,
        "platforms": ["android", "ios"],
        "sensitive_paths": [
            "runtime/",
            "PluginManifest.kt",
        ],
    }


def run_case(head: str, comparison: dict | None) -> dict:
    old_head = module.current_head
    old_compare = module.compare
    try:
        module.current_head = lambda repository, branch: head
        module.compare = lambda repository, base, current: comparison or {}
        return module.inspect_client("client", sample())
    finally:
        module.current_head = old_head
        module.compare = old_compare


def main() -> int:
    assert module.is_sensitive("runtime/PluginRuntime.kt", ["runtime/"])
    assert module.is_sensitive("PluginManifest.kt", ["PluginManifest.kt"])
    assert not module.is_sensitive("README.md", ["runtime/", "PluginManifest.kt"])

    identical = run_case("a" * 40, None)
    assert identical["status"] == "verified"
    assert identical["review_required"] is False

    unrelated = run_case(
        "b" * 40,
        {
            "status": "ahead",
            "ahead_by": 2,
            "behind_by": 0,
            "total_commits": 2,
            "files": [{"filename": "README.md"}, {"filename": "docs/changelog.md"}],
        },
    )
    assert unrelated["status"] == "advanced_unrelated"
    assert unrelated["review_required"] is False

    sensitive = run_case(
        "c" * 40,
        {
            "status": "ahead",
            "ahead_by": 1,
            "behind_by": 0,
            "total_commits": 1,
            "files": [{"filename": "runtime/PluginRuntime.kt"}],
        },
    )
    assert sensitive["status"] == "contract_review_required"
    assert sensitive["review_required"] is True
    assert sensitive["sensitive_changed_files"] == ["runtime/PluginRuntime.kt"]

    diverged = run_case(
        "d" * 40,
        {
            "status": "diverged",
            "ahead_by": 1,
            "behind_by": 1,
            "total_commits": 2,
            "files": [{"filename": "README.md"}],
        },
    )
    assert diverged["status"] == "contract_review_required"
    assert diverged["review_required"] is True

    truncated = run_case(
        "e" * 40,
        {
            "status": "ahead",
            "ahead_by": 300,
            "behind_by": 0,
            "total_commits": 250,
            "files": [{"filename": "README.md"}],
        },
    )
    assert truncated["status"] == "contract_review_required"
    assert truncated["review_required"] is True

    print("Nuvio client upstream drift guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
