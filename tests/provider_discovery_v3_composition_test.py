#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_candidates as discovery  # noqa: E402
from provider_base_store import build_clean_provider_seed  # noqa: E402

entry = {
    "id": "synthetic-discovery",
    "name": "Synthetic Discovery",
    "supportedTypes": ["movie"],
    "canonicalSupportedTypes": ["movie"],
}
model = {
    "strategy": "html_scraper",
    "knownSite": None,
    "officialSite": None,
    "officialHub": None,
    "officialApi": None,
    "fixedApi": None,
    "origins": [],
    "observedUrls": [],
    "routes": [],
    "apiRecipe": None,
    "routeProofVersion": 0,
    "identityInput": {
        "mode": "tmdb_direct",
        "requiresTmdbBeforeRun": False,
        "requiredFields": ["tmdbId", "mediaType"],
    },
    "strictIdentity": False,
    "strictHtmlIdentity": False,
}
seed = build_clean_provider_seed("synthetic-discovery")
seed_text = seed.decode("utf-8")
assert "NIAKVIO_PROVIDER_BASE_OWNED_V3" in seed_text
assert "const NIAKVIO_PROVIDER_MODEL = Object.freeze(" not in seed_text

bundle = discovery.compose_executable_seed(
    "synthetic-discovery",
    entry,
    seed,
    None,
    model,
    {"provider_patches": {}},
)
text = bundle.decode("utf-8")
assert text.count("/* BEGIN NIAKVIO_PROVIDER */") == 1, text[:500]
assert text.count("/* END NIAKVIO_PROVIDER */") == 1, text[-500:]
assert text.count("const NIAKVIO_PROVIDER_MODEL = Object.freeze(") == 1
assert '"providerId":"synthetic-discovery"' in text
assert "PROVIDER.SYNTHETIC-DISCOVERY.CONFIG.V1" in text

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
with tempfile.TemporaryDirectory(prefix="niakvio-discovery-v3-") as tmp:
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
    "composed discovery v3 candidate emitted no worker result; "
    f"exit={completed.returncode} stderr={completed.stderr[-2000:]}"
)
result = json.loads(rows[-1])
assert result.get("ok") is True, (
    "discovery staged a runtime-invalid Provider v3 candidate: "
    + json.dumps(result.get("error_details") or {"error": result.get("error")}, ensure_ascii=False)
)
assert int(result.get("stream_count") or 0) == 0, result

print("Provider v3 discovery DATA composition real-worker contract passed")
