#!/usr/bin/env python3
"""Upgrade AniKotoTV for the current MegaPlay native-source contract.

The current player exposes an internal ``data-id`` used by ``stream/getSources``.
That ID is authoritative over the historical ``<title>File N - MegaPlay`` value.
MegaPlay can also return an encrypted ``enc`` envelope, so AniKoto keeps the
provider-side AES decoder as a fallback. Core still owns terminal media probing
and remains fail-closed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts" / "provider_patches" / "anikototv_runtime_v2.py"
OVERRIDES = ROOT / "provider-overrides.json"
SCRIPT = "scripts/provider_patches/anikototv_runtime_v2.py"

OLD = '''function finalSource(raw){var data=parsed(raw),src=data&&data.sources;if(src&&typeof src==="object"){var file=s(src.file||src.url||src.src);if(/^https?:\\/\\//i.test(file))return file}if(Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\\/\\//i.test(u))return u}}return""}'''

NEW = '''function utf8Bytes(value){if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(String(value));var encoded=unescape(encodeURIComponent(String(value))),out=new Uint8Array(encoded.length);for(var i=0;i<encoded.length;i++)out[i]=encoded.charCodeAt(i)&255;return out}\nfunction bytesHex(bytes){var out="";for(var i=0;i<bytes.length;i++)out+=bytes[i].toString(16).padStart(2,"0");return out}\nfunction b64urlBytes(value){var x=s(value).replace(/-/g,"+").replace(/_/g,"/");while(x.length%4)x+="=";var raw=atob(x),out=new Uint8Array(raw.length);for(var i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i)&255;return out}\nfunction bytesText(bytes){if(typeof TextDecoder!=="undefined")return new TextDecoder("utf-8").decode(bytes);var raw="";for(var i=0;i<bytes.length;i++)raw+=String.fromCharCode(bytes[i]);try{return decodeURIComponent(escape(raw))}catch(_e){return raw}}\nfunction megaDecodedFile(decoded){var data=parsed(decoded);return s(data&&(data.file||(Array.isArray(data)&&data[0]&&data[0].file)))}\nasync function decryptMega(enc){try{var keyRaw=utf8Bytes("i?LMTAx0Q6,:}50U"),key=new Uint8Array(32),iv=utf8Bytes("W0;27ToaUpl_P%'c"),cipher=b64urlBytes(enc);for(var i=0;i<keyRaw.length&&i<32;i++)key[i]=keyRaw[i];try{if(g&&g.crypto&&g.crypto.subtle&&typeof g.crypto.subtle.importKey==="function"){var cryptoKey=await g.crypto.subtle.importKey("raw",key,{name:"AES-CBC"},false,["decrypt"]),plainBuffer=await g.crypto.subtle.decrypt({name:"AES-CBC",iv:iv},cryptoKey,cipher),webFile=megaDecodedFile(bytesText(new Uint8Array(plainBuffer)));if(/^https?:\\/\\//i.test(webFile))return webFile}}catch(_e){}try{if(g&&typeof g.__crypto_aes_decrypt_raw==="function"){var plain=g.__crypto_aes_decrypt_raw("AES-CBC",new Int8Array(key.buffer.slice(0)),new Int8Array(iv.buffer.slice(0)),new Int8Array(cipher.buffer.slice(0))),nativeFile=megaDecodedFile(bytesText(plain));if(/^https?:\\/\\//i.test(nativeFile))return nativeFile}}catch(_e){}if(typeof require!=="function")return"";var CryptoJS=require("crypto-js"),keyWord=CryptoJS.enc.Hex.parse(bytesHex(key)),ivWord=CryptoJS.enc.Hex.parse(bytesHex(iv)),cipherWord=CryptoJS.enc.Hex.parse(bytesHex(cipher)),params=CryptoJS.lib.CipherParams.create({ciphertext:cipherWord}),plainWord=CryptoJS.AES.decrypt(params,keyWord,{iv:ivWord,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}),cryptoFile=megaDecodedFile(plainWord.toString(CryptoJS.enc.Utf8));return /^https?:\\/\\//i.test(cryptoFile)?cryptoFile:""}catch(_e){return""}}\nfunction normalizeMegaMedia(file,tracks){var u=s(file);if(u.indexOf("//cdn.imgnex.top")>=0)u=u.replace("//cdn.imgnex.top","//ncdn.imgnex.top");if(u.indexOf("mewstream.buzz")>=0&&Array.isArray(tracks)){for(var i=0;i<tracks.length;i++){var f=s(tracks[i]&&tracks[i].file);if(!/^https?:\\/\\//i.test(f)||f.indexOf("mewstream.buzz")>=0)continue;try{var src=new URL(u),ref=new URL(f);src.host=ref.host;u=src.toString();break}catch(_e){}}}return u}\nasync function finalSource(raw){var data=parsed(raw),src=data&&data.sources,file="";if(src&&typeof src==="object"&&!Array.isArray(src))file=s(src.file||src.url||src.src);if(!file&&Array.isArray(src)){for(var i=0;i<src.length;i++){var row=src[i],u=s(row&&typeof row==="object"?(row.file||row.url||row.src):row);if(/^https?:\\/\\//i.test(u)){file=u;break}}}if(!file&&data&&data.enc)file=await decryptMega(data.enc);file=normalizeMegaMedia(file,data&&data.tracks);return /^https?:\\/\\//i.test(file)?file:""}'''

OLD_ID = '''function megaFileId(html){var m=/<title[^>]*>\\s*File\\s+(\\d+)\\s*-\\s*MegaPlay/i.exec(html);return s(m&&m[1])}'''
NEW_ID = '''function megaFileId(html){var current=/\\bdata-id=["'](\\d+)["']/i.exec(html);if(current&&current[1])return s(current[1]);var legacy=/<title[^>]*>\\s*File\\s+(\\d+)\\s*-\\s*MegaPlay/i.exec(html);return s(legacy&&legacy[1])}'''

OLD_RESOLVE = '''async function resolveMega(url,referer,cookie){if(!/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(s(url)))return"";var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return"";var sources=await get("https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid),url,true,page.cookie||cookie,"https://megaplay.buzz");return await finalSource(sources.body)}'''
NEW_RESOLVE = '''function mergeCookies(){var jar={},order=[];for(var a=0;a<arguments.length;a++){for(var part of s(arguments[a]).split(/;\\s*/)){var eq=part.indexOf("=");if(eq<=0)continue;var k=s(part.slice(0,eq)),v=s(part.slice(eq+1));if(!k||/^(?:path|domain|expires|max-age|samesite|secure|httponly)$/i.test(k))continue;if(!(k in jar))order.push(k);jar[k]=v}}return order.map(function(k){return k+"="+jar[k]}).join("; ")}\nfunction megaMediaHost(url){try{var host=new URL(s(url)).hostname.toLowerCase(),domains=["megaplay.buzz","mewstream.buzz","lostproject.club","voltara.click","kotocdn.site","shiora.top","akirax.buzz"];for(var i=0;i<domains.length;i++)if(host===domains[i]||host.endsWith("."+domains[i]))return true}catch(_e){}return false}\nfunction megaPlaybackHeaders(mediaUrl,embedUrl,cookie){var known=megaMediaHost(mediaUrl),out={Referer:known?"https://megaplay.buzz/":embedUrl,"User-Agent":c.userAgent,Origin:"https://megaplay.buzz"};var merged=s(cookie);if(merged&&!known)out.Cookie=merged;return out}\nasync function resolveMega(url,referer,cookie){if(!/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(s(url)))return null;var page=await get(url,referer,false,cookie,"https://megaplay.buzz"),fid=megaFileId(page.body);if(!fid)return null;var sessionCookie=mergeCookies(cookie,page.cookie),sources=await get("https://megaplay.buzz/stream/getSources?id="+encodeURIComponent(fid),url,true,sessionCookie,"https://megaplay.buzz"),media=await finalSource(sources.body),playbackCookie=mergeCookies(sessionCookie,sources.cookie);if(!media)return null;return{url:media,headers:megaPlaybackHeaders(media,url,playbackCookie)}}'''

OLD_MAP = '''var media=u;if(/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(u))media=await resolveMega(u,watch.url,watch.cookie||page.cookie);if(!media)continue;var isMega=/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(u),ql=quality(media),headers={Referer:isMega?"https://megaplay.buzz/":base+"/","User-Agent":c.userAgent};if(isMega)headers.Origin="https://megaplay.buzz";var row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers};'''
NEW_MAP = '''var isMega=/^https?:\\/\\/(?:www\\.)?megaplay\\.buzz\\//i.test(u),media=u,headers={Referer:base+"/","User-Agent":c.userAgent};if(isMega){var resolved=await resolveMega(u,watch.url,watch.cookie||page.cookie);if(!resolved||!resolved.url)continue;media=resolved.url;headers=resolved.headers||headers}if(!media)continue;var ql=quality(media),row={name:c.name,title:c.name,url:media,provider:c.provider,headers:headers};'''


def main() -> int:
    text = RUNTIME.read_text(encoding="utf-8")
    if NEW not in text:
        if OLD not in text:
            start = text.find("function utf8Bytes(value)")
            end = text.find("function megaFileId(html)")
            if start < 0 or end <= start:
                raise SystemExit("AniKoto finalSource/AES anchor not found")
            text = text[:start] + NEW + "\n" + text[end:]
        else:
            text = text.replace(OLD, NEW, 1)
    text = text.replace("return finalSource(sources.body)}", "return await finalSource(sources.body)}")

    if NEW_ID not in text:
        if OLD_ID not in text:
            raise SystemExit("AniKoto MegaPlay source-id anchor not found")
        text = text.replace(OLD_ID, NEW_ID, 1)

    if NEW_RESOLVE not in text:
        if OLD_RESOLVE not in text:
            # Upgrade a previously staged terminal-context resolver in place.
            start = text.find("function mergeCookies()")
            end = text.find("function quality(url)")
            if start < 0 or end <= start:
                raise SystemExit("AniKoto MegaPlay resolver anchor not found")
            text = text[:start] + NEW_RESOLVE + "\n" + text[end:]
        else:
            text = text.replace(OLD_RESOLVE, NEW_RESOLVE, 1)
    if NEW_MAP not in text:
        if OLD_MAP not in text:
            raise SystemExit("AniKoto stream mapping anchor not found")
        text = text.replace(OLD_MAP, NEW_MAP, 1)

    for old_family in (
        '"runtimeFamily": "anikoto-ajax-megaplay-v2"',
        '"runtimeFamily": "anikoto-ajax-megaplay-aes-v3"',
        '"runtimeFamily": "anikoto-ajax-megaplay-aes-v3-terminal-context-v4"',
    ):
        text = text.replace(old_family, '"runtimeFamily": "anikoto-megaplay-data-id-v5"')
    RUNTIME.write_text(text, encoding="utf-8")

    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("anikototv")
    if not isinstance(row, dict):
        raise SystemExit("anikototv patch missing")
    row["route_data_state"] = "repair"
    row["route_proof_version"] = max(7, int(row.get("route_proof_version") or 0))
    notes = [str(v) for v in (row.get("notes") or []) if str(v)]
    for note in (
        "MegaPlay source identity now prefers the current numeric data-id exposed by the player; historical title File N is fallback only.",
        "MegaPlay current `enc` envelope is decoded provider-side with WebCrypto AES-256-CBC (native/CryptoJS fallbacks); plaintext sources.file remains preferred when present.",
        "Known MegaPlay delivery hosts receive root MegaPlay Referer/Origin/User-Agent; unknown legacy media hosts retain embed context without weakening Core terminal validation.",
    ):
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
        "recoveryStatus": "megaplay-data-id-v5-staged",
        "terminalState": None,
        "reasonCodes": ["current_megaplay_data_id", "terminal_media_reproof_required"],
    })
    opts = row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"), dict) else {}
    opts.setdefault(SCRIPT, row.get("provider_lego_options", {}).get(SCRIPT, {}) if isinstance(row.get("provider_lego_options"), dict) else {})
    row["provider_lego_options"] = opts
    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ANIKOTOTV_MEGAPLAY_DATA_ID_V5_STAGED source_id=data-id aes=fallback terminal_headers=host-aware core_terminal_validation=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
