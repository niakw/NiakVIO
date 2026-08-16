#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "provider-refresh-repair.yml").read_text(encoding="utf-8")

prepare_anchor = "mv manifest.next.json manifest.json"
build = "python scripts/build_provider_runtime_profiles.py"
normalize = "python scripts/reapply_published_overrides.py"
language = "python scripts/generate_language_manifests.py"
fingerprint = "python scripts/release_evidence_fence.py fingerprint"
hashes = "python scripts/generate_release_hashes.py"
coverage = "python scripts/interstellar_nuvio_matrix.py"

prepare_pos = workflow.index(prepare_anchor)
build_pos = workflow.index(build, prepare_pos)
normalize_pos = workflow.index(normalize, build_pos)
language_pos = workflow.index(language, normalize_pos)
fingerprint_pos = workflow.index(fingerprint, language_pos)
coverage_pos = workflow.index(coverage, fingerprint_pos)
publish_build_pos = workflow.index(build, coverage_pos)
hashes_pos = workflow.index(hashes, publish_build_pos)

assert prepare_pos < build_pos < normalize_pos < language_pos < fingerprint_pos, (
    "promoted manifest must be normalized once before language projection/evidence"
)
assert fingerprint_pos < coverage_pos < publish_build_pos < hashes_pos, (
    "coverage stays diagnostic, then one final normalization precedes release hashes"
)
assert "--minimum-automatic 10" not in workflow, (
    "coverage diagnostics must not block routine publication"
)
assert "--minimum-automatic 0" in workflow and "continue-on-error: true" in workflow, (
    "Interstellar coverage must be measured without becoming a publication gate"
)
assert "Verify exact published main" not in workflow, (
    "push-triggered validation owns post-publish checks; routine refresh must not duplicate them"
)
assert "python scripts/normalize_provider_activation_overrides.py\n" in workflow
assert "python scripts/normalize_provider_activation_overrides.py --check" not in workflow

print("refresh manifest lean finalization test passed")
