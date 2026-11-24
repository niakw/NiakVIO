#!/usr/bin/env python3
"""Read-only generic contract oracle: external episodes.js versus inline token episodes."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Installed Brain parser modules are imported only by a compiler-owned hook.
SCRIPTS_ROOT = str(Path(__file__).resolve().parents[1])
if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)

MAX_BODY_CHARS = 1_048_576
SCRIPTS = re.compile(r"<script\b[^>]*>([\s\S]*?)</script\s*>", re.I)
SLOT = re.compile(r"\b(?:var|let|const)\s+eps\d+\s*=\s*\[")
LINK = re.compile(r"""["']lien:[a-zA-Z0-9_.:-]{1,200}["']""")
JETON = re.compile(r"\b(?:var|let|const)\s+epsJeton\s*=")
META = re.compile(r"\b(?:var|let|const)\s+epsMeta\s*=")
READERS = re.compile(r"\b(?:var|let|const)\s+lecteursInfos\s*=")
LANGS = re.compile(r"\b(?:var|let|const)\s+languesDispo\s*=")
DIRECT = re.compile(r"""["']https?://[^"' ]{4,2048}["']""", re.I)
HTML = re.compile(r"^\s*(?:<!doctype\s+html\b|<html\b)", re.I)


def classify(status: int, body: str) -> dict:
    """No raw source content, token, URL, hostname or player evidence survives."""
    if type(status) is not int or not 0 <= status <= 599:
        raise ValueError("invalid status")
    if not isinstance(body, str) or len(body) > MAX_BODY_CHARS:
        raise ValueError("invalid or oversized body")
    html = bool(HTML.search(body))
    text = "\n".join(SCRIPTS.findall(body)) if html else body
    slot, link, jeton = bool(SLOT.search(text)), bool(LINK.search(text)), bool(JETON.search(text))
    if status in {404, 410}:
        shape = "script_http_missing"
    elif 200 <= status < 300 and html and slot and link and jeton:
        shape = "catalogue_inline_token_episode"
    elif 200 <= status < 300 and not html and slot and DIRECT.search(text) and not link:
        shape = "legacy_external_episode_javascript"
    elif 200 <= status < 300 and html:
        shape = "script_html_2xx"
    else:
        shape = "unknown_response_shape"
    return {
        "schemaVersion": 1,
        "source": "read-only-catalogue-episode-shape-oracle",
        "shape": shape,
        "httpStatusClass": "2xx" if 200 <= status < 300 else "4xx" if 400 <= status < 500 else "5xx" if 500 <= status <= 599 else "other",
        "inlineSlotArrayObserved": slot,
        "opaqueLinkTokenObserved": link,
        "jetonDeclarationObserved": jeton,
        "episodeMetadataDeclarationObserved": bool(META.search(text)),
        "readerMapDeclarationObserved": bool(READERS.search(text)),
        "languageListDeclarationObserved": bool(LANGS.search(text)),
        "legacyMediaUrlArrayObserved": bool(DIRECT.search(text)),
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }


def current_family(root: Path, provider: str) -> dict:
    provider = str(provider or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", provider):
        raise ValueError("invalid provider")
    root = root.resolve()
    patches = json.loads((root / "provider-overrides.json").read_text("utf-8")).get("provider_patches") or {}
    patch = patches.get(provider) or {}
    routes = [str(x) for x in patch.get("learned_routes") or [] if isinstance(x, str)]
    supports_tokens = False
    for name in (patch.get("provider_lego_scripts") or [])[:16]:
        if not isinstance(name, str) or not name.startswith("scripts/provider_patches/"):
            continue
        file = (root / name).resolve()
        try:
            file.relative_to(root)
        except ValueError:
            continue
        if file.is_file():
            code = file.read_text("utf-8")
            if "epsJeton" in code and "/api/lien.php" in code:
                supports_tokens = True
                break
    return {
        "schemaVersion": 1,
        "provider": provider,
        "declaredLegacyEpisodeScriptRoutes": min(100, sum("/episodes.js" in route for route in routes)),
        "inlineTokenLegoPresent": supports_tokens,
        "currentSiteContractVerified": False,
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }


def discriminate(shape: dict, family: dict) -> dict:
    possible = (
        shape.get("shape") == "catalogue_inline_token_episode"
        and int(family.get("declaredLegacyEpisodeScriptRoutes") or 0) > 0
        and family.get("inlineTokenLegoPresent") is False
    )
    return {
        "schemaVersion": 1,
        "diagnosticFamily": "catalogue_inline_token_contract_drift_candidate" if possible else "catalogue_source_contract_unresolved",
        "requiresIndependentSourceAndEpisodeEvidence": True,
        "requiresOfficialClientReplay": True,
        "candidateMutationAllowed": False,
        "proofAuthority": False,
        "publicationAuthority": False,
        "nativePlaybackAuthority": False,
        "providerMutationAuthority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--status", type=int, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--provider")
    args = parser.parse_args()
    result = classify(args.status, args.body_file.read_text("utf-8"))
    if args.source_root or args.provider:
        if not (args.source_root and args.provider):
            raise SystemExit("both source root and provider required")
        result["familyDiscriminator"] = discriminate(
            result, current_family(args.source_root, args.provider)
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
