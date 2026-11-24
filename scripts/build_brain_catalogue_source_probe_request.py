#!/usr/bin/env python3
"""Build a catalogue source-probe request from an exact current native TV parent.

The committed JSON is only a bounded hypothesis template (provider/fixture,
slug/season/voice). Historical run/SHA/digest fields are never trusted.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
FLAGS=("proofAuthority","publicationAuthority","nativePlaybackAuthority","providerMutationAuthority")
ID=re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
SLUG=re.compile(r"^[a-z0-9][a-z0-9-]{0,125}$")
SHA40=re.compile(r"^[0-9a-f]{40}$")
SHA64=re.compile(r"^[0-9a-f]{64}$")
RUN=re.compile(r"^[0-9]{8,20}$")


def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("expected object: "+str(path))
    return value


def current_digest(root:Path,scope:str,provider:str)->str:
    manifest=load(root/scope)
    rows=[x for x in manifest.get("scrapers") or [] if isinstance(x,dict) and x.get("id")==provider]
    if len(rows)!=1: return ""
    relative=str(rows[0].get("filename") or "")
    if relative.startswith("../"): relative=relative[3:]
    if not relative.startswith("providers/") or ".." in Path(relative).parts: return ""
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file(): return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root:Path,template:dict[str,Any],ledger:dict[str,Any],native_run_id:str="")->dict[str,Any]|None:
    if (template.get("schemaVersion")!=1
            or template.get("probeKind")!="catalogue-inline-source-contract"
            or any(template.get(flag) is not False for flag in FLAGS)):
        raise ValueError("invalid source-probe template")
    provider=str(template.get("providerId") or "")
    fixture=str(template.get("fixture") or "")
    slug=str(template.get("catalogueSlug") or "")
    voice=str(template.get("voice") or "")
    season=template.get("season")
    if (not ID.fullmatch(provider) or not ID.fullmatch(fixture) or not SLUG.fullmatch(slug)
            or not ID.fullmatch(voice) or type(season) is not int or not 0<=season<=100):
        raise ValueError("invalid source-probe template identity")
    if (ledger.get("schemaVersion")!=1
            or ledger.get("authority")!="official-android-tv-emulator-diagnostic-only"
            or ledger.get("primaryClient")!="tv"
            or any(ledger.get(flag) is not False for flag in FLAGS)):
        raise ValueError("invalid native TV ledger")
    requested=str(native_run_id or "")
    if requested and not RUN.fullmatch(requested):
        raise ValueError("invalid requested native run")
    candidates=[]
    for row in ledger.get("rows") or []:
        if not isinstance(row,dict) or row.get("provider")!=provider or row.get("fixture")!=fixture: continue
        run=str(row.get("nativeRunId") or "")
        source=str(row.get("sourceNiakvioSha") or "")
        artifact=str(row.get("providerArtifactSha256") or "")
        scope=str(row.get("manifestScope") or "")
        if requested and run!=requested: continue
        if (not RUN.fullmatch(run) or not SHA40.fullmatch(source) or not SHA64.fullmatch(artifact)
                or scope not in {"manifest.json","vf/manifest.json"}
                or row.get("appSelected") is not True
                or row.get("readerEvidenceComplete") is not True
                or row.get("nativeExtractionZeroObserved") is not True
                or not any(x in {"script_http_missing","script_html_2xx"}
                           for x in row.get("nativeSourceScriptShapePatterns") or [])
                or any(row.get(flag) is not False for flag in FLAGS)
                or current_digest(root,scope,provider)!=artifact):
            continue
        candidates.append((int(run),row))
    if not candidates: return None
    candidates.sort(key=lambda x:x[0],reverse=True)
    top_run=candidates[0][0]
    selected=[row for run,row in candidates if run==top_run]
    if len(selected)!=1: raise ValueError("native source-probe parent is not unique")
    row=selected[0]
    return {
        "schemaVersion":1,"probeKind":"catalogue-inline-source-contract",
        "providerId":provider,"fixture":fixture,
        "sourceRunId":str(row["nativeRunId"]),
        "sourceNiakvioSha":row["sourceNiakvioSha"],
        "providerArtifactSha256":row["providerArtifactSha256"],
        "catalogueSlug":slug,"season":season,"voice":voice,
        **{flag:False for flag in FLAGS},
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--template",type=Path,required=True)
    p.add_argument("--native-ledger",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--native-run-id",default="")
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    request=build(a.root.resolve(),load(a.template),load(a.native_ledger),a.native_run_id)
    if request is None:
        a.output.unlink(missing_ok=True)
        print("FIELD_BRAIN_SOURCE_PROBE_REQUEST ready=false reason=no-exact-current-native-parent")
        return 0
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(request,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("FIELD_BRAIN_SOURCE_PROBE_REQUEST ready=true provider=%s native_run=%s artifact=%s" % (
        request["providerId"],request["sourceRunId"],request["providerArtifactSha256"][:16]))
    return 0


if __name__=="__main__": raise SystemExit(main())
