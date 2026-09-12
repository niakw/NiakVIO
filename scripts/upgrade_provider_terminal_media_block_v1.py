#!/usr/bin/env python3
"""Classify exact-identity resolved media blocks without weakening route proof.

A provider may have a healthy control/identity plane that resolves exact content to
concrete media URLs while the CI runner is forbidden from fetching those media
objects. That is materially different from a broken/stale route: the lane reached
its exact identity resolver, but playback transport is runner-blocked.

This migration adds a narrow, evidence-only classification. It never promotes a
blocked media URL as a live route and it never treats 404/5xx/status-0 as an
environmental block. If a typed resolver is otherwise eligible for positive type
credit but every concrete media object resolved by that exact fixture is blocked,
that type credit is suppressed: successful control-plane resolution is not the same
thing as playable transport proof.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
RECONSTRUCT = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1"

HELPERS = r'''

# PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1
_DIRECT_MEDIA_PATH_RE = re.compile(
    r"\.(?:m3u8|mpd|mp4|mkv|webm|m4v|ts)(?:$|[?#])",
    re.I,
)
_DIRECT_MEDIA_CONTENT_RE = re.compile(
    r"^(?:video/|audio/|application/(?:vnd\.apple\.mpegurl|x-mpegurl|dash\+xml|mp4|octet-stream))",
    re.I,
)


def _direct_media_fetch(fetch: dict[str, Any]) -> bool:
    content_type = str(fetch.get("content_type") or "").strip().split(";", 1)[0]
    if _DIRECT_MEDIA_CONTENT_RE.search(content_type):
        return True
    for raw in _fetch_route_urls(fetch):
        try:
            parsed = urllib.parse.urlsplit(raw)
            path = parsed.path or ""
        except ValueError:
            path = str(raw or "")
        if _DIRECT_MEDIA_PATH_RE.search(path):
            return True
    return False


def _typed_identity_control_fetch(
    fetch: dict[str, Any],
    task: dict[str, Any],
    media_type: str,
) -> bool:
    if not provider_fetch(fetch) or not success(fetch) or _direct_media_fetch(fetch):
        return False
    fixture = task.get("fixture") if isinstance(task.get("fixture"), dict) else {}
    tmdb = str(fixture.get("tmdbId") or "").strip()
    if not tmdb:
        return False

    identity_keys = {"id", "tmdb", "tmdbid", "tmdb_id", "mediaid", "media_id"}
    semantic_keys = {"type", "mediatype", "media_type", "media", "category", "kind"}
    season_keys = {"s", "season", "seasonid", "season_id", "season_number"}
    episode_keys = {"e", "ep", "episode", "episodeid", "episode_id", "episode_number"}
    wanted_season = str(fixture.get("season") or "").strip()
    wanted_episode = str(fixture.get("episode") or "").strip()

    for raw in _fetch_route_urls(fetch):
        try:
            parsed = urllib.parse.urlsplit(raw)
            pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        except ValueError:
            continue
        lowered = [(str(k).casefold(), str(v).strip()) for k, v in pairs]
        has_identity = any(key in identity_keys and value == tmdb for key, value in lowered)
        has_semantic = any(key in semantic_keys and canonical(value) == media_type for key, value in lowered)
        if not (has_identity and has_semantic):
            continue
        if media_type == "tv" and wanted_season and wanted_episode:
            has_season = any(key in season_keys and value == wanted_season for key, value in lowered)
            has_episode = any(key in episode_keys and value == wanted_episode for key, value in lowered)
            if not (has_season and has_episode):
                continue
        return True
    return False


def _resolved_media_block_evidence(
    task_rows: list[dict[str, Any]],
    required_types: set[str],
) -> tuple[set[str], dict[str, list[dict[str, Any]]]]:
    blocked_types: set[str] = set()
    evidence: dict[str, list[dict[str, Any]]] = {media_type: [] for media_type in required_types}
    for media_type in sorted(required_types):
        for task in task_rows:
            if canonical(task.get("semantic_type")) != media_type:
                continue
            fetches = [
                fetch for fetch in task.get("fetches") or []
                if isinstance(fetch, dict) and provider_fetch(fetch)
            ]
            controls = [
                fetch for fetch in fetches
                if _typed_identity_control_fetch(fetch, task, media_type)
            ]
            media_fetches = [fetch for fetch in fetches if _direct_media_fetch(fetch)]
            if not controls or not media_fetches:
                continue
            media_statuses = [int(fetch.get("status") or 0) for fetch in media_fetches]
            # Every resolved media fetch for this exact fixture must be an explicit
            # policy/auth/rate block. A 404, 5xx, timeout/status-0 or successful
            # media response means this narrow terminal classification does not apply.
            if not media_statuses or any(status not in BLOCKED_STATUSES for status in media_statuses):
                continue
            blocked_types.add(media_type)
            evidence[media_type].append({
                "fixture": task.get("fixture_slug"),
                "source": "exact-identity-resolved-media-blocked",
                "identityEvidence": [live_evidence(fetch, task) for fetch in controls[:3]],
                "mediaEvidence": [live_evidence(fetch, task) for fetch in media_fetches[:8]],
                "reusableRoutePromoted": False,
            })
            break
    return blocked_types, evidence
'''


def patch_validator() -> bool:
    text = VALIDATOR.read_text(encoding="utf-8")
    if MARKER in text:
        validate_validator(text)
        return False

    anchor = "\ndef evaluate_provider(\n"
    if text.count(anchor) != 1:
        raise AssertionError(f"validator helper anchor count={text.count(anchor)}")
    text = text.replace(anchor, HELPERS + anchor, 1)

    old_types = '''    type_route_evidence, type_route_templates, validated_types = _validate_declared_type_routes(\n        model, task_rows, required_types\n    )\n    declared_type_ratio = len(validated_types) / len(required_types) if required_types else 1.0\n    type_complete = required_types <= validated_types\n    playable_verified = any(task.get("status") == "playable_verified" for task in task_rows)\n'''
    new_types = '''    type_route_evidence, type_route_templates, validated_types = _validate_declared_type_routes(\n        model, task_rows, required_types\n    )\n    media_blocked_types, media_block_evidence = _resolved_media_block_evidence(task_rows, required_types)\n    playable_verified_types = {\n        canonical(task.get("semantic_type"))\n        for task in task_rows\n        if task.get("status") == "playable_verified"\n    }\n    # A 200 exact-identity resolver that immediately yields only blocked direct\n    # media is control-plane evidence, not positive lane proof. Do not erase a\n    # type that has an independently verified playable fixture.\n    media_blocked_unplayable_types = media_blocked_types - playable_verified_types\n    validated_types = set(validated_types) - media_blocked_unplayable_types\n    declared_type_ratio = len(validated_types) / len(required_types) if required_types else 1.0\n    type_complete = required_types <= validated_types\n    playable_verified = any(task.get("status") == "playable_verified" for task in task_rows)\n'''
    if text.count(old_types) != 1:
        raise AssertionError(f"validator type-credit anchor count={text.count(old_types)}")
    text = text.replace(old_types, new_types, 1)

    old = '''    provider_success_http = any(success(fetch) for fetch, _task in fetch_rows)\n    provider_blocked_only = bool(fetch_rows) and all(int(fetch.get("status") or 0) in BLOCKED_STATUSES for fetch, _task in fetch_rows)\n    direct_output_only = bool(required_types) and type_complete and not fetch_rows and all(\n'''
    new = '''    provider_success_http = any(success(fetch) for fetch, _task in fetch_rows)\n    provider_blocked_only = bool(fetch_rows) and all(int(fetch.get("status") or 0) in BLOCKED_STATUSES for fetch, _task in fetch_rows)\n    # Deliberately conservative: unlike ordinary terminal-unreachable handling,\n    # this classification is only complete when every declared lane independently\n    # resolves exact identity to direct media and every such media request is an\n    # explicit block. Partial lane coverage stays red.\n    provider_media_blocked_complete = bool(required_types) and required_types <= media_blocked_types\n    direct_output_only = bool(required_types) and type_complete and not fetch_rows and all(\n'''
    if text.count(old) != 1:
        raise AssertionError(f"validator evaluation anchor count={text.count(old)}")
    text = text.replace(old, new, 1)

    old_return = '''        "providerSuccessHttp": provider_success_http,\n        "providerBlockedOnly": provider_blocked_only,\n        "unresolvedObservedRequests": unresolved_observed[:40],\n'''
    new_return = '''        "providerSuccessHttp": provider_success_http,\n        "providerBlockedOnly": provider_blocked_only,\n        "providerMediaBlockedTypes": sorted(media_blocked_types),\n        "providerMediaBlockEvidence": media_block_evidence,\n        "providerMediaBlockedComplete": provider_media_blocked_complete,\n        "providerMediaBlockClassification": "exact-identity-resolved-media-blocked" if provider_media_blocked_complete else None,\n        "unresolvedObservedRequests": unresolved_observed[:40],\n'''
    if text.count(old_return) != 1:
        raise AssertionError(f"validator return anchor count={text.count(old_return)}")
    text = text.replace(old_return, new_return, 1)
    VALIDATOR.write_text(text, encoding="utf-8")
    validate_validator(text)
    return True


def patch_reconstruct() -> bool:
    text = RECONSTRUCT.read_text(encoding="utf-8")
    if "providerMediaBlockedComplete" in text and MARKER in text:
        validate_reconstruct(text)
        return False
    old = '''    if evaluation.get("providerBlockedOnly") and evaluation.get("providerRequestCount", 0) > 0:\n        return "terminal-blocked", evidence\n    if origins and evidence and not any(row.get("reachable") for row in evidence):\n'''
    new = '''    if evaluation.get("providerBlockedOnly") and evaluation.get("providerRequestCount", 0) > 0:\n        return "terminal-blocked", evidence\n    # PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1\n    # Exact identity resolution may succeed while every concrete media object is\n    # blocked by the runner. This is terminal transport evidence only: it never\n    # validates or promotes the blocked media URL as a live route.\n    if evaluation.get("providerMediaBlockedComplete"):\n        return "terminal-blocked", evidence\n    if origins and evidence and not any(row.get("reachable") for row in evidence):\n'''
    if text.count(old) != 1:
        raise AssertionError(f"reconstruct terminal anchor count={text.count(old)}")
    text = text.replace(old, new, 1)
    RECONSTRUCT.write_text(text, encoding="utf-8")
    validate_reconstruct(text)
    return True


def validate_validator(text: str | None = None) -> None:
    value = text if text is not None else VALIDATOR.read_text(encoding="utf-8")
    required = (
        MARKER,
        "def _direct_media_fetch(",
        "def _typed_identity_control_fetch(",
        "def _resolved_media_block_evidence(",
        "media_blocked_unplayable_types",
        "required_types <= media_blocked_types",
        '"providerMediaBlockedComplete": provider_media_blocked_complete',
        '"exact-identity-resolved-media-blocked"',
        "any(status not in BLOCKED_STATUSES for status in media_statuses)",
    )
    missing = [item for item in required if item not in value]
    if missing:
        raise AssertionError("terminal media block validator markers missing: " + ",".join(missing))


def validate_reconstruct(text: str | None = None) -> None:
    value = text if text is not None else RECONSTRUCT.read_text(encoding="utf-8")
    if MARKER not in value or 'evaluation.get("providerMediaBlockedComplete")' not in value:
        raise AssertionError("terminal media block reconstruction policy missing")


def patch() -> bool:
    changed = patch_validator()
    changed = patch_reconstruct() or changed
    return changed


def validate() -> None:
    validate_validator()
    validate_reconstruct()


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1_OK "
        f"changed={str(changed).lower()} exact_identity=required direct_media=required "
        "all_declared_lanes=required blocked_statuses_only=required route_proof_promoted=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
