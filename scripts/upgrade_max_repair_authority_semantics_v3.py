#!/usr/bin/env python3
"""Align live authorities and semantic capabilities proven by max-repair diagnostics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    for pid in ("wookafr", "flemmix", "allwish", "coflix"):
        if not isinstance(patches.get(pid), dict):
            raise AssertionError(f"provider patch missing: {pid}")
    return value


def add_note(row: dict[str, Any], note: str) -> None:
    notes = [str(v) for v in row.get("notes") or []]
    if note not in notes:
        notes.append(note)
    row["notes"] = notes


def normalize_domains(row: dict[str, Any], target: str, old_hosts: list[str]) -> None:
    mapping = row.get("domain_substitutions")
    if not isinstance(mapping, dict):
        mapping = {}
    for host in old_hosts:
        if host != target:
            mapping[host] = target
    mapping.pop(target, None)
    row["domain_substitutions"] = mapping
    runtime = row.get("runtime_domain_replacements")
    if not isinstance(runtime, dict):
        runtime = {}
    for host in old_hosts:
        if host != target:
            runtime[host] = target
    runtime.pop(target, None)
    row["runtime_domain_replacements"] = runtime


def reset_stale_repair_contract(row: dict[str, Any], published: list[str], reason: str) -> None:
    row["published_types"] = list(published)
    disp = row.get("repair_disposition")
    if isinstance(disp, dict):
        disp["requiredLanes"] = list(published)
        # Existing historical proof cannot be retained for lanes whose semantic
        # contract has changed. Keep positive lanes only if still declared.
        for key in ("currentVerifiedLanes", "provenLanes", "exactLockedLanes"):
            vals = [str(v) for v in disp.get(key) or []]
            disp[key] = [v for v in vals if v in published]
        missing = [lane for lane in published if lane not in set(disp.get("provenLanes") or [])]
        disp["missingLanes"] = missing
        disp["completeCapabilityProof"] = not missing
        if missing:
            disp["recoveryStatus"] = "repair"
        codes = [str(v) for v in disp.get("reasonCodes") or [] if str(v)]
        if reason not in codes:
            codes.append(reason)
        disp["reasonCodes"] = codes
        row["repair_disposition"] = disp


def patch() -> bool:
    value = load()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    patches = value["provider_patches"]

    wooka = patches["wookafr"]
    wooka["official_site"] = "https://wookafr.boston"
    wooka["known_site"] = "https://wookafr.boston"
    normalize_domains(wooka, "wookafr.boston", ["wookafr.blog", "wookafr.center", "wookafr.boston"])
    add_note(wooka, "Authority refresh 2026-09-16: wookafr.blog is DNS-dead; wookafr.center redirects to the live wookafr.boston authority. Runtime substitutions must therefore converge on .boston, never rewrite .boston back to .blog.")

    flemmix = patches["flemmix"]
    flemmix["official_site"] = "https://flemmix.me"
    flemmix["known_site"] = "https://flemmix.me"
    normalize_domains(flemmix, "flemmix.me", ["flemmix.cloud", "flemmix.vip", "flemmix.ws", "flemmix.me"])
    add_note(flemmix, "Authority refresh 2026-09-16: the current typed JSON search and signed /embed/video contract are live on flemmix.me; current .me URLs must not be rewritten to the historical .cloud authority.")

    allwish = patches["allwish"]
    reset_stale_repair_contract(allwish, ["anime"], "semantic_contract_corrected_to_current_anime_only_site")
    allwish["capability"] = "mixed_embed_resolver"
    allwish["preserve_embed_urls"] = True
    add_note(allwish, "Semantic correction 2026-09-16: the current AllWish service is an anime catalogue; historical movie/tv semantic lanes are removed. TV remains transport compatibility for anime through the shared semantic layer, not a generic TV capability.")

    coflix = patches["coflix"]
    reset_stale_repair_contract(coflix, ["movie", "tv"], "anime_lane_removed_no_current_catalogue_evidence")
    add_note(coflix, "Semantic correction 2026-09-16: current Coflix routes redirect to the live service but repeated anime/search probes expose no anime catalogue. Anime is removed rather than manufactured; movie/tv remain declared and require their own playback proof.")

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    p = load()["provider_patches"]
    if p["wookafr"].get("official_site") != "https://wookafr.boston":
        raise AssertionError("Wooka live authority mismatch")
    if (p["wookafr"].get("domain_substitutions") or {}).get("wookafr.boston"):
        raise AssertionError("Wooka live authority is still rewritten away")
    if p["flemmix"].get("official_site") != "https://flemmix.me":
        raise AssertionError("Flemmix live authority mismatch")
    if (p["flemmix"].get("domain_substitutions") or {}).get("flemmix.me"):
        raise AssertionError("Flemmix live authority is still rewritten away")
    if set(p["allwish"].get("published_types") or []) != {"anime"}:
        raise AssertionError("AllWish must be anime-only semantically")
    if set(p["coflix"].get("published_types") or []) != {"movie", "tv"}:
        raise AssertionError("Coflix anime lane not removed cleanly")


def main() -> int:
    changed = patch()
    validate()
    print("MAX_REPAIR_AUTHORITY_SEMANTICS_V3_OK changed=" + str(changed).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())