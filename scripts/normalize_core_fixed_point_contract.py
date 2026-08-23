#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize durable Core byte contracts, then verify their fixed point.

Only owning runtime/publication modules are normalized. The canonical rebuild
boundary is a Terser-preserved NUVIO comment placed after provider-derived code
and before every global Core hook. Tests are never rewritten here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
APPLY = ROOT / "scripts" / "apply_provider_overrides.py"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
SECURITY_HOOK = ROOT / "scripts" / "provider_patches" / "global_provider_security_hardening_v1.py"
PURIFICATION = ROOT / "scripts" / "provider_purification.py"
PURIFIER = ROOT / "engine_v2" / "scripts" / "purify-provider.mjs"
PLAYBACK_TEST = ROOT / "tests" / "global_playback_integrity_policy_test.py"
PURIFICATION_TEST = ROOT / "tests" / "provider_purification_contract_test.py"

CORE_START_MARKER = "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"
SECURITY_BOUNDARY = "__nuvioGlobalProviderSecurityBoundaryV1"
SECURITY_MARKER = "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1"


def normalize_apply(text: str) -> str:
    if f'CORE_START_MARKER = "{CORE_START_MARKER}"' not in text:
        anchor = 'GLOBAL_STREAM_PRESENTATION = "scripts/provider_patches/global_stream_presentation_v1.py"\n'
        if anchor not in text:
            raise ValueError("Core start boundary declaration anchor missing")
        text = text.replace(anchor, anchor + f'CORE_START_MARKER = "{CORE_START_MARKER}"\n', 1)

    domain_fn = dedent(r'''
    def _inject_runtime_domain_overrides(text: str, replacements: dict[str, Any]) -> tuple[str, int]:
        """Embed host rewriting into the provider JavaScript artifact itself.

        Existing wrappers are replaced at their current byte position. Moving one
        to byte zero on every reconstruction rotates hashes without semantic change.
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
    text = text[:start] + domain_fn + text[end:]

    strip_fn = dedent(r'''
    def _strip_generated_core_tail(text: str) -> tuple[str, bool]:
        """Recover provider-derived bytes before the global Core pipeline.

        New bundles carry a standalone NUVIO comment immediately before the first
        global Core hook. The final Terser policy explicitly preserves NUVIO
        comments, so unlike an executable assignment this boundary cannot acquire
        a JavaScript dependency or fail at runtime. Legacy global markers are only
        a one-pass migration fallback for bundles published before the boundary.
        """
        boundary_needle = f"/* {CORE_START_MARKER} */"
        boundary_index = text.find(boundary_needle)
        if boundary_index >= 0:
            return text[:boundary_index].rstrip(), True

        legacy_markers = tuple(GENERATED_CORE_TAIL_MARKERS) + (
            "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
            "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
            "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
            "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
            "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
            "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
        )
        starts = []
        for marker in legacy_markers:
            index = text.find(f"/* {marker}")
            if index >= 0:
                starts.append(index)
        if not starts:
            return text, False
        return text[:min(starts)].rstrip(), True
    ''').lstrip("\n")
    start = text.index("def _strip_generated_core_tail(")
    end = text.index("\ndef apply_overrides(", start)
    text = text[:start] + strip_fn + text[end:]

    boundary_block = '''        if CORE_START_MARKER not in text:\n            text = text.rstrip() + f"\\n/* {CORE_START_MARKER} */\\n"\n\n'''
    if boundary_block not in text:
        anchor = '        def _apply_playback_stage(hooks: list[str]) -> None:\n'
        if anchor not in text:
            raise ValueError("global playback stage anchor missing")
        text = text.replace(anchor, boundary_block + anchor, 1)
    return text


def normalize_reapply(text: str) -> str:
    purifier_import = "from provider_purification import purify_bytes\n"
    if purifier_import not in text:
        anchor = "from provider_engine_normalizer import (\n"
        if anchor not in text:
            raise ValueError("provider engine import anchor missing")
        text = text.replace(anchor, purifier_import + anchor, 1)

    text = text.replace(
        "def validate_artifact(data: bytes) -> None:\n",
        "def validate_artifact(data: bytes, provider_id: str) -> None:\n",
        1,
    )
    text = text.replace(
        'raise ValueError(f"patched published provider rejected:\\n{detail or \'no diagnostic\'}")',
        'raise ValueError(f"patched published provider rejected provider={provider_id}:\\n{detail or \'no diagnostic\'}")',
        1,
    )
    text = text.replace(
        "            validate_artifact(patched)\n",
        "            validate_artifact(patched, provider_id)\n",
        1,
    )

    if "purified, purification = purify_bytes(patched)" not in text:
        anchor = "        changed = patched != original\n"
        if anchor not in text:
            raise ValueError("published-byte digest anchor missing")
        block = '''        # Final provider bytes are purified only after every Core/provider/runtime\n        # transform. These exact validated bytes are content-addressed and later\n        # proved by Deep and native Labs.\n        purified, purification = purify_bytes(patched)\n        if purification["applied"]:\n            records = list(records) + [{\n                "type": "provider_purification",\n                "phase": "final-post-transform",\n                "revision": 2,\n                "tool": "terser",\n                "tool_version": str(purification.get("toolVersion") or ""),\n                "mode": str(purification.get("mode") or ""),\n                "mangle": False,\n                "fixed_point_verified": bool(purification.get("fixedPointVerified")),\n                "conservative_compression": bool(purification.get("conservativeCompression")),\n                "risk_flags": list(purification.get("riskFlags") or []),\n                "source_sha256": purification["sourceSha256"],\n                "output_sha256": purification["candidateSha256"],\n                "bytes_before": purification["bytesBefore"],\n                "bytes_after": purification["bytesAfter"],\n            }]\n        patched = purified\n'''
        text = text.replace(anchor, block + anchor, 1)
    return text


def normalized_outputs() -> dict[Path, str]:
    return {
        APPLY: normalize_apply(APPLY.read_text(encoding="utf-8")),
        REAPPLY: normalize_reapply(REAPPLY.read_text(encoding="utf-8")),
    }


def assert_contract() -> None:
    apply_text = APPLY.read_text(encoding="utf-8")
    reapply_text = REAPPLY.read_text(encoding="utf-8")
    security_text = SECURITY_HOOK.read_text(encoding="utf-8")
    purification_text = PURIFICATION.read_text(encoding="utf-8")
    purifier_text = PURIFIER.read_text(encoding="utf-8")
    playback_test = PLAYBACK_TEST.read_text(encoding="utf-8")
    purification_test = PURIFICATION_TEST.read_text(encoding="utf-8")

    for required in (
        f'CORE_START_MARKER = "{CORE_START_MARKER}"',
        'boundary_needle = f"/* {CORE_START_MARKER} */"',
        "text.find(boundary_needle)",
        f"/* {{CORE_START_MARKER}} */",
        '"NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"',
        '"NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1"',
        '"NUVIO_HLS_RUNTIME_INTEGRITY_V1"',
        "existing_span",
        "output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]",
    ):
        assert required in apply_text, f"missing apply fixed-point contract: {required}"
    assert f'HOOK_BOUNDARY = "{SECURITY_BOUNDARY}"' in security_text

    for required in (
        "from provider_purification import purify_bytes",
        "def validate_artifact(data: bytes, provider_id: str) -> None:",
        "patched published provider rejected provider={provider_id}",
        "validate_artifact(patched, provider_id)",
        "purified, purification = purify_bytes(patched)",
        '"phase": "final-post-transform"',
        '"mangle": False',
        "patched = purified",
        "digest = hashlib.sha256(patched).hexdigest()",
    ):
        assert required in reapply_text, f"missing final publication contract: {required}"
    assert reapply_text.index("purified, purification = purify_bytes(patched)") < reapply_text.index(
        "digest = hashlib.sha256(patched).hexdigest()"
    )

    for required in (
        'TERSER_VERSION = "5.50.0"',
        "def _stable_candidate(",
        "_run_purifier(first, format_only=format_only)",
        '"--format-only"',
        "validate_provider_artifact.cjs",
    ):
        assert required in purification_text, required
    for required in (
        'EXPECTED_TERSER_VERSION = "5.50.0"',
        "comments: /(?:@license|@preserve|NUVIO_|^!)/",
        "mangle: false",
        "unsafe: false",
        "keep_fnames: true",
        "keep_classnames: true",
    ):
        assert required in purifier_text, required
    for required in (
        "if reapplied != patched:",
        "Core discovery transform not byte-idempotent",
        "hashlib.sha256(patched).hexdigest()",
        "hashlib.sha256(reapplied).hexdigest()",
    ):
        assert required in playback_test, f"missing diagnostic fixed-point assertion: {required}"
    assert "purified, purification = purify_bytes(patched)" in purification_test


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    outputs = normalized_outputs()
    changed = [path for path, value in outputs.items() if value != path.read_text(encoding="utf-8")]
    if args.apply:
        for path in changed:
            path.write_text(outputs[path], encoding="utf-8")
        assert_contract()
        print(
            "FIELD_CORE_FIXED_POINT_CONTRACT "
            f"changed={len(changed)} core_start_boundary=preserved_comment "
            "runtime_domain_position=stable final_terser=5.50.0"
        )
        return 0

    if changed:
        for path in changed:
            print(f"STALE_CORE_FIXED_POINT_CONTRACT={path.relative_to(ROOT)}")
        return 1
    assert_contract()
    print(
        "FIELD_CORE_FIXED_POINT_CONTRACT changed=0 core_start_boundary=preserved_comment "
        "runtime_domain_position=stable final_terser=5.50.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
