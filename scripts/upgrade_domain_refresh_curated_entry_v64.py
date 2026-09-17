#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old[:120]!r}")
    if text.count(old) != 1:
        raise SystemExit(f"non-unique patch anchor in {path}: count={text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


resolver = ROOT / "scripts" / "resolve_provider_hubs.py"
replace_once(
    resolver,
    '''def has_authoritative_direct_source(cfg: dict[str, Any]) -> bool:\n    \"\"\"Explicit registry direct URLs supersede history/search when no hub exists.\"\"\"\n    if has_authoritative_hub_source(cfg):\n        return False\n    if is_http_url(cfg.get(\"direct_fallback\")):\n        return True\n    return any(is_http_url(url) for url in (cfg.get(\"direct_candidates\") or []))\n\n\ndef has_authoritative_route_source(cfg: dict[str, Any]) -> bool:\n    return has_authoritative_hub_source(cfg) or has_authoritative_direct_source(cfg)\n''',
    '''def has_authoritative_curated_entry_source(cfg: dict[str, Any]) -> bool:\n    \"\"\"Return True for a curated provider entry URL when no hub exists.\n\n    These URLs are *entry authorities*, not immutable terminal domains: an HTTP\n    redirect is expected to rotate the provider to its current terminal host.\n    \"\"\"\n    if has_authoritative_hub_source(cfg):\n        return False\n    if is_http_url(cfg.get(\"direct_fallback\")):\n        return True\n    return any(is_http_url(url) for url in (cfg.get(\"direct_candidates\") or []))\n\n\ndef has_authoritative_direct_source(cfg: dict[str, Any]) -> bool:\n    \"\"\"Backward-compatible alias for curated entry authority.\"\"\"\n    return has_authoritative_curated_entry_source(cfg)\n\n\ndef has_authoritative_route_source(cfg: dict[str, Any]) -> bool:\n    return has_authoritative_hub_source(cfg) or has_authoritative_curated_entry_source(cfg)\n''',
)
replace_once(
    resolver,
    '''    if (not has_authoritative_direct_source(cfg)) and isinstance(current, dict) and is_http_url(current.get(\"url\")):\n''',
    '''    if (not has_authoritative_curated_entry_source(cfg)) and isinstance(current, dict) and is_http_url(current.get(\"url\")):\n''',
)

refresh = ROOT / "scripts" / "refresh_authoritative_hub_domains.py"
insert_marker = '''\n\n\ndef _domain_host(value: str) -> str:\n'''
insert = '''\n\n\ndef resolve_authoritative_curated_entry_domain(\n    provider_id: str,\n    cfg: dict[str, Any],\n    history_row: dict[str, Any],\n    mode: str,\n    timeout: float,\n) -> dict[str, Any]:\n    \"\"\"Follow a curated provider entry URL to its current terminal.\n\n    Unlike hub discovery, the curated entry itself is a provider route and may\n    legitimately redirect as the site rotates domains. The final URL is promoted\n    only after the normal terminal safety + same-brand validation succeeds.\n    \"\"\"\n    item: dict[str, Any] = {\n        \"provider_id\": provider_id,\n        \"status\": \"hub_unresolved\",\n        \"terminal_probe_skipped\": False,\n        \"authority_kind\": \"curated_entry\",\n    }\n    if hubresolver.has_authoritative_hub_source(cfg):\n        return resolve_authoritative_hub_domain(provider_id, cfg, history_row, mode, timeout)\n    if not hubresolver.has_authoritative_curated_entry_source(cfg):\n        item[\"status\"] = \"not_applicable\"\n        item[\"reason\"] = \"no_authoritative_route_source\"\n        return item\n\n    candidates = hubresolver._seed_known_candidates(cfg, history_row)\n    validations: list[dict[str, Any]] = []\n    for row in candidates:\n        candidate = _candidate_url(row)\n        if not candidate:\n            continue\n        validation = hubresolver.validate_terminal(provider_id, cfg, candidate, timeout)\n        observed = dict(validation)\n        observed[\"source_type\"] = row.get(\"source_type\")\n        observed[\"source\"] = row.get(\"source\")\n        observed[\"candidate_score\"] = row.get(\"score\")\n        validations.append(observed)\n        if not validation.get(\"ok\"):\n            continue\n        terminal = str(validation.get(\"final_url\") or candidate).strip().rstrip(\"/\")\n        if not terminal or not hubresolver.is_provider_terminal_site_url(terminal):\n            continue\n        item.update({\n            \"status\": \"site_authoritative\",\n            \"reason\": \"curated_entry_redirect_terminal_validated\",\n            \"official_site\": terminal,\n            \"site_final_url\": terminal,\n            \"selected_source_type\": row.get(\"source_type\") or \"curated_direct\",\n            \"selected_source\": row.get(\"source\") or \"provider-hubs.json\",\n            \"candidate_score\": row.get(\"score\"),\n            \"terminal_probe_skipped\": False,\n            \"site_validations\": validations,\n            \"sources\": [],\n            \"api_candidates\": [],\n            \"api_probes\": [],\n            \"validated_api\": None,\n        })\n        return item\n\n    item[\"reason\"] = \"curated_entry_no_safe_terminal_candidate\"\n    item[\"site_validations\"] = validations\n    item[\"sources\"] = []\n    return item\n\n\ndef resolve_authoritative_route_domain(\n    provider_id: str,\n    cfg: dict[str, Any],\n    history_row: dict[str, Any],\n    mode: str,\n    timeout: float,\n) -> dict[str, Any]:\n    \"\"\"Resolve either a discovery hub or a redirect-following curated entry.\"\"\"\n    if hubresolver.has_authoritative_hub_source(cfg):\n        item = resolve_authoritative_hub_domain(provider_id, cfg, history_row, mode, timeout)\n        item.setdefault(\"authority_kind\", \"hub\")\n        return item\n    return resolve_authoritative_curated_entry_domain(provider_id, cfg, history_row, mode, timeout)\n'''
replace_once(refresh, insert_marker, insert + insert_marker)

transaction = ROOT / "scripts" / "domain_refresh_transaction_v2.py"
replace_once(
    transaction,
    '''        if not resolver.has_authoritative_hub_source(cfg):\n            continue\n''',
    '''        if not resolver.has_authoritative_route_source(cfg):\n            continue\n''',
)
replace_once(
    transaction,
    '''                refresh.resolve_authoritative_hub_domain,\n''',
    '''                refresh.resolve_authoritative_route_domain,\n''',
)
replace_once(
    transaction,
    '''        \"authority\": \"provider-hubs-authoritative-terminal\",\n        \"terminal_validation_required\": False,\n''',
    '''        \"authority\": \"provider-route-authoritative-terminal\",\n        \"terminal_validation_required\": False,\n        \"source_validation_policy\": \"hub=discovery-only; curated_entry=follow-redirect-and-validate\",\n''',
)

# Keep the legacy resolver unit test but make the intended terminology explicit.
test = ROOT / "tests" / "provider_hub_registry_test.py"
replace_once(
    test,
    '''assert resolver.has_authoritative_direct_source(direct_authority_cfg)\n''',
    '''assert resolver.has_authoritative_curated_entry_source(direct_authority_cfg)\nassert resolver.has_authoritative_direct_source(direct_authority_cfg)  # compatibility alias\n''',
)
replace_once(
    test,
    '''assert resolver.has_authoritative_direct_source(fallback_authority_cfg)\n''',
    '''assert resolver.has_authoritative_curated_entry_source(fallback_authority_cfg)\nassert resolver.has_authoritative_direct_source(fallback_authority_cfg)  # compatibility alias\n''',
)

new_test = ROOT / "tests" / "domain_refresh_curated_entry_redirect_test.py"
new_test.write_text('''import importlib.util\nimport sys\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\n\nimport resolve_provider_hubs as resolver\nimport refresh_authoritative_hub_domains as refresh\n\n\ndef main():\n    cfg = {\n        "hub": None,\n        "sources": [],\n        "aliases": ["moviesmod"],\n        "direct_candidates": ["https://moviesmod.zone/"],\n        "direct_fallback": "https://moviesmod.zone/",\n        "allowed_terminal_hosts": ["moviesmod.zone"],\n    }\n    assert resolver.has_authoritative_curated_entry_source(cfg)\n    assert not resolver.has_authoritative_hub_source(cfg)\n\n    original = resolver.validate_terminal\n    try:\n        resolver.validate_terminal = lambda provider_id, _cfg, candidate, timeout: {\n            "url": candidate,\n            "final_url": "https://moviesmod.ai.in",\n            "status": 200,\n            "ok": True,\n            "content_type": "text/html",\n            "safe_site_url": True,\n            "safe_content_type": True,\n            "attachment": False,\n            "brand_match": True,\n        }\n        item = refresh.resolve_authoritative_route_domain("moviesmod", cfg, {}, "quick", 2.0)\n    finally:\n        resolver.validate_terminal = original\n\n    assert item["status"] == "site_authoritative", item\n    assert item["official_site"] == "https://moviesmod.ai.in", item\n    assert item["authority_kind"] == "curated_entry", item\n    assert item["terminal_probe_skipped"] is False, item\n    assert item["reason"] == "curated_entry_redirect_terminal_validated", item\n    assert item["selected_source_type"] == "curated_direct", item\n    print("DOMAIN_REFRESH_CURATED_ENTRY_REDIRECT_OK")\n\n\nif __name__ == "__main__":\n    main()\n''', encoding="utf-8")

print("UPGRADE_DOMAIN_REFRESH_CURATED_ENTRY_V64_OK")
