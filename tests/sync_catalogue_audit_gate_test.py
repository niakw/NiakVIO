#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync.yml"


def main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    prepare = text.index("- name: Prepare validated manifest transaction")
    audit = text.index("- name: Block wrong-content and broken HLS publication")
    upload = text.index("- name: Upload global catalogue and media audit")
    publish = text.index("- name: Publish globally audited manifest transaction")
    push = text.index("git push origin HEAD:main", publish)
    assert prepare < audit < upload < publish < push
    assert 'NUVIO_CATALOGUE_AUDIT_OUTPUT: /tmp/catalogue-media-audit.json' in text
    assert 'NUVIO_CATALOGUE_AUDIT_WORKERS: "8"' in text
    assert 'NUVIO_CATALOGUE_AUDIT_TIMEOUT: "60"' in text
    assert 'run: python scripts/audit_catalogue_identity_media.py' in text
    assert 'name: catalogue-media-audit-${{ github.run_id }}' in text
    assert 'path: /tmp/catalogue-media-audit.json' in text
    audit_block = text[audit:upload]
    assert "continue-on-error" not in audit_block
    publish_block = text[publish:push]
    assert "generate_release_hashes.py" in publish_block
    assert "validate_release_integrity.py" in publish_block
    # The publish job needs enough room for the already-long deep transaction
    # plus the cross-provider catalogue/media proof.
    publish_job = text[text.index("  publish:"):]
    timeout_line = next(line for line in publish_job.splitlines() if "timeout-minutes:" in line)
    assert int(timeout_line.split(":", 1)[1].strip()) >= 60, timeout_line
    print("blocking global catalogue/media audit gate test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
