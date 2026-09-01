#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
DISCOVER_PATH = ROOT / "scripts" / "discover_candidates.py"
BASE_STORE_PATH = ROOT / "scripts" / "provider_base_store.py"
MEDIA_PATCH_PATH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


discover = load_module("discover_candidates_purstream_regression", DISCOVER_PATH)
base_store = load_module("provider_base_store_purstream_regression", BASE_STORE_PATH)
media_patch = load_module("global_media_type_resolution_purstream_regression", MEDIA_PATCH_PATH)

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
patch = overrides["provider_patches"]["purstream"]
capability = overrides["provider_capabilities"]["purstream"]
expected_site = str(patch.get("official_site") or "")
expected_api = str(patch.get("official_api") or "")
assert expected_site and expected_api
expected_site_host = discover.urllib.parse.urlparse(expected_site).hostname
expected_api_host = discover.urllib.parse.urlparse(expected_api).hostname

# Deliberately polluted historical knowledge reproduces the old candidate that
# contained stale/incomplete hosts. Corrective reconstruction may learn static
# route facts from LKG, but the clean model must keep only trusted Purstream
# origins and the durable declarative API recipe.
knowledge = {
    "hosts": [
        "purstream.id",
        "api.purstream.id",
        "api.purstream",
        "old.invalid",
        "raw.githubu",
    ],
    "routes": ["/", "/search-bar/search/{query}"],
    "observedUrls": [
        "https://api.purstream.id/api/v1",
        "https://old.invalid/x",
        "https://raw.githubu/x",
    ],
    "routeFragments": [],
}
model = discover.clean_provider_model(
    "purstream",
    knowledge,
    overrides,
    expected_site,
)
origin_hosts = {
    discover.urllib.parse.urlparse(value).hostname
    for value in model.get("origins") or []
}
observed_hosts = {
    discover.urllib.parse.urlparse(value).hostname
    for value in model.get("observedUrls") or []
}
assert model["apiRecipe"]["base"] == expected_api
assert model["apiRecipe"]["searchRoute"] == "/search-bar/search/{query}"
assert model["apiRecipe"]["movieRoute"] == "/media/{id}/sheet"
assert model["apiRecipe"]["episodeRoute"] == "/stream/{id}/episode?season={season}&episode={episode}"
assert model["apiRecipe"]["strictIdentity"] is True
assert model["apiRecipe"]["directSourcesOnly"] is True
assert expected_api_host in origin_hosts
assert expected_site_host in origin_hosts
assert origin_hosts.isdisjoint({"api.purstream", "old.invalid", "raw.githubu"})
assert observed_hosts.isdisjoint({"api.purstream", "old.invalid", "raw.githubu"})

entry = {
    "id": "purstream",
    "name": "Purstream",
    "supportedTypes": ["movie", "tv"],
}
reconstructed_entry = discover.reconstruction_manifest_entry(
    "purstream",
    entry,
    overrides,
)
assert reconstructed_entry["canonicalSupportedTypes"] == ["movie", "tv", "anime"]

seed = base_store.build_clean_provider_seed(
    "purstream",
    reconstructed_entry,
    known_site=expected_site,
    provider_model=model,
).decode("utf-8")
assert '"supportedTypes":["movie","tv","anime"]' in seed
assert '"routePlanVersion":2' in seed
assert '"modelSchemaVersion":3' in seed
assert "api.themoviedb.org" not in seed
assert "TMDB_API_KEY" not in seed
assert "old.invalid" not in seed
assert "raw.githubu" not in seed

bundle = media_patch.apply(
    seed,
    options={
        "semantic_types": ["movie", "tv", "anime"],
        "request_type_aliases": capability["request_type_aliases"],
        "provider_timeout_ms": 25_000,
    },
)

runner = r"""
const providerPath = process.argv[2];
const calls = [];
const tmdbCalls = [];

function jsonResponse(url, value) {
  return {
    ok: true,
    status: 200,
    url,
    headers: { get: (name) => String(name).toLowerCase() === "content-type" ? "application/json" : null },
    json: async () => value,
    text: async () => JSON.stringify(value)
  };
}

global.fetch = async function(rawUrl) {
  const url = String(rawUrl);
  calls.push(url);

  if (url.includes("api.themoviedb.org/3/movie/157336")) {
    tmdbCalls.push(url);
    return jsonResponse(url, {
      id: 157336,
      title: "Interstellar FR",
      original_title: "Interstellar",
      release_date: "2014-11-05",
      genres: [{id: 18, name: "Drama"}],
      original_language: "en",
      production_countries: [{iso_3166_1: "US"}],
      keywords: {keywords: []}
    });
  }
  if (url.includes("api.themoviedb.org/3/tv/1396")) {
    tmdbCalls.push(url);
    return jsonResponse(url, {
      id: 1396,
      name: "Breaking Bad",
      first_air_date: "2008-01-20",
      genres: [{id: 18, name: "Drama"}],
      original_language: "en",
      origin_country: ["US"],
      keywords: {results: []}
    });
  }
  if (url.includes("api.themoviedb.org/3/tv/95479")) {
    tmdbCalls.push(url);
    return jsonResponse(url, {
      id: 95479,
      name: "Jujutsu Kaisen",
      first_air_date: "2020-10-03",
      genres: [{id: 16, name: "Animation"}],
      original_language: "ja",
      origin_country: ["JP"],
      keywords: {results: [{name: "anime"}]}
    });
  }

  if (url.includes("/search-bar/search/Interstellar%20FR")) {
    return jsonResponse(url, {data:{items:{movies:{items:[]}}}});
  }
  if (url.includes("/search-bar/search/Interstellar")) {
    return jsonResponse(url, {data:{items:{
      movies:{items:[
        {id:"wrong-movie",title:"Interstellar Something Else",release_date:"2014-01-01"},
        {id:"p-movie",title:"Interstellar",release_date:"2014-11-05"}
      ]}
    }}});
  }
  if (url.includes("/search-bar/search/Breaking%20Bad")) {
    // Collision is intentionally split across independent API collections and
    // neither item carries an explicit type field. The clean resolver must retain
    // the collection identity instead of falling back to the first title match.
    return jsonResponse(url, {data:{items:{
      movies:{items:[
        {id:"wrong-tv",title:"Breaking Bad",release_date:"2008-01-01"}
      ]},
      series:{items:[
        {id:"p-tv",title:"Breaking Bad",first_air_date:"2008-01-20"}
      ]}
    }}});
  }
  if (url.includes("/search-bar/search/Jujutsu%20Kaisen")) {
    // Purstream historically exposes anime inside its anime catalogue collection,
    // while the episodic transport itself remains TV.
    return jsonResponse(url, {data:{items:{
      anime:{items:[
        {id:"p-anime",title:"Jujutsu Kaisen",first_air_date:"2020-10-03"}
      ]}
    }}});
  }

  if (url.includes("/media/p-movie/sheet")) {
    return jsonResponse(url, {
      urls: [
        {url:"https://embed.example/watch/p-movie"},
        {url:"https://free.finepulfe.xyz/movies/157336-test/master.m3u8"}
      ]
    });
  }
  if (url.includes("/stream/p-tv/episode?season=1&episode=1")) {
    return jsonResponse(url, {
      sources:[
        {stream_url:"https://embed.example/watch/p-tv"},
        {stream_url:"https://free.finepulfe.xyz/tv/1396-test/S01/E01/master.m3u8"}
      ]
    });
  }
  if (url.includes("/stream/p-anime/episode?season=1&episode=1")) {
    return jsonResponse(url, {
      sources:[
        {stream_url:"https://embed.example/watch/p-anime"},
        {stream_url:"https://free.finepulfe.xyz/animes/tv/p-anime/S1/E1/master.m3u8"}
      ]
    });
  }

  throw new Error("unexpected URL: " + url);
};

const provider = require(providerPath);

(async () => {
  const movie = await provider.getStreams("157336", "movie");
  if (!movie.length || !movie[0].url.includes("/movies/157336-test/") || movie.some(row => row.url.includes("embed.example"))) {
    throw new Error("Purstream movie route/direct-source regression: " + JSON.stringify(movie));
  }

  const series = await provider.getStreams("1396", "series", 1, 1);
  if (!series.length || !series[0].url.includes("/tv/1396-test/S01/E01/") || series.some(row => row.url.includes("embed.example"))) {
    throw new Error("Purstream series->tv route/direct-source regression: " + JSON.stringify(series));
  }

  // This is the key historical regression: Nuvio can describe an anime episode
  // as "series". Core must classify it as anime from TMDB, preserve that semantic
  // identity, then pass Purstream the TV transport expected by its episodic API.
  const animeFromSeries = await provider.getStreams("95479", "series", 1, 1);
  if (!animeFromSeries.length || !animeFromSeries[0].url.includes("/animes/tv/p-anime/S1/E1/")) {
    throw new Error("Purstream Nuvio-series anime regression: " + JSON.stringify(animeFromSeries));
  }

  const animeExplicit = await provider.getStreams("95479", "anime", 1, 1);
  if (!animeExplicit.length || !animeExplicit[0].url.includes("/animes/tv/p-anime/S1/E1/")) {
    throw new Error("Purstream explicit anime regression: " + JSON.stringify(animeExplicit));
  }

  const badAnimeTransport = calls.filter(url =>
    url.includes("api.purstream.id") && /(?:[?&](?:type|media)=anime\b|\/anime(?:[/?#]|$))/.test(url)
  );
  if (badAnimeTransport.length) {
    throw new Error("Purstream received semantic anime instead of TV transport: " + badAnimeTransport.join("\n"));
  }

  const tmdb95479 = tmdbCalls.filter(url => url.includes("/tv/95479"));
  if (tmdb95479.length !== 1) {
    throw new Error("TMDB anime identity should be cached across series/anime aliases, calls=" + tmdb95479.length);
  }

  console.log("Purstream regression passed: movie + series + Nuvio-series anime + explicit anime");
})().catch(error => {
  console.error(error);
  process.exit(1);
});
"""

with tempfile.TemporaryDirectory(prefix="purstream-semantic-transport-") as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "purstream.cjs"
    test_file = tmp_path / "runner.cjs"
    provider.write_text(bundle, encoding="utf-8")
    test_file.write_text(runner, encoding="utf-8")
    result = subprocess.run(
        ["node", str(test_file), str(provider)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Purstream regression passed" in result.stdout

print(
    "Purstream semantic/transport regression passed: "
    "historical movie+series+anime capability preserved through clean ProviderBase v2"
)
