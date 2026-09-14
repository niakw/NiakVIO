#!/usr/bin/env python3
"""Reuse the already-fetched HLS master as authoritative stream facts.

No second metadata request is introduced. The existing playback-integrity fetch
supplies variant RESOLUTION and EXT-X-MEDIA audio declarations; selected
providers opt in through Core options. Also make native strict probing honor the
existing probe_all_urls/fail_closed_unknown contract used to suppress terminal
403 rows such as PlayIMDb.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HLS = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
OVERRIDES = ROOT / "provider-overrides.json"


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in text:
        return text, False
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1), True


def patch_hls() -> bool:
    text = HLS.read_text(encoding="utf-8")
    changed = False

    old = '    minimum_vod_duration_seconds = max(30, min(int(cfg.get("minimum_vod_duration_seconds", 90)), 600))\n'
    new = old + '    inspect_master_facts = bool(cfg.get("inspect_master_facts", False))\n'
    text, did = replace_once(text, old, new, "HLS config master-facts flag")
    changed |= did

    old = '    payload = json.dumps(payload_config, separators=(",", ":"))\n'
    new = '''    if inspect_master_facts:\n        payload_config.update(\n            {\n                "inspectMasterFacts": True,\n                "implementationRevision": "native-master-facts-v10",\n            }\n        )\n    payload = json.dumps(payload_config, separators=(",", ":"))\n'''
    text, did = replace_once(text, old, new, "HLS payload master-facts flag")
    changed |= did

    anchor = '  async function validateChild(url,stream,referer){\n'
    helpers = r'''  function masterQuality(height){var h=Number(height||0);if(h>=2000)return"2160p";if(h>=1350)return"1440p";if(h>=900)return"1080p";if(h>=650)return"720p";if(h>=550)return"576p";if(h>=450)return"480p";if(h>=300)return"360p";return""}
  function hlsAttr(line,name){var key=String(name||"").replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),q=new RegExp("(?:^|,)\\s*"+key+"\\s*=\\s*\\\"([^\\\"]*)\\\"","i").exec(String(line||""));if(q)return clean(q[1]);var b=new RegExp("(?:^|,)\\s*"+key+"\\s*=\\s*([^,\\s]+)","i").exec(String(line||""));return clean(b&&b[1])}
  function hlsLang(value){var raw=clean(value).toLowerCase().replace(/_/g,"-"),first=raw.split("-")[0],a={eng:"en",english:"en",fra:"fr",fre:"fr",french:"fr",hin:"hi",hindi:"hi",jpn:"ja",japanese:"ja",tam:"ta",tamil:"ta",tel:"te",telugu:"te",ben:"bn",bengali:"bn",mal:"ml",malayalam:"ml",kan:"kn",kannada:"kn",pan:"pa",punjabi:"pa",guj:"gu",gujarati:"gu",mar:"mr",marathi:"mr",urd:"ur",urdu:"ur",kor:"ko",korean:"ko",spa:"es",spanish:"es",deu:"de",ger:"de",german:"de",ita:"it",italian:"it",por:"pt",portuguese:"pt",ara:"ar",arabic:"ar",tur:"tr",turkish:"tr",rus:"ru",russian:"ru",zho:"zh",chi:"zh",chinese:"zh"};if(a[raw])return a[raw];if(a[first])return a[first];return /^[a-z]{2}$/.test(first)?first:""}
  function masterFacts(body){var lines=clean(body).split(/\r?\n/),height=0,tracks=[],seen={};for(var i=0;i<lines.length;i++){var line=lines[i];if(/^#EXT-X-STREAM-INF\s*:/i.test(line)){var rm=/\bRESOLUTION\s*=\s*\d{2,5}\s*[xX]\s*(\d{2,5})/i.exec(line);if(rm)height=Math.max(height,Number(rm[1]||0));continue}if(!/^#EXT-X-MEDIA\s*:/i.test(line)||!/\bTYPE\s*=\s*AUDIO\b/i.test(line))continue;var code=hlsLang(hlsAttr(line,"LANGUAGE")),name=hlsAttr(line,"NAME");if(!code)code=hlsLang(name);if(!code||seen[code])continue;seen[code]=1;tracks.push({language:code,name:name||code.toUpperCase()})}return{height:height,quality:masterQuality(height),audioTracks:tracks}}
  function enrichMasterFacts(stream,facts){if(!stream||!facts)return stream;var row=Object.assign({},stream),tracks=Array.isArray(facts.audioTracks)?facts.audioTracks:[];if(facts.quality){if(clean(row.quality)&&!clean(row.sourceQuality))row.sourceQuality=clean(row.quality);if(clean(row.resolution)&&!clean(row.sourceResolution))row.sourceResolution=clean(row.resolution);row.quality=facts.quality;row.height=Number(facts.height)||row.height;row.hlsMasterQuality=facts.quality}if(tracks.length){row.audioTracks=tracks.map(function(t){return{language:t.language,name:t.name}});row.hlsMasterAudioTracks=row.audioTracks;if(tracks.length>1){if(clean(row.language)&&!clean(row.sourceLanguage))row.sourceLanguage=clean(row.language);row.language="MULTI"}}return row}
'''
    if "function masterFacts(body)" not in text:
        if text.count(anchor) != 1:
            raise AssertionError("HLS helper insertion anchor drifted")
        text = text.replace(anchor, helpers + anchor, 1)
        changed = True

    old = '    var body=await responseText(root),kind=playlistKind(body),base=root.url||String(stream.url||"");\n'
    new = '    var body=await responseText(root),kind=playlistKind(body),base=root.url||String(stream.url||""),facts=null;\n'
    text, did = replace_once(text, old, new, "native master facts prelude")
    changed |= did

    old = '    if(kind==="master"){\n      var variants=variantUris(body,base);'
    new = '    if(kind==="master"){\n      if(config.inspectMasterFacts)facts=masterFacts(body);\n      var variants=variantUris(body,base);'
    text, did = replace_once(text, old, new, "native master facts capture")
    changed |= did

    old = '    return proveMediaPlaylist(body,base,stream,referer);\n'
    new = '    var proof=await proveMediaPlaylist(body,base,stream,referer);if(facts)proof.facts=facts;return proof;\n'
    text, did = replace_once(text, old, new, "native master facts return")
    changed |= did

    old = '    var variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);\n'
    new = '    var facts=config.inspectMasterFacts?masterFacts(body):null,variants=variantUris(body,result.url||url),audio=audioUris(body,result.url||url);\n'
    text, did = replace_once(text, old, new, "browser master facts capture")
    changed |= did

    old = '    return {state:"valid",kind:"master",url:result.url,body:body,result:result};\n'
    new = '    return {state:"valid",kind:"master",url:result.url,body:body,result:result,facts:facts};\n'
    text, did = replace_once(text, old, new, "browser master facts return")
    changed |= did

    old = '    if(inspection.state==="valid")return stream;\n'
    new = '    if(inspection.state==="valid")return config.inspectMasterFacts&&inspection.facts?enrichMasterFacts(stream,inspection.facts):stream;\n'
    text, did = replace_once(text, old, new, "browser master facts enrichment")
    changed |= did

    old = '''      var checks=await Promise.all(rows.map(async function(stream){\n        if(!hlsHint(stream)||remaining<=0)return stream;\n        remaining-=1;\n        var proof=await nativeFirstSegmentProof(stream);\n        if(proof.state==="invalid"){\n          try{console.warn("[Nuvio HLS integrity] rejected invalid first media container",proof.reason||"invalid",String(stream&&stream.url||"").slice(0,180))}catch(_e){}\n          return null;\n        }\n        return stream;\n      }));\n'''
    new = '''      var checks=await Promise.all(rows.map(async function(stream){\n        if(remaining<=0)return stream;\n        if(!hlsHint(stream)){\n          if(!config.probeAllUrls)return stream;\n          remaining-=1;\n          return await validateOrRecover(stream);\n        }\n        remaining-=1;\n        var proof=await nativeFirstSegmentProof(stream);\n        if(proof.state==="invalid"||(proof.state==="unknown"&&config.failClosedUnknown)){\n          try{console.warn("[Nuvio HLS integrity] rejected invalid/strict-unknown native media",proof.reason||"invalid",String(stream&&stream.url||"").slice(0,180))}catch(_e){}\n          return null;\n        }\n        return config.inspectMasterFacts&&proof.facts?enrichMasterFacts(stream,proof.facts):stream;\n      }));\n'''
    text, did = replace_once(text, old, new, "native strict/facts branch")
    changed |= did

    HLS.write_text(text, encoding="utf-8")
    return changed


def patch_overrides() -> bool:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    providers = data.setdefault("provider_patches", {})
    changed = False

    for provider_id in ("purstream", "streamzo", "castle"):
        row = providers.setdefault(provider_id, {})
        core = row.setdefault("core_options", {})
        hls = core.setdefault("hls_runtime_integrity", {})
        if hls.get("inspect_master_facts") is not True:
            hls["inspect_master_facts"] = True
            changed = True

    play = providers.setdefault("playimdb", {})
    core = play.setdefault("core_options", {})
    hls = core.setdefault("hls_runtime_integrity", {})
    for key, value in (("probe_all_urls", True), ("fail_closed_unknown", True)):
        if hls.get(key) is not value:
            hls[key] = value
            changed = True

    # Keep legacy patch-script option mirrors aligned where they still exist;
    # clean v3 composition reads core_options as authority.
    for provider_id in ("purstream", "streamzo", "castle", "playimdb"):
        row = providers.get(provider_id) or {}
        mirrors = row.get("patch_script_options")
        if not isinstance(mirrors, dict):
            continue
        key = "scripts/provider_patches/hls_runtime_integrity_v1.py"
        mirror = mirrors.get(key)
        if not isinstance(mirror, dict):
            continue
        authority = ((row.get("core_options") or {}).get("hls_runtime_integrity") or {})
        for option, value in authority.items():
            if mirror.get(option) != value:
                mirror[option] = value
                changed = True

    if changed:
        OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    changes = {"hls": patch_hls(), "overrides": patch_overrides()}
    print("HLS_MASTER_FACTS_V1_OK", changes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
