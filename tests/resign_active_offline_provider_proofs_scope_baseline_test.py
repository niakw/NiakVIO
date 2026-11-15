#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "resign_active_offline_provider_proofs.py"
spec = importlib.util.spec_from_file_location("resign_active_offline_provider_proofs", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root / "manifest.json", {"scrapers": []})
    write(
        root / "vf" / "manifest.json",
        {
            "scrapers": [
                {
                    "id": "frdemo",
                    "enabled": True,
                    "filename": "../providers/frdemo-new.js",
                }
            ]
        },
    )
    write(
        root / "PROVENANCE.json",
        {
            "providers": {
                "frdemo": {
                    "activation_mode": mod.MODE,
                    "check_mode": mod.MODE,
                }
            }
        },
    )
    previous_global = root / "previous-global.json"
    previous_vf = root / "previous-vf.json"
    write(previous_global, {"scrapers": []})
    write(
        previous_vf,
        {
            "scrapers": [
                {
                    "id": "frdemo",
                    "enabled": True,
                    "filename": "../providers/frdemo.js",
                }
            ]
        },
    )

    result = mod.rebind(
        root,
        apply=False,
        previous_manifest=previous_global,
        previous_vf_manifest=previous_vf,
        scope_filter="global",
    )
    assert result["providerCount"] == 0, result
    assert result["changedCount"] == 0, result

assert result["providerCount"] == 0, "France-only drift must not enter a Global-only rematerialization rebind"

WORKFLOW = (ROOT / ".github" / "workflows" / "release-finalize.yml").read_text(encoding="utf-8")
final_reconcile = WORKFLOW.index("python3 scripts/reconcile_active_provider_publication.py")
rebind_calls = [
    idx for idx in range(len(WORKFLOW))
    if WORKFLOW.startswith("python3 scripts/resign_active_offline_provider_proofs.py", idx)
]
assert len(rebind_calls) >= 2, "release finalizer must rebind offline proofs after the final byte reconciliation"
assert max(rebind_calls) > final_reconcile, (
    "final offline proof rebind must happen after reconcile_active_provider_publication.py"
)
assert WORKFLOW.index("python3 scripts/validate_provider_materialization_authority.py", final_reconcile) > max(rebind_calls)

print("scoped offline proof baseline test passed")
