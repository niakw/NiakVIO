#!/usr/bin/env python3
"""Reactivate lifecycle-disabled providers from fresh exact-byte census proof.

This is a NiakVIO lifecycle transaction, not a provider repair. It can only
re-enable retained bytes when the current canonical census proved every declared
lane against the exact same provider bytes, identity remained contradiction-free,
and the provider's current route authority is unchanged from the tested SHA.

Brain/Learning is intentionally not required when no code mutation is needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "automation/provider-census-status.json"
LIFECYCLE = ROOT / "automation/provider-disabled-lifecycle.json"
LEDGER = ROOT / "automation/provider-disabled-reactivation-ledger.json"
LATEST = ROOT / "automation/provider-disabled-current-census-reactivation-latest.json"

PROOF_AUTHORITY = "current-census-exact-byte-terminal-v1"
SAFE_AUTO_OFF_PREFIXES = (
    "auto_off_current_architecture_regression",
    "auto_off_current_architecture_nonfunctional",
)


class EligibilityError(RuntimeError):
    pass


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def repo_path(filename: object) -> str:
    value = str(filename or "").strip().replace("\\", "/")
    while value.startswith("../"):
        value = value[3:]
    if not value.startswith("provider-disabled/") or ".." in Path(value).parts:
        raise EligibilityError(f"disabled provider path is not repository-safe: {filename!r}")
    return value


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(root: Path, ref: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise EligibilityError(f"tested source file missing at {ref}:{path}")
    return result.stdout


def git_json(root: Path, ref: str, path: str) -> dict[str, Any]:
    try:
        value = json.loads(git_bytes(root, ref, path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EligibilityError(f"tested source JSON invalid at {ref}:{path}") from exc
    if not isinstance(value, dict):
        raise EligibilityError(f"tested source JSON is not an object at {ref}:{path}")
    return value


def require_ancestor(root: Path, ref: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ref, "HEAD"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise EligibilityError(f"census source SHA is not an ancestor of current HEAD: {ref}")


def current_source(root: Path, provider: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    manifest = load(root / "manifest.json", {"scrapers": []})
    for row in manifest.get("scrapers") or []:
        if isinstance(row, dict) and canon(row.get("id")) == provider:
            return "global", row, manifest

    catalog = load(root / "provider_catalog.json", {"providers": []})
    for entry in catalog.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        scraper = entry.get("scraper") if isinstance(entry.get("scraper"), dict) else {}
        projections = entry.get("projections") if isinstance(entry.get("projections"), dict) else {}
        if canon(entry.get("canonicalId") or scraper.get("id")) != provider:
            continue
        if projections.get("general") is False and projections.get("vf") is True:
            return "france", scraper, catalog
        raise EligibilityError(f"{provider}: catalogue identity is not Global or France-only")
    raise EligibilityError(f"{provider}: provider is absent from current catalogue")


def tested_source_row(root: Path, trigger_sha: str, scope: str, provider: str) -> dict[str, Any]:
    path = "manifest.json" if scope == "global" else "vf/manifest.json"
    doc = git_json(root, trigger_sha, path)
    for row in doc.get("scrapers") or []:
        if isinstance(row, dict) and canon(row.get("id")) == provider:
            return row
    raise EligibilityError(f"{provider}: provider absent from tested {path}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def tested_provider_authority(
    root: Path,
    trigger_sha: str,
    provider: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tested_overrides = git_json(root, trigger_sha, "provider-overrides.json")
    tested_hubs = git_json(root, trigger_sha, "provider-hubs.json")
    patch = (tested_overrides.get("provider_patches") or {}).get(provider)
    registry = (tested_hubs.get("providers") or {}).get(provider)
    return (
        patch if isinstance(patch, dict) else {},
        registry if isinstance(registry, dict) else {},
    )


def current_provider_authority(
    root: Path,
    provider: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    overrides = load(root / "provider-overrides.json", {"provider_patches": {}})
    hubs = load(root / "provider-hubs.json", {"providers": {}})
    patches = overrides.setdefault("provider_patches", {})
    registries = hubs.setdefault("providers", {})
    patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
    registry = registries.get(provider) if isinstance(registries.get(provider), dict) else {}
    return patch, registry, overrides, hubs


def declared_lanes(row: dict[str, Any]) -> set[str]:
    raw = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    if isinstance(raw, str):
        raw = [raw]
    return {canon(value) for value in raw if canon(value) in {"movie", "tv", "anime"}}


def lane_verdicts(row: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in row.get("latestLaneVerdicts") or []:
        text = str(raw or "")
        if "=" not in text:
            continue
        lane, verdict = text.split("=", 1)
        out[canon(lane)] = verdict.strip()
    return out


def route_authority(patch: dict[str, Any], declared: set[str]) -> tuple[bool, list[str]]:
    route = patch.get("route_proof") if isinstance(patch.get("route_proof"), dict) else {}
    live = patch.get("live_route_gate") if isinstance(patch.get("live_route_gate"), dict) else {}
    canonical = (
        route.get("canonicalExecutionAuthority")
        if isinstance(route.get("canonicalExecutionAuthority"), dict)
        else {}
    )
    validated = {canon(v) for v in live.get("validated_types") or [] if canon(v)}
    covered = {canon(v) for v in canonical.get("coveredLanes") or [] if canon(v)}
    missing = {canon(v) for v in canonical.get("missingLanes") or [] if canon(v)}
    ok = (
        route.get("authority") == "observed-provider-http-request"
        and live.get("completion_state") == "declared-types-qualified"
        and bool(declared)
        and declared <= validated
        and not missing
        and declared <= covered
        and canonical.get("allEvidenceBackedAuthoritiesPreserved") is True
    )
    return ok, sorted(validated & declared)


def census_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    status = load(root / "automation/provider-census-status.json")
    run_id = str(status.get("runId") or "").strip()
    trigger_sha = str(status.get("triggerSha") or "").strip().casefold()
    if not run_id.isdigit() or len(trigger_sha) != 40:
        raise EligibilityError("canonical census is missing runId/triggerSha")
    summary = load(root / f"automation/current-bytes-full-provider-census-{run_id}-summary.json")
    raw = load(root / f"automation/current-bytes-full-provider-census-{run_id}.json")
    if str(summary.get("runId") or "") != run_id:
        raise EligibilityError("census summary runId mismatch")
    if str(summary.get("triggerSha") or "").casefold() != trigger_sha:
        raise EligibilityError("census summary trigger SHA mismatch")
    if int(raw.get("schema_version") or 0) < 6:
        raise EligibilityError("current-byte raw census schema is too old")
    return status, summary, raw


def status_row(status: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row for row in status.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider")) == provider
    ]
    if len(rows) != 1:
        raise EligibilityError(f"{provider}: expected one canonical census row, got {len(rows)}")
    return rows[0]


def validate_terminal_census(
    provider: str,
    declared: set[str],
    status: dict[str, Any],
    summary: dict[str, Any],
    raw: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    row = status_row(status, provider)
    if row.get("testedThisRun") is not True:
        raise EligibilityError(f"{provider}: census row was not tested this run")
    verified = {canon(v) for v in row.get("currentVerifiedLanes") or [] if canon(v)}
    if not declared or not declared <= verified:
        raise EligibilityError(
            f"{provider}: declared lanes not freshly verified "
            f"declared={sorted(declared)} verified={sorted(verified)}"
        )
    verdicts = lane_verdicts(row)
    if any(verdicts.get(lane) != "OK" for lane in declared):
        raise EligibilityError(f"{provider}: one or more declared lanes lacks an OK verdict")
    if str(row.get("dominantIssue") or "").strip().casefold() not in {"", "none"}:
        raise EligibilityError(f"{provider}: census still reports dominant issue {row.get('dominantIssue')}")
    if row.get("brainCheckRequired") is True:
        raise EligibilityError(f"{provider}: census still requires Brain diagnosis")

    verified_providers = {canon(v) for v in summary.get("verifiedProviders") or [] if canon(v)}
    wrong = {canon(v) for v in summary.get("wrongContentProviders") or [] if canon(v)}
    if provider not in verified_providers or provider in wrong:
        raise EligibilityError(f"{provider}: provider is not in the fresh strict verified set")

    provider_rows = [
        item for item in raw.get("rows") or []
        if isinstance(item, dict) and canon(item.get("provider_id")) == provider
    ]
    if not provider_rows:
        raise EligibilityError(f"{provider}: raw census rows are missing")
    if any(
        str(item.get("status") or "") == "wrong_content"
        or int(item.get("contradictions") or 0) != 0
        or item.get("identity_safe") is False
        for item in provider_rows
    ):
        raise EligibilityError(f"{provider}: raw census contains identity/content contradiction")

    lane_evidence: dict[str, list[dict[str, Any]]] = {}
    for lane in sorted(declared):
        positive = [
            item for item in provider_rows
            if canon(item.get("semantic_type")) == lane
            and str(item.get("status") or "") == "playable_verified"
            and int(item.get("verified") or 0) > 0
            and int(item.get("contradictions") or 0) == 0
            and item.get("identity_safe") is not False
        ]
        if not positive:
            raise EligibilityError(f"{provider}: no strict playable_verified raw row for lane {lane}")
        lane_evidence[lane] = [
            {
                "fixture": item.get("fixture"),
                "verified": int(item.get("verified") or 0),
                "qualityHeights": list(item.get("announced_quality_heights") or [])[:8],
            }
            for item in positive[:3]
        ]
    return lane_evidence


def validate_candidate(root: Path, provider: str) -> dict[str, Any]:
    provider = canon(provider)
    status, summary, raw = census_inputs(root)
    trigger_sha = str(status.get("triggerSha") or "").strip().casefold()
    run_id = str(status.get("runId") or "").strip()
    require_ancestor(root, trigger_sha)

    scope, row, _doc = current_source(root, provider)
    if row.get("enabled") is not False:
        raise EligibilityError(f"{provider}: provider is already active")
    if str(row.get("lifecycleState") or "") != "disabled-retained":
        raise EligibilityError(f"{provider}: provider is not disabled-retained")

    lifecycle = load(root / "automation/provider-disabled-lifecycle.json", {"disabled": {}})
    record = (lifecycle.get("disabled") or {}).get(provider)
    if not isinstance(record, dict) or str(record.get("state") or "") != "disabled-retained":
        raise EligibilityError(f"{provider}: lifecycle retention record is missing")
    reason = str(record.get("reason") or row.get("disabledReason") or "").strip()
    if not any(reason.startswith(prefix) for prefix in SAFE_AUTO_OFF_PREFIXES):
        raise EligibilityError(
            f"{provider}: disable reason is not automatic architecture recovery debt: {reason}"
        )
    if str(row.get("disabledReason") or reason).strip() != reason:
        raise EligibilityError(f"{provider}: manifest/lifecycle disable reason disagreement")

    declared = declared_lanes(row)
    evidence = validate_terminal_census(provider, declared, status, summary, raw)

    tested_row = tested_source_row(root, trigger_sha, scope, provider)
    if tested_row.get("enabled") is not False:
        raise EligibilityError(f"{provider}: tested source row was not disabled")
    if declared_lanes(tested_row) != declared:
        raise EligibilityError(f"{provider}: declared lanes drifted since census")

    current_path = repo_path(row.get("filename"))
    tested_path = repo_path(tested_row.get("filename"))
    if current_path != tested_path:
        raise EligibilityError(f"{provider}: provider artifact path drifted since census")
    current_asset = root / current_path
    if not current_asset.is_file():
        raise EligibilityError(f"{provider}: current disabled provider bytes are missing")
    current_digest = sha256(current_asset.read_bytes())
    tested_digest = sha256(git_bytes(root, trigger_sha, tested_path))
    if current_digest != tested_digest:
        raise EligibilityError(f"{provider}: current disabled bytes drifted from exact census source")

    patch, registry, _overrides, _hubs = current_provider_authority(root, provider)
    tested_patch, tested_registry = tested_provider_authority(root, trigger_sha, provider)
    if canonical_json(patch) != canonical_json(tested_patch):
        raise EligibilityError(f"{provider}: provider execution authority drifted since census")
    if canonical_json(registry) != canonical_json(tested_registry):
        raise EligibilityError(f"{provider}: provider hub/domain authority drifted since census")
    if str(patch.get("manual_off_reason") or registry.get("manual_off_reason") or "").strip():
        raise EligibilityError(f"{provider}: manual disable authority blocks automatic reactivation")
    authority_ok, authority_lanes = route_authority(patch, declared)
    if not authority_ok:
        raise EligibilityError(
            f"{provider}: current route authority does not cover every declared lane"
        )

    return {
        "provider": provider,
        "scope": scope,
        "proofAuthority": PROOF_AUTHORITY,
        "proofStatus": "terminal_identity_verified",
        "sourceKind": "current-bytes-census",
        "sourceRunId": run_id,
        "sourceSha": trigger_sha,
        "providerArtifactSha256": current_digest,
        "declaredLanes": sorted(declared),
        "verifiedLanes": sorted(declared),
        "testedThisRun": True,
        "verifiedRowCount": sum(len(rows) for rows in evidence.values()),
        "identityContradictionCount": 0,
        "wrongContent": False,
        "repairRequired": False,
        "directMutationAuthority": False,
        "routeAuthorityVerified": True,
        "routeValidatedLanes": authority_lanes,
        "laneEvidence": evidence,
        "disabledReason": reason,
    }


def apply_proofs(root: Path, proofs: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = load(root / "manifest.json", {"scrapers": []})
    catalog = load(root / "provider_catalog.json", {"providers": []})
    overrides = load(root / "provider-overrides.json", {"provider_patches": {}})
    hubs = load(root / "provider-hubs.json", {"providers": {}})
    ledger = load(
        root / "automation/provider-disabled-reactivation-ledger.json",
        {
            "schemaVersion": 1,
            "authority": "provider-disabled-reactivation-ledger-v1",
            "providers": {},
        },
    )
    ledger["schemaVersion"] = 1
    ledger["authority"] = "provider-disabled-reactivation-ledger-v1"
    ledger_rows = ledger.setdefault("providers", {})

    manifest_rows = {
        canon(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id"))
    }
    catalog_entries = {
        canon(entry.get("canonicalId") or (entry.get("scraper") or {}).get("id")): entry
        for entry in catalog.get("providers") or []
        if isinstance(entry, dict)
    }
    patches = overrides.setdefault("provider_patches", {})
    registries = hubs.setdefault("providers", {})

    applied: list[str] = []
    for proof in proofs:
        provider = canon(proof.get("provider"))
        scope = str(proof.get("scope") or "")
        if scope == "global":
            row = manifest_rows.get(provider)
        elif scope == "france":
            entry = catalog_entries.get(provider)
            row = (
                entry.get("scraper")
                if isinstance(entry, dict) and isinstance(entry.get("scraper"), dict)
                else None
            )
        else:
            row = None
        if not isinstance(row, dict) or row.get("enabled") is not False:
            raise RuntimeError(f"{provider}: activation source row changed after validation")

        row["enabled"] = True
        patch = patches.setdefault(provider, {})
        manifest_overrides = (
            patch.get("manifest_overrides")
            if isinstance(patch.get("manifest_overrides"), dict)
            else {}
        )
        manifest_overrides.pop("enabled", None)
        if manifest_overrides:
            patch["manifest_overrides"] = manifest_overrides
        else:
            patch.pop("manifest_overrides", None)
        if patch.get("route_data_state") == "off":
            patch.pop("route_data_state", None)
        if patch.get("activation_eligible") is False:
            patch.pop("activation_eligible", None)
        patch["disabled_reactivation_proof"] = dict(proof)

        registry = registries.get(provider) if isinstance(registries.get(provider), dict) else {}
        if str(registry.get("manifest_status") or "").strip().casefold() in {
            "désactivé", "desactive", "disabled", "inactif", "inactive"
        }:
            registry["manifest_status"] = "Active"
        if registry.get("activation_eligible") is False:
            registry.pop("activation_eligible", None)
        registries[provider] = registry

        ledger_rows[provider] = dict(proof)
        applied.append(provider)

    dump(root / "manifest.json", manifest)
    dump(root / "provider_catalog.json", catalog)
    dump(root / "provider-overrides.json", overrides)
    dump(root / "provider-hubs.json", hubs)
    dump(root / "automation/provider-disabled-reactivation-ledger.json", ledger)
    return {"applied": sorted(applied), "proofs": proofs}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--receipt", type=Path, default=LATEST)
    args = parser.parse_args()

    lifecycle = load(LIFECYCLE, {"disabled": {}})
    available = sorted(canon(key) for key in (lifecycle.get("disabled") or {}) if canon(key))
    requested = {canon(value) for value in args.provider if canon(value)}
    candidates = [provider for provider in available if not requested or provider in requested]
    missing = sorted(requested - set(available))
    if missing:
        raise SystemExit("requested disabled provider(s) missing: " + ",".join(missing))

    proofs: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    for provider in candidates:
        try:
            proofs.append(validate_candidate(ROOT, provider))
        except EligibilityError as exc:
            blocked.append({"provider": provider, "reason": str(exc)})

    status = load(STATUS, {})
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "authority": PROOF_AUTHORITY,
        "sourceCensusRunId": str(status.get("runId") or ""),
        "sourceCensusSha": str(status.get("triggerSha") or ""),
        "eligible": [proof["provider"] for proof in proofs],
        "blocked": blocked,
        "applied": [],
    }
    if args.apply and proofs:
        applied = apply_proofs(ROOT, proofs)
        result["applied"] = applied["applied"]
    if args.receipt:
        receipt = args.receipt if args.receipt.is_absolute() else ROOT / args.receipt
        dump(receipt, result)

    print(
        "FIELD_DISABLED_CURRENT_CENSUS_REACTIVATION "
        f"eligible={len(proofs)} applied={len(result['applied'])} blocked={len(blocked)} "
        f"providers={','.join(result['applied'] or result['eligible']) or '-'}"
    )
    if requested and not proofs:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
