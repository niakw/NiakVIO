#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflows = {
    "full": ROOT / ".github/workflows/temp-current-bytes-full-provider-census.yml",
    "sharded": ROOT / ".github/workflows/provider-census-sharded.yml",
    "waf": ROOT / ".github/workflows/provider-waf-browser-session.yml",
    "repair": ROOT / ".github/workflows/provider-recognition-repair-v6.yml",
}

for name, path in workflows.items():
    text = path.read_text(encoding="utf-8")
    assert "merge_waf_latest_evidence.py" in text, f"{name}: durable WAF latest merge missing"

full = workflows["full"].read_text(encoding="utf-8")
assert "--previous automation/provider-waf-browser-session-latest.json" in full
assert '--current "/tmp/provider-waf-browser-session-${run_id}.json"' in full
assert 'git add "automation/provider-waf-browser-session-${run_id}.json" automation/provider-waf-browser-session-latest.json' in full

sharded = workflows["sharded"].read_text(encoding="utf-8")
assert "--current /tmp/provider-waf-browser-session-sharded.json" in sharded
assert "automation/provider-waf-browser-session-latest.json" in sharded

waf = workflows["waf"].read_text(encoding="utf-8")
assert "Merge current transport refresh into durable latest" in waf
assert "--previous /tmp/provider-waf-prior.json" in waf

repair = workflows["repair"].read_text(encoding="utf-8")
assert 'cp "$waf" "$RUNNER_TEMP/provider-repair-waf-prior.json"' in repair
assert "Merge Repair transport refresh into durable latest" in repair
assert '--previous "$prior"' in repair

print("WAF latest automatic merge workflow contract passed")
