#!/usr/bin/env python3
"""Read-only audit of exact current active Provider v3 bytes; never reconstructs."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from provider_patch_blocks import decode_managed_data, owned_span, validate_managed_fixes
from provider_base_store import build_provider_data_model
from materialize_provider_v3_all import provider_model, normalize_anime_transport_compatibility
from provider_v3_filename_policy import matches_provider_v3_filename
from current_provider_scope import active_provider_ids, visible_provider_count

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def canon(v): return str(v or "").strip().casefold()

manifest=load(ROOT/"manifest.json"); overrides=load(ROOT/"provider-overrides.json"); material=load(ROOT/"provider-v3-materialization.json"); static=load(ROOT/"automation/provider-v3-static-knowledge.json")
active=active_provider_ids(); rows=[r for r in manifest.get("scrapers") or [] if isinstance(r,dict) and canon(r.get("id")) in active]; reports=[r for r in material.get("providers") or [] if isinstance(r,dict) and canon(r.get("provider")) in active]
assert {canon(r.get("id")) for r in rows}==active, (len(rows),len(active))
assert {canon(r.get("provider")) for r in reports}==active, (len(reports),len(active))
rb={canon(r.get("provider")):r for r in reports if isinstance(r,dict)}
patches=overrides.get("provider_patches") or {}; capabilities=overrides.get("provider_capabilities") or {}; static_rows=static.get("providers") or {}; seen=set()

# Filename stage is per-provider compatibility metadata, not activation
# authority. During a rolling materialization/publication transition, valid
# workspace and publication names may coexist in the same manifest. Each row
# still has to satisfy the exact content-addressed filename contract for its
# own stage. Provider activation remains owned by the literal providers/ tree.
def _filename_stage(pid: str, name: str) -> str:
    if pid and re.fullmatch(rf"{re.escape(pid)}-[0-9a-f]{{16}}\.js",name,re.I):
        return "workspace"
    if pid and re.fullmatch(rf"{re.escape(pid)}--[A-Za-z0-9._-]+--[0-9a-f]{{16}}\.js",name,re.I):
        return "publication"
    raise AssertionError((pid,name,"invalid-provider-v3-filename-shape"))

stage_counts={"workspace":0,"publication":0}
for row in rows:
    pid=canon(row.get("id")); assert pid and pid not in seen, pid; seen.add(pid)
    rel=str(row.get("filename") or ""); path=ROOT/rel
    assert rel.startswith("providers/") and path.is_file(), (pid,rel)
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    stage=_filename_stage(pid,path.name); stage_counts[stage]+=1
    assert matches_provider_v3_filename(pid,path.name,sha,material,execution_context=stage), (
        pid,path.name,sha[:16],stage,material.get("context"),material.get("publication")
    )
    rep=rb.get(pid); assert rep, pid
    text=raw.decode("utf-8")
    assert text.count("/* BEGIN NIAKVIO_PROVIDER */")==1 and text.count("/* END NIAKVIO_PROVIDER */")==1, pid
    assert text.rstrip().endswith("/* END NIAKVIO_PROVIDER */"), pid
    ids=validate_managed_fixes(text)
    comp=re.sub(r"[^A-Z0-9_.:-]+","_",pid.upper()).strip("_.:-"); cfg=f"PROVIDER.{comp}.CONFIG.V1"
    assert cfg in ids, pid
    spans={}
    for fix_id in ids:
        span=owned_span(text,fix_id)
        assert span is not None, (pid,fix_id)
        spans[fix_id]=span
    ordered=sorted(ids,key=lambda fix_id:spans[fix_id][0])
    first_core=next((i for i,x in enumerate(ordered) if x.startswith("CORE.")),len(ordered))
    assert all(x.startswith("PROVIDER.") for x in ordered[:first_core]), (pid,ordered)
    assert all(x.startswith("CORE.") for x in ordered[first_core:]), (pid,ordered)
    boundary="/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
    assert text.count(boundary)==1, (pid,text.count(boundary))
    boundary_at=text.index(boundary)
    provider_positions=[spans[fix_id][0] for fix_id in ids if fix_id.startswith("PROVIDER.")]
    core_positions=[spans[fix_id][0] for fix_id in ids if fix_id.startswith("CORE.")]
    assert not provider_positions or max(provider_positions)<boundary_at, (pid,ordered)
    assert core_positions and min(core_positions)>boundary_at, (pid,ordered)
    data=decode_managed_data(text,cfg); assert canon(data.get("providerId"))==pid, pid
    expected=str((patches.get(pid) or {}).get("official_site") or "").rstrip("/")
    if expected: assert str(data.get("officialSite") or "").rstrip("/")==expected, pid

    # Final CONFIG is authoritative only when it is a deterministic projection
    # of the *current* structured sources. The materialization report is earlier
    # stage evidence and may legitimately retain an older providerDataSha256
    # after Domain Refresh / CONFIG reconciliation (Flemmix exposed this drift).
    # Never compare final publication DATA to that historical stage hash.
    patch=patches.get(pid); capability=capabilities.get(pid); static_row=static_rows.get(pid)
    assert isinstance(patch,dict) and isinstance(capability,dict) and isinstance(static_row,dict), pid
    entry=json.loads(json.dumps(row))
    normalize_anime_transport_compatibility(entry)
    current_model=provider_model(pid,patch,capability,static_row)
    expected_data=build_provider_data_model(pid,entry,known_site=current_model.get("knownSite"),provider_model=current_model)
    assert data==expected_data, pid

assert set(rb)==seen
visible=visible_provider_count()
assert int(material.get("providerCount") or 0)==visible, (material.get("providerCount"),visible)
if "expectedProviderCount" in material:
    assert int(material.get("expectedProviderCount") or 0)==visible, (material.get("expectedProviderCount"),visible)
print(
    f"PROVIDER_V3_STATIC_AUDIT_OK active={len(active)} visible={visible} reconstruction=false "
    f"filename_stage=per-row workspace={stage_counts['workspace']} publication={stage_counts['publication']} "
    "structured_data=current"
)
