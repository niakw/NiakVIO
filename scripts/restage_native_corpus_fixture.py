#!/usr/bin/env python3
"""Rewrite native corpus test sources for another fixture without reconfiguring clients."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402


def staged_providers() -> list[dict]:
    providers = corpus.manifest_providers()
    return [{**provider, "asset": f"p{index:03d}.js"} for index, provider in enumerate(providers)]


def restage_desktop(workspace: Path, fixture: dict) -> None:
    providers = staged_providers()
    target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(corpus.desktop_test(fixture, providers), encoding="utf-8")


def restage_android(workspace: Path, fixture: dict) -> None:
    providers = staged_providers()
    mobile_test = workspace / "nuvio-mobile/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    mobile_test.parent.mkdir(parents=True, exist_ok=True)
    mobile_test.write_text(corpus.android_test(fixture, providers, "mobile"), encoding="utf-8")

    tv_test = workspace / "nuvio-tv/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    tv_test.parent.mkdir(parents=True, exist_ok=True)
    tv_test.write_text(corpus.android_test(fixture, providers, "tv"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "android"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    if args.target == "desktop":
        restage_desktop(workspace, fixture)
    else:
        restage_android(workspace, fixture)
    print(
        f"FIELD_NATIVE_CORPUS_RESTAGED target={args.target} fixture={args.fixture} "
        f"tmdb={fixture.get('tmdbId')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
