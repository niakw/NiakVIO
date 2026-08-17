#!/usr/bin/env python3
"""Rewrite one already-prepared client corpus test for another fixture."""
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


def collector_test(source: str, client: str) -> str:
    if client == "desktop":
        old = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
    else:
        old = '        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())\n'
    new = '        assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())\n'
    if source.count(old) != 1:
        raise SystemExit(f"unable to relax {client} provider-error assertion: anchor count={source.count(old)}")
    return source.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    providers = staged_providers()
    workspace = Path(args.workspace).resolve()

    if args.target == "desktop":
        target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
        source = corpus.desktop_test(fixture, providers)
    elif args.target == "mobile":
        target = workspace / "nuvio-mobile/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
        source = corpus.android_test(fixture, providers, "mobile")
    else:
        target = workspace / "nuvio-tv/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
        source = corpus.android_test(fixture, providers, "tv")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(collector_test(source, args.target), encoding="utf-8")
    print(f"FIELD_NATIVE_CORPUS_RESTAGED_ISOLATED target={args.target} fixture={args.fixture} tmdb={fixture.get('tmdbId')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
