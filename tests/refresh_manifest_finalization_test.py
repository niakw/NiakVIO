#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "provider-refresh-repair.yml").read_text(encoding="utf-8")

prepare_anchor = "mv manifest.next.json manifest.json"
normalize = "python scripts/reapply_published_overrides.py"
language = "python scripts/generate_language_manifests.py"
check = "python scripts/reapply_published_overrides.py --check"

prepare_pos = workflow.index(prepare_anchor)
normalize_pos = workflow.index(normalize, prepare_pos)
language_pos = workflow.index(language, prepare_pos)
check_pos = workflow.index(check, prepare_pos)

assert prepare_pos < normalize_pos < language_pos, (
    "published manifest must be normalized after manifest.next promotion and before language projection"
)
assert normalize_pos < check_pos, "manifest normalization must be checked for idempotence before publication"
assert "PROVENANCE.json provider-overrides.json" in workflow, (
    "post-normalization provenance/override mutations must be staged into the atomic publication"
)
assert "python scripts/reapply_published_overrides.py --check\n          npm test" in workflow, (
    "exact-main verification must assert normalization is already idempotent before npm lifecycle hooks"
)

print("refresh manifest finalization idempotence test passed")
