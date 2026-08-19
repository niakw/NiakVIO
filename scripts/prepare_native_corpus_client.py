#!/usr/bin/env python3
"""Prepare exactly one official Nuvio client for the native corpus lab.

This intentionally wraps the existing corpus generator instead of duplicating its
runtime contract. Provider/runtime failures are observations; the generated test
only fails when the corpus itself cannot be constructed/traversed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402
import native_player_diagnostics_codegen as reader_diag  # noqa: E402


def _collector_test(source: str, client: str) -> str:
    if client == "desktop":
        old = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
        new = '        assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")\n'
    else:
        old = '        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())\n'
        new = '        assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())\n'
    if source.count(old) != 1:
        raise SystemExit(f"unable to relax {client} provider-error assertion: anchor count={source.count(old)}")
    return source.replace(old, new, 1)


def _isolate_tv_android_test_sources(tv: Path) -> int:
    """Remove unrelated upstream instrumented sources from the ephemeral TV lab checkout."""
    removed = 0
    for source_dir in (tv / "app/src/androidTest/java", tv / "app/src/androidTest/kotlin"):
        if not source_dir.is_dir():
            continue
        for source in source_dir.rglob("*"):
            if source.is_file() and source.suffix.lower() in {".kt", ".java"}:
                source.unlink()
                removed += 1
    print(f"FIELD_NATIVE_CORPUS_TV_TEST_SOURCES_ISOLATED removed={removed}")
    return removed


def _selected(providers: list[dict], provider: str | None) -> list[dict]:
    try:
        return reader_diag.filter_staged_providers(providers, provider)
    except ValueError as error:
        raise SystemExit(str(error)) from error


def prepare_desktop(workspace: Path, fixture: dict, provider: str | None) -> None:
    staged = corpus.stage_providers(ROOT / "native-corpus-stage")
    providers = _selected(staged, provider)
    target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.desktop_test(fixture, providers), "desktop"), encoding="utf-8")


def prepare_mobile(workspace: Path, fixture: dict, provider: str | None, player_probes: int) -> None:
    mobile = workspace / "nuvio-mobile"
    corpus.enable_mobile_device_tests(mobile)
    assets = mobile / "composeApp/src/androidDeviceTest/assets/niakvio"
    staged = corpus.stage_providers(assets)
    providers = _selected(staged, provider)
    source = corpus.android_test(fixture, providers, "mobile")
    source = reader_diag.augment_android_test(
        source,
        client="mobile",
        expected_duration_minutes=fixture.get("expectedDurationMinutes"),
        max_player_probes=player_probes,
    )
    target = mobile / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(source, "mobile"), encoding="utf-8")


def prepare_tv(workspace: Path, fixture: dict, provider: str | None, player_probes: int) -> None:
    tv = workspace / "nuvio-tv"
    corpus.enable_tv_tests(tv)
    _isolate_tv_android_test_sources(tv)
    assets = tv / "app/src/androidTest/assets/niakvio"
    staged = corpus.stage_providers(assets)
    providers = _selected(staged, provider)
    source = corpus.android_test(fixture, providers, "tv")
    source = reader_diag.augment_android_test(
        source,
        client="tv",
        expected_duration_minutes=fixture.get("expectedDurationMinutes"),
        max_player_probes=player_probes,
    )
    target = tv / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(source, "tv"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--provider", default="", help="optional exact provider id for a targeted human-style run")
    parser.add_argument("--player-probes", type=int, default=1, help="number of returned streams played by the native reader (1-4)")
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    provider = args.provider.strip() or None
    probes = max(1, min(args.player_probes, 4))
    if args.target == "desktop":
        prepare_desktop(workspace, fixture, provider)
    elif args.target == "mobile":
        prepare_mobile(workspace, fixture, provider, probes)
    else:
        prepare_tv(workspace, fixture, provider, probes)
    print(
        f"FIELD_NATIVE_CORPUS_PREPARED_ISOLATED target={args.target} fixture={args.fixture} "
        f"title={fixture.get('title')} tmdb={fixture.get('tmdbId')} provider={provider or 'all'} player_probes={probes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
