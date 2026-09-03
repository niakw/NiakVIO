#!/usr/bin/env python3
"""Published Provider v3 bundles must already be minimizer fixed-points."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("provider_v3_minimizer_published", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
files = [ROOT / str(row["filename"]) for row in manifest.get("scrapers") or []]
assert len(files) == 96

non_fixed = []
for path in files:
    text = path.read_text(encoding="utf-8")
    result = module.minimize_text(text)
    module.validate_transform(text, result.text)
    if result.text != text:
        non_fixed.append((path.name, result.saved_bytes))

assert not non_fixed, non_fixed[:20]

node_script = """
const fs = require('fs');
const vm = require('vm');
const files = process.argv.slice(1);
if (files.length !== 96) throw new Error('expected 96 files, got ' + files.length);
for (const file of files) {
  new vm.Script(fs.readFileSync(file, 'utf8'), {filename: file});
}
process.stdout.write('NODE_PUBLISHED_PARSE_OK files=' + files.length);
"""
proc = subprocess.run(
    ["node", "-e", node_script, *[str(path) for path in files]],
    cwd=ROOT,
    text=True,
    capture_output=True,
    timeout=60,
    check=False,
)
assert proc.returncode == 0, proc.stdout + proc.stderr
assert "NODE_PUBLISHED_PARSE_OK files=96" in proc.stdout

total = sum(path.stat().st_size for path in files)
print(f"PROVIDER_V3_MINIMIZER_PUBLISHED_OK providers=96 total_bytes={total}")
