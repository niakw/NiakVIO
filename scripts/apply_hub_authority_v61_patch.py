#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str, marker: str | None = None) -> None:
    text = read(path)
    if marker and marker in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"V61 patch anchor {path}: expected=1 observed={count}")
    write(path, text.replace(old, new, 1))


def patch_resolver() -> None:
    replace_once(
        "scripts/resolve_provider_hubs.py",
        '''    fallback = str(cfg.get("direct_fallback") or "").strip().rstrip("/")
    if fallback and host(fallback) != host(hub_url):
        candidates.append({"url": fallback, "label": "curated direct fallback", "score": 70, "document_index": -1, "fallback": True})
    _sort_official_candidates(candidates, resolver)
''',
        '''    fallback = str(cfg.get("direct_fallback") or "").strip().rstrip("/")
    # HUB_AUTHORITY_STRICT_V61: an authoritative hub candidate always outranks
    # stale direct/LKG data. The fallback exists only when the hub exposes no
    # valid terminal at all.
    if not candidates and fallback and host(fallback) != host(hub_url):
        candidates.append({"url": fallback, "label": "curated direct fallback", "score": 70, "document_index": -1, "fallback": True})
    _sort_official_candidates(candidates, resolver)
''',
        "HUB_AUTHORITY_STRICT_V61",
    )


def patch_transaction() -> None:
    replace_once(
        "scripts/domain_refresh_transaction_v2.py",
        "import resolve_provider_hubs as resolver\n",
        "import resolve_provider_hubs as resolver\nimport reconcile_domain_refresh_static_authority as static_authority\n",
        "import reconcile_domain_refresh_static_authority as static_authority",
    )
    replace_once(
        "scripts/domain_refresh_transaction_v2.py",
        '''        history["updated_at"] = resolver.now_iso()
        write(HISTORY_PATH, history)
        bundle_updates = rebuild_provider_configs(changed_provider_ids)
''',
        '''        history["updated_at"] = resolver.now_iso()
        write(HISTORY_PATH, history)

        # DOMAIN_REFRESH_STATIC_AUTHORITY_V61: rematerialization also consumes
        # durable static knowledge. Align address-only fields before the first
        # CONFIG rebuild so stale static DATA cannot undo the hub transaction.
        static_doc = load(STATIC_KNOWLEDGE_PATH)
        static_rows = static_doc.get("providers") or {}
        patches = config.get("provider_patches") or {}
        static_changed: list[str] = []
        for provider_id in sorted(set(changed_provider_ids)):
            row = static_rows.get(provider_id) if isinstance(static_rows, dict) else None
            patch = patches.get(provider_id) if isinstance(patches, dict) else None
            model = row.get("model") if isinstance(row, dict) else None
            if not isinstance(model, dict) or not isinstance(patch, dict):
                raise RuntimeError(f"{provider_id}: static authority state missing")
            if static_authority.sync_model(model, patch):
                static_changed.append(provider_id)
        if static_changed:
            write(STATIC_KNOWLEDGE_PATH, static_doc)
        print(
            "FIELD_DOMAIN_STATIC_AUTHORITY_TX "
            f"changed={len(static_changed)} providers={','.join(static_changed) if static_changed else '-'}"
        )
        bundle_updates = rebuild_provider_configs(changed_provider_ids)
''',
        "DOMAIN_REFRESH_STATIC_AUTHORITY_V61",
    )


def patch_flemmix_runtime() -> None:
    replace_once(
        "scripts/provider_patches/flemmix_current_runtime_v1.py",
        '''          try{raw=_text((NIAKVIO_PROVIDER_MODEL&&(
            NIAKVIO_PROVIDER_MODEL.officialSite||NIAKVIO_PROVIDER_MODEL.knownSite
          ))||"https://flemmix.cloud");}catch(_e){raw="https://flemmix.cloud";}
          try{raw=_substituteDomain(raw);}catch(_e){}
          return String(raw||"https://flemmix.cloud").replace(/\\/+$/g,"");
''',
        '''          try{raw=_text((NIAKVIO_PROVIDER_MODEL&&(
            NIAKVIO_PROVIDER_MODEL.officialSite||NIAKVIO_PROVIDER_MODEL.knownSite
          ))||"");}catch(_e){raw="";}
          try{raw=_substituteDomain(raw);}catch(_e){}
          return String(raw||"").replace(/\\/+$/g,"");
''',
        "NIAKVIO_FLEMMIX_NO_STATIC_TERMINAL_FALLBACK_V61",
    )
    text = read("scripts/provider_patches/flemmix_current_runtime_v1.py")
    if "NIAKVIO_FLEMMIX_NO_STATIC_TERMINAL_FALLBACK_V61" not in text:
        text = text.replace(
            "/* NIAKVIO_FLEMMIX_CURRENT_RUNTIME_V1 */",
            "/* NIAKVIO_FLEMMIX_CURRENT_RUNTIME_V1 */\n/* NIAKVIO_FLEMMIX_NO_STATIC_TERMINAL_FALLBACK_V61 */",
            1,
        )
    text = text.replace(
        "var lane=_mediaNamespace(mediaType),meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title)return [];",
        "var lane=_mediaNamespace(mediaType),meta=await _tmdb(tmdbId,mediaType);if(!meta||!meta.title||!BASE)return [];",
        1,
    )
    write("scripts/provider_patches/flemmix_current_runtime_v1.py", text)


def patch_tests() -> None:
    path = "tests/provider_hub_registry_test.py"
    text = read(path)
    marker = "# HUB_AUTHORITY_STRICT_V61_REGRESSION"
    if marker not in text:
        text += '''

# HUB_AUTHORITY_STRICT_V61_REGRESSION
flemmix_authority_cfg = copy.deepcopy(hubs['flemmix'])
flemmix_authority_cfg['direct_fallback'] = 'https://flemmix.cloud/'
flemmix_authority_cfg['direct_candidates'] = ['https://flemmix.cloud/']
flemmix_html = '<a href="https://flemmix.party/">Flemmix - Domaine principal</a>'
flemmix_candidates, preferred = resolver.choose_official(
    'flemmix', flemmix_authority_cfg, flemmix_authority_cfg['hub'], flemmix_html
)
assert preferred == 'https://flemmix.party', flemmix_candidates
assert all(resolver.host(row['url']) != 'flemmix.cloud' for row in flemmix_candidates), flemmix_candidates
'''
        write(path, text)

    path = "tests/flemmix_runtime_domain_authority_test.py"
    text = read(path)
    old = 'assert \'"https://flemmix.cloud"\' in text, "Flemmix fallback must be the current canonical .cloud host"\n'
    new = '''for retired in ("https://flemmix.me", "https://flemmix.kim", "https://flemmix.cloud", "https://flemmix.party"):
    assert retired not in text, f"Flemmix runtime must not bake terminal {retired}"
assert "NIAKVIO_FLEMMIX_NO_STATIC_TERMINAL_FALLBACK_V61" in text
'''
    if old in text:
        text = text.replace(old, new, 1)
    text = text.replace(
        'print("flemmix runtime domain authority regression passed: canonical model-owned host, no retired .me pin")',
        'print("flemmix runtime domain authority regression passed: model-owned terminal only, no baked-in domain")',
    )
    write(path, text)


def patch_domain_workflow() -> None:
    path = ".github/workflows/domain-refresh.yml"
    text = read(path)
    if "scripts/reconcile_domain_refresh_static_authority.py" not in text:
        text = text.replace(
            "      - 'scripts/reconcile_provider_domain_metadata.py'\n",
            "      - 'scripts/reconcile_provider_domain_metadata.py'\n"
            "      - 'scripts/reconcile_domain_refresh_static_authority.py'\n"
            "      - 'scripts/validate_domain_refresh_static_non_destructive.py'\n",
            1,
        )
    if "tests/domain_refresh_static_authority_test.py" not in text:
        text = text.replace(
            "      - 'tests/provider_domain_metadata_reconcile_test.py'\n",
            "      - 'tests/provider_domain_metadata_reconcile_test.py'\n"
            "      - 'tests/domain_refresh_static_authority_test.py'\n"
            "      - 'tests/domain_refresh_static_non_destructive_test.py'\n",
            1,
        )
    if "provider-v3-static-knowledge.before.json" not in text:
        text = text.replace(
            '          cp provider-v3-materialization.json "$RUNNER_TEMP/provider-v3-materialization.before.json"\n',
            '          cp provider-v3-materialization.json "$RUNNER_TEMP/provider-v3-materialization.before.json"\n'
            '          cp automation/provider-v3-static-knowledge.json "$RUNNER_TEMP/provider-v3-static-knowledge.before.json"\n',
            1,
        )
    if "reconcile_domain_refresh_static_authority.py --changes" not in text:
        text = text.replace(
            '          if [ "${#CHANGED[@]}" -gt 0 ]; then\n',
            '          python scripts/reconcile_domain_refresh_static_authority.py --changes health-output/domain-site-changes.json --check\n'
            '          if [ "${#CHANGED[@]}" -gt 0 ]; then\n',
            1,
        )
    static_guard = '''          python scripts/validate_domain_refresh_static_non_destructive.py \\
            --before-static "$RUNNER_TEMP/provider-v3-static-knowledge.before.json" \\
            --changes health-output/domain-site-changes.json
'''
    if static_guard not in text:
        anchor = '''          python scripts/validate_provider_domain_graph.py provider-overrides.json
'''
        if anchor not in text:
            raise SystemExit("V61 domain workflow guard anchor missing")
        text = text.replace(anchor, static_guard + anchor, 1)
    validate_marker = "          python tests/domain_refresh_static_authority_test.py\n"
    if validate_marker not in text:
        anchor = "          python tests/provider_domain_metadata_reconcile_test.py\n"
        if anchor not in text:
            raise SystemExit("V61 domain workflow test anchor missing")
        text = text.replace(
            anchor,
            anchor
            + "          python tests/domain_refresh_static_authority_test.py\n"
            + "          python tests/domain_refresh_static_non_destructive_test.py\n",
            1,
        )
    if "automation/provider-v3-static-knowledge.json manifest.json" not in text:
        text = text.replace(
            "            provider-v3-materialization.json providers/ \\\n",
            "            provider-v3-materialization.json automation/provider-v3-static-knowledge.json providers/ \\\n",
            1,
        )
    write(path, text)


def patch_workflow_test() -> None:
    path = "tests/domain_refresh_non_destructive_workflow_test.py"
    text = read(path)
    if "DOMAIN_REFRESH_STATIC_AUTHORITY_WORKFLOW_V61" not in text:
        text += '''

# DOMAIN_REFRESH_STATIC_AUTHORITY_WORKFLOW_V61
workflow = (ROOT / '.github/workflows/domain-refresh.yml').read_text(encoding='utf-8')
assert 'reconcile_domain_refresh_static_authority.py' in workflow
assert 'validate_domain_refresh_static_non_destructive.py' in workflow
assert 'provider-v3-static-knowledge.before.json' in workflow
assert 'automation/provider-v3-static-knowledge.json' in workflow
'''
        write(path, text)


def main() -> int:
    patch_resolver()
    patch_transaction()
    patch_flemmix_runtime()
    patch_tests()
    patch_domain_workflow()
    patch_workflow_test()
    print("V61_PATCH_APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
