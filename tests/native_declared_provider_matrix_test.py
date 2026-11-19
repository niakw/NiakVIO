#!/usr/bin/env python3
"""Regression coverage for fail-closed declared-route native Lab gates.

Each production projection is gated independently. Their active provider union
must equal current_provider_scope.projection_active_provider_ids().
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rotating_corpus import select_fixtures  # noqa: E402
from current_provider_scope import projection_active_provider_ids  # noqa: E402

GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"
MANIFESTS = (ROOT / "manifest.json", ROOT / "vf/manifest.json")
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
TYPES = ("movie", "tv", "anime")


def b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode().rstrip("=")


def fixtures() -> dict[str, str]:
    result: dict[str, str] = {}
    for lane in TYPES:
        selected = select_fixtures(lane, count=1, seed="native-matrix-test", provider="matrix-test")
        assert len(selected) == 1
        result[lane] = selected[0]["slug"]
    return result


def manifest_rows(manifest: Path) -> list[dict]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return [
        row for row in data.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    ]


def active_rows(manifest: Path) -> list[dict]:
    return [row for row in manifest_rows(manifest) if row.get("enabled") is True]


def routes(manifest: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for row in active_rows(manifest):
        provider = str(row.get("id") or "").strip()
        declared = {str(v).lower() for v in (row.get("supportedTypes") or [])}
        for media_type in TYPES:
            if media_type in declared:
                out.append((provider, media_type))
    return out


def write_android_logs(
    root: Path,
    manifest: Path,
    missing_terminal: tuple[str, str] | None = None,
) -> list[Path]:
    by_type = {kind: [] for kind in TYPES}
    fixture_by_type = fixtures()
    missing_key = ((missing_terminal[0].casefold(), missing_terminal[1]) if missing_terminal else ("", ""))
    for provider, media_type in routes(manifest):
        fixture = fixture_by_type[media_type]
        encoded = b64(provider)
        by_type[media_type].append(
            f"FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture={fixture} provider64={encoded} request_type={media_type}\n"
        )
        if (provider.casefold(), media_type) != missing_key:
            by_type[media_type].append(
                f"FIELD_NATIVE_RESULT client=tv fixture={fixture} provider64={encoded} request_type={media_type} count=0\n"
            )
    paths: list[Path] = []
    for media_type, lines in by_type.items():
        path = root / f"{manifest.parent.name or 'root'}-tv-{media_type}.log"
        path.write_text("".join(lines), encoding="utf-8")
        paths.append(path)
    return paths


def write_ios_log(root: Path, manifest: Path) -> Path:
    fixture_by_type = fixtures()
    lines: list[str] = []
    for provider, media_type in routes(manifest):
        fixture = fixture_by_type[media_type]
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_BEGIN fixture={fixture} provider={provider} type={media_type} enabled=true\n"
        )
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_END fixture={fixture} provider={provider} state=completed duration_ms=1\n"
        )
    path = root / f"{manifest.parent.name or 'root'}-ios.log"
    path.write_text("".join(lines), encoding="utf-8")
    return path


def run(client: str, manifest: Path, logs: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GATE),
            "--client", client,
            "--manifest", str(manifest),
            "--corpus", str(CORPUS),
            *map(str, logs),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


union_providers: set[str] = set()
union_routes: set[tuple[str, str]] = set()
for manifest in MANIFESTS:
    current_rows = active_rows(manifest)
    current_routes = routes(manifest)
    providers = {str(row.get("id") or "").strip().casefold().replace("_", "-") for row in current_rows}
    assert providers, manifest
    union_providers |= providers
    union_routes |= {(provider.casefold().replace("_", "-"), media_type) for provider, media_type in current_routes}

    counts = {kind: sum(1 for _, route_type in current_routes if route_type == kind) for kind in TYPES}
    assert any(counts.values()), (manifest, counts)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ok = run("tv", manifest, write_android_logs(root, manifest))
        assert ok.returncode == 0, ok.stdout + ok.stderr
        assert f"providers={len(providers)}" in ok.stdout
        assert f"completed={len(current_routes)}" in ok.stdout

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        missing = current_routes[0]
        bad = run("tv", manifest, write_android_logs(root, manifest, missing_terminal=missing))
        assert bad.returncode == 1, bad.stdout + bad.stderr
        assert "missing_end=1" in bad.stdout
        assert "reason=missing_terminal" in bad.stdout

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ios = run("ios", manifest, [write_ios_log(root, manifest)])
        assert ios.returncode == 0, ios.stdout + ios.stderr
        assert f"providers={len(providers)}" in ios.stdout
        assert f"completed={len(current_routes)}" in ios.stdout

expected = projection_active_provider_ids()
assert union_providers == expected, (
    f"canonical manifest union drift missing={sorted(expected-union_providers)} "
    f"extra={sorted(union_providers-expected)}"
)

print(
    "native declared provider matrix gate passed "
    f"providers={len(union_providers)} routes={len(union_routes)} "
    "manifests=manifest.json+vf/manifest.json adaptive_recent_fixtures=true"
)
