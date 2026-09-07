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
    old_quality='function quality(row,b){if(meaningful(row.quality)){var v=s(row.quality);return /^(?:4k|2160p)$/i.test(v)?"2160p":v}var u=b.toUpperCase();if(/(?:\\b4K\\b|\\b2160P?\\b|\\bUHD\\b)/.test(u))return"2160p";var m=u.match(/\\b(1440|1080|720|576|540|480|360)P?\\b/);return m?m[1]+"p":""}'
    new_quality='function qualityFromHeight(height){var h=Number(height||0);if(h>=2000)return"2160p";if(h>=1350)return"1440p";if(h>=900)return"1080p";if(h>=650)return"720p";if(h>=450)return"480p";if(h>=300)return"360p";return""}\nfunction quality(row,b){if(meaningful(row.quality)){var v=s(row.quality);return /^(?:4k|2160p)$/i.test(v)?"2160p":v}var resolution=s(row&&row.resolution),rm=resolution.match(/(\\d{2,5})\\s*[xX×]\\s*(\\d{2,5})/);if(rm){var rq=qualityFromHeight(rm[2]);if(rq)return rq}var hq=qualityFromHeight(row&&row.height);if(hq)return hq;var u=b.toUpperCase();if(/(?:\\b4K\\b|\\b2160P?\\b|\\bUHD\\b)/.test(u))return"2160p";var m=u.match(/\\b(1440|1080|720|576|540|480|360)P?\\b/);return m?m[1]+"p":""}'
    text=once(text,old_quality,new_quality,'facts-resolution-height-quality')
    text=once(text,'if(q)out.quality=q;if(l)out.language=l;','if(q)out.quality=q;else if("quality" in out&&!meaningful(out.quality))delete out.quality;if(l)out.language=l;','facts-quality-cleanup')
    TARGET.write_text(text,encoding='utf-8')

value=TARGET.read_text(encoding='utf-8')
for needle in (MARKER,'row&&row.resolution','row&&row.height','urlFacts(row)','qualityFromHeight','resolution.match','else if("quality" in out&&!meaningful(out.quality))delete out.quality'):
    if needle not in value:
        raise AssertionError(needle)
print('STREAM_FACTS_QUALITY_V2_PREPATCH_OK')
