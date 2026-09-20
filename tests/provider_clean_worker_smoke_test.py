#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_base_store import (  # noqa: E402
    build_clean_provider_seed,
    build_provider_data_model,
    compose_provider_bundle,
)
from apply_provider_overrides import apply_overrides  # noqa: E402

entry = {
    "name": "Synthetic Clean Worker",
    "supportedTypes": ["movie"],
    "canonicalSupportedTypes": ["movie"],
}
model = build_provider_data_model(
    "synthetic-clean-worker",
    entry,
    known_site="https://example.invalid",
    provider_model={
        "strategy": "html_scraper",
        "officialSite": "https://example.invalid",
        "origins": ["https://example.invalid"],
        "routes": [],
    },
)
bundle = compose_provider_bundle(
    "synthetic-clean-worker",
    build_clean_provider_seed("synthetic-clean-worker"),
    model,
)

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
        "maxFetches": 4,
        "maxResponseBytes": 131072,
        "maxTotalResponseBytes": 262144,
        "maxDistinctHosts": 2,
    },
}

def run_worker(provider: Path) -> dict:
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
        "clean ProviderBase worker emitted no protocol result; "
        f"exit={completed.returncode} stderr={completed.stderr[-2000:]}"
    )
    return json.loads(rows[-1])


with tempfile.TemporaryDirectory(prefix="niakvio-clean-worker-") as tmp:
    root = Path(tmp)
    provider = root / "provider.js"
    provider.write_bytes(bundle)

    bare = run_worker(provider)
    assert bare.get("ok") is True, (
        "bare clean ProviderBase is syntax-valid but runtime-invalid: "
        + json.dumps(bare.get("error_details") or {"error": bare.get("error")}, ensure_ascii=False)
    )
    assert int(bare.get("stream_count") or 0) == 0, bare

    # Exercise the real global Core composition without provider-specific routes
    # or external network dependence. This catches a common Core tail that is
    # syntactically valid but throws at runtime for every reconstructed provider.
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    config.setdefault("provider_patches", {})["synthetic-clean-worker"] = {}
    config.setdefault("provider_capabilities", {})["synthetic-clean-worker"] = {
        "strategy": "unknown",
        "catalogue_types": ["movie"],
    }
    config_path = root / "provider-overrides.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with_core, _applied = apply_overrides(
        "synthetic-clean-worker",
        bundle,
        phase="discovery",
        include_global_core=True,
        config_path=config_path,
    )
    provider.write_bytes(with_core)
    core = run_worker(provider)
    assert core.get("ok") is True, (
        "clean ProviderBase + global Core is runtime-invalid: "
        + json.dumps(core.get("error_details") or {"error": core.get("error")}, ensure_ascii=False)
    )
    assert int(core.get("stream_count") or 0) == 0, core

print("clean ProviderBase real-worker smoke test passed (bare + global Core)")
