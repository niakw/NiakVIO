#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from provider_base_store import build_clean_provider_seed, build_provider_data_model, compose_provider_bundle  # noqa: E402

OVERRIDES = ROOT / "provider-overrides.json"
original_overrides = OVERRIDES.read_bytes()

def make_provider(stage: Path, provider_id: str) -> tuple[Path, dict]:
    path = stage / "providers" / "synthetic" / f"{provider_id}.js"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": provider_id,
        "name": provider_id.title(),
        "supportedTypes": ["movie"],
        "canonicalSupportedTypes": ["movie"],
    }
    model = build_provider_data_model(
        provider_id,
        entry,
        known_site=f"https://{provider_id}.example",
        provider_model={
            "strategy": "html_scraper",
            "officialSite": f"https://{provider_id}.example",
            "origins": [f"https://{provider_id}.example"],
            "routes": [],
        },
    )
    payload = compose_provider_bundle(
        provider_id,
        build_clean_provider_seed(provider_id),
        model,
    )
    path.write_bytes(payload)
    candidate = {
        "key": f"synthetic:{provider_id}",
        "source": "synthetic",
        "upstream_id": provider_id,
        "canonical_id": provider_id,
        "local_path": str(path.relative_to(stage)),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "local_patches": [],
        "candidate_code_origin": "new-niakvio-clean-seed",
        "upstream_code_executed": False,
        "legacy_provider_js_executed_for_reconstruction": False,
        "metadata": {
            "id": provider_id,
            "name": provider_id.title(),
            "supportedTypes": ["movie"],
        },
    }
    return path, candidate

try:
    with tempfile.TemporaryDirectory(prefix="niakvio-targeted-profiles-") as tmp:
        stage = Path(tmp)
        alpha_path, alpha = make_provider(stage, "alpha")
        beta_path, beta = make_provider(stage, "beta")
        registry = {
            "schema_version": 63,
            "candidates": [alpha, beta],
        }
        registry_path = stage / "candidates.json"
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

        beta_before = beta_path.read_bytes()
        beta_sha_before = beta["sha256"]
        beta_patches_before = copy.deepcopy(beta["local_patches"])

        overrides = json.loads(original_overrides.decode("utf-8"))
        generation = overrides.setdefault("provider_profile_generation", {})
        generation["provider_count"] = 777
        generation["staged_provider_count"] = 555
        generation["source"] = "targeted-test-sentinel"
        OVERRIDES.write_text(json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "build_provider_runtime_profiles.py"),
                "--stage",
                str(stage),
                "--apply-stage",
                "--provider",
                "alpha",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=40,
        )
        assert completed.returncode == 0, (
            f"targeted profile refresh failed: stdout={completed.stdout[-3000:]} "
            f"stderr={completed.stderr[-5000:]}"
        )
        assert "staged=1" in completed.stdout, completed.stdout

        updated_registry = json.loads(registry_path.read_text(encoding="utf-8"))
        rows = {row["canonical_id"]: row for row in updated_registry["candidates"]}
        assert beta_path.read_bytes() == beta_before, "non-target provider bytes changed"
        assert rows["beta"]["sha256"] == beta_sha_before, rows["beta"]
        assert rows["beta"]["local_patches"] == beta_patches_before, rows["beta"]

        after = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        generation_after = after["provider_profile_generation"]
        assert generation_after["provider_count"] == 777, generation_after
        assert generation_after["staged_provider_count"] == 555, generation_after
        assert generation_after["source"] == "targeted-test-sentinel", generation_after
        assert generation_after["last_refresh_scope"] == "targeted", generation_after
        assert generation_after["last_targeted_provider_count"] == 1, generation_after
        assert generation_after["last_targeted_staged_provider_count"] == 1, generation_after
        assert generation_after["last_targeted_providers"] == ["alpha"], generation_after

        caps = after.get("provider_capabilities") or {}
        assert "alpha" in caps, "target provider capability not refreshed"
finally:
    OVERRIDES.write_bytes(original_overrides)

print("Learning targeted runtime-profile behavior test passed")
