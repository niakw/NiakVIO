#!/usr/bin/env python3
"""Read-only audit of the exact 96 published Provider v3 bytes; never reconstructs."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from provider_patch_blocks import decode_managed_data, owned_span, validate_managed_fixes
from provider_base_store import build_provider_data_model
from materialize_provider_v3_all import provider_model, normalize_anime_transport_compatibility

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def canon(v): return str(v or "").strip().casefold()

manifest=load(ROOT/"manifest.json"); overrides=load(ROOT/"provider-overrides.json"); material=load(ROOT/"provider-v3-materialization.json"); static=load(ROOT/"automation/provider-v3-static-knowledge.json")
rows=manifest.get("scrapers") or []; reports=material.get("providers") or []
assert len(rows)==96 and len(reports)==96, (len(rows),len(reports))
rb={canon(r.get("provider")):r for r in reports if isinstance(r,dict)}
patches=overrides.get("provider_patches") or {}; capabilities=overrides.get("provider_capabilities") or {}; static_rows=static.get("providers") or {}; seen=set()
for row in rows:
    pid=canon(row.get("id")); assert pid and pid not in seen, pid; seen.add(pid)
    rel=str(row.get("filename") or ""); path=ROOT/rel
    assert rel.startswith("providers/") and path.is_file(), (pid,rel)
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    # Final publication filenames are source-qualified and content addressed.
    # provider-v3-materialization.json describes the earlier materialization
    # stage, so its file/sha/generation must not be compared to final bytes
    # after reapply_published_overrides.py has composed publication CONFIG.
    expected_name=rf"{re.escape(pid)}--[A-Za-z0-9._-]+--{sha[:16]}\.js"
    assert re.fullmatch(expected_name,path.name), (pid,path.name,sha[:16])
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
assert material.get("providerCount")==96 and material.get("expectedProviderCount")==96
print("PROVIDER_V3_STATIC_AUDIT_OK providers=96 reconstruction=false publication_stage=final structured_data=current")
