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
assert "NIAKVIO_PROVIDER_BASE_OWNED_V2" in text
assert "upstreamCodeEmbedded" in text
assert '"upstreamCodeEmbedded":false' in text
assert '"upstreamCodeExecuted":false' in text
assert "async function getStreams" in text
assert "function _playerLike" in text
assert "async function _crawlDirectMedia" in text
assert "function _runtimeApiUrls" in text
assert "function _sourceUrls" in text
assert "async function _resolveRuntimeApi" in text
assert "requests < 12" in text
module.assert_base_layering(clean, "synthetic-clean")
with tempfile.NamedTemporaryFile(suffix=".js") as handle:
    handle.write(clean)
    handle.flush()
    subprocess.run(["node", "--check", handle.name], check=True)
module.validate_base(clean, "synthetic-clean")

print("ProviderBase store unit tests passed")
