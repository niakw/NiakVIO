#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'scripts/provider_patches/global_stream_facts_v1.py'
MARKER='NUVIO_STREAM_QUALITY_RECOVERY_V2'

def once(text,old,new,label):
    count=text.count(old)
    if count!=1:
        raise AssertionError(f'{label}: expected one anchor, got {count}')
    return text.replace(old,new,1)

text=TARGET.read_text(encoding='utf-8')
if MARKER not in text:
    old='function blob(row){return [row&&row.name,row&&row.title,row&&row.size,row&&row.description,row&&row.quality,row&&row.language,row&&row.codec,row&&row.audio,row&&row.sourceType,row&&row.releaseType,row&&row.format,row&&row.hdr,row&&row.videoTech,row&&row.bitDepth,row&&row.subtitles].map(s).join(" ")}'
    new='/* NUVIO_STREAM_QUALITY_RECOVERY_V2 */\nfunction urlFacts(row){var u=s(row&&row.url);if(!u)return"";try{u=decodeURIComponent(u)}catch(_e){}return u.replace(/[?#&=/_\\.\\-]+/g," ")}\nfunction blob(row){return [row&&row.name,row&&row.title,row&&row.size,row&&row.description,row&&row.quality,row&&row.resolution,row&&row.height,row&&row.width,row&&row.label,row&&row.language,row&&row.codec,row&&row.audio,row&&row.sourceType,row&&row.releaseType,row&&row.format,row&&row.hdr,row&&row.videoTech,row&&row.bitDepth,row&&row.subtitles,row&&row.sourceLabel,row&&row.filename,urlFacts(row)].map(s).join(" ")}'
    text=once(text,old,new,'facts-current-blob')
    text=once(text,'if(q)out.quality=q;if(l)out.language=l;','if(q)out.quality=q;else if("quality" in out&&!meaningful(out.quality))delete out.quality;if(l)out.language=l;','facts-quality-cleanup')
    TARGET.write_text(text,encoding='utf-8')

value=TARGET.read_text(encoding='utf-8')
for needle in (MARKER,'row&&row.resolution','row&&row.height','urlFacts(row)','else if("quality" in out&&!meaningful(out.quality))delete out.quality'):
    if needle not in value:
        raise AssertionError(needle)
print('STREAM_FACTS_QUALITY_V2_PREPATCH_OK')
