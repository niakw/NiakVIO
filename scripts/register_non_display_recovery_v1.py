#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
PROVIDERS = {
    "animesama-co": "https://animesama.co",
    "animevostfr": "https://v2.animevostfr.org",
    "coflix": "https://coflix.wiki",
    "neko-sama": "https://animes-sama.su",
    "sekai": "https://sekai.one",
    "voiranime-rip": "https://voiranime.rip",
}
V1_LEGOS = {
    "animesama-co": "scripts/provider_patches/animesamaco_nondisplay_recovery_v1.py",
    "animevostfr": "scripts/provider_patches/animevostfr_nondisplay_recovery_v1.py",
    "coflix": "scripts/provider_patches/coflix_nondisplay_recovery_v1.py",
    "neko-sama": "scripts/provider_patches/neko_sama_nondisplay_recovery_v1.py",
    "sekai": "scripts/provider_patches/sekai_nondisplay_recovery_v1.py",
    "voiranime-rip": "scripts/provider_patches/voiranime_rip_nondisplay_recovery_v1.py",
}
V2_LEGOS = {
    "animesama-co": "scripts/provider_patches/animesamaco_nondisplay_recovery_v2.py",
    "neko-sama": "scripts/provider_patches/neko_sama_nondisplay_recovery_v2.py",
    "sekai": "scripts/provider_patches/sekai_nondisplay_recovery_v2.py",
    "voiranime-rip": "scripts/provider_patches/voiranime_rip_nondisplay_recovery_v2.py",
}
V3_SECURITY_LEGOS = {
    "animesama-co": "scripts/provider_patches/animesamaco_nondisplay_security_v3.py",
    "animevostfr": "scripts/provider_patches/animevostfr_nondisplay_security_v3.py",
    "coflix": "scripts/provider_patches/coflix_nondisplay_security_v3.py",
    "neko-sama": "scripts/provider_patches/neko_sama_nondisplay_security_v3.py",
    "sekai": "scripts/provider_patches/sekai_nondisplay_security_v3.py",
    "voiranime-rip": "scripts/provider_patches/voiranime_rip_nondisplay_security_v3.py",
}
LEGACY_SHARED = {
    "scripts/provider_patches/non_display_recovery_runtime_v1.py",
    "scripts/provider_patches/non_display_recovery_entry_v1.py",
}
RETIRED_LEGOS = {
    "scripts/provider_patches/coflix_livavid_origin_v2.py",
}


def _wanted(provider: str, base: str) -> dict[str, object]:
    return {"provider": provider, "base": base, "max_streams": 4}


def apply_document(doc: dict[str, Any]) -> list[str]:
    patches = doc.setdefault("provider_patches", {})
    changed: list[str] = []
    for provider, base in PROVIDERS.items():
        row = patches.get(provider)
        if not isinstance(row, dict):
            raise ValueError(f"missing provider patch row: {provider}")
        scripts = row.setdefault("provider_lego_scripts", [])
        before_scripts = list(scripts)
        scripts[:] = [x for x in scripts if x not in LEGACY_SHARED and x not in RETIRED_LEGOS]
        v1 = V1_LEGOS[provider]
        if v1 not in scripts:
            scripts.append(v1)
        v2 = V2_LEGOS.get(provider)
        if v2:
            scripts[:] = [x for x in scripts if x != v2]
            scripts.append(v2)
        # Security V3 must be the final provider-owned Lego: it hardens the V1
        # visible-text primitive after any V2 route resolver has been composed.
        v3 = V3_SECURITY_LEGOS[provider]
        scripts[:] = [x for x in scripts if x != v3]
        scripts.append(v3)
        if scripts != before_scripts:
            changed.append(provider)

        options = row.setdefault("provider_lego_options", {})
        for old in LEGACY_SHARED | RETIRED_LEGOS:
            options.pop(old, None)
        wanted = _wanted(provider, base)
        if options.get(v1) != wanted:
            options[v1] = wanted
            if provider not in changed:
                changed.append(provider)
        if v2 and options.get(v2) != wanted:
            options[v2] = wanted
            if provider not in changed:
                changed.append(provider)
        if options.get(v3) != {}:
            options[v3] = {}
            if provider not in changed:
                changed.append(provider)

    coflix = patches["coflix"]
    if coflix.get("official_site") != "https://coflix.wiki":
        coflix["official_site"] = "https://coflix.wiki"
        if "coflix" not in changed:
            changed.append("coflix")
    for key in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = coflix.get(key)
        if not isinstance(mapping, dict):
            continue
        before = dict(mapping)
        mapping.pop("coflix.wiki", None)
        for host in list(mapping):
            if host.startswith("coflix.") and host != "coflix.wiki":
                mapping[host] = "coflix.wiki"
        if mapping != before and "coflix" not in changed:
            changed.append("coflix")

    sekai = patches["sekai"]
    if sekai.get("official_site") != "https://sekai.one":
        sekai["official_site"] = "https://sekai.one"
        if "sekai" not in changed:
            changed.append("sekai")
    return changed


def validate_document(doc: dict[str, Any]) -> None:
    patches = doc.get("provider_patches") or {}
    for provider, base in PROVIDERS.items():
        row = patches.get(provider)
        if not isinstance(row, dict):
            raise AssertionError(provider)
        scripts = row.get("provider_lego_scripts") or []
        v1 = V1_LEGOS[provider]
        if v1 not in scripts:
            raise AssertionError(f"{provider}: recovery V1 Lego missing")
        if any(old in scripts for old in LEGACY_SHARED | RETIRED_LEGOS):
            raise AssertionError(f"{provider}: retired/legacy recovery Lego still registered")
        options = row.get("provider_lego_options") or {}
        if any(old in options for old in RETIRED_LEGOS):
            raise AssertionError(f"{provider}: retired recovery options still registered")
        if options.get(v1) != _wanted(provider, base):
            raise AssertionError(f"{provider}: recovery V1 options drift")
        v2 = V2_LEGOS.get(provider)
        if v2:
            if v2 not in scripts:
                raise AssertionError(f"{provider}: recovery V2 Lego missing")
            if options.get(v2) != _wanted(provider, base):
                raise AssertionError(f"{provider}: recovery V2 options drift")
        v3 = V3_SECURITY_LEGOS[provider]
        if v3 not in scripts:
            raise AssertionError(f"{provider}: recovery security V3 Lego missing")
        if scripts[-1] != v3:
            raise AssertionError(f"{provider}: recovery security V3 must be last provider Lego")
        if options.get(v3) != {}:
            raise AssertionError(f"{provider}: recovery security V3 options drift")
    coflix = patches["coflix"]
    if coflix.get("official_site") != "https://coflix.wiki":
        raise AssertionError("coflix current authority drift")
    for key in ("domain_substitutions", "replacements", "runtime_domain_replacements"):
        mapping = coflix.get(key)
        if isinstance(mapping, dict) and mapping.get("coflix.wiki") not in (None, "coflix.wiki"):
            raise AssertionError(f"coflix.wiki stale rewrite remains in {key}")
    if patches["sekai"].get("official_site") != "https://sekai.one":
        raise AssertionError("sekai current authority drift")


def main() -> None:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(doc)
    validate_document(doc)
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("NON_DISPLAY_RECOVERY_REGISTERED providers=" + ",".join(sorted(PROVIDERS)) + " changed=" + ",".join(sorted(changed)))


if __name__ == "__main__":
    main()
