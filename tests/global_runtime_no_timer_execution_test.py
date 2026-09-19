#!/usr/bin/env python3
"""Execute the Core runtime shim with timer globals absent.

Static ownership already verifies that every published bundle contains the Core
runtime block. This test proves the actual semantic contract: a provider that
uses setTimeout/clearTimeout does not disappear with ReferenceError when the
host runtime exposes neither function.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

import global_runtime_compat_v1  # type: ignore  # noqa: E402

BASE_PROVIDER = r'''
async function getStreams() {
  const token = setTimeout(function () { throw new Error("must_not_fire"); }, 25000);
  clearTimeout(token);
  return [{ url: "https://example.invalid/stream.m3u8", quality: "1080p" }];
}
this.getStreams = getStreams;
'''

patched = global_runtime_compat_v1.apply(BASE_PROVIDER)
assert 'typeof g.setTimeout!=="function"' in patched
assert 'typeof g.clearTimeout!=="function"' in patched

HARNESS = r'''
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
const context = { console };
vm.createContext(context);
if (typeof context.setTimeout !== 'undefined') throw new Error('timer unexpectedly preinstalled');
if (typeof context.clearTimeout !== 'undefined') throw new Error('clearTimer unexpectedly preinstalled');
vm.runInContext(source, context, { filename: 'synthetic-provider.js' });
if (typeof context.setTimeout !== 'function') throw new Error('Core did not install setTimeout');
if (typeof context.clearTimeout !== 'function') throw new Error('Core did not install clearTimeout');
if (typeof context.getStreams !== 'function') throw new Error('provider getStreams disappeared');
Promise.resolve(context.getStreams('157336', 'movie')).then((rows) => {
  if (!Array.isArray(rows) || rows.length !== 1) throw new Error('provider result missing');
  console.log('GLOBAL_RUNTIME_NO_TIMER_EXECUTION_OK rows=' + rows.length + ' setTimeout=' + typeof context.setTimeout + ' clearTimeout=' + typeof context.clearTimeout);
}).catch((error) => {
  console.error(error && error.stack || error);
  process.exit(1);
});
'''

with tempfile.TemporaryDirectory(prefix="niakvio-no-timer-") as tmp:
    root = Path(tmp)
    provider = root / "provider.js"
    harness = root / "harness.cjs"
    provider.write_text(patched, encoding="utf-8")
    harness.write_text(HARNESS, encoding="utf-8")
    subprocess.run(["node", str(harness), str(provider)], cwd=ROOT, check=True)

print("global runtime no-timer execution test passed: Desktop-like timer absence is Core-shimmed")
