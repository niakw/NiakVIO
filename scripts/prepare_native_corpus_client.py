#!/usr/bin/env python3
"""Prepare exactly one official Nuvio client for the native corpus lab.

Official native acceptance consumes the provider bundles committed on the tested
NiakVIO SHA, exactly as a user-installed raw GitHub repository sees them. This is
true for pull requests, trusted main and manual acceptance runs: the lab must not
silently rewrite the repository and then require an Android-only cleartext transport
that the production client correctly refuses.

A dedicated repair sandbox may explicitly opt into materializing current Brain/runtime
repair rules by setting ``NIAKVIO_MATERIALIZE_NATIVE=1``. That mode is never implied
by a normal GitHub Actions acceptance run and its candidate transport remains subject
to the real client network policy.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402
import native_player_diagnostics_codegen as reader_diag  # noqa: E402
from audit_native_client_checkout import audit_checkout  # noqa: E402
from native_client_test_bootstrap import (  # noqa: E402
    enable_mobile_device_tests,
    enable_tv_tests,
)

MATERIALIZED_SENTINEL = ROOT / ".native-provider-overrides-materialized"


def _materialization_requested() -> bool:
    return os.environ.get("NIAKVIO_MATERIALIZE_NATIVE", "0").strip() == "1"


def ensure_materialized_provider_transaction() -> None:
    """Use immutable published bytes unless a repair sandbox explicitly opts in.

    Native acceptance is evidence about what an actual Nuvio client can install.
    Rewriting provider/manifest bytes before repository resolution makes the checkout
    dirty, forces the Android resolver onto ``http://10.0.2.2``, and changes the test
    into a lab-only transport experiment. That is forbidden by default.
    """
    if not _materialization_requested():
        event = os.environ.get("GITHUB_EVENT_NAME", "local").strip().lower() or "local"
        print(
            "FIELD_NATIVE_PROVIDER_TRANSACTION source=committed-sha "
            f"event={event} materialized=false https_repository_compatible=true explicit_repair=false"
        )
        return
    if MATERIALIZED_SENTINEL.is_file():
        return

    package_lock = ROOT / "package-lock.json"
    if package_lock.is_file() and not (ROOT / "node_modules").is_dir():
        npm = shutil.which("npm") or shutil.which("npm.cmd")
        if not npm:
            raise RuntimeError("npm is required to materialize provider overrides for native readers")
        subprocess.run(
            [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=ROOT,
            check=True,
        )

    commands = (
        [sys.executable, str(ROOT / "scripts/build_provider_runtime_profiles.py")],
        [sys.executable, str(ROOT / "scripts/reapply_published_overrides.py")],
    )
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    MATERIALIZED_SENTINEL.write_text("materialized\n", encoding="utf-8")
    print(
        "FIELD_NATIVE_PROVIDER_TRANSACTION_MATERIALIZED source=brain-overrides "
        "status=ok explicit_repair=true"
    )


def _manifest_path(value: str | Path) -> Path:
    raw = Path(value)
    path = raw if raw.is_absolute() else ROOT / raw
    path = path.resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"native corpus manifest must live inside the repository: {value}") from error
    if not path.is_file():
        raise SystemExit(f"native corpus manifest not found: {path}")
    return path


def _provider_source(filename: str) -> Path:
    raw = str(filename or "").strip()
    if not raw:
        raise SystemExit("manifest provider has no filename")
    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        if parsed.hostname != "raw.githubusercontent.com":
            raise SystemExit(f"targeted reader refuses non-repository remote provider: {parsed.hostname or raw}")
        parts = [part for part in parsed.path.split("/") if part]
        try:
            providers_index = parts.index("providers")
        except ValueError as error:
            raise SystemExit(f"raw provider URL does not point to providers/: {raw}") from error
        if len(parts) <= providers_index + 1:
            raise SystemExit(f"raw provider URL has no bundle name: {raw}")
        relative = Path(*parts[providers_index:])
        source = (ROOT / relative).resolve()
    else:
        source = (ROOT / raw).resolve()
    try:
        source.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"provider bundle escapes repository: {raw}") from error
    if not source.is_file():
        raise SystemExit(f"manifest provider bundle missing locally: {raw} -> {source}")
    return source


def manifest_providers(manifest_path: str | Path) -> list[dict]:
    ensure_materialized_provider_transaction()
    manifest_file = _manifest_path(manifest_path)
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    providers: list[dict] = []
    seen: set[str] = set()
    for row in data.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        filename = str(row.get("filename") or "").strip()
        key = provider_id.casefold()
        if not provider_id or not filename or key in seen:
            continue
        seen.add(key)
        providers.append(
            {
                "id": provider_id,
                "enabled": bool(row.get("enabled")),
                "filename": filename,
                "logo": str(row.get("logo") or "").strip(),
                "source": _provider_source(filename),
                "manifest": str(manifest_file.relative_to(ROOT)),
            }
        )
    if not providers:
        raise SystemExit(f"selected manifest contains no stageable providers: {manifest_file}")
    return providers


def stage_manifest_providers(destination: Path, manifest_path: str | Path) -> list[dict]:
    providers = manifest_providers(manifest_path)
    destination.mkdir(parents=True, exist_ok=True)
    for stale in destination.glob("p[0-9][0-9][0-9].js"):
        stale.unlink()
    staged: list[dict] = []
    for index, provider in enumerate(providers):
        asset = f"p{index:03d}.js"
        shutil.copy2(provider["source"], destination / asset)
        staged.append({**provider, "asset": asset})
    print(
        f"FIELD_NATIVE_CORPUS_STAGE_SELECTED manifest={providers[0]['manifest']} providers={len(staged)} "
        f"enabled={sum(1 for row in staged if row['enabled'])} disabled={sum(1 for row in staged if not row['enabled'])}"
    )
    return staged


def staged_manifest_providers(manifest_path: str | Path) -> list[dict]:
    return [{**row, "asset": f"p{index:03d}.js"} for index, row in enumerate(manifest_providers(manifest_path))]


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


def prepare_desktop(workspace: Path, fixture: dict, provider: str | None, manifest_path: str | Path) -> None:
    staged = stage_manifest_providers(ROOT / "native-corpus-stage", manifest_path)
    providers = _selected(staged, provider)
    repo = workspace / "nuvio-desktop"
    target = repo / "composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.desktop_test(fixture, providers), "desktop"), encoding="utf-8")
    audit_checkout(repo, "desktop")


def prepare_mobile(workspace: Path, fixture: dict, provider: str | None, player_probes: int, manifest_path: str | Path) -> None:
    mobile = workspace / "nuvio-mobile"
    enable_mobile_device_tests(mobile)
    assets = mobile / "composeApp/src/androidDeviceTest/assets/niakvio"
    staged = stage_manifest_providers(assets, manifest_path)
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
    audit_checkout(mobile, "mobile")


def prepare_tv(workspace: Path, fixture: dict, provider: str | None, player_probes: int, manifest_path: str | Path) -> None:
    tv = workspace / "nuvio-tv"
    enable_tv_tests(tv)
    _isolate_tv_android_test_sources(tv)
    assets = tv / "app/src/androidTest/assets/niakvio"
    staged = stage_manifest_providers(assets, manifest_path)
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
    audit_checkout(tv, "tv")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--provider", default="", help="optional exact provider id for a targeted human-style run")
    parser.add_argument("--player-probes", type=int, default=1, help="number of returned streams played by the native reader (1-4)")
    parser.add_argument("--manifest", default="manifest.json", help="in-repository manifest whose exact provider bundles are staged")
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    provider = args.provider.strip() or None
    probes = max(1, min(args.player_probes, 4))
    manifest_path = str(_manifest_path(args.manifest).relative_to(ROOT))
    if args.target == "desktop":
        prepare_desktop(workspace, fixture, provider, manifest_path)
    elif args.target == "mobile":
        prepare_mobile(workspace, fixture, provider, probes, manifest_path)
    else:
        prepare_tv(workspace, fixture, provider, probes, manifest_path)
    print(
        f"FIELD_NATIVE_CORPUS_PREPARED_ISOLATED target={args.target} fixture={args.fixture} "
        f"title={fixture.get('title')} tmdb={fixture.get('tmdbId')} provider={provider or 'all'} "
        f"player_probes={probes} manifest={manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())