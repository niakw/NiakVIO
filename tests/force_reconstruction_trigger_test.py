#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from consume_force_reconstruction_trigger import consume  # noqa: E402
from provider_base_store import (  # noqa: E402
    CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
    CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
    CLEAN_RECONSTRUCTION_SOURCE,
    build_base_from_seed,
    build_clean_provider_seed,
    sha256,
)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "provider-bases").mkdir(parents=True)
    stage = root / "stage"
    (stage / "providers").mkdir(parents=True)

    overrides = root / "provider-overrides.json"
    overrides.write_text(json.dumps({"provider_patches": {}, "provider_capabilities": {}}), encoding="utf-8")

    def candidate(provider_id: str) -> dict:
        metadata = {
            "id": provider_id,
            "name": provider_id.title(),
            "supportedTypes": ["movie", "tv"],
            "formats": ["m3u8"],
        }
        model = {
            "providerId": provider_id,
            "displayName": provider_id.title(),
            "knownSite": f"https://{provider_id}.example.org",
            "supportedTypes": ["movie", "tv"],
            "strategy": "direct_media",
            "origins": [f"https://{provider_id}.example.org"],
            "observedUrls": [f"https://{provider_id}.example.org/api/v1"],
            "routes": ["/api/v1", "/stream/{id}"],
            "reconstructionState": "learning-clean-seed",
            "runtimeRole": "reader",
            "runtimeDiscovery": False,
            "routePlanVersion": 1,
            "authoring": "niakvio-owned-v2",
            "upstreamCodeEmbedded": False,
            "upstreamCodeExecuted": False,
        }
        return {
            "canonical_id": provider_id,
            "upstream_id": provider_id,
            "clean_reconstruction_mode": True,
            "candidate_code_origin": "new-niakvio-clean-seed",
            "provider_base_reconstruction_required": True,
            "upstream_code_executed": False,
            "legacy_provider_js_executed_for_reconstruction": False,
            "observed_upstream_site": f"https://{provider_id}.example.org",
            "metadata": metadata,
            "clean_provider_model": model,
            "local_path": f"providers/{provider_id}.js",
        }

    candidates = [candidate("alpha"), candidate("beta")]
    registry = stage / "candidates.json"
    registry.write_text(json.dumps({"candidates": candidates}), encoding="utf-8")
    # Alpha was materially staged; beta is deliberately absent on the first pass.
    (stage / candidates[0]["local_path"]).write_text("// staged clean seed\n", encoding="utf-8")

    provenance_rows = {}
    alpha = candidates[0]
    alpha_seed = build_clean_provider_seed(
        "alpha",
        alpha["metadata"],
        known_site=alpha["observed_upstream_site"],
        provider_model=alpha["clean_provider_model"],
    )
    alpha_base, _ = build_base_from_seed("alpha", alpha_seed, overrides_path=overrides)
    alpha_digest = sha256(alpha_base)
    alpha_rel = f"provider-bases/alpha--base--{alpha_digest[:16]}.js"
    (root / alpha_rel).write_bytes(alpha_base)
    provenance_rows["alpha"] = {
        "base_source": CLEAN_RECONSTRUCTION_SOURCE,
        "base_filename": alpha_rel,
        "base_sha256": alpha_digest,
        "clean_reconstruction_candidate": False,
        "clean_reconstruction_verified": True,
        "clean_reconstruction_required": False,
    }

    provenance = root / "PROVENANCE.json"
    provenance.write_text(json.dumps({"providers": provenance_rows}), encoding="utf-8")

    trigger = root / "force.json"
    trigger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mode": "explicit-one-shot",
                "reason": "test",
                "providers": ["alpha", "beta"],
                "remove_after_materialization": True,
            }
        ),
        encoding="utf-8",
    )

    consumed, remaining = consume(trigger, registry, provenance, overrides, root)
    assert consumed == ["alpha"], (consumed, remaining)
    assert remaining == ["beta"], (consumed, remaining)
    persisted_trigger = json.loads(trigger.read_text(encoding="utf-8"))
    assert persisted_trigger["providers"] == ["beta"]
    assert persisted_trigger["consumedProviders"] == ["alpha"]

    # Staging alone must never consume beta: the one-shot remains active until
    # the exact deterministic clean ProviderBase is durable in repository state.
    (stage / candidates[1]["local_path"]).write_text("// staged clean seed\n", encoding="utf-8")
    consumed, remaining = consume(trigger, registry, provenance, overrides, root)
    assert consumed == [], (consumed, remaining)
    assert remaining == ["beta"], (consumed, remaining)
    persisted_trigger = json.loads(trigger.read_text(encoding="utf-8"))
    assert persisted_trigger["providers"] == ["beta"]
    assert persisted_trigger["consumedProviders"] == ["alpha"]

    beta = candidates[1]
    beta_seed = build_clean_provider_seed(
        "beta",
        beta["metadata"],
        known_site=beta["observed_upstream_site"],
        provider_model=beta["clean_provider_model"],
    )
    beta_base, _ = build_base_from_seed("beta", beta_seed, overrides_path=overrides)
    beta_digest = sha256(beta_base)
    beta_rel = f"provider-bases/beta--base--{beta_digest[:16]}.js"
    (root / beta_rel).write_bytes(beta_base)
    provenance_rows["beta"] = {
        "base_source": CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
        "base_filename": beta_rel,
        "base_sha256": beta_digest,
        "clean_reconstruction_candidate": True,
        "clean_reconstruction_verified": False,
        "clean_reconstruction_required": True,
        "clean_reconstruction_authoring_version": CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "legacy_provider_js_executed_for_reconstruction": False,
        "upstream_code_executed": False,
    }
    provenance.write_text(json.dumps({"providers": provenance_rows}), encoding="utf-8")

    consumed, remaining = consume(trigger, registry, provenance, overrides, root)
    assert consumed == ["beta"], (consumed, remaining)
    assert remaining == []
    assert not trigger.exists(), "one-shot trigger must disappear after exact durable materialization"

print("force reconstruction trigger lifecycle passed")
