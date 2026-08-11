#!/usr/bin/env python3
"""Guard the deep provider publication as one atomic main-branch transaction."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/sync.yml").read_text(encoding="utf-8")

assert 'git commit -m "chore: stage validated provider versions"' not in workflow, (
    "deep workflow must not publish provider/report state before its manifest passes final gates"
)
assert workflow.count("git push origin HEAD:main") == 1, (
    "deep workflow must have exactly one main push after all publication gates"
)
assert 'git commit -m "chore: publish validated provider transaction"' in workflow

stage = workflow.index("Publish provider files and reports before the manifest")
activation = workflow.index("python scripts/validate_activation_preservation.py", stage)
commit = workflow.index('git commit -m "chore: publish validated provider transaction"', activation)
push = workflow.index("git push origin HEAD:main", commit)
assert stage < activation < commit < push

print("atomic deep publication workflow test passed")
