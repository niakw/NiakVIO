#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"


def run(extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        manifest = {"scrapers": [{"id": "demo", "enabled": True, "supportedTypes": ["movie"]}]}
        corpus = {"native_reader_acceptance": {"fixture_by_type": {"movie": "m", "tv": "t", "anime": "a"}}}
        log = "\n".join([
            "FIELD_NATIVE_PROVIDER_BEGIN client=tv provider=demo request_type=movie",
            "FIELD_NATIVE_RESULT client=tv provider=demo request_type=movie count=0",
        ]) + "\n"
        manifest_path = root / "manifest.json"
        corpus_path = root / "corpus.json"
        log_path = root / "lab.log"
        output = root / "result.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
        log_path.write_text(log, encoding="utf-8")
        command = [
            sys.executable, str(GATE), "--client", "tv",
            "--manifest", str(manifest_path), "--corpus", str(corpus_path),
            "--json-output", str(output), *(extra or []), str(log_path),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        if output.exists():
            result._native_json = json.loads(output.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
        return result


strict = run()
assert strict.returncode != 0, strict.stdout + strict.stderr
assert "health=failed" in strict.stdout
assert "status=RESAMPLE" in strict.stdout
assert "FIELD_NATIVE_ACTIVE_UNCERTIFIED" in strict.stdout
assert strict._native_json["state"] == "failed"  # type: ignore[attr-defined]
assert strict._native_json["providers"][0]["status"] == "RESAMPLE"  # type: ignore[attr-defined]

repair = run(["--allow-nonfull"])
assert repair.returncode == 0, repair.stdout + repair.stderr
assert "allow_nonfull=true" in repair.stdout
assert repair._native_json["healthState"] == "failed"  # type: ignore[attr-defined]
assert repair._native_json["state"] == "passed"  # type: ignore[attr-defined]

print("native active FULL certification gate tests passed")
