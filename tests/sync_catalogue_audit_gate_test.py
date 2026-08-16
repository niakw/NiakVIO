#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync.yml"


def main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    prepare = text.index("- name: Build canonical publication transaction")
    audit = text.index("- name: Audit content identity and media")
    upload = text.index("- name: Upload catalogue/media audit")
    publish = text.index("- name: Publish atomic ARCHI2 transaction")
    push = text.index("git push origin HEAD:main", publish)
    assert prepare < audit < upload < publish < push

    assert "NUVIO_CATALOGUE_AUDIT_OUTPUT: /tmp/catalogue-media-audit.json" in text
    assert "NUVIO_CATALOGUE_AUDIT_WORKERS: '8'" in text
    assert "NUVIO_CATALOGUE_AUDIT_TIMEOUT: '60'" in text
    assert "python scripts/audit_catalogue_identity_media.py" in text
    assert 'name: catalogue-media-audit-${{ github.run_id }}' in text
    assert 'path: /tmp/catalogue-media-audit.json' in text

    audit_block = text[audit:upload]
    # Deep stays fail-closed because its audit call is executed under shell -e.
    assert 'if [ "${{ needs.stage-and-test.outputs.validation_mode }}" = "deep" ]' in audit_block
    # Quick may turn a strong audit failure into an explicit quarantine rather
    # than aborting the entire refresh, but it must then rerun the cache/version
    # finalizer, language projection and canonical catalog before publication.
    assert "quarantine_catalogue_audit_failures.py" in audit_block
    assert audit_block.count("sync_release_versions.py") == 1
    assert "validate_activation_preservation.py" in audit_block
    assert "validate_language_projection.py" in audit_block
    assert "bootstrap-provider-catalog.mjs" in audit_block
    assert "render-manifests-from-catalog.mjs" in audit_block
    assert "release_evidence_fence.py fingerprint" in audit_block

    publish_block = text[publish:push]
    assert "release_evidence_fence.py validate" in publish_block
    assert "generate_release_hashes.py" in publish_block
    assert "validate_release_integrity.py" in publish_block
    assert "provider-catalog.test.mjs" in publish_block

    # The publish job needs enough room for the cross-provider catalogue/media
    # proof plus the final version/hash transaction.
    publish_job = text[text.index("  publish:"):]
    timeout_line = next(line for line in publish_job.splitlines() if "timeout-minutes:" in line)
    assert int(timeout_line.split(":", 1)[1].strip()) >= 60, timeout_line
    print("ARCHI2 catalogue/media audit publication gate test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
