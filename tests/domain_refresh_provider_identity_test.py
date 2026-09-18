#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

import refresh_authoritative_hub_domains as refresh

cfg={
    'terminal_aliases':['4khdhub'],
    'allowed_terminal_hosts':['4khdhub.one'],
    'blocked_hosts':['hdhub4u.bi','hdhub4u.ms'],
}
same={'source_type':'redirect','url':'https://4khdhub.new/'}
explicit={'source_type':'redirect','url':'https://4khdhub.one/'}
cross={'source_type':'redirect','url':'https://hdhub4u.download/'}

assert refresh._safe_authoritative_candidate('4khdhub',cfg,same) is True
assert refresh._safe_authoritative_candidate('4khdhub',cfg,explicit) is True
assert refresh._safe_authoritative_candidate('4khdhub',cfg,cross) is False

# Providers without terminal_aliases retain the previous permissive rotation
# policy, subject to the existing safety/blocked-host gates.
generic={'allowed_terminal_hosts':[],'blocked_hosts':[]}
assert refresh._safe_authoritative_candidate(
    'generic',generic,{'source_type':'hub','url':'https://new-domain.example/'}
) is True

# The real curated registry must outrank stale embedded official_domain_hubs.
import json
config=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
hubs=refresh._authoritative_hub_configs(config)
row=hubs['4khdhub']
assert str(row.get('hub') or '').rstrip('/') == 'https://4khdhub.one'
assert str((row.get('direct_candidates') or [''])[0]).rstrip('/') == 'https://4khdhub.one'
assert '4khdhub' in [str(x).casefold() for x in row.get('terminal_aliases') or []]
assert 'hdhub4u.bi' in [str(x).casefold() for x in row.get('blocked_hosts') or []]

print('Domain Refresh curated-priority + provider-identity contract passed')
