#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from scripts.stream_score import score_stream

best=score_stream(
 {"resolution":"2160p","videoCodec":"HEVC","videoBitrateMbps":28.7,"bitDepth":10,"dynamicRange":"HDR10","source":"UHD-REMUX","audioCodec":"TrueHD","audioChannels":7.1},
 {"throughputMbps":160,"startupSeconds":0.8,"stallCount":0,"segmentSuccessRatio":1.0,"providerSuccessRatio":0.98,"providerSampleCount":30,"providerEvidenceAgeHours":4},
)
assert best["status"]=="scored"
assert best["grade"]=="S+"
assert best["badgeId"]=="stream-score-s-plus"
assert best["token"]=="STREAM_SCORE=S+"
assert best["score"]>=95

good=score_stream(
 {"resolution":"1080p","videoCodec":"HEVC","videoBitrateMbps":7.8,"bitDepth":10,"dynamicRange":"SDR","source":"WEB-DL","audioCodec":"E-AC-3","audioChannels":5.1},
 {"throughputMbps":32,"startupSeconds":1.2,"stallCount":0,"segmentSuccessRatio":1.0,"providerSuccessRatio":0.94,"providerSampleCount":20,"providerEvidenceAgeHours":8},
)
assert good["grade"] in {"S","S+"}

p720=score_stream(
 {"resolution":"720p","videoCodec":"HEVC","videoBitrateMbps":5.0,"bitDepth":10,"dynamicRange":"SDR","source":"WEB-DL","audioCodec":"AAC","audioChannels":2.0},
 {"throughputMbps":30,"startupSeconds":1.0,"stallCount":0,"segmentSuccessRatio":1.0,"providerSuccessRatio":0.95,"providerSampleCount":20},
)
p1080_bad=score_stream(
 {"resolution":"1080p","videoCodec":"AVC","videoBitrateMbps":2.2,"bitDepth":8,"dynamicRange":"SDR","source":"WEBRip","audioCodec":"AAC","audioChannels":2.0},
 {"throughputMbps":30,"startupSeconds":1.0,"stallCount":0,"segmentSuccessRatio":1.0,"providerSuccessRatio":0.95,"providerSampleCount":20},
)
assert p720["score"]>p1080_bad["score"]

slow=score_stream(
 {"resolution":"2160p","videoCodec":"HEVC","videoBitrateMbps":20,"bitDepth":10,"dynamicRange":"HDR10","source":"WEB-DL","audioCodec":"E-AC-3","audioChannels":5.1},
 {"throughputMbps":15,"startupSeconds":8,"stallCount":3,"stallSeconds":8,"segmentSuccessRatio":0.84,"providerSuccessRatio":0.65,"providerSampleCount":20},
)
assert slow["score"]<=39
assert slow["grade"]=="E"

missing=score_stream({"resolution":"1080p","videoCodec":"HEVC","videoBitrateMbps":6.0,"source":"WEB-DL"},{})
assert missing["status"]=="insufficient-evidence"
assert missing["grade"] is None
assert missing["badgeId"] is None

rejected=score_stream({"wrongMedia":True},{"throughputMbps":100})
assert rejected["status"]=="rejected"
assert rejected["badgeId"] is None


PATCH = ROOT / "scripts" / "provider_patches" / "global_stream_score_v1.py"
spec = importlib.util.spec_from_file_location("global_stream_score_v1", PATCH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

source = r'''module.exports={getStreams:async()=>[{
  name:"Demo - 1080p",
  title:"Demo - 1080p",
  description:"🎬 Demo • 2026\n🎞️ WEB-DL • AVC • 1080p\n🔊 AAC • 2.0",
  size:"🎬 Demo • 2026\n🎞️ WEB-DL • AVC • 1080p\n🔊 AAC • 2.0",
  quality:"1080p",
  sourceType:"WEB-DL",
  codec:"AVC",
  audioCodec:"AAC",
  audioChannels:"2.0",
  bitrate:"6.0 Mbps",
  presentationFacts:{quality:"1080p",sourceType:"WEB-DL",codec:"AVC",audioCodec:"AAC",audioChannels:"2.0",bitrate:"6.0 Mbps"},
  badgeIds:["1080p-full-hd","webdl","avc","aac","2.0"],
  displayBadges:["1080p","WEB-DL","AVC","AAC","2.0"],
  __nuvioStreamNetworkEvidenceV1:{success:true,sampleMbps:30,sampleConfidence:.75,latencyMs:120,segmentSuccessRatio:1,terminalProbeLatencyMs:140},
  url:"https://cdn.example/demo.mp4"
}]};'''
patched = runtime.apply(source)
with tempfile.TemporaryDirectory() as tmp:
    provider = Path(tmp) / "provider.cjs"
    provider.write_text(patched, encoding="utf-8")
    runner = Path(tmp) / "runner.cjs"
    runner.write_text(
        "const p=require(process.argv[2]);p.getStreams('1','movie').then(v=>console.log(JSON.stringify(v[0]))).catch(e=>{console.error(e);process.exit(1)});",
        encoding="utf-8",
    )
    proc = subprocess.run(["node", str(runner), str(provider)], text=True, capture_output=True, timeout=10)
assert proc.returncode == 0, proc.stdout + proc.stderr
scored_row = json.loads(proc.stdout.strip().splitlines()[-1])
assert scored_row["streamScore"]["status"] == "scored", scored_row
assert scored_row["streamScore"]["grade"], scored_row
grade = scored_row["streamScore"]["grade"]
assert f"stream-score-{grade.lower().replace('+','-plus')}" in scored_row["badgeIds"], scored_row
assert f"Stream Score: {grade}" in scored_row["description"], scored_row
assert scored_row["size"] == scored_row["description"], scored_row
assert "__nuvioStreamNetworkEvidenceV1" not in scored_row, scored_row

estimated_source = source.replace(
    ',\n  __nuvioStreamNetworkEvidenceV1:{success:true,sampleMbps:30,sampleConfidence:.75,latencyMs:120,segmentSuccessRatio:1,terminalProbeLatencyMs:140}',
    ''
)
estimated_patched = runtime.apply(estimated_source)
with tempfile.TemporaryDirectory() as tmp:
    provider = Path(tmp) / "provider.cjs"
    provider.write_text(estimated_patched, encoding="utf-8")
    runner = Path(tmp) / "runner.cjs"
    runner.write_text(
        "const p=require(process.argv[2]);p.getStreams('1','movie').then(v=>console.log(JSON.stringify(v[0]))).catch(e=>{console.error(e);process.exit(1)});",
        encoding="utf-8",
    )
    proc = subprocess.run(["node", str(runner), str(provider)], text=True, capture_output=True, timeout=10)
assert proc.returncode == 0, proc.stdout + proc.stderr
estimated_row = json.loads(proc.stdout.strip().splitlines()[-1])
assert estimated_row["streamScore"]["status"] == "estimated", estimated_row
assert estimated_row["streamScore"]["mode"] == "technical-estimate", estimated_row
assert estimated_row["streamScore"]["grade"], estimated_row
estimated_grade = estimated_row["streamScore"]["grade"]
assert f"stream-score-{estimated_grade.lower().replace('+','-plus')}" in estimated_row["badgeIds"], estimated_row
assert f"Stream Score: {estimated_grade}" in estimated_row["description"], estimated_row
assert estimated_row["streamScore"]["networkEvidence"] is None, estimated_row

