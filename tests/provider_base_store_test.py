#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "provider_base_store.py"
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("provider_base_store", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = b"module.exports={getStreams:async()=>[]};\n"
digest = module.sha256(data)
relative = module.base_relative("Stream Zo", digest)
assert relative.startswith("provider-bases/stream-zo--base--"), relative
assert relative.endswith(".js"), relative
assert module.safe_base_path(relative) == (ROOT / relative).resolve()
assert module.safe_base_path("../providers/escape.js") is None
assert module.safe_base_path("providers/not-a-base.js") is None

clean = module.build_clean_provider_seed(
    "synthetic",
    {"name": "Synthetic", "supportedTypes": ["movie", "tv"]},
    known_site="https://example.invalid",
    provider_model={
        "strategy": "html_scraper",
        "officialSite": "https://example.invalid",
        "origins": ["https://example.invalid"],
        "routes": ["/search", "/watch"],
        "observedUrls": ["https://example.invalid/search"],
    },
)
text = clean.decode("utf-8")
assert "NIAKVIO_PROVIDER_BASE_OWNED_V3" in text
assert module.PROVIDER_BASE_OWNED_MARKER == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert module.CLEAN_RECONSTRUCTION_AUTHORING_VERSION >= 3
assert module.CLEAN_RECONSTRUCTION_SOURCE == "niakvio-clean-reconstruction-v3"
assert "upstreamCodeEmbedded" in text
assert '"upstreamCodeEmbedded":false' in text
assert '"upstreamCodeExecuted":false' in text
assert "async function getStreams" in text
assert "function _playerLike" in text
assert "async function _crawlDirectMedia" in text
assert "function _runtimeApiUrls" in text
assert "function _directPlayerUrls" in text
assert "function _mediaNamespace(mediaType)" in text
assert "const desiredMedia = _mediaNamespace(mediaType);" in text
assert 'url.searchParams.set("m", transportType)' in text
assert "function _sourceUrls" in text
assert "async function _resolveRuntimeApi" in text
assert "const discoveredNested = _uniq(urls.filter(_playerLike));" in text
assert "const crawled = await _crawlDirectMedia(" in text
assert text.index("const runtime = await _resolveRuntimeApi(") < text.index("const crawled = await _crawlDirectMedia(")
assert '(!meta.title && !meta.tmdbId)' in text
assert 'tmdbId: String(tmdbId || "")' in text
assert "requests < 4" in text
assert "slice(0, 24)" not in text
assert "function _detailGuesses" not in text
assert "if (!_runtimePlanAvailable()) return [];" in text
assert "NIAKVIO_PROVIDER_MODEL.observedUrls || []" not in text
assert "function _apiBases()" in text
assert 'const bases = kind === "api" ? _apiBases() : _searchBases();' in text
assert '!(type === "movie" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime"))' not in text

dirty_model = module.build_provider_data_model(
    "synthetic",
    {"name": "Synthetic", "supportedTypes": ["anime"]},
    known_site="https://example.invalid",
    provider_model={
        "strategy": "html_scraper",
        "officialSite": "https://example.invalid",
        "origins": ["https://example.invalid", "https://npms.io", "https://lodash.com"],
        "observedUrls": [
            "https://example.invalid/watch",
            "https://sendvid.com/embed/${token}",
            "https://openjsf.org/",
        ],
        "routes": ["/?s={query}", "/embed/${token}", "/search?q=ponyfill", "/license"],
    },
)
assert dirty_model["origins"] == ["https://example.invalid"]
assert dirty_model["observedUrls"] == ["https://example.invalid/watch"]
assert dirty_model["routes"] == ["/?s={query}"]
module.assert_base_layering(clean, "synthetic-clean")
with tempfile.NamedTemporaryFile(suffix=".js") as handle:
    handle.write(clean)
    handle.flush()
    subprocess.run(["node", "--check", handle.name], check=True)
module.validate_base(clean, "synthetic-clean")

print("ProviderBase store unit tests passed")
