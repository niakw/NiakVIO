#!/usr/bin/env python3
"""Export the immutable baseline for the current release-version generation.

The baseline is the oldest manifest on first-parent history in the current
contiguous release-version run. That makes release finalization idempotent:
docs/tests-only commits remain a no-op, while provider/manifest drift that
occurred without a version bump is compared to the originally published bytes
for that version.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def manifest_at(commit: str, relative: str) -> dict:
    raw = git("show", f"{commit}:{relative}")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError(f"manifest at {commit} is not an object")
    return payload


def find_baseline(relative: str) -> tuple[str, dict]:
    current_path = ROOT / relative
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current_version = str(current.get("version") or "").strip()
    if not current_version:
        raise RuntimeError("current manifest has no release version")

    commits = git("rev-list", "--first-parent", "HEAD", "--", relative).splitlines()
    if not commits:
        raise RuntimeError(f"no git history for {relative}")

    baseline_commit: str | None = None
    baseline_manifest: dict | None = None
    entered_current_generation = False

    for commit in commits:
        try:
            payload = manifest_at(commit, relative)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        version = str(payload.get("version") or "").strip()
        if version == current_version:
            entered_current_generation = True
            baseline_commit = commit
            baseline_manifest = payload
            continue
        if entered_current_generation:
            break

    if baseline_commit is None or baseline_manifest is None:
        raise RuntimeError(f"unable to resolve baseline for release {current_version}")
    return baseline_commit, baseline_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    commit, payload = find_baseline(args.manifest)
    output = pathlib.Path(args.output)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_RELEASE_BASELINE commit={commit} version={payload.get('version')} manifest={args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
