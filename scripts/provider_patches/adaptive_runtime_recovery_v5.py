#!/usr/bin/env python3
"""Harden adaptive runtime recovery so file extensions are hints, not proof.

The internal Core generator performs bounded recursive page/player recovery.
V5 hardens its output so a URL ending in .mp4/.m3u8/etc. is never accepted as
direct media before a network probe. Some hosts deliberately expose HTML/player pages on media-looking
paths, which caused quick repair to return a candidate that the health probe then
correctly rejected.

V5 reuses the audited internal Core resolver and applies narrow, guarded source rewrites:
- MIME/body/disposition/binary signatures remain positive media proof;
- an extension-only candidate is probed before it can be returned;
- HTML reached through a media-looking URL is parsed recursively as a player;
- nested media-looking links are recursively verified rather than trusted;
- unverified native rows are never re-emitted as a last-resort "success".

Its marker remains outside the legacy V4 migration prefix. Historical V4
bundles are accepted only as migration input and are upgraded directly to V5.
V5 removes/replaces its own prior wrapper before delegating to the internal
Core generator.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "scripts" / "adaptive_runtime" / "runtime_recovery_generator.py"
_spec = importlib.util.spec_from_file_location("nuvio_adaptive_runtime_generator", GENERATOR_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {GENERATOR_PATH}")
_generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_generator)

MARKER_V5 = "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5"
MARKER_COMMENT = f"/* {MARKER_V5}:"
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"adaptive_runtime_recovery_v5:{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def _replace_one_of(text: str, olds: tuple[str, ...], new: str, label: str) -> str:
    matches = [(old, text.count(old)) for old in olds]
    present = [(old, count) for old, count in matches if count]
    if len(present) != 1 or present[0][1] != 1:
        detail = ",".join(f"{old}:{count}" for old, count in matches)
        raise ValueError(f"adaptive_runtime_recovery_v5:{label}: expected one unique legacy/current match; {detail}")
    return text.replace(present[0][0], new, 1)


def _replace_variant(
    text: str,
    variants: tuple[tuple[str, str], ...],
    label: str,
) -> str:
    matches = [(old, new, text.count(old)) for old, new in variants]
    present = [(old, new, count) for old, new, count in matches if count]
    if len(present) != 1 or present[0][2] != 1:
        detail = ",".join(f"{index}:{count}" for index, (_old, _new, count) in enumerate(matches))
        raise ValueError(
            f"adaptive_runtime_recovery_v5:{label}: expected one unique source-shape match; {detail}"
        )
    old, new, _count = present[0]
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
    patched = _generator.apply(native, options=options, **kwargs)

    patched = _replace_once(
        patched,
        "NUVIO_ADAPTIVE_RUNTIME_CORE_V7:",
        f"{MARKER_V5}:",
        "marker",
    )
    patched = _replace_one_of(
        patched,
        (
            '"runtimeRevision":"generic-core-v3-census-focus"',
            '"runtimeRevision":"generic-core-v2"',
        ),
        '"runtimeRevision":"generic-core-v3"',
        "runtime_revision",
    )

    patched = _replace_once(
        patched,
        ',proof=mediaProof(finalUrl,type,"",disposition);if(proof)return{url:finalUrl,proof:proof};if(/(?:text\\/html|application\\/(?:json|javascript|xml)|text\\/(?:plain|xml|javascript))/i.test(type))return null;var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);',
        ',proof=mediaProof(finalUrl,type,"",disposition);if(proof==="extension"){if(mediaType(type))proof="mime";else if(mediaDisposition(disposition))proof="disposition"}if(proof&&proof!=="extension")return{url:finalUrl,proof:proof};if(/(?:text\\/html|application\\/(?:json|javascript|xml)|text\\/(?:xml|javascript))/i.test(type))return null;var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);',
        "opaque_positive_proof",
    )

    patched = _replace_variant(
        patched,
        (
            (
                'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",body=null;if(json){body=await r.json()}else if(media(finalUrl,type,"",disposition)){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,status:r.status};',
                'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",body=null,directProof=mediaProof(finalUrl,type,"",disposition);if(json){body=await r.json()}else if((directProof&&directProof!=="extension")||mediaType(type)||mediaDisposition(disposition)){body=""}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,status:r.status};',
            ),
            (
                'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",contentRange=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-range")):"",body=null,proof=mediaProof(finalUrl,type,"",disposition);if(json){body=await r.json()}else if(proof){body=""}else if((Number(r.status)===206||contentRange)&&!/(?:text\\/|application\\/(?:json|javascript|xml))/i.test(type)){proof="range";body=""}else if(/application\\/(?:octet-stream|binary)/i.test(type)){var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);if(binary){proof=binary;body=""}else{U[u]=true;U[finalUrl]=true;body=""}}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,contentRange:contentRange,status:r.status,proof:proof};',
                'var finalUrl=s(r.url||u),type=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-type")):"",disposition=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-disposition")):"",contentRange=r.headers&&typeof r.headers.get==="function"?s(r.headers.get("content-range")):"",body=null,proof=mediaProof(finalUrl,type,"",disposition);if(proof==="extension"){if(mediaType(type))proof="mime";else if(mediaDisposition(disposition))proof="disposition";else proof=""}if(json){body=await r.json()}else if(proof){body=""}else if((Number(r.status)===206||contentRange)&&!/(?:text\\/|application\\/(?:json|javascript|xml))/i.test(type)){proof="range";body=""}else if(/application\\/(?:octet-stream|binary)/i.test(type)){var bytes=await prefixBytes(r,a),binary=binaryProof(bytes);if(binary){proof=binary;body=""}else{U[u]=true;U[finalUrl]=true;body=""}}else{body=await r.text()}var result={body:body,url:finalUrl,type:type,disposition:disposition,contentRange:contentRange,status:r.status,proof:proof};',
            ),
        ),
        "request_extension_hint",
    )

    patched = _replace_once(
        patched,
        'var staticProof=mediaProof(requested,"","","");if(staticProof)return[{url:requested,referer:ref||requested,direct:true,proof:staticProof}];if(opaqueProbeCandidate(requested,ref)){',
        'var staticProof=mediaProof(requested,"","","");if(staticProof&&staticProof!=="extension")return[{url:requested,referer:ref||requested,direct:true,proof:staticProof}];if(staticProof==="extension"){var staticProbe=await probeOpaque(requested,ref);if(staticProbe)return[{url:staticProbe.url,referer:ref||requested,direct:true,proof:staticProbe.proof}]}if(opaqueProbeCandidate(requested,ref)){',
        "resolver_entry_probe",
    )

    patched = _replace_variant(
        patched,
        (
            (
                'var proof=mediaProof(page,doc.type,doc.body,doc.disposition);if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));',
                'var proof=mediaProof(page,doc.type,doc.body,doc.disposition);if(proof==="extension"){if(mediaType(doc.type))proof="mime";else if(mediaDisposition(doc.disposition))proof="disposition";else if(mediaBody(doc.body))proof="body";else proof=""}if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),xs=urls(body,page).concat(normalizedPlayers(body,page));',
            ),
            (
                'var proof=s(doc.proof)||mediaProof(page,doc.type,doc.body,doc.disposition);if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),out=[],form=playerForm(body,page);',
                'var proof=s(doc.proof)||mediaProof(page,doc.type,doc.body,doc.disposition);if(proof==="extension"){if(mediaType(doc.type))proof="mime";else if(mediaDisposition(doc.disposition))proof="disposition";else if(mediaBody(doc.body))proof="body";else proof=""}if(proof)return[{url:page,referer:ref||requested,direct:true,proof:proof}];var body=s(doc.body),out=[],form=playerForm(body,page);',
            ),
        ),
        "resolved_page_positive_proof",
    )

    patched = _replace_one_of(
        patched,
        (
            'var handPage=handed.url||form.url,handProof=s(handed.proof)||mediaProof(handPage,handed.type,handed.body,handed.disposition);if(handProof)return[{url:handPage,referer:page,direct:true,proof:handProof}];',
            'var handPage=handed.url||form.url,handProof=s(handed.proof)||mediaProof(handPage,handed.type,handed.body,handed.disposition);if(handProof==="extension"){if(mediaType(handed.type))handProof="mime";else if(mediaDisposition(handed.disposition))handProof="disposition";else if(mediaBody(handed.body))handProof="body";else handProof=""}if(handProof)return[{url:handPage,referer:page,direct:true,proof:handProof}];',
        ),
        'var handPage=handed.url||form.url,handProof=s(handed.proof)||mediaProof(handPage,handed.type,handed.body,handed.disposition);if(handProof==="extension"){if(mediaType(handed.type))handProof="mime";else if(mediaDisposition(handed.disposition))handProof="disposition";else if(mediaBody(handed.body))handProof="body";else handProof=""}if(handProof)return[{url:handPage,referer:page,direct:true,proof:handProof}];',
        "handoff_page_positive_proof",
    )

    patched = _replace_once(
        patched,
        'var directProof=mediaProof(xs[d],"","","");if(directProof)out.push({url:xs[d],referer:page,direct:true,proof:directProof})',
        'var directProof=mediaProof(xs[d],"","","");if(directProof&&directProof!=="extension")out.push({url:xs[d],referer:page,direct:true,proof:directProof})',
        "nested_direct_proof",
    )
    patched = _replace_variant(
        patched,
        (
            (
                'if(media(xs[i],"","",""))continue;var ps=playerScore(xs[i],page);',
                'var inlineProof=mediaProof(xs[i],"","","");if(inlineProof&&inlineProof!=="extension")continue;var ps=playerScore(xs[i],page);',
            ),
            (
                'if(media(xs[i],"","",""))continue;var nestedEpisode=episodeMarker(xs[i],q),ps=playerScore(xs[i],page);',
                'var inlineProof=mediaProof(xs[i],"","","");if(inlineProof&&inlineProof!=="extension")continue;var nestedEpisode=episodeMarker(xs[i],q),ps=playerScore(xs[i],page);',
            ),
            (
                'if(media(xs[i],"",""))continue;var nestedEpisode=episodeMarker(xs[i],q),ps=playerScore(xs[i],page);',
                'var inlineProof=mediaProof(xs[i],"","","");if(inlineProof&&inlineProof!=="extension")continue;var nestedEpisode=episodeMarker(xs[i],q),ps=playerScore(xs[i],page);',
            ),
        ),
        "nested_extension_recurse",
    )

    patched = _replace_one_of(
        patched,
        (
            'for(var hd=0;hd<handXs.length;hd++){var hp=mediaProof(handXs[hd],"","","");if(hp)out.push({url:handXs[hd],referer:handPage,direct:true,proof:hp})}',
            'for(var hd=0;hd<handXs.length;hd++){var hp=mediaProof(handXs[hd],"","","");if(hp&&hp!=="extension")out.push({url:handXs[hd],referer:handPage,direct:true,proof:hp})}',
        ),
        'for(var hd=0;hd<handXs.length;hd++){var hp=mediaProof(handXs[hd],"","","");if(hp&&hp!=="extension")out.push({url:handXs[hd],referer:handPage,direct:true,proof:hp})}',
        "handoff_nested_direct_proof",
    )
    patched = _replace_one_of(
        patched,
        (
            'if(media(handXs[hi],"","",""))continue;var handEpisode=episodeMarker(handXs[hi],q);',
            'var handInlineProof=mediaProof(handXs[hi],"","","");if(handInlineProof&&handInlineProof!=="extension")continue;var handEpisode=episodeMarker(handXs[hi],q);',
            'if(media(handXs[hi],"",""))continue;var handEpisode=episodeMarker(handXs[hi],q);',
        ),
        'var handInlineProof=mediaProof(handXs[hi],"","","");if(handInlineProof&&handInlineProof!=="extension")continue;var handEpisode=episodeMarker(handXs[hi],q);',
        "handoff_nested_extension_recurse",
    )

    patched = _replace_variant(
        patched,
        (
            (
                'if(directProof){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{});',
                'if(directProof&&directProof!=="extension"){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{});',
            ),
            (
                'if(directProof){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{},q);',
                'if(directProof&&directProof!=="extension"){var directRow=Object.assign({},row,{isDirect:true});resolved.push(directRow);continue}var mediaRows=await resolve(url,ref,0,{},q);',
            ),
        ),
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
