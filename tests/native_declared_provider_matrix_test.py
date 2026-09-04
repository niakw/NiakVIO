#!/usr/bin/env python3
"""Regression coverage for the fail-closed 96-provider / declared-route native Lab gate."""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
TYPES = ("movie", "tv", "anime")


def b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode().rstrip("=")


def fixtures() -> dict[str, str]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    return dict((data.get("native_reader_acceptance") or {}).get("fixture_by_type") or {})


def routes() -> list[tuple[str, str]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = []
    for row in manifest.get("scrapers") or []:
        provider = str(row.get("id") or "")
        declared = {str(v).lower() for v in (row.get("supportedTypes") or [])}
        for media_type in TYPES:
            if media_type in declared:
                out.append((provider, media_type))
    return out


def write_android_logs(root: Path, missing_terminal: tuple[str, str] | None = None) -> list[Path]:
    by_type = {kind: [] for kind in TYPES}
    fixture_by_type = fixtures()
    for provider, media_type in routes():
        fixture = fixture_by_type[media_type]
        encoded = b64(provider)
        by_type[media_type].append(
            f"FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture={fixture} provider64={encoded} request_type={media_type}\n"
        )
        if (provider.casefold(), media_type) != (
            (missing_terminal[0].casefold(), missing_terminal[1]) if missing_terminal else ("", "")
        ):
            by_type[media_type].append(
                f"FIELD_NATIVE_RESULT client=tv fixture={fixture} provider64={encoded} request_type={media_type} count=0\n"
            )
    paths = []
    for media_type, lines in by_type.items():
        path = root / f"tv-{media_type}.log"
        path.write_text("".join(lines), encoding="utf-8")
        paths.append(path)
    return paths


def write_ios_log(root: Path) -> Path:
    fixture_by_type = fixtures()
    lines = []
    for provider, media_type in routes():
        fixture = fixture_by_type[media_type]
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_BEGIN fixture={fixture} provider={provider} type={media_type} enabled=true\n"
        )
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_END fixture={fixture} provider={provider} state=completed duration_ms=1\n"
        )
    path = root / "ios.log"
    path.write_text("".join(lines), encoding="utf-8")
    return path


def run(client: str, logs: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(GATE),
            "--client",
            client,
            "--manifest",
            str(MANIFEST),
            "--corpus",
            str(CORPUS),
            *map(str, logs),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


all_routes = routes()
provider_count = len({provider.casefold() for provider, _ in all_routes})
counts = {kind: sum(1 for _, route_type in all_routes if route_type == kind) for kind in TYPES}
route_count = len(all_routes)
assert provider_count == 96
assert route_count == sum(counts.values())
assert all(counts[kind] > 0 for kind in TYPES), counts
expected_summary = (
    f"providers={provider_count} routes={route_count} "
    f"movie={counts['movie']} tv={counts['tv']} anime={counts['anime']}"
)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    ok = run("tv", write_android_logs(root))
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert expected_summary in ok.stdout
    assert f"completed={route_count}" in ok.stdout

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    missing = all_routes[0]
    bad = run("tv", write_android_logs(root, missing_terminal=missing))
    assert bad.returncode == 1
    assert "missing_end=1" in bad.stdout
    assert "reason=missing_terminal" in bad.stdout

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    ios = run("ios", [write_ios_log(root)])
    assert ios.returncode == 0, ios.stdout + ios.stderr
    assert expected_summary in ios.stdout
    assert f"completed={route_count}" in ios.stdout

print(
    "native declared provider matrix gate passed "
    f"providers={provider_count} routes={route_count} "
    f"movie={counts['movie']} tv={counts['tv']} anime={counts['anime']}"
)
