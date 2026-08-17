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
    """Remove unrelated upstream instrumented sources from the ephemeral TV lab checkout.

    connectedFullDebugAndroidTest compiles the complete androidTest source set before
    applying instrumentation filters. Upstream UI tests can therefore break the
    provider corpus when their own app APIs change, even though NiakVIO never invokes
    those tests. Keep manifests/resources/assets intact and remove only Kotlin/Java
    test sources before writing the standalone NiakVIO corpus test.
    """
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


def prepare_desktop(workspace: Path, fixture: dict) -> None:
    providers = corpus.stage_providers(ROOT / "native-corpus-stage")
    target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.desktop_test(fixture, providers), "desktop"), encoding="utf-8")


def prepare_mobile(workspace: Path, fixture: dict) -> None:
    mobile = workspace / "nuvio-mobile"
    corpus.enable_mobile_device_tests(mobile)
    assets = mobile / "composeApp/src/androidDeviceTest/assets/niakvio"
    providers = corpus.stage_providers(assets)
    target = mobile / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.android_test(fixture, providers, "mobile"), "mobile"), encoding="utf-8")


def prepare_tv(workspace: Path, fixture: dict) -> None:
    tv = workspace / "nuvio-tv"
    corpus.enable_tv_tests(tv)
    _isolate_tv_android_test_sources(tv)
    assets = tv / "app/src/androidTest/assets/niakvio"
    providers = corpus.stage_providers(assets)
    target = tv / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.android_test(fixture, providers, "tv"), "tv"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    {"desktop": prepare_desktop, "mobile": prepare_mobile, "tv": prepare_tv}[args.target](workspace, fixture)
    print(
        f"FIELD_NATIVE_CORPUS_PREPARED_ISOLATED target={args.target} fixture={args.fixture} "
        f"title={fixture.get('title')} tmdb={fixture.get('tmdbId')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())