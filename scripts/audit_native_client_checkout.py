#!/usr/bin/env python3
"""Fail closed when a native human-UX lab mutates official Nuvio runtime code.

The labs are allowed to add instrumentation/test sources and the minimum Gradle
plumbing needed to execute them. They are not allowed to make the application
more permissive or easier to play than the official checkout.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


FORBIDDEN_DIFF_TOKENS = (
    "android.permission.INTERNET",
    "usesCleartextTraffic",
    "networkSecurityConfig",
    "cleartextTrafficPermitted",
    "setDefaultRequestProperties",
    "setRequestProperty(\"Referer\"",
    "setRequestProperty(\"Origin\"",
    "setRequestProperty(\"User-Agent\"",
    "PlayerPlaybackNetworking",
    "PlatformPlaybackDataSourceFactory",
    "ExoPlayer.Builder",
    "NativePlayerController(",
    "decoderPriority",
    "nvidiaRtxSuperResolutionEnabled",
    "PluginRepository.clearLocalState",
)

ALLOWED_PREFIXES = {
    "mobile": (
        "composeApp/build.gradle.kts",
        "composeApp/src/androidDeviceTest/",
        "local.properties",
    ),
    "tv": (
        "app/build.gradle.kts",
        "app/src/androidTest/",
        "local.properties",
        "local.dev.properties",
    ),
    "desktop": (
        "composeApp/src/desktopTest/",
        "local.properties",
    ),
}

# Added lines permitted in tracked Gradle files. Braces/blank lines are ignored.
MOBILE_GRADLE_ADDITIONS = (
    'withDeviceTest {',
    'instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"',
    'execution = "HOST"',
    'val androidDeviceTest by getting {',
    'dependencies {',
    'implementation("junit:junit:4.13.2")',
    'implementation("androidx.test.ext:junit:1.3.0")',
    'implementation("androidx.test:runner:1.7.0")',
)
TV_GRADLE_ADDITIONS = (
    'signingConfig = signingConfigs.getByName("debug")',
    'testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"',
    'dependencies {',
    'androidTestImplementation("androidx.test.ext:junit:1.3.0")',
    'androidTestImplementation("androidx.test:runner:1.7.0")',
)


def _run(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout


def _status_paths(repo: Path) -> list[str]:
    paths: list[str] = []
    for line in _run(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not line.strip():
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw.strip())
    return paths


def _path_allowed(client: str, path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PREFIXES[client])


def _audit_gradle_diff(client: str, diff: str) -> None:
    allowed = MOBILE_GRADLE_ADDITIONS if client == "mobile" else TV_GRADLE_ADDITIONS
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        value = line[1:].strip()
        if not value or value in {"{", "}"}:
            continue
        if value not in allowed:
            raise SystemExit(f"native lab forbidden Gradle mutation ({client}): {value}")


def audit_checkout(repo: Path, client: str) -> None:
    repo = Path(repo).resolve()
    client = str(client).strip().lower()
    if client not in ALLOWED_PREFIXES:
        raise SystemExit(f"unsupported native client audit target: {client}")
    if not (repo / ".git").exists():
        raise SystemExit(f"native client checkout is not a git repository: {repo}")

    paths = _status_paths(repo)
    forbidden_paths = [path for path in paths if not _path_allowed(client, path)]
    if forbidden_paths:
        raise SystemExit(
            "native human-UX lab mutated runtime-owned path(s): " + ", ".join(forbidden_paths[:20])
        )

    tracked_diff = _run(repo, "diff", "--no-ext-diff", "--unified=0", "--")
    for token in FORBIDDEN_DIFF_TOKENS:
        if token in tracked_diff:
            raise SystemExit(f"native human-UX lab introduced forbidden runtime mutation: {token}")

    if client == "mobile" and "composeApp/build.gradle.kts" in paths:
        _audit_gradle_diff(
            client,
            _run(repo, "diff", "--no-ext-diff", "--unified=0", "--", "composeApp/build.gradle.kts"),
        )
    if client == "tv" and "app/build.gradle.kts" in paths:
        _audit_gradle_diff(
            client,
            _run(repo, "diff", "--no-ext-diff", "--unified=0", "--", "app/build.gradle.kts"),
        )

    print(
        f"FIELD_NATIVE_CHECKOUT_AUDIT client={client} changed_paths={len(paths)} "
        "runtime_mutation=false status=ok"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=tuple(ALLOWED_PREFIXES))
    parser.add_argument("repo")
    args = parser.parse_args()
    audit_checkout(Path(args.repo), args.client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
