#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Normalize durable Core fixed-point contracts before provider publication.

This normalizer owns the byte-level invariants that must remain true across every
Core reconstruction:

* generated security/facts/identity/presentation tails are rebuilt from the
  canonical provider prefix using a Terser-stable JavaScript sentinel;
* runtime-domain wrappers keep their existing byte position;
* final published provider bytes are purified by pinned Terser only after all
  Core/provider/runtime transforms and before content-addressing;
* regression tests assert those contracts directly.

The script is intentionally idempotent. ``--check`` fails whenever a target file
would still be changed by the normalization.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts" / "apply_provider_overrides.py"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
PLAYBACK_TEST = ROOT / "tests" / "global_playback_integrity_policy_test.py"
PURIFICATION_TEST = ROOT / "tests" / "provider_purification_contract_test.py"


def normalize_apply_provider_overrides(text: str) -> str:
    tuple_old = '''GENERATED_CORE_TAIL_MARKERS = (\n    "NUVIO_GLOBAL_STREAM_FACTS_V1",'''
    tuple_new = '''GENERATED_CORE_TAIL_MARKERS = (\n    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",\n    "NUVIO_GLOBAL_STREAM_FACTS_V1",'''
    if '"NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",\n    "NUVIO_GLOBAL_STREAM_FACTS_V1"' not in text:
        if tuple_old not in text:
            raise ValueError("unable to locate generated Core tail marker tuple")
        text = text.replace(tuple_old, tuple_new, 1)

    function_start = text.index("def _strip_generated_core_tail(")
    function_end = text.index("\ndef apply_overrides(", function_start)
    canonical_strip = dedent(r'''
    def _strip_generated_core_tail(text: str) -> tuple[str, bool]:
        """Return provider-derived code without a generated Core tail.

        The security hook emits a real JavaScript string-expression sentinel as
        the first generated-tail statement. Terser may move comments, but it does
        not reorder this statement under the conservative profile. Prefer that
        boundary whenever present and use comment markers only for legacy bundles.
        """
        security_sentinel = '"NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"'
        security_index = text.find(security_sentinel)
        if security_index >= 0:
            prefix = text[:security_index]
            # Terser can reattach retained NUVIO comments to earlier nodes. Remove
            # relocated generated-marker comments from the provider prefix so they
            # cannot accumulate across fixed-point passes.
            prefix = re.sub(
                r"/\*\s*NUVIO_GLOBAL_(?:PROVIDER_SECURITY_HOOK_V1|STREAM_(?:FACTS|IDENTITY|PRESENTATION)_V1(?::[^*]*)?)\s*\*/\s*",
                "",
                prefix,
                flags=re.DOTALL,
            )
            return prefix.rstrip(), True

        starts = []
        for marker in GENERATED_CORE_TAIL_MARKERS:
            needle = (
                f"/* {marker} */"
                if marker == "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"
                else f"/* {marker}:"
            )
            index = text.find(needle)
            if index >= 0:
                starts.append(index)
        if not starts:
            return text, False
        return text[:min(starts)].rstrip(), True
    ''').lstrip("\n")
    text = text[:function_start] + canonical_strip + text[function_end:]

    text = text.replace(
        "    Facts, identity and presentation are generated artifacts owned by the Core\n    scheduler.",
        "    Security, facts, identity and presentation are generated artifacts owned by the Core\n    scheduler.",
        1,
    )

    canonical = dedent(r'''
    def _inject_runtime_domain_overrides(text: str, replacements: dict[str, Any]) -> tuple[str, int]:
        """Embed host rewriting into the provider JavaScript artifact itself.

        Existing wrappers are replaced at their current byte position. Moving
        one back to byte zero during every reconstruction reorders it against
        idempotent prefix wrappers and rotates hashes without semantic change.
        """
        from urllib.parse import urlparse

        original_text = text
        rules: dict[str, str] = {}
        for old, new in replacements.items():
            old_value = str(old).lower().strip().rstrip("/")
            new_value = str(new).lower().strip().rstrip("/")
            old_host = urlparse(old_value).hostname if "://" in old_value else old_value
            new_host = urlparse(new_value).hostname if "://" in new_value else new_value
            if old_host and new_host and old_host != new_host:
                rules[old_host] = new_host

        marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"
        marker_comment = f"/* {marker} */"
        existing_span: tuple[int, int] | None = None
        if marker_comment in text:
            existing_start = text.find(marker_comment)
            call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', existing_start)
            existing_end = text.find(");\n", call) if call >= 0 else -1
            if existing_start < 0 or existing_end < 0:
                raise ValueError("unterminated runtime domain override bootstrap")
            existing_span = (existing_start, existing_end + 3)

        if not rules:
            if existing_span is None:
                return text, 0
            output = text[:existing_span[0]] + text[existing_span[1]:]
            return output, 0 if output == original_text else 1

        import base64
        encoded_rules = [
            [base64.b64encode(old.encode("utf-8")).decode("ascii"), new]
            for old, new in sorted(rules.items())
        ]
        payload = json.dumps(encoded_rules, separators=(",", ":"))
        bootstrap = """/* %s */
    ;(function(g,rules){
      if(!g||typeof g.fetch!=="function")return;
      var key="__nuvioDomainOverrideV1";
      var state=g[key];
      if(!state){
        state={native:g.fetch.bind(g),rules:Object.create(null)};
        g[key]=state;
        g.fetch=function(input,init){
          var next=input;
          try{
            var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
            var url=new URL(raw);
            var replacement=state.rules[String(url.hostname).toLowerCase()];
            if(replacement){
              url.hostname=replacement;
              next=(typeof Request!=="undefined"&&input instanceof Request)?new Request(url.toString(),input):url.toString();
            }
          }catch(_error){}
          return state.native(next,init);
        };
      }
      for(var i=0;i<rules.length;i++){
        try{state.rules[atob(rules[i][0])]=rules[i][1];}catch(_error){}
      }
    })(typeof globalThis!=="undefined"?globalThis:this,%s);
    """ % (marker, payload)

        if existing_span is None:
            output = bootstrap + text
        else:
            output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]
        return output, 0 if output == original_text else len(rules)
    ''').lstrip("\n")
    start = text.index("def _inject_runtime_domain_overrides(")
    end = text.index("\ndef _strip_legacy_global_stream_guards", start)
    text = text[:start] + canonical + text[end:]
    return text


def normalize_reapply_published_overrides(text: str) -> str:
    purification_import = "from provider_purification import purify_bytes\n"
    import_anchor = "from provider_engine_normalizer import (\n"
    if purification_import not in text:
        if import_anchor not in text:
            raise ValueError("provider engine import anchor missing")
        text = text.replace(import_anchor, purification_import + import_anchor, 1)

    purification_block = '''        # Final provider bytes are purified only after every Core/provider/runtime\n        # transform. The resulting validated bytes are the ones content-addressed,\n        # referenced by manifests and later proved by Deep/native Labs.\n        purified, purification = purify_bytes(patched)\n        if purification["applied"]:\n            records = list(records) + [{\n                "type": "provider_purification",\n                "phase": "final-post-transform",\n                "revision": 2,\n                "tool": "terser",\n                "tool_version": str(purification.get("toolVersion") or ""),\n                "mode": str(purification.get("mode") or ""),\n                "mangle": False,\n                "fixed_point_verified": bool(purification.get("fixedPointVerified")),\n                "conservative_compression": bool(purification.get("conservativeCompression")),\n                "risk_flags": list(purification.get("riskFlags") or []),\n                "source_sha256": purification["sourceSha256"],\n                "output_sha256": purification["candidateSha256"],\n                "bytes_before": purification["bytesBefore"],\n                "bytes_after": purification["bytesAfter"],\n            }]\n        patched = purified\n'''
    if "purified, purification = purify_bytes(patched)" not in text:
        anchor = "        changed = patched != original\n"
        if anchor not in text:
            raise ValueError("published-byte changed anchor missing")
        text = text.replace(anchor, purification_block + anchor, 1)
    else:
        # Upgrade the durable publication record when an older normalization was
        # already materialized.
        text = text.replace('"revision": 1,\n                "tool": "terser",', '"revision": 2,\n                "tool": "terser",', 1)
        if '"mode": str(purification.get("mode") or ""),' not in text:
            text = text.replace(
                '"tool_version": str(purification.get("toolVersion") or ""),\n                "mangle": False,',
                '"tool_version": str(purification.get("toolVersion") or ""),\n                "mode": str(purification.get("mode") or ""),\n                "mangle": False,\n                "fixed_point_verified": bool(purification.get("fixedPointVerified")),',
                1,
            )
    return text


def normalize_playback_test(text: str) -> str:
    security_marker = "# Security is itself a generated Core boundary and must be rebuilt, not retained as provider source."
    legacy_block = dedent('''
    # Security is itself a generated Core boundary and must be rebuilt, not retained as provider source.
    boundary_input = "provider-source\\n/* NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1 */\\n/* NUVIO_GLOBAL_STREAM_FACTS_V1:old */\\nstale-tail"
    boundary_prefix, boundary_removed = module._strip_generated_core_tail(boundary_input)
    assert boundary_removed is True
    assert boundary_prefix == "provider-source"

    ''').lstrip("\n")
    sentinel_block = dedent('''
    # Security is itself a generated Core boundary and must be rebuilt, not retained as provider source.
    boundary_input = 'provider-source\\n"NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1";\\n/* NUVIO_GLOBAL_STREAM_FACTS_V1:old */\\nstale-tail'
    boundary_prefix, boundary_removed = module._strip_generated_core_tail(boundary_input)
    assert boundary_removed is True
    assert boundary_prefix == "provider-source"
    # Retained comments may be reattached by Terser before the real sentinel; they
    # must never become the authoritative cut point or delete provider code.
    relocated = '/* NUVIO_GLOBAL_STREAM_FACTS_V1:relocated */\\nprovider-source\\n"NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1";\\nstale-tail'
    relocated_prefix, relocated_removed = module._strip_generated_core_tail(relocated)
    assert relocated_removed is True
    assert relocated_prefix == "provider-source"

    ''').lstrip("\n")
    if legacy_block in text:
        text = text.replace(legacy_block, sentinel_block, 1)
    elif security_marker not in text:
        anchor = "# The complete discovery transform must be byte-idempotent. Stable output bytes\n"
        if anchor not in text:
            raise ValueError("security fixed-point test anchor missing")
        text = text.replace(anchor, sentinel_block + anchor, 1)
    elif 'relocated = ' not in text:
        raise ValueError("existing security fixed-point test is not sentinel-aware")

    runtime_marker = "# Runtime-domain wrappers preserve their existing position across reconstruction."
    if runtime_marker not in text:
        anchor = "# Runtime repair phase must not inject discovery wrappers.\n"
        block = dedent('''
        # Runtime-domain wrappers preserve their existing position across reconstruction.
        domain_seed = 'provider-source\\n'
        domain_once, _ = module._inject_runtime_domain_overrides(domain_seed, {'old.example': 'new.example'})
        domain_prefixed = 'HLS-PREFIX\\n' + domain_once
        domain_twice, _ = module._inject_runtime_domain_overrides(domain_prefixed, {'old.example': 'new.example'})
        assert domain_twice == domain_prefixed
        assert domain_twice.index('HLS-PREFIX') < domain_twice.index('NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1')

        ''').lstrip("\n")
        if anchor not in text:
            raise ValueError("runtime-domain fixed-point test anchor missing")
        text = text.replace(anchor, block + anchor, 1)
    return text


def normalize_purification_test(text: str) -> str:
    reapply_decl = 'reapply = (ROOT / "scripts/reapply_published_overrides.py").read_text(encoding="utf-8")\n'
    if reapply_decl not in text:
        anchor = 'deep = (ROOT / "scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")\n'
        if anchor not in text:
            raise ValueError("purification contract deep anchor missing")
        text = text.replace(anchor, anchor + reapply_decl, 1)

    marker = "# Published provider bytes must end with the same pinned Terser purification."
    if marker not in text:
        anchor = "# Native-reader Brain candidates must be purified before they are copied into the\n"
        block = '''# Published provider bytes must end with the same pinned Terser purification.\n# No provider/Core/runtime byte transform may happen between purification and the\n# content-addressed digest used by manifests/provenance.\nfor required in (\n    "from provider_purification import purify_bytes",\n    "purified, purification = purify_bytes(patched)",\n    '"phase": "final-post-transform"',\n    '"tool": "terser"',\n    '"mangle": False',\n    "patched = purified",\n):\n    assert required in reapply, required\nassert reapply.index("purified, purification = purify_bytes(patched)") < reapply.index("digest = hashlib.sha256(patched).hexdigest()")\n\n'''
        if anchor not in text:
            raise ValueError("native reader purification anchor missing")
        text = text.replace(anchor, block + anchor, 1)
    return text


def normalize_targets() -> dict[Path, str]:
    return {
        APPLY: normalize_apply_provider_overrides(APPLY.read_text(encoding="utf-8")),
        REAPPLY: normalize_reapply_published_overrides(REAPPLY.read_text(encoding="utf-8")),
        PLAYBACK_TEST: normalize_playback_test(PLAYBACK_TEST.read_text(encoding="utf-8")),
        PURIFICATION_TEST: normalize_purification_test(PURIFICATION_TEST.read_text(encoding="utf-8")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    outputs = normalize_targets()
    changed = [path for path, output in outputs.items() if output != path.read_text(encoding="utf-8")]
    if args.check:
        if changed:
            for path in changed:
                print(f"STALE_CORE_FIXED_POINT_CONTRACT={path.relative_to(ROOT)}")
            return 1
        print("FIELD_CORE_FIXED_POINT_CONTRACT changed=0 security_boundary=sentinel runtime_domain_position=stable final_terser=5.50.0")
        return 0

    for path, output in outputs.items():
        if output != path.read_text(encoding="utf-8"):
            path.write_text(output, encoding="utf-8")
    print(
        "FIELD_CORE_FIXED_POINT_CONTRACT "
        f"changed={len(changed)} security_boundary=sentinel runtime_domain_position=stable "
        "final_terser=5.50.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
