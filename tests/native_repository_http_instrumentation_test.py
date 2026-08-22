#!/usr/bin/env python3
"""Regression guard: native runtime instrumentation entry points stay non-mutating."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "automation/native-human-ux-policy.json").read_text(encoding="utf-8"))
CLIENT = ROOT / "scripts/instrument_native_client_evidence.py"
REPOSITORY = ROOT / "scripts/instrument_native_repository_http_evidence.py"
DESKTOP = ROOT / "scripts/instrument_native_desktop_evidence.py"

assert "patch Nuvio source code for logging or instrumentation" in POLICY["forbidden_behaviors"]
assert "patch Nuvio repository/network loaders to inject evidence interceptors" in POLICY["forbidden_behaviors"]

for path in (CLIENT, REPOSITORY, DESKTOP):
    text = path.read_text(encoding="utf-8")
    assert "disabled_by_human_ux_policy" in text, path.name
    assert "runtime_mutation=false" in text, path.name
    for forbidden in (
        "write_text(",
        "write_bytes(",
        "replace_once(",
        "addInterceptor",
        "PluginRuntime.kt",
        "FetchBridge.kt",
        "AndroidManifest.xml",
        "android.permission.INTERNET",
        "usesCleartextTraffic",
        "networkSecurityConfig",
    ):
        assert forbidden not in text, f"{path.name}:{forbidden}"


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    marker = path / "production-runtime.txt"
    marker.write_text("official runtime\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "production-runtime.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.email=native-lab@example.invalid",
            "-c",
            "user.name=Native Lab",
            "commit",
            "-qm",
            "baseline",
        ],
        check=True,
    )


def assert_clean(path: Path) -> None:
    status = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=all"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    assert status.strip() == "", status


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    tv = root / "tv"
    mobile = root / "mobile"
    desktop = root / "desktop"
    for repo in (tv, mobile, desktop):
        repo.mkdir()
        init_repo(repo)

    calls = (
        ([sys.executable, str(CLIENT), "tv", str(tv)], tv, "client=tv"),
        ([sys.executable, str(CLIENT), "mobile", str(mobile)], mobile, "client=mobile"),
        ([sys.executable, str(REPOSITORY), "tv", str(tv)], tv, "client=tv"),
        ([sys.executable, str(REPOSITORY), "mobile", str(mobile)], mobile, "client=mobile"),
        ([sys.executable, str(REPOSITORY), "desktop", str(desktop)], desktop, "client=desktop"),
        ([sys.executable, str(DESKTOP), str(desktop)], desktop, "client=desktop"),
    )
    for command, repo, marker in calls:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "disabled_by_human_ux_policy" in completed.stdout
        assert marker in completed.stdout
        assert_clean(repo)

print("native runtime instrumentation shims are policy-locked and non-mutating")
