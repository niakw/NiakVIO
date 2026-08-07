#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "desktop_runtime_compat_v1.py"


def load_apply():
    spec = importlib.util.spec_from_file_location("desktop_runtime_compat_v1", PATCH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def main() -> int:
    apply = load_apply()
    source = "module.exports={getStreams:async function(id,type,s,e){await fetch('https://api.purstream.club/test',{headers:{Referer:'https://purstream.club/'}});var t=setTimeout(function(){},5000);clearTimeout(t);return [{name:'Breaking.Bad.S01E01.1080p',url:'https://example/video.m3u8'},{name:'Breaking.Bad.S05E16.1080p',url:'https://example/other.m3u8'}]}};"
    options = {
        "normalize_missing_episodes": True,
        "filter_episode_labels": True,
        "max_series_streams": 1,
        "domain_failover": {
            "host_prefixes": ["api.purstream", "purstream"],
            "suffixes": ["club", "art"],
        },
    }
    patched = apply(source, options)
    assert "NUVIO_DESKTOP_RUNTIME_COMPAT_V1" in patched
    assert 'typeof g.setTimeout!=="function"' in patched
    assert "args[2]=positive" in patched
    assert "episodeMatch" in patched
    assert "output.slice(0,config.maxSeriesStreams)" in patched
    assert '"hostPrefixes":["api.purstream","purstream"]' in patched
    assert '"suffixes":["club","art"]' in patched
    assert apply(patched, options) == patched

    with tempfile.TemporaryDirectory() as temp:
        bundle = Path(temp) / "bundle.js"
        runner = Path(temp) / "runner.cjs"
        bundle.write_text(patched, encoding="utf-8")
        runner.write_text(
            "delete global.setTimeout; delete global.clearTimeout;\n"
            "const attempts=[];\n"
            "global.fetch=async function(url,init){\n"
            "  const value=String(url); attempts.push({url:value,referer:init&&init.headers&&init.headers.Referer});\n"
            "  if(value.startsWith('https://api.purstream.club/')) throw new Error('club unavailable');\n"
            "  if(value.startsWith('https://api.purstream.art/')) return {ok:true,status:200};\n"
            "  throw new Error(value);\n"
            "};\n"
            f"const provider=require({str(bundle)!r});\n"
            "provider.getStreams('1396','tv',undefined,undefined).then(function(rows){\n"
            "  if(typeof global.setTimeout!=='function') throw new Error('timer shim missing');\n"
            "  if(rows.length!==1||!/S01E01/i.test(rows[0].name)) throw new Error(JSON.stringify(rows));\n"
            "  if(attempts.length!==2) throw new Error('unexpected attempts '+JSON.stringify(attempts));\n"
            "  if(!attempts[0].url.startsWith('https://api.purstream.club/')) throw new Error(JSON.stringify(attempts));\n"
            "  if(!attempts[1].url.startsWith('https://api.purstream.art/')) throw new Error(JSON.stringify(attempts));\n"
            "  if(attempts[1].referer!=='https://purstream.art/') throw new Error('referer not rewritten '+JSON.stringify(attempts));\n"
            "  console.log('desktop runtime JS execution passed');\n"
            "}).catch(function(error){console.error(error);process.exit(1)});\n",
            encoding="utf-8",
        )
        process = subprocess.run(["node", str(runner)], capture_output=True, text=True, timeout=20)
        assert process.returncode == 0, process.stderr or process.stdout
        assert "desktop runtime JS execution passed" in process.stdout

    print("desktop runtime compatibility patch tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
