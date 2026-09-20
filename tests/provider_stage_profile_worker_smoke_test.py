#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from provider_base_store import build_clean_provider_seed, build_provider_data_model, compose_provider_bundle  # noqa: E402

OVERRIDES = ROOT / "provider-overrides.json"

fixture = {
    "tmdbId": "157336",
    "id": "157336",
    "mediaType": "movie",
    "type": "movie",
    "category": "movie",
    "title": "Interstellar",
    "year": 2014,
}
context = {
    "platform": "android",
    "locale": "en-US",
    "languages": ["en-US", "en"],
    "maxSettingsProfiles": 1,
    "networkLimits": {
        "maxFetches": 2,
        "maxResponseBytes": 65536,
        "maxTotalResponseBytes": 131072,
        "maxDistinctHosts": 2,
    },
}

original_overrides = OVERRIDES.read_bytes()
try:
    with tempfile.TemporaryDirectory(prefix="niakvio-stage-profile-worker-") as tmp:
        stage = Path(tmp)
        providers = stage / "providers" / "synthetic"
        providers.mkdir(parents=True)
        provider = providers / "brandnew.js"
        entry = {
            "id": "brandnew",
            "name": "BrandNew",
            "supportedTypes": ["movie"],
            "canonicalSupportedTypes": ["movie"],
        }
        model = build_provider_data_model(
            "brandnew",
            entry,
            known_site="https://brandnew.example",
            provider_model={
                "strategy": "html_scraper",
                "officialSite": "https://brandnew.example",
                "origins": ["https://brandnew.example"],
                "routes": [],
            },
        )
        payload = compose_provider_bundle(
            "brandnew",
            build_clean_provider_seed("brandnew"),
            model,
        )
        provider.write_bytes(payload)
        registry = {
            "schema_version": 63,
            "candidates": [{
                "key": "synthetic:brandnew",
                "source": "synthetic",
                "upstream_id": "brandnew",
                "canonical_id": "brandnew",
                "local_path": str(provider.relative_to(stage)),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "local_patches": [],
                "candidate_code_origin": "new-niakvio-clean-seed",
                "upstream_code_executed": False,
                "legacy_provider_js_executed_for_reconstruction": False,
                "metadata": {
                    "id": "brandnew",
                    "name": "BrandNew",
                    "supportedTypes": ["movie"],
                },
            }],
        }
        (stage / "candidates.json").write_text(
            json.dumps(registry, indent=2) + "\n",
            encoding="utf-8",
        )

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "build_provider_runtime_profiles.py"),
                "--stage",
                str(stage),
                "--apply-stage",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        completed = subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "provider_worker.cjs"),
                str(provider),
                json.dumps(fixture, separators=(",", ":")),
                json.dumps(context, separators=(",", ":")),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        marker = "NUVIO_HEALTH_RESULT="
        rows = [
            line[len(marker):]
            for line in completed.stdout.splitlines()
            if line.startswith(marker)
        ]
        assert rows, (
            "stage-profile worker emitted no protocol result; "
            f"exit={completed.returncode} stderr={completed.stderr[-2000:]}"
        )
        result = json.loads(rows[-1])
        assert result.get("ok") is True, (
            "build_provider_runtime_profiles --apply-stage produced runtime-invalid bytes: "
            + json.dumps(
                result.get("error_details") or {"error": result.get("error")},
                ensure_ascii=False,
            )
        )
        assert int(result.get("stream_count") or 0) == 0, result
        updated = json.loads((stage / "candidates.json").read_text(encoding="utf-8"))
        candidate = updated["candidates"][0]
        assert candidate["sha256"] == hashlib.sha256(provider.read_bytes()).hexdigest()
finally:
    OVERRIDES.write_bytes(original_overrides)

print("stage runtime-profile real-worker smoke test passed")
