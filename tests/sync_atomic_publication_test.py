#!/usr/bin/env python3
"""Guard ARCHI2 publication as one atomic main-branch transaction."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")

assert workflow.count("git push origin HEAD:main") == 1, (
    "ARCHI2 must have exactly one main push after all publication gates"
)
assert 'git commit -m "chore: publish validated ARCHI2 provider transaction"' in workflow
assert "Publish atomic ARCHI2 transaction" in workflow
assert "Build canonical publication transaction" in workflow
assert "Audit content identity and media" in workflow
assert "provider_catalog.json" in workflow
assert workflow.count("python scripts/sync_release_versions.py") >= 2
assert workflow.count("--manifest manifest.json") >= 2
assert workflow.count('--previous "$NUVIO_PUBLISHED_MANIFEST_BASELINE"') >= 2
assert "Capture published manifest baseline" in workflow

build = workflow.index("Build canonical publication transaction")
first_version = workflow.index("python scripts/sync_release_versions.py", build)
first_activation = workflow.index("python scripts/validate_activation_preservation.py", first_version)
audit = workflow.index("Audit content identity and media", first_activation)
final_version = workflow.index("python scripts/sync_release_versions.py", audit)
final_activation = workflow.index("python scripts/validate_activation_preservation.py", final_version)
final_catalog = workflow.index("node engine_v2/scripts/bootstrap-provider-catalog.mjs", final_activation)
hashes = workflow.index("python scripts/generate_release_hashes.py", final_catalog)
commit = workflow.index('git commit -m "chore: publish validated ARCHI2 provider transaction"', hashes)
push = workflow.index("git push origin HEAD:main", commit)
verify = workflow.index("Verify exact published main", push)

assert build < first_version < first_activation < audit < final_version < final_activation < final_catalog < hashes < commit < push < verify
assert "git add -A providers" in workflow
assert workflow.index("git add -A providers", hashes) < commit

print("atomic ARCHI2 publication workflow test passed")
