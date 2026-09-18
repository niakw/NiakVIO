#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATCHES=ROOT/'scripts'/'provider_patches'

forbidden=('searchParams.set(', 'searchParams.delete(')
hits=[]
for path in sorted(PATCHES.glob('*.py')):
    text=path.read_text(encoding='utf-8')
    for token in forbidden:
        if token in text:
            hits.append(f"{path.relative_to(ROOT)}:{token}")

assert not hits, "QuickJS-incompatible provider Lego remains: " + ", ".join(hits)
print("provider patch QuickJS compatibility test passed")
