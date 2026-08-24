#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "scripts" / "provider_patches"


def load(name: str):
    path = PATCHES / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Materialize the durable Core contract before loading the patch. This mirrors the
# Core finalizer and keeps the test valid on a fresh checkout of the V11 control plane.
normalizer_path = ROOT / "scripts" / "normalize_stream_presentation_v11.py"
spec = importlib.util.spec_from_file_location("normalize_stream_presentation_v11", normalizer_path)
assert spec and spec.loader
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
normalizer.normalize(apply=True)
normalizer.assert_contract()

facts = load("global_stream_facts_v1.py")
presentation = load("global_stream_presentation_v1.py")

legacy = """module.exports={getStreams:async()=>[{name:'Purstream | 4k | Dual-Audio',title:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',size:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',description:'🎬 Interstellar - 2014\\n🔥 4k | 🔊 Dual-Audio\\n🎯 HLS • HEVC | 🎧 AAC • 169 min • BLU-RAY',url:'https://media.example/master.m3u8',quality:'',language:'',format:'m3u8',headers:{Referer:'https://purstream.example/'}}]};\n"""
with_facts = facts.apply(legacy, context={"provider_id": "purstream"})
assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in with_facts
patched = presentation.apply(with_facts, context={"provider_id": "purstream"})
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in patched
assert "all-providers-forced-description-badge-emoji-tmdb-v11" in patched
assert patched == presentation.apply(patched, context={"provider_id": "purstream"})


def run(source: str, fetch_impl: str, call: str) -> object:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            "global.fetch=" + fetch_impl + ";\n"
            "const p=require(" + json.dumps(str(provider)) + ");\n"
            + call
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False, timeout=15)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


tmdb_ok = r"""async function(url){
  if(!String(url).includes('api.themoviedb.org')) throw new Error('presentation must not fetch playback URLs');
  return {ok:true,status:200,json:async()=>({id:157336,title:'Interstellar',release_date:'2014-11-05',runtime:169,overview:'Des explorateurs traversent un trou de ver pour chercher un nouveau foyer pour l’humanité.',genres:[{name:'Science-fiction'},{name:'Drame'}],release_dates:{results:[{iso_3166_1:'FR',release_dates:[{certification:'-12'}]}]}})};
}"""
row = run(
    patched,
    tmdb_ok,
    "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert row["url"] == "https://media.example/master.m3u8"
assert row["headers"] == {"Referer": "https://purstream.example/"}
assert row["quality"] == "2160p", row
assert row["language"] == "Dual Audio", row
assert row["codec"] == "HEVC", row
assert row["audio"] == "AAC", row
assert row["duration"] == 169, row
assert row["sourceType"] == "BLU-RAY", row
assert row["ageRating"] == "-12", row
assert row["title"] == "Purstream • Interstellar", row
assert "size" not in row, row
assert row["badgeIds"][:2] == ["4k-ultra-hd", "blu-ray-disc"], row
assert "hevc" in row["badgeIds"], row
assert "4K" in row["displayBadges"], row
assert "HEVC" in row["displayBadges"], row
assert row["presentationFacts"]["quality"] == "2160p"
assert row["presentationFacts"]["format"] == "HLS"
assert "Interstellar • 2014 • Science-fiction, Drame" in row["description"], row
assert "Unknown" not in row["description"]
for expected in (
    "🎞️ ", "2160p", "BLU-RAY", "HEVC", "HLS",
    "🔊 AAC", "🌐 Dual Audio", "⏱ 2h49", "🔞 -12",
):
    assert expected in row["description"], (expected, row)

# Empty provider output must not start an optional TMDB request that can outlive
# the provider route and make native evidence look incomplete.
empty = "module.exports={getStreams:async()=>[]};\n"
empty_patched = presentation.apply(empty, context={"provider_id": "movieshunt"})
empty_result = run(
    empty_patched,
    "async function(){global.__tmdbCalls=(global.__tmdbCalls||0)+1;throw new Error('must not run')}",
    "p.getStreams({tmdbId:'1233413',mediaType:'movie',title:'Sinners',year:2025}).then(v=>console.log(JSON.stringify({streams:v,calls:global.__tmdbCalls||0})))",
)
assert empty_result == {"streams": [], "calls": 0}, empty_result

# Resolution alone never invents Blu-ray provenance. It remains visible in the
# emoji technical line and can independently match a native resolution badge.
plain = "module.exports={getStreams:async()=>[{name:'Cineby',url:'https://media.example/video.mp4',quality:'1080p'}]};\n"
plain_patched = presentation.apply(plain, context={"provider_id": "cineby"})
plain_row = run(
    plain_patched,
    "async function(){throw new Error('tmdb offline')}",
    "p.getStreams({mediaType:'movie',title:'Example',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert plain_row["quality"] == "1080p"
assert "sourceType" not in plain_row
assert plain_row["badgeIds"] == ["1080p-full-hd"], plain_row
assert "BLU-RAY" not in plain_row["description"]
assert "🎞️ 1080p" in plain_row["description"]
assert "MP4" in plain_row["description"]
assert "Example • 2026" in plain_row["description"]

# Metadata-poor reconstructed HLS keeps playback intact, derives HLS only from the
# actual URL and uses request/TMDB identity instead of leaking Unknown labels.
unknown = "module.exports={getStreams:async()=>[{name:'Movix',url:'https://media.example/u.m3u8',description:'Unknown',size:'Unknown',headers:{Origin:'https://movix.example'}}]};\n"
unknown_patched = presentation.apply(unknown, context={"provider_id": "movix"})
unknown_row = run(
    unknown_patched,
    "async function(){throw new Error('offline')}",
    "p.getStreams({tmdbId:'999',mediaType:'movie',title:'Fallback title',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert unknown_row["url"] == "https://media.example/u.m3u8"
assert unknown_row["headers"] == {"Origin": "https://movix.example"}
assert unknown_row["format"] == "HLS"
assert unknown_row["presentationFacts"]["format"] == "HLS"
assert "size" not in unknown_row
assert "Unknown" not in unknown_row["description"]
assert "Fallback title • 2026" in unknown_row["description"]
assert "🎞️ HLS" in unknown_row["description"]

# A true file size remains visible even if a client ignores the structured size key.
sized = "module.exports={getStreams:async()=>[{name:'Example',url:'https://media.example/video.mkv',size:'8.4 GB',quality:'720p'}]};\n"
sized_row = run(
    presentation.apply(sized, context={"provider_id": "example"}),
    "async function(){throw new Error('offline')}",
    "p.getStreams({mediaType:'movie',title:'Movie',year:2026}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert sized_row["size"] == "8.4 GB"
assert "720p-hd" in sized_row["badgeIds"]
assert "🎞️ 720p" in sized_row["description"]
assert "💾 8.4 GB" in sized_row["description"]

# Provider-owned UI layout is input-only. Core may read technical facts from it,
# but the original text itself must never survive into the rendered description.
garbage = "module.exports={getStreams:async()=>[{name:'AnyProvider',url:'https://media.example/master.m3u8',description:'Unknown | UNKNOWN | provider private layout',quality:'1080p',audio:'Dolby Atmos TrueHD 7.1',sourceType:'UHD Blu-ray',releaseType:'REMUX',language:'VFF',subtitles:'VOSTFR'}]};\n"
garbage_row = run(
    presentation.apply(garbage, context={"provider_id": "anyprovider"}),
    tmdb_ok,
    "p.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(v=>console.log(JSON.stringify(v[0])))",
)
assert "provider private layout" not in garbage_row["description"]
assert "Unknown" not in garbage_row["description"]
for expected in (
    "🎞️ 1080p", "ULTRA HD BLU-RAY REMUX",
    "🔊 Dolby Atmos • TrueHD • 7.1", "🌐 VFF • VOSTFR",
    "⏱ 2h49", "🔞 -12",
):
    assert expected in garbage_row["description"], (expected, garbage_row)
for badge_id in ("uhd-blu-ray", "remux", "dolby-atmos", "truehd", "7.1", "vff", "vostfr"):
    assert badge_id in garbage_row["badgeIds"], (badge_id, garbage_row)

print("global stream presentation + native-badge/emoji fallback contract tests passed")
