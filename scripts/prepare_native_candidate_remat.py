#!/usr/bin/env python3
"""Source-pinned ephemeral ProviderBase candidate; never a published/Brain repair."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "NIAKVIO_PROVIDER_NATIVE_PLAYER_HEDGE_V27"
# Additional causal signatures are only source-owned generic Core/ProviderBase
# mechanisms. The caller cannot substitute provider-specific executable code.
REQUIRED_MARKERS = {
    "",
    "NIAKVIO_HLS_TS_WRAPPED_AAC_RENDITION_V20",
    "NIAKVIO_PROVIDER_NATIVE_FETCH_CAPABILITY_GATE_V28",
    "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29",
    "NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30",
    "NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31",
}


BRAIN_EXPERIMENT_TYPE = "native-blocking-player-origin-priority"
BRAIN_RUNTIME_SCOPE = "native-blocking-fetch"
BRAIN_MARKER = "NIAKVIO_PROVIDER_NATIVE_BLOCKING_ORIGIN_PRIORITY_EXPERIMENT_V29"
BRAIN_LEDGER = ROOT / "automation" / "brain-native-candidate-experiments.json"
HOST = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
SHA40 = re.compile(r"[a-f0-9]{40}")
SHA64 = re.compile(r"[a-f0-9]{64}")


def _validate_brain_experiment(raw: str, provider: str, source_sha: str | None = None) -> dict:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Brain candidate experiment must be an object")
    if value.get("experimentType") != BRAIN_EXPERIMENT_TYPE:
        raise ValueError("unsupported Brain candidate experiment")
    if str(value.get("providerId") or "").strip().lower() != provider:
        raise ValueError("Brain candidate provider mismatch")
    if value.get("runtimeScope") != BRAIN_RUNTIME_SCOPE:
        raise ValueError("Brain candidate runtime scope mismatch")
    if value.get("candidateOnly") is not True or value.get("generatedByBrain") is not True:
        raise ValueError("Brain candidate provenance missing")
    if any(value.get(flag) is not False for flag in (
        "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
        "providerMutationAuthority",
    )):
        raise ValueError("Brain candidate cannot carry authority")
    evidence_sha = str(value.get("sourceNiakvioSha") or "").strip().lower()
    artifact_sha = str(value.get("providerArtifactSha256") or "").strip().lower()
    run_id = str(value.get("sourceRunId") or "").strip()
    client_sha = str(value.get("officialClientSha") or "").strip().lower()
    if not SHA40.fullmatch(evidence_sha):
        raise ValueError("Brain candidate source NiakVIO SHA invalid")
    if source_sha is not None and evidence_sha != source_sha:
        raise ValueError("explicit Brain candidate must target the exact observed NiakVIO SHA")
    if not SHA64.fullmatch(artifact_sha) or not run_id.isdigit():
        raise ValueError("Brain candidate source provenance invalid")
    if client_sha and not SHA40.fullmatch(client_sha):
        raise ValueError("Brain candidate official client SHA invalid")
    def hosts(key: str) -> list[str]:
        out = []
        for item in value.get(key) or []:
            host = str(item or "").strip().lower().rstrip(".")
            if HOST.fullmatch(host) and host not in out:
                out.append(host)
            if len(out) >= 4:
                break
        return out
    preferred = hosts("preferredHosts")
    deprioritized = [host for host in hosts("deprioritizedHosts") if host not in preferred]
    if not preferred or not deprioritized:
        raise ValueError("Brain candidate requires preferred and deprioritized origins")
    fingerprint = str(value.get("experimentFingerprint") or "").strip().lower()
    basis_keys = (
        "experimentType", "providerId", "fixture", "requestType",
        "sourceNiakvioSha", "sourceRunId", "providerArtifactSha256",
        "officialClientSha", "runtimeScope", "preferredHosts",
        "deprioritizedHosts", "evidencePattern",
    )
    basis = {key: value.get(key) for key in basis_keys}
    expected = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    if not SHA64.fullmatch(fingerprint) or fingerprint != expected:
        raise ValueError("Brain candidate fingerprint mismatch")
    brain_sha = str(value.get("brainSha") or "").strip().lower()
    if brain_sha and not SHA40.fullmatch(brain_sha):
        raise ValueError("Brain candidate Brain SHA invalid")
    return {
        **{key: value.get(key) for key in basis_keys},
        "brainSha": brain_sha,
        "preferredHosts": preferred,
        "deprioritizedHosts": deprioritized,
        "experimentFingerprint": fingerprint,
        "candidateOnly": True,
        "generatedByBrain": True,
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }




V30_MARKER = "NIAKVIO_PROVIDER_NATIVE_HLS_ROOT_RECEIPT_V30"
V30_EXPERIMENT_TYPE = "native-hls-master-receipt-v30"
V30_EVIDENCE_PATTERN = "same-hls-root-2xx-then-403-pre-player"
V30_FINGERPRINT_KEYS = (
    "experimentType", "providerId", "fixture", "requestType",
    "sourceNiakvioSha", "sourceRunId", "providerArtifactSha256",
    "officialClientSha", "runtimeScope", "evidencePattern",
    "priorCandidateRunId", "priorCandidateSourceSha",
    "priorCandidateJsSha256",
)


def _validate_brain_hls_receipt_experiment(raw: str, provider: str, baseline_sha: str) -> dict:
    """Reject V30 if the original exact source and restored V29 failure are not persisted."""
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Brain V30 must be an object")
    permitted = set(V30_FINGERPRINT_KEYS) | {
        "schemaVersion", "experimentFingerprint", "candidateOnly", "generatedByBrain",
        "modelExecuted", "proofAuthority", "publicationAuthority",
        "nativePlaybackAuthority", "providerMutationAuthority", "brainSha",
    }
    if set(value) - permitted:
        raise ValueError("Brain V30 contains unknown/private fields")
    if (
        value.get("schemaVersion") != 1
        or value.get("experimentType") != V30_EXPERIMENT_TYPE
        or value.get("evidencePattern") != V30_EVIDENCE_PATTERN
        or value.get("runtimeScope") != BRAIN_RUNTIME_SCOPE
        or value.get("providerId") != provider
        or value.get("providerArtifactSha256") != baseline_sha
        or value.get("candidateOnly") is not True
        or value.get("generatedByBrain") is not True
        or value.get("modelExecuted") is not False
        or any(value.get(flag) is not False for flag in (
            "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
            "providerMutationAuthority",
        ))
    ):
        raise ValueError("Brain V30 provenance or authority mismatch")
    for field in ("sourceNiakvioSha", "officialClientSha", "priorCandidateSourceSha"):
        if not SHA40.fullmatch(str(value.get(field) or "")):
            raise ValueError("Brain V30 source/client SHA invalid")
    for field in ("providerArtifactSha256", "priorCandidateJsSha256"):
        if not SHA64.fullmatch(str(value.get(field) or "")):
            raise ValueError("Brain V30 bundle SHA invalid")
    for field in ("sourceRunId", "priorCandidateRunId"):
        if not re.fullmatch(r"[0-9]{8,20}", str(value.get(field) or "")):
            raise ValueError("Brain V30 run ID invalid")
    fingerprint = str(value.get("experimentFingerprint") or "")
    expected = hashlib.sha256(json.dumps(
        {key: value.get(key) for key in V30_FINGERPRINT_KEYS},
        sort_keys=True, separators=(",", ":"),
    ).encode("ascii")).hexdigest()
    if fingerprint != expected:
        raise ValueError("Brain V30 fingerprint invalid")
    brain_sha = str(value.get("brainSha") or "")
    if brain_sha and not SHA40.fullmatch(brain_sha):
        raise ValueError("Brain V30 Brain SHA invalid")

    ledger = json.loads(BRAIN_LEDGER.read_text(encoding="utf-8"))
    if (
        ledger.get("authority") != "candidate-only"
        or ledger.get("publicationAuthority") is not False
        or ledger.get("providerMutationAuthority") is not False
    ):
        raise ValueError("Brain V30 native candidate ledger untrusted")
    witnesses = []
    for row in ledger.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if any(str(row.get(k) or "") != str(value.get(k) or "") for k in (
            "providerId", "sourceNiakvioSha", "sourceRunId",
            "providerArtifactSha256", "officialClientSha",
        )):
            continue
        if any(row.get(flag) is not False for flag in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority",
        )):
            continue
        matches = [
            attempt for attempt in (row.get("candidateAttempts") or [])
            if isinstance(attempt, dict)
            and attempt.get("candidateVerdict") == "candidate_zero_stream"
            and attempt.get("candidateExecutionObserved") is True
            and attempt.get("candidateRestoredObserved") is True
            and attempt.get("candidateDecodedVideoObserved") is False
            and str(attempt.get("candidateRunId") or "") == str(value.get("priorCandidateRunId"))
            and attempt.get("candidateSourceSha") == value.get("priorCandidateSourceSha")
            and attempt.get("candidateJsSha256") == value.get("priorCandidateJsSha256")
            and attempt.get("validatedRepair") is False
            and attempt.get("publicationAllowed") is False
        ]
        if len(matches) == 1:
            witnesses.append(row)
    if len(witnesses) != 1:
        raise ValueError("Brain V30 lacks unique executed/restored V29 negative witness")
    return {**{key: value.get(key) for key in V30_FINGERPRINT_KEYS},
            "schemaVersion": 1, "experimentFingerprint": expected,
            "brainSha": brain_sha, "candidateOnly": True,
            "generatedByBrain": True, "modelExecuted": False,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False}


def _select_persisted_brain_hls_receipt_experiment(provider: str, baseline_sha: str) -> dict:
    """Recompile only an immutable Brain V30 plan already persisted in Learning."""
    ledger = json.loads(BRAIN_LEDGER.read_text(encoding="utf-8"))
    plans = []
    for row in ledger.get("rows") or []:
        if not isinstance(row, dict) or row.get("providerId") != provider:
            continue
        for plan in row.get("candidateFollowUpExperiments") or []:
            if not isinstance(plan, dict):
                continue
            try:
                validated = _validate_brain_hls_receipt_experiment(
                    json.dumps(plan, sort_keys=True), provider, baseline_sha,
                )
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
            if not SHA40.fullmatch(str(validated.get("brainSha") or "")):
                continue
            plans.append(validated)
    if len(plans) != 1:
        raise ValueError("Brain V30 requires one exact persisted HLS receipt experiment")
    return plans[0]


V31_MARKER = "NIAKVIO_PROVIDER_NATIVE_HLS_RECEIPT_DEDUPE_V31"
V31_EXPERIMENT_TYPE = "native-hls-master-receipt-dedupe-v31"
V31_EVIDENCE_PATTERN = "v30-zero-after-same-hls-root-2xx-403-first-wins-dedupe"
V31_FINGERPRINT_KEYS = (
    "experimentType", "providerId", "fixture", "requestType",
    "sourceNiakvioSha", "sourceRunId", "providerArtifactSha256",
    "officialClientSha", "runtimeScope", "evidencePattern",
    "parentExperimentFingerprint", "priorCandidateRunId",
    "priorCandidateSourceSha", "priorCandidateJsSha256",
)


def _validate_brain_hls_dedupe_experiment(raw: str, provider: str, baseline_sha: str) -> dict:
    """Fail closed unless V31 follows exactly one executed/restored V30 zero."""
    value = json.loads(raw)
    permitted = set(V31_FINGERPRINT_KEYS) | {
        "schemaVersion", "experimentFingerprint", "candidateOnly",
        "generatedByBrain", "modelExecuted", "proofAuthority",
        "publicationAuthority", "nativePlaybackAuthority",
        "providerMutationAuthority", "brainSha",
    }
    if not isinstance(value, dict) or set(value) - permitted:
        raise ValueError("Brain V31 object contains unknown/private fields")
    if (
        value.get("schemaVersion") != 1
        or value.get("experimentType") != V31_EXPERIMENT_TYPE
        or value.get("evidencePattern") != V31_EVIDENCE_PATTERN
        or value.get("runtimeScope") != BRAIN_RUNTIME_SCOPE
        or value.get("providerId") != provider
        or value.get("providerArtifactSha256") != baseline_sha
        or value.get("candidateOnly") is not True
        or value.get("generatedByBrain") is not True
        or value.get("modelExecuted") is not False
        or any(value.get(flag) is not False for flag in (
            "proofAuthority", "publicationAuthority", "nativePlaybackAuthority",
            "providerMutationAuthority",
        ))
    ):
        raise ValueError("Brain V31 provenance or authority mismatch")
    for key in ("sourceNiakvioSha", "officialClientSha", "priorCandidateSourceSha"):
        if not SHA40.fullmatch(str(value.get(key) or "")):
            raise ValueError("Brain V31 source/client SHA invalid")
    for key in ("providerArtifactSha256", "priorCandidateJsSha256", "parentExperimentFingerprint"):
        if not SHA64.fullmatch(str(value.get(key) or "")):
            raise ValueError("Brain V31 artifact/parent fingerprint invalid")
    for key in ("sourceRunId", "priorCandidateRunId"):
        if not re.fullmatch(r"[0-9]{8,20}", str(value.get(key) or "")):
            raise ValueError("Brain V31 exact run invalid")
    expected = hashlib.sha256(json.dumps(
        {key: value.get(key) for key in V31_FINGERPRINT_KEYS},
        sort_keys=True, separators=(",", ":"),
    ).encode("ascii")).hexdigest()
    if value.get("experimentFingerprint") != expected:
        raise ValueError("Brain V31 deterministic fingerprint mismatch")
    brain_sha = str(value.get("brainSha") or "")
    if brain_sha and not SHA40.fullmatch(brain_sha):
        raise ValueError("Brain V31 validated Brain SHA invalid")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", str(value.get("fixture") or "")):
        raise ValueError("Brain V31 fixture invalid")
    if value.get("requestType") not in {"anime", "tv", "movie"}:
        raise ValueError("Brain V31 request type invalid")
    ledger = json.loads(BRAIN_LEDGER.read_text(encoding="utf-8"))
    if (ledger.get("authority") != "candidate-only"
        or ledger.get("publicationAuthority") is not False
        or ledger.get("providerMutationAuthority") is not False):
        raise ValueError("Brain V31 ledger authority invalid")
    witnesses = []
    for parent in (ledger.get("rows") or [])[:512]:
        if not isinstance(parent, dict) or any(
            str(parent.get(key) or "") != str(value.get(key) or "")
            for key in ("providerId", "providerArtifactSha256", "sourceNiakvioSha",
                        "sourceRunId", "officialClientSha", "fixture", "requestType")
        ):
            continue
        if any(parent.get(flag) is not False for flag in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority",
        )):
            continue
        for follow in (parent.get("candidateFollowUpExperiments") or [])[:8]:
            if not isinstance(follow, dict) or (
                follow.get("experimentType") != "native-hls-master-receipt-v30"
                or follow.get("experimentFingerprint") != value.get("parentExperimentFingerprint")
                or follow.get("candidateOnly") is not True
                or follow.get("generatedByBrain") is not True
                or any(follow.get(flag) is not False for flag in (
                    "proofAuthority", "publicationAuthority",
                    "nativePlaybackAuthority", "providerMutationAuthority",
                ))
            ):
                continue
            for a in (follow.get("candidateAttempts") or [])[-8:]:
                if not isinstance(a, dict):
                    continue
                if (
                    a.get("candidateExperimentType") == "native-hls-master-receipt-v30"
                    and a.get("candidateVerdict") == "candidate_zero_stream"
                    and a.get("candidateExecutionObserved") is True
                    and a.get("candidateRestoredObserved") is True
                    and a.get("candidateDecodedVideoObserved") is False
                    and a.get("validatedRepair") is False
                    and a.get("publicationAllowed") is False
                    and str(a.get("candidateRunId") or "") == str(value.get("priorCandidateRunId"))
                    and a.get("candidateSourceSha") == value.get("priorCandidateSourceSha")
                    and a.get("candidateJsSha256") == value.get("priorCandidateJsSha256")
                ):
                    witnesses.append((parent, follow, a))
    if len(witnesses) != 1:
        raise ValueError("Brain V31 lacks unique V30 executed/restored zero witness")
    return {**{key: value.get(key) for key in V31_FINGERPRINT_KEYS},
            "schemaVersion": 1, "experimentFingerprint": expected,
            "brainSha": brain_sha, "candidateOnly": True,
            "generatedByBrain": True, "modelExecuted": False,
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False, "providerMutationAuthority": False}


def _select_persisted_brain_hls_dedupe_experiment(provider: str, baseline_sha: str) -> dict:
    """Compile only one never-executed persisted V31 follow-up."""
    ledger = json.loads(BRAIN_LEDGER.read_text(encoding="utf-8"))
    plans = []
    for parent in (ledger.get("rows") or [])[:512]:
        if not isinstance(parent, dict) or parent.get("providerId") != provider:
            continue
        for plan in (parent.get("candidateFollowUpExperiments") or [])[:8]:
            if not isinstance(plan, dict) or plan.get("experimentType") != V31_EXPERIMENT_TYPE:
                continue
            if plan.get("candidateAttempts"):
                continue
            try:
                checked = _validate_brain_hls_dedupe_experiment(
                    json.dumps(plan, sort_keys=True), provider, baseline_sha,
                )
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
            if SHA40.fullmatch(str(checked.get("brainSha") or "")):
                plans.append(checked)
    if len(plans) != 1:
        raise ValueError("Brain V31 requires unique persisted, unexecuted Core experiment")
    return plans[0]


def _select_persisted_brain_experiment(provider: str, baseline_sha: str) -> dict:
    if not BRAIN_LEDGER.is_file():
        raise ValueError("Brain native candidate experiment ledger missing")
    ledger = json.loads(BRAIN_LEDGER.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict):
        raise ValueError("Brain native candidate experiment ledger invalid")
    if (
        ledger.get("authority") != "candidate-only"
        or ledger.get("publicationAuthority") is not False
        or ledger.get("providerMutationAuthority") is not False
    ):
        raise ValueError("Brain native candidate ledger authority mismatch")
    matches: list[dict] = []
    for row in ledger.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("providerId") or "").strip().lower() != provider:
            continue
        if str(row.get("providerArtifactSha256") or "").strip().lower() != baseline_sha:
            continue
        try:
            validated = _validate_brain_experiment(
                json.dumps(row, sort_keys=True, separators=(",", ":")),
                provider,
                None,
            )
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        if not SHA40.fullmatch(str(validated.get("brainSha") or "")):
            continue
        matches.append(validated)
    if not matches:
        raise ValueError("no persisted Brain experiment matches exact published provider bytes")
    matches.sort(key=lambda row: (
        int(str(row.get("sourceRunId") or "0")),
        str(row.get("experimentFingerprint") or ""),
    ))
    return matches[-1]


def rows(manifest: Path, provider: str) -> tuple[dict, int]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    seen: set[str] = set()
    index = 0
    for row in data.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        name, filename = str(row.get("id") or "").strip().lower(), str(row.get("filename") or "").strip()
        if not name or not filename or name in seen:
            continue
        seen.add(name)
        if name == provider:
            if row.get("enabled") is not True:
                raise ValueError("candidate provider must be active")
            return row, index
        index += 1
    raise ValueError("candidate provider absent from selected manifest")


def js_path(manifest: Path, row: dict) -> Path:
    filename = str(row.get("filename") or "")
    if filename.startswith(("http://", "https://")):
        raise ValueError("candidate filename must be local")
    path = (manifest.parent / filename).resolve()
    relative = path.relative_to(ROOT)
    if not relative.parts or relative.parts[0] != "providers" or path.suffix != ".js" or not path.is_file():
        raise ValueError("candidate JS must be a local active provider")
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--source-sha", default="")
    p.add_argument("--output", default="automation/native-candidate-remat-proof.json")
    p.add_argument("--verify-staging", action="store_true")
    p.add_argument("--client-root", default="")
    p.add_argument("--required-marker", default="")
    p.add_argument("--brain-experiment-json", default="")
    args = p.parse_args()

    required_marker = args.required_marker.strip()
    if required_marker not in REQUIRED_MARKERS:
        raise ValueError("unsupported source-owned native candidate marker")
    provider = args.provider.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,79}", provider):
        raise ValueError("invalid provider")
    manifest = (ROOT / args.manifest).resolve()
    if manifest not in {(ROOT / "manifest.json").resolve(), (ROOT / "vf/manifest.json").resolve()}:
        raise ValueError("unsupported manifest projection")
    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)
    row, index = rows(manifest, provider)
    local_js = js_path(manifest, row)

    if args.verify_staging:
        proof = json.loads(output.read_text(encoding="utf-8"))
        if (
            proof.get("provider") != provider
            or proof.get("manifest") != args.manifest
            or proof.get("requiredCoreMarker", "") != required_marker
        ):
            raise ValueError("candidate provenance mismatch")
        candidate_sha = str(proof.get("candidateJsSha256") or "")
        if not re.fullmatch(r"[a-f0-9]{64}", candidate_sha) or sha256(local_js) != candidate_sha:
            raise ValueError("candidate source bytes diverged")
        if required_marker and required_marker not in local_js.read_text(encoding="utf-8"):
            raise ValueError("required generic Core marker absent from staged candidate source")
        if not args.client_root:
            raise ValueError("official client checkout required")
        # The native stage filters to NIAKVIO_PROVIDER_SCOPE_MATRIX *before*
        # assigning pNNN.js indexes. The single-provider candidate must be p000.
        scope_raw = os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", "").strip()
        if not scope_raw:
            raise ValueError("candidate requires exact native provider scope")
        scope_path = Path(scope_raw).resolve()
        scope_path.relative_to(ROOT)
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
        stage_ids = [str(v.get("manifestId") or v.get("provider") or "").strip().lower()
                     for v in scope.get("rows") or [] if isinstance(v, dict)]
        if stage_ids != [provider] or int(scope.get("providerCount") or 0) != 1:
            raise ValueError("candidate staging scope must contain exactly the requested provider")
        asset = Path(args.client_root).resolve() / "app/src/androidTest/assets/niakvio/p000.js"
        if not asset.is_file() or sha256(asset) != candidate_sha:
            raise ValueError("candidate bytes not actually staged in official NuvioTV test")
        proof["officialTvTestAssetByteMatched"] = True
        proof["productionPlaybackVerified"] = False
        proof["publicationAllowed"] = False
        write(output, proof)
        print(f"FIELD_NATIVE_CANDIDATE_STAGED provider={provider} sha256={candidate_sha} matched=true publication=false", flush=True)
        return

    source_sha = args.source_sha.strip().lower()
    actual_source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha) or source_sha != actual_source:
        raise ValueError("candidate requires exact source checkout SHA")
    if os.environ.get("NUVIO_PROVIDER_V3_CONTEXT") != "workspace":
        raise ValueError("candidate requires ephemeral workspace materialization")
    baseline_sha = sha256(local_js)
    if args.brain_experiment_json.strip():
        if required_marker == V31_MARKER:
            brain_experiment = _validate_brain_hls_dedupe_experiment(
                args.brain_experiment_json, provider, baseline_sha
            )
        elif required_marker == V30_MARKER:
            brain_experiment = _validate_brain_hls_receipt_experiment(
                args.brain_experiment_json, provider, baseline_sha
            )
        else:
            brain_experiment = _validate_brain_experiment(
                args.brain_experiment_json, provider, source_sha
            )
    elif required_marker == BRAIN_MARKER:
        # Older source-pinned native evidence is bound to exact published JS.
        brain_experiment = _select_persisted_brain_experiment(provider, baseline_sha)
    elif required_marker == V30_MARKER:
        brain_experiment = _select_persisted_brain_hls_receipt_experiment(provider, baseline_sha)
    elif required_marker == V31_MARKER:
        brain_experiment = _select_persisted_brain_hls_dedupe_experiment(provider, baseline_sha)
    else:
        brain_experiment = None
    if brain_experiment and required_marker not in {BRAIN_MARKER, V30_MARKER, V31_MARKER}:
        raise ValueError("Brain native experiment requires its source-owned Core marker")
    if not brain_experiment and required_marker in {BRAIN_MARKER, V30_MARKER, V31_MARKER}:
        raise ValueError("Brain native marker requires a Brain experiment")
    child_env = os.environ.copy()
    if brain_experiment:
        if brain_experiment["providerArtifactSha256"] != baseline_sha:
            raise ValueError("Brain candidate observed artifact is not the current published baseline")
        selected_env = (
            "NIAKVIO_NATIVE_BRAIN_HLS_RECEIPT_DEDUPE" if required_marker == V31_MARKER
            else "NIAKVIO_NATIVE_BRAIN_HLS_ROOT_RECEIPT" if required_marker == V30_MARKER
            else "NIAKVIO_NATIVE_BRAIN_ORIGIN_PRIORITY"
        )
        child_env[selected_env] = json.dumps(
            brain_experiment, sort_keys=True, separators=(",", ":")
        )
    subprocess.run(
        [sys.executable, "scripts/materialize_provider_v3_one.py", provider],
        cwd=ROOT, check=True, timeout=240, env=child_env,
    )
    updated_row, _ = rows(manifest, provider)
    candidate_path = js_path(manifest, updated_row)
    candidate_sha = sha256(candidate_path)
    candidate_source = candidate_path.read_text(encoding="utf-8")
    if candidate_sha == baseline_sha or MARKER not in candidate_source:
        raise ValueError("candidate did not rematerialize changed ProviderBase bytes")
    if required_marker and required_marker not in candidate_source:
        raise ValueError("candidate did not materialize required source-owned Core marker")
    if brain_experiment:
        fingerprint = brain_experiment["experimentFingerprint"]
        data_marker = (
            "nativeHlsReceiptDedupeV31" if required_marker == V31_MARKER
            else "nativeHlsRootReceiptV30" if required_marker == V30_MARKER
            else "nativeBlockingOriginPriority"
        )
        if data_marker not in candidate_source or fingerprint not in candidate_source:
            raise ValueError("Brain candidate experiment was not compiled into Provider DATA")
    proof = {
        "schemaVersion": 1, "provider": provider, "manifest": args.manifest,
        "sourceNiakvioSha": source_sha, "publishedBaselineJsSha256": baseline_sha,
        "candidateJsSha256": candidate_sha, "candidateByteChanged": True,
        "requiredCoreMarker": required_marker,
        "generatedByBrain": bool(brain_experiment), "generatedByProviderBase": True,
        "brainExperimentFingerprint": (
            brain_experiment["experimentFingerprint"] if brain_experiment else ""
        ),
        "brainPreferredHosts": (
            brain_experiment.get("preferredHosts", []) if brain_experiment else []
        ),
        "brainDeprioritizedHosts": (
            brain_experiment.get("deprioritizedHosts", []) if brain_experiment else []
        ),
        "brainExperimentType": (
            str(brain_experiment.get("experimentType") or "") if brain_experiment else ""
        ),
        "brainSha": (
            str(brain_experiment.get("brainSha") or "") if brain_experiment else ""
        ),
        "brainEvidenceSourceNiakvioSha": (
            str(brain_experiment.get("sourceNiakvioSha") or "") if brain_experiment else ""
        ),
        "brainEvidenceSourceRunId": (
            str(brain_experiment.get("sourceRunId") or "") if brain_experiment else ""
        ),
        "brainObservedBaselineJsSha256": (
            str(brain_experiment.get("providerArtifactSha256") or "") if brain_experiment else ""
        ),
        "officialTvTestAssetByteMatched": False, "productionPlaybackVerified": False,
        "publicationAllowed": False,
    }
    write(output, proof)
    print(f"FIELD_NATIVE_CANDIDATE_REMAT provider={provider} from={baseline_sha} to={candidate_sha} marker=true publication=false", flush=True)


if __name__ == "__main__":
    main()
