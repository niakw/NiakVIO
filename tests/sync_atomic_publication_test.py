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
assert "provider_catalog.json" in workflow
assert "python scripts/sync_release_versions.py" in workflow
assert "--manifest manifest.json" in workflow
assert '--previous "$PREVIOUS_MANIFEST"' in workflow

build = workflow.index("Build canonical publication transaction")
version = workflow.index("python scripts/sync_release_versions.py", build)
manifest_arg = workflow.index("--manifest manifest.json", version)
previous_arg = workflow.index('--previous "$PREVIOUS_MANIFEST"', manifest_arg)
activation = workflow.index("python scripts/validate_activation_preservation.py", previous_arg)
catalog = workflow.index("node engine_v2/scripts/bootstrap-provider-catalog.mjs", activation)
hashes = workflow.index("python scripts/generate_release_hashes.py", catalog)
commit = workflow.index('git commit -m "chore: publish validated ARCHI2 provider transaction"', hashes)
push = workflow.index("git push origin HEAD:main", commit)
verify = workflow.index("Verify exact published main", push)

assert build < version < manifest_arg < previous_arg < activation < catalog < hashes < commit < push < verify
assert "git add -A providers" in workflow
assert workflow.index("git add -A providers", hashes) < commit

print("atomic ARCHI2 publication workflow test passed")
