#!/usr/bin/env python3
"""Upgrade AniKotoTV V2 for MegaPlay's current encrypted source envelope.

Current MegaPlay `/stream/getSources` and `/stream/getSourcesNew` return `enc`
instead of `sources.file`. The envelope is base64url AES-256-CBC and can be
decoded with the same CryptoJS capability already used by NiakVIO Castle.
This remains provider/player extraction; Core still owns terminal media probing.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts" / "provider_patches" / "anikototv_runtime_v2.py"
OVERRIDES = ROOT / "provider-overrides.json"
SCRIPT = "scripts/provider_patches/anikototv_runtime_v2.py"

OLD = '''function finalSource(raw){var data=parsed(raw),src=data&&data.sources;if(src&&typeof src==="object"){var file=s(src.file||src.url||src.src);if(/^https?:\\/\\//i.test(file))return file}if(Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\\/\\//i.test(u))return u}}return""}'''

NEW = '''function utf8Bytes(value){if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(String(value));var encoded=unescape(encodeURIComponent(String(value))),out=new Uint8Array(encoded.length);for(var i=0;i<encoded.length;i++)out[i]=encoded.charCodeAt(i)&255;return out}\nfunction bytesHex(bytes){var out="";for(var i=0;i<bytes.length;i++)out+=bytes[i].toString(16).padStart(2,"0");return out}\nfunction b64urlBytes(value){var x=s(value).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";var raw=atob(x),out=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i)&255;return out}\nfunction bytesText(bytes){if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8").decode(bytes);var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);try{return decodeURIComponent(escape(raw))}catch(_e){return raw}}\nfunction decryptMega(enc){try{var keyRaw=utf8Bytes("i?LMTAx0Q6,:}50U"),key=new Uint8Array(32),iv=utf8Bytes("W0;27ToaUpl_P%'c"),cipher=b64urlBytes(enc);for(var i=0;i<keyRaw.length&&i<32;i++)key[i]=keyRaw[i];try{if(g&&typeof g.__crypto_aes_decrypt_raw==="function"){var plain=g.__crypto_aes_decrypt_raw("AES-CBC",new Int8Array(key.buffer.slice(0)),new Int8Array(iv.buffer.slice(0)),new Int8Array(cipher.buffer.slice(0))),nativeText=s(bytesText(plain)),nativeJson=parsed(nativeText),nativeFile=s(nativeJson&&(nativeJson.file||(Array.isArray(nativeJson)&&nativeJson[0]&&nativeJson[0].file)));if(/^https?:\\/\\//i.test(nativeFile))return nativeFile}}catch(_e){}if(typeof require!=="function")return"";var CryptoJS=require("crypto-js"),keyWord=CryptoJS.enc.Hex.parse(bytesHex(key)),ivWord=CryptoJS.enc.Hex.parse(bytesHex(iv)),cipherWord=CryptoJS.enc.Hex.parse(bytesHex(cipher)),params=CryptoJS.lib.CipherParams.create({ciphertext:cipherWord}),plainWord=CryptoJS.AES.decrypt(params,keyWord,{iv:ivWord,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}),decoded=s(plainWord.toString(CryptoJS.enc.Utf8)),data=parsed(decoded),file=s(data&&(data.file||(Array.isArray(data)&&data[0]&&data[0].file)));return /^https?:\\/\\//i.test(file)?file:""}catch(_e){return""}}\nfunction normalizeMegaMedia(file,tracks){var u=s(file);if(u.indexOf("//cdn.imgnex.top")>=0)u=u.replace("//cdn.imgnex.top","//ncdn.imgnex.top");if(u.indexOf("mewstream.buzz")>=0&&Array.isArray(tracks)){for(var i=0;i<tracks.length;i++){var f=s(tracks[i]&&tracks[i].file);if(!/^https?:\\/\\//i.test(f)||f.indexOf("mewstream.buzz")>=0)continue;try{var src=new URL(u),ref=new URL(f);src.host=ref.host;u=src.toString();break}catch(_e){}}}return u}\nfunction finalSource(raw){var data=parsed(raw),src=data&&data.sources,file="";if(src&&typeof src==="object"&&!Array.isArray(src))file=s(src.file||src.url||src.src);if(!file&&Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\\/\\//i.test(u)){file=u;break}}}if(!file&&data&&data.enc)file=decryptMega(data.enc);file=normalizeMegaMedia(file,data&&data.tracks);return /^https?:\\/\\//i.test(file)?file:""}'''


def main() -> int:
    text = RUNTIME.read_text(encoding="utf-8")
    if NEW not in text:
        if OLD not in text:
            raise SystemExit("AniKoto finalSource anchor not found")
        text = text.replace(OLD, NEW, 1)
    text = text.replace('"runtimeFamily": "anikoto-ajax-megaplay-v2"', '"runtimeFamily": "anikoto-ajax-megaplay-aes-v3"')
    RUNTIME.write_text(text, encoding="utf-8")

    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("anikototv")
    if not isinstance(row, dict):
        raise SystemExit("anikototv patch missing")
    row["route_data_state"] = "repair"
    row["route_proof_version"] = max(5, int(row.get("route_proof_version") or 0))
    notes = [str(v) for v in (row.get("notes") or []) if str(v)]
    note = "MegaPlay current `enc` envelope is decoded provider-side with AES-256-CBC; terminal URL still passes through Core media validation."
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    disp = row.get("repair_disposition")
    if not isinstance(disp, dict):
        disp = {}
        row["repair_disposition"] = disp
    disp.update({
        "routeDataState": "repair",
        "currentVerifiedLanes": [],
        "provenLanes": [],
        "missingLanes": ["anime"],
        "completeCapabilityProof": False,
        "recoveryStatus": "megaplay-aes-v3-staged",
        "terminalState": None,
        "reasonCodes": ["current_megaplay_enc_envelope", "aes_v3_staged"],
    })
    opts = row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"), dict) else {}
    opts.setdefault(SCRIPT, row.get("provider_lego_options", {}).get(SCRIPT, {}) if isinstance(row.get("provider_lego_options"), dict) else {})
    row["provider_lego_options"] = opts
    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ANIKOTOTV_MEGAPLAY_AES_V3_STAGED crypto=crypto-js core_terminal_validation=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
