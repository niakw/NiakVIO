#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_target_media_v4.py"


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location("target_media_v4_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def encode_current_vidzy(url: str, hostname: str) -> str:
    host_key = sum(ord(ch) for ch in hostname) & 255
    plain = url.encode("latin1")
    reversed_encoded = bytes(
        value ^ ((0x3D + index * 89 + host_key) & 255)
        for index, value in enumerate(plain)
    )
    raw = reversed_encoded[::-1]
    return base64.b64encode(raw).decode("ascii")


def run_provider_test(apply, *, embed_url: str, media_url: str, html: str, options: dict, forbidden: list[str]) -> None:
    source = f'''module.exports={{getStreams:async function(){{return [{{name:"Fixture",title:"Fixture",url:{json.dumps(embed_url)},headers:{{Referer:"https://streamzo.fr/"}}}}]}}}};'''
    patched = apply(source, options=options)
    assert "function decodeVidzy(text,base)" in patched
    assert "function decodeLecteurVideo(text,base)" in patched
    assert "function genericUrls(text,base)" in patched
    assert "PLAYER_HOST" in patched

    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        target = Path(tmp) / "provider.cjs"
        target.write_text(patched, encoding="utf-8")
        subprocess.run(["node", "--check", str(target)], check=True)
        harness = r'''
const target = process.argv[1];
const embedUrl = process.argv[2];
const mediaUrl = process.argv[3];
const html = Buffer.from(process.argv[4], "base64").toString("utf8");
const forbidden = JSON.parse(process.argv[5]);
const requested = [];
class HeadersStub {
  constructor(values = {}) { this.values = values; }
  get(name) { return this.values[String(name).toLowerCase()] || null; }
}
function response(url, body, contentType) {
  const bytes = Buffer.from(body, "utf8");
  return {
    ok: true,
    status: 200,
    url,
    headers: new HeadersStub({"content-type": contentType}),
    arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    text: async () => body,
  };
}
global.fetch = async function(input) {
  const url = typeof input === "string" ? input : String(input && input.url || input);
  requested.push(url);
  if (url === embedUrl) return response(url, html, "text/html; charset=UTF-8");
  if (url === mediaUrl) return response(url, "#EXTM3U\n#EXT-X-VERSION:3\n#EXTINF:90,\nseg-1.ts\n#EXT-X-ENDLIST\n", "application/vnd.apple.mpegurl");
  if (forbidden.some((value) => url.includes(value))) return response(url, "\x00\x00\x00\x18ftypisom000000000000", "video/mp4");
  return {ok:false,status:404,url,headers:new HeadersStub(),arrayBuffer:async()=>new ArrayBuffer(0),text:async()=>""};
};
(async () => {
  const provider = require(target);
  const rows = await provider.getStreams("157336", "movie", null, null);
  process.stdout.write(JSON.stringify({rows, requested}));
})().catch((error) => {
  console.error(error && error.stack || error);
  process.exit(1);
});
'''
        result = subprocess.run(
            [
                "node",
                "-e",
                harness,
                str(target.resolve()),
                embed_url,
                media_url,
                base64.b64encode(html.encode()).decode(),
                json.dumps(forbidden),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        decoded = json.loads(result.stdout)
        rows = decoded["rows"]
        requested = decoded["requested"]
        assert len(rows) == 1, decoded
        assert rows[0]["url"] == media_url, decoded
        assert rows[0].get("isDirect") is True, decoded
        assert media_url in requested, decoded
        for value in forbidden:
            assert not any(value in url for url in requested), decoded


def run() -> None:
    apply = load_apply(PATCH)

    vidzy_embed = "https://vidzy.org/embed-fixture.html"
    vidzy_media = "https://u14.vidzy.cc/hls2/08/00029/fixture/master.m3u8?t=proof"
    fallback = "https://s1.fsvid.lol/troll/master.m3u8"
    payload = encode_current_vidzy(vidzy_media, "vidzy.org")
    vidzy_html = f'''<html><script>
var _fsvHls="{fallback}";
var player = videojs('vjsplayer', {{sources: [{{src: (function(s){{
var h=(location&&location.hostname)||"",H=0;
for(var j=0;j<h.length;j++){{H=(H+h.charCodeAt(j))&255;}}
var b=atob(s),a=b.split("").reverse().join(""),r="";
for(var i=0;i<a.length;i++){{var kk=(0x3d+i*89+H)&255;r+=String.fromCharCode(a.charCodeAt(i)^kk)}}
return /^https?:/.test(r)?r:"{fallback}";
}})("{payload}"), type:"application/x-mpegURL"}}]}});
</script></html>'''
    run_provider_test(
        apply,
        embed_url=vidzy_embed,
        media_url=vidzy_media,
        html=vidzy_html,
        options={"provider_name": "Fixture", "max_candidates": 12, "timeout_ms": 8000, "blocked_hosts": ["s1.fsvid.lol"]},
        forbidden=["/troll/master.m3u8"],
    )

    lecteur_embed = "https://lecteurvideo.com/embed.php?id=18230&t=fixture"
    lecteur_media = "https://media.example/hls/interstellar/master.m3u8"
    encoded_media = base64.b64encode(lecteur_media.encode()).decode()
    encoded_telemetry = base64.b64encode(b"https://www.googletagmanager.com/gtag/js?id=G-TEST").decode()
    unrelated_game = "https://s.yimg.com/pv/games/videos/SolitaireClassic_anim_600x400.mp4"
    challenge_video = "https://developers.cloudflare.com/static/hero-video.mp4"
    lecteur_html = f'''<html><body>
<a href="{unrelated_game}">unrelated game shell</a>
<video src="{challenge_video}"></video>
<script>
function showVideo(encoded,type){{return atob(encoded)}}
showVideo('{encoded_telemetry}','2');
showVideo('{encoded_media}','2');
</script></body></html>'''
    run_provider_test(
        apply,
        embed_url=lecteur_embed,
        media_url=lecteur_media,
        html=lecteur_html,
        options={"provider_name": "Coflix", "max_candidates": 12, "timeout_ms": 8000, "blocked_hosts": ["fstream.top"]},
        forbidden=["googletagmanager.com", "s.yimg.com", "developers.cloudflare.com"],
    )


run()
print("hostname-keyed Vidzy/FSVid, LecteurVideo and unrelated-media rejection tests passed")
