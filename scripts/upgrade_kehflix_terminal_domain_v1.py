#!/usr/bin/env python3
"""Keep Kehflix structured DATA aligned with the current address authority.

The historical September-14 live proof observed kehflix.wiki as a playable
runtime terminal, but the later September-18 provider registry explicitly
promoted kehflix.com as the current runtime terminal while keeping
kehflix.wiki as the authoritative address hub. Reconstruction migrations must
follow that newer registry authority and must not overwrite it with the older
observation.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
TERMINAL = "https://kehflix.com"
HUB = "https://kehflix.wiki"
OLD = "kehflix.lol"
NEW = "kehflix.com"
HUB_HOST = "kehflix.wiki"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonicalize_mapping(raw: object) -> dict[str, str]:
    mapping = dict(raw) if isinstance(raw, dict) else {}
    # The current explicit authority is hub(.wiki) -> runtime(.com).
    # Redirect-only .lol must also converge to the runtime terminal.
    mapping.pop(NEW, None)
    mapping[OLD] = NEW
    mapping[HUB_HOST] = NEW
    return dict(sorted((str(k), str(v)) for k, v in mapping.items() if str(k).strip() and str(v).strip()))


def patch_overrides(value: dict) -> bool:
    patches = value.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("kehflix"), dict):
        raise AssertionError("provider_patches.kehflix missing")
    patch = patches["kehflix"]
    before = json.dumps(patch, ensure_ascii=False, sort_keys=True)
    patch["official_site"] = TERMINAL
    patch["official_hub"] = HUB + "/"
    patch["domain_substitutions"] = canonicalize_mapping(patch.get("domain_substitutions"))
    patch["runtime_domain_replacements"] = canonicalize_mapping(patch.get("runtime_domain_replacements"))
    # terminal_domain_proof is historical observation evidence. Do not rewrite
    # it merely to match the newer address-authority decision.
    return before != json.dumps(patch, ensure_ascii=False, sort_keys=True)


def patch_knowledge(value: dict) -> bool:
    providers = value.get("providers")
    if not isinstance(providers, dict) or not isinstance(providers.get("kehflix"), dict):
        raise AssertionError("static knowledge kehflix row missing")
    row = providers["kehflix"]
    model = row.get("model")
    if not isinstance(model, dict):
        raise AssertionError("static knowledge kehflix.model missing")
    before = json.dumps(model, ensure_ascii=False, sort_keys=True)
    model["officialSite"] = TERMINAL
    model["knownSite"] = TERMINAL
    model["officialHub"] = HUB + "/"
    model["domainSubstitutions"] = canonicalize_mapping(model.get("domainSubstitutions"))
    origins = [str(v).rstrip("/") for v in model.get("origins") or [] if str(v).strip()]
    model["origins"] = list(dict.fromkeys([TERMINAL, HUB, *origins]))
    observed = [str(v) for v in model.get("observedUrls") or [] if str(v).strip()]
    model["observedUrls"] = list(dict.fromkeys([TERMINAL + "/", HUB + "/", *observed]))
    return before != json.dumps(model, ensure_ascii=False, sort_keys=True)


def validate(overrides: dict, knowledge: dict) -> None:
    patch = overrides["provider_patches"]["kehflix"]
    model = knowledge["providers"]["kehflix"]["model"]
    substitutions = patch.get("domain_substitutions") or {}
    replacements = patch.get("runtime_domain_replacements") or {}
    model_substitutions = model.get("domainSubstitutions") or {}
    assert patch.get("official_site") == TERMINAL
    assert patch.get("official_hub") == HUB + "/"
    assert substitutions.get(OLD) == NEW
    assert substitutions.get(HUB_HOST) == NEW
    assert NEW not in substitutions
    assert replacements.get(OLD) == NEW
    assert replacements.get(HUB_HOST) == NEW
    assert NEW not in replacements
    assert model.get("officialSite") == TERMINAL
    assert model.get("knownSite") == TERMINAL
    assert model.get("officialHub") == HUB + "/"
    assert model_substitutions.get(OLD) == NEW
    assert model_substitutions.get(HUB_HOST) == NEW
    assert NEW not in model_substitutions
    assert "/title/tv/{id}-{slug}" in (model.get("routes") or []), model.get("routes")
    assert "/api/streams/episode?id&season&episode&k" in (model.get("routes") or []), model.get("routes")


def main() -> int:
    overrides = load(OVERRIDES)
    knowledge = load(KNOWLEDGE)
    changed_o = patch_overrides(overrides)
    changed_k = patch_knowledge(knowledge)
    validate(overrides, knowledge)
    if changed_o:
        write(OVERRIDES, overrides)
    if changed_k:
        write(KNOWLEDGE, knowledge)
    print(
        "KEHFLIX_TERMINAL_DOMAIN_V1_OK "
        f"changed={str(changed_o or changed_k).lower()} terminal={NEW} hub={HUB_HOST} old_redirect={OLD}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
