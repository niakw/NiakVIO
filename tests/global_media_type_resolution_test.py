#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = r'''
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  return [{ tmdbId, mediaType, season, episode }];
}
module.exports = { getStreams };
'''
patched = mod.apply(base)
assert "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1" in patched
assert "TMDB_API_KEY" in patched
assert "TMDB_ACCESS_TOKEN" in patched
assert "series" in patched and "show" in patched and "other" in patched

runner = r'''
global.TMDB_API_KEY = "test-key";
global.fetch = async (url) => ({
  ok: true,
  json: async () => ({
    id: 46260,
    genres: [{id:16,name:"Animation"}],
    original_language: "ja",
    origin_country: ["JP"],
    keywords: {results:[{name:"anime"}]}
  })
});
const provider = require(process.argv[2]);
(async () => {
  const seriesAnime = await provider.getStreams("46260", "series", 1, 1);
  if (seriesAnime[0].mediaType !== "anime") throw new Error("series anime was not refined to anime");

  delete global.TMDB_API_KEY;
  const ordinarySeries = await provider.getStreams("1396", "series", 1, 1);
  if (ordinarySeries[0].mediaType !== "tv") throw new Error("series alias did not default to tv");

  const objectAnime = await provider.getStreams({
    tmdbId: "46260",
    mediaType: "series",
    category: "anime",
    season: 1,
    episode: 1
  });
  if (objectAnime[0].mediaType !== "anime") throw new Error("trusted anime category was lost");
})().catch((error) => { console.error(error); process.exit(1); });
'''
# Object-form validation needs a provider that accepts the object contract.
object_base = r'''
"use strict";
async function getStreams(arg) { return [arg]; }
module.exports = { getStreams };
'''
object_patched = mod.apply(object_base)

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.js"
    object_provider = tmp_path / "provider-object.js"
    test = tmp_path / "test.js"
    provider.write_text(patched, encoding="utf-8")
    object_provider.write_text(object_patched, encoding="utf-8")

    # positional tests
    positional_runner = runner.replace(
        "  const objectAnime = await provider.getStreams({\n"
        "    tmdbId: \"46260\",\n"
        "    mediaType: \"series\",\n"
        "    category: \"anime\",\n"
        "    season: 1,\n"
        "    episode: 1\n"
        "  });\n"
        "  if (objectAnime[0].mediaType !== \"anime\") throw new Error(\"trusted anime category was lost\");\n",
        ""
    )
    test.write_text(positional_runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

    object_runner = r'''
const provider = require(process.argv[2]);
(async () => {
  const value = await provider.getStreams({
    tmdbId: "46260",
    mediaType: "series",
    category: "anime",
    season: 1,
    episode: 1
  });
  if (value[0].mediaType !== "anime") throw new Error("trusted anime category was lost");
  if (value[0].nuvioInputMediaType !== "series") throw new Error("input alias evidence was lost");
})().catch((error) => { console.error(error); process.exit(1); });
'''
    test.write_text(object_runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(object_provider)], check=True)

print("global media-type resolver tests passed: series=>tv, proven TMDB anime=>anime")
