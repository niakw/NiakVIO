#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_base_store as base_store

provider_base_path = ROOT / "scripts" / "provider_base_store.py"
before_v35 = provider_base_path.read_bytes()
subprocess.run([sys.executable, "scripts/upgrade_provider_route_media_binding_v35.py"], cwd=ROOT, check=True)
after_v35 = provider_base_path.read_bytes()
assert after_v35 == before_v35, "committed ProviderBase must already be at the V35 fixed point"
subprocess.run([sys.executable, "scripts/upgrade_provider_route_media_binding_v35.py"], cwd=ROOT, check=True)
assert provider_base_path.read_bytes() == after_v35, "V35 migration must be byte-idempotent"

model = base_store.build_provider_data_model(
    "typed-route-demo",
    {
        "id": "typed-route-demo",
        "name": "Typed Route Demo",
        "supportedTypes": ["movie", "tv", "anime"],
    },
    known_site="https://provider.example",
    provider_model={
        "strategy": "mixed_embed_resolver",
        "knownSite": "https://provider.example",
        "officialSite": "https://provider.example",
        "origins": ["https://provider.example"],
        "observedUrls": ["https://provider.example"],
        "routes": [
            "/play/movie/{tmdbId}",
            "/play/tv/{tmdbId}/{season}/{episode}",
            "/anime/{tmdbId}",
        ],
        "identityInput": {
            "mode": "tmdb_direct",
            "requiresTmdbBeforeRun": False,
            "requiredFields": ["tmdbId", "mediaType"],
        },
        "routeProofVersion": 0,
    },
)
assert model["routeProofVersion"] == 0
assert model["routes"] == [
    "/play/movie/{tmdbId}",
    "/play/tv/{tmdbId}/{season}/{episode}",
    "/anime/{tmdbId}",
]

base = base_store.build_clean_provider_seed("typed-route-demo")
bundle = base_store.compose_provider_bundle("typed-route-demo", base, model)

runner = r'''
const provider = require(process.argv[2]);
const calls = [];
function headers(type) {
  return { get: (key) => String(key).toLowerCase() === "content-type" ? type : "" };
}
function page(url) {
  if (url.includes("/play/movie/603")) return '<a href="https://media.example/movie.mp4">movie</a>';
  if (url.includes("/play/tv/60059/1/1")) return '<a href="https://media.example/tv.mp4">tv</a>';
  if (url.includes("/anime/37854")) return '<a href="https://media.example/anime.mp4">anime</a>';
  return "<html><body>empty</body></html>";
}
global.fetch = async (url) => {
  const u = String(url);
  calls.push(u);
  if (u.startsWith("https://provider.example/")) {
    return {
      ok: true,
      status: 200,
      url: u,
      headers: headers("text/html"),
      text: async () => page(u),
      json: async () => ({})
    };
  }
  throw new Error("unexpected fetch " + u);
};

function assertOnly(label, slice, required, forbidden) {
  if (!slice.some(u => u.includes(required))) {
    throw new Error(label + " did not execute required route: " + JSON.stringify(slice));
  }
  for (const token of forbidden) {
    if (slice.some(u => u.includes(token))) {
      throw new Error(label + " crossed media route " + token + ": " + JSON.stringify(slice));
    }
  }
}

(async () => {
  let start = calls.length;
  const movie = await provider.getStreams("603", "movie");
  const movieCalls = calls.slice(start);
  if (!movie.length) throw new Error("movie route returned no stream: " + JSON.stringify(movieCalls));
  assertOnly("movie", movieCalls, "/play/movie/603", ["/play/tv/", "/anime/603"]);

  start = calls.length;
  const tv = await provider.getStreams("60059", "tv", 1, 1);
  const tvCalls = calls.slice(start);
  if (!tv.length) throw new Error("tv route returned no stream: " + JSON.stringify(tvCalls));
  assertOnly("tv", tvCalls, "/play/tv/60059/1/1", ["/play/movie/", "/anime/60059"]);

  start = calls.length;
  const anime = await provider.getStreams("37854", "anime", 1, 1);
  const animeCalls = calls.slice(start);
  if (!anime.length) throw new Error("anime route returned no stream: " + JSON.stringify(animeCalls));
  assertOnly("anime", animeCalls, "/anime/37854", ["/play/movie/", "/play/tv/"]);

  console.log("PROVIDER_ROUTE_MEDIA_BINDING_V35_RUNTIME_OK movie=" + movieCalls.join(",") + " tv=" + tvCalls.join(",") + " anime=" + animeCalls.join(","));
})().catch(error => {
  console.error(error && error.stack || error);
  process.exit(1);
});
'''

with tempfile.TemporaryDirectory(prefix="niakvio-route-media-v35-") as td:
    root = Path(td)
    provider = root / "provider.js"
    test = root / "test.js"
    provider.write_bytes(bundle)
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=30)

source = (ROOT / "scripts/provider_base_store.py").read_text(encoding="utf-8")
assert source.count("NIAKVIO_PROVIDER_ROUTE_MEDIA_BINDING_V35") == 1
assert 'if (!_spv34RouteMediaCompatible(route, mediaType)) continue;' in source
assert 'if (kind === "api" && !_spv34RouteMediaCompatible(route, mediaType)) continue;' not in source
assert 'function _directPlayerUrls(tmdbId, mediaType, season, episode) {' in source
assert 'const out = _learnedUrls(' in source
assert '"player",' in source
assert 'const known = _directPlayerUrls(tmdbId, mediaType, season, episode).slice(0, 2);' in source
assert '..._directPlayerUrls(meta.tmdbId, mediaType, season, episode)' in source

migration = (ROOT / "scripts/upgrade_provider_route_media_binding_v35.py").read_text(encoding="utf-8")
assert "NIAKVIO_PROVIDER_ROUTE_MEDIA_BINDING_V35" in migration
materializer = (ROOT / "scripts/materialize_provider_base_v3_store.py").read_text(encoding="utf-8")
assert "upgrade_provider_route_media_binding_v35.py" in materializer

print("ProviderBase V35 typed route execution contract passed")
