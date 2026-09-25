#!/usr/bin/env python3
"""Truthful NiakVIO global stream scoring contract."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

GRADE_BANDS=(("S+",95),("S",90),("A+",85),("A",80),("B",70),("C",60),("D",40),("E",0))
GRADE_BADGES={"S+":"stream-score-s-plus","S":"stream-score-s","A+":"stream-score-a-plus","A":"stream-score-a","B":"stream-score-b","C":"stream-score-c","D":"stream-score-d","E":"stream-score-e"}
RESOLUTION_SCORE={4320:100,2160:96,1440:90,1080:84,720:70,576:54,480:48,360:32,240:20}
CODEC_EFFICIENCY={"av1":100,"hevc":94,"h265":94,"vp9":88,"avc":78,"h264":78,"vc1":58,"mpeg2":48,"mpeg4":45}
TARGET_1080P24_MBPS={"av1":2.8,"hevc":3.5,"h265":3.5,"vp9":4.2,"avc":6.0,"h264":6.0,"vc1":7.0,"mpeg2":10.0,"mpeg4":7.5}
SOURCE_SCORE={"uhd-remux":100,"bd-remux":98,"blu-ray-remux":98,"uhd-blu-ray":100,"blu-ray":92,"bdmv":92,"web-dl":84,"webdl":84,"hdtv":65,"webrip":58,"dvd":35,"dvd-rip":35,"cam":8,"ts":12,"telesync":12,"tc":18,"telecine":18}
AUDIO_SCORE={"truehd":100,"dts-hd ma":98,"dts-hd":94,"lpcm":100,"pcm":98,"flac":96,"eac3":80,"e-ac-3":80,"ac3":68,"ac-3":68,"aac":65,"opus":76,"dts":72,"mp3":45,"alac":96}

def _norm(v:Any)->str: return str(v or "").strip().casefold().replace("_","-").replace(".","")
def _num(v:Any)->float|None:
    try: n=float(v)
    except (TypeError,ValueError): return None
    return n if n>=0 else None

def _curve(v:float,p:tuple[tuple[float,float],...])->float:
    if v<=p[0][0]: return p[0][1]
    if v>=p[-1][0]: return p[-1][1]
    for (x0,y0),(x1,y1) in zip(p,p[1:]):
        if x0<=v<=x1:
            r=(v-x0)/(x1-x0)
            return y0+(y1-y0)*r
    return p[-1][1]

def _weighted(parts:list[tuple[float,float]])->tuple[float|None,float]:
    if not parts: return None,0.0
    w=sum(a for a,_ in parts)
    return sum(a*b for a,b in parts)/w,w

def _height(f:dict[str,Any])->int|None:
    raw=f.get("height") or f.get("resolutionHeight")
    if raw is not None:
        try: return int(raw)
        except (TypeError,ValueError): pass
    t=_norm(f.get("resolution"))
    if "8k" in t: return 4320
    if "4k" in t or "uhd" in t: return 2160
    for h in sorted(RESOLUTION_SCORE,reverse=True):
        if str(h) in t: return h
    return None

def _codec(f:dict[str,Any])->str:
    r=_norm(f.get("codec") or f.get("videoCodec"))
    return {"h-265":"hevc","h265":"hevc","h-264":"avc","h264":"avc","mpeg-2":"mpeg2","mpeg-4":"mpeg4","vc-1":"vc1"}.get(r,r)

def _video(f:dict[str,Any])->tuple[float|None,float]:
    parts=[]
    h=_height(f)
    if h: parts.append((.30,RESOLUTION_SCORE.get(h,96 if h>2160 else 84 if h>1080 else 60)))
    codec=_codec(f)
    if codec in CODEC_EFFICIENCY: parts.append((.20,CODEC_EFFICIENCY[codec]))
    br=_num(f.get("videoBitrateMbps") or f.get("bitrateMbps"))
    fps=_num(f.get("fps") or f.get("frameRate")) or 24.0
    if br and h:
        target=TARGET_1080P24_MBPS.get(codec,6.0)*(h/1080.0)**2*max(.75,fps/24.0)
        parts.append((.35,_curve(br/max(target,.1),((0,0),(.4,25),(.6,50),(.8,72),(1,86),(1.3,94),(1.7,98),(2.2,100)))))
    bit=int(_num(f.get("bitDepth")) or 8)
    hdr=_norm(f.get("hdr") or f.get("dynamicRange"))
    dyn=82.0 if bit>=10 else 65.0
    if "dolby-vision" in hdr or "dolbyvision" in hdr: dyn=98
    elif "hdr10+" in hdr or "hdr10plus" in hdr: dyn=96
    elif "hdr10" in hdr or hdr=="hdr": dyn=92
    elif "hlg" in hdr: dyn=90
    parts.append((.15,dyn))
    s,w=_weighted(parts)
    return s,min(1.0,w)

def _source(f:dict[str,Any])->tuple[float|None,float]:
    s=_norm(f.get("source") or f.get("provenance")).replace(" ","-")
    v=SOURCE_SCORE.get(s)
    return (float(v),1.0) if v is not None else (None,0.0)

def _audio(f:dict[str,Any])->tuple[float|None,float]:
    raw=_norm(f.get("audioCodec"))
    key={"eac3":"eac3","ac3":"ac3","dtshdma":"dts-hd ma","dtshd":"dts-hd"}.get(raw.replace("-","").replace(" ",""),raw)
    base=AUDIO_SCORE.get(key)
    if base is None: return None,0.0
    ch=_num(f.get("audioChannels") or f.get("channels")) or 2.0
    chs=100 if ch>=7.1 else 90 if ch>=5.1 else 70 if ch>=2 else 50
    return .70*base+.30*chs,1.0

def _playback(p:dict[str,Any],media_br:float|None)->tuple[float|None,float,dict[str,Any]]:
    parts=[]; detail={}
    throughput=_num(p.get("throughputMbps"))
    headroom=_num(p.get("headroomRatio"))
    if headroom is None and throughput is not None and media_br: headroom=throughput/max(media_br,.1)
    if headroom is not None:
        detail["headroomRatio"]=round(headroom,3)
        parts.append((.40,_curve(headroom,((.5,5),(.8,20),(1,40),(1.25,60),(1.5,75),(2.5,90),(4,98),(6,100)))))
    startup=_num(p.get("startupSeconds"))
    if startup is not None:
        detail["startupSeconds"]=startup
        parts.append((.20,100 if startup<=1 else 90 if startup<=2 else 75 if startup<=4 else 50 if startup<=8 else 25 if startup<=12 else 10))
    stalls=_num(p.get("stallCount")); stall_sec=_num(p.get("stallSeconds")) or 0.0
    if stalls is not None:
        detail["stallCount"]=int(stalls); detail["stallSeconds"]=stall_sec
        parts.append((.25,max(0.0,100.0-stalls*22.0-stall_sec*5.0)))
    success=_num(p.get("segmentSuccessRatio"))
    if success is not None:
        success=max(0.0,min(1.0,success)); detail["segmentSuccessRatio"]=success
        parts.append((.15,success*100.0))
    s,w=_weighted(parts)
    return s,min(1.0,w),detail

def _reliability(p:dict[str,Any])->tuple[float|None,float]:
    ratio=_num(p.get("providerSuccessRatio"))
    if ratio is None: return None,0.0
    ratio=max(0.0,min(1.0,ratio))
    n=int(_num(p.get("providerSampleCount")) or 0)
    age=_num(p.get("providerEvidenceAgeHours")) or 0.0
    fresh=1.0 if age<=24 else .85 if age<=72 else .65 if age<=168 else .40
    return ratio*100.0,min(1.0,n/20.0)*fresh

def _grade(score:float)->str:
    for grade,minimum in GRADE_BANDS:
        if score>=minimum: return grade
    return "E"

def score_stream(facts:dict[str,Any],playback:dict[str,Any]|None=None)->dict[str,Any]:
    p=playback or {}
    invalid=[k for k in ("wrongMedia","invalidMedia","placeholderMedia") if facts.get(k) is True or p.get(k) is True]
    if invalid:
        return {"schemaVersion":1,"status":"rejected","score":0,"grade":None,"badgeId":None,"token":None,"confidence":1.0,"reasons":invalid}
    components=[]
    for name,weight,fn in (("videoQuality",45.0,_video),("sourceProvenance",10.0,_source),("audioQuality",10.0,_audio)):
        val,conf=fn(facts)
        if val is not None: components.append((name,weight,val,conf))
    media_br=_num(facts.get("videoBitrateMbps") or facts.get("bitrateMbps"))
    play,pc,detail=_playback(p,media_br)
    if play is not None: components.append(("playbackNetwork",30.0,play,pc))
    rel,rc=_reliability(p)
    if rel is not None: components.append(("providerReliability",5.0,rel,rc))
    if not components:
        return {"schemaVersion":1,"status":"insufficient-evidence","score":None,"grade":None,"badgeId":None,"token":None,"confidence":0.0,"breakdown":{}}
    active=sum(w for _,w,_,_ in components)
    raw=sum(w*s for _,w,s,_ in components)/active
    confidence=sum(w*c for _,w,_,c in components)/100.0
    cap=None
    hr=detail.get("headroomRatio")
    if isinstance(hr,(int,float)) and hr<.9: cap=39.0
    if (detail.get("stallCount") or 0)>=3 and (detail.get("stallSeconds") or 0)>=5: cap=min(cap or 100.0,39.0)
    sr=detail.get("segmentSuccessRatio")
    if isinstance(sr,(int,float)) and sr<.80: cap=min(cap or 100.0,39.0)
    if cap is not None: raw=min(raw,cap)
    score=round(max(0.0,min(100.0,raw)),1)
    status="scored" if play is not None and confidence>=.60 else "insufficient-evidence"
    grade=_grade(score) if status=="scored" else None
    return {"schemaVersion":1,"status":status,"score":score,"grade":grade,"badgeId":GRADE_BADGES.get(grade) if grade else None,"token":f"STREAM_SCORE={grade}" if grade else None,"confidence":round(confidence,3),"breakdown":{n:{"weight":w,"score":round(s,1),"confidence":round(c,3)} for n,w,s,c in components},"playback":detail,"hardCap":cap}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); args=ap.parse_args()
    payload=json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(score_stream(payload.get("facts") if isinstance(payload.get("facts"),dict) else {},payload.get("playback") if isinstance(payload.get("playback"),dict) else {}),ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
