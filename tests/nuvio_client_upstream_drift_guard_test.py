#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_nuvio_client_upstreams.py"
BRAIN_GUARD = ROOT / "scripts" / "guard_nuvio_client_brain_compat.py"
CONFIG = ROOT / "automation" / "nuvio-client-upstreams.json"

spec = importlib.util.spec_from_file_location("nuvio_client_upstream_guard", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

brain_spec = importlib.util.spec_from_file_location("nuvio_client_brain_guard", BRAIN_GUARD)
assert brain_spec is not None and brain_spec.loader is not None
brain_guard = importlib.util.module_from_spec(brain_spec)
brain_spec.loader.exec_module(brain_guard)


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
        module.compare = lambda repository, base, current, patch_rules=None: comparison or {}
        return module.inspect_client("client", sample(), state or {})
    finally:
        module.current_head = old_head
        module.compare = old_compare


def brain_config() -> dict:
    return {
        "clients": {
            "client": {
                "contract_paths": ["runtime/", "ui/screens/stream/"],
                "brain_mutation_contract_paths": ["runtime/"],
                "semantic_review_tokens": ["getStreams", "StreamItem", "MediaItem", "exoplayer"],
                "brain_mutation_semantic_tokens": ["getStreams", "StreamItem"],
            }
        }
    }


def classify(result: dict) -> tuple[list[str], list[str]]:
    report = {
        "clients": {"client": result},
        "review_required": ["client"] if result.get("review_required") else [],
        "inconclusive": ["client"] if result.get("status") == "verification_inconclusive" else [],
    }
    return brain_guard.classify_provider_mutation_compat(report, brain_config())


def main() -> int:
    assert module.path_matches("runtime/PluginRuntime.kt", ["runtime/"])
    assert module.path_matches("PluginManifest.kt", ["PluginManifest.kt"])
    assert not module.path_matches("README.md", ["runtime/", "PluginManifest.kt"])
    assert module.semantic_hits("+val item: StreamItem\n", ["StreamItem"]) == ["StreamItem"]
    assert module.semantic_hits("+selectedSubtitleId = null\n", ["StreamItem"]) == []

    source = SCRIPT.read_text(encoding="utf-8")
    brain_source = BRAIN_GUARD.read_text(encoding="utf-8")
    assert '"--clients"' in source
    assert "ThreadPoolExecutor" in source
    assert "parallel-git-ls-remote-plus-targeted-partial-tree-diff" in source
    assert "patch_files = [name for name in files if path_matches(name, patch_rules)]" in source
    assert '"--no-fail"' in brain_source
    assert "classify_provider_mutation_compat" in brain_source

    # Hard contract paths model provider request/result/extraction. Reader/UI stream
    # surfaces remain semantic-review paths: they still force fresh native reader
    # proof when runtime-sensitive tokens move, without making presentation-only UI
    # changes look like provider-contract breakage.
    upstreams = json.loads(CONFIG.read_text(encoding="utf-8"))["clients"]
    mobile = upstreams["nuvio-mobile"]
    mobile_stream_root = "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/"
    assert mobile_stream_root not in mobile["contract_paths"]
    assert mobile_stream_root in mobile["semantic_review_paths"]
    for hard_path in (
        "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/PlaybackUrlCredentials.kt",
        "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamFetchSupport.kt",
        "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamModels.kt",
        "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamParser.kt",
        "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamsRepository.kt",
    ):
        assert hard_path in mobile["contract_paths"], hard_path
        assert hard_path in mobile["brain_mutation_contract_paths"], hard_path
    assert "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/StreamsScreen.kt" not in mobile["contract_paths"]
    assert "composeApp/src/commonMain/kotlin/com/nuvio/app/features/streams/" in upstreams["nuvio-desktop"]["contract_paths"]
    assert "app/src/main/java/com/nuvio/tv/ui/screens/stream/" in upstreams["nuvio-tv"]["contract_paths"]
    assert "app/src/main/java/com/nuvio/tv/ui/screens/stream/" not in upstreams["nuvio-tv"]["brain_mutation_contract_paths"]
    assert "app/src/full/java/com/nuvio/tv/core/plugin/" in upstreams["nuvio-tv"]["brain_mutation_contract_paths"]
    assert "MediaItem" in upstreams["nuvio-tv"]["semantic_review_tokens"]
    assert "MediaItem" not in upstreams["nuvio-tv"]["brain_mutation_semantic_tokens"]
    assert "StreamItem" in upstreams["nuvio-tv"]["brain_mutation_semantic_tokens"]

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

    # Brain-specific fence: full reader review remains pending for UI/player-only
    # drift, but provider mutation is allowed unless request/result/extraction
    # semantics are implicated.
    blockers, pending = classify(
        {
            "status": "contract_review_required",
            "compare_status": "ahead",
            "review_required": True,
            "contract_changed_files": ["ui/screens/stream/StreamScreenViewModel.kt"],
            "semantic_token_hits": {},
        }
    )
    assert blockers == []
    assert pending == ["client"]

    blockers, pending = classify(
        {
            "status": "contract_review_required",
            "compare_status": "ahead",
            "review_required": True,
            "contract_changed_files": [],
            "semantic_token_hits": {"player/Playback.kt": ["MediaItem", "exoplayer"]},
        }
    )
    assert blockers == []
    assert pending == ["client"]

    blockers, pending = classify(
        {
            "status": "contract_review_required",
            "compare_status": "ahead",
            "review_required": True,
            "contract_changed_files": ["runtime/PluginRuntime.kt"],
            "semantic_token_hits": {},
        }
    )
    assert any("provider_contract_drift" in value for value in blockers)
    assert pending == []

    blockers, pending = classify(
        {
            "status": "contract_review_required",
            "compare_status": "ahead",
            "review_required": True,
            "contract_changed_files": [],
            "semantic_token_hits": {"player/Playback.kt": ["StreamItem"]},
        }
    )
    assert any("provider_contract_drift" in value for value in blockers)
    assert pending == []

    blockers, _pending = classify(
        {
            "status": "contract_review_required",
            "compare_status": "history_divergence",
            "review_required": True,
            "contract_changed_files": [],
            "semantic_token_hits": {},
        }
    )
    assert any("history_history_divergence" in value for value in blockers)

    blockers, _pending = classify(
        {
            "status": "verification_inconclusive",
            "review_required": False,
            "contract_changed_files": [],
            "semantic_token_hits": {},
        }
    )
    assert blockers == ["client:verification_inconclusive"]

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

    assert module.is_infrastructure_transport_error(
        RuntimeError("fatal: unable to access https://github.com/x/y: server certificate verification failed")
    )
    assert module.is_infrastructure_transport_error(
        RuntimeError("fatal: unable to access https://github.com/x/y: Could not resolve host: github.com")
    )
    assert not module.is_infrastructure_transport_error(RuntimeError("history status is history_divergence"))

    old_head = module.current_head
    try:
        module.current_head = lambda repository, branch: (_ for _ in ()).throw(
            RuntimeError("server certificate verification failed")
        )
        inconclusive = module.resilient_inspect_client("client", sample(), sources("b" * 40))
    finally:
        module.current_head = old_head
    assert inconclusive["status"] == "verification_inconclusive", inconclusive
    assert inconclusive["review_required"] is False
    assert inconclusive["auto_advance_safe"] is False
    assert inconclusive["accepted_ref"] == "b" * 40
    assert inconclusive["contract_ref"] == "a" * 40

    old_head = module.current_head
    try:
        module.current_head = lambda repository, branch: (_ for _ in ()).throw(RuntimeError("logic exploded"))
        try:
            module.resilient_inspect_client("client", sample(), {})
        except RuntimeError as error:
            assert "logic exploded" in str(error)
        else:
            raise AssertionError("non-infrastructure verification error was incorrectly suppressed")
    finally:
        module.current_head = old_head

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
    config = {"clients": {"client": sample(), "unselected": sample()}}
    advanced = module.apply_safe_state(payload, config, result, "2026-08-09T00:00:00+00:00")
    assert advanced == ["client"]
    saved = payload["nuvio_client_compatibility"]["clients"]["client"]
    assert saved["contract_ref"] == "a" * 40
    assert saved["accepted_ref"] == "c" * 40
    assert saved["acceptance"] == "automatic-contract-safe-advance"
    assert "unselected" not in payload["nuvio_client_compatibility"]["clients"]

    print("Nuvio client upstream drift guard tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
