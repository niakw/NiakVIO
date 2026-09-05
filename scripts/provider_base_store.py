#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides, _strip_generated_core_tail
from provider_byte_stability import split_owned_prefix_bootstraps
from provider_patch_blocks import (
    PROVIDER_BEGIN_MARKER,
    PROVIDER_END_MARKER,
    render_managed_fix,
    strip_all_managed_fixes,
    validate_managed_fixes,
)

ROOT = Path(__file__).resolve().parents[1]
BASES = ROOT / "provider-bases"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
QUARANTINE_PATCH = "scripts/provider_patches/quarantine_provider_v1.py"

# Read-only migration identifiers. These files are intentionally absent from the
# clean-v3 patch surface; their names may still appear in historical provenance.
LEGACY_SOURCE_PATCH_PATHS = {
    "scripts/provider_patches/runtime_repository_domain_materializer_v1.py",
    "scripts/provider_patches/adaptive_domain_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
    "scripts/provider_patches/castle_strict_identity_v1.py",
}
DERIVED_PATCH_SCRIPTS = {QUARANTINE_PATCH}

# Clean reconstruction never replays historical source-shape patch paths.
CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS = (
    DERIVED_PATCH_SCRIPTS | LEGACY_SOURCE_PATCH_PATHS
)

# ProviderBase owns durable provider logic. Everything below is derived publication
# state and must never become an input to the next Core build.
DERIVED_BASE_MARKERS = (
    "NIAKVIO_FIX",
    "NUVIO_PROVIDER_SECURITY_HARDENING_V1",
    "NUVIO_PROVIDER_CONSOLE_SHADOW_V1",
    "NUVIO_PROVIDER_QUARANTINE_V1",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
    "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
    "NUVIO_STREAM_OUTPUT_SANITIZER_V4",
    "NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5",
    "NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6",
    "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1",
    "NUVIO_GLOBAL_PROVIDER_EXECUTION_BUDGET_V1",
    "NUVIO_NATIVE_HLS_INTEGRITY_BUDGET_V1",
    "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
    "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
    "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
    "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
    "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5",
    "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1",
    "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1",
    "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1",
)

CLEAN_RECONSTRUCTION_SOURCE = "niakvio-clean-reconstruction-v3"
CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE = "niakvio-clean-reconstruction-v3-candidate"
CLEAN_RECONSTRUCTION_AUTHORING_VERSION = 3
PROVIDER_BASE_OWNED_MARKER = "NIAKVIO_PROVIDER_BASE_OWNED_V3"
CURRENT_PROVIDER_MODEL_AUTHORING = "niakvio-owned-v3"
PROVIDER_BASE_AUTHORING_MARKER = f"NIAKVIO_PROVIDER_BASE_AUTHORING:{CURRENT_PROVIDER_MODEL_AUTHORING}"
INITIAL_RECONSTRUCTION_SCOPE = 96


def is_clean_reconstructed(provenance_row: dict[str, Any] | None) -> bool:
    row = provenance_row if isinstance(provenance_row, dict) else {}
    return (
        str(row.get("base_source") or "") == CLEAN_RECONSTRUCTION_SOURCE
        and row.get("clean_reconstruction_verified") is True
        and int(row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    )


def requires_clean_reconstruction(provenance_row: dict[str, Any] | None) -> bool:
    return not is_clean_reconstructed(provenance_row)


def is_clean_reconstruction_candidate(provenance_row: dict[str, Any] | None) -> bool:
    row = provenance_row if isinstance(provenance_row, dict) else {}
    return (
        str(row.get("base_source") or "") == CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE
        and row.get("clean_reconstruction_candidate") is True
        and row.get("clean_reconstruction_verified") is not True
        and int(row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    )


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


NON_EXECUTABLE_KNOWLEDGE_HOSTS = {
    "npms.io", "lodash.com", "www.lodash.com", "openjsf.org", "www.openjsf.org",
    "underscorejs.org", "www.underscorejs.org", "arm.haglund.dev", "v3-cinemeta.strem.io",
}


def _provider_data_url_is_executable(value: object) -> bool:
    text = str(value or "").strip()
    if not text or "${" in text or "encodeURIComponent(" in text:
        return False
    lowered = text.casefold()
    return not any(f"://{host}" in lowered for host in NON_EXECUTABLE_KNOWLEDGE_HOSTS)


def _provider_data_route_is_executable(value: object) -> bool:
    text = str(value or "").strip()
    if not text or "${" in text or "encodeURIComponent(" in text or "decodeURIComponent(" in text:
        return False
    lowered = text.casefold()
    if "q=ponyfill" in lowered or lowered.rstrip("/") == "/license":
        return False
    if text.count("{") != text.count("}") or text.count("[") != text.count("]") or text.count("(") != text.count(")"):
        return False
    if re.search(r"(?:\(\?:|\(\?=|\(\?!|\\[dDsSwW][+*?]?|\[[^\]]*$|(?:^|[/_-])i\[$)", text, re.I):
        return False
    if re.search(r"\.(?:css|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)", text, re.I):
        return False
    if re.search(r"/(?:refs/heads/[^/]+/)?domains?\.json(?:[?#]|$)", text, re.I):
        return False
    return True


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_relative(provider_id: str, digest: str) -> str:
    return f"provider-bases/{safe_fragment(provider_id.casefold())}--base--{digest[:16]}.js"


def safe_base_path(relative: str) -> Path | None:
    if not isinstance(relative, str) or not relative.startswith("provider-bases/"):
        return None
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(BASES.resolve())
    except ValueError:
        return None
    return path


def forbidden_base_markers(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="strict")
    return [marker for marker in DERIVED_BASE_MARKERS if marker in text]


def _strip_leaked_provider_model_data(text: str) -> tuple[str, bool]:
    """Remove only the serialized Provider DATA declaration from a contaminated base.

    References to NIAKVIO_PROVIDER_MODEL are part of the common skeleton and are
    preserved. This helper never derives code from a published provider and never
    rewrites executable logic outside the single declaration statement.
    """
    prefixes = (
        "const NIAKVIO_PROVIDER_MODEL = Object.freeze(",
        "let NIAKVIO_PROVIDER_MODEL = Object.freeze(",
        "var NIAKVIO_PROVIDER_MODEL = Object.freeze(",
    )
    starts = [(text.find(prefix), prefix) for prefix in prefixes if text.find(prefix) >= 0]
    if not starts:
        return text, False
    if len(starts) != 1:
        raise ValueError("ProviderBase contains multiple provider model DATA declarations")
    start, prefix = starts[0]
    open_paren = start + len(prefix) - 1
    depth = 0
    quote = ""
    escaped = False
    end = None
    for index in range(open_paren, len(text)):
        ch = text[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                cursor = index + 1
                while cursor < len(text) and text[cursor] in " \t":
                    cursor += 1
                if cursor >= len(text) or text[cursor] != ";":
                    raise ValueError("ProviderBase provider model DATA declaration has no terminating semicolon")
                cursor += 1
                if cursor < len(text) and text[cursor] == "\r":
                    cursor += 1
                if cursor < len(text) and text[cursor] == "\n":
                    cursor += 1
                end = cursor
                break
    if end is None:
        raise ValueError("ProviderBase provider model DATA declaration is unterminated")
    cleaned = text[:start] + text[end:]
    return cleaned, True


def _strip_leaked_provider_identity_data(text: str) -> tuple[str, bool]:
    """Remove only a standalone generated NIAKVIO_PROVIDER_ID comment."""
    pattern = re.compile(r"(?m)^\s*/\*\s*NIAKVIO_PROVIDER_ID:[^*]+\*/\s*\r?\n?")
    cleaned, count = pattern.subn("", text)
    if count > 1:
        raise ValueError("ProviderBase contains multiple provider identity DATA comments")
    return cleaned, bool(count)


def clean_derived_provider_base(provider_id: str, data: bytes) -> tuple[bytes, bool]:
    """Strip only generated/composed layers from an existing ProviderBase.

    This is the manual reconstruction cleanup path. It never consults published
    Provider JS, upstream JS, snapshots or Git history.
    """
    text = data.decode("utf-8", errors="strict")
    if PROVIDER_BEGIN_MARKER in text or PROVIDER_END_MARKER in text:
        raise ValueError(f"{provider_id}: ProviderBase envelope contamination requires Learning review")
    text, model_stripped = _strip_leaked_provider_model_data(text)
    text, identity_stripped = _strip_leaked_provider_identity_data(text)
    text, managed_fixes = strip_all_managed_fixes(
        text,
        restore_replaced_source=True,
        require_provider_base_restore=True,
    )
    text, stripped_core = _strip_generated_core_tail(text)
    text, stripped_adaptive = strip_adaptive_runtime_wrappers(text)
    data_out = text.encode("utf-8")
    prefix, body = split_owned_prefix_bootstraps(data_out)
    if prefix:
        data_out = body
    assert_base_layering(data_out, provider_id)
    return data_out, bool(
        model_stripped or identity_stripped or managed_fixes
        or stripped_core or stripped_adaptive or prefix
    )


def assert_base_layering(data: bytes, provider_id: str) -> None:
    """ProviderBase is common code only: no envelope, DATA, Provider/Core Lego or derived tail."""
    markers = forbidden_base_markers(data)
    if markers:
        raise ValueError(
            f"{provider_id}: ProviderBase contains derived/composed layer(s): "
            + ",".join(markers)
        )
    text = data.decode("utf-8", errors="strict")
    if PROVIDER_BEGIN_MARKER in text or PROVIDER_END_MARKER in text:
        raise ValueError(f"{provider_id}: ProviderBase must not contain the Provider envelope")
    fix_ids = validate_managed_fixes(text)
    if fix_ids:
        raise ValueError(
            f"{provider_id}: ProviderBase must not contain managed Lego: "
            + ",".join(fix_ids)
        )
    if "NIAKVIO_PROVIDER_ID:" in text:
        raise ValueError(f"{provider_id}: ProviderBase must not contain provider identity DATA")
    if "NIAKVIO_PROVIDER_MODEL = Object.freeze(" in text:
        raise ValueError(f"{provider_id}: ProviderBase must not contain provider model DATA")


def assert_clean_provider_base(
    data: bytes,
    provider_id: str,
    *,
    require_current_authoring: bool = True,
) -> None:
    """Fail closed unless bytes are the common, owned, non-derived ProviderBase."""
    assert_base_layering(data, provider_id)
    text = data.decode("utf-8", errors="strict")
    if PROVIDER_BASE_OWNED_MARKER not in text:
        raise ValueError(
            f"{provider_id}: clean ProviderBase missing owned marker {PROVIDER_BASE_OWNED_MARKER}"
        )
    if require_current_authoring and PROVIDER_BASE_AUTHORING_MARKER not in text:
        raise ValueError(
            f"{provider_id}: clean ProviderBase authoring drift "
            f"expected={CURRENT_PROVIDER_MODEL_AUTHORING}"
        )


def strip_adaptive_runtime_wrappers(text: str) -> tuple[str, int]:
    """Remove only owned adaptive runtime wrappers from legacy provider bytes."""
    markers = (
        "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
        "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5:",
    )
    call = '})(typeof globalThis!=="undefined"?globalThis:this,'
    removed = 0
    while True:
        starts = [text.find(marker) for marker in markers]
        starts = [value for value in starts if value >= 0]
        if not starts:
            break
        start = min(starts)
        call_at = text.find(call, start)
        end = text.find(");", call_at) if call_at >= 0 else -1
        if call_at < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper in ProviderBase")
        end += 2
        if text[end:end + 2] == "\r\n":
            end += 2
        elif text[end:end + 1] in ("\r", "\n"):
            end += 1
        text = text[:start] + text[end:]
        removed += 1
    return text.rstrip(), removed


def validate_base(data: bytes, provider_id: str) -> None:
    # A ProviderBase must remain an independently valid provider implementation.
    assert_base_layering(data, provider_id)
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), "--provider-base", str(temporary)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            detail = "\n".join(v.strip() for v in (result.stdout, result.stderr) if v.strip())
            raise ValueError(f"{provider_id}: ProviderBase rejected: {detail or 'no diagnostic'}")
    finally:
        temporary.unlink(missing_ok=True)


def write_base(provider_id: str, data: bytes) -> tuple[str, str]:
    digest = sha256(data)
    relative = base_relative(provider_id, digest)
    path = safe_base_path(relative)
    if path is None:
        raise ValueError(f"{provider_id}: unsafe ProviderBase path")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return relative, digest


def resolve_base(provider_id: str, provenance_row: dict[str, Any], *, require: bool = True) -> tuple[Path | None, str | None]:
    relative = str(provenance_row.get("base_filename") or "").strip()
    digest = str(provenance_row.get("base_sha256") or "").strip().casefold()
    path = safe_base_path(relative)
    if path is None or not path.is_file():
        if require:
            raise ValueError(f"{provider_id}: missing durable ProviderBase")
        return None, None
    actual = sha256(path.read_bytes())
    if not digest or actual != digest:
        raise ValueError(f"{provider_id}: ProviderBase SHA mismatch expected={digest or 'missing'} actual={actual}")
    return path, actual


def resolve_runtime_base(
    provider_id: str,
    provenance_row: dict[str, Any],
    *,
    require: bool = True,
) -> tuple[Path | None, str | None]:
    """Resolve the production seed without letting an unverified clean candidate regress LKG behavior.

    The clean candidate remains the canonical reconstruction artifact in provenance
    and is still used by Learning/Deep proof. Runtime compilation falls back to
    the preserved pre-reconstruction ProviderBase until the clean candidate is
    explicitly verified.
    """
    row = provenance_row if isinstance(provenance_row, dict) else {}
    if is_clean_reconstruction_candidate(row):
        relative = str(row.get("legacy_base_filename_before_clean_candidate") or "").strip()
        digest = str(row.get("legacy_base_sha256_before_clean_candidate") or "").strip().casefold()
        path = safe_base_path(relative)
        if path is not None and path.is_file():
            actual = sha256(path.read_bytes())
            if digest and actual == digest:
                return path, actual
            if digest:
                raise ValueError(
                    f"{provider_id}: legacy runtime ProviderBase SHA mismatch "
                    f"expected={digest} actual={actual}"
                )
    return resolve_base(provider_id, row, require=require)


def clean_base_from_published(provider_id: str, published_data: bytes) -> tuple[bytes, bool]:
    """Legacy-only recovery path.

    ProviderBase v3 is never recovered from a published bundle. Its sole source
    is the common NiakVIO skeleton plus persisted provider DATA/fix bricks.
    """
    published_text = published_data.decode("utf-8", errors="strict")
    if "NIAKVIO_PROVIDER_BASE_OWNED_V3" in published_text or PROVIDER_BEGIN_MARKER in published_text:
        raise ValueError(
            f"{provider_id}: ProviderBase v3 reverse recovery from published JS is forbidden"
        )
    base_text, managed_fixes = strip_all_managed_fixes(
        published_text,
        restore_replaced_source=True,
        require_provider_base_restore=True,
    )
    base_text, stripped_core = _strip_generated_core_tail(base_text)
    base_text, stripped_adaptive = strip_adaptive_runtime_wrappers(base_text)
    base_data = base_text.encode("utf-8")
    prefix, body = split_owned_prefix_bootstraps(base_data)
    if prefix:
        base_data = body
    assert_base_layering(base_data, provider_id)
    return base_data, bool(managed_fixes or stripped_core or stripped_adaptive or prefix)


def persist_base_from_published(provider_id: str, published_data: bytes) -> tuple[str, str, bool]:
    """Persist provider logic only; generated Core/routing layers are always derived."""
    base_data, stripped = clean_base_from_published(provider_id, published_data)
    validate_base(base_data, provider_id)
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, stripped


def build_base_from_seed(
    provider_id: str,
    seed_data: bytes,
    *,
    overrides_path: Path | None = None,
) -> tuple[bytes, bool]:
    """Return common ProviderBase bytes without composing provider DATA or Lego."""
    if PROVIDER_BASE_OWNED_MARKER.encode("utf-8") in seed_data:
        # Clean v3 seeds are already the immutable common skeleton. Nothing may
        # patch, strip or infer provider-specific behavior from these bytes.
        assert_clean_provider_base(seed_data, provider_id)
        validate_base(seed_data, provider_id)
        return seed_data, False

    # Compatibility-only path for pre-v3 seeds. It may recover historical base
    # code, but a current clean ProviderBase is never reverse-engineered.
    rebuilt, _records = apply_overrides(
        provider_id,
        seed_data,
        phase="discovery",
        excluded_patch_scripts=CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS,
        include_global_core=False,
        config_path=overrides_path,
    )
    base_data, stripped = clean_base_from_published(provider_id, rebuilt)
    validate_base(base_data, provider_id)
    return base_data, stripped


def persist_base_from_seed(
    provider_id: str,
    seed_data: bytes,
    *,
    overrides_path: Path | None = None,
) -> tuple[str, str, bool]:
    """Rebuild durable provider logic from a clean provider seed.

    Publication-only quarantine, dynamic domain materialization and adaptive
    runtime/domain recovery are deliberately excluded. They remain derived state
    and are regenerated later by the finalizer from current policy/evidence.
    """
    base_data, stripped = build_base_from_seed(
        provider_id,
        seed_data,
        overrides_path=overrides_path,
    )
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, stripped



def _normalize_identity_input(value: Any) -> dict[str, Any]:
    """Normalize the explicit DATA execution contract; runtime never infers it."""
    raw = value if isinstance(value, dict) else {}
    mode = str(raw.get("mode") or "tmdb_direct").strip().casefold()
    if mode not in {"tmdb_direct", "catalog_search", "external_id"}:
        raise ValueError(f"invalid provider identityInput.mode: {mode}")
    required = bool(raw.get("requiresTmdbBeforeRun", mode != "tmdb_direct"))
    fields = [
        str(item).strip()
        for item in raw.get("requiredFields") or []
        if str(item).strip()
    ]
    if not fields:
        fields = (
            ["title", "year", "mediaType"]
            if required
            else ["tmdbId", "mediaType"]
        )
    return {
        "mode": mode,
        "requiresTmdbBeforeRun": required,
        "requiredFields": list(dict.fromkeys(fields)),
    }

def build_provider_data_model(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
    provider_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize all provider-specific differences into deterministic structured DATA."""
    entry = manifest_entry if isinstance(manifest_entry, dict) else {}
    semantic_values = (
        entry.get("canonicalSupportedTypes")
        if isinstance(entry.get("canonicalSupportedTypes"), list) and entry.get("canonicalSupportedTypes")
        else entry.get("supportedTypes")
    )
    supported = [
        str(value).strip().casefold()
        for value in semantic_values or []
        if str(value).strip().casefold() in {"movie", "tv", "anime"}
    ]
    supported = list(dict.fromkeys(supported))
    display_name = str(entry.get("name") or provider_id).strip() or provider_id
    incoming_model = provider_model if isinstance(provider_model, dict) else {}
    return {
        "providerId": canonical_id(provider_id),
        "displayName": display_name,
        "knownSite": str(known_site or incoming_model.get("knownSite") or "").strip() or None,
        "supportedTypes": supported,
        "strategy": str(incoming_model.get("strategy") or "unknown").strip().casefold(),
        "officialSite": str(incoming_model.get("officialSite") or "").strip() or None,
        "officialHub": str(incoming_model.get("officialHub") or "").strip() or None,
        "officialApi": str(incoming_model.get("officialApi") or "").strip() or None,
        "fixedApi": str(incoming_model.get("fixedApi") or "").strip() or None,
        "origins": [
            str(value).strip()
            for value in incoming_model.get("origins") or []
            if _provider_data_url_is_executable(value)
        ][:24],
        "observedUrls": [
            str(value).strip()
            for value in incoming_model.get("observedUrls") or []
            if _provider_data_url_is_executable(value)
        ][:32],
        "routes": [
            str(value).strip()
            for value in incoming_model.get("routes") or []
            if _provider_data_route_is_executable(value)
        ][:64],
        "apiRecipe": (
            incoming_model.get("apiRecipe")
            if isinstance(incoming_model.get("apiRecipe"), dict)
            else None
        ),
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),
        "identityInput": _normalize_identity_input(incoming_model.get("identityInput")),
        "strictIdentity": bool(incoming_model.get("strictIdentity", False)),
        "strictHtmlIdentity": bool(incoming_model.get("strictHtmlIdentity", False)),
        "outputUrlHostRewrites": [
            {
                "fromHost": str(row.get("fromHost") or "").strip().casefold(),
                "toHost": str(row.get("toHost") or "").strip().casefold(),
            }
            for row in incoming_model.get("outputUrlHostRewrites") or []
            if isinstance(row, dict)
            and str(row.get("fromHost") or "").strip()
            and str(row.get("toHost") or "").strip()
        ][:16],
        "outputLanguageRules": [
            {
                "language": str(row.get("language") or "").strip().casefold(),
                "hostPrefix": str(row.get("hostPrefix") or "").strip().casefold(),
            }
            for row in incoming_model.get("outputLanguageRules") or []
            if isinstance(row, dict)
            and str(row.get("language") or "").strip()
            and str(row.get("hostPrefix") or "").strip()
        ][:16],
        "domainSubstitutions": {
            str(old).strip().casefold(): str(new).strip().casefold()
            for old, new in (
                incoming_model.get("domainSubstitutions")
                if isinstance(incoming_model.get("domainSubstitutions"), dict)
                else {}
            ).items()
            if str(old).strip() and str(new).strip()
        },
        "reconstructionState": "learning-clean-seed",
        "runtimeRole": "reader",
        "runtimeDiscovery": False,
        "routePlanVersion": 3,
        "modelSchemaVersion": 4,
        "authoring": CURRENT_PROVIDER_MODEL_AUTHORING,
        "upstreamCodeEmbedded": False,
        "upstreamCodeExecuted": False,
    }


def provider_data_sha256(model: dict[str, Any]) -> str:
    payload = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
    provider_model: dict[str, Any] | None = None,
) -> bytes:
    """Build the immutable common ProviderBase skeleton.

    Arguments are retained for call-site compatibility, but they MUST NOT affect
    ProviderBase bytes. Provider identity/routes/types/endpoints are materialized
    later as structured DATA by compose_provider_bundle().
    """
    del provider_id, manifest_entry, known_site, provider_model
    template = r'''/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
/* NIAKVIO_PROVIDER_BASE_AUTHORING:niakvio-owned-v3 */
"use strict";

function _uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}
function _origin(value) {
  try { return new URL(value).origin; } catch (_) { return ""; }
}
function _substituteDomain(raw) {
  const value = _text(raw).trim();
  if (!value) return value;
  try {
    const parsed = new URL(value);
    const mapping = NIAKVIO_PROVIDER_MODEL.domainSubstitutions &&
      typeof NIAKVIO_PROVIDER_MODEL.domainSubstitutions === "object"
      ? NIAKVIO_PROVIDER_MODEL.domainSubstitutions
      : {};
    const host = _text(parsed.hostname).toLowerCase();
    const target = _text(mapping[host]).toLowerCase();
    if (target) parsed.hostname = target;
    return parsed.toString();
  } catch (_) {
    return value;
  }
}
function _absolute(value, base) {
  try { return _substituteDomain(new URL(value, base).toString()); } catch (_) { return ""; }
}
function _text(value) {
  return String(value == null ? "" : value);
}
function _embeddedText(value) {
  return _text(value).split("\\/").join("/").replace(
    /\\u002[fF]|\\u003[aA]|\\u0026|\\u003[dD]|\\"|&quot;|&#34;|&amp;/gi,
    token => {
      const normalized = token.toLowerCase();
      if (normalized === "\\u002f") return "/";
      if (normalized === "\\u003a") return ":";
      if (normalized === "\\u0026" || normalized === "&amp;") return "&";
      if (normalized === "\\u003d") return "=";
      if (normalized === '\\"' || normalized === "&quot;" || normalized === "&#34;") return '"';
      return token;
    }
  );
}
function _slug(value) {
  return _text(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
function _directMedia(url) {
  return /\.(?:m3u8|mpd|mp4|mkv|webm)(?:[?#]|$)|\/(?:hls|dash|stream)(?:\/|[?#]|$)/i.test(_text(url));
}
function _extractUrls(text, base) {
  const out = [];
  const normalized = _embeddedText(text);
  const patterns = [
    /(?:src|href|file|url|pathname|permalink|embedUrl|embed_url|contentUrl)\s*["']?\s*[:=]\s*["']([^"'<>\s]+)["']/gi,
    /["'](\/(?:api|watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|manifest|action)(?:[^"'<>\\\s]{0,500}))["']/gi,
    /https?:\/\/[^"'<>\s]+/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(normalized))) {
      const raw = match[1] || match[0] || "";
      const absolute = _absolute(raw, base);
      if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
      if (out.length >= 240) break;
    }
  }
  return _uniq(out);
}
function _mediaNamespace(mediaType) {
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    if (ctx && (ctx.tmdbNamespace === "movie" || ctx.tmdbNamespace === "tv")) return ctx.tmdbNamespace;
  } catch (_) {}
  return mediaType === "movie" ? "movie" : "tv";
}
function _playerLike(url) {
  try {
    const parsed = new URL(url);
    const host = _text(parsed.hostname).toLowerCase();
    // Shared download/intermediate hosts used by multiple catalogue providers.
    // They are resolver pages, not playable output, so the bounded crawler may
    // traverse them but _directMedia() must still prove the final stream.
    if (/(?:^|\.)(?:abhilinks\.(?:site|life)|vcloud\.zip|hubcloud\.[a-z0-9.-]+|driveseed\.[a-z0-9.-]+|hubdrive\.[a-z0-9.-]+|gdflix\.[a-z0-9.-]+)$/i.test(host)) {
      return true;
    }
    return /\/(?:watch|embed|player|play|video|videos|stream|streams|source|sources|server|servers|resolve|proxy|drive|download)(?:[/?#.-]|$)/i.test(parsed.pathname + parsed.search);
  } catch (_) {
    return false;
  }
}
function _crawlUrlScore(url) {
  try {
    if (_directMedia(url)) return 5000;
    const parsed = new URL(url);
    const host = _text(parsed.hostname).toLowerCase();
    const path = (parsed.pathname + parsed.search).toLowerCase();
    let score = 0;
    if (/(?:^|\.)(?:vcloud|hubcloud|driveseed|hubdrive|gdflix|gofile|pixeldrain|streamtape|vidmoly|filelions|filemoon|streamwish|wishfast|dood|doodstream|mixdrop|voe|lulustream|savefiles)\./i.test(host)) score += 900;
    if (/(?:^|\.)(?:abhilinks\.(?:site|life))$/i.test(host)) score += 500;
    if (/\/(?:watch|embed|player|play|video|stream|source|server|resolve|proxy|drive|download|dl|links?|redirect)(?:[/?#.-]|$)/i.test(path)) score += 420;
    if (/\/archives?\/\d+/i.test(path)) score += 180;
    if (/(?:^|\.)(?:t\.me|telegram\.me|facebook\.com|instagram\.com|twitter\.com|x\.com|youtube\.com|youtu\.be)$/i.test(host)) score -= 1600;
    if (/\/(?:feed|comments?\/feed|wp-json\/oembed|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) score -= 1200;
    if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) score -= 1600;
    return score;
  } catch (_) { return -5000; }
}
function _crawlCanonical(url) {
try {
const parsed = new URL(url);
if (!/^https?:$/i.test(parsed.protocol)) return "";
parsed.hash = "";
return parsed.toString();
} catch (_) { return ""; }
}
function _crawlEligible(url) {
  try {
    if (_directMedia(url)) return true;
    const parsed = new URL(url);
    if (!/^https?:$/i.test(parsed.protocol)) return false;
    const host = _text(parsed.hostname).toLowerCase();
    const path = (parsed.pathname + parsed.search).toLowerCase();
    const hash = _text(parsed.hash).toLowerCase();
    if (/^#(?:comments?|respond|reply|share)/i.test(hash)) return false;
    if (/(?:^|\.)(?:t\.me|telegram\.me|facebook\.com|instagram\.com|twitter\.com|x\.com|youtube\.com|youtu\.be)$/i.test(host)) return false;
    if (/\/(?:feed|comments?\/feed|wp-json(?:\/|$)|wp-admin|admin|login|register|assets?|static|images?|icons?|fonts?)(?:[/?#.-]|$)/i.test(path)) return false;
    if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;
    if (/(?:\+t\.uri|code%3a|message%3a|xhr%3a|\{status:)/i.test(path)) return false;
    return _playerLike(url) || _crawlUrlScore(url) > 0;
  } catch (_) { return false; }
}
async function _crawlDirectMedia(seedUrls, referer, maxDepth) {
  const queue = _uniq(seedUrls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8).map(url => ({ url, depth: 0, referer }));
  const seen = new Set();
  const streams = [];
  let requests = 0;
  while (queue.length && requests < 10 && streams.length < 12) {
    queue.sort((a,b)=>_crawlUrlScore(b.url)-_crawlUrlScore(a.url));
    const row = queue.shift();
    if (!row || seen.has(row.url)) continue;
    seen.add(row.url);
    requests += 1;
    try {
      const response = await _fetch(row.url, {
        headers: row.referer ? { Referer: row.referer } : {}
      });
      const responseUrl = response.url || row.url;
      const contentType = _text(response.headers.get("content-type")).toLowerCase();
      if (_directMedia(responseUrl) || /(?:mpegurl|dash\+xml|video\/)/i.test(contentType)) {
        streams.push(..._streams([responseUrl], row.referer || referer || ""));
        continue;
      }
      let urls = [];
      if (contentType.includes("json")) {
        urls = _jsonUrls(await response.json());
      } else {
        urls = _extractUrls(await response.text(), responseUrl);
      }
      const direct = urls.filter(_directMedia);
      if (direct.length) {
        streams.push(..._streams(direct, responseUrl));
        continue;
      }
      if (row.depth < Math.max(0, Number(maxDepth) || 0)) {
        for (const next of _uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 4)) {
          if (!seen.has(next)) queue.push({ url: next, depth: row.depth + 1, referer: responseUrl });
        }
      }
    } catch (_) {}
  }
  return streams.slice(0, 40);
}
function _candidateScore(url, meta) {
  let parsed;
  try { parsed = new URL(url); } catch (_) { return -1; }
  const path = decodeURIComponent(parsed.pathname || "").toLowerCase();
  if (!path || path === "/" || /\/(?:_next|static|assets?|images?|icons?|fonts?)(?:\/|$)/i.test(path)) return -1;
  const slug = _slug(meta && meta.title);
  const tokens = slug.split("-").filter(token => token.length >= 3);
  let score = 0;
  if (slug && path.includes(slug)) score += 120;
  for (const token of tokens) if (path.includes(token)) score += 18;
  if (meta && meta.year && path.includes(String(meta.year))) score += 20;
  if (meta && meta.tmdbId && path.includes(String(meta.tmdbId))) score += 45;
  if (/\/(?:movie|movies|film|films|series|tv|show|watch|title|media)\//i.test(path)) score += 12;
  return score;
}
function _identityMode() {
  const raw = NIAKVIO_PROVIDER_MODEL && NIAKVIO_PROVIDER_MODEL.identityInput;
  return _text(raw && raw.mode || "tmdb_direct").toLowerCase();
}
function _identityUsesTmdbId() {
  return _identityMode() === "tmdb_direct";
}
function _expandLearnedRoute(pattern, meta, mediaType, season, episode, bases) {
  let route = _text(pattern);
  if (/\$\{|encodeURIComponent\s*\(/i.test(route)) return [];
  if (!route || /^https?:\/\//i.test(route) && !/\{[^}]+\}/.test(route)) {
    return /^https?:\/\//i.test(route) ? [route] : [];
  }
  const id = _text(meta && meta.tmdbId);
  const title = _text(meta && meta.title);
  const slug = _slug(title);
  const transport = mediaType === "movie" ? "movie" : "tv";
  route = route.replace(/\{tmdb_?id\}/gi, encodeURIComponent(id));
  // {id} has no universal meaning across providers. It can be a provider
  // catalogue/session/file/MAL id. Only the explicit tmdb_direct identity
  // contract permits using the incoming TMDB id as its implicit value.
  if (/\{id\}/i.test(route)) {
    if (!_identityUsesTmdbId()) return [];
    route = route.replace(/\{id\}/gi, encodeURIComponent(id));
  }
  route = route
    .replace(/\{slug\}/gi, encodeURIComponent(slug))
    .replace(/\{(?:title|query|q)\}/gi, encodeURIComponent(title))
    .replace(/\{(?:media|media_?type|type)\}/gi, encodeURIComponent(transport))
    .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
    .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
  if (/\{[^}]+\}/.test(route)) return [];
  const out = [];
  for (const base of (bases || _runtimeBases())) {
    const absolute = _absolute(route, base);
    if (absolute) out.push(absolute);
  }
  return _uniq(out);
}
function _routeKind(route) {
  const value = _text(route).toLowerCase();
  if (!value || /\/(?:track|report|warm|dead|working|ad-link|fp)(?:[/?#]|$)/i.test(value)) return "ignore";
  // Search semantics are more specific than a generic /api prefix. A route
  // such as /api?m=search&q={query} must carry Core title metadata instead of
  // falling into _apiUrls(), where title is intentionally empty for ID routes.
  if (/\/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword)=/i.test(value)) return "search";
  if (/\/(?:api)(?:[./?#]|$)/i.test(value)) return "api";
  if (/\/(?:player|embed|play)(?:[/?#]|$)/i.test(value)) return "player";
  if (/\{(?:tmdb_?id|id|slug|title)\}/i.test(value) || /\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
  return "ignore";
}
function _learnedUrls(kind, meta, mediaType, season, episode) {
  const out = [];
  const bases = kind === "api" ? _apiBases() : _searchBases();
  for (const route of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (_routeKind(route) !== kind) continue;
    out.push(..._expandLearnedRoute(route, meta, mediaType, season, episode, bases));
  }
  return _uniq(out);
}
function _providerDeadlineExceeded() {
  try {
    const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
    return Number.isFinite(deadline) && deadline > 0 && Date.now() >= deadline;
  } catch (_) {
    return false;
  }
}
function _providerTimeoutError() {
  const error = new Error("nuvio_provider_timeout");
  error.name = "TimeoutError";
  error.code = "NUVIO_PROVIDER_TIMEOUT";
  error.__nuvioProviderTimeout = true;
  return error;
}
async function _fetch(url, options) {
  if (_providerDeadlineExceeded()) throw _providerTimeoutError();
  const requestOptions = options && typeof options === "object" ? Object.assign({}, options) : {};
  requestOptions.redirect = requestOptions.redirect || "follow";
  requestOptions.headers = Object.assign({
    "Accept": "application/json,text/html,application/xhtml+xml,text/plain,*/*",
    "User-Agent": "Mozilla/5.0 NiakVIO/3"
  }, requestOptions.headers || {});
  const response = await fetch(url, requestOptions);
  if (_providerDeadlineExceeded()) throw _providerTimeoutError();
  if (!response.ok) throw new Error("provider_http_" + response.status);
  return response;
}
async function _tmdb(tmdbId, mediaType) {
  if (!tmdbId) return null;
  const type = _mediaNamespace(mediaType);
  const identity = type + ":" + String(tmdbId || "");
  function project(row) {
    if (!row || typeof row !== "object") return null;
    const alternativeRows = row.alternative_titles && (
      row.alternative_titles.titles || row.alternative_titles.results || row.alternative_titles
    );
    const aliases = _uniq([
      row.title,
      row.name,
      row.original_title,
      row.original_name,
      ...(Array.isArray(alternativeRows) ? alternativeRows.map(item => item && (item.title || item.name)) : [])
    ].map(_text).filter(Boolean));
    const externalIds = row.external_ids && typeof row.external_ids === "object"
      ? row.external_ids
      : {};
    const imdbId = _text(
      row.imdb_id || row.imdbId || externalIds.imdb_id || ""
    ).trim();
    return {
      title: aliases[0] || "",
      aliases,
      year: String(row.release_date || row.first_air_date || row.year || "").slice(0, 4),
      tmdbId: String(tmdbId || ""),
      imdbId,
      externalIds
    };
  }
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    const ctxId = String(ctx && ctx.tmdbId || "");
    const ctxNamespace = String(ctx && ctx.tmdbNamespace || "");
    if (ctx && (!ctxId || ctxId === String(tmdbId)) && (!ctxNamespace || ctxNamespace === type)) {
      const projected = project(ctx.tmdbMetadata);
      if (projected) return projected;
    }
  } catch (_) {}
  try {
    const cache = typeof globalThis !== "undefined" ? globalThis.__nuvioTmdbMetadataCacheV1 : null;
    const cached = cache && cache[identity];
    if (cached) {
      const settled = typeof cached.then === "function" ? await cached : cached;
      const row = settled && settled.metadata && typeof settled.metadata === "object" ? settled.metadata : settled;
      const projected = project(row);
      if (projected) return projected;
    }
  } catch (_) {}
  try {
    const getTmdbData = typeof globalThis !== "undefined" ? globalThis.__nuvioCoreGetTmdbDataV1 : null;
    if (typeof getTmdbData === "function") {
      const result = await getTmdbData({ tmdbId: String(tmdbId), mediaType: type, tmdbNamespace: type });
      const row = result && result.metadata && typeof result.metadata === "object" ? result.metadata : null;
      const projected = project(row);
      if (projected) return projected;
    }
  } catch (_) {}
  return null;
}
function _searchBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite,
    NIAKVIO_PROVIDER_MODEL.officialHub
  ].map(_substituteDomain)).filter(value => /^https?:/i.test(value));
}
function _apiBases() {
  return _uniq([
    NIAKVIO_PROVIDER_MODEL.fixedApi,
    NIAKVIO_PROVIDER_MODEL.officialApi,
    NIAKVIO_PROVIDER_MODEL.officialSite,
    NIAKVIO_PROVIDER_MODEL.knownSite
  ].map(_substituteDomain)).filter(value => /^https?:/i.test(value));
}
function _runtimeBases() {
  return _uniq([..._searchBases(), ..._apiBases()]);
}
function _searchUrls(meta, mediaType, season, episode) {
  return _learnedUrls("search", meta, mediaType, season, episode);
}
function _runtimePlanAvailable() {
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) return true;
  return (NIAKVIO_PROVIDER_MODEL.routes || []).some(route => ["search","detail","player","api"].includes(_routeKind(route)));
}
function _apiUrls(tmdbId, mediaType, season, episode) {
  const bases = _apiBases();
  const out = [];
  // Route DATA is executable knowledge. API-family providers commonly persist
  // only a relative route plus one trusted origin; consume that plan directly
  // instead of requiring an observed full endpoint URL.
  out.push(..._learnedUrls(
    "api",
    { tmdbId: _text(tmdbId), title: "" },
    mediaType,
    season,
    episode
  ));
  // A bare API origin is not an executable request plan. The legacy fallback
  // that appended ?tmdbId=... is valid only for providers explicitly classified
  // tmdb_direct; catalogue providers must execute an observed route/search chain.
  if (!_identityUsesTmdbId()) return _uniq(out);
  for (const base of bases) {
    if (!/^https?:/i.test(base)) continue;
    let url = base
      .replace(/\{tmdb_?id\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{id\}/gi, encodeURIComponent(tmdbId || ""))
      .replace(/\{(?:media_?type|type)\}/gi, encodeURIComponent(mediaType || "movie"))
      .replace(/\{season\}/gi, encodeURIComponent(season == null ? "" : season))
      .replace(/\{episode\}/gi, encodeURIComponent(episode == null ? "" : episode));
    out.push(url);
    try {
      const parsed = new URL(url);
      if (!parsed.search) {
        const params = [
          ["tmdbId", tmdbId || ""],
          ["type", mediaType || "movie"]
        ];
        if (season != null) params.push(["season", String(season)]);
        if (episode != null) params.push(["episode", String(episode)]);
        out.push(parsed.origin + parsed.pathname + "?" + params
          .map(pair => encodeURIComponent(pair[0]) + "=" + encodeURIComponent(pair[1]))
          .join("&") + (parsed.hash || ""));
      }
    } catch (_) {}
  }
  return _uniq(out);
}
function _directPlayerUrls(tmdbId, mediaType) {
  if (!tmdbId || !_identityUsesTmdbId()) return [];
  const hasPlayerRoute = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    /^\/player(?:[?#]|$)/i.test(_text(route))
  );
  if (!hasPlayerRoute) return [];
  const transportType = _mediaNamespace(mediaType);
  const out = [];
  for (const base of _searchBases()) {
    try {
      const parsed = new URL("/player", base);
      out.push(
        parsed.origin + parsed.pathname
        + "?m=" + encodeURIComponent(transportType)
        + "&id=" + encodeURIComponent(_text(tmdbId))
      );
    } catch (_) {}
  }
  return _uniq(out);
}
function _runtimeApiUrls(playerUrl, mediaType, tmdbId, season, episode) {
  let player;
  try { player = new URL(playerUrl); } catch (_) { return []; }
  const out = [];
  // Transport-level player media values are commonly movie/tv even when
  // Nuvio's semantic type is anime. Preserve anime as a Nuvio type, but route
  // episodic/anime players through the site's TV transport convention.
  const desiredMedia = _mediaNamespace(mediaType);
  const observedMedia = _text(player.searchParams.get("m") || player.searchParams.get("media") || player.searchParams.get("type")).toLowerCase();
  for (const pattern of NIAKVIO_PROVIDER_MODEL.routes || []) {
    if (!/^\/api\/(?:streams?(?:\/|$)|source|sources|resolve|proxy)/i.test(_text(pattern))) continue;
    if (/\/(?:working|dead|warm)(?:[?#]|$)/i.test(_text(pattern))) continue;
    const parts = _text(pattern).split("?", 2);
    let path = parts[0].replace(/\{media\}/gi, encodeURIComponent(desiredMedia));
    if (observedMedia && /\/(?:movie|tv|anime)$/i.test(path)) {
      path = path.replace(/\/(?:movie|tv|anime)$/i, "/" + encodeURIComponent(desiredMedia));
    }
    const keys = (parts[1] || "").split("&").map(part => part.split("=", 1)[0]).filter(Boolean);
    if (!keys.length) continue;
    let target;
    try { target = new URL(path, player.origin); } catch (_) { continue; }
    let missing = false;
    const query = [];
    for (const key of keys) {
      const lower = key.toLowerCase();
      let value = player.searchParams.get(key);
      if (value == null && lower === "id" && _identityUsesTmdbId()) value = _text(tmdbId);
      if (value == null && /^(?:m|media|type)$/.test(lower)) value = desiredMedia;
      if (value == null && /^(?:season|s)$/.test(lower) && season != null) value = _text(season);
      if (value == null && /^(?:episode|e)$/.test(lower) && episode != null) value = _text(episode);
      if (value == null || value === "") { missing = true; break; }
      query.push(encodeURIComponent(key) + "=" + encodeURIComponent(_text(value)));
    }
    if (!missing) {
      const targetUrl = target.origin + target.pathname + (query.length ? "?" + query.join("&") : "");
      out.push({ url: targetUrl, referer: player.toString() });
    }
  }
  const seen = new Set();
  return out.filter(row => row.url && !seen.has(row.url) && seen.add(row.url));
}
function _jsonUrls(value, out) {
  out = out || [];
  if (typeof value === "string") {
    if (/^https?:/i.test(value)) out.push(value);
    return out;
  }
  if (Array.isArray(value)) {
    for (const child of value) _jsonUrls(child, out);
    return out;
  }
  if (value && typeof value === "object") {
    for (const child of Object.values(value)) _jsonUrls(child, out);
  }
  return out;
}
function _sourceUrls(value, base, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _sourceUrls(child, base, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  for (const [key, child] of Object.entries(value)) {
    if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
      const absolute = _absolute(child, base);
      if (absolute && /^https?:/i.test(absolute) &&
          !/\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
        out.push(absolute);
      }
    }
    if (child && typeof child === "object") _sourceUrls(child, base, out);
  }
  return out;
}
function _rewriteOutputUrl(raw) {
  const value = _substituteDomain(_text(raw).trim());
  if (!/^https?:\/\//i.test(value)) return value;
  try {
    const parsed = new URL(value);
    const host = _text(parsed.hostname).toLowerCase();
    for (const rule of NIAKVIO_PROVIDER_MODEL.outputUrlHostRewrites || []) {
      const fromHost = _text(rule && rule.fromHost).toLowerCase();
      const toHost = _text(rule && rule.toHost).toLowerCase();
      if (!fromHost || !toHost || host !== fromHost) continue;
      parsed.hostname = toHost;
      return parsed.toString();
    }
  } catch (_) {}
  return value;
}
function _outputLanguage(url) {
  try {
    const host = new URL(_text(url)).hostname.toLowerCase();
    for (const rule of NIAKVIO_PROVIDER_MODEL.outputLanguageRules || []) {
      const prefix = _text(rule && rule.hostPrefix).toLowerCase();
      const language = _text(rule && rule.language).toLowerCase();
      if (prefix && language && host.startsWith(prefix)) return language;
    }
  } catch (_) {}
  return "";
}
function _streams(urls, referer, extraHeaders) {
  const headers = Object.assign({}, extraHeaders || {});
  if (referer) headers.Referer = referer;
  const hasHeaders = Object.keys(headers).length > 0;
  return _uniq(urls)
    .map(_rewriteOutputUrl)
    .filter(Boolean)
    .filter((url, index, list) => list.indexOf(url) === index)
    .slice(0, 40)
    .map((url, index) => {
      const language = _outputLanguage(url);
      return {
        name: NIAKVIO_PROVIDER_MODEL.displayName,
        title: NIAKVIO_PROVIDER_MODEL.displayName + (index ? " #" + (index + 1) : ""),
        url,
        language: language || undefined,
        headers: hasHeaders ? Object.assign({}, headers) : undefined
      };
    });
}
function _recipeValue(row, fields) {
  if (!row || typeof row !== "object") return "";
  for (const field of fields || []) {
    const value = row[field];
    if (value != null && value !== "") return _text(value);
  }
  return "";
}
function _collectionMediaType(key) {
  const value = _text(key).toLowerCase().replace(/[^a-z0-9]+/g, "");
  if (["movie","movies","film","films"].includes(value)) return "movie";
  if (["tv","tvs","series","show","shows","anime","animes","episode","episodes"].includes(value)) return "tv";
  return "";
}
function _recipeObjects(value, out, inheritedMedia) {
  out = out || [];
  inheritedMedia = inheritedMedia || "";
  if (Array.isArray(value)) {
    for (const child of value) _recipeObjects(child, out, inheritedMedia);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  if (inheritedMedia && !value.__nuvioCollectionMediaType) {
    out.push(Object.assign({ __nuvioCollectionMediaType: inheritedMedia }, value));
  } else {
    out.push(value);
  }
  for (const [key, child] of Object.entries(value)) {
    if (child && typeof child === "object") {
      _recipeObjects(child, out, _collectionMediaType(key) || inheritedMedia);
    }
    if (out.length >= 400) break;
  }
  return out;
}
function _recipeMediaType(row, recipe) {
  const raw = _recipeValue(row, recipe.typeFields || ["type","media_type","mediaType","kind","category"]).toLowerCase();
  if (raw) {
    if (["tv","series","show","anime","episode"].includes(raw)) return "tv";
    if (["movie","film"].includes(raw)) return "movie";
  }
  const inherited = _text(row && row.__nuvioCollectionMediaType).toLowerCase();
  return inherited === "movie" || inherited === "tv" ? inherited : "";
}
function _recipeScore(row, meta, recipe, expectedMedia) {
  const title = _slug(_recipeValue(row, recipe.titleFields || ["title","name","post_title","original_title"]));
  const expectedTitles = _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_slug).filter(Boolean);
  const expected = expectedTitles[0] || "";
  const actualMedia = _recipeMediaType(row, recipe);
  const year = _recipeValue(row, recipe.yearFields || ["year","release_date","first_air_date"]).slice(0, 4);
  const expectedYear = _text(meta && meta.year).slice(0, 4);
  const providerId = _recipeValue(row, recipe.idFields || ["id","_id","media_id","post_id"]);

  if (recipe.strictIdentity) {
    if (!providerId || !title || !expectedTitles.length || !expectedTitles.includes(title)) return -1;
    if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
    if (recipe.requireProviderTypeEvidence === true && (!actualMedia || !expectedMedia)) return -1;
    if (expectedYear) {
      if (!year || !/^\d{4}$/.test(year)) return -1;
      if (Math.abs(Number(year) - Number(expectedYear)) > 1) return -1;
    }
    return 100 + (year === expectedYear ? 20 : 10) + 20;
  }

  if (actualMedia && expectedMedia && actualMedia !== expectedMedia) return -1;
  if (year && expectedYear && year !== expectedYear) return -1;
  let score = 0;
  if (title && expected && title === expected) score += 200;
  else if (title && expected && (title.includes(expected) || expected.includes(title))) score += 90;
  if (title && expected) {
    for (const token of expected.split("-").filter(value => value.length >= 3)) {
      if (title.includes(token)) score += 10;
    }
  }
  if (year && expectedYear && year === expectedYear) score += 40;
  if (actualMedia && expectedMedia && actualMedia === expectedMedia) score += 60;
  if (providerId) score += 15;
  return score;
}
function _recipeSourceUrls(value, base, recipe) {
  const urls = _sourceUrls(value, base);
  if (!recipe || !recipe.directSourcesOnly) return urls;
  return urls.filter(_directMedia);
}
function _recipeUrl(pattern, values, base) {
  let route = _text(pattern);
  if (!route) return "";
  const replacements = {
    query: values.query,
    title: values.query,
    id: values.providerId,
    providerId: values.providerId,
    tmdbId: values.tmdbId,
    tmdb_id: values.tmdbId,
    media: values.media,
    type: values.media,
    season: values.season,
    episode: values.episode,
    source: values.source
  };
  route = route.replace(/\{([^}]+)\}/g, (match, key) => {
    const value = replacements[key];
    return value == null ? "" : encodeURIComponent(_text(value));
  });
  let url;
  try {
    if (/^https?:\/\//i.test(route)) {
      url = new URL(route).toString();
    } else {
      const parsedBase = new URL(_text(base).trim());
      const basePath = _text(parsedBase.pathname || "").replace(/\/+$/, "");
      const prefix = parsedBase.origin + (basePath && basePath !== "/" ? basePath : "");
      url = prefix + "/" + route.replace(/^\/+/, "");
    }
  } catch (_) { return ""; }
  // NuvioTV's QuickJS URL polyfill does not synchronize URL.href after
  // searchParams mutations. Rebuild the query explicitly instead of relying
  // on mutating searchParams before toString().
  try {
    const parsed = new URL(url);
    const remove = new Set(
      ["season","episode","source"].filter(key => values[key] == null || values[key] === "")
    );
    if (!remove.size) return parsed.toString();
    const query = _text(parsed.search || "").replace(/^\?/, "");
    const kept = query ? query.split("&").filter(part => {
      const rawKey = part.split("=", 1)[0] || "";
      let key = rawKey;
      try { key = decodeURIComponent(rawKey); } catch (_) {}
      return !remove.has(_text(key).toLowerCase());
    }) : [];
    return parsed.origin + parsed.pathname + (kept.length ? "?" + kept.join("&") : "") + _text(parsed.hash || "");
  } catch (_) {
    return url;
  }
}
async function _recipePayload(url, recipe, body) {
  const headers = Object.assign({}, recipe.requestHeaders || {});
  if (recipe.referer) headers.Referer = recipe.referer;
  if (recipe.origin) headers.Origin = recipe.origin;
  const options = { headers };
  const requestTimeoutMs = Math.max(0, Number(recipe.requestTimeoutMs || 0) || 0);
  if (requestTimeoutMs > 0) {
    try {
      let timeoutMs = requestTimeoutMs;
      const deadline = Number(globalThis && globalThis.__nuvioProviderDeadlineMs);
      if (Number.isFinite(deadline) && deadline > 0) timeoutMs = Math.max(1, Math.min(timeoutMs, deadline - Date.now()));
      if (typeof AbortSignal !== "undefined" && AbortSignal.timeout) options.signal = AbortSignal.timeout(timeoutMs);
    } catch (_) {}
  }
  if (body != null) {
    options.method = "POST";
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await _fetch(url, options);
  const type = _text(response.headers.get("content-type")).toLowerCase();
  if (type.includes("json")) return { value: await response.json(), base: response.url || url };
  const text = await response.text();
  try { return { value: JSON.parse(text), base: response.url || url }; }
  catch (_) { return { value: text, base: response.url || url }; }
}
function _recipeField(value,path){var cur=value;for(const part of _text(path).split(".").filter(Boolean)){if(!cur||typeof cur!=="object")return"";cur=cur[part]}return _text(cur)}
function _recipeStatusBase(domain,recipe){
  let raw=_text(domain).replace(/^https?:\/\//i,"").replace(/\/+$/,"");
  if(!raw)return"";
  let host=raw.split("/")[0];
  const prefix=_text(recipe.statusApiPrefix);
  if(prefix&&host.toLowerCase().indexOf(prefix.toLowerCase())!==0)host=prefix+host;
  const suffix=_text(recipe.statusApiSuffix);
  return "https://"+host+(suffix?(suffix.charAt(0)==="/"?suffix:"/"+suffix):"");
}
function _recipeStaticBases(recipe){
  const explicitFallbackBases=Array.isArray(recipe.fallbackBases)?recipe.fallbackBases:[];
  const modelFallbackBases=recipe.allowModelBases===true
    ? [NIAKVIO_PROVIDER_MODEL.fixedApi,NIAKVIO_PROVIDER_MODEL.officialApi,..._runtimeBases()]
    : [];
  return _uniq([
    recipe.base,
    ...explicitFallbackBases,
    ...modelFallbackBases
  ]).filter(value=>/^https?:/i.test(_text(value)));
}
async function _recipeStatusDynamicBase(recipe){
  if(!/^https?:\/\//i.test(_text(recipe.statusUrl))||!recipe.statusDomainField)return"";
  try{
    const statusOptions={headers:{Accept:"application/json,text/plain,*/*"}};
    try{
      const requestTimeoutMs=Math.max(0,Number(recipe.requestTimeoutMs||0)||0);
      if(requestTimeoutMs>0&&typeof AbortSignal!=="undefined"&&AbortSignal.timeout)statusOptions.signal=AbortSignal.timeout(requestTimeoutMs);
    }catch(_){}
    const response=await _fetch(_text(recipe.statusUrl),statusOptions);
    let value=null;
    const type=_text(response.headers&&response.headers.get?response.headers.get("content-type"):"").toLowerCase();
    if(type.includes("json"))value=await response.json();
    else{
      const body=await response.text();
      try{value=JSON.parse(body)}catch(_){value=null}
    }
    return _recipeStatusBase(_recipeField(value,recipe.statusDomainField),recipe);
  }catch(_){return""}
}
async function _recipeBases(recipe){
  return _recipeStaticBases(recipe);
}
async function _resolveApiRecipe(meta, mediaType, season, episode) {
  const recipe = NIAKVIO_PROVIDER_MODEL.apiRecipe;
  if (!recipe || typeof recipe !== "object") return [];
  const media = _mediaNamespace(mediaType);
  const bases = await _recipeBases(recipe);
  if (!bases.length) return [];
  const values = {
    query: _text(meta && meta.title),
    providerId: _text(meta && meta.tmdbId),
    tmdbId: _text(meta && meta.tmdbId),
    media,
    season,
    episode,
    source: null
  };

  if (recipe.directRoute) {
    const streams = [];
    const sources = Array.isArray(recipe.sources) && recipe.sources.length ? recipe.sources.slice(0, 12) : [null];
    const batchSize = Math.max(1, Math.min(Number(recipe.sourceBatchSize || 4) || 4, 6));
    const minStreamsBeforeStop = Math.max(1, Math.min(Number(recipe.minStreamsBeforeStop || 1) || 1, 20));
    for (const base of bases.slice(0, 2)) {
      for (let offset = 0; offset < sources.length; offset += batchSize) {
        const batch = sources.slice(offset, offset + batchSize);
        const batchRows = await Promise.all(batch.map(async source => {
          const localValues = Object.assign({}, values, { source });
          const url = _recipeUrl(recipe.directRoute, localValues, base);
          if (!url) return [];
          try {
            const payload = await _recipePayload(url, recipe, null);
            if (typeof payload.value === "string") {
              return _streams(
                _extractUrls(payload.value, payload.base).filter(_directMedia),
                recipe.referer || base,
                Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
              );
            }
            return _streams(
              _recipeSourceUrls(payload.value, payload.base, recipe),
              recipe.referer || base,
              Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
            );
          } catch (_) {
            return [];
          }
        }));
        for (const rows of batchRows) streams.push(...rows);
        if (streams.length >= minStreamsBeforeStop) break;
      }
      if (streams.length) break;
    }
    return streams.slice(0, 40);
  }

  if (!recipe.searchRoute) return [];
  const searchQueries = _uniq([
    meta && meta.title,
    ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])
  ].map(_text).filter(Boolean)).slice(0, 3);

  let statusFallbackBlocked = false;
  async function findProvider(baseList) {
    const blockedBases = new Set();
    const skipStatuses = new Set(
      (Array.isArray(recipe.skipStatusOnHttpStatuses) ? recipe.skipStatusOnHttpStatuses : [])
        .map(value => Number(value))
        .filter(value => Number.isFinite(value))
    );
    const candidates = baseList.slice(0, 3);
    for (const query of searchQueries) {
      values.query = query;
      for (const base of candidates) {
        if (blockedBases.has(base)) continue;
        const url = _recipeUrl(recipe.searchRoute, values, base);
        if (!url) continue;
        try {
          const payload = await _recipePayload(url, recipe, null);
          if (!payload.value || typeof payload.value === "string") continue;
          const rows = _recipeObjects(payload.value, [])
            .map(row => ({ row, score: _recipeScore(row, meta, recipe, media) }))
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score);
          if (!rows.length) continue;
          const id = _recipeValue(rows[0].row, recipe.idFields || ["id","_id","media_id","post_id"]);
          if (id) return { id, base };
        } catch (error) {
          const match = _text(error && error.message).match(/provider_http_(\d+)/i);
          const status = match ? Number(match[1]) : 0;
          if (status && skipStatuses.has(status)) blockedBases.add(base);
        }
      }
    }
    if (candidates.length && candidates.every(base => blockedBases.has(base))) statusFallbackBlocked = true;
    return null;
  }

  let providerMatch = await findProvider(bases);
  let dynamicStatusBase = "";
  if (!providerMatch && !statusFallbackBlocked) {
    dynamicStatusBase = await _recipeStatusDynamicBase(recipe);
    if (dynamicStatusBase && !bases.includes(dynamicStatusBase)) {
      providerMatch = await findProvider([dynamicStatusBase]);
    }
  }
  if (!providerMatch) return [];

  values.providerId = providerMatch.id;
  const route = media === "movie" ? recipe.movieRoute : (recipe.episodeRoute || recipe.movieRoute);
  if (!route) return [];

  async function resolveRoute(baseList) {
    for (const base of baseList.slice(0, 3)) {
      const url = _recipeUrl(route, values, base);
      if (!url) continue;
      try {
        const payload = await _recipePayload(url, recipe, null);
        if (typeof payload.value === "string") {
          const urls = _extractUrls(payload.value, payload.base).filter(_directMedia);
          if (urls.length) return _streams(
            urls,
            recipe.referer || base,
            Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
          );
        } else {
          const urls = _recipeSourceUrls(payload.value, payload.base, recipe);
          if (urls.length) return _streams(
            urls,
            recipe.referer || base,
            Object.assign({}, recipe.playbackHeaders || {}, recipe.origin ? { Origin: recipe.origin } : {})
          );
        }
      } catch (_) {}
    }
    return [];
  }

  const routeBases = _uniq([providerMatch.base, ...bases]);
  let resolved = await resolveRoute(routeBases);
  if (resolved.length) return resolved;

  if (!dynamicStatusBase) dynamicStatusBase = await _recipeStatusDynamicBase(recipe);
  if (dynamicStatusBase && !routeBases.includes(dynamicStatusBase)) {
    resolved = await resolveRoute([dynamicStatusBase]);
    if (resolved.length) return resolved;
  }
  return [];
}
async function _resolveApi(tmdbId, mediaType, season, episode) {
  const streams = [];
  for (const url of _apiUrls(tmdbId, mediaType, season, episode).slice(0, 4)) {
    try {
      const response = await _fetch(url);
      const type = _text(response.headers.get("content-type")).toLowerCase();
      if (type.includes("json")) {
        const value = await response.json();
        streams.push(..._jsonUrls(value).filter(_directMedia));
      } else {
        const text = await response.text();
        streams.push(..._extractUrls(text, response.url || url).filter(_directMedia));
      }
    } catch (_) {}
    if (streams.length) break;
  }
  return _streams(streams, _searchBases()[0] || "");
}
async function _resolveRuntimeApi(playerUrls, mediaType, tmdbId, season, episode) {
  const streams = [];
  for (const playerUrl of _uniq(playerUrls).slice(0, 3)) {
    for (const row of _runtimeApiUrls(playerUrl, mediaType, tmdbId, season, episode).slice(0, 4)) {
      try {
        const response = await _fetch(row.url, {
          headers: row.referer ? { Referer: row.referer } : {}
        });
        const type = _text(response.headers.get("content-type")).toLowerCase();
        if (type.includes("json")) {
          const value = await response.json();
          const sources = _sourceUrls(value, response.url || row.url);
          if (sources.length) streams.push(..._streams(sources, row.referer));
        } else {
          const text = await response.text();
          const urls = _extractUrls(text, response.url || row.url);
          const direct = urls.filter(_directMedia);
          if (direct.length) streams.push(..._streams(direct, row.referer));
        }
      } catch (_) {}
      if (streams.length) break;
    }
    if (streams.length) break;
  }
  return streams.slice(0, 40);
}
async function _resolveKnownPlayer(tmdbId, mediaType, season, episode) {
  const known = _directPlayerUrls(tmdbId, mediaType).slice(0, 2);
  for (const playerUrl of known) {
    try {
      const response = await _fetch(playerUrl);
      const responseUrl = response.url || playerUrl;
      let text = "";
      try { text = await response.text(); } catch (_) {}
      const candidates = _uniq([
        responseUrl,
        ..._extractUrls(text, responseUrl).filter(_playerLike)
      ]).slice(0, 3);
      const runtime = await _resolveRuntimeApi(candidates, mediaType, tmdbId, season, episode);
      if (runtime.length) return runtime;
      const direct = _extractUrls(text, responseUrl).filter(_directMedia);
      if (direct.length) return _streams(direct, responseUrl).slice(0, 12);
    } catch (_) {}
  }
  return [];
}
function _htmlVisibleText(value) {
  const source = _text(value);
  const lower = source.toLowerCase();
  let out = "";
  let cursor = 0;
  let hidden = "";
  while (cursor < source.length) {
    if (hidden) {
      const closeAt = lower.indexOf("</" + hidden, cursor);
      if (closeAt < 0) break;
      cursor = closeAt;
      hidden = "";
      continue;
    }
    if (source.charAt(cursor) !== "<") {
      out += source.charAt(cursor);
      cursor += 1;
      continue;
    }
    const end = source.indexOf(">", cursor + 1);
    if (end < 0) {
      out += source.slice(cursor);
      break;
    }
    let raw = source.slice(cursor + 1, end).trim();
    let closing = raw.charAt(0) === "/";
    if (closing) raw = raw.slice(1).trim();
    let name = "";
    for (let i = 0; i < raw.length; i += 1) {
      const code = raw.charCodeAt(i);
      const alpha = (code >= 65 && code <= 90) || (code >= 97 && code <= 122);
      if (!alpha) break;
      name += raw.charAt(i).toLowerCase();
    }
    if (!closing && (name === "script" || name === "style")) hidden = name;
    out += " ";
    cursor = end + 1;
  }
  return out;
}
function _strictHtmlIdentityOk(html, meta) {
  if (!NIAKVIO_PROVIDER_MODEL.strictHtmlIdentity) return true;
  if (!meta || !meta.title) return false;
  const visible = _htmlVisibleText(html);
  const normalized = _slug(visible);
  const titles = _uniq([meta.title, ...((Array.isArray(meta.aliases) ? meta.aliases : []))])
    .map(_slug)
    .filter(Boolean);
  if (!titles.length || !titles.some(title => normalized.includes(title))) return false;
  const year = _text(meta.year).slice(0, 4);
  if (year && /^\d{4}$/.test(year)) {
    const years = _text(html).match(/\b(?:19|20)\d{2}\b/g) || [];
    if (years.length && !years.includes(year)) return false;
  }
  return true;
}
async function _resolveHtml(meta, mediaType, season, episode) {
  if (!meta || (!meta.title && !meta.tmdbId)) return [];
  const candidates = [];
  if (meta.title) {
    for (const searchUrl of _searchUrls(meta, mediaType, season, episode).slice(0, 2)) {
      try {
        const response = await _fetch(searchUrl);
        const html = await response.text();
        const urls = _extractUrls(html, response.url || searchUrl)
          .filter(value => {
            const host = _origin(value);
            return host && _searchBases().some(base => _origin(base) === host);
          })
          .map(value => ({ url: value, score: _candidateScore(value, meta) }))
          .filter(row => row.score >= 18)
          .sort((a, b) => b.score - a.score)
          .map(row => row.url);
        candidates.push(...urls);
      } catch (_) {}
      if (candidates.length) break;
    }
  }
  candidates.push(..._learnedUrls("detail", meta, mediaType, season, episode));
  const streams = [];
  for (const detailUrl of _uniq(candidates).slice(0, 6)) {
    try {
      const response = await _fetch(detailUrl);
      const html = await response.text();
      if (!_strictHtmlIdentityOk(html, meta)) continue;
      let urls = _extractUrls(html, response.url || detailUrl);
      if (mediaType !== "movie" && season != null && episode != null) {
        const token = new RegExp("(?:s(?:eason)?\\s*0*" + Number(season) + "[^\\n]{0,80}e(?:pisode)?\\s*0*" + Number(episode) + "|0*" + Number(season) + "x0*" + Number(episode) + ")", "i");
        const episodeLinks = urls.filter(value => token.test(value));
        if (episodeLinks.length) {
          for (const episodeUrl of episodeLinks.slice(0, 2)) {
            try {
              const episodeResponse = await _fetch(episodeUrl);
              const episodeHtml = await episodeResponse.text();
              urls = urls.concat(_extractUrls(episodeHtml, episodeResponse.url || episodeUrl));
            } catch (_) {}
          }
        }
      }
      const direct = urls.filter(_directMedia);
      if (direct.length) streams.push(..._streams(direct, response.url || detailUrl));
      if (!direct.length && /iframe|mixed_embed|html_scraper|direct_media/i.test(NIAKVIO_PROVIDER_MODEL.strategy)) {
        const discoveredNested = _uniq(urls.filter(_crawlEligible).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a))).slice(0, 10);
        if (discoveredNested.length) {
          const runtimeCandidates = _uniq([
            ...discoveredNested,
            ..._directPlayerUrls(meta.tmdbId, mediaType)
          ]);
          // A signed player URL can carry short-lived keys required by a
          // learned runtime API. Consume that exact route before recursively
          // crawling third-party embeds, otherwise an unrelated player-like
          // URL can steal the bounded crawl budget and the signed key is lost.
          const runtime = await _resolveRuntimeApi(
            runtimeCandidates,
            mediaType,
            meta.tmdbId,
            season,
            episode
          );
          if (runtime.length) {
            streams.push(...runtime);
          } else {
            // Runtime-route enrichment remains fail-open: providers without a
            // usable learned API continue through the generic player crawl.
            const crawled = await _crawlDirectMedia(
              discoveredNested,
              response.url || detailUrl,
              2
            );
            if (crawled.length) streams.push(...crawled);
          }
        } else {
          const runtimeCandidates = _directPlayerUrls(meta.tmdbId, mediaType);
          if (runtimeCandidates.length) {
            const runtime = await _resolveRuntimeApi(
              runtimeCandidates,
              mediaType,
              meta.tmdbId,
              season,
              episode
            );
            if (runtime.length) streams.push(...runtime);
          }
        }
      }
    } catch (_) {}
    if (streams.length >= 12) break;
  }
  return streams.slice(0, 40);
}
async function getStreams(tmdbId, mediaType, season, episode) {
  const type = String(mediaType || "movie").toLowerCase();
  if (NIAKVIO_PROVIDER_MODEL.supportedTypes.length &&
      !NIAKVIO_PROVIDER_MODEL.supportedTypes.includes(type) &&
      !(type === "tv" && NIAKVIO_PROVIDER_MODEL.supportedTypes.includes("anime"))) {
    return [];
  }
  if (!_runtimePlanAvailable()) return [];
  const strategy = NIAKVIO_PROVIDER_MODEL.strategy;

  // Declarative ProviderBase recipe: a clean reconstruction may need a bounded
  // search -> provider-id -> source chain. This remains data-driven and executes
  // no upstream JavaScript.
  if (NIAKVIO_PROVIDER_MODEL.apiRecipe) {
    const recipeMeta = await _tmdb(tmdbId, type) || {
      title: "",
      year: "",
      tmdbId: String(tmdbId || "")
    };
    const recipe = await _resolveApiRecipe(recipeMeta, type, season, episode);
    if (recipe.length) return recipe;
    if (NIAKVIO_PROVIDER_MODEL.apiRecipe.allowGenericFallback !== true) return [];
  }

  // Reader fast path: consume already learned ID/API/player routes before any
  // title metadata lookup. Runtime executes a plan; it does not discover one.
  if (/api_stream_resolver|direct_media/i.test(strategy)) {
    const api = await _resolveApi(tmdbId, type, season, episode);
    if (api.length) return api;
  }
  const player = await _resolveKnownPlayer(tmdbId, type, season, episode);
  if (player.length) return player;

  const needsMetadata = (NIAKVIO_PROVIDER_MODEL.routes || []).some(route =>
    ["search","detail"].includes(_routeKind(route))
  );
  if (!needsMetadata) {
    if (!/api_stream_resolver|direct_media/i.test(strategy)) {
      return _resolveApi(tmdbId, type, season, episode);
    }
    return [];
  }

  const meta = await _tmdb(tmdbId, type) || {
    title: "",
    year: "",
    tmdbId: String(tmdbId || "")
  };
  const html = await _resolveHtml(meta, type, season, episode);
  if (html.length) return html;
  if (!/api_stream_resolver|direct_media/i.test(strategy)) {
    return _resolveApi(tmdbId, type, season, episode);
  }
  return [];
}
/* NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4 */
/* NIAKVIO_PROVIDER_BASE_RUNTIME_V5 */
/* NIAKVIO_PROVIDER_BASE_RUNTIME_V6 */
/* NIAKVIO_PROVIDER_BASE_RUNTIME_V7 */
function _spv4Family() {
  return _text(NIAKVIO_PROVIDER_MODEL.sourceRuntimeFamily || "unknown").toLowerCase();
}
function _spv4Routes() {
  return Array.isArray(NIAKVIO_PROVIDER_MODEL.routes) ? NIAKVIO_PROVIDER_MODEL.routes.map(_text).filter(Boolean) : [];
}
function _spv4Titles(meta) {
  return _uniq([meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])])
    .map(_text).filter(Boolean).slice(0, 4);
}
function _spv4Base64(value) {
  const raw = _text(value).replace(/\s+/g, "");
  try { if (typeof atob === "function") return atob(raw); } catch (_) {}
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  let bits = 0, bitCount = 0, out = "";
  for (let i = 0; i < raw.length; i += 1) {
    if (raw[i] === "=") break;
    const n = alphabet.indexOf(raw[i]);
    if (n < 0) continue;
    bits = (bits << 6) | n;
    bitCount += 6;
    if (bitCount >= 8) {
      bitCount -= 8;
      out += String.fromCharCode((bits >> bitCount) & 255);
    }
  }
  return out;
}
function _spv4Expand(pattern, meta, vars, mediaType, season, episode) {
  let route = _text(pattern);
  if (!route) return [];
  vars = vars || {};
  const values = {
    query: vars.query != null ? vars.query : (meta && meta.title),
    title: vars.query != null ? vars.query : (meta && meta.title),
    slug: vars.slug != null ? vars.slug : _slug(meta && meta.title),
    id: vars.providerId != null ? vars.providerId : "",
    providerid: vars.providerId != null ? vars.providerId : "",
    tmdbid: meta && meta.tmdbId,
    tmdb_id: meta && meta.tmdbId,
    imdbid: meta && meta.imdbId,
    imdb_id: meta && meta.imdbId,
    media: mediaType === "movie" ? "movie" : "tv",
    type: mediaType === "movie" ? "movie" : "tv",
    season,
    episode
  };
  const encodedQuery = values.query == null ? "" : encodeURIComponent(_text(values.query));
  if (encodedQuery) route = route.replace(/([?&](?:s|q|query|keyword|search|story)=)(?:\.{3})?(?=&|#|$)/gi, function(_, prefix) { return prefix + encodedQuery; });
  route = route.replace(/\{([^}]+)\}/g, function(match, key) {
    const value = values[_text(key).toLowerCase()];
    return value == null || value === "" ? "" : encodeURIComponent(_text(value));
  });
  if (/\{[^}]+\}/.test(route)) return [];
  if (/^https?:\/\//i.test(route)) return [route];
  const out = [];
  for (const base of _runtimeBases()) {
    const absolute = _absolute(route, base);
    if (absolute) out.push(absolute);
  }
  return _uniq(out);
}
function _spv4IsSearchRoute(route, family) {
  const value = _text(route).toLowerCase();
  if (/\{query\}|[?&](?:s|q|query|keyword|search|story)=/i.test(value)) return true;
  if (/\/api\/search(?:[/?#]|$)/i.test(value)) return true;
  return /form/.test(family) && /\/template-php\/[^?#]*fetch\.php(?:[?#]|$)/i.test(value);
}
function _spv4IsActionRoute(route) {
  return /full-story\.php|controller\.php\?mod=playepisode/i.test(_text(route));
}
function _spv4IsDetailRoute(route, family) {
  const value = _text(route).toLowerCase();
  if (!value || _spv4IsSearchRoute(value, family) || _spv4IsActionRoute(value)) return false;
  return /\{(?:slug|id|imdbid|imdb_id|tmdbid|tmdb_id|season|episode)\}/i.test(value) ||
    /\/(?:anime|animes|movie|movies|film|films|serie|series|voir-series|episode|saison|season|saga|catalogue|watch)(?:[/?#.-]|$)/i.test(value);
}
function _spv4SameProviderOrigin(url) {
const candidate = _origin(_substituteDomain(url));
return !!candidate && _runtimeBases().some(base => _origin(_substituteDomain(base)) === candidate);
}
function _spv4AttrUrls(text, base) {
  const out = [];
  const value = _embeddedText(text);
  const re = /(?:src|href|file|url|data-[a-z0-9_:-]+)\s*=\s*["']([^"']+)["']/gi;
  let match;
  while ((match = re.exec(value)) !== null) {
    const absolute = _absolute(match[1], base);
    if (absolute && /^https?:/i.test(absolute)) out.push(absolute);
    if (out.length >= 160) break;
  }
  return _uniq(out.concat(_extractUrls(value, base)));
}
function _spv4UrlScore(url, meta) {
  let score = _candidateScore(url, meta);
  try {
    const path = decodeURIComponent(new URL(url).pathname || "").toLowerCase();
    const wanted = _spv4Titles(meta).map(_slug).filter(Boolean);
    for (const title of wanted) {
      if (title && path.includes(title)) score += 100;
      for (const token of title.split("-").filter(v => v.length >= 3)) if (path.includes(token)) score += 16;
    }
    if (/\/(?:anime|animes|movie|movies|film|films|serie|series|voir-series|watch|title)\//i.test(path)) score += 24;
  } catch (_) {}
  return score;
}
function _spv7DetailUrlEligible(url) {
try {
const parsed = new URL(url);
const path = _text(parsed.pathname).toLowerCase();
const hash = _text(parsed.hash).toLowerCase();
if (/^#(?:comments?|respond|reply|share)/i.test(hash)) return false;
if (/\/(?:feed|wp-json|wp-admin|admin|login|register|privacy|terms)(?:[/?#.-]|$)/i.test(path)) return false;
if (/\.(?:css|js|jpe?g|png|gif|webp|svg|avif|ico|woff2?|ttf)(?:[?#]|$)/i.test(path)) return false;
return true;
} catch (_) { return false; }
}
function _spv4HtmlDetails(html, base, meta) {
return _spv4AttrUrls(html, base)
.filter(_spv4SameProviderOrigin)
.filter(_spv7DetailUrlEligible)
.map(url => ({ url: _substituteDomain(url), score: _spv4UrlScore(url, meta) }))
.filter(row => row.score >= 36)
.sort((a, b) => b.score - a.score)
.map(row => row.url)
.slice(0, 8);
}
function _spv4JsonRows(value, out) {
  out = out || [];
  if (Array.isArray(value)) {
    for (const child of value) _spv4JsonRows(child, out);
    return out;
  }
  if (!value || typeof value !== "object") return out;
  out.push(value);
  for (const child of Object.values(value)) {
    if (child && typeof child === "object") _spv4JsonRows(child, out);
    if (out.length >= 300) break;
  }
  return out;
}
function _spv4TitleScore(title, meta) {
  const actual = _slug(title);
  if (!actual) return 0;
  let best = 0;
  for (const expected of _spv4Titles(meta).map(_slug).filter(Boolean)) {
    if (actual === expected) best = Math.max(best, 240);
    else if (actual.includes(expected) || expected.includes(actual)) best = Math.max(best, 110);
    else {
      let score = 0;
      for (const token of expected.split("-").filter(v => v.length >= 3)) if (actual.includes(token)) score += 18;
      best = Math.max(best, score);
    }
  }
  return best;
}
function _spv4Scalar(value) {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number") return _text(value);
  if (typeof value !== "object") return "";
  for (const key of ["rendered","raw","value","text","title","name","slug","href","url","link","path"]) {
    const child = value[key];
    if (typeof child === "string" || typeof child === "number") return _text(child);
  }
  return "";
}
function _spv4JsonDetails(value, base, meta, mediaType, season, episode, family) {
  const details = [];
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  const rows = _spv4JsonRows(value, [])
    .map(row => ({
      row,
      score: _spv4TitleScore(_spv4Scalar(row.title) || _spv4Scalar(row.name) || _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) || _spv4Scalar(row.label) || "", meta)
    }))
    .filter(item => item.score >= 36)
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);
  for (const item of rows) {
    const row = item.row;
    const direct = _spv4Scalar(row.url) || _spv4Scalar(row.href) || _spv4Scalar(row.permalink) || _spv4Scalar(row.link) || _spv4Scalar(row.path) || _spv4Scalar(row.guid) || "";
    if (direct) {
      const absolute = _absolute(direct, base);
      if (absolute && _spv4SameProviderOrigin(absolute)) details.push(absolute);
    }
    const vars = {
      slug: _spv4Scalar(row.slug) || _spv4Scalar(row.permalink_slug) || _spv4Scalar(row.seo_slug) || _slug(_spv4Scalar(row.title) || _spv4Scalar(row.name) || meta.title),
      providerId: _spv4Scalar(row.id) || _spv4Scalar(row.ID) || _spv4Scalar(row._id) || _spv4Scalar(row.media_id) || _spv4Scalar(row.post_id)
    };
    for (const route of detailRoutes) {
      details.push(..._spv4Expand(route, meta, vars, mediaType, season, episode));
    }
  }
  return _uniq(details).slice(0, 12);
}
async function _spv4SearchResponse(url, query, family) {
  const form = /form/.test(family) && /\/template-php\/[^?#]*fetch\.php(?:[?#]|$)/i.test(url);
  const options = form ? {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Requested-With": "XMLHttpRequest",
      "Referer": _searchBases()[0] || ""
    },
    body: "query=" + encodeURIComponent(_text(query))
  } : {};
  const response = await _fetch(url, options);
  const contentType = _text(response.headers.get("content-type")).toLowerCase();
  if (contentType.includes("json")) return { json: await response.json(), text: "", base: response.url || url };
  const text = await response.text();
  try {
    if (/^\s*[\[{]/.test(text)) return { json: JSON.parse(text), text: "", base: response.url || url };
  } catch (_) {}
  return { json: null, text, base: response.url || url };
}
async function _spv4FindDetails(meta, mediaType, season, episode, family) {
  const out = [];
  const searchRoutes = _spv4Routes().filter(route => _spv4IsSearchRoute(route, family));
  for (const query of _spv4Titles(meta).slice(0, 3)) {
    for (const route of searchRoutes.slice(0, 3)) {
      const urls = _spv4Expand(route, Object.assign({}, meta, { title: query }), { query }, mediaType, season, episode);
      for (const url of urls.slice(0, 2)) {
        try {
          const payload = await _spv4SearchResponse(url, query, family);
          if (payload.json != null) out.push(..._spv4JsonDetails(payload.json, payload.base, meta, mediaType, season, episode, family));
          else out.push(..._spv4HtmlDetails(payload.text, payload.base, meta));
        } catch (_) {}
        if (out.length) break;
      }
      if (out.length) break;
    }
    if (out.length) break;
  }

  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  for (const title of _spv4Titles(meta).slice(0, 3)) {
    const slug = _slug(title);
    if (!slug) continue;
    for (const route of detailRoutes) {
      if (!/\{slug\}/i.test(route) || /\{id\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, Object.assign({}, meta, { title }), { slug }, mediaType, season, episode));
    }
  }
  return _uniq(out).slice(0, 16);
}
function _spv4DirectStreams(urls, referer) {
  const direct = _uniq(urls).filter(_directMedia);
  return direct.length ? _streams(direct, referer).slice(0, 12) : [];
}
async function _spv4NestedStreams(urls, referer) {
  const candidates = _uniq(urls.map(_crawlCanonical)).filter(Boolean).filter(url => _crawlEligible(url) || /(?:sibnet|vidmoly|streamtape|sendvid|vidoza|myvi)/i.test(url)).sort((a,b)=>_crawlUrlScore(b)-_crawlUrlScore(a)).slice(0, 8);
  if (!candidates.length) return [];
  return (await _crawlDirectMedia(candidates, referer, 2)).slice(0, 12);
}
async function _spv4FullStory(detailUrl, meta, mediaType, season, episode) {
  const idMatch = _text(detailUrl).match(/\/(\d+)-/);
  if (!idMatch) return [];
  const route = _spv4Routes().find(value => /full-story\.php/i.test(value));
  if (!route) return [];
  const targets = _spv4Expand(route, meta, { providerId: idMatch[1] }, mediaType, season, episode);
  for (const target of targets.slice(0, 2)) {
    try {
      const response = await _fetch(target, { headers: { "X-Requested-With": "XMLHttpRequest", "Referer": detailUrl } });
      let html = "";
      const contentType = _text(response.headers.get("content-type")).toLowerCase();
      if (contentType.includes("json")) {
        const value = await response.json();
        html = _text(value && value.html);
      } else {
        const raw = await response.text();
        try { const value = JSON.parse(raw); html = _text(value && value.html); } catch (_) { html = raw; }
      }
      if (!html) continue;
      const wanted = Math.max(1, Number(episode) || 1);
      const epNumbers = [];
      const epRe = /data-number\s*=\s*["'](\d+)["']/gi;
      let epMatch;
      while ((epMatch = epRe.exec(html)) !== null) epNumbers.push(Number(epMatch[1]));
      const players = [];
      const cpRe = /id\s*=\s*["']content_player_(\d+)[a-z]*["'][^>]*>\s*(\d+)\s*</gi;
      let cp;
      while ((cp = cpRe.exec(html)) !== null) players.push(cp[2]);
      const index = epNumbers.indexOf(wanted);
      if (index >= 0 && index < players.length && /^\d+$/.test(players[index])) {
        return _streams(["https://video.sibnet.ru/shell.php?videoid=" + players[index]], detailUrl).slice(0, 4);
      }
      const urls = _spv4AttrUrls(html, target);
      const direct = _spv4DirectStreams(urls, target);
      if (direct.length) return direct;
      const nested = await _spv4NestedStreams(urls, target);
      if (nested.length) return nested;
    } catch (_) {}
  }
  return [];
}
async function _spv4PlayEpisode(detailUrl, html, meta, mediaType, season, episode) {
  let pageUrl = detailUrl;
  let pageHtml = html;
  if (mediaType !== "movie" && season != null && episode != null && /\.html(?:[?#]|$)/i.test(detailUrl)) {
    pageUrl = detailUrl.replace(/\.html(?:[?#].*)?$/i, "") + "/" + Number(season || 1) + "-saison/" + Number(episode || 1) + "-episode.html";
    try {
      const response = await _fetch(pageUrl);
      pageHtml = await response.text();
    } catch (_) { return []; }
  }
  const pairs = [];
  const pairRe = /playEpisode\([^,]+,\s*["'](\d+)["']\s*,\s*["']([^"']+)["']/gi;
  let match;
  while ((match = pairRe.exec(pageHtml)) !== null) {
    const key = match[1] + "\u0000" + match[2];
    if (!pairs.some(row => row.key === key)) pairs.push({ key, id: match[1], xfield: match[2] });
    if (pairs.length >= 6) break;
  }
  if (!pairs.length) return [];
  const actionRoute = _spv4Routes().find(value => /controller\.php\?mod=playepisode/i.test(value));
  if (!actionRoute) return [];
  const actionUrls = _spv4Expand(actionRoute, meta, {}, mediaType, season, episode);
  for (const actionUrl of actionUrls.slice(0, 2)) {
    for (const pair of pairs.slice(0, 4)) {
      try {
        const response = await _fetch(actionUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": pageUrl
          },
          body: "id=" + encodeURIComponent(pair.id) + "&xfield=" + encodeURIComponent(pair.xfield) + "&action=playEpisode"
        });
        const text = await response.text();
        const urls = _spv4AttrUrls(text, response.url || actionUrl);
        const direct = _spv4DirectStreams(urls, pageUrl);
        if (direct.length) return direct;
        const nested = await _spv4NestedStreams(urls, pageUrl);
        if (nested.length) return nested;
      } catch (_) {}
    }
  }
  return [];
}
function _spv4SagaTargets(episode) {
  const out = [];
  try {
    const ctx = typeof globalThis !== "undefined" ? globalThis.__nuvioMediaContext : null;
    for (const key of ["absoluteEpisode", "absoluteEpisodeNumber", "episodeAbsolute", "absolute_episode"]) {
      const n = Number(ctx && ctx[key]);
      if (Number.isFinite(n) && n > 0 && !out.includes(n)) out.push(n);
    }
  } catch (_) {}
  const ep = Number(episode);
  if (Number.isFinite(ep) && ep > 0 && !out.includes(ep)) out.push(ep);
  return out;
}
function _spv4ParseSagaMedia(html, targets) {
  const constants = Object.create(null);
  const constRe = /var\s+([A-Za-z0-9_]+)\s*=\s*atob\(["']([^"']+)["']\)/g;
  let cm;
  while ((cm = constRe.exec(html)) !== null) constants[cm[1]] = _spv4Base64(cm[2]);
  const found = [];
  const assignment = /(episodeHD|episodeLow|episode)\s*\[\s*(\d+)\s*\]\s*=\s*([A-Za-z0-9_]+)\s*\+\s*["']([^"']+\.(?:mp4|m3u8))["']/gi;
  let row;
  while ((row = assignment.exec(html)) !== null) {
    const number = Number(row[2]);
    if (!targets.includes(number)) continue;
    const url = _text(constants[row[3]]) + row[4];
    if (/^https?:\/\//i.test(url)) found.push(url);
  }
  return _uniq(found);
}
async function _spv4Saga(detailUrl, html, episode) {
  const targets = _spv4SagaTargets(episode);
  if (!targets.length) return [];
  let urls = _spv4ParseSagaMedia(html, targets);
  if (urls.length) return _streams(urls, detailUrl).slice(0, 6);
  const sagaUrls = _spv4AttrUrls(html, detailUrl).filter(url => /\/saga-\d+(?:[/?#]|$)/i.test(url)).slice(0, 6);
  for (const sagaUrl of sagaUrls) {
    try {
      const response = await _fetch(sagaUrl);
      const sagaHtml = await response.text();
      urls = _spv4ParseSagaMedia(sagaHtml, targets);
      if (urls.length) return _streams(urls, sagaUrl).slice(0, 6);
    } catch (_) {}
  }
  return [];
}
function _spv5SafeHttpStreamUrl(value) {
  const url = _text(value).trim();
  if (!/^https?:\/\//i.test(url)) return "";
  if (/\.torrent(?:[?#]|$)|[?&](?:magnet|infohash|btih)=/i.test(url)) return "";
  return url;
}
async function _spv5Stremio(tmdbId, mediaType, season, episode) {
  const type = mediaType === "movie" ? "movie" : "tv";
  const routes = _spv4Routes().filter(route => {
    const low = _text(route).toLowerCase();
    return /\/stream\//.test(low) && (type === "movie" ? /\/stream\/movie\//.test(low) : /\/stream\/(?:series|tv)\//.test(low));
  });
  for (const route of routes.slice(0, 4)) {
    for (const target of _spv4Expand(route, {tmdbId:_text(tmdbId),title:""}, {providerId:_text(tmdbId)}, type, season, episode).slice(0,3)) {
      try {
        const response = await _fetch(target, {headers:{Accept:"application/json"}});
        let value = null;
        const ct = _text(response.headers.get("content-type")).toLowerCase();
        if (ct.includes("json")) value = await response.json(); else { const raw=await response.text(); try{value=JSON.parse(raw)}catch(_){} }
        const urls=[];
        for (const row of (value && Array.isArray(value.streams) ? value.streams : []).slice(0,40)) {
          if (!row || typeof row !== "object" || row.infoHash || row.infohash || row.magnet || row.torrent) continue;
          const url=_spv5SafeHttpStreamUrl(row.url || row.streamUrl || row.stream_url || "");
          if (url) urls.push(url);
        }
        if (urls.length) return _streams(urls, response.url || target).slice(0,20);
      } catch (_) {}
    }
  }
  return [];
}
async function _spv5DleFilmApi(detailUrl, html, meta, mediaType, season, episode) {
  if (mediaType !== "movie") return [];
  const route = _spv4Routes().find(value => /\/engine\/ajax\/film_api\.php/i.test(_text(value)));
  if (!route) return [];
  const idMatch = _text(detailUrl).match(/\/(\d{2,})-[^/?#]+/) || _text(html).match(/(?:news[_-]?id|data-id|post[_-]?id)\s*[:=]\s*["']?(\d{2,})/i);
  if (!idMatch) return [];
  let targets = _spv4Expand(route, meta, {providerId:idMatch[1]}, mediaType, season, episode);
  targets = targets.map(value => /[?&]id=\d+/i.test(value) ? value : value + (value.includes("?") ? "&" : "?") + "id=" + encodeURIComponent(idMatch[1]));
  for (const target of targets.slice(0,3)) {
    try {
      const response = await _fetch(target,{headers:{"X-Requested-With":"XMLHttpRequest",Referer:detailUrl}});
      const ct=_text(response.headers.get("content-type")).toLowerCase();
      let urls=[];
      if (ct.includes("json")) { const value=await response.json(); urls=_uniq(_sourceUrls(value,response.url||target).concat(_jsonUrls(value))); }
      else { const raw=await response.text(); try{const value=JSON.parse(raw);urls=_uniq(_sourceUrls(value,response.url||target).concat(_jsonUrls(value)))}catch(_){urls=_spv4AttrUrls(raw,response.url||target)} }
      const direct=_spv4DirectStreams(urls,detailUrl); if (direct.length) return direct;
      const nested=await _spv4NestedStreams(urls,detailUrl); if (nested.length) return nested;
    } catch (_) {}
  }
  return [];
}
async function _spv4ResolveDetail(detailUrl, meta, mediaType, season, episode, family) {
  let response, html;
  try {
    response = await _fetch(detailUrl);
    html = await response.text();
  } catch (_) { return []; }
  const base = response.url || detailUrl;
  if (!_strictHtmlIdentityOk(html, meta)) return [];

  if (family === "dle-full-story") {
    const special = await _spv4FullStory(base, meta, mediaType, season, episode);
    if (special.length) return special;
  }
  if (family === "dle-playepisode-form") {
    const special = await _spv4PlayEpisode(base, html, meta, mediaType, season, episode);
    if (special.length) return special;
  }
  if (family === "slug-saga-inline-media") {
    const special = await _spv4Saga(base, html, episode);
    if (special.length) return special;
  }
  if (family === "dle-film-api") {
    const special = await _spv5DleFilmApi(base, html, meta, mediaType, season, episode);
    if (special.length) return special;
  }

  let urls = _spv4AttrUrls(html, base);
  if (mediaType !== "movie" && season != null && episode != null) {
    const s = Math.max(1, Number(season) || 1);
    const e = Math.max(1, Number(episode) || 1);
    const patterns = [
      new RegExp("/saison[-_/]?0*" + s + "[^?#]*episode[-_/]?0*" + e + "(?:[./?#]|$)", "i"),
      new RegExp("/0*" + s + "-saison/0*" + e + "-episode(?:[./?#]|$)", "i"),
      new RegExp("/episode[-_/]?0*" + e + "(?:[./?#]|$)", "i")
    ];
    const episodeLinks = urls.filter(url => patterns.some(pattern => pattern.test(url))).slice(0, 3);
    for (const episodeUrl of episodeLinks) {
      try {
        const epResponse = await _fetch(episodeUrl);
        const epHtml = await epResponse.text();
        urls = urls.concat(_spv4AttrUrls(epHtml, epResponse.url || episodeUrl));
      } catch (_) {}
    }
  }

  // DLE/legacy pages sometimes expose a numeric Sibnet id without a URL.
  const numeric = [];
  const sibRe = /(?:content_player_[^>]+>|videoid\s*[:=]\s*["']?)(\d{3,})/gi;
  let sm;
  while ((sm = sibRe.exec(html)) !== null) numeric.push("https://video.sibnet.ru/shell.php?videoid=" + sm[1]);
  urls = urls.concat(numeric);

  const direct = _spv4DirectStreams(urls, base);
  if (direct.length) return direct;
  return _spv4NestedStreams(urls, base);
}
function _spv7ProviderSiteBases() {
  return _uniq([NIAKVIO_PROVIDER_MODEL.officialSite, NIAKVIO_PROVIDER_MODEL.knownSite])
    .map(_substituteDomain).filter(value => /^https?:/i.test(value));
}
function _spv7DleDetailLinks(html, base, meta) {
  const out = [];
  const text = _embeddedText(html);
  const re = /<a\b([^>]*)href=["']([^"']*(?:newsid=\d+|\/\d+[^"']*))['"]([^>]*)>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = re.exec(text)) !== null) {
    const label = _text(match[1]) + " " + _text(match[3]) + " " + _htmlVisibleText(match[4]);
    const score = _spv4TitleScore(label, meta);
    const url = _absolute(match[2], base);
    if (url && score >= 36 && _spv4SameProviderOrigin(url)) out.push({url:_substituteDomain(url), score});
    if (out.length >= 12) break;
  }
  return out.sort((a,b)=>b.score-a.score).map(row=>row.url).slice(0,6);
}
async function _spv7DleFindDetails(meta, mediaType, season, episode) {
  const out = [];
  for (const base of _spv7ProviderSiteBases().slice(0,2)) {
    try {
      const target = new URL("/engine/ajax/search.php", base).toString();
      const response = await _fetch(target, {
        method:"POST",
        headers:{"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With":"XMLHttpRequest",Referer:base+"/"},
        body:"query="+encodeURIComponent(_text(meta && meta.title))+"&page=1"
      });
      out.push(..._spv7DleDetailLinks(await response.text(), response.url || target, meta));
    } catch (_) {}
    if (out.length) break;
  }
  if (out.length) return _uniq(out).slice(0,8);
  return _spv4FindDetails(meta, mediaType, season, episode, "dle-film-api");
}
async function _spv7DleTv(tmdbId, mediaType, season, episode) {
  if (mediaType === "movie" || tmdbId == null || episode == null) return [];
  const wantedSeason = Math.max(1, Number(season) || 1);
  const wantedEpisode = String(Math.max(1, Number(episode) || 1));
  for (const base of _spv7ProviderSiteBases().slice(0,2)) {
    try {
      const seasonsUrl = new URL("/engine/ajax/get_seasons.php?serie_tag=s-"+encodeURIComponent(_text(tmdbId))+"&news_id=0", base).toString();
      const response = await _fetch(seasonsUrl, {headers:{Accept:"application/json,text/plain,*/*",Referer:base+"/"}});
      const raw = await response.text();
      let seasons = null; try { seasons = JSON.parse(raw); } catch (_) {}
      if (!Array.isArray(seasons) || !seasons.length) continue;
      let chosen = seasons.find(row => {
        const match = _text(row && row.title).match(/saison\s*(\d+)/i);
        return match && Number(match[1]) === wantedSeason;
      }) || seasons[0];
      const seasonId = _text(chosen && chosen.id).trim();
      if (!seasonId) continue;
      const epsUrl = new URL("/data/eps_"+encodeURIComponent(seasonId)+".txt?v="+Math.floor(Date.now()/30000), base).toString();
      const epsResponse = await _fetch(epsUrl, {headers:{Accept:"application/json,text/plain,*/*",Referer:base+"/"}});
      const epsRaw = await epsResponse.text();
      let eps = null; try { eps = JSON.parse(epsRaw); } catch (_) {}
      if (!eps || typeof eps !== "object") continue;
      const rows = [];
      const seen = new Set();
      for (const lang of ["vf","vostfr","vo"]) {
        const bucket = eps[lang];
        const players = bucket && (bucket[wantedEpisode] || bucket[Number(wantedEpisode)]);
        if (!players || typeof players !== "object") continue;
        for (const [host, value] of Object.entries(players)) {
          const url = _text(value).trim();
          if (!/^https?:\/\//i.test(url) || seen.has(url)) continue;
          seen.add(url);
          rows.push({name:NIAKVIO_PROVIDER_MODEL.displayName,title:"["+lang.toUpperCase()+"] "+_text(host).toUpperCase(),url,language:lang,headers:{Referer:base+"/"}});
        }
      }
      if (rows.length) return rows.slice(0,24);
    } catch (_) {}
  }
  return [];
}
async function _spv4GetStreams(tmdbId, mediaType, season, episode) {
const family = _spv4Family();
const type = _text(mediaType || "movie").toLowerCase();
if (family === "stremio-json") {
const stremio = await _spv5Stremio(tmdbId, type, season, episode);
if (stremio.length) return stremio;
}
if (family && family !== "unknown") {
const meta = await _tmdb(tmdbId, type);
// Known source families execute their typed source plan before the generic
// fallback. This prevents broad catalogue/API guesses from spending the
// provider budget on category pages, dead aliases and placeholder routes.
if (meta && meta.title) {
if (family === "dle-film-api" && type !== "movie") {
const tv = await _spv7DleTv(tmdbId, type, season, episode);
if (tv.length) return tv;
}
const details = family === "dle-film-api"
? await _spv7DleFindDetails(meta, type, season, episode)
: await _spv4FindDetails(meta, type, season, episode, family);
for (const detail of details.slice(0, 8)) {
const streams = await _spv4ResolveDetail(detail, meta, type, season, episode, family);
if (streams.length) return streams;
}
}
}
const primary = await getStreams(tmdbId, type, season, episode);
if (Array.isArray(primary) && primary.length) return primary;
return [];
}
module.exports = {
  getStreams: _spv4GetStreams,
  get __niakvioProviderBase(){ return NIAKVIO_PROVIDER_MODEL; }
};
'''
    return template.encode("utf-8")


def compose_provider_bundle(
    provider_id: str,
    base_data: bytes,
    provider_data: dict[str, Any],
) -> bytes:
    """Compose one Provider envelope from common Base + DATA; Core Lego comes later."""
    assert_clean_provider_base(base_data, provider_id)
    if not isinstance(provider_data, dict):
        raise ValueError(f"{provider_id}: provider DATA must be an object")
    model = dict(provider_data)
    canonical = canonical_id(provider_id)
    if str(model.get("providerId") or "") != canonical:
        raise ValueError(
            f"{provider_id}: provider DATA id mismatch actual={model.get('providerId')!r}"
        )
    if str(model.get("authoring") or "") != CURRENT_PROVIDER_MODEL_AUTHORING:
        raise ValueError(
            f"{provider_id}: provider DATA authoring mismatch "
            f"actual={model.get('authoring')!r}"
        )
    payload = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fix_component = canonical.upper()
    config_id = f"PROVIDER.{fix_component}.CONFIG.V1"
    config_block = render_managed_fix(
        config_id,
        f"const NIAKVIO_PROVIDER_MODEL = Object.freeze({payload});",
        data=model,
    )
    base_text = base_data.decode("utf-8", errors="strict").rstrip()
    source = (
        f"{PROVIDER_BEGIN_MARKER}\n"
        f"/* NIAKVIO_PROVIDER_ID:{canonical} */\n"
        f"{base_text}\n\n"
        f"{config_block}\n"
        f"{PROVIDER_END_MARKER}\n"
    )
    fix_ids = validate_managed_fixes(source)
    if fix_ids != [config_id]:
        raise ValueError(f"{provider_id}: invalid initial Provider Lego layout: {fix_ids}")
    if source.count(PROVIDER_BEGIN_MARKER) != 1 or source.count(PROVIDER_END_MARKER) != 1:
        raise ValueError(f"{provider_id}: composed Provider envelope cardinality invalid")
    if not source.rstrip().endswith(PROVIDER_END_MARKER):
        raise ValueError(f"{provider_id}: bytes found after END PROVIDER")
    return source.encode("utf-8")


def persist_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
    provider_model: dict[str, Any] | None = None,
    overrides_path: Path | None = None,
) -> tuple[str, str, bool]:
    return persist_base_from_seed(
        provider_id,
        build_clean_provider_seed(
            provider_id,
            manifest_entry,
            known_site=known_site,
            provider_model=provider_model,
        ),
        overrides_path=overrides_path,
    )


def provider_base_store_metadata(
    *,
    provider_count: int,
    unique_base_count: int,
    clean_reconstructed: int,
    reconstruction_required: int,
    previous_store: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical ProviderBase-store metadata shared by every publisher."""
    previous = previous_store if isinstance(previous_store, dict) else {}
    initial_scope = int(previous.get("initial_reconstruction_scope") or INITIAL_RECONSTRUCTION_SCOPE)
    if provider_count > 0:
        initial_scope = min(max(1, initial_scope), provider_count)
    return {
        "schema_version": max(4, int(previous.get("schema_version") or 0)),
        "provider_count": int(provider_count),
        "unique_base_count": int(unique_base_count),
        "initial_reconstruction_scope": initial_scope,
        "migration_scope": "all-current-providers",
        "owner": "provider_pipeline",
        "future_source": "provider_pipeline_only",
        "clean_reconstructed": int(clean_reconstructed),
        "reconstruction_required": int(reconstruction_required),
        "authoring_version": CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "authoring_policy": "niakvio-owned-clean-reconstruction-only",
        "clean_source": CLEAN_RECONSTRUCTION_SOURCE,
        "legacy_provider_role": "compatibility-lkg-and-knowledge-only",
        "upstream_code_role": "knowledge-only",
        "runtime_role": "reader-only",
        "runtime_route_discovery": False,
        "upstream_code_executed": False,
        "published_legacy_code_may_seed_new_base": False,
        "upstream_code_may_seed_new_base": False,
        "git_history_code_may_seed_new_base": False,
        "core_may_create_or_mutate_base": False,
        "semantic_validation": "on_base_creation_or_change",
        "core_integrity_validation": "coverage_and_sha_only",
        "derived_layers_forbidden": list(DERIVED_BASE_MARKERS),
    }

def repair_legacy_bases() -> dict[str, Any]:
    """Mark every pre-v2 ProviderBase as compatibility-only legacy state.

    This command deliberately does *not* reconstruct ProviderBase bytes. The
    currently published implementation may remain available to existing clients
    and may be observed as LKG evidence, but it is never an executable seed for
    the new NiakVIO-owned ProviderBase.

    A provider leaves this queue only after a clean NiakVIO seed has been
    reconstructed independently, validated in Learning/Lab, materialized as a
    ProviderBase, and recorded with CLEAN_RECONSTRUCTION_SOURCE.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    provider_count = 0
    reconstruction_required = 0
    clean_reconstructed = 0
    marked_at = datetime.now(timezone.utc).isoformat()

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or ""))
        if not provider_id:
            continue
        provider_count += 1
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        assert_base_layering(path.read_bytes(), provider_id)

        if requires_clean_reconstruction(row):
            reconstruction_required += 1
            row["clean_reconstruction_required"] = True
            if is_clean_reconstruction_candidate(row):
                row["legacy_provider_base_role"] = "superseded-by-clean-candidate"
                row["clean_reconstruction_candidate_role"] = "pending-pipeline-proof"
            else:
                row["legacy_provider_base_role"] = "compatibility-lkg-only"
                row.pop("clean_reconstruction_candidate_role", None)
            row["legacy_provider_js_role"] = "knowledge-only-for-reconstruction"
            row["legacy_provider_js_executed_for_reconstruction"] = False
            row.setdefault("clean_reconstruction_marked_at", marked_at)
        else:
            clean_reconstructed += 1
            row["clean_reconstruction_required"] = False
            row.pop("legacy_provider_base_role", None)
            row.pop("legacy_provider_js_role", None)
            row.pop("legacy_provider_js_executed_for_reconstruction", None)
            row.pop("clean_reconstruction_candidate_role", None)

    store = provenance.get("provider_base_store")
    if not isinstance(store, dict):
        store = {}
        provenance["provider_base_store"] = store
    store.update(
        provider_base_store_metadata(
            provider_count=provider_count,
            unique_base_count=provider_count,
            clean_reconstructed=clean_reconstructed,
            reconstruction_required=reconstruction_required,
            previous_store=store,
        )
    )
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "providers": provider_count,
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": reconstruction_required,
    }

def repair_derived_base_tails() -> dict[str, Any]:
    """Remove leaked publication-only tails from canonical ProviderBase files.

    This is a layering repair only. It never promotes a pending clean candidate,
    never changes the preserved production LKG reference, and never invents
    provider logic. If a previously verified canonical base must change, its
    clean proof is invalidated and it returns to pending canonical Deep proof.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    repaired: list[str] = []
    invalidated: list[str] = []
    repaired_at = datetime.now(timezone.utc).isoformat()

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or ""))
        if not provider_id:
            continue
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        data = path.read_bytes()
        text = data.decode("utf-8", errors="strict")
        leaked = forbidden_base_markers(data)
        if "NIAKVIO_PROVIDER_MODEL = Object.freeze(" in text:
            leaked.append("NIAKVIO_PROVIDER_MODEL_DATA")
        if "NIAKVIO_PROVIDER_ID:" in text:
            leaked.append("NIAKVIO_PROVIDER_ID_DATA")
        if not leaked:
            continue

        clean, stripped = clean_derived_provider_base(provider_id, data)
        if not stripped or clean == data:
            raise ValueError(
                f"{provider_id}: derived ProviderBase layer detected but deterministic strip made no change: "
                + ",".join(leaked)
            )
        validate_base(clean, provider_id)
        relative, digest = write_base(provider_id, clean)

        was_verified = is_clean_reconstructed(row)
        row["base_filename"] = relative
        row["base_sha256"] = digest
        row["base_migration_stripped_generated_core"] = True
        row["base_layering_repaired_at"] = repaired_at
        row["base_layering_repair"] = {
            "schema_version": 1,
            "mode": "strip-derived-publication-tail-only",
            "removed_markers": leaked,
        }
        if was_verified:
            row["base_source"] = CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE
            row["clean_reconstruction_candidate"] = True
            row["clean_reconstruction_verified"] = False
            row["clean_reconstruction_required"] = True
            row["clean_reconstruction_candidate_role"] = "pending-pipeline-proof"
            row["legacy_provider_base_role"] = "superseded-by-clean-candidate"
            invalidated.append(provider_id)
        repaired.append(provider_id)

    provider_ids = [
        canonical_id(str(entry.get("id") or ""))
        for entry in manifest.get("scrapers") or []
        if isinstance(entry, dict) and canonical_id(str(entry.get("id") or ""))
    ]
    clean_count = sum(1 for provider_id in provider_ids if is_clean_reconstructed(rows.get(provider_id)))
    store = provenance.get("provider_base_store")
    if not isinstance(store, dict):
        store = {}
        provenance["provider_base_store"] = store
    store.update(
        provider_base_store_metadata(
            provider_count=len(provider_ids),
            unique_base_count=len(provider_ids),
            clean_reconstructed=clean_count,
            reconstruction_required=len(provider_ids) - clean_count,
            previous_store=store,
        )
    )
    if repaired:
        PROVENANCE.write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "providers": len(provider_ids),
        "repaired": len(repaired),
        "repaired_ids": repaired,
        "invalidated": len(invalidated),
        "invalidated_ids": invalidated,
    }


def migrate_existing() -> dict[str, Any]:
    """Disabled legacy migration entry point.

    Published, upstream, snapshot and Git-history JavaScript are knowledge only;
    none of them may be transformed into a durable ProviderBase.
    """
    raise ValueError(
        "migrate-existing is disabled: legacy/upstream/public JavaScript may not seed ProviderBase; "
        "use NiakVIO clean reconstruction through Learning"
    )

def validate_all(*, validate_artifacts: bool = False) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers") or {}
    checked = 0
    bases: set[str] = set()
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        data = path.read_bytes()
        assert_base_layering(data, provider_id)
        if validate_artifacts:
            validate_base(data, provider_id)
        bases.add(path.relative_to(ROOT).as_posix())
        checked += 1
    if checked != len(manifest.get("scrapers") or []):
        raise ValueError(f"ProviderBase coverage mismatch checked={checked} manifest={len(manifest.get('scrapers') or [])}")
    clean_reconstructed = sum(
        1
        for entry in manifest.get("scrapers") or []
        if isinstance(entry, dict)
        and is_clean_reconstructed(rows.get(canonical_id(str(entry.get("id") or ""))))
    )
    return {
        "checked": checked,
        "unique_bases": len(bases),
        "artifact_validation": bool(validate_artifacts),
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": checked - clean_reconstructed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate-existing")
    sub.add_parser("repair-legacy")
    sub.add_parser("repair-derived")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also run the expensive Node provider validator for every base.",
    )
    args = parser.parse_args()
    if args.command == "migrate-existing":
        result = migrate_existing()
        print(
            f"FIELD_PROVIDER_BASE_MIGRATION providers={result['providers']} "
            f"migrated={result['migrated']} reused={result['reused']}"
        )
    elif args.command == "repair-legacy":
        result = repair_legacy_bases()
        print(
            f"FIELD_PROVIDER_BASE_REPAIR providers={result['providers']} "
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']}"
        )
    elif args.command == "repair-derived":
        result = repair_derived_base_tails()
        print(
            f"FIELD_PROVIDER_BASE_DERIVED_REPAIR providers={result['providers']} "
            f"repaired={result['repaired']} invalidated={result['invalidated']} "
            f"ids={','.join(result['repaired_ids']) or 'none'}"
        )
    else:
        result = validate_all(validate_artifacts=bool(args.artifacts))
        print(
            f"FIELD_PROVIDER_BASE_COVERAGE checked={result['checked']} "
            f"unique_bases={result['unique_bases']} "
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']} "
            f"artifact_validation={str(result['artifact_validation']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
