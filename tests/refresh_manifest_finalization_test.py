#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "provider-refresh-repair.yml").read_text(encoding="utf-8")

prepare_anchor = "mv manifest.next.json manifest.json"
build = "python scripts/build_provider_runtime_profiles.py"
normalize = "python scripts/reapply_published_overrides.py"
language = "python scripts/generate_language_manifests.py"
check = "python scripts/reapply_published_overrides.py --check"
fingerprint = "python scripts/release_evidence_fence.py fingerprint"
hashes = "python scripts/generate_release_hashes.py"

prepare_pos = workflow.index(prepare_anchor)
build_pos = workflow.index(build, prepare_pos)
normalize_pos = workflow.index(normalize, build_pos)
language_pos = workflow.index(language, normalize_pos)
second_build_pos = workflow.index(build, language_pos)
second_normalize_pos = workflow.index(normalize, second_build_pos)
check_pos = workflow.index(check, second_normalize_pos)
fingerprint_pos = workflow.index(fingerprint, check_pos)
publish_build_pos = workflow.index(build, fingerprint_pos)
hashes_pos = workflow.index(hashes, publish_build_pos)

assert prepare_pos < build_pos < normalize_pos < language_pos, (
    "runtime profiles must be rebuilt from the promoted manifest before normalization/language projection"
)
assert language_pos < second_build_pos < second_normalize_pos < check_pos < fingerprint_pos, (
    "final manifest/profile state must reach an idempotent fixed point before release fingerprinting"
)
assert fingerprint_pos < publish_build_pos < hashes_pos, (
    "publication must re-derive profiles after the catalogue audit before calculating release hashes"
)
assert "PROVENANCE.json provider-overrides.json" in workflow, (
    "post-normalization provenance/override mutations must be staged into the atomic publication"
)
assert (
    "python scripts/build_provider_runtime_profiles.py\n"
    "          python scripts/reapply_published_overrides.py --check\n"
    "          git diff --exit-code\n"
    "          npm test"
) in workflow, (
    "exact-main verification must prove npm pretest cannot create a post-commit runtime-profile drift"
)

print("refresh manifest finalization idempotence test passed")
