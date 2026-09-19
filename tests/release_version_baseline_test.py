#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "scripts" / "release_version_baseline.py").read_text(encoding="utf-8")


def run(*args: str, cwd: pathlib.Path) -> str:
    return subprocess.check_output(list(args), cwd=cwd, text=True).strip()


def write_manifest(root: pathlib.Path, version: str, filename: str) -> None:
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "name": "NiakVIO-test",
                "version": version,
                "scrapers": [
                    {
                        "id": "demo",
                        "version": "1.0.0",
                        "filename": filename,
                        "enabled": True,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    run("git", "init", "-q", cwd=root)
    run("git", "config", "user.name", "test", cwd=root)
    run("git", "config", "user.email", "test@example.invalid", cwd=root)

    write_manifest(root, "5.21.31", "providers/demo-a.js")
    run("git", "add", "manifest.json", cwd=root)
    run("git", "commit", "-qm", "release 5.21.31", cwd=root)
    first_531 = run("git", "rev-parse", "HEAD", cwd=root)

    (root / "README.md").write_text("docs\n", encoding="utf-8")
    run("git", "add", "README.md", cwd=root)
    run("git", "commit", "-qm", "docs", cwd=root)

    write_manifest(root, "5.21.31", "providers/demo-b.js")
    run("git", "add", "manifest.json", cwd=root)
    run("git", "commit", "-qm", "provider drift without bump", cwd=root)

    script = SOURCE.replace(
        "ROOT = pathlib.Path(__file__).resolve().parents[1]",
        f"ROOT = pathlib.Path({str(root)!r})",
    )
    local_script = root / "baseline.py"
    local_script.write_text(script, encoding="utf-8")
    output = root / "baseline.json"
    result = subprocess.run(
        [sys.executable, str(local_script), "--output", str(output)],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert f"commit={first_531}" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["version"] == "5.21.31"
    assert payload["scrapers"][0]["filename"] == "providers/demo-a.js"

    write_manifest(root, "5.21.32", "providers/demo-b.js")
    run("git", "add", "manifest.json", cwd=root)
    run("git", "commit", "-qm", "release 5.21.32", cwd=root)
    first_532 = run("git", "rev-parse", "HEAD", cwd=root)
    output.unlink()
    result = subprocess.run(
        [sys.executable, str(local_script), "--output", str(output)],
        cwd=root,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert f"commit={first_532}" in result.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["version"] == "5.21.32"

print("release version baseline tests passed")
