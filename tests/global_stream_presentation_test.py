#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "scripts" / "provider_patches"
CONTRACT = ROOT / "automation" / "native-stream-presentation-contract.json"
FUSION = ROOT / "assets" / "stream-badges-fusion.json"
RAW_PREFIX = "https://raw.githubusercontent.com/niakw/NiakVIO/main/"


def load(name: str):
    path = PATCHES / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalizer_path = ROOT / "scripts" / "normalize_stream_presentation_v12.py"
spec = importlib.util.spec_from_file_location("normalize_stream_presentation_v12", normalizer_path)
assert spec and spec.loader
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
normalizer.normalize(apply=True)
normalizer.assert_contract()

presentation = load("global_stream_presentation_v1.py")


def run(source: str, provider_id: str, fetch_impl: str, call: str) -> object:
    patched = presentation.apply(source, context={"provider_id": provider_id})
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in patched
    assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in patched
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
    assert "all-providers-client-projected-badge-emoji-tmdb-v12" in patched
    assert patched == presentation.apply(patched, context={"provider_id": provider_id})
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(patched, encoding="utf-8")
        runner.write_text(
            "global.fetch=" + fetch_impl + ";\n"
            "const p=require(" + json.dumps(str(provider)) + ");\n"
            + call
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False, timeout=20)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


TMDB_OK = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('presentation must not fetch playback URLs');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,overview:'Des explorateurs traversent un trou de ver.',genres:[{name:'Science-fiction'},{name:'Drame'}],release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""
TMDB_OFFLINE = "async function(){throw new Error('tmdb offline')}"
CALL = "p.getStreams('157336','movie').then(v=>console.log(JSON.stringify(v[0])))"

# Rich provider-owned layout is input-only. V12 extracts facts, rebuilds the visible
# presentation and mirrors it into size because all three official clients preserve it.
legacy = """module.exports={getStreams:async()=>[{name:'Purstream | provider-private',title:'🔥 PRIVATE TITLE',description:'🔥 provider private layout | 4K Dual-Audio HEVC E-AC3 5.1 BLU-RAY 169 min',size:'8.4 GB',url:'https://media.example/master.m3u8',quality:'4K',language:'Dual Audio',codec:'HEVC',audio:'E-AC3 5.1',sourceType:'BLU-RAY',headers:{Referer:'https://purstream.example/'}}]};\n"""
row = run(legacy, "purstream", TMDB_OK, CALL)
assert row["url"] == "https://media.example/master.m3u8"
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert row["quality"] == "", row
assert row["language"] == "", row
assert row["presentationFacts"]["quality"] == "2160p"
assert row["presentationFacts"]["language"] == "Dual Audio"
assert row["presentationFacts"]["codec"] == "HEVC"
assert row["presentationFacts"]["audioCodec"] == "E-AC3"
assert row["presentationFacts"]["audioChannels"] == "5.1"
assert row["presentationFacts"]["duration"] == 169
assert row["presentationFacts"]["sourceType"] == "BLU-RAY"
assert row["presentationFacts"]["fileSize"] == "8.4 GB"
assert row["fileSize"] == "8.4 GB"
assert row["description"] == row["size"] == row["nuvioPresentation"]
assert "provider private layout" not in row["description"]
assert "PRIVATE TITLE" not in row["description"]
assert "Unknown" not in row["description"]
for expected in (
    "🎬 Interstellar • 2014 • Science-fiction, Drame",
    "🎞️ 2160p • BLU-RAY • HEVC • HLS",
    "🔊 E-AC3 • 5.1",
    "🌐 Dual Audio",
    "⏱ 2h49",
    "💾 8.4 GB",
    "🔞 -12",
):
    assert expected in row["description"], (expected, row)
for badge_id in ("4k-ultra-hd", "blu-ray-disc", "hevc", "dolby-digital-plus", "5.1", "multi"):
    assert badge_id in row["badgeIds"], (badge_id, row)

# Sparse Purstream is no longer reduced to "Dual Audio". Even with TMDB offline the
# direct-media format is a Core fact, so the common technical grammar remains visible.
sparse = """module.exports={getStreams:async()=>[{name:'Purstream',url:'https://media.example/sparse.m3u8',sourceLabel:'Dual Audio'}]};\n"""
sparse_row = run(sparse, "purstream", TMDB_OFFLINE, CALL)
assert sparse_row["description"] == sparse_row["size"]
assert "🎞️ HLS" in sparse_row["description"], sparse_row
assert "🌐 Dual Audio" in sparse_row["description"], sparse_row
assert sparse_row["description"].strip() != "Dual Audio"

# Provider-specific formatting/emojis must never alter the canonical presentation.
# These three fixtures deliberately expose the same facts through different legacy
# layouts/field aliases, matching the concrete providers reported in native UI.
sources = {
    "purstream": """module.exports={getStreams:async()=>[{name:'💧 Purstream',url:'https://media.example/a.m3u8',quality:'4K',language:'Dual Audio',codec:'HEVC',audio:'E-AC3 5.1',sourceType:'BLU-RAY',description:'💧 old Purstream layout'}]};\n""",
    "vegamovies": """module.exports={getStreams:async()=>[{name:'⭐ VegaMovies',url:'https://media.example/a.m3u8',resolution:'2160p',lang:'Dual Audio',videoCodec:'HEVC',audioCodec:'E-AC3 5.1',source_type:'BLU-RAY',description:'⭐ VEGAMOVIES PRIVATE UI'}]};\n""",
    "hindmoviez": """module.exports={getStreams:async()=>[{name:'🇮🇳 HindMoviez',url:'https://media.example/a.m3u8',sourceLabel:'2160p Dual Audio HEVC E-AC3 5.1 BLU-RAY',description:'🇮🇳 HINDMOVIEZ PRIVATE UI'}]};\n""",
}
projected: dict[str, dict[str, str]] = {}
canonical: str | None = None
for provider_id, source in sources.items():
    candidate = run(source, provider_id, TMDB_OK, CALL)
    visible = candidate["size"]
    assert candidate["description"] == visible
    assert candidate["quality"] == ""
    assert candidate["language"] == ""
    assert "PRIVATE UI" not in visible and "old Purstream layout" not in visible
    assert "💧" not in visible and "⭐" not in visible and "🇮🇳" not in visible
    if canonical is None:
        canonical = visible
    else:
        assert visible == canonical, (provider_id, visible, canonical)

    # Exact official-client compatibility projections documented from source:
    # Mobile/Desktop => non-empty quality + size + language; TV => size.
    mobile_desktop = " • ".join(
        value for value in (candidate.get("quality", ""), candidate.get("size", ""), candidate.get("language", ""))
        if value
    )
    tv = candidate.get("size", "")
    projected[provider_id] = {"mobileDesktop": mobile_desktop, "tv": tv}
    assert mobile_desktop == visible
    assert tv == visible

assert len({value["mobileDesktop"] for value in projected.values()}) == 1, projected
assert len({value["tv"] for value in projected.values()}) == 1, projected

# The machine-readable contract must describe the exact compatibility transport above.
contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert contract["revision"] == "global_core_v12"
assert contract["canonical"]["compatibility_envelope_field"] == "size"
assert contract["canonical"]["suppressed_legacy_recomposition_fields"] == ["quality", "language"]
assert contract["badges"]["requires_nuvio_rule_import"] is True
for client in ("nuvio-mobile", "nuvio-desktop", "nuvio-tv"):
    assert client in contract["clients"]

# Badge rules must be executable regexes against the canonical transport, and every
# image URL must resolve to a committed asset path. This catches the historical
# double-escaping bug where Nuvio received a literal "\\b" instead of a word boundary.
feed = json.loads(FUSION.read_text(encoding="utf-8"))
feed_by_id = {str(item.get("id") or ""): item for item in feed.get("filters") or []}
assert feed_by_id
for badge_id in ("4k-ultra-hd", "blu-ray-disc", "hevc", "dolby-digital-plus", "5.1", "multi"):
    item = feed_by_id[badge_id]
    pattern = str(item["pattern"])
    assert "\\\\" not in pattern, (badge_id, repr(pattern))
    assert re.search(pattern, canonical or ""), (badge_id, pattern, canonical)
    image_url = str(item["imageURL"])
    assert image_url.startswith(RAW_PREFIX), (badge_id, image_url)
    image_path = ROOT / image_url.removeprefix(RAW_PREFIX)
    assert image_path.is_file() and image_path.stat().st_size > 0, (badge_id, image_path)

print(
    "global stream presentation V12 passed: "
    "provider_projection=purstream+vegamovies+hindmoviez "
    "clients=mobile+desktop+tv badge_regexes=executable"
)
