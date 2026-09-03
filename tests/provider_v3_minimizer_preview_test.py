#!/usr/bin/env python3
"""Preview all 96 minimized Provider v3 bundles and parse them with one Node VM."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("provider_v3_minimizer_preview", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

from provider_patch_blocks import validate_managed_fixes  # noqa: E402

node_script = """
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const dir = process.argv[1];
const files = fs.readdirSync(dir).filter(x => x.endsWith('.js')).sort();
if (files.length !== 96) throw new Error('expected 96 preview files, got ' + files.length);
for (const file of files) {
  const source = fs.readFileSync(path.join(dir, file), 'utf8');
  new vm.Script(source, {filename: file});
}
process.stdout.write('NODE_MINIMIZER_PARSE_OK files=' + files.length);
"""

with tempfile.TemporaryDirectory() as tmp:
    preview_dir = Path(tmp) / "preview"
    report = module.write_preview(preview_dir, syntax_check=False)
    assert report["provider_count"] == 96

    for path in sorted(preview_dir.glob("*.js")):
        text = path.read_text(encoding="utf-8")
        ids = validate_managed_fixes(text)
        assert ids, path.name
        assert text.count("/* BEGIN NIAKVIO_PROVIDER */") == 1, path.name
        assert text.count("/* END NIAKVIO_PROVIDER */") == 1, path.name
        assert text.count("/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */") == 1, path.name

    proc = subprocess.run(
        ["node", "-e", node_script, str(preview_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "NODE_MINIMIZER_PARSE_OK files=96" in proc.stdout

print(
    "PROVIDER_V3_MINIMIZER_PREVIEW_OK "
    f"providers=96 saved_bytes={report['totals']['saved_bytes']} "
    f"transformed_lines={report['totals']['transformed_lines']}"
)
