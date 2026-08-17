#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync.yml"
sys.path.insert(0, str(ROOT / "scripts"))

from quarantine_catalogue_audit_failures import derive_scopes, scoped_quarantine_source  # noqa: E402


def assert_scoped_quarantine_runtime() -> None:
    single_tv = [{
        "fixture": "vf_revenant_s01e01",
        "provider_id": "streamzo",
        "identity_contradiction_count": 1,
        "playable_stream_count": 1,
    }]
    scopes = derive_scopes(single_tv)
    assert len(scopes) == 1 and scopes[0]["kind"] == "fixture", scopes
    assert scopes[0]["mediaType"] == "tv" and scopes[0]["tmdbId"] == "126485", scopes

    impossible = [{
        "fixture": "impossible_movie",
        "provider_id": "example",
        "identity_contradiction_count": 1,
        "playable_identity_false_positive": True,
        "playable_stream_count": 1,
    }]
    impossible_scopes = derive_scopes(impossible)
    assert impossible_scopes == [{
        "kind": "media_type",
        "mediaType": "movie",
        "reason": "playable_unknown_identity_false_positive",
    }], impossible_scopes

    repeated_tv = single_tv + [{
        "fixture": "vf_jjk_s01e01",
        "provider_id": "streamzo",
        "identity_contradiction_count": 1,
        "playable_stream_count": 1,
    }]
    repeated_scopes = derive_scopes(repeated_tv)
    assert repeated_scopes == [{
        "kind": "media_type",
        "mediaType": "tv",
        "reason": "repeated_playable_identity_contradiction",
    }], repeated_scopes

    source = "module.exports={getStreams:async function(id,type,season,episode){return [{url:'https://media.example/ok.mp4'}]}};"
    wrapped = scoped_quarantine_source(source, "streamzo", scopes)
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as handle:
        handle.write(wrapped)
        handle.write("\n(async()=>{const p=module.exports;const movie=await p.getStreams('1215638','movie',null,null);const bad=await p.getStreams('126485','tv',1,1);const other=await p.getStreams('95479','tv',1,1);const objectBad=await p.getStreams({tmdbId:'126485',mediaType:'tv',season:1,episode:1});if(movie.length!==1||bad.length!==0||other.length!==1||objectBad.length!==0)process.exit(7)})().catch(()=>process.exit(8));\n")
        path = Path(handle.name)
    try:
        result = subprocess.run(["node", str(path)], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        path.unlink(missing_ok=True)


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
    assert 'if [ "${{ needs.stage-and-test.outputs.validation_mode }}" = "deep" ]' in audit_block
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

    publish_job = text[text.index("  publish:"):]
    timeout_line = next(line for line in publish_job.splitlines() if "timeout-minutes:" in line)
    assert int(timeout_line.split(":", 1)[1].strip()) >= 60, timeout_line

    assert_scoped_quarantine_runtime()
    print("ARCHI2 catalogue/media audit publication gate and scoped quarantine tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
