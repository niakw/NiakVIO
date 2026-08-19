#!/usr/bin/env python3
"""Prepare real-reader acceptance corpus runs for official Nuvio Android clients.

The fixture can provide a curated provider scope, while ``--provider all`` deliberately
selects every stageable provider from the chosen manifest, including entries whose
published ``enabled`` flag is false. Primary acceptance can play every returned
stream; broad regression can sample a bounded number of streams. No provider-specific
repair logic lives here.

Pull-request validation is intentionally bounded: a small provider sample from each
fixture and one returned stream are enough to prove the real reader path while the
trusted-main/manual runs keep the exhaustive all-provider/all-stream evidence path.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import native_player_diagnostics_codegen as reader_diag  # noqa: E402
import prepare_native_corpus_client as client_prepare  # noqa: E402
import prepare_native_corpus_validation as corpus  # noqa: E402

CORPUS_PATH = ROOT / ".github/triggers/nuvio-client-lab.json"
DEFAULT_PR_PROVIDER_LIMIT = 4


def _is_pull_request() -> bool:
    return os.environ.get("GITHUB_EVENT_NAME", "").strip().lower() == "pull_request"


def _pr_provider_limit() -> int:
    raw = os.environ.get("NIAKVIO_PR_PROVIDER_LIMIT", str(DEFAULT_PR_PROVIDER_LIMIT)).strip()
    try:
        return max(1, min(int(raw), 12))
    except ValueError:
        return DEFAULT_PR_PROVIDER_LIMIT


def fixture_row(slug: str) -> dict:
    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    for row in data.get("fixtures", []):
        if isinstance(row, dict) and str(row.get("slug") or "") == slug:
            fixture = row.get("fixture")
            providers = row.get("providers")
            if not isinstance(fixture, dict) or not isinstance(providers, list):
                break
            return {"slug": slug, "fixture": {"slug": slug, **fixture}, "providers": providers}
    raise SystemExit(f"unknown or malformed native reader fixture: {slug}")


def select_providers(manifest_path: str, slug: str, provider: str | None) -> list[dict]:
    available = client_prepare.manifest_providers(manifest_path)
    by_id = {str(row.get("id") or "").casefold(): row for row in available}
    requested: list[str]
    mode = str(provider or "fixture").strip().casefold()
    if mode == "all":
        # Lab scope intentionally ignores the publication enabled flag. Disabled
        # providers are valuable repair candidates and must receive the same real
        # reader/device evidence as currently active providers.
        requested = [str(row.get("id") or "") for row in available if str(row.get("id") or "").strip()]
    elif mode == "fixture":
        requested = [str(value) for value in fixture_row(slug)["providers"] if str(value).strip()]
    else:
        requested = [str(provider)]
    selected: list[dict] = []
    missing: list[str] = []
    seen: set[str] = set()
    for raw in requested:
        key = raw.casefold()
        if key in seen:
            continue
        seen.add(key)
        row = by_id.get(key)
        if row is None:
            missing.append(raw)
        else:
            selected.append(row)
    if missing:
        raise SystemExit(
            f"native reader fixture {slug} references provider(s) absent from {manifest_path}: "
            + ", ".join(missing)
        )
    if not selected:
        raise SystemExit(f"native reader fixture {slug} selected no providers from {manifest_path}")
    return selected


def stage_selected(destination: Path, providers: list[dict]) -> list[dict]:
    destination.mkdir(parents=True, exist_ok=True)
    for stale in destination.glob("p[0-9][0-9][0-9].js"):
        stale.unlink()
    staged: list[dict] = []
    for index, provider in enumerate(providers):
        asset = f"p{index:03d}.js"
        shutil.copy2(provider["source"], destination / asset)
        staged.append({**provider, "asset": asset})
    return staged


def parse_stream_scope(value: str | int) -> str | int:
    raw = str(value).strip().casefold()
    if raw == "all":
        return "all"
    try:
        count = int(raw)
    except ValueError as error:
        raise SystemExit(f"invalid stream scope {value!r}; expected all or 1-4") from error
    if count < 1 or count > 4:
        raise SystemExit(f"invalid stream scope {value!r}; expected all or 1-4")
    return count


def reader_source(source: str, client: str, expected_duration_minutes: int | float | None, stream_scope: str | int) -> str:
    scope = parse_stream_scope(stream_scope)
    probes = 4 if scope == "all" else int(scope)
    output = reader_diag.augment_android_test(
        source,
        client=client,
        expected_duration_minutes=expected_duration_minutes,
        max_player_probes=probes,
    )
    if scope != "all":
        return output

    # The normal generator intentionally caps device cost. Primary acceptance
    # removes that cap for both sanitized row evidence and actual Media3 playback.
    output, replacements = re.subn(r"rows\.take\(\d+\)\.forEachIndexed", "rows.forEachIndexed", output)
    if replacements < 2:
        raise SystemExit(f"exhaustive reader rewrite incomplete: replacements={replacements}")
    if re.search(r"rows\.take\(\d+\)\.forEachIndexed", output):
        raise SystemExit("exhaustive reader source still contains sampled stream iteration")
    return output


def prepare(
    target: str,
    workspace: Path,
    slug: str,
    manifest_path: str,
    provider: str | None,
    initial: bool,
    stream_scope: str | int,
) -> Path:
    row = fixture_row(slug)
    fixture = row["fixture"]
    requested_provider = str(provider or "fixture").strip() or "fixture"
    requested_stream_scope = stream_scope
    effective_provider = requested_provider
    effective_stream_scope = stream_scope
    pr_bounded = _is_pull_request()

    # PRs prove the end-to-end native path without re-running the exhaustive corpus
    # on every commit. Trusted main/manual execution still honors all/all exactly.
    if pr_bounded:
        if effective_provider.casefold() == "all":
            effective_provider = "fixture"
        if str(effective_stream_scope).strip().casefold() == "all":
            effective_stream_scope = 1

    selected = select_providers(manifest_path, slug, effective_provider)
    if pr_bounded and effective_provider.casefold() == "fixture":
        selected = selected[: _pr_provider_limit()]
    scope = parse_stream_scope(effective_stream_scope)

    if target == "tv":
        repo = workspace / "nuvio-tv"
        if initial:
            corpus.enable_tv_tests(repo)
            client_prepare._isolate_tv_android_test_sources(repo)
        assets = repo / "app/src/androidTest/assets/niakvio"
        staged = stage_selected(assets, selected)
        source = corpus.android_test(fixture, staged, "tv")
        source = reader_source(source, "tv", fixture.get("expectedDurationMinutes"), scope)
        source = client_prepare._collector_test(source, "tv")
        output = repo / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    else:
        repo = workspace / "nuvio-mobile"
        if initial:
            corpus.enable_mobile_device_tests(repo)
        assets = repo / "composeApp/src/androidDeviceTest/assets/niakvio"
        staged = stage_selected(assets, selected)
        source = corpus.android_test(fixture, staged, "mobile")
        source = reader_source(source, "mobile", fixture.get("expectedDurationMinutes"), scope)
        source = client_prepare._collector_test(source, "mobile")
        output = repo / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source, encoding="utf-8")
    ids = ",".join(str(row.get("id") or "") for row in staged)
    enabled = sum(1 for provider_row in staged if provider_row.get("enabled"))
    disabled = len(staged) - enabled
    print(
        f"FIELD_NATIVE_READER_ACCEPTANCE_PREPARED client={target} fixture={slug} "
        f"manifest={manifest_path} providers={len(staged)} enabled={enabled} disabled={disabled} "
        f"provider_ids={ids} streams={scope} initial={str(initial).lower()} "
        f"ci_mode={'pr-bounded' if pr_bounded else 'deep'} requested_provider={requested_provider} "
        f"requested_streams={requested_stream_scope} provider_limit={_pr_provider_limit() if pr_bounded else 0}"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("tv", "mobile"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--provider", default="fixture", help="all selects every manifest provider, including disabled; fixture uses fixture scope; otherwise exact provider id")
    parser.add_argument("--streams", default="all", help="all, or a bounded reader sample 1-4")
    parser.add_argument("--initial", action="store_true", help="enable official client device tests before first fixture")
    args = parser.parse_args()

    manifest = str(client_prepare._manifest_path(args.manifest).relative_to(ROOT))
    prepare(
        args.target,
        Path(args.workspace).resolve(),
        args.fixture,
        manifest,
        args.provider.strip() or "fixture",
        args.initial,
        args.streams,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
