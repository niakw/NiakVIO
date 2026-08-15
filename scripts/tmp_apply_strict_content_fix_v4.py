#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / 'scripts' / 'tmp_apply_strict_content_fix_v3.py'
spec = importlib.util.spec_from_file_location('strict_fix_v3', V3)
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load strict content fix v3')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.mod.main()

# v3's own post-processing runs only in its __main__ block, so reproduce the
# episode-marker exemption here before refining precedence.
path = ROOT / 'scripts' / 'nuvio_client_lab.cjs'
text = path.read_text(encoding='utf-8')
old_loop = """  for (const strongLabel of strongIdentityLabels) {
    const strongTokens = contentTokens(strongLabel);
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
"""
new_loop = """  for (const strongLabel of strongIdentityLabels) {
    const carriesEpisodeIdentity = /(?:^|\\D)s(?:eason|aison)?\\s*0*\\d{1,3}\\s*[-_. ]*e(?:p(?:isode)?)?\\s*0*\\d{1,4}(?:\\D|$)/i.test(strongLabel)
      || /(?:season|saison)\\s*0*\\d{1,3}/i.test(strongLabel)
      || /(?:^|\\D)(?:episode|ep)\\s*0*\\d{1,4}(?:\\D|$)/i.test(strongLabel);
    if (carriesEpisodeIdentity) continue;
    const strongTokens = contentTokens(strongLabel);
    if (strongTokens.length >= 2 && expectedTokens.size && !strongTokens.some((token) => expectedTokens.has(token))) {
"""
if old_loop not in text:
    raise RuntimeError('strong identity loop missing after base patch')
text = text.replace(old_loop, new_loop, 1)
needle = """  const strongIdentityLabels = [stream?.title, stream?.filename, mediaFilename]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
  for (const strongLabel of strongIdentityLabels) {
"""
replacement = """  const strongIdentityLabels = [stream?.title, stream?.filename, mediaFilename]
    .map((value) => String(value || '').trim())
    .filter(Boolean);
  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };
  for (const strongLabel of strongIdentityLabels) {
"""
if needle not in text:
    raise RuntimeError('strong identity block missing after episode refinement')
text = text.replace(needle, replacement, 1)
late = "  if (normalized && forbiddenAliases.some((alias) => normalized.includes(alias))) return { status: 'contradiction', reason: 'forbidden_title_alias' };\n  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };\n"
if late not in text:
    raise RuntimeError('late forbidden alias gate missing')
text = text.replace(late, "  if (normalized && expected.some((alias) => normalized.includes(alias))) return { status: 'match', reason: 'expected_title_alias' };\n", 1)
path.write_text(text, encoding='utf-8')
print('strict content promotion patch v4 applied')
