#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'run_provider_upstream_parity_v3.py'
MARKER = 'PARITY_LOCAL_ONLY_UNMATCHED_V1'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding='utf-8')
    if MARKER in text:
        print('PROVIDER_PARITY_LOCAL_ONLY_V1_ALREADY_CURRENT')
        return 0

    anchor = '''def one_provider(\n    provider_id: str,\n    local: dict[str, Any],\n    upstream: dict[str, Any],\n    upstream_path: Path,\n    *,\n    timeout: int,\n    sample_count: int,\n    seed: str,\n) -> dict[str, Any]:\n'''
    insert = '''def run_local_only_lane(\n    provider_id: str,\n    lane: str,\n    local_path: Path,\n    *,\n    timeout: int,\n    sample_count: int,\n    seed: str,\n) -> dict[str, Any]:\n    # PARITY_LOCAL_ONLY_UNMATCHED_V1\n    samples: list[dict[str, Any]] = []\n    candidates = select_fixtures(\n        lane,\n        count=sample_count,\n        seed=seed,\n        provider=provider_id,\n    )\n    for candidate in candidates:\n        local = _run_verified(local_path, fixture_payload(candidate, lane, upstream=False), timeout)\n        positive = int(local.get("stream_count") or 0) > 0 and bool(local.get("terminal_verified"))\n        samples.append({\n            "fixture": candidate["slug"],\n            "tmdbId": str(candidate.get("tmdbId") or ""),\n            "classification": "local_terminal_positive" if positive else (\n                "local_technical_unresolved" if technical(local) else (\n                    "local_candidate_unverified" if int(local.get("candidate_stream_count") or 0) > 0 else "local_catalog_miss"\n                )\n            ),\n            "niakvio": local,\n        })\n        if positive:\n            break\n    if any(row["classification"] == "local_terminal_positive" for row in samples):\n        status = "POSITIVE"\n    elif samples and all(row["classification"] in {"local_catalog_miss", "local_candidate_unverified"} for row in samples):\n        status = "RESAMPLE"\n    else:\n        status = "TECHNICAL_UNRESOLVED"\n    return {\n        "lane": lane,\n        "status": status,\n        "samples": samples,\n        "sampleCount": len(samples),\n        "candidateCount": len(candidates),\n    }\n\n\ndef one_unmatched_provider(\n    provider_id: str,\n    local: dict[str, Any],\n    *,\n    timeout: int,\n    sample_count: int,\n    seed: str,\n) -> dict[str, Any]:\n    lanes = canonical_lanes(local["entry"], {})\n    lane_rows = [\n        run_local_only_lane(\n            provider_id, lane, local["path"],\n            timeout=timeout, sample_count=sample_count, seed=seed,\n        )\n        for lane in lanes\n    ]\n    states = [row["status"] for row in lane_rows]\n    if states and all(value == "POSITIVE" for value in states):\n        status = "UNMATCHED_FULL"\n    elif "POSITIVE" in states:\n        status = "UNMATCHED_PARTIAL"\n    elif states and all(value == "RESAMPLE" for value in states):\n        status = "UNMATCHED_RESAMPLE"\n    else:\n        status = "UNMATCHED_ZERO"\n    return {\n        "providerId": provider_id,\n        "upstreamSource": None,\n        "comparisonMode": "local-only-no-upstream",\n        "status": status,\n        "lanes": lane_rows,\n    }\n\n\n''' + anchor
    text = replace_once(text, anchor, insert, 'local-only functions')

    old_scope = '''    requested = {cid(value) for value in args.provider if cid(value)}\n    provider_ids = [\n        pid for pid in sorted(local)\n        if pid in upstreams and (not requested or pid in requested)\n    ]\n'''
    new_scope = '''    requested = {cid(value) for value in args.provider if cid(value)}\n    accounting_scope = [pid for pid in sorted(local) if not requested or pid in requested]\n    provider_ids = [\n        pid for pid in accounting_scope\n        if pid in upstreams\n    ]\n'''
    text = replace_once(text, old_scope, new_scope, 'targeted accounting scope')

    old_missing = '''    missing_upstream = sorted(\n        pid for pid in local\n        if pid not in upstreams and (not requested or pid in requested)\n    )\n'''
    new_missing = '''    missing_upstream = sorted(\n        pid for pid in accounting_scope\n        if pid not in upstreams\n    )\n'''
    text = replace_once(text, old_missing, new_missing, 'missing upstream scope')

    old = '''    rows.sort(key=lambda row: str(row.get("providerId") or ""))\n    counts = Counter(str(row.get("status") or "UNKNOWN") for row in rows)\n'''
    new = '''    # Every selected provider must have an auditable row. Providers without an\n    # upstream authority are evaluated locally instead of disappearing from the\n    # status denominator (Kehflix exposed this blind spot).\n    for provider_id in missing_upstream:\n        try:\n            rows.append(one_unmatched_provider(\n                provider_id,\n                local[provider_id],\n                timeout=max(5, args.timeout),\n                sample_count=sample_count,\n                seed=seed,\n            ))\n        except Exception as exc:\n            rows.append({\n                "providerId": provider_id,\n                "upstreamSource": None,\n                "comparisonMode": "local-only-no-upstream",\n                "status": "HARNESS_ERROR",\n                "error": f"{type(exc).__name__}: {exc}"[:240],\n                "lanes": [],\n            })\n\n    rows.sort(key=lambda row: str(row.get("providerId") or ""))\n    counts = Counter(str(row.get("status") or "UNKNOWN") for row in rows)\n'''
    text = replace_once(text, old, new, 'append unmatched rows')

    old_payload = '''        "scopeProviderCount": len(scoped),\n        "matchedUpstreamProviders": len(provider_ids),\n        "testedProviders": len(rows),\n        "samplesPerLane": sample_count,\n'''
    new_payload = '''        "scopeProviderCount": len(scoped),\n        "selectedProviderCount": len(accounting_scope),\n        "matchedUpstreamProviders": len(provider_ids),\n        "testedProviders": len(rows),\n        "accountedProviders": len(rows),\n        "localOnlyProviders": len(missing_upstream),\n        "allSelectedProvidersAccounted": len(rows) == len(accounting_scope),\n        "allScopedProvidersAccounted": (not requested) and len(rows) == len(scoped),\n        "samplesPerLane": sample_count,\n'''
    text = replace_once(text, old_payload, new_payload, 'coverage payload')

    old_print = '''        f"scope={len(scoped)} matched={len(provider_ids)} tested={len(rows)} "\n        f"missing_upstream={len(missing_upstream)} downloads_failed={len(download_errors)} samples_per_lane={sample_count}"\n'''
    new_print = '''        f"scope={len(scoped)} selected={len(accounting_scope)} matched={len(provider_ids)} "\n        f"accounted={len(rows)} tested={len(rows)} missing_upstream={len(missing_upstream)} "\n        f"local_only={len(missing_upstream)} downloads_failed={len(download_errors)} samples_per_lane={sample_count}"\n'''
    text = replace_once(text, old_print, new_print, 'coverage print')

    old_return = '''    return 0 if rows else 2\n'''
    new_return = '''    if len(rows) != len(accounting_scope):\n        raise SystemExit(\n            f"Provider parity accounting failure accounted={len(rows)} expected={len(accounting_scope)}"\n        )\n    return 0 if rows else 2\n'''
    text = replace_once(text, old_return, new_return, 'accounting invariant')

    TARGET.write_text(text, encoding='utf-8')
    print('PROVIDER_PARITY_LOCAL_ONLY_V1_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
