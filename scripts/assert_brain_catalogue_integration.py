#!/usr/bin/env python3
"""End-to-end read-only test of pinned Brain's actual NiakVIO source memories.

No provider generation, stream extraction, network access or playback claims.
Run against the NiakVIO tree and external Brain SHA pinned by this checkout.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAIN = ROOT / "brain-replay"
sys.path.insert(0, str(BRAIN / "src"))

from niakvio_brain_llm.niakvio_adapter import request_from_checkout  # noqa:E402

pin = json.loads((ROOT / "automation/brain-pinned-source.json").read_text("utf-8"))
sha = str(pin.get("sha") or "")
assert re.fullmatch(r"[a-f0-9]{40}", sha)
assert (BRAIN / "src/niakvio_brain_llm/niakvio_adapter.py").is_file()

request = request_from_checkout(ROOT, "anime-sama")
native = [
    x.get("value") for x in request.observations
    if x.get("source") == "official-android-tv-emulator"
]
probes = [
    x.get("value") for x in request.observations
    if x.get("source") == "independent-catalogue-source-probe"
]
assert len(native) >= 1, "no exact current-byte official TV parent"
assert len(probes) == 2, "source probe history lost or not source-pinned"
assert [v.get("probeRunId") for v in probes] == [
    "44798438960", "44797871788",
], probes
current = probes[0]
assert current["inlineTokenResponseCount"] == 1
assert current["catalogueSlugUnverified"] == "mushoku-tensei"
assert any(
    v.get("originHost") == "anime-sama.to"
    and v.get("seasonSourceShape") == "catalogue_inline_token_episode"
    and v.get("seasonPageStatus") == 200
    and v.get("inlineTokenSeasonObserved") is True
    for v in current["sourceObservations"]
), "inline token observation not passed to Brain"
assert current["currentProviderArtifactSha256"] == native[0]["providerArtifactSha256"]
assert current["nativeParentRunId"] == native[0]["sourceRunId"]
assert current["nativeParentSourceSha"] == native[0]["sourceNiakvioSha"]
assert current["independentNetworkNotOfficialClient"] is True
assert all(
    v.get(flag) is False
    for v in probes
    for flag in (
        "proofAuthority", "publicationAuthority",
        "nativePlaybackAuthority", "providerMutationAuthority",
        "catalogueIdentityVerified", "episodeIdentityVerified",
        "sourceContractVerifiedOnOfficialTv",
    )
)
# Neither HTTP success nor independent GitHub source token detection confers
# current NuvioTV reader/identity or provider mutation authority.
body = json.dumps(probes)
for secret in ("rawHtml", "signedUrl", "bodyPreview", "access_token", "cookie="):
    assert secret not in body
assert request.advisor_only is False  # caller decides whether to run advisory
request.advisor_only = True
from niakvio_brain_llm.prompting import build_prompt_payload  # noqa:E402
prompt = build_prompt_payload(
    request, experiences=[], documents=[],
    causal_prior={"confidence": 0.91, "target_layer": "unknown",
                  "strategy_prior": "source-contract-diagnose"},
    mutation_policy={"allow_mutations": False, "allowed_scopes": []},
)
prompt_observations = prompt.get("request", {}).get("observations") or []
witness = prompt.get("source_contract_witness") or {}
has_causal_source = (
    witness.get("seasonHtmlShape") == "catalogue_inline_token_episode"
    and witness.get("officialParentRunId") == "44781039914"
    and witness.get("independentProbeRunId") == "44798438960"
    and witness.get("catalogueSlugUnverified") == "mushoku-tensei"
    and witness.get("sourceContractVerifiedOnOfficialTv") is False
    and witness.get("providerMutationAuthority") is False
)
print(
    "FIELD_BRAIN_CATALOGUE_PROMPT_WITNESS "
    f"prompt_observations={len(prompt_observations)} "
    f"source_visible={str(has_causal_source).lower()} "
    f"witness_present={str(bool(witness)).lower()} "
    f"chars={prompt.get('context_budget', {}).get('serialized_user_chars')} "
    "authority=false",
    flush=True,
)
assert has_causal_source, "Brain LLM prompt lost the attested inline source contract witness"
print(
    "FIELD_BRAIN_CATALOGUE_ADAPTER_INTEGRATION "
    f"brain_sha={sha[:12]} provider=anime-sama native_parents={len(native)} "
    f"probe_history={len(probes)} inline_probe={current['inlineTokenResponseCount']} "
    "byte_matched=true independent_not_tv=true publication=false mutation=false "
    "terminal_playback=false"
)
