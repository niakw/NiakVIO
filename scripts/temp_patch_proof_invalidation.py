#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/check_provider_non_regression_v1.py')
t = p.read_text(encoding='utf-8')

old = 'DEFAULT_OUT = ROOT / "automation" / "provider-non-regression-gate.json"\nCURRENT_MANIFEST = ROOT / "manifest.json"'
new = 'DEFAULT_OUT = ROOT / "automation" / "provider-non-regression-gate.json"\nDEFAULT_INVALIDATIONS = ROOT / "automation" / "provider-proof-invalidations.json"\nCURRENT_MANIFEST = ROOT / "manifest.json"'
if 'DEFAULT_INVALIDATIONS' not in t:
    if old not in t:
        raise SystemExit('constants insertion point missing')
    t = t.replace(old, new, 1)

anchor = 'def git_text(ref: str, path: str) -> str:\n'
helper = '''def load_proof_invalidations(path: Path = DEFAULT_INVALIDATIONS) -> dict[str, dict[str, Any]]:\n    if not path.exists():\n        return {}\n    doc = load(path)\n    if int(doc.get("schemaVersion") or 0) != 1:\n        raise ValueError("proof invalidation schemaVersion must be 1")\n    if doc.get("authority") != "provider-proof-invalidation-v1":\n        raise ValueError("proof invalidation authority mismatch")\n    raw = doc.get("providers")\n    if not isinstance(raw, dict):\n        raise ValueError("proof invalidation providers must be an object")\n    out: dict[str, dict[str, Any]] = {}\n    for raw_pid, raw_row in raw.items():\n        pid = canon(raw_pid)\n        if not pid or not isinstance(raw_row, dict):\n            raise ValueError("proof invalidation provider row invalid")\n        if raw_row.get("active") is not True:\n            continue\n        lanes = sorted({canon(x) for x in raw_row.get("invalidatedLanes") or [] if canon(x)})\n        reasons = [canon(x) for x in raw_row.get("reasonCodes") or [] if canon(x)]\n        refs = [str(x).strip() for x in raw_row.get("evidenceRefs") or [] if str(x).strip()]\n        authority = canon(raw_row.get("contradictionAuthority"))\n        invalidate_positive = raw_row.get("invalidateProviderPositive") is True\n        if not lanes:\n            raise ValueError(f"{pid}: active proof invalidation must name lanes")\n        if not authority or not reasons or len(refs) < 2:\n            raise ValueError(f"{pid}: proof invalidation requires contradiction authority, reasons, and >=2 evidence refs")\n        if invalidate_positive and "cross_fixture_identity_collision" not in reasons:\n            raise ValueError(f"{pid}: provider-positive invalidation requires cross_fixture_identity_collision")\n        row = dict(raw_row)\n        row["invalidatedLanes"] = lanes\n        row["reasonCodes"] = reasons\n        row["evidenceRefs"] = refs\n        row["contradictionAuthority"] = authority\n        row["invalidateProviderPositive"] = invalidate_positive\n        out[pid] = row\n    return out\n\n\ndef invalidated_lanes_for(invalidations: dict[str, dict[str, Any]], provider_id: str) -> set[str]:\n    row = invalidations.get(canon(provider_id))\n    if not isinstance(row, dict):\n        return set()\n    return {canon(x) for x in row.get("invalidatedLanes") or [] if canon(x)}\n\n\n'''
if 'def load_proof_invalidations(' not in t:
    if anchor not in t:
        raise SystemExit('helper insertion point missing')
    t = t.replace(anchor, helper + anchor, 1)

old = '    activation_debt = current_activation_debt()\n\n    obligations: dict[str, Any] = {}'
new = '    activation_debt = current_activation_debt()\n    invalidations = load_proof_invalidations()\n\n    obligations: dict[str, Any] = {}'
if 'invalidations = load_proof_invalidations()' not in t:
    if old not in t:
        raise SystemExit('candidate invalidation insertion point missing')
    t = t.replace(old, new, 1)

old = '''        historical_specific = {canon(x) for x in row.get("historicalVerifiedLanes") or [] if canon(x)}\n        rolling = set(baseline_lanes.get(pid) or set())\n        required_lanes = historical_specific | rolling\n        got = set(candidate_lanes.get(pid) or set())'''
new = '''        invalidation = invalidations.get(pid) if isinstance(invalidations.get(pid), dict) else {}\n        invalidated_lanes = invalidated_lanes_for(invalidations, pid)\n        historical_specific_raw = {canon(x) for x in row.get("historicalVerifiedLanes") or [] if canon(x)}\n        rolling_raw = set(baseline_lanes.get(pid) or set())\n        historical_specific = historical_specific_raw - invalidated_lanes\n        rolling = rolling_raw - invalidated_lanes\n        required_lanes = historical_specific | rolling\n        provider_positive_invalidated = bool(invalidation.get("invalidateProviderPositive"))\n        got = set(candidate_lanes.get(pid) or set())'''
if 'historical_specific_raw' not in t:
    if old not in t:
        raise SystemExit('candidate floor replacement point missing')
    t = t.replace(old, new, 1)

old = '        require_any = historical_positive and not required_lanes\n'
new = '        require_any = historical_positive and not required_lanes and not provider_positive_invalidated\n'
if 'not provider_positive_invalidated' not in t:
    if old not in t:
        raise SystemExit('require_any replacement point missing')
    t = t.replace(old, new, 1)

old = '''            "historicalPositiveVersions": historical_positive_versions,\n            "historicalVerifiedLanes": sorted(historical_specific),\n            "rollingAcceptedLanes": sorted(rolling),'''
new = '''            "historicalPositiveVersions": historical_positive_versions,\n            "proofInvalidationApplied": bool(invalidation),\n            "proofInvalidationAuthority": invalidation.get("contradictionAuthority") if isinstance(invalidation, dict) else None,\n            "proofInvalidationReasons": invalidation.get("reasonCodes") if isinstance(invalidation, dict) else [],\n            "invalidatedVerifiedLanes": sorted(invalidated_lanes),\n            "providerPositiveInvalidated": provider_positive_invalidated,\n            "historicalVerifiedLanesRaw": sorted(historical_specific_raw),\n            "historicalVerifiedLanes": sorted(historical_specific),\n            "rollingAcceptedLanesRaw": sorted(rolling_raw),\n            "rollingAcceptedLanes": sorted(rolling),'''
if '"proofInvalidationApplied"' not in t:
    if old not in t:
        raise SystemExit('obligation audit insertion point missing')
    t = t.replace(old, new, 1)

old = '''        "historicalFloorSource": "automation/provider-history-matrix.json schema v3",\n        "candidateSource": str(DEFAULT_CANDIDATE.relative_to(ROOT)),'''
new = '''        "historicalFloorSource": "automation/provider-history-matrix.json schema v3",\n        "proofInvalidationSource": str(DEFAULT_INVALIDATIONS.relative_to(ROOT)),\n        "proofInvalidationPolicy": "only active, evidence-backed contradiction records may remove invalidated historical/rolling lanes from the candidate floor; all other floors remain unchanged",\n        "candidateSource": str(DEFAULT_CANDIDATE.relative_to(ROOT)),'''
if '"proofInvalidationSource"' not in t:
    if old not in t:
        raise SystemExit('return audit insertion point missing')
    t = t.replace(old, new, 1)

p.write_text(t, encoding='utf-8')
print('PROVIDER_PROOF_INVALIDATION_PATCH_OK')
