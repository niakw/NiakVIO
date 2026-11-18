#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (
    ROOT / ".github/workflows/temp-current-bytes-full-provider-census.yml"
).read_text(encoding="utf-8")

persist = workflow.index("- name: Persist exact census evidence")
push = workflow.index("git push origin HEAD:main", persist)
dispatch = workflow.index("gh workflow run provider-disabled-lifecycle.yml", push)
field = workflow.index("FIELD_CURRENT_BYTES_CENSUS_LIFECYCLE", dispatch)
assert persist < push < dispatch < field
assert "--ref main" in workflow[dispatch:field]
assert "actions: write" in workflow
print("current bytes census explicitly hands persisted proof to Provider Disabled Lifecycle")
