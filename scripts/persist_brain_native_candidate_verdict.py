#!/usr/bin/env python3
"""Persist bounded verdicts for isolated Brain-generated native TV candidates."""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
RUN_ID = re.compile(r"[0-9]{8,20}")
FIELD = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
LANG = re.compile(r"^[a-z]{2,3}(?:-[a-z]{2})?$")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _decode64(value: str) -> str:
    text = str(value or "").replace("-", "+").replace("_", "/")
    text += "=" * ((4 - len(text) % 4) % 4)
    try:
        return base64.b64decode(text).decode("utf-8")
    except Exception:
        return ""


def _fields(line: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in FIELD.finditer(line)}


def _languages(*values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        for token in re.split(r"[,;|\s]+", str(value or "").strip().lower()):
            token = token.replace("_", "-")
            if LANG.fullmatch(token) and token not in out:
                out.append(token)
            if len(out) >= 12:
                return out
    return out


def _matching_reports(root: Path) -> list[dict[str, Any]]:
    reports = []
    for path in sorted(root.rglob("*-brain.json")):
        try:
            value = _load(path)
        except (ValueError, json.JSONDecodeError):
            continue
        if value.get("schemaVersion") == 5:
            reports.append(value)
    return reports


def persist_verdict(
    artifact_root: Path,
    ledger_path: Path,
    candidate_source_sha: str,
    candidate_run_id: str,
) -> dict[str, Any]:
    candidate_source_sha = candidate_source_sha.strip().lower()
    candidate_run_id = candidate_run_id.strip()
    if not SHA40.fullmatch(candidate_source_sha) or not RUN_ID.fullmatch(candidate_run_id):
        raise ValueError("candidate verdict requires exact source SHA and numeric run")

    proofs = sorted(artifact_root.rglob("native-candidate-remat-proof.json"))
    if len(proofs) != 1:
        raise ValueError("candidate verdict requires exactly one rematerialization proof")
    proof = _load(proofs[0])
    provider = str(proof.get("provider") or "").strip().lower()
    fingerprint = str(proof.get("brainExperimentFingerprint") or "").strip().lower()
    candidate_sha = str(proof.get("candidateJsSha256") or "").strip().lower()
    baseline_sha = str(proof.get("publishedBaselineJsSha256") or "").strip().lower()
    observed_baseline_sha = str(proof.get("brainObservedBaselineJsSha256") or "").strip().lower()
    if (
        proof.get("generatedByBrain") is not True
        or proof.get("generatedByProviderBase") is not True
        or proof.get("candidateByteChanged") is not True
        or proof.get("officialTvTestAssetByteMatched") is not True
        or proof.get("publicationAllowed") is not False
        or proof.get("productionPlaybackVerified") is not False
        or str(proof.get("sourceNiakvioSha") or "").strip().lower() != candidate_source_sha
        or not re.fullmatch(r"[a-z][a-z0-9-]{1,79}", provider)
        or not SHA64.fullmatch(fingerprint)
        or not SHA64.fullmatch(candidate_sha)
        or not SHA64.fullmatch(baseline_sha)
        or observed_baseline_sha != baseline_sha
    ):
        raise ValueError("candidate rematerialization proof is not authoritative for a diagnostic verdict")

    ledger = _load(ledger_path)
    if (
        ledger.get("authority") != "candidate-only"
        or ledger.get("publicationAuthority") is not False
        or ledger.get("providerMutationAuthority") is not False
    ):
        raise ValueError("candidate experiment ledger authority mismatch")
    rows = [row for row in (ledger.get("rows") or []) if isinstance(row, dict)]
    experiment_type = str(proof.get("brainExperimentType") or "native-blocking-player-origin-priority")
    if experiment_type == "native-hls-master-receipt-v30":
        matches = [
            (parent, followup)
            for parent in rows
            for followup in (parent.get("candidateFollowUpExperiments") or [])
            if isinstance(followup, dict)
            and followup.get("experimentType") == experiment_type
            and str(followup.get("experimentFingerprint") or "").lower() == fingerprint
            and str(followup.get("providerArtifactSha256") or "").lower() == baseline_sha
            and parent.get("providerId") == provider
            and parent.get("providerArtifactSha256") == baseline_sha
            and followup.get("candidateOnly") is True
            and followup.get("generatedByBrain") is True
            and all(followup.get(k) is False for k in (
                "proofAuthority", "publicationAuthority",
                "nativePlaybackAuthority", "providerMutationAuthority",
            ))
        ]
        if len(matches) != 1:
            raise ValueError("V30 candidate proof has no uniquely persisted Brain follow-up")
        parent, row = matches[0]
        prior = [
            attempt for attempt in (parent.get("candidateAttempts") or [])
            if isinstance(attempt, dict)
            and str(attempt.get("candidateRunId") or "") == str(row.get("priorCandidateRunId") or "")
            and attempt.get("candidateSourceSha") == row.get("priorCandidateSourceSha")
            and attempt.get("candidateJsSha256") == row.get("priorCandidateJsSha256")
            and attempt.get("candidateVerdict") == "candidate_zero_stream"
            and attempt.get("candidateExecutionObserved") is True
            and attempt.get("candidateRestoredObserved") is True
        ]
        if len(prior) != 1:
            raise ValueError("V30 candidate lost exact V29 negative witness")
    elif experiment_type == "native-blocking-player-origin-priority":
        matches = [row for row in rows if str(row.get("experimentFingerprint") or "").lower() == fingerprint]
        if len(matches) != 1:
            raise ValueError("V29 candidate experiment fingerprint not uniquely persisted")
        row = matches[0]
    else:
        raise ValueError("unknown Brain native candidate experiment type")
    fixture = str(row.get("fixture") or "").strip().lower()
    request_type = str(row.get("requestType") or "").strip().lower()
    if (
        str(row.get("providerId") or "").strip().lower() != provider
        or str(row.get("providerArtifactSha256") or "").strip().lower() != baseline_sha
        or row.get("candidateOnly") is not True
        or row.get("generatedByBrain") is not True
        or any(row.get(flag) is not False for flag in (
            "proofAuthority", "publicationAuthority",
            "nativePlaybackAuthority", "providerMutationAuthority",
        ))
    ):
        raise ValueError("candidate proof does not match persisted Brain experiment")

    byte_check = False
    runtime_count: int | None = None
    restored = False
    integrity_failure = False
    for path in sorted(artifact_root.rglob("*.log")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "FIELD_NATIVE_CANDIDATE_BYTE_MISMATCH " in line or "FIELD_NATIVE_CANDIDATE_RESTORE_FAILED " in line:
                integrity_failure = True
            if "FIELD_NATIVE_CANDIDATE_RUNTIME_BYTE_CHECK " in line:
                fields = _fields(line)
                byte_check = byte_check or (
                    _decode64(fields.get("provider64", "")).strip().lower() == provider
                    and fields.get("sha256", "").lower() == candidate_sha
                    and fields.get("matched") == "true"
                    and fields.get("runtime") == "official_plugin_manager"
                )
            if "FIELD_NATIVE_CANDIDATE_RUNTIME_RESULT " in line:
                fields = _fields(line)
                if (
                    _decode64(fields.get("provider64", "")).strip().lower() == provider
                    and fields.get("sha256", "").lower() == candidate_sha
                    and fields.get("runtime") == "official_plugin_manager"
                ):
                    try:
                        count = int(fields.get("count", "-1"))
                    except ValueError:
                        count = -1
                    if 0 <= count <= 200:
                        runtime_count = max(runtime_count or 0, count)
            if "FIELD_NATIVE_CANDIDATE_RESTORED " in line:
                fields = _fields(line)
                restored = restored or (
                    _decode64(fields.get("provider64", "")).strip().lower() == provider
                    and fields.get("exact_previous_state") == "true"
                )

    extraction_nonempty = False
    reader_healthy = False
    decoded_video = False
    audio_languages: list[str] = []
    subtitle_languages: list[str] = []
    for report in _matching_reports(artifact_root):
        for obs in report.get("extractionHealthyObservations") or []:
            if (
                isinstance(obs, dict)
                and str(obs.get("client") or "").lower() == "tv"
                and str(obs.get("provider") or "").lower() == provider
                and str(obs.get("fixture") or "").lower() == fixture
                and str(obs.get("requestType") or "").lower() == request_type
                and int(obs.get("returnedCount") or 0) > 0
            ):
                extraction_nonempty = True
        for obs in report.get("observations") or []:
            if not isinstance(obs, dict):
                continue
            if (
                str(obs.get("client") or "").lower() != "tv"
                or str(obs.get("provider") or "").lower() != provider
                or str(obs.get("fixture") or "").lower() != fixture
                or str(obs.get("requestType") or "").lower() != request_type
                or obs.get("observationLayer") != "player"
                or obs.get("failureClass") != "healthy"
            ):
                continue
            reader_healthy = True
            decoded_video = decoded_video or obs.get("playerVideoFormatObserved") is True
            audio_languages = _languages(
                *audio_languages,
                obs.get("playerAudioTrackLanguages"),
                obs.get("transportAudioTrackLanguages"),
            )
            subtitle_languages = _languages(
                *subtitle_languages,
                obs.get("playerSubtitleTrackLanguages"),
                obs.get("transportSubtitleTrackLanguages"),
            )

    execution_observed = bool(byte_check and runtime_count is not None and not integrity_failure)
    if integrity_failure:
        verdict = "candidate_integrity_failure"
    elif not execution_observed:
        verdict = "candidate_not_executed"
    elif runtime_count == 0:
        verdict = "candidate_zero_stream"
    elif not extraction_nonempty:
        verdict = "candidate_runtime_nonempty_unconfirmed_extraction"
    elif not reader_healthy:
        verdict = "candidate_extraction_improved_reader_unverified"
    elif not decoded_video:
        verdict = "candidate_reader_healthy_decode_unverified"
    else:
        verdict = "candidate_terminal_decode_observed"

    attempt = {
        "candidateRunId": candidate_run_id,
        "candidateExperimentType": experiment_type,
        "candidateSourceSha": candidate_source_sha,
        "candidateJsSha256": candidate_sha,
        "candidateExecutionObserved": execution_observed,
        "candidateRuntimeReturnedCount": runtime_count if runtime_count is not None else -1,
        "candidateRestoredObserved": restored,
        "candidateExtractionNonEmpty": extraction_nonempty,
        "candidateTerminalReaderHealthy": reader_healthy,
        "candidateDecodedVideoObserved": decoded_video,
        "candidateAudioLanguages": audio_languages,
        "candidateSubtitleLanguages": subtitle_languages,
        "candidateFrAudioObserved": "fr" in audio_languages,
        "candidateVerdict": verdict,
        "validatedRepair": False,
        "publicationAllowed": False,
    }
    attempts = [
        item for item in (row.get("candidateAttempts") or [])
        if isinstance(item, dict) and str(item.get("candidateRunId") or "") != candidate_run_id
    ]
    attempts.append(attempt)
    row["candidateAttempts"] = attempts[-8:]
    row["lastCandidateRunId"] = candidate_run_id
    row["lastCandidateSourceSha"] = candidate_source_sha
    row["lastCandidateJsSha256"] = candidate_sha
    row["lastCandidateVerdict"] = verdict
    row["lastCandidateExecutionObserved"] = execution_observed
    row["lastCandidateExtractionNonEmpty"] = extraction_nonempty
    row["lastCandidateTerminalReaderHealthy"] = reader_healthy
    row["lastCandidateDecodedVideoObserved"] = decoded_video
    row["lastCandidateFrAudioObserved"] = "fr" in audio_languages
    row["lastCandidateValidatedRepair"] = False

    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return attempt


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--artifacts", type=Path, required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--candidate-source-sha", required=True)
    p.add_argument("--candidate-run-id", required=True)
    args = p.parse_args()
    attempt = persist_verdict(
        args.artifacts.resolve(),
        args.ledger.resolve(),
        args.candidate_source_sha,
        args.candidate_run_id,
    )
    print(
        "FIELD_BRAIN_NATIVE_CANDIDATE_VERDICT "
        f"run={attempt['candidateRunId']} verdict={attempt['candidateVerdict']} "
        f"executed={str(attempt['candidateExecutionObserved']).lower()} "
        f"extraction_nonempty={str(attempt['candidateExtractionNonEmpty']).lower()} "
        f"reader_healthy={str(attempt['candidateTerminalReaderHealthy']).lower()} "
        f"decoded_video={str(attempt['candidateDecodedVideoObserved']).lower()} "
        "validated_repair=false publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
