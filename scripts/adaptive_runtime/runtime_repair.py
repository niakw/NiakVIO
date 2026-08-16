#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Provider-agnostic adaptive layer for the strict runtime repair engine."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "scripts" / "runtime_repair.py"
_spec = importlib.util.spec_from_file_location("_nuvio_runtime_repair_base", BASE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load base runtime repair engine: {BASE_PATH}")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
for _name in dir(_base):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_base, _name)

INFRASTRUCTURE_HOSTS = {
    "api.themoviedb.org", "graphql.anilist.co", "kitsu.io",
    "arm.haglund.dev", "v3-cinemeta.strem.io", "raw.githubusercontent.com",
    "github.com", "npms.io", "lodash.com", "openjsf.org", "underscorejs.org",
}
ADAPTIVE_MARKERS = (
    "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5",
)
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'


def _mapping_entry(mapping: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(mapping, dict):
        return {}
    direct = mapping.get(provider_id)
    if isinstance(direct, dict):
        return direct
    wanted = provider_id.casefold()
    for key, value in mapping.items():
        if str(key).casefold() == wanted and isinstance(value, dict):
            return value
    return {}


def _origin(raw: Any) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value.lstrip("/")
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _provider_metadata(candidate: dict[str, Any]) -> dict[str, Any]:
    for key in ("manifest_provider", "metadata", "canonical_metadata", "manifest"):
        value = candidate.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _adaptive_runtime_options(candidate: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    provider_id = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
    if not provider_id:
        return None
    patch = _mapping_entry(config.get("provider_patches"), provider_id)
    capability = _mapping_entry(config.get("provider_capabilities"), provider_id)
    metadata = _provider_metadata(candidate)
    canonical = candidate.get("canonical") if isinstance(candidate.get("canonical"), dict) else {}
    if str(capability.get("strategy") or patch.get("capability") or "") == "official_domain_hub" and not patch.get("official_site"):
        return None

    recovery_options: dict[str, Any] = {}
    script_options = patch.get("patch_script_options")
    if isinstance(script_options, dict):
        for key, value in script_options.items():
            if str(key).endswith("vf_catalogue_recovery.py") and isinstance(value, dict):
                recovery_options = value
                break

    explicit = [
        recovery_options.get("base_url"), patch.get("official_site"),
        metadata.get("baseUrl"), metadata.get("base_url"), metadata.get("url"),
        canonical.get("baseUrl"), canonical.get("base_url"), canonical.get("url"),
    ]
    explicit.extend((metadata.get("logo"), canonical.get("logo")))
    observed = capability.get("observed_origins") if isinstance(capability.get("observed_origins"), list) else []

    provider_token = re.sub(r"[^a-z0-9]+", "", provider_id)
    base_url = None
    for raw in explicit + list(observed):
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        compact_host = re.sub(r"[^a-z0-9]+", "", host)
        if raw in {patch.get("official_site"), recovery_options.get("base_url")} or (provider_token and provider_token in compact_host):
            base_url = peer
            break
    if not base_url:
        return None

    types: list[str] = []
    for source in (
        recovery_options.get("types"), patch.get("published_types"),
        metadata.get("supportedTypes"), canonical.get("supportedTypes"),
        capability.get("catalogue_types"),
    ):
        if isinstance(source, list):
            for value in source:
                item = str(value).casefold()
                if item in {"movie", "tv", "anime"} and item not in types:
                    types.append(item)
    if not types:
        types = ["movie", "tv", "anime"]

    search_paths = [str(v) for v in recovery_options.get("search_paths") or [] if str(v).strip()] or [
        "/?s={query}", "/search?q={query}",
        "/index.php?do=search&subaction=search&story={query}",
    ]
    direct_paths = [str(v) for v in recovery_options.get("direct_paths") or [] if str(v).strip()] or [
        "/{slug}", "/film/{slug}", "/films/{slug}",
        "/anime/{slug}", "/serie/{slug}", "/series/{slug}",
    ]
    blocked_hosts = {
        "googletagmanager.com", "google-analytics.com", "static.cloudflareinsights.com",
        "cloudflareinsights.com", "connect.facebook.net", "doubleclick.net",
        "googlesyndication.com", "fstream.top",
    }
    blocked_hosts.update(str(v).casefold().lstrip(".") for v in recovery_options.get("blocked_hosts") or [] if str(v).strip())
    blocked_paths = {"/gtag/js", "/cdn-cgi/rum", "/beacon.min.js", "/troll/"}
    blocked_paths.update(str(v).casefold() for v in recovery_options.get("blocked_path_patterns") or [] if str(v).strip())

    endpoint_origins: list[str] = []
    for raw in observed:
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        if peer not in endpoint_origins:
            endpoint_origins.append(peer)

    return {
        "provider_name": str(metadata.get("name") or provider_id or "Provider"),
        "base_url": base_url,
        "endpoint_origins": endpoint_origins[:32],
        "types": types,
        "search_paths": search_paths,
        "direct_paths": direct_paths,
        "max_pages": 10,
        "max_embeds": 10,
        "max_depth": 3,
        "timeout_ms": 9000,
        "blocked_hosts": sorted(blocked_hosts),
        "blocked_path_patterns": sorted(blocked_paths),
    }


def _adaptive_failure(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "runtime_error")
    playable = _base.playable_stream_count(result)
    if status == "healthy" and playable > 0:
        return False
    failures = {str(test.get("failure_class") or "") for test in _base._tests(result)}
    return status in {"no_streams", "degraded", "blocked", "provider_unreachable", "unavailable"} or bool(failures & {
        "content_lookup_completed_no_streams", "stream_not_playback_verified",
        "stream_http_blocked", "provider_http_blocked", "provider_http_error",
        "worker_memory_exhausted",
    })


def matching_profiles(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
    config = config or load_overrides()
    matches = list(_base.matching_profiles(candidate, result, source_text, config))
    name = "adaptive_runtime_recovery"
    if _adaptive_failure(result) and _adaptive_runtime_options(candidate, config) is not None and name not in matches:
        matches.append(name)
    return matches


def _strip_generated_adaptive_wrapper(source_text: str) -> str:
    """Remove repository-generated V1-V5 adaptive wrappers before peer inference."""
    cursor = 0
    parts: list[str] = []
    while True:
        starts = [source_text.find(marker, cursor) for marker in ADAPTIVE_MARKERS]
        starts = [value for value in starts if value >= 0]
        if not starts:
            parts.append(source_text[cursor:])
            break
        start = min(starts)
        parts.append(source_text[cursor:start])
        call = source_text.find(ADAPTIVE_CALL, start)
        end = source_text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper")
        cursor = end + 2
    return "".join(parts)


def _source_endpoint_origins(source_text: str) -> list[str]:
    output: list[str] = []
    for raw in re.findall(r"https?://[A-Za-z0-9.-]+(?::\d+)?", source_text):
        peer = _origin(raw)
        if not peer:
            continue
        host = (urlparse(peer).hostname or "").casefold()
        if host in INFRASTRUCTURE_HOSTS or any(host.endswith("." + item) for item in INFRASTRUCTURE_HOSTS):
            continue
        if peer not in output:
            output.append(peer)
        if len(output) >= 32:
            break
    return output


def _apply_adaptive(parent_data: bytes, candidate: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    options = _adaptive_runtime_options(candidate, load_overrides())
    if options is None:
        return parent_data, []
    source_text = parent_data.decode("utf-8", errors="strict")
    native_source = _strip_generated_adaptive_wrapper(source_text)
    options = dict(options)
    peers = list(options.get("endpoint_origins") or [])
    for peer in _source_endpoint_origins(native_source):
        if peer not in peers:
            peers.append(peer)
    options["endpoint_origins"] = peers[:32]
    script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py"
    spec = importlib.util.spec_from_file_location("nuvio_adaptive_runtime_recovery", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched = module.apply(source_text, options=options).encode("utf-8")
    if patched == parent_data:
        return parent_data, []
    return patched, [{"type": "patch_profile", "profile": "adaptive_runtime_recovery", "phase": "runtime", "revision": 5, "options": options}]


def create_repair_candidate(stage: Path, candidate: dict[str, Any], profile_name: str, round_number: int) -> tuple[dict[str, Any] | None, str | None]:
    if profile_name != "adaptive_runtime_recovery":
        return _base.create_repair_candidate(stage, candidate, profile_name, round_number)
    source_path = (stage / str(candidate.get("local_path") or "")).resolve()
    providers_root = (stage / "providers").resolve()
    try:
        source_path.relative_to(providers_root)
    except ValueError:
        return None, "unsafe_parent_path"
    if not source_path.is_file():
        return None, "missing_parent_artifact"
    parent_data = source_path.read_bytes()
    try:
        patched, records = _apply_adaptive(parent_data, candidate)
    except Exception as exc:
        return None, f"patch_exception:{type(exc).__name__}:{exc}"
    if patched == parent_data or not records:
        return None, "structural_profile_made_no_change"

    digest = hashlib.sha256(patched).hexdigest()
    parent_digest = hashlib.sha256(parent_data).hexdigest()
    repair_dir = stage / "providers" / "runtime-repairs" / _base._safe_fragment(str(candidate.get("source") or "source"))
    repair_dir.mkdir(parents=True, exist_ok=True)
    target = repair_dir / (
        f"{_base._safe_fragment(str(candidate.get('canonical_id') or 'provider'))}--"
        f"r{round_number}--adaptive_runtime_recovery--{digest[:16]}.js"
    )
    target.write_bytes(patched)
    try:
        _base._validate_artifact(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        return None, f"artifact_validation_failed:{type(exc).__name__}:{exc}"

    repaired = copy.deepcopy(candidate)
    parent_key = str(candidate.get("key"))
    repaired["key"] = f"{parent_key}::repair:r{round_number}:adaptive_runtime_recovery:{digest[:8]}"
    repaired["local_path"] = target.relative_to(stage).as_posix()
    repaired["sha256"] = digest
    repaired["bytes"] = len(patched)
    repaired["local_patches"] = list(candidate.get("local_patches") or []) + records
    repaired["runtime_repair"] = {
        "parent_key": parent_key,
        "parent_sha256": parent_digest,
        "round": round_number,
        "profile": "",
        "strategy": "adaptive_runtime_recovery",
        "revision": 5,
    }
    return repaired, None
