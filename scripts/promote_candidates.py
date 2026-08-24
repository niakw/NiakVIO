#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Publish the complete non-P2P catalogue with conservative activation.

Automatic activation requires current playback/identity safety gates; quality and language are ranking/projection signals for the general manifest. A SHA-pinned runtime
evidence record may activate a provider only when CI is explicitly inconclusive
while the same file has been confirmed working in the real Nuvio application.
Confirmed failures and P2P output can never be overridden. An upstream-disabled
flag is advisory only when the exact current JS passes the complete strict deep proof. Duplicate variants are resolved after every check.

The eleven gates are:
1. no P2P/torrent evidence;
2. healthy functional status;
3. minimum aggregate score;
4. representative-fixture and declared-type coverage;
5. at least one playable stream when runtime output is returned;
6. at least one reachable media host when runtime output is returned;
7. verified media payload/playback evidence when runtime output is returned;
8. media-quality diagnostics (non-blocking for a verified general stream);
9. language/subtitle diagnostics (VF filtering is handled by language projection);
10. no title/episode/duration identity contradiction;
11. acceptable latency plus one successful deep validation of the current SHA.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides, load_overrides

ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(os.environ.get("NUVIO_STAGE", ROOT / "staging")).resolve()
SOURCES_PATH = ROOT / "sources.json"
CONFIG_PATH = ROOT / "health-config.json"
RUNTIME_EVIDENCE_PATH = ROOT / "runtime-evidence.json"
LKG_PATH = ROOT / "provider-lkg.json"
ACTIVATION_LKG_PATH = ROOT / "provider-activation-lkg.json"
HEALTH_RESULTS_PATH = Path(
    os.environ.get("NUVIO_HEALTH_RESULTS", STAGE / "health-results.json")
).resolve()
MANIFEST_PATH = ROOT / "manifest.json"
NEXT_MANIFEST_PATH = ROOT / "manifest.next.json"
VF_MANIFEST_PATH = ROOT / "vf" / "manifest.json"
VOSTFR_MANIFEST_PATH = ROOT / "vostfr" / "manifest.json"
HISTORY_PATH = ROOT / "health-history.json"
AVAILABILITY_HISTORY_PATH = ROOT / "availability-history.json"
REPORT_PATH = ROOT / "health-report.json"
PROVENANCE_PATH = ROOT / "PROVENANCE.json"
VERSIONS_DIR = ROOT / "providers"


def load_json(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary_name = handle.name
    os.replace(temporary_name, path)


def safe_fragment(value: str) -> str:
    return (
        re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip())
        .strip(".-")[:120]
        or "provider"
    )


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def manifest_payload_without_version(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": manifest.get("name"),
        "scrapers": manifest.get("scrapers", []),
    }


def next_manifest_version(current_version: str, base_version: str, changed: bool) -> str:
    """Keep the manifest in the configured version series and bump on payload changes.

    ``base_version`` is a version floor so unchanged runs cannot preserve an
    obsolete version series.
    """
    def parse(value: str) -> tuple[int, int, int] | None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
        if not match:
            return None
        return tuple(int(match.group(index)) for index in range(1, 4))

    base = parse(base_version) or (5, 5, 0)
    current = parse(current_version)

    if current is None or current < base:
        return ".".join(str(part) for part in base)
    if not changed:
        return ".".join(str(part) for part in current)
    if current[:2] == base[:2]:
        return f"{current[0]}.{current[1]}.{current[2] + 1}"
    return ".".join(str(part) for part in base)


def historical_inconclusive_decision(
    item: dict[str, Any],
    activation: dict[str, Any],
    previous_record: dict[str, Any] | None,
    gates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Allow any provider, not a named exception, to survive an inconclusive CI run.

    The same exact JavaScript must previously have passed the score and every
    substantive quality gate. A current P2P or conclusive failure always wins.
    """
    previous_record = previous_record if isinstance(previous_record, dict) else {}
    status = str(item.get("health", {}).get("status", "runtime_error"))
    minimum_score = int(activation.get("minimum_score", 70))
    prior_gates = previous_record.get("activation_gates", {})
    required_prior = [
        "01_policy_safe_no_p2p",
        "03_minimum_score",
        "04_fixture_and_type_coverage",
        "05_stream_and_fixture_coverage",
        "06_distinct_host_diversity",
        "07_verified_payload_playability",
        "08_quality_and_bitrate",
        "09_language_and_subtitle_integrity",
        "10_content_identity_integrity",
    ]
    checks = {
        "current_status_inconclusive": status in inconclusive_statuses(activation),
        "same_sha256": bool(item.get("sha256")) and previous_record.get("sha256") == item.get("sha256"),
        "prior_score_meets_threshold": int(previous_record.get("health_score", 0)) >= minimum_score,
        "prior_quality_gates_passed": all(bool(prior_gates.get(name, {}).get("passed")) for name in required_prior),
        "current_no_p2p": bool(gates.get("01_policy_safe_no_p2p", {}).get("passed", False)),
        "upstream_enabled": bool(item.get("metadata", {}).get("enabled", True)),
    }
    eligible = all(checks.values())
    return {
        "eligible": eligible,
        "checks": checks,
        "previous_health_score": int(previous_record.get("health_score", 0)),
        "reason": None if eligible else "historical_inconclusive_rejected:" + ",".join(k for k,v in checks.items() if not v),
    }


def is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def excluded_ids(sources: dict[str, Any]) -> set[str]:
    return {
        canonical_id(str(value))
        for value in sources.get("exclusions", {}).get("provider_ids", [])
    }


def metadata_is_excluded(entry: dict[str, Any], sources: dict[str, Any]) -> bool:
    text = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    return any(
        str(pattern).casefold() in text
        for pattern in sources.get("exclusions", {}).get("metadata_patterns", [])
    )


def copy_candidate(candidate: dict[str, Any]) -> tuple[Path, str]:
    source_path = (STAGE / candidate["local_path"]).resolve()
    if not is_under(source_path, STAGE / "providers") or not source_path.exists():
        raise ValueError(f"unsafe or missing staged provider path: {source_path}")

    staged_data = source_path.read_bytes()
    staged_digest = hashlib.sha256(staged_data).hexdigest()
    if staged_digest != candidate["sha256"]:
        raise ValueError(f"hash mismatch for {candidate['key']}")

    # Defence in depth: reapply provider overrides in the write-enabled
    # promotion job. The operation is idempotent, so a correctly patched
    # staging artifact remains byte-identical. This prevents an unpatched
    # candidate from ever reaching providers/ even if staging changes later.
    data, promotion_patches = apply_overrides(candidate["canonical_id"], staged_data)
    digest = hashlib.sha256(data).hexdigest()
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as validation_file:
        validation_file.write(data)
        validation_path = Path(validation_file.name)
    try:
        validation = subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "validate_provider_artifact.cjs"),
                str(validation_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if validation.returncode != 0:
            details = "\n".join(
                part.strip()
                for part in (validation.stdout, validation.stderr)
                if part and part.strip()
            )
            raise ValueError(
                f"generated provider artifact rejected for {candidate.get('key', candidate.get('canonical_id', 'unknown'))}: "
                f"validator exit={validation.returncode}\n"
                f"{details or 'validator returned no diagnostic'}"
            )
    finally:
        validation_path.unlink(missing_ok=True)
    if promotion_patches:
        existing = candidate.setdefault("local_patches", [])
        existing.extend(patch for patch in promotion_patches if patch not in existing)
        candidate["sha256"] = digest

    published_source = "nuvio" if candidate.get("local_patches") else candidate["source"]
    destination = VERSIONS_DIR / (
        f"{safe_fragment(candidate['canonical_id'])}--"
        f"{safe_fragment(published_source)}--{digest[:16]}.js"
    )
    if not destination.exists() or destination.read_bytes() != data:
        destination.write_bytes(data)
    return destination, digest


def build_entry(
    candidate: dict[str, Any],
    destination: Path,
    enabled: bool,
    claims: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = candidate.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"missing metadata for {candidate.get('key')}")

    entry = dict(metadata)
    config = load_overrides()
    specific = (config.get("provider_patches") or {}).get(str(candidate.get("canonical_id") or "").casefold(), {})
    manifest_overrides = specific.get("manifest_overrides") or {}
    if isinstance(manifest_overrides, dict):
        entry.update(manifest_overrides)
    claims = claims if isinstance(claims, dict) else {}
    curated_types = [
        str(value)
        for value in claims.get("supported_types", [])
        if str(value) in {"movie", "tv", "anime"}
    ]
    canonical = str(candidate.get("canonical_id") or "").casefold()
    capability = (config.get("provider_capabilities") or {}).get(canonical, {})
    explicit_types = [
        str(value)
        for value in (capability.get("catalogue_types") or [])
        if str(value) in {"movie", "tv", "anime"}
    ] if isinstance(capability, dict) else []
    policy_types = [
        str(value)
        for value in (specific.get("published_types") or [])
        if str(value) in {"movie", "tv", "anime"}
    ] if isinstance(specific, dict) else []
    published_types = policy_types or list(dict.fromkeys(curated_types + explicit_types))
    if published_types:
        # A provider-level published_types policy is authoritative. It prevents
        # an upstream metadata union from re-advertising request shapes that the
        # current bundle does not implement (for example Papadustream movies).
        entry["supportedTypes"] = published_types
    entry["filename"] = destination.relative_to(ROOT).as_posix()
    # StreamZo needs an external player for ordinary embed/recovery bundles.
    # Only the globally audited direct-media bundle can safely advertise native playback.
    if canonical == "streamzo":
        entry["supportsExternalPlayer"] = "--nuvio-tv-global--" not in entry["filename"]
    force_disabled = isinstance(manifest_overrides, dict) and manifest_overrides.get("enabled") is False
    entry["enabled"] = bool(enabled) and not force_disabled
    if not isinstance(entry.get("id"), str) or not entry["id"].strip():
        entry["id"] = candidate.get("upstream_id") or candidate["canonical_id"]
    return entry



def bump_provider_version(value: str) -> str:
    """Increment a provider patch version, defaulting malformed values to 1.0.1."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return "1.0.1"
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def provider_entry_version(new_entry: dict[str, Any], old_entry: dict[str, Any] | None) -> str:
    """Bump the scraper version whenever its published artifact changes.

    Nuvio caches providers by manifest metadata. A hash-addressed filename change
    therefore needs a matching scraper version change, otherwise clients may keep
    the previous JavaScript even though the repository manifest changed.
    """
    declared = str(new_entry.get("version") or "1.0.0")
    if not isinstance(old_entry, dict):
        return declared
    previous = str(old_entry.get("version") or declared or "1.0.0")
    tracked_fields = ("filename", "supportedTypes", "supportsExternalPlayer")
    if any(old_entry.get(field) != new_entry.get(field) for field in tracked_fields):
        return bump_provider_version(previous)
    return previous

def validate_manifest(manifest: dict[str, Any], sources: dict[str, Any]) -> None:
    scrapers = manifest.get("scrapers")
    if not isinstance(scrapers, list) or not scrapers:
        raise ValueError("manifest has no providers")

    seen: set[str] = set()
    explicit = excluded_ids(sources)
    for entry in scrapers:
        if not isinstance(entry, dict):
            raise ValueError("manifest entry is not an object")
        cid = canonical_id(str(entry.get("id", "")))
        if not cid or cid in seen:
            raise ValueError(f"duplicate or missing provider id: {cid!r}")
        if cid in explicit or metadata_is_excluded(entry, sources):
            raise ValueError(f"excluded P2P/torrent entry remains: {cid}")
        seen.add(cid)

        filename = entry.get("filename")
        target = (ROOT / filename).resolve() if isinstance(filename, str) else None
        if (
            target is None
            or not is_under(target, ROOT / "providers")
            or not target.exists()
        ):
            raise ValueError(f"missing or unsafe provider file for {cid}")


def normalized_manifest_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()


def normalize_manifest_language(value: Any) -> str | None:
    text = normalized_manifest_text(value).strip()
    aliases = {
        "english": "en", "eng": "en", "en-us": "en", "en-gb": "en",
        "french": "fr", "francais": "fr", "fre": "fr", "fra": "fr",
        "japanese": "ja", "jpn": "ja", "jp": "ja",
    }
    if text in aliases:
        return aliases[text]
    match = re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", text)
    return text[:2] if match else None


def normalize_supported_type(value: Any) -> str | None:
    text = normalized_manifest_text(value).strip()
    if re.fullmatch(r"(?:movie|movies|film|films|cinema)", text):
        return "movie"
    if re.fullmatch(r"(?:tv|series|serie|show|shows|television)", text):
        return "tv"
    if re.fullmatch(r"(?:anime|animes|manga|mangas)", text):
        return "anime"
    return None


def manifest_type_signals(text: str) -> dict[str, bool]:
    normalized = normalized_manifest_text(text)
    return {
        "movie": bool(re.search(r"\b(?:movie|movies|film|films|cinema|cinematic)\b", normalized)),
        "tv": bool(re.search(r"\b(?:tv|television|serie|series|show|shows)\b", normalized)),
        "anime": bool(re.search(r"\b(?:anime|animes|manga|mangas)\b", normalized)),
    }


def variant_supported_types(variant: dict[str, Any]) -> set[str]:
    metadata = variant.get("metadata", {}) if isinstance(variant.get("metadata"), dict) else {}
    declared = {
        normalized
        for value in metadata.get("supportedTypes", [])
        if (normalized := normalize_supported_type(value))
    } if isinstance(metadata.get("supportedTypes"), list) else set()
    text = " ".join(
        str(value or "")
        for value in (
            variant.get("canonical_id"),
            metadata.get("id"),
            metadata.get("name"),
            metadata.get("description"),
        )
    )
    signals = manifest_type_signals(text)
    inferred = {name for name, present in signals.items() if present}
    # Anime-only descriptions frequently declare movie/tv merely because those
    # are Nuvio request shapes. Conversely, a description such as Movix's
    # "Films, Séries et Animes" explicitly covers all three catalogues.
    if signals["anime"] and not signals["movie"] and not signals["tv"]:
        return {"anime"}
    combined = declared | inferred
    return combined or {"movie", "tv"}


def manifest_height_from_text(text: str) -> int | None:
    if re.search(r"(?:^|[^a-z0-9])(?:4k|uhd|2160p?)(?:[^a-z0-9]|$)", text):
        return 2160
    if re.search(r"(?:^|[^a-z0-9])(?:2k|qhd|1440p?)(?:[^a-z0-9]|$)", text):
        return 1440
    if re.search(r"(?:^|[^a-z0-9])(?:full[ -]?hd|fhd|1080p?)(?:[^a-z0-9]|$)", text):
        return 1080
    if re.search(r"(?:^|[^a-z0-9])(?:720p?|hd)(?:[^a-z0-9]|$)", text):
        return 720
    if re.search(r"\b(?:high[ -]?quality|good[ -]?quality|bonne qualite|hd quality)\b", text):
        return 720
    return None


def aggregate_manifest_claims(variants: list[dict[str, Any]]) -> dict[str, Any]:
    descriptions: list[str] = []
    languages: set[str] = set()
    supported_types: set[str] = set()
    declared_supported_types: set[str] = set()
    type_text_parts: list[str] = []
    formats: set[str] = set()
    sources: set[str] = set()
    quality_signals: set[str] = set()
    language_modes: set[str] = set()
    max_height: int | None = None

    for variant in variants:
        metadata = variant.get("metadata", {}) if isinstance(variant.get("metadata"), dict) else {}
        description = str(metadata.get("description") or "").strip()
        if description:
            descriptions.append(description)
        sources.add(str(variant.get("source") or "unknown"))
        for value in metadata.get("contentLanguage", []) if isinstance(metadata.get("contentLanguage"), list) else []:
            normalized = normalize_manifest_language(value)
            if normalized:
                languages.add(normalized)
        if isinstance(metadata.get("supportedTypes"), list):
            for value in metadata.get("supportedTypes", []):
                normalized_type = normalize_supported_type(value)
                if normalized_type:
                    declared_supported_types.add(normalized_type)
        type_text_parts.extend(
            str(value or "")
            for value in (
                variant.get("canonical_id"),
                metadata.get("id"),
                metadata.get("name"),
                description,
            )
        )
        for value in metadata.get("formats", []) if isinstance(metadata.get("formats"), list) else []:
            if value:
                formats.add(str(value).casefold())

        quality_metadata = []
        for key in ("quality", "qualities", "resolution", "resolutions"):
            value = metadata.get(key)
            if isinstance(value, list):
                quality_metadata.extend(str(item) for item in value if item is not None)
            elif value is not None:
                quality_metadata.append(str(value))
        text = normalized_manifest_text(
            " ".join(
                [
                    str(variant.get("canonical_id") or ""),
                    str(metadata.get("id") or ""),
                    str(metadata.get("name") or ""),
                    description,
                    " ".join(quality_metadata),
                ]
            )
        )
        height = manifest_height_from_text(text)
        if height is not None:
            max_height = max(max_height or 0, height)
            quality_signals.add(f"explicit_height:{height}")
        if re.search(r"\b(?:multi[ -]?quality|multiple quality|multi[ -]?resolution|multiple resolution)\b", text):
            quality_signals.add("multiple_quality_options")
        if re.search(r"\b(?:direct links?|direct streams?|direct streaming|cdn direct|high[ -]?speed|lightning fast|fast streaming|streams? directs?|tres rapides?)\b", text):
            quality_signals.add("direct_or_fast_delivery")
        if re.search(r"\b(?:multi[ -]?servers?|multiple (?:streaming )?servers?|server sources?)\b", text):
            quality_signals.add("multiple_servers")
        if re.search(r"\b(?:gros catalogue|large catalogue|large catalog|big catalog|tres actif|very active|sorties du jour|latest .* daily|trending)\b", text):
            quality_signals.add("catalogue_or_freshness")
        explicit_vf = bool(re.search(
            r"\b(?:vf|truefrench|version[ -]?francaise|audio[ -]?francais|french[ -]?(?:audio|dub|dubbed)|dubbed(?:[ -]?in)?[ -]?french)\b",
            text,
        ))
        explicit_vostfr = bool(re.search(
            r"\b(?:vostfr|version[ -]?originale[ -]?sous[ -]?titree?[ -]?francais|sous[ -]?titres?[ -]?francais|french[ -]?(?:sub|subbed|subtitle|subtitles)|subtitles?(?:[ -]?in)?[ -]?french)\b",
            text,
        ))
        if explicit_vf:
            language_modes.add("vf")
            languages.add("fr")
        if explicit_vostfr:
            language_modes.add("vostfr")
            languages.add("fr")
        if re.search(r"\b(?:french|francais)\b", text):
            languages.add("fr")
        if re.search(r"\b(?:english|eng|dual[ -]?audio|multi[ -]?(?:language|langue))\b", text):
            languages.add("en")

    type_signals = manifest_type_signals(" ".join(type_text_parts))
    inferred_supported_types = {
        name for name, present in type_signals.items() if present
    }
    if type_signals["anime"] and not type_signals["movie"] and not type_signals["tv"]:
        supported_types = {"anime"}
    else:
        supported_types = declared_supported_types | inferred_supported_types
        if not supported_types:
            supported_types = {"movie", "tv"}

    accepted = languages & {"fr", "en"}
    combined_text = normalized_manifest_text(" ".join(descriptions))
    if "fr" in languages and not language_modes:
        language_modes.add("fr_unspecified")
    rich_language = len(accepted) >= 2 or bool(
        re.search(r"\b(?:vf|vostfr|dual|dubbed|subbed|multi[ -]?(?:language|langue)|multi)\b", combined_text)
    )
    usable_formats = formats & {"mp4", "mkv", "m3u8", "hls", "dash", "mpd"}
    description_present = any(len(value) >= 8 for value in descriptions)

    curation_score = 0
    if max_height is not None or "multiple_quality_options" in quality_signals:
        curation_score += 3
    if quality_signals & {"direct_or_fast_delivery", "multiple_servers"}:
        curation_score += 2
    if "catalogue_or_freshness" in quality_signals:
        curation_score += 1
    if accepted:
        curation_score += 2
    if rich_language:
        curation_score += 1
    if usable_formats:
        curation_score += 1
    if description_present:
        curation_score += 1
    if len(sources) >= 2:
        curation_score += 1
        quality_signals.add("declared_by_multiple_manifests")

    return {
        "description_present": description_present,
        "max_height": max_height,
        "accepted_languages": sorted(languages),
        "supported_types": sorted(supported_types),
        "formats": sorted(formats),
        "source_count": len(sources),
        "sources": sorted(sources),
        "curation_score": curation_score,
        "quality_signals": sorted(quality_signals),
        "usable_stream_format": bool(usable_formats),
        "rich_language_description": rich_language,
        "language_modes": sorted(language_modes),
    }


def manifest_ordering_profile(result: dict[str, Any], proof: dict[str, Any]) -> dict[str, Any]:
    candidate_profile = result.get("candidate_profile", {}) if isinstance(result.get("candidate_profile"), dict) else {}
    claims = candidate_profile.get("manifest_claims_aggregated", {}) if isinstance(candidate_profile.get("manifest_claims_aggregated"), dict) else {}
    declared_modes = {str(value).casefold() for value in claims.get("language_modes", []) if value}
    languages = {str(value).casefold() for value in proof.get("manifest_accepted_languages", []) if value}

    raw_audio = {
        normalized_manifest_text(value).strip()
        for value in proof.get("audio_languages", [])
        if value
    }
    accepted_audio = {
        str(value).casefold()
        for value in proof.get("accepted_audio_languages", [])
        if value
    }
    raw_subtitles = {
        normalized_manifest_text(value).strip()
        for value in proof.get("subtitle_languages", [])
        if value
    }
    accepted_subtitles = {
        str(value).casefold()
        for value in proof.get("accepted_subtitle_languages", [])
        if value
    }

    observed_vostfr = (
        any("vostfr" in value for value in raw_audio | raw_subtitles)
        or (
            "fr" in accepted_subtitles
            and "fr" not in accepted_audio
        )
    )
    observed_vf = (
        "fr" in accepted_audio
        and not (
            observed_vostfr
            and accepted_audio == {"fr"}
            and any("vostfr" in value for value in raw_audio)
        )
    ) or any(
        re.search(r"(?:^|[^a-z])(?:vf|truefrench)(?:[^a-z]|$)", value)
        for value in raw_audio
    )

    # Runtime evidence takes precedence over broad manifest wording. A provider
    # advertising both VF and VOSTFR is classified by what it actually returned
    # during the representative request. Manifest modes are only a fallback when
    # the runtime response contains no usable language-mode evidence.
    observed_modes: set[str] = set()
    if observed_vf:
        observed_modes.add("vf")
    if observed_vostfr:
        observed_modes.add("vostfr")
    modes = observed_modes if observed_modes else declared_modes

    if "vf" in modes:
        language_group = "vf"
        language_tier = 0
    elif "vostfr" in modes:
        language_group = "vostfr"
        language_tier = 1
    elif "fr" in languages or "fr" in accepted_audio or "fr" in accepted_subtitles:
        language_group = "fr_unspecified"
        language_tier = 2
    else:
        language_group = "other"
        language_tier = 3

    measured_height = int(proof.get("effective_max_height") or 0)
    declared_height = int(proof.get("manifest_effective_height") or 0)
    health_score = int(result.get("score", 0) or 0)
    curation_score = int(proof.get("manifest_curation_score", 0) or 0)
    return {
        "language_group": language_group,
        "language_tier": language_tier,
        "quality_height": max(measured_height, declared_height),
        "health_score": health_score,
        "manifest_curation_score": curation_score,
        "provider_server_successful_response": bool(proof.get("provider_server_successful_response", False)),
        "observed_language_modes": sorted(
            mode for mode in {"vf" if observed_vf else None, "vostfr" if observed_vostfr else None} if mode
        ),
    }


def manifest_entry_sort_key(
    entry: dict[str, Any], profiles: dict[str, dict[str, Any]]
) -> tuple[int, int, int, int, int, int, int, str]:
    cid = canonical_id(str(entry.get("id", "")))
    profile = profiles.get(cid, {})
    manual_priority = int(profile.get("manual_priority", 10_000))
    tier = int(profile.get("language_tier", 3))
    height = int(profile.get("quality_height", 0))
    health = int(profile.get("health_score", 0))
    curation = int(profile.get("manifest_curation_score", 0))
    # VF, VOSTFR and other French-capable groups load highest resolutions first.
    # For VO/other-language providers, the aggregate quality/health score is the
    # primary ranking signal, followed by resolution.
    if tier <= 2:
        primary = -height
        secondary = -health
    else:
        primary = -health
        secondary = -height
    return (
        0 if entry.get("enabled") else 1,
        manual_priority,
        tier,
        primary,
        secondary,
        -curation,
        0 if profile.get("provider_server_successful_response") else 1,
        cid,
    )


def apply_aggregate_manifest_claims(
    candidates: list[dict[str, Any]], result_by_key: dict[str, dict[str, Any]]
) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        grouped.setdefault(str(candidate.get("canonical_id") or ""), []).append(candidate)

    for variants in grouped.values():
        claims = aggregate_manifest_claims(variants)
        for candidate in variants:
            result = result_by_key.get(str(candidate.get("key") or ""))
            if not isinstance(result, dict):
                continue
            evidence = result.setdefault("evidence", {})
            evidence.update(
                {
                    "manifest_description_present": claims["description_present"],
                    "manifest_supported_types": claims["supported_types"],
                    "manifest_effective_height": claims["max_height"],
                    "manifest_accepted_languages": claims["accepted_languages"],
                    "manifest_formats": claims["formats"],
                    "manifest_source_count": claims["source_count"],
                    "manifest_sources": claims["sources"],
                    "manifest_curation_score": claims["curation_score"],
                    "manifest_quality_signals": claims["quality_signals"],
                    "manifest_usable_stream_format": claims["usable_stream_format"],
                    "manifest_rich_language_description": claims["rich_language_description"],
                    "manifest_language_modes": claims["language_modes"],
                }
            )
            profile = result.setdefault("candidate_profile", {})
            profile["manifest_claims_aggregated"] = claims


def result_evidence(result: dict[str, Any]) -> dict[str, Any]:
    evidence = result.get("evidence")
    if isinstance(evidence, dict):
        return evidence

    tests = result.get("tests") if isinstance(result.get("tests"), list) else []
    healthy = [
        item
        for item in tests
        if isinstance(item, dict) and item.get("status") == "healthy"
    ]
    hosts = {
        str(host).casefold()
        for item in healthy
        for host in item.get("reachable_hosts", [])
        if host
    }
    return {
        "fixtures_tested": len(tests),
        "healthy_fixtures": len(healthy),
        "healthy_fixture_ratio": len(healthy) / len(tests) if tests else 0.0,
        "playable_fixtures": sum(
            1 for item in healthy if int(item.get("streams_playable", 0)) > 0
        ),
        "required_fixture_categories": result.get(
            "candidate_profile", {}
        ).get("required_fixture_categories", []),
        "healthy_fixture_categories": [
            item.get("fixture", {}).get("category")
            for item in healthy
            if item.get("fixture", {}).get("category")
        ],
        "streams_playable": sum(
            int(item.get("streams_playable", item.get("streams_reachable", 0)))
            for item in healthy
        ),
        "payload_verified_streams": sum(
            int(item.get("payload_verified_streams", 0)) for item in healthy
        ),
        "identity_verified_streams": sum(
            int(item.get("identity_verified_streams", 0)) for item in tests
        ),
        "identity_unverified_streams": sum(
            int(item.get("identity_unverified_streams", 0)) for item in tests
        ),
        "identity_contradiction_count": sum(
            int(item.get("identity_contradiction_count", 0)) for item in tests
        ),
        "duration_identity_mismatch_count": sum(
            int(item.get("duration_identity_mismatch_count", 0)) for item in tests
        ),
        "distinct_reachable_hosts": len(hosts),
        "reachable_hosts": sorted(hosts),
        "effective_max_height": max(
            [int(item.get("effective_max_height", 0) or 0) for item in healthy]
            or [0]
        )
        or None,
        "max_bandwidth": max(
            [int(item.get("max_bandwidth", 0) or 0) for item in healthy] or [0]
        )
        or None,
        "accepted_audio_languages": sorted(
            {
                str(value).casefold()
                for item in healthy
                for value in item.get("accepted_audio_languages", [])
            }
        ),
        "accepted_subtitle_languages": sorted(
            {
                str(value).casefold()
                for item in healthy
                for value in item.get("accepted_subtitle_languages", [])
            }
        ),
        "accepted_subtitles_advertised": sum(
            int(item.get("accepted_subtitles_advertised", 0)) for item in healthy
        ),
        "accepted_subtitles_reachable": sum(
            int(item.get("accepted_subtitles_reachable", 0)) for item in healthy
        ),
        "provider_median_latency_ms": None,
        "stream_median_latency_ms": None,
        "disallowed_streams": sum(
            int(item.get("disallowed_streams", 0)) for item in tests
        ),
    }


def independently_proven_categories(
    result: dict[str, Any], activation: dict[str, Any]
) -> set[str]:
    """Return catalogue types that independently pass current media proof.

    This is deliberately stricter than merely observing a healthy provider. A
    type is eligible only when at least one current fixture for that type has a
    verified playable payload, meets the unchanged quality/bitrate floor, and
    carries accepted FR/EN audio or subtitle evidence. The result can safely
    narrow supportedTypes without allowing a good movie to mask a broken TV
    path (or vice versa).
    """
    tests = result.get("tests") if isinstance(result.get("tests"), list) else []
    minimum_streams = int(activation.get("minimum_playable_streams", 1))
    minimum_payload = int(activation.get("minimum_payload_verified_streams", 1))
    minimum_height = int(activation.get("minimum_effective_height", 0))
    minimum_bandwidth = int(activation.get("minimum_bandwidth_bps_when_reported", 0))
    accepted_audio = {
        str(value).casefold() for value in activation.get("accepted_audio_languages", ["fr", "en"])
    }
    accepted_subtitles = {
        str(value).casefold() for value in activation.get("accepted_subtitle_languages", ["fr", "en"])
    }
    require_language = bool(activation.get("require_accepted_language_evidence", False))
    require_reachable_subtitles = bool(
        activation.get("require_reachable_accepted_subtitle_when_advertised", True)
    )
    proven: set[str] = set()
    for test in tests:
        if not isinstance(test, dict) or test.get("status") != "healthy":
            continue
        category = str((test.get("fixture") or {}).get("category") or "")
        if category not in {"movie", "tv", "anime"}:
            continue
        if int(test.get("streams_playable", 0)) < minimum_streams:
            continue
        if int(test.get("payload_verified_streams", 0)) < minimum_payload:
            continue
        height = int(test.get("effective_max_height", 0) or 0)
        bandwidth_raw = test.get("max_bandwidth")
        bandwidth = int(bandwidth_raw) if bandwidth_raw else None
        if minimum_height > 0 and height > 0 and height < minimum_height:
            continue
        if minimum_bandwidth > 0 and bandwidth is not None and bandwidth < minimum_bandwidth:
            continue
        audio = {
            str(value).casefold() for value in test.get("accepted_audio_languages", []) if value
        } & accepted_audio
        subtitles = {
            str(value).casefold() for value in test.get("accepted_subtitle_languages", []) if value
        } & accepted_subtitles
        advertised = int(test.get("accepted_subtitles_advertised", 0) or 0)
        reachable = int(test.get("accepted_subtitles_reachable", 0) or 0)
        subtitle_ok = bool(subtitles) and (
            not require_reachable_subtitles or advertised == 0 or reachable > 0
        )
        if require_language and not (audio or subtitle_ok):
            continue
        proven.add(category)
    return proven


def gate(
    passed: bool,
    evidence: Any,
    threshold: Any,
) -> dict[str, Any]:
    return {
        "passed": bool(passed),
        "evidence": evidence,
        "threshold": threshold,
    }


def evaluate_pre_stability_gates(
    item: dict[str, Any], activation: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    result = item["health"]
    proof = result_evidence(result)
    status = str(result.get("status", "runtime_error"))
    score = int(result.get("score", 0))

    minimum_score = int(activation.get("minimum_score_enabled", 70))
    minimum_fixtures = int(activation.get("minimum_healthy_fixtures", 1))
    minimum_ratio = float(activation.get("minimum_healthy_fixture_ratio", 0.5))
    require_type_coverage = bool(
        activation.get("require_declared_type_coverage", True)
    )
    minimum_streams = int(activation.get("minimum_playable_streams", 1))
    minimum_playable_fixtures = int(
        activation.get("minimum_playable_fixtures", 1)
    )
    minimum_hosts = int(activation.get("minimum_distinct_hosts", 1))
    minimum_payload = int(
        activation.get("minimum_payload_verified_streams", 1)
    )
    minimum_height = int(activation.get("minimum_effective_height", 0))
    minimum_manifest_curation_score = int(
        activation.get("minimum_manifest_curation_score", 5)
    )
    minimum_bandwidth = int(
        activation.get("minimum_bandwidth_bps_when_reported", 1_000_000)
    )
    maximum_provider_latency = int(
        activation.get("maximum_provider_median_latency_ms", 15_000)
    )
    maximum_stream_latency = int(
        activation.get("maximum_stream_median_latency_ms", 12_000)
    )

    required_categories = {
        str(value)
        for value in proof.get("required_fixture_categories", [])
        if value
    }
    healthy_categories = {
        str(value)
        for value in proof.get("healthy_fixture_categories", [])
        if value
    }
    type_scoped_activation = bool(activation.get("allow_type_scoped_activation", False))
    independently_proven = independently_proven_categories(result, activation) if type_scoped_activation else set()
    scoped_categories = required_categories & independently_proven
    effective_required_categories = scoped_categories if scoped_categories else required_categories
    representative_fixture_mode = bool(
        activation.get("representative_fixture_mode", True)
    )
    category_coverage = (
        not require_type_coverage
        or not effective_required_categories
        or (
            bool(effective_required_categories & healthy_categories)
            if representative_fixture_mode
            else effective_required_categories.issubset(healthy_categories)
        )
    )

    healthy_fixtures = int(proof.get("healthy_fixtures", 0))
    healthy_ratio = float(proof.get("healthy_fixture_ratio", 0.0) or 0.0)
    scoped_tests = [
        item for item in (result.get("tests") or [])
        if isinstance(item, dict)
        and str((item.get("fixture") or {}).get("category") or "") in scoped_categories
    ]
    # Type-scoped activation measures proven catalogue capabilities, not how many
    # arbitrary titles happened to be absent. Once a category has a current
    # verified payload, earlier primary/fallback catalogue misses remain
    # diagnostics and cannot dilute that category's activation ratio.
    scoped_healthy_categories = scoped_categories & healthy_categories
    coverage_healthy_fixtures = (
        len(scoped_healthy_categories) if scoped_categories else healthy_fixtures
    )
    coverage_ratio = (
        len(scoped_healthy_categories) / len(scoped_categories)
        if scoped_categories
        else healthy_ratio
    )
    playable_streams = int(proof.get("streams_playable", 0))
    playable_fixtures = int(proof.get("playable_fixtures", 0))
    hosts = int(proof.get("distinct_reachable_hosts", 0))
    payloads = int(proof.get("payload_verified_streams", 0))
    effective_height = int(proof.get("effective_max_height", 0) or 0)
    bandwidth_raw = proof.get("max_bandwidth")
    bandwidth = int(bandwidth_raw) if bandwidth_raw else None
    identity_verified_streams = int(proof.get("identity_verified_streams", 0) or 0)
    identity_unverified_streams = int(proof.get("identity_unverified_streams", 0) or 0)
    identity_contradictions = int(proof.get("identity_contradiction_count", 0) or 0)
    duration_identity_mismatches = int(proof.get("duration_identity_mismatch_count", 0) or 0)

    accepted_audio_languages = {
        str(value).casefold() for value in activation.get("accepted_audio_languages", ["fr", "en"])
    }
    accepted_subtitle_languages = {
        str(value).casefold() for value in activation.get("accepted_subtitle_languages", ["fr", "en"])
    }
    accepted_audio = {
        str(value).casefold()
        for value in proof.get("accepted_audio_languages", [])
        if value
    }
    accepted_subtitles = {
        str(value).casefold()
        for value in proof.get("accepted_subtitle_languages", [])
        if value
    }
    runtime_observed_languages = {
        str(value).casefold()
        for key in ("audio_languages", "subtitle_languages")
        for value in proof.get(key, [])
        if value
    }
    advertised_subtitles = int(
        proof.get("accepted_subtitles_advertised", 0)
    )
    reachable_subtitles = int(
        proof.get("accepted_subtitles_reachable", 0)
    )
    allow_audio_without_subtitles = bool(
        activation.get("allow_accepted_audio_without_subtitles", True)
    )
    require_language = bool(
        activation.get("require_accepted_language_evidence", True)
    )
    require_reachable_advertised_subtitles = bool(
        activation.get(
            "require_reachable_accepted_subtitle_when_advertised", True
        )
    )

    language_present = bool(accepted_audio or accepted_subtitles)
    subtitle_integrity = (
        not require_reachable_advertised_subtitles
        or advertised_subtitles == 0
        or reachable_subtitles > 0
    )
    # Optional subtitle tracks must not disable an otherwise playable stream with
    # accepted audio. Subtitle reachability remains relevant when subtitles are
    # the only accepted-language evidence (for example a VOSTFR stream).
    accepted_audio_path = allow_audio_without_subtitles and bool(accepted_audio)
    accepted_subtitle_path = bool(accepted_subtitles) and subtitle_integrity
    language_subtitle_pass = (
        True
        if not require_language
        else (language_present and (accepted_audio_path or accepted_subtitle_path))
    )

    provider_latency = proof.get("provider_median_latency_ms")
    stream_latency = proof.get("stream_median_latency_ms")
    provider_latency_ok = (
        provider_latency is not None
        and float(provider_latency) <= maximum_provider_latency
    )
    stream_latency_ok = (
        stream_latency is not None
        and float(stream_latency) <= maximum_stream_latency
    )

    no_p2p = (
        status != "excluded"
        and int(proof.get("disallowed_streams", 0)) == 0
    )
    manifest_height = int(proof.get("manifest_effective_height") or 0)
    manifest_languages = {
        str(value).casefold() for value in proof.get("manifest_accepted_languages", []) if value
    }
    manifest_formats = {
        str(value).casefold() for value in proof.get("manifest_formats", []) if value
    }
    manifest_curation_score = int(proof.get("manifest_curation_score", 0) or 0)
    manifest_quality_signals = [
        str(value) for value in proof.get("manifest_quality_signals", []) if value
    ]
    manifest_usable_stream_format = bool(
        proof.get("manifest_usable_stream_format", False)
        or manifest_formats & {"mp4", "mkv", "m3u8", "hls", "dash", "mpd"}
    )
    server_accessible = bool(proof.get("provider_server_accessible", False))
    manifest_description_present = bool(proof.get("manifest_description_present", False))
    runtime_light = status == "reachable" and server_accessible
    manifest_curated = (
        manifest_description_present
        and (not require_language or bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages)))
        and manifest_usable_stream_format
        and manifest_curation_score >= minimum_manifest_curation_score
    )
    current_verified_media = playable_streams >= minimum_streams and payloads >= minimum_payload
    measured_quality_ok = (
        current_verified_media
        and (minimum_height <= 0 or effective_height == 0 or effective_height >= minimum_height)
        and (minimum_bandwidth <= 0 or bandwidth is None or bandwidth >= minimum_bandwidth)
    )
    runtime_light_quality_ok = runtime_light and (
        (minimum_height > 0 and manifest_height >= minimum_height) or manifest_curated
    )
    quality_ok = measured_quality_ok or runtime_light_quality_ok

    # Some verified containers expose no audio/subtitle language tags at all.
    # In that narrow case, a current upstream manifest language may fill the
    # metadata gap, but only after the same deep run has already proved playable
    # media payloads. Any observed runtime language disables this fallback so a
    # manifest claim can never override contradictory stream evidence.
    manifest_audio_fallback_languages = manifest_languages & accepted_audio_languages
    verified_manifest_audio_fallback = (
        status == "healthy"
        and playable_streams >= minimum_streams
        and payloads >= minimum_payload
        and not runtime_observed_languages
        and bool(manifest_audio_fallback_languages)
    )
    if verified_manifest_audio_fallback:
        accepted_audio = accepted_audio | manifest_audio_fallback_languages
        language_present = bool(accepted_audio or accepted_subtitles)
        accepted_audio_path = allow_audio_without_subtitles and bool(accepted_audio)
        language_subtitle_pass = (
            True
            if not require_language
            else (language_present and (accepted_audio_path or accepted_subtitle_path))
        )

    if runtime_light:
        accepted_audio = accepted_audio | manifest_languages
        language_present = bool(accepted_audio or accepted_subtitles)
        language_subtitle_pass = (
            True
            if not require_language
            else manifest_description_present and bool(manifest_languages & (accepted_audio_languages | accepted_subtitle_languages))
        )

    gates = {
        "01_policy_safe_no_p2p": gate(
            no_p2p,
            {
                "status": status,
                "disallowed_streams": int(
                    proof.get("disallowed_streams", 0)
                ),
            },
            "no disallowed P2P/torrent output",
        ),
        "02_healthy_functional_status": gate(
            status in {"healthy", "reachable"},
            status,
            "healthy or reachable server/API",
        ),
        "03_minimum_score": gate(
            score >= minimum_score,
            score,
            minimum_score,
        ),
        "04_fixture_and_type_coverage": gate(
            (coverage_healthy_fixtures >= minimum_fixtures
            and coverage_ratio >= minimum_ratio
            and category_coverage) or (runtime_light and manifest_description_present),
            {
                "healthy_fixtures": coverage_healthy_fixtures,
                "fixtures_tested": len(scoped_categories) if scoped_categories else int(proof.get("fixtures_tested", 0)),
                "healthy_fixture_ratio": coverage_ratio,
                "required_categories": sorted(effective_required_categories),
                "original_required_categories": sorted(required_categories),
                "healthy_categories": sorted(healthy_categories),
                "activation_supported_types": sorted(scoped_categories),
                "type_scope_applied": bool(scoped_categories and scoped_categories != required_categories),
            },
            {
                "minimum_healthy_fixtures": minimum_fixtures,
                "minimum_healthy_fixture_ratio": minimum_ratio,
                "require_declared_type_coverage": require_type_coverage,
                "representative_fixture_mode": representative_fixture_mode,
            },
        ),
        "05_stream_and_fixture_coverage": gate(
            (playable_streams >= minimum_streams
            and playable_fixtures >= minimum_playable_fixtures) or runtime_light,
            {
                "playable_streams": playable_streams,
                "playable_fixtures": playable_fixtures,
            },
            {
                "minimum_playable_streams": minimum_streams,
                "minimum_playable_fixtures": minimum_playable_fixtures,
            },
        ),
        "06_distinct_host_diversity": gate(
            hosts >= minimum_hosts or runtime_light,
            {
                "distinct_reachable_hosts": hosts,
                "reachable_hosts": proof.get("reachable_hosts", []),
            },
            minimum_hosts,
        ),
        "07_verified_payload_playability": gate(
            (payloads >= minimum_payload
            and playable_streams >= minimum_streams) or runtime_light,
            {
                "payload_verified_streams": payloads,
                "playable_streams": playable_streams,
            },
            {
                "minimum_payload_verified_streams": minimum_payload,
                "minimum_playable_streams": minimum_streams,
            },
        ),
        "08_quality_and_bitrate": gate(
            quality_ok,
            {
                "effective_max_height": effective_height or None,
                "max_bandwidth": bandwidth,
                "manifest_effective_height": manifest_height or None,
                "manifest_curation_score": manifest_curation_score,
                "manifest_quality_signals": manifest_quality_signals,
                "manifest_formats": sorted(manifest_formats),
                "manifest_sources": proof.get("manifest_sources", []),
            },
            {
                "minimum_effective_height": minimum_height,
                "minimum_bandwidth_bps_when_reported": minimum_bandwidth,
                "minimum_manifest_curation_score_when_stream_is_not_returned": minimum_manifest_curation_score,
            },
        ),
        "09_language_and_subtitle_integrity": gate(
            language_subtitle_pass,
            {
                "accepted_audio_languages": sorted(accepted_audio),
                "accepted_subtitle_languages": sorted(accepted_subtitles),
                "accepted_subtitles_advertised": advertised_subtitles,
                "accepted_subtitles_reachable": reachable_subtitles,
                "runtime_observed_languages": sorted(runtime_observed_languages),
                "manifest_accepted_languages": sorted(manifest_languages),
                "verified_manifest_audio_fallback": verified_manifest_audio_fallback,
            },
            {
                "accepted_audio_languages": activation.get(
                    "accepted_audio_languages", ["fr", "en"]
                ),
                "accepted_subtitle_languages": activation.get(
                    "accepted_subtitle_languages", ["fr", "en"]
                ),
                "reachable_advertised_subtitle_required": (
                    require_reachable_advertised_subtitles
                ),
            },
        ),
        "10_content_identity_integrity": gate(
            identity_contradictions == 0 and duration_identity_mismatches == 0,
            {
                "identity_verified_streams": identity_verified_streams,
                "identity_unverified_streams": identity_unverified_streams,
                "identity_contradiction_count": identity_contradictions,
                "duration_identity_mismatch_count": duration_identity_mismatches,
            },
            {
                "maximum_identity_contradictions": 0,
                "maximum_duration_identity_mismatches": 0,
                "unknown_identity_is_not_ui_unknown_quality": True,
            },
        ),
    }
    performance = {
        "passed": provider_latency_ok and stream_latency_ok,
        "provider_median_latency_ms": provider_latency,
        "stream_median_latency_ms": stream_latency,
        "maximum_provider_median_latency_ms": maximum_provider_latency,
        "maximum_stream_median_latency_ms": maximum_stream_latency,
    }
    return gates, {
        **proof,
        "performance": performance,
        "activation_supported_types": sorted(scoped_categories),
        "activation_type_scope_applied": bool(scoped_categories and scoped_categories != required_categories),
        "activation_original_supported_types": sorted(required_categories),
    }


def all_gates_pass(gates: dict[str, dict[str, Any]]) -> bool:
    return bool(gates) and all(bool(value.get("passed")) for value in gates.values())


def inconclusive_statuses(activation: dict[str, Any]) -> set[str]:
    return {
        str(value)
        for value in activation.get(
            "inconclusive_statuses",
            ["no_streams", "blocked", "provider_unreachable", "runtime_error"],
        )
    }


def update_strict_history(
    previous: dict[str, Any],
    candidates: list[dict[str, Any]],
    results: list[dict[str, Any]],
    pre_evaluations: dict[str, tuple[dict[str, dict[str, Any]], dict[str, Any]]],
    mode: str,
    activation: dict[str, Any],
) -> dict[str, Any]:
    """Update strict validation history without turning CI ambiguity into failure.

    A matching-SHA inconclusive deep result preserves a previously established
    strict validation for a small grace window. A conclusive failure or SHA
    change resets it immediately.
    """

    variants = dict(previous.get("variants", {}))
    now = datetime.now(timezone.utc).isoformat()
    override_policy = load_overrides()
    configured_provider_patches = override_policy.get("provider_patches") or {}
    present = {candidate["key"] for candidate in candidates}
    inconclusive = inconclusive_statuses(activation)
    preserve_inconclusive = bool(
        activation.get("preserve_strict_history_on_inconclusive", True)
    )
    minimum_consecutive = int(
        activation.get("minimum_consecutive_deep_passes", 1)
    )
    minimum_total = int(activation.get("minimum_total_deep_passes", 1))

    for result in results:
        key = result["key"]
        old = dict(variants.get(key, {}))
        gates, proof = pre_evaluations[key]
        performance_pass = bool(proof.get("performance", {}).get("passed", False))
        pre_stability_pass = all_gates_pass(gates) and performance_pass
        status = str(result.get("status", "runtime_error"))
        sha256 = str(result.get("sha256", ""))
        same_sha = bool(sha256) and old.get("sha256") == sha256
        is_inconclusive = status in inconclusive

        consecutive = int(old.get("strict_consecutive_deep_passes", 0))
        total = int(old.get("strict_total_deep_passes", 0))
        consecutive_inconclusive = int(
            old.get("consecutive_inconclusive_deep_checks", 0)
        )
        validated_sha = old.get("strict_validated_sha256")
        strict_last_success_at = old.get("strict_last_success_at")

        # Migrate v5.3 history: one strict pass on the same stored SHA already
        # constitute a validated SHA even though the explicit field did not exist.
        if (
            not validated_sha
            and same_sha
            and consecutive >= minimum_consecutive
            and total >= minimum_total
            and old.get("last_deep_pre_stability_pass") is True
        ):
            validated_sha = sha256
            strict_last_success_at = old.get("last_checked_at")

        if mode == "deep":
            if not same_sha:
                consecutive = 1 if pre_stability_pass else 0
                total = 1 if pre_stability_pass else 0
                consecutive_inconclusive = 0
                validated_sha = None
                strict_last_success_at = now if pre_stability_pass else None
            elif pre_stability_pass:
                consecutive += 1
                total += 1
                consecutive_inconclusive = 0
                strict_last_success_at = now
                if consecutive >= minimum_consecutive and total >= minimum_total:
                    validated_sha = sha256
            elif is_inconclusive and preserve_inconclusive:
                consecutive_inconclusive += 1
                grace_limit = int(
                    activation.get(
                        "maximum_consecutive_inconclusive_deep_checks_for_strict_grace",
                        2,
                    )
                )
                if consecutive_inconclusive > grace_limit:
                    consecutive = 0
                    validated_sha = None
                # Up to the finite grace limit, keep strict counters and the
                # validated SHA. Beyond it, a fresh one-pass validation is needed.
            else:
                consecutive = 0
                consecutive_inconclusive = 0
                validated_sha = None

        variants[key] = {
            **old,
            "source": result.get("source"),
            "upstream_id": result.get("upstream_id"),
            "canonical_id": result.get("canonical_id"),
            "sha256": sha256,
            "last_status": status,
            "last_ci_classification": result.get("ci_classification"),
            "last_score": int(result.get("score", 0)),
            "last_checked_at": now,
            "last_mode": mode,
            "last_deep_pre_stability_pass": (
                pre_stability_pass
                if mode == "deep"
                else old.get("last_deep_pre_stability_pass")
            ),
            "strict_consecutive_deep_passes": consecutive,
            "strict_total_deep_passes": total,
            "consecutive_inconclusive_deep_checks": consecutive_inconclusive,
            "strict_validated_sha256": validated_sha,
            "strict_last_success_at": strict_last_success_at,
            "last_gate_results": gates,
            "last_performance_result": proof.get("performance", {}),
            "present_in_latest_discovery": True,
        }

    for key, old in list(variants.items()):
        if key not in present:
            variants[key] = {**old, "present_in_latest_discovery": False}

    return {"schema_version": 63, "updated_at": now, "variants": variants}


def runtime_evidence_decision(
    item: dict[str, Any],
    activation: dict[str, Any],
    evidence_registry: dict[str, Any],
    gates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Validate an exact, explicit Nuvio runtime observation.

    Runtime evidence is deliberately not a generic fallback for ``no_streams``.
    It applies only to a named provider/source/upstream id, exact JavaScript SHA,
    upstream-enabled metadata and an allowed inconclusive CI status.
    """

    cid = canonical_id(str(item.get("canonical_id") or item.get("upstream_id") or ""))
    record = evidence_registry.get("providers", {}).get(cid)
    checks: dict[str, bool] = {
        "policy_allows_runtime_evidence": bool(
            activation.get("allow_manual_runtime_evidence_for_inconclusive_only", True)
        ),
        "record_present": isinstance(record, dict),
    }
    if not isinstance(record, dict):
        return {"eligible": False, "record": None, "checks": checks, "reason": "runtime_evidence_missing"}

    status = str(item.get("health", {}).get("status", "runtime_error"))
    allowed_global = inconclusive_statuses(activation)
    allowed_record = {str(value) for value in record.get("allowed_ci_statuses", [])}
    upstream_enabled = bool(item.get("metadata", {}).get("enabled", True))
    exact_sha = str(record.get("sha256", "")) == str(item.get("sha256", ""))
    source_matches = str(record.get("source", "")) == str(item.get("source", ""))
    upstream_id_matches = canonical_id(str(record.get("upstream_id", ""))) == canonical_id(
        str(item.get("upstream_id", ""))
    )
    no_p2p = bool(gates.get("01_policy_safe_no_p2p", {}).get("passed", False))
    conclusive_failure = status in {"excluded", "unavailable", "degraded"}

    checks.update(
        {
            "record_enabled": bool(record.get("enabled", False)),
            "kind_confirmed_working": record.get("kind") == "confirmed_working_in_nuvio",
            "source_matches": source_matches,
            "upstream_id_matches": upstream_id_matches,
            "sha256_matches": exact_sha,
            "upstream_enabled": upstream_enabled,
            "status_globally_inconclusive": status in allowed_global,
            "status_allowed_by_record": status in allowed_record,
            "no_p2p_evidence": no_p2p,
            "not_conclusive_failure": not conclusive_failure,
        }
    )
    eligible = all(checks.values())
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "eligible": eligible,
        "record": record,
        "checks": checks,
        "reason": None if eligible else "runtime_evidence_rejected:" + ",".join(failed),
    }


def activation_decision(
    item: dict[str, Any],
    activation: dict[str, Any],
    history_item: dict[str, Any],
    auto_disabled: bool,
    pre_evaluation: tuple[dict[str, dict[str, Any]], dict[str, Any]],
    evidence_registry: dict[str, Any] | None = None,
    previous_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enable only a provider proven functional by the current deep run.

    Publication follows three ordered gates:
      1. DNS/access preflight succeeded;
      2. provider-specific runtime access succeeded;
      3. at least one playable stream passed the quality gates.

    Historical state, an old SHA, manual runtime evidence, or an inconclusive
    result can never enable a provider. They remain diagnostic data only.
    """
    gates, proof = pre_evaluation
    gates = {name: dict(value) for name, value in gates.items()}

    status = str(item.get("health", {}).get("status", "runtime_error"))
    upstream_enabled = bool(item.get("metadata", {}).get("enabled", True))
    respect_upstream = bool(activation.get("respect_upstream_disabled_state", True))

    dns = item.get("health", {}).get("dns_preflight") or {}
    dns_decision = dns.get("decision") if isinstance(dns, dict) else {}
    dns_status = str((dns_decision or {}).get("status") or "unknown")
    dns_pass = dns_status not in {
        "confirmed_french_block", "dns_failed", "unresolved", "unreachable"
    } and not bool(proof.get("runtime_skipped_by_dns_preflight", False))

    access_pass = bool(proof.get("provider_server_successful_response", False))
    stream_pass = (
        status == "healthy"
        and int(proof.get("streams_playable", 0)) > 0
        and int(proof.get("healthy_fixtures", 0)) > 0
    )

    gates["00_dns_or_alternative_domain"] = gate(
        dns_pass,
        {"dns_status": dns_status},
        {"required": "DNS resolution or validated alternative domain"},
    )
    gates["00_provider_specific_access"] = gate(
        access_pass,
        {
            "provider_server_successful_response": proof.get("provider_server_successful_response", False),
            "provider_server_hosts": proof.get("provider_server_hosts", []),
            "provider_server_http_statuses": proof.get("provider_server_http_statuses", []),
        },
        {"required": "successful provider-owned HTTP response"},
    )
    gates["00_current_playable_stream"] = gate(
        stream_pass,
        {
            "status": status,
            "streams_playable": proof.get("streams_playable", 0),
            "healthy_fixtures": proof.get("healthy_fixtures", 0),
            "effective_max_height": proof.get("effective_max_height"),
        },
        {"required": "at least one currently playable stream"},
    )

    current_pass = dns_pass and access_pass and stream_pass and all_gates_pass(gates)
    # ``enabled:false`` in an upstream manifest is advisory when this exact JS
    # has just passed Niakvio's own strict current deep proof. Treating the flag
    # as a hard veto caused proven-working providers (for example Desiflix) to
    # disappear with no failed activation gate. Hard P2P evidence and every
    # current DNS/access/media/quality gate above remain authoritative.
    upstream_disabled_overridden_by_current_strict_proof = bool(
        respect_upstream and not upstream_enabled and current_pass
    )
    eligible = current_pass
    enabled = eligible and not auto_disabled
    blockers = [name for name, value in gates.items() if not value.get("passed")]
    if respect_upstream and not upstream_enabled and not current_pass:
        blockers.append("upstream_disabled")
    if eligible and auto_disabled:
        blockers.append("availability_auto_disabled")

    disabled_reason = None
    if not dns_pass:
        disabled_reason = "dns_or_alternative_domain_failed"
    elif not access_pass:
        disabled_reason = "provider_specific_access_failed"
    elif not stream_pass:
        disabled_reason = "no_current_playable_stream"
    elif blockers:
        disabled_reason = "quality_gate_failed"

    return {
        "enabled": enabled,
        "activation_eligible": eligible,
        "strict_activation_eligible": eligible,
        "strict_grace_eligible": False,
        "historical_quality_grace_eligible": False,
        "runtime_evidence_eligible": False,
        "activation_mode": "strict_current" if eligible else "disabled",
        "activation_blockers": blockers,
        "activation_gates": gates,
        "proof": proof,
        "historical_quality_grace": {"eligible": False, "reason": "disabled_by_current_proof_policy"},
        "runtime_evidence": {"eligible": False, "reason": "disabled_by_current_proof_policy"},
        "disabled_reason": disabled_reason,
        "upstream_disabled_overridden_by_current_strict_proof": upstream_disabled_overridden_by_current_strict_proof,
    }

def failed_declared_ids(registry: dict[str, Any]) -> set[str]:
    output: set[str] = set()
    for report in registry.get("upstreams", {}).values():
        if not isinstance(report, dict):
            continue
        for failure in report.get("failures", []):
            if isinstance(failure, dict) and failure.get("id"):
                output.add(canonical_id(str(failure["id"])))
    return output


def has_conclusive_stream_proof(variant: dict[str, Any]) -> bool:
    health = variant.get("health", {}) if isinstance(variant.get("health"), dict) else {}
    evidence = health.get("evidence", {}) if isinstance(health.get("evidence"), dict) else {}
    return (
        health.get("status") == "healthy"
        and int(evidence.get("streams_playable", 0)) > 0
        and int(evidence.get("healthy_fixtures", 0)) > 0
    )


def healthy_categories(variant: dict[str, Any]) -> set[str]:
    health = variant.get("health", {}) if isinstance(variant.get("health"), dict) else {}
    evidence = health.get("evidence", {}) if isinstance(health.get("evidence"), dict) else {}
    return {str(value) for value in (evidence.get("healthy_fixture_categories") or []) if value}


def ci_result_is_inconclusive(variant: dict[str, Any], activation: dict[str, Any]) -> bool:
    """Treat either the explicit CI class or an inconclusive runtime status as uncertainty."""
    health = variant.get("health", {}) if isinstance(variant.get("health"), dict) else {}
    classification = str(health.get("ci_classification") or "")
    status = str(health.get("status") or "runtime_error")
    return classification == "inconclusive" or status in inconclusive_statuses(activation)


def previous_state_is_safety_quarantine(
    entry: dict[str, Any] | None, provenance: dict[str, Any] | None
) -> bool:
    """Recognize a previously published safety state without weakening its validator.

    This helper only decides whether the promoter must retain the old disabled
    artifact when current evidence is inconclusive. The activation-preservation
    validator remains authoritative and re-verifies the complete quarantine
    evidence before publication.
    """
    if not isinstance(entry, dict) or not isinstance(provenance, dict):
        return False
    if entry.get("enabled") is not False:
        return False
    filename = str(entry.get("filename") or "")
    blockers = {str(value) for value in provenance.get("activation_blockers") or []}
    mode = str(provenance.get("activation_mode") or "")
    return (
        mode == "configured_safety_quarantine"
        or "configured_safety_quarantine" in blockers
        or "catalogue_audit_playable_identity_contradiction" in blockers
        or "--nuvio-audit-quarantine--" in filename
    )


def choose_variant_with_baseline_protection(
    variants: list[dict[str, Any]],
    rank,
    lkg_record: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not variants:
        return None
    ranked = sorted(variants, key=rank, reverse=True)
    baselines = [variant for variant in ranked if bool(variant.get("baseline"))]
    record = lkg_record if isinstance(lkg_record, dict) else {}
    required_categories = {str(value) for value in (record.get("verified_categories") or []) if value}
    if not required_categories and baselines:
        metadata = baselines[0].get("metadata", {}) if isinstance(baselines[0].get("metadata"), dict) else {}
        required_categories = {
            str(value) for value in (metadata.get("supportedTypes") or [])
            if value in {"movie", "tv", "anime"}
        }
    replacements = [
        variant for variant in ranked
        if not bool(variant.get("baseline"))
        and has_conclusive_stream_proof(variant)
        and (not required_categories or required_categories.issubset(healthy_categories(variant)))
    ]
    if replacements:
        candidates = [
            *replacements,
            *[variant for variant in baselines if has_conclusive_stream_proof(variant)],
        ]
        return max(candidates, key=rank)
    if baselines:
        return max(
            baselines,
            key=lambda variant: (1 if variant.get("lkg") else 0, rank(variant)),
        )
    return ranked[0]


def main() -> int:
    sources = load_json(SOURCES_PATH, {})
    config = load_json(CONFIG_PATH, {})
    override_config = load_overrides()
    configured_provider_patches = (
        override_config.get("provider_patches", {})
        if isinstance(override_config, dict)
        else {}
    )
    override_policy = override_config
    registry = load_json(STAGE / "candidates.json")
    health = load_json(HEALTH_RESULTS_PATH)
    current_manifest = load_json(MANIFEST_PATH, {"scrapers": []})
    previous_history = load_json(HISTORY_PATH, {"variants": {}})
    previous_provenance = load_json(PROVENANCE_PATH, {"providers": {}})
    availability = load_json(AVAILABILITY_HISTORY_PATH, {"providers": {}})
    lkg_registry = load_json(LKG_PATH, {"providers": {}})
    lkg_records = lkg_registry.get("providers", {}) if isinstance(lkg_registry, dict) else {}

    if not registry or not health:
        raise RuntimeError("missing candidates or health results")

    activation = config.get("activation", {})
    configured_evidence_name = str(
        activation.get("manual_runtime_evidence_file", RUNTIME_EVIDENCE_PATH.name)
    )
    configured_evidence_path = (ROOT / configured_evidence_name).resolve()
    if configured_evidence_path.parent != ROOT.resolve():
        raise RuntimeError("runtime evidence file must be located at repository root")
    runtime_evidence = load_json(configured_evidence_path, {"providers": {}})
    required_mode = str(activation.get("required_validation_mode", "deep"))
    mode = str(health.get("mode", ""))
    if mode != required_mode:
        raise RuntimeError(
            f"{required_mode} validation is required for publication; got {mode!r}"
        )

    configured = set(sources.get("upstreams", {}))
    loaded = {
        key
        for key, value in registry.get("upstreams", {}).items()
        if isinstance(value, dict) and value.get("status") == "loaded"
    }
    missing = sorted(configured - loaded)
    if missing:
        raise RuntimeError(
            "all configured upstream manifests are required: " + ", ".join(missing)
        )

    candidates = registry.get("candidates", [])
    results = health.get("results", [])
    result_by_key = {
        result["key"]: result
        for result in results
        if isinstance(result, dict) and result.get("key")
    }
    candidate_by_key = {candidate["key"]: candidate for candidate in candidates}
    unchecked = sorted(
        candidate["key"]
        for candidate in candidates
        if candidate["key"] not in result_by_key
    )
    if unchecked:
        raise RuntimeError("unchecked candidates: " + ", ".join(unchecked[:20]))

    # Merge descriptions, languages, formats and quality signals from every
    # canonical variant before ranking or activation. One incomplete upstream
    # entry can no longer erase richer metadata declared by either of the other
    # two manifests.
    apply_aggregate_manifest_claims(candidates, result_by_key)

    pre_evaluations = {
        key: evaluate_pre_stability_gates(
            {**candidate_by_key[key], "health": result},
            activation,
        )
        for key, result in result_by_key.items()
        if key in candidate_by_key
    }
    history = update_strict_history(
        previous_history,
        candidates,
        results,
        pre_evaluations,
        mode,
        activation,
    )
    history_variants = history.get("variants", {})

    by_cid: dict[str, list[dict[str, Any]]] = {}
    dynamic_excluded: set[str] = set()
    for candidate in candidates:
        result = result_by_key[candidate["key"]]
        if result.get("status") == "excluded":
            dynamic_excluded.add(candidate["canonical_id"])
            continue
        by_cid.setdefault(candidate["canonical_id"], []).append(
            {**candidate, "health": result}
        )

    existing = {
        canonical_id(str(entry.get("id", ""))): dict(entry)
        for entry in current_manifest.get("scrapers", [])
        if isinstance(entry, dict) and entry.get("id")
    }
    explicit = excluded_ids(sources)
    failed_ids = failed_declared_ids(registry)
    availability_states = availability.get("providers", {})
    activation_lkg_payload = load_json(ACTIVATION_LKG_PATH, {}) or {}
    activation_lkg_ids = {
        canonical_id(str(value))
        for value in activation_lkg_payload.get("active_ids", [])
        if str(value).strip()
    }

    entries: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    report_items: list[dict[str, Any]] = []
    priority_values = (sources.get("selection_policy") or {}).get("manual_provider_priority") or []
    manual_priority = {canonical_id(str(value)): index for index, value in enumerate(priority_values)}
    manifest_order_profiles: dict[str, dict[str, Any]] = {
        cid: {"manual_priority": index} for cid, index in manual_priority.items()
    }
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    all_ids = sorted(
        set(by_cid)
        | failed_ids
        | dynamic_excluded
        | (explicit & set(existing))
    )
    for cid in all_ids:
        if cid in explicit or cid in dynamic_excluded:
            report_items.append(
                {
                    "id": cid,
                    "action": "removed-disallowed-p2p",
                    "enabled": False,
                    "activation_eligible": False,
                    "failed_gates": ["01_policy_safe_no_p2p"],
                    "activation_gates": {},
                    "variant_count": 0,
                }
            )
            continue

        variants = by_cid.get(cid, [])
        auto_disabled = bool(
            availability_states.get(cid, {}).get("auto_disabled", False)
        )
        decisions: dict[str, dict[str, Any]] = {}

        for variant in variants:
            decisions[variant["key"]] = activation_decision(
                variant,
                activation,
                history_variants.get(variant["key"], {}),
                auto_disabled,
                pre_evaluations[variant["key"]],
                runtime_evidence,
                previous_provenance.get("providers", {}).get(variant["canonical_id"], {}),
            )
            provider_policy = configured_provider_patches.get(cid, {})
            manifest_overrides = provider_policy.get("manifest_overrides", {}) if isinstance(provider_policy, dict) else {}
            if isinstance(manifest_overrides, dict) and manifest_overrides.get("enabled") is False:
                decision = decisions[variant["key"]]
                decision["enabled"] = False
                decision["activation_eligible"] = False
                decision["strict_activation_eligible"] = False
                decision["activation_mode"] = "disabled"
                if "configured_safety_quarantine" not in decision["activation_blockers"]:
                    decision["activation_blockers"].append("configured_safety_quarantine")
                decision["disabled_reason"] = "configured_safety_quarantine"

        def rank(variant: dict[str, Any]) -> tuple[int, int, int, int, int, int, int]:
            decision = decisions[variant["key"]]
            gates = decision["activation_gates"]
            proof = decision["proof"]
            mode_priority = {
                "strict_current": 3,
                "disabled": 0,
            }.get(decision["activation_mode"], 0)
            passed_gates = sum(1 for value in gates.values() if value.get("passed"))
            return (
                1 if decision["activation_eligible"] else 0,
                mode_priority,
                passed_gates,
                int(variant["health"].get("score", 0)),
                int(proof.get("healthy_fixtures", 0)),
                int(proof.get("distinct_reachable_hosts", 0)),
                -int(variant.get("source_priority", 999)),
            )

        lkg_record = lkg_records.get(cid, {}) if isinstance(lkg_records, dict) else {}
        selected = choose_variant_with_baseline_protection(variants, rank, lkg_record)

        if selected is not None:
            decision = decisions[selected["key"]]
            enabled = bool(decision["enabled"])
            eligible = bool(decision["activation_eligible"])
            blockers = list(decision["activation_blockers"])
            gates = decision["activation_gates"]
            proof = decision["proof"]
            activation_mode = decision["activation_mode"]

            # CI cannot reliably distinguish a provider that is genuinely dead
            # from one whose search/runtime is blocked or content-specific. A
            # new provider still requires current positive proof, but a provider
            # already enabled in the published manifest is preserved when the
            # current result is merely inconclusive. It is disabled only by an
            # explicit exclusion, an upstream-disabled declaration, sustained
            # availability failure, or another conclusive failure.
            old_entry = existing.get(cid, {})
            observed_status = str(selected.get("health", {}).get("status", "runtime_error"))
            selected_upstream_enabled = bool(selected.get("metadata", {}).get("enabled", True))
            # A published-baseline candidate reflects our previous local manifest,
            # not the current upstream activation declaration. When baseline
            # protection selects it because every live probe is inconclusive,
            # derive the upstream veto from current non-baseline manifests.
            live_upstream_variants = [
                variant
                for variant in variants
                if str(variant.get("source") or "") != "published-baseline"
            ]
            upstream_enabled = (
                any(
                    bool((variant.get("metadata") or {}).get("enabled", True))
                    for variant in live_upstream_variants
                )
                if live_upstream_variants
                else selected_upstream_enabled
            )
            if upstream_enabled and "upstream_disabled" in blockers:
                blockers = [value for value in blockers if value != "upstream_disabled"]
            preserve_statuses = {
                str(value)
                for value in activation.get(
                    "preserve_enabled_on_ci_uncertain_statuses",
                    [
                        "blocked",
                        "provider_unreachable",
                        "runtime_error",
                        "no_streams",
                        "reachable",
                    ],
                )
            }
            old_filename = old_entry.get("filename") if isinstance(old_entry, dict) else None
            old_target = (ROOT / old_filename).resolve() if isinstance(old_filename, str) else None
            old_artifact_available = bool(
                old_target
                and is_under(old_target, ROOT / "providers")
                and old_target.exists()
            )
            old_was_enabled = bool(old_entry.get("enabled", False))
            old_provenance = previous_provenance.get("providers", {}).get(cid, {})
            old_safety_quarantine = previous_state_is_safety_quarantine(old_entry, old_provenance)
            current_ci_inconclusive = ci_result_is_inconclusive(selected, activation)
            restore_activation_lkg = bool(
                cid in activation_lkg_ids
                and current_ci_inconclusive
                and gates.get("01_policy_safe_no_p2p", {}).get("passed", False)
            )
            preserve_previous_state = (
                not enabled
                and current_ci_inconclusive
                and (old_was_enabled or restore_activation_lkg or old_safety_quarantine)
                and not auto_disabled
                and upstream_enabled
                and old_artifact_available
                and observed_status in preserve_statuses
                and not metadata_is_excluded(old_entry, sources)
            )
            if preserve_previous_state:
                retained = dict(old_entry)
                # Never turn a proven safety quarantine back on merely because
                # the new CI run is uncertain. Conversely, an LKG-active state
                # remains active until current conclusive evidence says otherwise.
                retained["enabled"] = False if old_safety_quarantine else True
                entries[cid] = retained
                retained_digest = hashlib.sha256(old_target.read_bytes()).hexdigest()

                if old_safety_quarantine:
                    provenance[cid] = {
                        **old_provenance,
                        "checked_at": now,
                        "check_mode": mode,
                        "check_status": observed_status,
                        "preserved_reason": "ci_uncertain_kept_last_conclusive_safety_quarantine",
                        "preserved_candidate_key": selected.get("key"),
                        "preserved_candidate_sha256": selected.get("sha256"),
                    }
                    report_items.append(
                        {
                            "id": cid,
                            "action": "preserved-conclusive-safety-quarantine-ci-uncertain",
                            "enabled": False,
                            "activation_eligible": False,
                            "activation_mode": str(old_provenance.get("activation_mode") or "safety_quarantine"),
                            "failed_gates": [
                                name for name, value in gates.items() if not value.get("passed")
                            ],
                            "activation_blockers": list(old_provenance.get("activation_blockers") or blockers),
                            "activation_gates": gates,
                            "observed_status": observed_status,
                            "published_filename": old_filename,
                            "variant_count": len(variants),
                        }
                    )
                else:
                    provenance[cid] = {
                        **old_provenance,
                        "id": cid,
                        "published_filename": old_filename,
                        "sha256": retained_digest,
                        "patched_sha256": retained_digest,
                        "checked_at": now,
                        "check_mode": mode,
                        "check_status": observed_status,
                        "activation_eligible": False,
                        "activation_mode": "preserved_current_ci_uncertain",
                        "activation_blockers": blockers,
                        "preserved_reason": "ci_uncertain_kept_last_published_artifact",
                        "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                        "preservation_upstream_enabled": upstream_enabled,
                        "preservation_live_upstream_sources": sorted(
                            {
                                str(variant.get("source") or "")
                                for variant in live_upstream_variants
                                if str(variant.get("source") or "")
                            }
                        ),
                        "preserved_candidate_key": selected.get("key"),
                        "preserved_candidate_sha256": selected.get("sha256"),
                    }
                    report_items.append(
                        {
                            "id": cid,
                            "action": (
                                "restored-activation-lkg-enabled-ci-uncertain"
                                if restore_activation_lkg and not old_was_enabled
                                else "preserved-current-enabled-ci-uncertain"
                            ),
                            "enabled": True,
                            "restored_from_activation_lkg": bool(restore_activation_lkg and not old_was_enabled),
                            "preservation_upstream_enabled": upstream_enabled,
                            "activation_eligible": False,
                            "activation_mode": "preserved_current_ci_uncertain",
                            "failed_gates": [
                                name for name, value in gates.items() if not value.get("passed")
                            ],
                            "activation_blockers": blockers,
                            "activation_gates": gates,
                            "observed_status": observed_status,
                            "published_filename": old_filename,
                            "variant_count": len(variants),
                        }
                    )
                continue

            try:
                destination, digest = copy_candidate(selected)
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                # A generated candidate may still be invalid after all upstream
                # checks. Reject only that candidate, retain the last published
                # local artifact when it is safe, and continue promoting the
                # remaining providers. The validator diagnostic is surfaced in
                # the Actions log instead of being hidden by capture_output.
                print(
                    f"::error title=Provider candidate rejected::{cid}: {exc}",
                    file=sys.stderr,
                )
                old_entry = existing.get(cid)
                filename = old_entry.get("filename") if old_entry else None
                target = (ROOT / filename).resolve() if isinstance(filename, str) else None
                if (
                    old_entry
                    and target
                    and is_under(target, ROOT / "providers")
                    and target.exists()
                    and not metadata_is_excluded(old_entry, sources)
                ):
                    retained = dict(old_entry)
                    retained["enabled"] = bool(old_entry.get("enabled", False))
                    entries[cid] = retained
                    old_provenance = previous_provenance.get("providers", {}).get(cid, {})
                    provenance[cid] = {
                        **old_provenance,
                        "id": cid,
                        "published_filename": filename,
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "activation_eligible": False,
                        "activation_blockers": ["generated_candidate_validation_failed"],
                        "promotion_error": str(exc),
                    }
                    report_items.append(
                        {
                            "id": cid,
                            "action": "retained-local-copy-generated-candidate-invalid",
                            "enabled": bool(retained.get("enabled", False)),
                            "activation_eligible": False,
                            "failed_gates": [],
                            "activation_blockers": ["generated_candidate_validation_failed"],
                            "activation_gates": {},
                            "promotion_error": str(exc),
                            "variant_count": len(variants),
                        }
                    )
                else:
                    report_items.append(
                        {
                            "id": cid,
                            "action": "omitted-generated-candidate-invalid-no-local-copy",
                            "enabled": False,
                            "activation_eligible": False,
                            "failed_gates": [],
                            "activation_blockers": ["generated_candidate_validation_failed"],
                            "activation_gates": {},
                            "promotion_error": str(exc),
                            "variant_count": len(variants),
                        }
                    )
                continue
            result = selected["health"]
            aggregated_claims = (
                result.get("candidate_profile", {}).get("manifest_claims_aggregated", {})
                if isinstance(result.get("candidate_profile"), dict)
                else {}
            )
            promoted_entry = build_entry(selected, destination, enabled, aggregated_claims)
            activation_supported_types = [
                str(value) for value in (proof.get("activation_supported_types") or [])
                if str(value) in {"movie", "tv", "anime"}
            ]
            provider_policy = (override_policy.get("provider_patches") or {}).get(cid, {})
            capability_policy = (override_policy.get("provider_capabilities") or {}).get(cid, {})
            authoritative_published_types = [
                str(value) for value in (provider_policy.get("published_types") or [])
                if str(value) in {"movie", "tv", "anime"}
            ] if isinstance(provider_policy, dict) else []
            curated_capability_types = [
                str(value) for value in (capability_policy.get("catalogue_types") or [])
                if str(value) in {"movie", "tv", "anime"}
            ] if isinstance(capability_policy, dict) else []
            authoritative_catalogue_types = authoritative_published_types or curated_capability_types
            if (
                enabled
                and activation_mode == "strict_current"
                and activation_supported_types
                and not authoritative_catalogue_types
            ):
                promoted_entry["supportedTypes"] = activation_supported_types
            promoted_entry["version"] = provider_entry_version(promoted_entry, existing.get(cid))
            entries[cid] = promoted_entry
            ordering = manifest_ordering_profile(result, proof)
            ordering["manual_priority"] = manual_priority.get(cid, 10_000)
            manifest_order_profiles[cid] = ordering

            failed_gate_names = [
                name for name, value in gates.items() if not value.get("passed")
            ]
            if enabled and activation_mode == "strict_current":
                action = "enabled-current-dns-access-stream-quality-passed"
            elif enabled and activation_mode == "preserved_current_inconclusive":
                action = "preserved-current-enabled-ci-inconclusive"
            elif enabled and activation_mode == "strict_grace_inconclusive":
                action = "enabled-strict-validation-grace-ci-inconclusive"
            elif enabled and activation_mode == "historical_quality_grace":
                action = "enabled-same-sha-prior-score-and-quality-gates"
            elif enabled and activation_mode == "runtime_evidence":
                action = "enabled-sha-pinned-nuvio-runtime-evidence"
            elif eligible and auto_disabled:
                action = "disabled-sustained-outage"
            elif failed_gate_names == ["11_performance_and_stability"]:
                action = "published-disabled-probation-or-performance"
            elif str(result.get("status")) in inconclusive_statuses(activation):
                action = "published-disabled-ci-inconclusive-no-valid-runtime-evidence"
            else:
                action = "published-disabled-failed-gates"

            provenance[cid] = {
                "id": cid,
                "published_filename": destination.relative_to(ROOT).as_posix(),
                "sha256": digest,
                "patched_sha256": digest,
                "upstream_sha256": selected.get("upstream_sha256"),
                "local_patches": selected.get("local_patches", []),
                "source": selected.get("source"),
                "source_name": selected.get("source_name"),
                "source_repository": selected.get("source_repository"),
                "source_license": selected.get("source_license"),
                "source_license_evidence": selected.get(
                    "source_license_evidence"
                ),
                "upstream_id": selected.get("upstream_id"),
                "upstream_filename": selected.get("metadata", {}).get("filename"),
                "checked_at": now,
                "check_mode": mode,
                "check_status": result.get("status"),
                "health_score": int(result.get("score", 0)),
                "activation_eligible": eligible,
                "strict_activation_eligible": bool(decision["strict_activation_eligible"]),
                "strict_grace_eligible": bool(decision["strict_grace_eligible"]),
                "historical_quality_grace_eligible": bool(decision["historical_quality_grace_eligible"]),
                "runtime_evidence_eligible": bool(decision["runtime_evidence_eligible"]),
                "activation_mode": activation_mode,
                "activation_blockers": blockers,
                "activation_gates": gates,
                "manifest_ordering": ordering,
                "settings_validation": {
                    "settings_profiles_tested": proof.get("settings_profiles_tested", 0),
                    "settings_profiles_producing_streams": proof.get("settings_profiles_producing_streams", 0),
                    "selected_settings_profiles": proof.get("selected_settings_profiles", []),
                    "selected_setting_keys": proof.get("selected_setting_keys", []),
                },
                "historical_quality_grace": decision["historical_quality_grace"],
                "runtime_evidence": decision["runtime_evidence"],
                "strict_consecutive_deep_passes": int(
                    history_variants.get(selected["key"], {}).get(
                        "strict_consecutive_deep_passes", 0
                    )
                ),
                "strict_total_deep_passes": int(
                    history_variants.get(selected["key"], {}).get(
                        "strict_total_deep_passes", 0
                    )
                ),
            }
            report_items.append(
                {
                    "id": cid,
                    "action": action,
                    "enabled": enabled,
                    "activation_eligible": eligible,
                    "strict_activation_eligible": bool(decision["strict_activation_eligible"]),
                    "strict_grace_eligible": bool(decision["strict_grace_eligible"]),
                    "runtime_evidence_eligible": bool(decision["runtime_evidence_eligible"]),
                    "activation_mode": activation_mode,
                    "historical_quality_grace": decision["historical_quality_grace"],
                    "runtime_evidence": decision["runtime_evidence"],
                    "failed_gates": [
                        name
                        for name, value in gates.items()
                        if not value.get("passed")
                    ],
                    "activation_blockers": blockers,
                    "activation_gates": gates,
                    "selected_source": selected.get("source"),
                    "selected_upstream_id": selected.get("upstream_id"),
                    "observed_status": result.get("status"),
                    "observed_score": int(result.get("score", 0)),
                    "manifest_ordering": ordering,
                    "settings_validation": {
                        "settings_profiles_tested": proof.get("settings_profiles_tested", 0),
                        "settings_profiles_producing_streams": proof.get("settings_profiles_producing_streams", 0),
                        "selected_settings_profiles": proof.get("selected_settings_profiles", []),
                        "selected_setting_keys": proof.get("selected_setting_keys", []),
                        "settings_diagnostics": proof.get("settings_diagnostics", []),
                    },
                    "evidence": proof,
                    "variant_count": len(variants),
                }
            )
            continue

        old_entry = existing.get(cid)
        filename = old_entry.get("filename") if old_entry else None
        target = (ROOT / filename).resolve() if isinstance(filename, str) else None
        if (
            old_entry
            and target
            and is_under(target, ROOT / "providers")
            and target.exists()
            and not metadata_is_excluded(old_entry, sources)
        ):
            retained = dict(old_entry)
            # A transient source download failure must not disable a published
            # local provider.
            retained["enabled"] = bool(old_entry.get("enabled", False))
            entries[cid] = retained
            old_provenance = previous_provenance.get("providers", {}).get(cid, {})
            provenance[cid] = {
                **old_provenance,
                "id": cid,
                "published_filename": filename,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "activation_eligible": False,
                "activation_blockers": ["declared_but_download_failed"],
            }
            report_items.append(
                {
                    "id": cid,
                    "action": "retained-local-copy-download-failed",
                    "enabled": bool(retained.get("enabled", False)),
                    "activation_eligible": False,
                    "failed_gates": [],
                    "activation_blockers": ["declared_but_download_failed"],
                    "activation_gates": {},
                    "variant_count": 0,
                }
            )
        else:
            report_items.append(
                {
                    "id": cid,
                    "action": "omitted-download-failed-no-local-copy",
                    "enabled": False,
                    "activation_eligible": False,
                    "failed_gates": [],
                    "activation_blockers": ["declared_but_download_failed"],
                    "activation_gates": {},
                    "variant_count": 0,
                }
            )

    base_version = sources.get("repository", {}).get("manifest_version", "5.13.0")
    candidate_manifest = {
        "name": sources.get("repository", {}).get("name", "Nuvio Curated Providers"),
        "scrapers": sorted(
            entries.values(),
            key=lambda entry: manifest_entry_sort_key(entry, manifest_order_profiles),
        ),
    }
    payload_changed = (
        manifest_payload_without_version(current_manifest)
        != manifest_payload_without_version(candidate_manifest)
    )
    manifest = {
        **candidate_manifest,
        "version": next_manifest_version(
            str(current_manifest.get("version", "")),
            str(base_version),
            payload_changed,
        ),
    }
    validate_manifest(manifest, sources)

    manifest_positions = {
        canonical_id(str(entry.get("id", ""))): index
        for index, entry in enumerate(manifest["scrapers"], start=1)
    }
    for item in report_items:
        item["manifest_position"] = manifest_positions.get(
            canonical_id(str(item.get("id", "")))
        )
    report_items.sort(
        key=lambda item: (
            item.get("manifest_position") is None,
            int(item.get("manifest_position") or 10**9),
            canonical_id(str(item.get("id", ""))),
        )
    )

    enabled_count = sum(1 for entry in manifest["scrapers"] if entry.get("enabled"))
    eligible_count = sum(
        1 for item in report_items if item.get("activation_eligible") is True
    )
    strict_enabled_count = sum(
        1 for item in report_items
        if item.get("enabled") is True and item.get("activation_mode") == "strict"
    )
    strict_grace_enabled_count = sum(
        1 for item in report_items
        if item.get("enabled") is True
        and item.get("activation_mode") == "strict_grace_inconclusive"
    )
    runtime_evidence_enabled_count = sum(
        1 for item in report_items
        if item.get("enabled") is True
        and item.get("activation_mode") == "runtime_evidence"
    )
    inconclusive_disabled_count = sum(
        1 for item in report_items
        if item.get("enabled") is False
        and item.get("observed_status") in inconclusive_statuses(activation)
    )
    disabled_count = len(manifest["scrapers"]) - enabled_count

    thresholds = {
        key: activation.get(key)
        for key in (
            "required_validation_mode",
            "minimum_score_enabled",
            "minimum_healthy_fixtures",
            "minimum_healthy_fixture_ratio",
            "require_declared_type_coverage",
            "representative_fixture_mode",
            "minimum_playable_streams",
            "minimum_playable_fixtures",
            "minimum_distinct_hosts",
            "minimum_payload_verified_streams",
            "minimum_effective_height",
            "minimum_manifest_curation_score",
            "preferred_height",
            "minimum_bandwidth_bps_when_reported",
            "accepted_audio_languages",
            "accepted_subtitle_languages",
            "require_accepted_language_evidence",
            "require_reachable_accepted_subtitle_when_advertised",
            "maximum_provider_median_latency_ms",
            "maximum_stream_median_latency_ms",
            "minimum_consecutive_deep_passes",
            "minimum_total_deep_passes",
            "maximum_consecutive_inconclusive_deep_checks_for_strict_grace",
            "inconclusive_statuses",
            "manual_runtime_evidence_file",
            "respect_upstream_disabled_state",
        )
    }
    public_report = {
        "schema_version": 63,
        "generated_at": now,
        "test_environment": health.get("environment"),
        "test_mode": mode,
        "upstream_manifest_count": len(configured),
        "upstream_manifests_loaded": sorted(loaded),
        "candidate_variants_checked": len(candidates),
        "canonical_providers_discovered": len(by_cid),
        "excluded_during_discovery": registry.get("excluded_count", 0),
        "published_providers": len(manifest["scrapers"]),
        "enabled_providers": enabled_count,
        "disabled_providers": disabled_count,
        "activation_eligible_providers": eligible_count,
        "strictly_validated_enabled_providers": strict_enabled_count,
        "strict_grace_enabled_providers": strict_grace_enabled_count,
        "runtime_evidence_enabled_providers": runtime_evidence_enabled_count,
        "ci_inconclusive_disabled_providers": inconclusive_disabled_count,
        "status_counts": health.get("counts", {}),
        "activation_gate_count": 11,
        "activation_thresholds": thresholds,
        "activation_gate_names": [
            "01_policy_safe_no_p2p",
            "02_healthy_functional_status",
            "03_minimum_score",
            "04_fixture_and_type_coverage",
            "05_stream_and_fixture_coverage",
            "06_distinct_host_diversity",
            "07_verified_payload_playability",
            "08_quality_and_bitrate",
            "09_language_and_subtitle_integrity",
            "10_content_identity_integrity",
            "11_performance_and_stability",
        ],
        "policy": {
            "no_static_provider_preselection": True,
            "all_three_manifests_required": True,
            "all_candidates_checked_before_publication": True,
            "deduplication_after_checks": True,
            "upstream_metadata_preserved_with_canonical_supported_types_union": True,
            "all_eleven_activation_gates_are_mandatory_for_automatic_activation": True,
            "sha_pinned_runtime_evidence_only_resolves_ci_inconclusive_results": True,
            "runtime_evidence_never_overrides_p2p_hard_failure_or_sha_change": True,
            "previous_strict_validation_has_finite_inconclusive_grace": True,
            "quick_checks_are_report_only": True,
            "deep_checks_are_required_for_publication": True,
            "all_other_discovered_providers_published_disabled": True,
            "p2p_and_torrent_excluded": True,
            "content_addressed_files": True,
            "enabled_manifest_order": [
                "vf",
                "vostfr",
                "fr_unspecified",
                "other",
            ],
            "within_language_group_order": {
                "vf_vostfr_fr": [
                    "quality_height_desc",
                    "health_score_desc",
                    "manifest_curation_score_desc",
                ],
                "other": [
                    "health_score_desc",
                    "quality_height_desc",
                    "manifest_curation_score_desc",
                ],
            },
            "content_type_inference": "merged supportedTypes plus explicit films/series/anime descriptions",
            "derived_language_manifests": {
                "vf/manifest.json": ["vf"],
            },
        },
        "providers": report_items,
    }
    provenance_payload = {
        "schema_version": 63,
        "generated_at": now,
        "notice": (
            "Third-party files retain upstream authorship and licence. "
            "See THIRD_PARTY_NOTICES.md."
        ),
        "providers": {cid: provenance[cid] for cid in sorted(provenance)},
    }

    atomic_write_json(HISTORY_PATH, history)
    atomic_write_json(REPORT_PATH, public_report)
    atomic_write_json(PROVENANCE_PATH, provenance_payload)
    atomic_write_json(NEXT_MANIFEST_PATH, manifest)
    print(
        f"Checked {len(candidates)} variants from {len(configured)} manifests; "
        f"published {len(manifest['scrapers'])} unique providers, "
        f"{enabled_count} enabled by strict validation, finite strict grace, "
        f"or exact runtime evidence; {disabled_count} disabled."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
