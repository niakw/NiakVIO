#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prepare_brain_learning_parent_stage.py"
spec = importlib.util.spec_from_file_location("learning_parent_stage", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    published = root / "published"
    reconstruction = root / "reconstruction"
    output = root / "learning"
    (published / "providers").mkdir(parents=True)
    (reconstruction / "providers").mkdir(parents=True)

    exact_alpha = b'"use strict"; module.exports={getStreams:async()=>[{url:"https://media.invalid/a.m3u8"}]};\n'
    clean_alpha = b'"use strict"; module.exports={getStreams:async()=>[]};\n'
    exact_beta = b'"use strict"; module.exports={getStreams:async()=>[{url:"https://media.invalid/b.m3u8"}]};\n'
    clean_beta = b'"use strict"; module.exports={getStreams:async()=>[]}; /* clean required */\n'

    for name, data in (("alpha.js", exact_alpha), ("beta.js", exact_beta)):
        (published / "providers" / name).write_bytes(data)
    for name, data in (("alpha.js", clean_alpha), ("beta.js", clean_beta)):
        (reconstruction / "providers" / name).write_bytes(data)

    published_registry = {
        "candidates": [
            {
                "key": "published-v3:alpha",
                "source": "published-v3",
                "canonical_id": "alpha",
                "local_path": "providers/alpha.js",
                "sha256": sha(exact_alpha),
                "published_exact_bytes": True,
                "metadata": {"formats": ["movie"], "runtimeToken": "published"},
                "canonical_metadata": {"contentLanguage": ["fr"]},
                "repair_allowed": False,
            },
            {"key": "published-v3:beta", "canonical_id": "beta", "local_path": "providers/beta.js", "sha256": sha(exact_beta), "published_exact_bytes": True},
        ]
    }
    reconstruction_registry = {
        "candidates": [
            {
                "key": "local:alpha",
                "canonical_id": "alpha",
                "local_path": "providers/alpha.js",
                "sha256": sha(clean_alpha),
                "upstream_sha256": sha(exact_alpha),
                "patched_sha256": sha(clean_alpha),
                "local_patches": [{"type": "patch_script", "script": "synthetic", "count": 1}],
                "repair_history": [{"accepted": True, "profile": "synthetic"}],
                "provider_base_reconstruction_required": False,
                "candidate_code_origin": "existing-niakvio-provider-base-v2",
                "metadata": {"formats": ["anime"], "runtimeToken": "reconstruction"},
                "canonical_metadata": {"contentLanguage": ["en"]},
                "repair_allowed": True,
            },
            {"key": "local:beta", "canonical_id": "beta", "local_path": "providers/beta.js", "sha256": sha(clean_beta), "provider_base_reconstruction_required": True, "candidate_code_origin": "new-niakvio-clean-seed"},
        ]
    }
    (published / "candidates.json").write_text(json.dumps(published_registry))
    (reconstruction / "candidates.json").write_text(json.dumps(reconstruction_registry))

    report = module.prepare(published, reconstruction, output, ["alpha", "beta"])
    rows = module.rows_by_provider(json.loads((output / "candidates.json").read_text()))

    assert (output / "providers" / "alpha.js").read_bytes() == exact_alpha
    assert rows["alpha"]["sha256"] == sha(exact_alpha)
    assert rows["alpha"]["learning_parent_authority"] == "published-exact-current-candidate"
    assert rows["alpha"]["learning_parent_overlay_applied"] is True
    assert rows["alpha"]["learning_reconstruction_sha256"] == sha(clean_alpha)
    assert rows["alpha"]["provider_base_reconstruction_required"] is False
    assert rows["alpha"]["key"] == "published-v3:alpha"
    assert rows["alpha"]["source"] == "published-v3"
    assert rows["alpha"]["metadata"] == {"formats": ["movie"], "runtimeToken": "published"}
    assert rows["alpha"]["canonical_metadata"] == {"contentLanguage": ["fr"]}
    assert rows["alpha"]["repair_allowed"] is True
    assert rows["alpha"]["learning_parent_published_exact_metadata"] is True
    assert rows["alpha"]["learning_reconstruction_key"] == "local:alpha"
    assert rows["alpha"]["learning_reconstruction_candidate_code_origin"] == "existing-niakvio-provider-base-v2"
    assert rows["alpha"]["upstream_sha256"] == sha(exact_alpha)
    assert rows["alpha"]["patched_sha256"] == sha(exact_alpha)
    assert rows["alpha"]["local_patches"] == []
    assert rows["alpha"]["repair_history"] == []

    assert (output / "providers" / "beta.js").read_bytes() == clean_beta
    assert rows["beta"]["sha256"] == sha(clean_beta)
    assert rows["beta"]["learning_parent_authority"] == "clean-reconstruction-required"
    assert rows["beta"]["learning_parent_overlay_applied"] is False
    assert rows["beta"]["provider_base_reconstruction_required"] is True

    # The deterministic reconstruction oracle is immutable: overlay happens only
    # in the isolated Learning execution stage.
    assert (reconstruction / "providers" / "alpha.js").read_bytes() == clean_alpha
    assert (reconstruction / "providers" / "beta.js").read_bytes() == clean_beta
    assert report["overlaidPublishedExactProviders"] == ["alpha"]
    assert report["retainedCleanReconstructionProviders"] == ["beta"]
    assert report["proofAuthority"] is False
    assert report["publicationAuthority"] is False

print("Brain Learning published-parent execution stage contract passed")
