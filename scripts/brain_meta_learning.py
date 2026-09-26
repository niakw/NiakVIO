#!/usr/bin/env python3
"""NiakVIO Brain meta-learning and architecture-gap synthesis.

Provider-agnostic architecture layer: classify sanitized failures, detect
capability gaps, and synthesize bounded new strategy/layer contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

FAILURE_FAMILY_TAXONOMY: dict[str, tuple[str, ...]] = {
    "route_discovery": ("route", "hub", "domain", "redirect", "authority", "discovery"),
    "search_catalogue": ("search", "catalog", "lookup", "query", "result_zero"),
    "session_antibot": ("waf", "challenge", "cookie", "session", "captcha", "antibot", "cloudflare"),
    "network_transport": ("network", "http_error", "timeout", "connect", "transport"),
    "tls_dns": ("tls", "ssl", "sni", "alpn", "dns", "certificate", "resolve"),
    "api_schema": ("api", "schema", "json", "graphql", "response_shape"),
    "dynamic_javascript": ("javascript", "bundle", "hydration", "dynamic", "script"),
    "player_embed": ("player", "embed", "iframe", "server"),
    "terminal_media": ("terminal", "media", "stream", "m3u8", "mpd", "hls", "dash"),
    "token_crypto": ("token", "encrypt", "decrypt", "signature", "nonce", "hash", "key"),
    "content_identity": ("identity", "wrong_content", "tmdb", "title", "alias"),
    "episodic_mapping": ("season", "episode", "episod", "series", "anime"),
    "pagination_navigation": ("pagination", "page", "cursor", "next"),
    "rate_limit_cache": ("rate", "429", "throttle", "cache", "stale"),
    "provider_runtime_code": ("runtime", "exception", "syntax", "provider_js", "execution"),
    "materialization_projection": ("materializ", "projection", "manifest", "override", "published_bytes"),
    "stream_metadata": ("language", "quality", "resolution", "badge", "metadata"),
    "media_integrity": ("playback", "duration", "temporary", "placeholder", "fake_media", "short_vod"),
    "client_runtime_divergence": ("android", "ios", "desktop", "native", "node", "client", "harness"),
}

ARCHITECTURE_LAYERS: tuple[dict[str, str], ...] = (
    {"id": "causal_failure_taxonomy", "output": "failure_family"},
    {"id": "capability_gap_detector", "output": "capability_gap"},
    {"id": "meta_learning_gap_synthesis", "output": "strategy_blueprint"},
    {"id": "architecture_layer_synthesis", "output": "target_layer"},
    {"id": "verification_contract_synthesis", "output": "acceptance_contract"},
    {"id": "negative_memory_novelty_guard", "output": "negative_memory_signature"},
    {"id": "force_architecture_promotion", "output": "promotion_contract"},
)


@dataclass(frozen=True)
class GapDiagnosis:
    failure_family: str
    target_layer: str
    gap_kind: str
    needs_new_strategy: bool
    needs_new_layer: bool
    negative_memory_signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "failureFamily": self.failure_family,
            "targetLayer": self.target_layer,
            "gapKind": self.gap_kind,
            "needsNewStrategy": self.needs_new_strategy,
            "needsNewLayer": self.needs_new_layer,
            "negativeMemorySignature": self.negative_memory_signature,
        }


def classify_failure_family(*values: Any) -> str:
    text = " ".join(str(value or "") for value in values).casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", text)
    for family, needles in FAILURE_FAMILY_TAXONOMY.items():
        for needle in needles:
            token = re.sub(r"[^a-z0-9]+", " ", needle.casefold()).strip()
            if token and re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", normalized):
                return family
    return "unknown_new_failure"


def infer_target_layer(failure_family: str, *values: Any) -> str:
    text = " ".join(str(value or "") for value in values).casefold()
    if failure_family in {"network_transport", "tls_dns", "session_antibot"}:
        return "harness" if any(x in text for x in ("harness", "native", "browser", "client")) else "network"
    if failure_family == "materialization_projection":
        return "materialization"
    if failure_family == "client_runtime_divergence":
        return "client-runtime"
    if failure_family in {"content_identity", "episodic_mapping", "stream_metadata", "media_integrity"}:
        return "core"
    if failure_family in {
        "route_discovery", "search_catalogue", "api_schema", "dynamic_javascript",
        "player_embed", "terminal_media", "token_crypto", "pagination_navigation",
        "rate_limit_cache", "provider_runtime_code",
    }:
        return "provider"
    return "unknown-new-layer"


def diagnose_gap(
    *,
    failure_class: Any,
    profile: Any = "",
    signature: Any = "",
    observed_stage: Any = "",
    exhausted_profiles: list[str] | tuple[str, ...] = (),
) -> GapDiagnosis:
    family = classify_failure_family(failure_class, profile, signature, observed_stage)
    layer = infer_target_layer(family, failure_class, profile, signature, observed_stage)
    exhausted = {str(x or "").strip() for x in exhausted_profiles if str(x or "").strip()}
    unknown = family == "unknown_new_failure"
    gap_kind = (
        "novel_failure_and_layer"
        if unknown and layer == "unknown-new-layer"
        else "novel_failure_family"
        if unknown
        else "known_family_exhausted"
        if exhausted
        else "known_family"
    )
    return GapDiagnosis(
        failure_family=family,
        target_layer=layer,
        gap_kind=gap_kind,
        needs_new_strategy=bool(unknown or exhausted),
        needs_new_layer=layer == "unknown-new-layer",
        negative_memory_signature=(
            f"family:{family}|layer:{layer}|profile:{str(profile or '').strip() or 'none'}"
        ),
    )


def synthesize_gap_blueprint(provider_ids: list[str], diagnosis: GapDiagnosis) -> dict[str, Any]:
    providers = sorted({str(x or "").strip().casefold() for x in provider_ids if str(x or "").strip()})
    strategy = "novel_architecture_layer_synthesis_v1" if diagnosis.needs_new_layer else "novel_failure_gap_synthesis_v1"
    return {
        "strategyId": strategy,
        "failureFamily": diagnosis.failure_family,
        "targetLayer": diagnosis.target_layer,
        "gapKind": diagnosis.gap_kind,
        "providers": providers,
        "providerCount": len(providers),
        "causalTrigger": "known strategies are exhausted or evidence falls outside the current technical taxonomy",
        "method": "derive the smallest new allowlisted capability, execute it only in Learning/Lab, and require causal proof before Core eligibility",
        "requiredEvidence": [
            "sanitized failing observation",
            "current pipeline stage and causal boundary",
            "negative memory for exhausted strategies",
            "current-byte or representative-client reproduction",
        ],
        "acceptanceProof": [
            "new capability is causally distinguishable from existing families",
            "bounded executable implementation exists",
            "targeted test proves progress or resolution",
            "identity/content safety is preserved",
            "green-lane non-regression passes",
        ],
        "negativeMemorySignature": diagnosis.negative_memory_signature,
        "productionWritesAllowed": False,
        "providerPublicationAuthority": False,
        "forcePromotionEligible": True,
    }
