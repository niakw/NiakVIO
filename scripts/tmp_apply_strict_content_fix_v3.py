#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / 'scripts' / 'tmp_apply_strict_content_fix_v2.py'
spec = importlib.util.spec_from_file_location('strict_fix_v2', V2)
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load strict content fix v2')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.main()

path = ROOT / 'scripts' / 'nuvio_client_lab.cjs'
text = path.read_text(encoding='utf-8')
old = """  for (const strongLabel of strongIdentityLabels) {
    const strongTokens = contentTokens(strongLabel);
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
"""
new = """  for (const strongLabel of strongIdentityLabels) {
    const carriesEpisodeIdentity = /(?:^|\\D)s(?:eason|aison)?\\s*0*\\d{1,3}\\s*[-_. ]*e(?:p(?:isode)?)?\\s*0*\\d{1,4}(?:\\D|$)/i.test(strongLabel)
      || /(?:season|saison)\\s*0*\\d{1,3}/i.test(strongLabel)
      || /(?:^|\\D)(?:episode|ep)\\s*0*\\d{1,4}(?:\\D|$)/i.test(strongLabel);
    if (carriesEpisodeIdentity) continue;
    const strongTokens = contentTokens(strongLabel);
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
"""
if old not in text:
    raise RuntimeError('strong identity loop anchor missing after v2 patch')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('strict content promotion patch v3 applied')
