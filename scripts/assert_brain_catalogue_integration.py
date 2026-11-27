#!/usr/bin/env python3
"""End-to-end read-only proof that current source evidence reaches the pinned Brain.

This gate intentionally validates the evidence bridge only:
current exact-byte official parent -> independent sanitized source probe -> Brain
adapter -> prompt witness. It never grants provider mutation, publication,
identity or playback authority, and it must not pin historical run counts.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAIN = ROOT / "brain-replay"
sys.path.insert(0, str(BRAIN / "src"))

from niakvio_brain_llm.niakvio_adapter import request_from_checkout  # noqa:E402
from niakvio_brain_llm.prompting import build_prompt_payload  # noqa:E402
from niakvio_brain_llm.priors import build_causal_prior  # noqa:E402

pin = json.loads((ROOT / "automation/brain-pinned-source.json").read_text("utf-8"))
sha = str(pin.get("sha") or "")
assert re.fullmatch(r"[a-f0-9]{40}", sha)
assert pin.get("proofAuthority") is False
assert pin.get("publicationAuthority") is False
assert int(pin.get("providerRepairCount") or 0) == 0
assert (BRAIN / "src/niakvio_brain_llm/niakvio_adapter.py").is_file()

# The pin is provenance for the exact gitlink, not an independent moving truth.
gitlink = subprocess.check_output(
    ["git", "ls-files", "-s", "brain-llm"], cwd=ROOT, text=True
).split()[1]
assert sha == gitlink, f"Brain pin/gitlink drift: pin={sha} gitlink={gitlink}"

request = request_from_checkout(ROOT, "anime-sama")
assert request.failure_class == "media_extraction_gap", (
    "current exact-parent html_player evidence did not refine the Brain causal owner: "
    + str(request.failure_class)
)
native = [
    x.get("value") for x in request.observations
    if x.get("source") == "official-android-tv-emulator"
    and isinstance(x.get("value"), dict)
]
probes = [
    x.get("value") for x in request.observations
    if x.get("source") == "independent-catalogue-source-probe"
    and isinstance(x.get("value"), dict)
]
assert native, "no exact current-byte official TV parent"
assert probes, "no sanitized independent source probe reached the Brain adapter"

def exact_parent_match(probe: dict) -> bool:
    return any(
        str(parent.get("sourceRunId") or "") == str(probe.get("nativeParentRunId") or "")
        and str(parent.get("sourceNiakvioSha") or "") == str(probe.get("nativeParentSourceSha") or "")
        and str(parent.get("providerArtifactSha256") or "") == str(probe.get("currentProviderArtifactSha256") or "")
        and str(parent.get("fixture") or "") == str(probe.get("fixture") or "")
        and str(parent.get("manifestScope") or "") == str(probe.get("manifestScope") or "")
        for parent in native
    )

matched = [probe for probe in probes if exact_parent_match(probe)]
assert matched, "source probe history reached Brain but no probe matches its official exact-byte parent"

def run_number(probe: dict) -> int:
    value = str(probe.get("probeRunId") or "")
    return int(value) if value.isdigit() else -1

current = max(matched, key=run_number)
assert run_number(current) > 0
assert current.get("independentNetworkNotOfficialClient") is True
assert current.get("catalogueIdentityVerified") is False
assert current.get("episodeIdentityVerified") is False
assert current.get("sourceContractVerifiedOnOfficialTv") is False
for flag in (
    "proofAuthority", "publicationAuthority",
    "nativePlaybackAuthority", "providerMutationAuthority",
):
    assert current.get(flag) is False, f"{flag} leaked authority"

source_rows = [
    row for row in current.get("sourceObservations") or []
    if isinstance(row, dict)
]
inline = next((
    row for row in source_rows
    if row.get("seasonSourceShape") == "catalogue_inline_token_episode"
    and row.get("seasonPageStatus") == 200
    and row.get("inlineTokenSeasonObserved") is True
), None)
assert inline is not None, "current source contract did not reach Brain"

# Resolver/target fields are sanitized facts only. Their presence must survive
# the adapter whenever the current source probe observed them.
if int(current.get("tokenResolverProbeCount") or 0) > 0:
    assert inline.get("tokenResolverContract") == "same-origin-api-lien-j-l-v1"
    assert type(inline.get("tokenResolverJsonObjectObserved")) is bool
    assert type(inline.get("tokenResolverUrlFieldObserved")) is bool
    assert type(inline.get("tokenResolverHttpsUrlObserved")) is bool

allowed_target_shapes = {
    "hls_manifest", "dash_manifest", "media_binary",
    "html_player", "html_page", "json", "javascript", "text", "empty",
    "redirect", "http_error", "transport_error", "oversized",
}
if int(current.get("resolvedTargetProbeCount") or 0) > 0:
    assert inline.get("resolvedTargetShape") in allowed_target_shapes
    assert type(inline.get("resolvedTargetDirectMediaObserved")) is bool
    assert type(inline.get("resolvedTargetPlayerEmbedObserved")) is bool
    assert type(inline.get("resolvedTargetSameOrigin")) is bool
    assert type(inline.get("resolvedTargetRedirectObserved")) is bool
    structure_class = inline.get("resolvedTargetPlayerStructureClass")
    if structure_class is not None:
        assert structure_class in {
            "none", "iframe_shell", "video_tag", "scripted_player",
            "form_handoff", "packed_script", "request_bootstrap", "mixed",
        }
        for key, limit in {
            "resolvedTargetIframeCount": 8,
            "resolvedTargetVideoTagCount": 8,
            "resolvedTargetSourceTagCount": 16,
            "resolvedTargetExternalScriptCount": 16,
            "resolvedTargetInlineScriptCount": 16,
            "resolvedTargetFormCount": 8,
            "resolvedTargetHiddenInputCount": 32,
            "resolvedTargetRequestCallCount": 32,
            "resolvedTargetFetchCallCount": 32,
            "resolvedTargetXhrCallCount": 32,
            "resolvedTargetAxiosCallCount": 32,
            "resolvedTargetAjaxCallCount": 32,
            "resolvedTargetRequestLiteralUrlCount": 32,
            "resolvedTargetRequestDynamicUrlCount": 32,
            "resolvedTargetRequestTemplateUrlCount": 32,
            "resolvedTargetRequestConcatUrlCount": 32,
            "resolvedTargetRequestSameOriginLiteralCount": 32,
            "resolvedTargetRequestCrossOriginLiteralCount": 32,
        }.items():
            assert type(inline.get(key)) is int and 0 <= inline[key] <= limit, (key, inline.get(key))
        for key in (
            "resolvedTargetPostFormObserved",
            "resolvedTargetRequestBootstrapObserved",
            "resolvedTargetPackedScriptObserved",
            "resolvedTargetBase64DecodeObserved",
            "resolvedTargetMetaRefreshObserved",
        ):
            assert type(inline.get(key)) is bool, (key, inline.get(key))

body = json.dumps(probes, sort_keys=True)
for secret in (
    "rawHtml", "signedUrl", "bodyPreview", "access_token", "cookie=",
    "epsJeton", "/api/lien.php?j=", "m3u8?",
):
    assert secret not in body, f"unsafe source material leaked into Brain observations: {secret}"

request.advisor_only = True
causal_prior = build_causal_prior(request, [])
assert causal_prior.get("target_layer") == "provider", causal_prior
assert causal_prior.get("strategy_prior") == "proven_request_program_and_terminal_extraction", causal_prior
assert float(causal_prior.get("confidence") or 0) >= 0.95, causal_prior
prompt = build_prompt_payload(
    request,
    experiences=[],
    documents=[],
    causal_prior=causal_prior,
    mutation_policy={"allow_mutations": False, "allowed_scopes": []},
)
witness = prompt.get("source_contract_witness") or {}
assert witness, "Brain prompt lost the current source-contract witness"
assert str(witness.get("independentProbeRunId") or "") == str(current.get("probeRunId") or "")
assert str(witness.get("officialParentRunId") or "") == str(current.get("nativeParentRunId") or "")
assert witness.get("seasonHtmlShape") == "catalogue_inline_token_episode"
assert witness.get("sourceContractVerifiedOnOfficialTv") is False
assert witness.get("providerMutationAuthority") is False
assert witness.get("publicationAuthority") is False
assert witness.get("proofAuthority") is False

if int(current.get("tokenResolverProbeCount") or 0) > 0:
    assert witness.get("tokenResolverContract") == "same-origin-api-lien-j-l-v1"
if int(current.get("resolvedTargetProbeCount") or 0) > 0:
    assert witness.get("resolvedTargetShape") == inline.get("resolvedTargetShape")
    if inline.get("resolvedTargetPlayerStructureClass") is not None:
        assert witness.get("resolvedTargetPlayerStructureClass") == inline.get("resolvedTargetPlayerStructureClass")
        for key in (
            "resolvedTargetIframeCount", "resolvedTargetVideoTagCount",
            "resolvedTargetSourceTagCount", "resolvedTargetExternalScriptCount",
            "resolvedTargetInlineScriptCount", "resolvedTargetFormCount",
            "resolvedTargetHiddenInputCount", "resolvedTargetRequestCallCount",
            "resolvedTargetFetchCallCount", "resolvedTargetXhrCallCount",
            "resolvedTargetAxiosCallCount", "resolvedTargetAjaxCallCount",
            "resolvedTargetRequestLiteralUrlCount", "resolvedTargetRequestDynamicUrlCount",
            "resolvedTargetRequestTemplateUrlCount", "resolvedTargetRequestConcatUrlCount",
            "resolvedTargetRequestSameOriginLiteralCount", "resolvedTargetRequestCrossOriginLiteralCount",
            "resolvedTargetPostFormObserved",
            "resolvedTargetRequestBootstrapObserved", "resolvedTargetPackedScriptObserved",
            "resolvedTargetBase64DecodeObserved", "resolvedTargetMetaRefreshObserved",
        ):
            if key in inline:
                assert witness.get(key) == inline.get(key), (key, witness.get(key), inline.get(key))

print(
    "FIELD_BRAIN_CATALOGUE_ADAPTER_INTEGRATION "
    f"brain_sha={sha[:12]} provider=anime-sama "
    f"native_parents={len(native)} probe_history={len(probes)} "
    f"matched_probes={len(matched)} current_probe={current.get('probeRunId')} "
    f"failure_class={request.failure_class} "
    f"strategy_prior={causal_prior.get('strategy_prior')} "
    f"resolver={int(current.get('tokenResolverProbeCount') or 0)} "
    f"resolved_target={int(current.get('resolvedTargetProbeCount') or 0)} "
    f"target_shape={witness.get('resolvedTargetShape') or 'none'} "
    f"player_structure={witness.get('resolvedTargetPlayerStructureClass') or 'none'} "
    f"packed={str(witness.get('resolvedTargetPackedScriptObserved') is True).lower()} "
    f"bootstrap={str(witness.get('resolvedTargetRequestBootstrapObserved') is True).lower()} "
    "exact_parent=true independent_not_tv=true publication=false mutation=false "
    "terminal_playback=false"
)
