#!/usr/bin/env python3
"""Regression coverage for the fail-closed scoped declared-route native Lab gate."""
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

GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
SCOPE = ROOT / "automation/evidence/hub-lab-matrix-46.json"
TYPES = ("movie", "tv", "anime")


def b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode().rstrip("=")


def fixtures() -> dict[str, str]:
    # Synthetic matrix evidence uses the same recent global pools as real Labs;
    # old regression slugs remain targeted fixtures only.
    result: dict[str, str] = {}
    for lane in TYPES:
        selected = select_fixtures(lane, count=1, seed="native-matrix-test", provider="matrix-test")
        assert len(selected) == 1
        result[lane] = selected[0]["slug"]
    return result


def scope_ids() -> set[str]:
    data = json.loads(SCOPE.read_text(encoding="utf-8"))
    ids = {
        str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
        for row in data.get("rows") or []
        if isinstance(row, dict) and str(row.get("manifestId") or row.get("provider") or "").strip()
    }
    declared = int(data.get("hubCount") or 0)
    assert declared > 0 and len(ids) == declared, (declared, len(ids))
    return ids


def routes() -> list[tuple[str, str]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scoped = scope_ids()
    out = []
    seen: set[str] = set()
    for row in manifest.get("scrapers") or []:
        provider = str(row.get("id") or "").strip()
        if not provider or provider.casefold() not in scoped:
            continue
        seen.add(provider.casefold())
        declared = {str(v).lower() for v in (row.get("supportedTypes") or [])}
        for media_type in TYPES:
            if media_type in declared:
                out.append((provider, media_type))
    assert seen == scoped
    return out


def write_android_logs(root: Path, missing_terminal: tuple[str, str] | None = None) -> list[Path]:
    by_type = {kind: [] for kind in TYPES}
    fixture_by_type = fixtures()
    missing_key = ((missing_terminal[0].casefold(), missing_terminal[1]) if missing_terminal else ("", ""))
    for provider, media_type in routes():
        fixture = fixture_by_type[media_type]
        encoded = b64(provider)
        by_type[media_type].append(
            f"FIELD_NATIVE_PROVIDER_BEGIN client=tv fixture={fixture} provider64={encoded} request_type={media_type}\n"
        )
        if (provider.casefold(), media_type) != missing_key:
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
        # Deliberately omit FIELD_NATIVE_IOS_RESULT here: provider END must still
        # derive the lane from any adaptive fixture slug and count as a terminal.
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
            "--scope-matrix",
            str(SCOPE),
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
assert provider_count == len(scope_ids())
assert route_count == sum(counts.values())
assert all(counts[kind] > 0 for kind in TYPES), counts
# The active matrix is the complete executable publication scope. Recoverable
# disabled providers remain in the 46-row catalogue but are not native Lab rows.
expected_summary = (
    f"providers={provider_count} disabled=0 routes={route_count} "
    f"movie={counts['movie']} tv={counts['tv']} anime={counts['anime']}"
)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    ok = run("tv", write_android_logs(root))
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert expected_summary in ok.stdout, ok.stdout
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
    assert expected_summary in ios.stdout, ios.stdout
    assert f"completed={route_count}" in ios.stdout

print(
    "native declared provider matrix gate passed "
    f"providers={provider_count} routes={route_count} "
    f"movie={counts['movie']} tv={counts['tv']} anime={counts['anime']} "
    "adaptive_recent_fixtures=true"
)