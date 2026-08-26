#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize durable Core byte contracts, then verify their fixed point.

Only owning runtime/publication modules are normalized. Rebuild boundaries are
accepted only after the provider export bridge, so a preserved comment relocated
by a JS formatter can never truncate provider-derived bytes. Tests are never
rewritten here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent
from core_rebuild_safety import harden_generated_apply

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
            if existing_end < 0 and call >= 0:
                existing_end = text.find(");", call)
            if existing_start < 0 or existing_end < 0:
                raise ValueError("unterminated runtime domain override bootstrap")
            existing_span = (existing_start, existing_end + 2)
            if text[existing_end + 2:existing_end + 3] == "\n":
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
    def _provider_export_floor(text: str) -> int:
        """Return the end of the last provider export bridge, or -1 when unknown.

        Core-generated wrappers must never become the authority for where provider
        bytes end. The common Nuvio bundle bridge is deliberately narrow here; an
        unrecognized bundle shape fails closed and is kept intact for validation.
        """
        patterns = (
            r"\bmodule\.exports\s*=\s*__provider\b",
            r"\bglobalThis\.getStreams\s*=\s*__provider\.getStreams\b",
            r"\bglobal\.getStreams\s*=\s*__provider\.getStreams\b",
            r"\bself\.getStreams\s*=\s*__provider\.getStreams\b",
        )
        ends = [match.end() for pattern in patterns for match in re.finditer(pattern, text)]
        if ends:
            return max(ends)
        # A minority of upstream bundles export a provider object directly rather
        # than through __provider. CommonJS export remains the safest generic floor.
        generic = [match.end() for match in re.finditer(r"\bmodule\.exports\s*=", text)]
        return max(generic) if generic else -1


    def _strip_generated_core_tail(text: str) -> tuple[str, bool]:
        """Recover provider bytes without ever cutting before the export bridge.

        Terser is allowed to preserve comments while changing their attachment to
        AST nodes. Therefore a Core boundary/marker found before the provider export
        is stale metadata, not a truncation point. Stale boundary comments are
        removed, then only markers at or after the export floor may delimit the
        generated Core tail. Unknown export shapes fail closed and retain all bytes.
        """
        original = text
        boundary_needle = f"/* {CORE_START_MARKER} */"
        floor = _provider_export_floor(text)
        if floor < 0:
            return text, False

        boundary_index = text.find(boundary_needle, floor)
        if boundary_index >= floor:
            prefix = text[:boundary_index].replace(boundary_needle, "").rstrip()
            return prefix, True

        # A preserved comment may have floated before the provider bridge. It must
        # not suppress insertion of a fresh post-export boundary on reconstruction.
        if boundary_needle in text:
            text = text.replace(boundary_needle, "")
            floor = _provider_export_floor(text)
            if floor < 0:
                return original, False

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
            index = text.find(f"/* {marker}", floor)
            if index >= floor:
                starts.append(index)
        if starts:
            return text[:min(starts)].rstrip(), True
        return text, text != original
    ''').lstrip("\n")
    start = text.index("def _strip_generated_core_tail(")
    # Replace an older helper too when this normalization has already been applied.
    helper_start = text.rfind("def _provider_export_floor(", 0, start)
    if helper_start >= 0:
        start = helper_start
    end = text.index("\ndef apply_overrides(", start)
    text = text[:start] + strip_fn + text[end:]

    boundary_block = '''        provider_floor = _provider_export_floor(text)\n        boundary_needle = f"/* {CORE_START_MARKER} */"\n        if provider_floor >= 0 and text.find(boundary_needle, provider_floor) < 0:\n            text = text.rstrip() + f"\\n{boundary_needle}\\n"\n\n'''
    old_boundary_blocks = (
        '''        if CORE_START_MARKER not in text:\n            text = text.rstrip() + f"\\n/* {CORE_START_MARKER} */\\n"\n\n''',
        boundary_block,
    )
    anchor = '        def _apply_playback_stage(hooks: list[str]) -> None:\n'
    if anchor not in text:
        raise ValueError("global playback stage anchor missing")
    # Collapse any previous boundary insertion form before materializing the guarded one.
    for old in old_boundary_blocks:
        text = text.replace(old, "", 1)
    text = text.replace(anchor, boundary_block + anchor, 1)
    return harden_generated_apply(text)


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
        "def _provider_export_floor(text: str) -> int:",
        'r"\\bmodule\\.exports\\s*=\\s*__provider\\b"',
        'boundary_index = text.find(boundary_needle, floor)',
        'if boundary_index >= floor:',
        'if index >= floor:',
        'text.replace(boundary_needle, "")',
        'text.find(f"/* {marker}", floor)',
        "provider_floor = _provider_export_floor(text)",
        'text.find(boundary_needle, provider_floor) < 0',
        '"NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"',
        '"NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1"',
        '"NUVIO_HLS_RUNTIME_INTEGRITY_V1"',
        "existing_span",
        "def _runtime_domain_span_matches_rules(candidate: str, rules: dict[str, str]) -> bool:",
        "_strip_runtime_domain_orphan_calls(text, rules)",
        "_runtime_domain_span_matches_rules(candidate, rules)",
        "return text, 0 if text == original_text else max(1, orphan_count)",
    ):
        assert required in apply_text, f"missing apply fixed-point contract: {required}"
    assert "if boundary_index > floor:" not in apply_text
    assert "if index > floor:" not in apply_text
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
            f"changed={len(changed)} core_start_boundary=export_guarded_comment "
            "runtime_domain_position=stable final_terser=5.50.0"
        )
        return 0

    if changed:
        for path in changed:
            print(f"STALE_CORE_FIXED_POINT_CONTRACT={path.relative_to(ROOT)}")
        return 1
    assert_contract()
    print(
        "FIELD_CORE_FIXED_POINT_CONTRACT changed=0 core_start_boundary=export_guarded_comment "
        "runtime_domain_position=stable final_terser=5.50.0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
