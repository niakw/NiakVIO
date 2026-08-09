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
        "contract_paths": [
            "runtime/",
            "PluginManifest.kt",
        ],
        "semantic_review_paths": [
            "player/",
            "gradle/libs.versions.toml",
        ],
        "semantic_review_tokens": [
            "getStreams",
            "StreamItem",
            "MediaItem",
            "quickjs",
        ],
    }


def sources(accepted: str | None = None) -> dict:
    if accepted is None:
        return {}
    return {
        "nuvio_client_compatibility": {
            "schema_version": 1,
            "clients": {
                "client": {
                    "contract_ref": "a" * 40,
                    "accepted_ref": accepted,
                }
            },
        }
    }


def run_case(head: str, comparison: dict | None, state: dict | None = None) -> dict:
    old_head = module.current_head
    old_compare = module.compare
    try:
        module.current_head = lambda repository, branch: head
        module.compare = lambda repository, base, current: comparison or {}
        return module.inspect_client("client", sample(), state or {})
    finally:
        module.current_head = old_head
        module.compare = old_compare


def main() -> int:
    assert module.path_matches("runtime/PluginRuntime.kt", ["runtime/"])
    assert module.path_matches("PluginManifest.kt", ["PluginManifest.kt"])
    assert not module.path_matches("README.md", ["runtime/", "PluginManifest.kt"])
    assert module.semantic_hits("+val item: StreamItem\n", ["StreamItem"]) == ["StreamItem"]
    assert module.semantic_hits("+selectedSubtitleId = null\n", ["StreamItem"]) == []

    identical = run_case("a" * 40, None)
    assert identical["status"] == "verified"
    assert identical["review_required"] is False

    unrelated = run_case(
        "b" * 40,
        {
            "status": "ahead",
            "files": [{"filename": "README.md"}, {"filename": "docs/changelog.md"}],
            "patches": {},
        },
    )
    assert unrelated["status"] == "safe_advance_available"
    assert unrelated["auto_advance_safe"] is True
    assert unrelated["review_required"] is False

    subtitle_only = run_case(
        "c" * 40,
        {
            "status": "ahead",
            "files": [{"filename": "player/PlayerTrackSelection.kt"}],
            "patches": {
                "player/PlayerTrackSelection.kt": "+selectedSubtitleId = null\n-addonSubtitleId = old\n"
            },
        },
    )
    assert subtitle_only["status"] == "safe_advance_available"
    assert subtitle_only["observed_sensitive_changed_files"] == ["player/PlayerTrackSelection.kt"]

    semantic_player = run_case(
        "d" * 40,
        {
            "status": "ahead",
            "files": [{"filename": "player/Playback.kt"}],
            "patches": {
                "player/Playback.kt": "+val item = StreamItem(url = source)\n"
            },
        },
    )
    assert semantic_player["status"] == "contract_review_required"
    assert semantic_player["review_required"] is True
    assert semantic_player["semantic_changed_files"] == ["player/Playback.kt"]

    hard = run_case(
        "e" * 40,
        {
            "status": "ahead",
            "files": [{"filename": "runtime/PluginRuntime.kt"}],
            "patches": {"runtime/PluginRuntime.kt": "+getStreams(payload)\n"},
        },
    )
    assert hard["status"] == "contract_review_required"
    assert hard["review_required"] is True
    assert hard["contract_changed_files"] == ["runtime/PluginRuntime.kt"]

    diverged = run_case(
        "f" * 40,
        {
            "status": "history_divergence",
            "files": [{"filename": "README.md"}],
            "patches": {},
        },
    )
    assert diverged["status"] == "contract_review_required"
    assert diverged["review_required"] is True

    # accepted_ref is the incremental comparison point; contract_ref remains pinned.
    state = sources("b" * 40)
    incremental = run_case(
        "c" * 40,
        {
            "status": "ahead",
            "files": [{"filename": "README.md"}],
            "patches": {},
        },
        state,
    )
    assert incremental["accepted_ref"] == "b" * 40
    assert incremental["contract_ref"] == "a" * 40

    payload: dict = {}
    result = {
        "client": {
            "status": "safe_advance_available",
            "current_head": "c" * 40,
            "changed_file_count": 2,
            "observed_sensitive_changed_files": ["player/Subtitle.kt"],
            "unrelated_changed_files": ["README.md"],
        }
    }
    config = {"clients": {"client": sample()}}
    advanced = module.apply_safe_state(payload, config, result, "2026-08-09T00:00:00+00:00")
    assert advanced == ["client"]
    saved = payload["nuvio_client_compatibility"]["clients"]["client"]
    assert saved["contract_ref"] == "a" * 40
    assert saved["accepted_ref"] == "c" * 40
    assert saved["acceptance"] == "automatic-contract-safe-advance"

    print("Nuvio client upstream drift guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
