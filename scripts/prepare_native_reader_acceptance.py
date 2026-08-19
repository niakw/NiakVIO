#!/usr/bin/env python3
"""Prepare an exhaustive real-reader acceptance corpus for official Nuvio Android clients.

This is deliberately provider-agnostic. The fixture decides which providers are in
scope; every stream returned by each selected provider is then played by the real
Media3 reader. No provider-specific repair logic lives here.
"""
from __future__ import annotations

import argparse
import json
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
    if provider and provider.casefold() not in {"all", "fixture"}:
        requested = [provider]
    else:
        requested = [str(value) for value in fixture_row(slug)["providers"] if str(value).strip()]
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


def exhaustive_reader_source(source: str, client: str, expected_duration_minutes: int | float | None) -> str:
    # The existing codegen is the single implementation of the official reader
    # path. Acceptance only changes sampling into exhaustive enumeration.
    output = reader_diag.augment_android_test(
        source,
        client=client,
        expected_duration_minutes=expected_duration_minutes,
        max_player_probes=4,
    )
    output, replacements = re.subn(r"rows\.take\(\d+\)\.forEachIndexed", "rows.forEachIndexed", output)
    if replacements < 2:
        raise SystemExit(f"exhaustive reader rewrite incomplete: replacements={replacements}")
    if re.search(r"rows\.take\(\d+\)\.forEachIndexed", output):
        raise SystemExit("exhaustive reader source still contains sampled stream iteration")
    return output


def prepare(target: str, workspace: Path, slug: str, manifest_path: str, provider: str | None, initial: bool) -> Path:
    row = fixture_row(slug)
    fixture = row["fixture"]
    selected = select_providers(manifest_path, slug, provider)

    if target == "tv":
        repo = workspace / "nuvio-tv"
        if initial:
            corpus.enable_tv_tests(repo)
            client_prepare._isolate_tv_android_test_sources(repo)
        assets = repo / "app/src/androidTest/assets/niakvio"
        staged = stage_selected(assets, selected)
        source = corpus.android_test(fixture, staged, "tv")
        source = exhaustive_reader_source(source, "tv", fixture.get("expectedDurationMinutes"))
        source = client_prepare._collector_test(source, "tv")
        output = repo / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    else:
        repo = workspace / "nuvio-mobile"
        if initial:
            corpus.enable_mobile_device_tests(repo)
        assets = repo / "composeApp/src/androidDeviceTest/assets/niakvio"
        staged = stage_selected(assets, selected)
        source = corpus.android_test(fixture, staged, "mobile")
        source = exhaustive_reader_source(source, "mobile", fixture.get("expectedDurationMinutes"))
        source = client_prepare._collector_test(source, "mobile")
        output = repo / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source, encoding="utf-8")
    ids = ",".join(str(row.get("id") or "") for row in staged)
    print(
        f"FIELD_NATIVE_READER_ACCEPTANCE_PREPARED client={target} fixture={slug} "
        f"manifest={manifest_path} providers={len(staged)} provider_ids={ids} streams=all initial={str(initial).lower()}"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("tv", "mobile"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--provider", default="fixture", help="fixture/all uses fixture provider scope; otherwise exact provider id")
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
