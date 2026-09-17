import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import resolve_provider_hubs as resolver
import refresh_authoritative_hub_domains as refresh


def main():
    cfg = {
        "hub": None,
        "sources": [],
        "aliases": ["moviesmod"],
        "direct_candidates": ["https://moviesmod.zone/"],
        "direct_fallback": "https://moviesmod.zone/",
        "allowed_terminal_hosts": ["moviesmod.zone"],
    }
    assert resolver.has_authoritative_curated_entry_source(cfg)
    assert not resolver.has_authoritative_hub_source(cfg)

    original = resolver.validate_terminal
    try:
        resolver.validate_terminal = lambda provider_id, _cfg, candidate, timeout: {
            "url": candidate,
            "final_url": "https://moviesmod.ai.in",
            "status": 200,
            "ok": True,
            "content_type": "text/html",
            "safe_site_url": True,
            "safe_content_type": True,
            "attachment": False,
            "brand_match": True,
        }
        item = refresh.resolve_authoritative_route_domain("moviesmod", cfg, {}, "quick", 2.0)
    finally:
        resolver.validate_terminal = original

    assert item["status"] == "site_authoritative", item
    assert item["official_site"] == "https://moviesmod.ai.in", item
    assert item["authority_kind"] == "curated_entry", item
    assert item["terminal_probe_skipped"] is False, item
    assert item["reason"] == "curated_entry_redirect_terminal_validated", item
    assert item["selected_source_type"] == "curated_direct", item
    print("DOMAIN_REFRESH_CURATED_ENTRY_REDIRECT_OK")


if __name__ == "__main__":
    main()
