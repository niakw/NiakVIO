#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reindex_provider_publication_fingerprints.py"


def load_module():
    spec = importlib.util.spec_from_file_location("reindex_provider_publication_fingerprints_union_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        providers = root / "providers"
        providers.mkdir()
        rows = []
        provenance_rows = {}
        byte_proof = {}
        for provider_id, marker in (("global-one", b"global"), ("france-only", b"france")):
            path = providers / f"{provider_id}-0123456789abcdef.js"
            payload = b"// " + marker + b"\n"
            path.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            relative = path.relative_to(root).as_posix()
            rows.append({"id": provider_id, "filename": relative, "enabled": True})
            provenance_rows[provider_id] = {
                "published_filename": relative,
                "sha256": digest,
            }
            byte_proof[provider_id] = payload

        overrides = root / "provider-overrides.json"
        provenance = root / "PROVENANCE.json"
        overrides.write_text(json.dumps({"provider_patches": {}, "provider_capabilities": {}}) + "\n")
        provenance.write_text(json.dumps({"providers": provenance_rows}) + "\n")

        module.ROOT = root
        module.OVERRIDES = overrides
        module.PROVENANCE = provenance
        module.PUBLICATION_CONTRACT_SCHEMA = 4
        module.projection_active_provider_rows = lambda: list(rows)
        module.publication_contract_sha = lambda config: "contract-sha"
        module.provider_policy_sha = lambda config, provider_id: f"policy-{provider_id}"
        module.resolve_runtime_base = lambda provider_id, row, require=True: (
            root / f"{provider_id}.base.js",
            f"base-{provider_id}",
        )
        module.provider_build_input_sha = (
            lambda provider_id, base_sha, contract_sha, policy_sha, row:
            f"build-{provider_id}-{base_sha}-{contract_sha}-{policy_sha}"
        )

        assert module.main() == 0
        result = json.loads(provenance.read_text())
        assert result["provider_publication_contract"]["provider_count"] == 2
        for provider_id in ("global-one", "france-only"):
            row = result["providers"][provider_id]
            assert row["build_contract_schema"] == 4
            assert row["provider_policy_sha256"] == f"policy-{provider_id}"
            assert row["build_input_sha256"].startswith(f"build-{provider_id}-")
            path = root / row["published_filename"]
            assert path.read_bytes() == byte_proof[provider_id]

    print("PROVIDER_PUBLICATION_FINGERPRINT_UNION_OK global=1 france_only=1 bytes_changed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
