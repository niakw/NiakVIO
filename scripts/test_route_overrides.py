#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        results={"results":[{"canonical_id":"demo","tests":[{"network_observations":[
            {"stage":"origin_probe","host":"demo.test","status":200,"infrastructure":False},
            {"stage":"search","host":"demo.test","method":"GET","path_pattern":"/search?q={value}","status":404,"infrastructure":False},
            {"stage":"search","host":"demo.test","method":"GET","path_pattern":"/search?q={value}","status":404,"infrastructure":False},
            {"stage":"search","host":"demo.test","method":"GET","path_pattern":"/search?q={value}","status":404,"infrastructure":False},
        ]}]}]}
        config={"schema_version":2,"route_override_defaults":{"minimum_requests":3,"obsolete_statuses":[404,410],"obsolete_ratio":0.75,"require_successful_origin_probe":True},"provider_patches":{"demo":{"replacements":{},"route_replacements":{}}}}
        rp=tmp/'results.json'; cp=tmp/'config.json'; out=tmp/'report.json'
        rp.write_text(json.dumps(results)); cp.write_text(json.dumps(config))
        subprocess.run([sys.executable,str(ROOT/'scripts/validate_route_overrides.py'),'--config',str(cp),'--results',str(rp),'--report',str(out)],check=True)
        report=json.loads(out.read_text())
        assert len(report['regressions'])==1, report
        assert report['regressions'][0]['path_patterns'][0]['pattern']=='/search?q={value}'

        gap_results={"results":[{"canonical_id":"demo","tests":[{"network_observations":[
            {"stage":"origin_probe","host":"demo.test","status":200,"infrastructure":False}
        ]}]}]}
        rp.write_text(json.dumps(gap_results))
        cp.write_text(json.dumps(config))
        completed=subprocess.run([sys.executable,str(ROOT/'scripts/validate_route_overrides.py'),'--config',str(cp),'--results',str(rp),'--report',str(out),'--strict'],capture_output=True,text=True)
        assert completed.returncode == 0, completed
        gap_report=json.loads(out.read_text())
        assert gap_report['instrumentation_gaps'][0]['provider']=='demo', gap_report
        assert 'deprecated' in completed.stdout.lower(), completed.stdout
    print('route override tests passed')
if __name__=='__main__': main()
