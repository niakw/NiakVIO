#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "desktop_runtime_compat_v1.py"
GLOBAL_PATCH = ROOT / "scripts" / "provider_patches" / "global_runtime_compat_v1.py"


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def test_legacy_scoped_patch() -> None:
    apply = load_apply(PATCH)
    source = (
        "module.exports={getStreams:async function(id,type,s,e){"
        "await fetch('https://api.purstream.id/test',{headers:{Referer:'https://purstream.id/'}});"
        "var t=setTimeout(function(){},5000);clearTimeout(t);"
        "return [{name:'Breaking.Bad.S01E01.1080p',url:'https://example/video.m3u8'},"
        "{name:'Breaking.Bad.S05E16.1080p',url:'https://example/other.m3u8'}]}};"
    )
    options = {
        "normalize_missing_episodes": True,
        "filter_episode_labels": True,
        "max_series_streams": 1,
    }
    patched = apply(source, options)
    assert "NUVIO_DESKTOP_RUNTIME_COMPAT_V1" in patched
    assert 'typeof g.setTimeout!=="function"' in patched
    assert "args[2]=positive" in patched
    assert "episodeMatch" in patched
    assert "output.slice(0,config.maxSeriesStreams)" in patched
    assert "domainFailover" not in patched
    assert "rewriteHost" not in patched
    assert "orderedSuffixes" not in patched
    assert "api.purstream.id/test" in patched
    assert apply(patched, options) == patched

    for forbidden in (
        {"domain_failover": {"host_prefixes": ["api.purstream"], "suffixes": ["club"]}},
        {"domain_replacements": {"api.purstream.id": "api.purstream.club"}},
    ):
        try:
            apply(source, forbidden)
        except ValueError as error:
            assert "domain-agnostic" in str(error)
        else:
            raise AssertionError(f"domain rewrite option was incorrectly accepted: {forbidden}")

def test_global_core_runtime_patch() -> None:
    apply = load_apply(GLOBAL_PATCH)
    source = r'''
var globalThis=this;
var URL=function(raw){
  this.href=String(raw);
  var m=this.href.match(/^(https?:)\/\/([^\/]+)([^?#]*)(\?[^#]*)?(#.*)?$/);
  this.protocol=m[1]; this.host=m[2]; this.hostname=m[2]; this.port="";
  this.pathname=m[3]||"/"; this.search=m[4]||""; this.hash=m[5]||"";
};
URL.prototype.toString=function(){return this.href;};
var nativeCalls=[];
var fetch=async function(input){nativeCalls.push(String(input));return {ok:true,status:200};};
/* Model the historical NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 behavior. */
;(function(g){
  var native=g.fetch.bind(g);
  g.fetch=function(input){var u=new URL(String(input));u.hostname="player.videasy.to";return native(u.toString());};
})(globalThis);
'''
    patched = apply(source, {})
    assert "NUVIO_GLOBAL_RUNTIME_COMPAT_V1" in patched
    assert "__nuvioGlobalRuntimeCompatV1" in patched
    assert "staleMutableUrl" in patched
    assert apply(patched, {}) == patched

    script = patched + r'''
(async function(){
  await fetch("https://player.videasy.net/movie/1");
  if(nativeCalls[0]!=="https://player.videasy.to/movie/1") throw new Error(nativeCalls[0]);
  if(typeof setTimeout!=="function"||typeof clearTimeout!=="function") throw new Error("timer shim missing");
  var u=new URL("https://old.example/a?q=1"); u.hostname="new.example";
  if(String(u)!=="https://new.example/a?q=1") throw new Error("URL mutation remains stale: "+String(u));
  console.log("global Core runtime compatibility passed");
})().catch(function(error){console.error(error);process.exit(1)});
'''
    process = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr or process.stdout
    assert "global Core runtime compatibility passed" in process.stdout


def main() -> int:
    test_legacy_scoped_patch()
    test_global_core_runtime_patch()
    print("desktop/mobile + global Core runtime compatibility patch tests passed: provider domains remain authoritative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
