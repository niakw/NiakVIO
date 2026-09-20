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

with tempfile.TemporaryDirectory(prefix="niakvio-clean-worker-") as tmp:
    provider = Path(tmp) / "provider.js"
    provider.write_bytes(bundle)
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
result = json.loads(rows[-1])
assert result.get("ok") is True, (
    "clean ProviderBase is syntax-valid but runtime-invalid: "
    + json.dumps(result.get("error_details") or {"error": result.get("error")}, ensure_ascii=False)
)
assert int(result.get("stream_count") or 0) == 0, result
print("clean ProviderBase real-worker smoke test passed")
