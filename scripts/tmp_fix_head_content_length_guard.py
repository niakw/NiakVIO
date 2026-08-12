#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
worker = ROOT / 'scripts' / 'provider_worker.cjs'
test = ROOT / 'tests' / 'provider_worker_security.test.cjs'

source = worker.read_text(encoding='utf-8')
old = "        if (declaredLength > maxResponseBytes) throw new Error(`response body exceeds limit (${declaredLength} bytes)`);"
new = "        if (requestMeta.method !== 'HEAD' && declaredLength > maxResponseBytes) throw new Error(`response body exceeds limit (${declaredLength} bytes)`);"
if new not in source:
    if old not in source:
        raise SystemExit('provider worker content-length anchor missing')
    source = source.replace(old, new, 1)
worker.write_text(source, encoding='utf-8')

source = test.read_text(encoding='utf-8')
anchor = "assert.match(result.stdout,/provider module blocked: node:child_process/);\n"
block = "assert.match(result.stdout,/provider module blocked: node:child_process/);\nconst workerSource=fs.readFileSync(path.join(root,'scripts/provider_worker.cjs'),'utf8');\nassert.match(workerSource,/requestMeta\\.method !== 'HEAD' && declaredLength > maxResponseBytes/);\n"
if block not in source:
    if anchor not in source:
        raise SystemExit('provider worker security test anchor missing')
    source = source.replace(anchor, block, 1)
test.write_text(source, encoding='utf-8')
print('HEAD content-length guard fix applied')
