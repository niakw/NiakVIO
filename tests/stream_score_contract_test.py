#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
