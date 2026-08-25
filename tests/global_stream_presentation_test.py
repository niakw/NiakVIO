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
CORE_REVISION = "all-providers-client-projected-quality-preserved-badge-emoji-tmdb-v12"


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


def run(source: str, provider_id: str, fetch_impl: str, call: str) -> dict:
    patched = presentation.apply(source, context={"provider_id": provider_id})
    assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in patched
    assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in patched
    assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
    assert CORE_REVISION in patched
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


def mobile_desktop_description(row: dict) -> str:
    return " • ".join(
        value for value in (row.get("quality", ""), row.get("size", ""), row.get("language", ""))
        if value
    )


def tv_title_and_description(row: dict) -> tuple[str, str]:
    # Mirrors LocalScraperResult.toStream(): name gets " - quality", description=size.
    base = str(row.get("name") or row.get("title") or "")
    quality = str(row.get("quality") or "")
    title = base if not quality or quality in base else f"{base} - {quality}"
    return title, str(row.get("size") or "")


TMDB_OK = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('presentation must not fetch playback URLs');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,overview:'Des explorateurs traversent un trou de ver.',genres:[{name:'Science-fiction'},{name:'Drame'}],release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""
TMDB_OFFLINE = "async function(){throw new Error('tmdb offline')}"
CALL = "p.getStreams('157336','movie').then(v=>console.log(JSON.stringify(v[0])))"

# Rich provider-owned layout is input-only. Quality is preserved because official
# clients use it in labels/sorting; language is carried inside the multiline envelope.
legacy = """module.exports={getStreams:async()=>[{name:'Purstream | provider-private',title:'🔥 PRIVATE TITLE',description:'🔥 provider private layout | 4K Dual-Audio HEVC E-AC3 5.1 BLU-RAY 169 min',size:'8.4 GB',url:'https://media.example/master.m3u8',quality:'4K',language:'Dual Audio',codec:'HEVC',audio:'E-AC3 5.1',sourceType:'BLU-RAY',headers:{Referer:'https://purstream.example/'}}]};\n"""
row = run(legacy, "purstream", TMDB_OK, CALL)
assert row["url"] == "https://media.example/master.m3u8"
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert row["quality"] == "2160p", row
assert "language" not in row, row
assert row["presentationFacts"]["quality"] == "2160p"
assert row["presentationFacts"]["language"] == "Multi"
assert row["presentationFacts"]["codec"] == "HEVC"
assert row["presentationFacts"]["audioCodec"] == "E-AC3"
assert row["presentationFacts"]["audioChannels"] == "5.1"
assert row["presentationFacts"]["duration"] == 169
assert row["presentationFacts"]["sourceType"] == "BLU-RAY"
assert row["presentationFacts"]["fileSize"] == "8.4 GB"
assert row["fileSize"] == "8.4 GB"
assert row["description"] == row["nuvioPresentation"]
assert row["size"] == row["nuvioCompatibilityEnvelope"]
assert row["description"] != row["size"]  # canonical contains quality; envelope does not.
assert "provider private layout" not in row["description"]
assert "PRIVATE TITLE" not in row["description"]
assert "Unknown" not in row["description"]
assert "2160p" in row["description"]
assert "2160p" not in row["size"]
for expected_line in (
    "🎬 Interstellar • 2014 • Science-fiction, Drame",
    "🎞️ BLU-RAY • HEVC • HLS",
    "🔊 E-AC3 • 5.1",
    "🌐 Multi",
):
    assert expected_line in row["size"].splitlines(), (expected_line, row)
assert "⏱ 2h49" in row["size"]
assert "💾 8.4 GB" in row["size"]
assert "🔞 -12" in row["size"]
assert len(row["size"].splitlines()) >= 5, row["size"]

mobile_visible = mobile_desktop_description(row)
assert mobile_visible.startswith("2160p • 🎬 Interstellar"), mobile_visible
assert mobile_visible.count("2160p") == 1
assert "\n🎞️ " in mobile_visible and "\n🔊 " in mobile_visible and "\n🌐 " in mobile_visible

tv_title, tv_description = tv_title_and_description(row)
assert tv_title.endswith(" - 2160p"), tv_title
assert "Unknown" not in tv_title
assert tv_description == row["size"]

for badge_id in ("4k-ultra-hd", "blu-ray-disc", "hevc", "dolby-digital-plus", "5.1", "multi"):
    assert badge_id in row["badgeIds"], (badge_id, row)

# Sparse Purstream must not collapse to a lone "Dual Audio" string.
sparse = """module.exports={getStreams:async()=>[{name:'Purstream',url:'https://media.example/sparse.m3u8',sourceLabel:'Dual Audio'}]};\n"""
sparse_row = run(sparse, "purstream", TMDB_OFFLINE, CALL)
assert "🎞️ HLS" in sparse_row["size"], sparse_row
assert "🌐 Multi" in sparse_row["size"], sparse_row
assert sparse_row["size"].strip() != "Dual Audio"
assert "language" not in sparse_row

# Equivalent facts coming from different provider layouts must render identically.
sources = {
    "purstream": """module.exports={getStreams:async()=>[{name:'💧 Purstream',url:'https://media.example/a.m3u8',quality:'4K',language:'Dual Audio',codec:'HEVC',audio:'E-AC3 5.1',sourceType:'BLU-RAY',description:'💧 old Purstream layout'}]};\n""",
    "vegamovies": """module.exports={getStreams:async()=>[{name:'⭐ VegaMovies',url:'https://media.example/a.m3u8',resolution:'2160p',lang:'Dual Audio',videoCodec:'HEVC',audioCodec:'E-AC3 5.1',source_type:'BLU-RAY',description:'⭐ VEGAMOVIES PRIVATE UI'}]};\n""",
    "hindmoviez": """module.exports={getStreams:async()=>[{name:'🇮🇳 HindMoviez',url:'https://media.example/a.m3u8',sourceLabel:'2160p Dual Audio HEVC E-AC3 5.1 BLU-RAY',description:'🇮🇳 HINDMOVIEZ PRIVATE UI'}]};\n""",
}
projected: dict[str, dict[str, str]] = {}
canonical_envelope: str | None = None
for provider_id, source in sources.items():
    candidate = run(source, provider_id, TMDB_OK, CALL)
    assert candidate["quality"] == "2160p"
    assert "language" not in candidate
    envelope = candidate["size"]
    assert "PRIVATE UI" not in envelope and "old Purstream layout" not in envelope
    assert "💧" not in envelope and "⭐" not in envelope and "🇮🇳" not in envelope
    if canonical_envelope is None:
        canonical_envelope = envelope
    else:
        assert envelope == canonical_envelope, (provider_id, envelope, canonical_envelope)
    mobile = mobile_desktop_description(candidate)
    tv_name, tv = tv_title_and_description(candidate)
    assert mobile.count("2160p") == 1
    assert tv_name.endswith(" - 2160p")
    projected[provider_id] = {"mobileDesktop": mobile, "tv": tv}

assert len({value["mobileDesktop"] for value in projected.values()}) == 1, projected
assert len({value["tv"] for value in projected.values()}) == 1, projected

# MoviesHunt-style provider size strings may contain a whole private layout. Only the
# actual file-size token is factual; no surrounding provider prose may survive.
movieshunt = """module.exports={getStreams:async()=>[{name:'MoviesHunt - PRIVATE',url:'https://media.example/movie.m3u8',quality:'1080p',language:'VFF',size:'🔥 1080p | WEB-DL | provider private description | 2.4 GB | click fast',description:'🔥 MOVIESHUNT PRIVATE DESCRIPTION',sourceLabel:'WEB-DL HEVC E-AC3 5.1'}]};\n"""
movieshunt_row = run(movieshunt, "movieshunt", TMDB_OK, CALL)
assert movieshunt_row["quality"] == "1080p"
assert movieshunt_row["fileSize"] == "2.4 GB"
assert "provider private" not in movieshunt_row["size"].lower()
assert "movieshunt private" not in movieshunt_row["size"].lower()
assert "click fast" not in movieshunt_row["size"].lower()
assert "💾 2.4 GB" in movieshunt_row["size"]
assert len(movieshunt_row["size"].splitlines()) >= 4

contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
assert contract["revision"] == "global_core_v12"
assert contract["canonical"]["compatibility_envelope_field"] == "size"
assert contract["canonical"]["preserved_legacy_fields"] == ["quality"]
assert contract["canonical"]["suppressed_legacy_recomposition_fields"] == ["language"]
assert contract["badges"]["requires_nuvio_rule_import"] is True
for client in ("nuvio-mobile", "nuvio-desktop", "nuvio-tv"):
    assert client in contract["clients"]

# Match exactly what official clients expose to StreamBadgeMatcher after parsing.
feed = json.loads(FUSION.read_text(encoding="utf-8"))
feed_by_id = {str(item.get("id") or ""): item for item in feed.get("filters") or []}
assert feed_by_id
match_surface = mobile_visible
for badge_id in ("4k-ultra-hd", "blu-ray-disc", "hevc", "dolby-digital-plus", "5.1", "multi"):
    item = feed_by_id[badge_id]
    pattern = str(item["pattern"])
    assert "\\\\" not in pattern, (badge_id, repr(pattern))
    re.compile(pattern)
    assert re.search(pattern, match_surface), (badge_id, pattern, match_surface)
    image_url = str(item["imageURL"])
    assert image_url.startswith(RAW_PREFIX), (badge_id, image_url)
    image_path = ROOT / image_url.removeprefix(RAW_PREFIX)
    assert image_path.is_file() and image_path.stat().st_size > 0, (badge_id, image_path)

print(
    "global stream presentation V12 passed: quality=preserved multiline=true "
    "provider_projection=purstream+vegamovies+hindmoviez+movieshunt "
    "clients=mobile+desktop+tv fusion_badges=matchable"
)
