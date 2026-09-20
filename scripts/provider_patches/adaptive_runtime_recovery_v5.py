#!/usr/bin/env python3
"""Harden adaptive runtime recovery so file extensions are hints, not proof.

V4 already performs bounded recursive page/player recovery. Its remaining false
positive was treating a URL ending in .mp4/.m3u8/etc. as direct media before a
network probe. Some hosts deliberately expose HTML/player pages on media-looking
paths, which caused quick repair to return a candidate that the health probe then
correctly rejected.

V5 reuses the audited V4 resolver and applies narrow, guarded source rewrites:
- MIME/body/disposition/binary signatures remain positive media proof;
- an extension-only candidate is probed before it can be returned;
- HTML reached through a media-looking URL is parsed recursively as a player;
- nested media-looking links are recursively verified rather than trusted;
- unverified native rows are never re-emitted as a last-resort "success".

Its marker is intentionally outside the legacy V4 migration prefix. Older
``reapply_published_overrides`` logic can therefore maintain historical V4
bundles without ever downgrading a V5 bundle back to extension-trusting code.
V5 removes/replaces its own prior wrapper before delegating to the V4 generator.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
V4_PATH = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"
_spec = importlib.util.spec_from_file_location("nuvio_adaptive_runtime_recovery_v4", V4_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {V4_PATH}")
_v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v4)

MARKER_V5 = "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5"
MARKER_COMMENT = f"/* {MARKER_V5}:"
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"adaptive_runtime_recovery_v5:{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def _strip_previous_v5(text: str) -> str:
    cursor = 0
    parts: list[str] = []
    while True:
        start = text.find(MARKER_COMMENT, cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        parts.append(text[cursor:start])
        call = text.find(ADAPTIVE_CALL, start)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("adaptive_runtime_recovery_v5: unterminated prior wrapper")
        cursor = end + 2
    return "".join(parts).rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    native = _strip_previous_v5(text)
    patched = _v4.apply(native, options=options, **kwargs)

    patched = _replace_once(
        patched,
        "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:",
        f"{MARKER_V5}:",
        "marker",
    )
    patched = _replace_once(
        patched,
        '"runtimeRevision":"generic-core-v2"',
        '"runtimeRevision":"generic-core-v3"',
        "runtime_revision",
    )

    patched = _replace_once(
        patched,
        ',proof=mediaProof(finalUrl,type,"",disposition);if(proof)return{url:finalUrl,proof:proof};if(/(?:text\\/html|application\\/(?:json|javascript|xml)|text\\/(?:plain|xml|javascript))/i.test(type))return null;var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);',
        ',proof=mediaProof(finalUrl,type,"",disposition);if(proof==="extension"){if(mediaType(type))proof="mime";else if(mediaDisposition(disposition))proof="disposition"}if(proof&&proof!=="extension")return{url:finalUrl,proof:proof};if(/(?:text\\/html|application\\/(?:json|javascript|xml)|text\\/(?:xml|javascript))/i.test(type))return null;var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);',
        "opaque_positive_proof",
    )

    patched = _replace_once(
        patched,
        'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",body=null;if(json){body=await r.json()}else if(media(finalUrl,type,"",disposition)){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,status:r.status};',
        'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",body=null,directProof=mediaProof(finalUrl,type,"",disposition);if(json){body=await r.json()}else if((directProof&&directProof!=="extension")||mediaType(type)||mediaDisposition(disposition)){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,status:r.status};',
        "request_extension_hint",
    )

    patched = _replace_once(
        patched,
        'var staticProof=mediaProof(requested,"","","");if(staticProof)return[{url:requested,referer:ref||requested,direct:true,proof:staticProof}];if(opaqueProbeCandidate(requested,ref)){',
        'var staticProof=mediaProof(requested,"","","");if(staticProof&&staticProof!=="extension")return[{url:requested,referer:ref||requested,direct:true,proof:staticProof}];if(staticProof==="extension"){var staticProbe=await probeOpaque(requested,ref);if(staticProbe)return[{url:staticProbe.url,referer:ref||requested,direct:true,proof:staticProbe.proof}]}if(opaqueProbeCandidate(requested,ref)){',
        "resolver_entry_probe",
    )

    patched = _replace_once(
        patched,
        'var proof=mediaProof(page,doc.type,doc.body,doc.disposition);if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));',
        'var proof=mediaProof(page,doc.type,doc.body,doc.disposition);if(proof==="extension"){if(mediaType(doc.type))proof="mime";else if(mediaDisposition(doc.disposition))proof="disposition";else if(mediaBody(doc.body))proof="body";else proof=""}if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));',
        "resolved_page_positive_proof",
    )

    patched = _replace_once(
        patched,
        'var directProof=mediaProof(xs[d],"","","");if(directProof)out.push({url:xs[d],referer:page,direct:true,proof:directProof})',
        'var directProof=mediaProof(xs[d],"","","");if(directProof&&directProof!=="extension")out.push({url:xs[d],referer:page,direct:true,proof:directProof})',
        "nested_direct_proof",
    )
    patched = _replace_once(
        patched,
        'if(media(xs[i],"",""))continue;var ps=playerScore(xs[i],page);',
        'var inlineProof=mediaProof(xs[i],"","","");if(inlineProof&&inlineProof!=="extension")continue;var ps=playerScore(xs[i],page);',
        "nested_extension_recurse",
    )

    patched = _replace_once(
        patched,
        'if(directProof){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{});',
        'if(directProof&&directProof!=="extension"){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{});',
        "native_extension_probe",
    )

    patched = _replace_once(
        patched,
        'var safeNative=Array.isArray(native)?native.filter(function(row){var u=row&&s(row.url);return !!u&&!U[u]&&!bad(u)}):[];return r.length?r:safeNative',
        'var safeNative=Array.isArray(native)?native.filter(function(row){var u=row&&s(row.url),p=mediaProof(u,s(row&&(row.mimeType||row.contentType||row.type||row.format)),"","");return !!u&&!!p&&p!=="extension"&&!U[u]&&!bad(u)}):[];return r.length?r:safeNative',
        "unverified_native_fallback",
    )

    if MARKER_V5 not in patched:
        raise ValueError("adaptive_runtime_recovery_v5: marker missing after hardening")
    return patched
