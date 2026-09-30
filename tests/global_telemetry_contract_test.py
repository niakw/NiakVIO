#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))
from global_telemetry_v1 import apply as apply_telemetry  # noqa: E402

fixture = """/* BEGIN NIAKVIO_PROVIDER */
              /* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
              module.exports={getStreams:async function(){return [{url:"https://secret.example/video.m3u8",title:"Secret Movie",headers:{Authorization:"Bearer secret-token"}}]}};
              /* END NIAKVIO_PROVIDER */
          """
patched = apply_telemetry(fixture, context={"provider_id": "demo"})

with tempfile.TemporaryDirectory(prefix="niakvio-telemetry-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(patched, encoding="utf-8")
    runner.write_text(
        """
const store=new Map();
global.localStorage={
  getItem:(k)=>store.has(k)?store.get(k):null,
  setItem:(k,v)=>store.set(k,String(v))
};
const sent=[];
global.__NIAKVIO_TELEMETRY_V1__={
  endpoint:"https://telemetry.example/collect",
  accountPseudonym:"acct-hash-123",
  appVersion:"1.2.3"
};
global.fetch=function(url,opts){sent.push({url:String(url),body:String(opts&&opts.body||"")});return Promise.resolve({ok:true});};
const p=require(%s);
Promise.resolve()
.then(()=>p.getStreams({mediaType:"movie",title:"Do not send me"}))
.then(first=>p.getStreams({mediaType:"movie",title:"Do not send me"}).then(second=>({first,second})))
.then(({first,second})=>{
  const bodies=sent.map(x=>JSON.parse(x.body));
  console.log(JSON.stringify({first,second,sent,bodies,stored:[...store.entries()]}));
}).catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
"""
        % json.dumps(str(provider)),
        encoding="utf-8",
    )
    done = subprocess.run(
        ["node", str(runner)],
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    data = json.loads(done.stdout.strip())

rows = data["first"]
assert rows == data["second"]
assert rows[0]["url"] == "https://secret.example/video.m3u8"
assert rows[0]["title"] == "Secret Movie"
assert rows[0]["headers"]["Authorization"] == "Bearer secret-token"
assert len(data["sent"]) == 2
assert data["sent"][0]["url"] == "https://telemetry.example/collect"
bodies = data["bodies"]
assert bodies[0]["installId"] == bodies[1]["installId"]
assert bodies[0]["sessionId"] == bodies[1]["sessionId"]
assert bodies[0]["providerId"] == "demo"
assert bodies[0]["mediaType"] == "movie"
assert bodies[0]["streamCount"] == 1
assert bodies[0]["accountPseudonym"] == "acct-hash-123"
assert bodies[0]["appVersion"] == "1.2.3"
serialized = json.dumps(bodies)
for forbidden in (
    "secret.example",
    "Secret Movie",
    "Authorization",
    "secret-token",
    "Do not send me",
):
    assert forbidden not in serialized, forbidden
assert data["stored"][0][0] == "niakvio.installId.v1"

# Without a host bridge, the production default endpoint still emits aggregate
# events but must not invent an installId.
anonymous_patched = apply_telemetry(fixture, context={"provider_id": "demo"})
with tempfile.TemporaryDirectory(prefix="niakvio-telemetry-anonymous-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(anonymous_patched, encoding="utf-8")
    runner.write_text(
        """
const sent=[];
global.fetch=function(url,opts){sent.push({url:String(url),body:String(opts&&opts.body||"")});return Promise.resolve({ok:true});};
const p=require(%s);
p.getStreams({mediaType:"tv"}).then(rows=>setTimeout(()=>console.log(JSON.stringify({rows,sent})),0)).catch(e=>{console.error(e);process.exit(1)});
"""
        % json.dumps(str(provider)),
        encoding="utf-8",
    )
    done = subprocess.run(["node", str(runner)], text=True, capture_output=True, timeout=10, check=False)
    assert done.returncode == 0, done.stdout + done.stderr
    anonymous = json.loads(done.stdout.strip())
    assert len(anonymous["sent"]) == 1, anonymous
    assert anonymous["sent"][0]["url"] == "https://www.eittyweb.fr/niakvio-telemetry-collect.php", anonymous
    anon_body = json.loads(anonymous["sent"][0]["body"])
    assert "installId" not in anon_body, anon_body
    assert anon_body["identityScope"] == "anonymous-runtime", anon_body
    assert anon_body["providerId"] == "demo", anon_body

# Explicitly disabling both bridge and default endpoint remains a strict no-op.
no_endpoint_patched = apply_telemetry(
    fixture,
    options={"default_endpoint": ""},
    context={"provider_id": "demo"},
)
with tempfile.TemporaryDirectory(prefix="niakvio-telemetry-no-endpoint-") as raw:
    root = Path(raw)
    provider = root / "provider.cjs"
    runner = root / "runner.cjs"
    provider.write_text(no_endpoint_patched, encoding="utf-8")
    runner.write_text(
        """
const store=new Map();let calls=0;
global.localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,String(v))};
global.fetch=function(){calls++;return Promise.resolve({ok:true})};
const p=require(%s);
p.getStreams({mediaType:"tv"}).then(rows=>console.log(JSON.stringify({calls,rows}))).catch(e=>{console.error(e);process.exit(1)});
"""
        % json.dumps(str(provider)),
        encoding="utf-8",
    )
    done = subprocess.run(
        ["node", str(runner)],
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    data = json.loads(done.stdout.strip())
    assert data["calls"] == 0
    assert data["rows"][0]["url"] == "https://secret.example/video.m3u8"

print("GLOBAL_TELEMETRY_V1_OK privacy=minimal identity=stable-ip-independent fire_and_forget=true")
