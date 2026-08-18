#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / '.github' / 'workflows'
SHA = re.compile(r'^[0-9a-f]{40}$', re.IGNORECASE)
USES = re.compile(r'^\s*(?:-\s*)?uses:\s*([^\s#]+)', re.MULTILINE)
errors: list[str] = []

for path in sorted([*WORKFLOWS.glob('*.yml'), *WORKFLOWS.glob('*.yaml')]):
    text = path.read_text(encoding='utf-8')
    rel = path.relative_to(ROOT)
    if re.search(r'^\s*pull_request_target\s*:', text, re.MULTILINE):
        errors.append(f'{rel}: pull_request_target is forbidden')
    if re.search(r'^\s*permissions\s*:\s*write-all\s*$', text, re.MULTILINE):
        errors.append(f'{rel}: permissions write-all is forbidden')
    if 'permissions:' not in text:
        errors.append(f'{rel}: explicit permissions are required')
    for match in USES.finditer(text):
        value = match.group(1).strip('"\'')
        if value.startswith('./'):
            continue
        if value.startswith('docker://'):
            if '@sha256:' not in value:
                errors.append(f'{rel}: Docker action/image must be digest-pinned: {value}')
            continue
        if '@' not in value:
            errors.append(f'{rel}: action/ref missing immutable pin: {value}')
            continue
        _action, ref = value.rsplit('@', 1)
        if not SHA.fullmatch(ref):
            errors.append(f'{rel}: external action must use full commit SHA: {value}')

if errors:
    raise SystemExit('workflow security policy failed:\n- ' + '\n- '.join(errors))
print('workflow security policy tests passed')
