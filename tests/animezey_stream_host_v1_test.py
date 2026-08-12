#!/usr/bin/env python3
import importlib.util,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'scripts/provider_patches/animezey_stream_host_v1.py'
s=importlib.util.spec_from_file_location('patch',p);m=importlib.util.module_from_spec(s);assert s.loader;s.loader.exec_module(m)
src=m.apply('module.exports={getStreams:async()=>({streams:[{url:"https://animezey16082023.animezey16082023.workers.dev/download.aspx?id=1&token=x"},{url:"https://other.example/a.mkv"}]})};',options={'from_host':'animezey16082023.animezey16082023.workers.dev','to_host':'1.animezeydl.workers.dev'})
runner='const vm=require("vm");const x=process.argv[2],b={module:{exports:{}},exports:{},URL};b.globalThis=b;vm.runInNewContext(x,b);b.module.exports.getStreams({}).then(v=>console.log(JSON.stringify(v)));'
with tempfile.TemporaryDirectory() as d:
    q=Path(d)/'r.cjs';q.write_text(runner);cp=subprocess.run(['node',str(q),src],capture_output=True,text=True,timeout=10);assert cp.returncode==0,cp.stderr
    rows=json.loads(cp.stdout)['streams'];assert rows[0]['url'].startswith('https://1.animezeydl.workers.dev/download.aspx?');assert 'token=x' in rows[0]['url'];assert rows[1]['url']=='https://other.example/a.mkv'
print('AnimeZey stream host wrapper test passed')
