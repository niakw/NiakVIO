#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_provider_artifact.cjs"

source = b'''const DOMAINS="https://raw.githubusercontent.com/example/repo/main/domains.json";
async function getStreams(){return []}
if(typeof module!=="undefined")module.exports={getStreams};
'''

with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
    handle.write(source)
    path = Path(handle.name)
try:
    public = subprocess.run(
        ["node", str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert public.returncode != 0, public.stdout
    assert "provider runtime repository dependency forbidden" in public.stderr

    base = subprocess.run(
        ["node", str(VALIDATOR), "--provider-base", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert base.returncode == 0, base.stdout + base.stderr
    assert "repository_runtime_dependencies=maintenance-input-only" in base.stdout
finally:
    path.unlink(missing_ok=True)

print("provider artifact validation modes passed")
