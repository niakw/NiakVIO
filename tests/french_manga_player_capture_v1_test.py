#!/usr/bin/env python3
import importlib.util,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'scripts/provider_patches/french_manga_player_capture_v1.py'
s=importlib.util.spec_from_file_location('capture',p);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m)
base='module.exports={getStreams:async()=>{await fetch("https://vidzy.live/embed-fixture.html");return [{url:"https://s1.fsvid.lol/troll/master.m3u8"}]}};'
src=m.apply(base,options={'provider_name':'French-Manga','base_url':'https://w16.french-manga.net'})
runner=r'''const vm=require('vm');const src=process.argv[2];const calls=[];const b={module:{exports:{}},exports:{},URL,fetch:async u=>{calls.push(String(u));return{ok:true,status:200,url:String(u),headers:{get:()=>"text/html"},text:async()=>"",arrayBuffer:async()=>new ArrayBuffer(0)}}};b.globalThis=b;vm.runInNewContext(src,b);b.module.exports.getStreams('1','tv',1,1).then(v=>console.log(JSON.stringify({v,calls})));'''
with tempfile.TemporaryDirectory() as d:
    q=Path(d)/'r.cjs';q.write_text(runner);cp=subprocess.run(['node',str(q),src],capture_output=True,text=True,timeout=10);assert cp.returncode==0,cp.stderr
    out=json.loads(cp.stdout);rows=out['v'];assert any(r.get('url')=='https://vidzy.live/embed-fixture.html' for r in rows),rows;assert any('/troll/master.m3u8' in r.get('url','') for r in rows),rows
print('French-Manga player capture test passed')
