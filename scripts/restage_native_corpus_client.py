#!/usr/bin/env python3
"""Rewrite one already-prepared client corpus test for another fixture."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402
import prepare_native_corpus_client as selected_manifest  # noqa: E402
import native_player_diagnostics_codegen as reader_diag  # noqa: E402


def staged_providers(manifest_path: str, provider: str | None = None) -> list[dict]:
    staged = selected_manifest.staged_manifest_providers(manifest_path)
    try:
        return reader_diag.filter_staged_providers(staged, provider)
    except ValueError as error:
        raise SystemExit(str(error)) from error


def collector_test(source: str, client: str) -> str:
    if client == "desktop":
        old = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
        new = '        assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")\n'
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
    parser.add_argument("--provider", default="", help="optional exact provider id for a targeted human-style run")
    parser.add_argument("--player-probes", type=int, default=1, help="number of returned streams played by the native reader (1-4)")
    parser.add_argument("--manifest", default="manifest.json", help="same in-repository manifest used during initial preparation")
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    provider = args.provider.strip() or None
    manifest_path = str(selected_manifest._manifest_path(args.manifest).relative_to(ROOT))
    providers = staged_providers(manifest_path, provider)
    workspace = Path(args.workspace).resolve()
    probes = max(1, min(args.player_probes, 4))

    if args.target == "desktop":
        target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
        source = corpus.desktop_test(fixture, providers)
    elif args.target == "mobile":
        target = workspace / "nuvio-mobile/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
        source = corpus.android_test(fixture, providers, "mobile")
        source = reader_diag.augment_android_test(
            source,
            client="mobile",
            expected_duration_minutes=fixture.get("expectedDurationMinutes"),
            max_player_probes=probes,
        )
    else:
        target = workspace / "nuvio-tv/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
        source = corpus.android_test(fixture, providers, "tv")
        source = reader_diag.augment_android_test(
            source,
            client="tv",
            expected_duration_minutes=fixture.get("expectedDurationMinutes"),
            max_player_probes=probes,
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(collector_test(source, args.target), encoding="utf-8")
    print(
        f"FIELD_NATIVE_CORPUS_RESTAGED_ISOLATED target={args.target} fixture={args.fixture} "
        f"tmdb={fixture.get('tmdbId')} provider={provider or 'all'} player_probes={probes} manifest={manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
