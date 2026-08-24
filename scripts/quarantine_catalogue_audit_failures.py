#!/usr/bin/env python3
"""Apply publication-scoped catalogue audit quarantines without killing valid scopes.

A playback failure/unknown result is never a quarantine decision: it remains a
Repair observation. Only a *playable identity contradiction* can be quarantined.
The quarantine is as narrow as the evidence permits:

* an impossible-ID false positive blocks that media type (the resolver proved it
  can return arbitrary playable content for that type);
* a contradiction on a real title blocks only that exact fixture;
* two or more distinct contradictory fixtures of the same media type escalate
  to a media-type quarantine;
* the provider is disabled only when no declared media type remains usable.

These quarantines are publication-scoped and recoverable on a later Quick when a
new sibling earns fresh strict proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
HEALTH_REPORT = ROOT / "health-report.json"
BLOCKER = "catalogue_audit_playable_identity_contradiction"
SCOPED_MARKER = "NUVIO_CATALOGUE_SCOPE_QUARANTINE_V1"

FIXTURE_SCOPE: dict[str, dict[str, Any]] = {
    "kdrama_squid_game_s01e01": {"mediaType": "tv", "tmdbId": "93405", "season": 1, "episode": 1},
    "vf_revenant_s01e01": {"mediaType": "tv", "tmdbId": "126485", "season": 1, "episode": 1},
    "vf_mushoku_s01e01": {"mediaType": "anime", "tmdbId": "94664", "season": 1, "episode": 1},
    "impossible_movie": {"mediaType": "movie", "tmdbId": "999999999"},
    "strict_movie_identity": {"mediaType": "movie", "tmdbId": "1215638"},
    "vf_jjk_s01e01": {"mediaType": "tv", "tmdbId": "95479", "season": 1, "episode": 1},
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bump_patch(value: Any) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.casefold()).strip(".-") or "provider"


def conclusive_rows(audit: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return identity contradictions only; playback/HLS failures stay in Repair."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in audit.get("rows") or []:
        if not isinstance(row, dict):
            continue
        wrong = int(row.get("identity_contradiction_count") or 0) > 0
        false_positive = row.get("playable_identity_false_positive") is True
        if not (wrong or false_positive):
            continue
        if int(row.get("playable_stream_count") or 0) <= 0:
            continue
        provider_id = str(row.get("provider_id") or "").strip().casefold()
        if provider_id:
            grouped.setdefault(provider_id, []).append(row)
    return grouped


def derive_scopes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive the narrowest safe quarantine scopes from conclusive evidence."""
    scopes: list[dict[str, Any]] = []
    exact_by_type: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        fixture_name = str(row.get("fixture") or "")
        fixture = FIXTURE_SCOPE.get(fixture_name)
        if not fixture:
            continue
        media_type = str(fixture.get("mediaType") or "").casefold()
        if not media_type:
            continue
        if fixture_name.startswith("impossible_") or row.get("playable_identity_false_positive") is True:
            scopes.append({
                "kind": "media_type",
                "mediaType": media_type,
                "reason": "playable_unknown_identity_false_positive",
            })
            continue
        exact = {
            "kind": "fixture",
            "fixture": fixture_name,
            "mediaType": media_type,
            "tmdbId": str(fixture.get("tmdbId") or ""),
            "reason": "playable_identity_contradiction",
        }
        if fixture.get("season") is not None:
            exact["season"] = int(fixture["season"])
        if fixture.get("episode") is not None:
            exact["episode"] = int(fixture["episode"])
        scopes.append(exact)
        exact_by_type[media_type].add(exact["tmdbId"])

    # Multiple independent real-title contradictions for one type justify a
    # type-wide quarantine. One title never does.
    for media_type, ids in exact_by_type.items():
        if len(ids) >= 2:
            scopes = [
                scope for scope in scopes
                if not (scope.get("kind") == "fixture" and scope.get("mediaType") == media_type)
            ]
            scopes.append({
                "kind": "media_type",
                "mediaType": media_type,
                "reason": "repeated_playable_identity_contradiction",
            })

    # A media-type scope dominates exact scopes of the same type.
    blocked_types = {
        str(scope.get("mediaType") or "")
        for scope in scopes
        if scope.get("kind") == "media_type"
    }
    scopes = [
        scope for scope in scopes
        if scope.get("kind") == "media_type"
        or str(scope.get("mediaType") or "") not in blocked_types
    ]

    unique: dict[str, dict[str, Any]] = {}
    for scope in scopes:
        key = json.dumps(scope, sort_keys=True, separators=(",", ":"))
        unique[key] = scope
    return sorted(
        unique.values(),
        key=lambda scope: (
            str(scope.get("mediaType") or ""),
            0 if scope.get("kind") == "media_type" else 1,
            str(scope.get("tmdbId") or ""),
        ),
    )


def scoped_quarantine_source(source: str, provider_id: str, scopes: list[dict[str, Any]]) -> str:
    """Append a getStreams wrapper that returns [] only for proven-bad scopes."""
    encoded = json.dumps(scopes, ensure_ascii=True, separators=(",", ":"))
    provider = json.dumps(provider_id, ensure_ascii=True)
    return source + f"""

/* {SCOPED_MARKER}: provider={provider_id} */
;(function() {{
  const __nuvioScopedRules = {encoded};
  const __nuvioScopedProvider = {provider};
  const __nuvioExports = (typeof module !== 'undefined' && module && module.exports) ? module.exports : null;
  const __nuvioOriginal = (__nuvioExports && typeof __nuvioExports.getStreams === 'function')
    ? __nuvioExports.getStreams
    : (typeof globalThis !== 'undefined' && typeof globalThis.getStreams === 'function' ? globalThis.getStreams : null);
  if (typeof __nuvioOriginal !== 'function') return;

  function __nuvioInvocation(args) {{
    const first = args[0];
    if (first && typeof first === 'object' && !Array.isArray(first)) {{
      return {{
        tmdbId: String(first.tmdbId ?? first.id ?? ''),
        mediaType: String(first.mediaType ?? first.type ?? first.category ?? '').toLowerCase(),
        season: first.season == null ? null : Number(first.season),
        episode: first.episode == null ? null : Number(first.episode),
      }};
    }}
    return {{
      tmdbId: String(first ?? ''),
      mediaType: String(args[1] ?? '').toLowerCase(),
      season: args[2] == null ? null : Number(args[2]),
      episode: args[3] == null ? null : Number(args[3]),
    }};
  }}

  function __nuvioMatches(rule, request) {{
    if (String(rule.mediaType || '').toLowerCase() !== request.mediaType) return false;
    if (rule.kind === 'media_type') return true;
    if (String(rule.tmdbId || '') !== request.tmdbId) return false;
    if (rule.season != null && Number(rule.season) !== request.season) return false;
    if (rule.episode != null && Number(rule.episode) !== request.episode) return false;
    return true;
  }}

  async function __nuvioScopedGetStreams(...args) {{
    const request = __nuvioInvocation(args);
    if (__nuvioScopedRules.some((rule) => __nuvioMatches(rule, request))) return [];
    return await __nuvioOriginal.apply(this, args);
  }}
  try {{ if (__nuvioExports && typeof __nuvioExports === 'object') __nuvioExports.getStreams = __nuvioScopedGetStreams; }} catch {{}}
  try {{ if (typeof globalThis !== 'undefined') globalThis.getStreams = __nuvioScopedGetStreams; }} catch {{}}
  try {{ if (typeof global !== 'undefined') global.getStreams = __nuvioScopedGetStreams; }} catch {{}}
  try {{ if (typeof self !== 'undefined') self.getStreams = __nuvioScopedGetStreams; }} catch {{}}
  try {{ if (typeof globalThis !== 'undefined') globalThis.__NUVIO_CATALOGUE_SCOPE_QUARANTINE__ = {{ provider: __nuvioScopedProvider, rules: __nuvioScopedRules }}; }} catch {{}}
}})();
"""


def _remaining_types(entry: dict[str, Any], scopes: list[dict[str, Any]]) -> list[str]:
    values = entry.get("supportedTypes") or []
    if isinstance(values, str):
        values = [values]
    declared = [str(value).strip().casefold() for value in values if str(value).strip()]
    blocked = {
        str(scope.get("mediaType") or "").casefold()
        for scope in scopes
        if scope.get("kind") == "media_type"
    }
    return [value for value in declared if value not in blocked]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--evidence")
    parser.add_argument("--workflow-run-id", type=int, default=0)
    parser.add_argument("--tested-commit-sha", default="")
    # Temporary CLI compatibility for in-flight Deep workflows created before the canonical audit migration.
    parser.add_argument("--manifest", help=argparse.SUPPRESS)
    parser.add_argument("--overrides", help=argparse.SUPPRESS)
    args = parser.parse_args()

    audit = load(Path(args.audit).resolve())
    failures = conclusive_rows(audit)
    if not failures:
        print("catalogue audit quarantine: no conclusive identity failures")
        return 0

    manifest = load(MANIFEST)
    provenance = load(PROVENANCE)
    health = load(HEALTH_REPORT)
    manifest_rows = {
        str(row.get("id") or "").strip().casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    provenance_rows = provenance.setdefault("providers", {})
    if not isinstance(provenance_rows, dict):
        raise ValueError("PROVENANCE providers must be an object")
    health_rows = {
        str(row.get("id") or "").strip().casefold(): row
        for row in health.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    missing_manifest = sorted(set(failures) - set(manifest_rows))
    missing_health = sorted(set(failures) - set(health_rows))
    if missing_manifest:
        raise SystemExit("audit quarantine providers missing from manifest: " + ", ".join(missing_manifest))
    if missing_health:
        raise SystemExit("audit quarantine providers missing from health report: " + ", ".join(missing_health))

    referenced_before = {
        str(row.get("filename") or "")
        for row in manifest_rows.values()
        if str(row.get("filename") or "")
    }
    old_candidates: list[Path] = []
    scoped_count = 0
    disabled_count = 0

    for provider_id, evidence_rows in sorted(failures.items()):
        scopes = derive_scopes(evidence_rows)
        if not scopes:
            print(f"catalogue audit quarantine: {provider_id} has no safely classifiable scope; leaving to Repair")
            continue

        entry = manifest_rows[provider_id]
        old_relative = str(entry.get("filename") or "").strip()
        old_path = (ROOT / old_relative).resolve()
        if not old_relative.startswith("providers/") or not old_path.is_file():
            raise SystemExit(f"{provider_id}: unsafe or missing current bundle: {old_relative}")
        old_sha = file_sha(old_path)
        source = old_path.read_text(encoding="utf-8")
        payload_text = scoped_quarantine_source(source, provider_id, scopes)
        if SCOPED_MARKER not in payload_text:
            raise SystemExit(f"{provider_id}: scoped quarantine marker missing")
        payload = payload_text.encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        new_relative = f"providers/{safe_id(provider_id)}--nuvio-audit-quarantine--{digest[:16]}.js"
        new_path = ROOT / new_relative
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_bytes(payload)

        original_types = entry.get("supportedTypes")
        remaining_types = _remaining_types(entry, scopes)
        if original_types is not None:
            entry["supportedTypes"] = remaining_types
        entry["filename"] = new_relative
        if original_types is not None and not remaining_types:
            entry["enabled"] = False
            disabled_count += 1
        entry["version"] = bump_patch(entry.get("version"))

        fixtures = sorted({str(row.get("fixture") or "") for row in evidence_rows if str(row.get("fixture") or "")})
        identity_contradictions = sum(int(row.get("identity_contradiction_count") or 0) for row in evidence_rows)
        playable_streams = sum(int(row.get("playable_stream_count") or 0) for row in evidence_rows)
        audit_record = {
            "type": "scoped_safety_quarantine",
            "phase": "publication",
            "source": "catalogue_media_audit",
            "reason": BLOCKER,
            "workflow_run_id": int(args.workflow_run_id or 0),
            "tested_commit_sha": str(args.tested_commit_sha or ""),
            "tested_filename": old_relative,
            "tested_sha256": old_sha,
            "fixtures": fixtures,
            "scopes": scopes,
            "identity_contradictions": identity_contradictions,
            "playable_streams": playable_streams,
        }

        provider_provenance = provenance_rows.setdefault(provider_id, {})
        if not isinstance(provider_provenance, dict):
            provider_provenance = {}
            provenance_rows[provider_id] = provider_provenance
        provider_provenance["published_filename"] = new_relative
        provider_provenance["sha256"] = digest
        provider_provenance["patched_sha256"] = digest
        provider_provenance["catalogue_audit_quarantine_scopes"] = scopes
        provider_provenance["activation_mode"] = (
            "catalogue_audit_scoped_quarantine"
            if entry.get("enabled") is not False
            else "catalogue_audit_all_declared_scopes_quarantined"
        )
        local_patches = [
            row for row in list(provider_provenance.get("local_patches") or [])
            if not (
                isinstance(row, dict)
                and row.get("source") == "catalogue_media_audit"
                and row.get("type") in {"safety_quarantine", "scoped_safety_quarantine"}
            )
        ]
        local_patches.append(audit_record)
        provider_provenance["local_patches"] = local_patches
        if entry.get("enabled") is False:
            provider_provenance["activation_eligible"] = False
            provider_provenance["strict_activation_eligible"] = False
            provider_provenance["strict_grace_eligible"] = False
            provider_provenance["historical_quality_grace_eligible"] = False
            provider_provenance["runtime_evidence_eligible"] = False
            blockers = [str(value) for value in provider_provenance.get("activation_blockers") or [] if str(value)]
            if BLOCKER not in blockers:
                blockers.append(BLOCKER)
            provider_provenance["activation_blockers"] = blockers

        health_row = health_rows[provider_id]
        health_row["enabled"] = bool(entry.get("enabled"))
        health_row["action"] = (
            "published-scoped-quarantine"
            if entry.get("enabled") is not False
            else "published-disabled-all-declared-scopes-quarantined"
        )
        health_row["catalogue_audit_quarantine"] = {
            "reason": BLOCKER,
            "tested_filename": old_relative,
            "tested_sha256": old_sha,
            "quarantined_filename": new_relative,
            "quarantined_sha256": digest,
            "fixtures": fixtures,
            "scopes": scopes,
            "identity_contradictions": identity_contradictions,
            "playable_streams": playable_streams,
        }
        if entry.get("enabled") is False:
            failed_gates = [str(value) for value in health_row.get("failed_gates") or [] if str(value)]
            if BLOCKER not in failed_gates:
                failed_gates.append(BLOCKER)
            health_row["failed_gates"] = failed_gates

        old_candidates.append(old_path)
        scoped_count += 1
        scope_text = ",".join(
            f"{scope.get('kind')}:{scope.get('mediaType')}:{scope.get('tmdbId', '*')}"
            for scope in scopes
        )
        print(
            f"catalogue audit scoped quarantine: {provider_id} scopes={scope_text} "
            f"contradictions={identity_contradictions} enabled={entry.get('enabled')} -> {new_relative}"
        )

    write(MANIFEST, manifest)
    write(PROVENANCE, provenance)
    write(HEALTH_REPORT, health)

    subprocess.run(["python", "scripts/generate_language_manifests.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/sync_release_versions.py", "--manifest", "manifest.json"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/prune_unreferenced_providers.py"], cwd=ROOT, check=True)
    subprocess.run(["python", "scripts/validate_language_projection.py"], cwd=ROOT, check=True)

    current_manifest = load(MANIFEST)
    referenced_after = {
        str(row.get("filename") or "")
        for row in current_manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("filename") or "")
    }
    for old_path in old_candidates:
        try:
            relative = old_path.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if relative not in referenced_after and relative in referenced_before and old_path.is_file():
            print(f"catalogue audit scoped quarantine: superseded bundle retained only by non-manifest state: {relative}")

    if args.evidence:
        evidence = Path(args.evidence).resolve()
        subprocess.run([
            "python", "scripts/release_evidence_fence.py", "fingerprint",
            "--manifest", "manifest.json", "--root", ".", "--output", str(evidence),
        ], cwd=ROOT, check=True)

    print(
        f"catalogue audit scoped quarantine complete: providers={scoped_count} "
        f"fully_disabled={disabled_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
