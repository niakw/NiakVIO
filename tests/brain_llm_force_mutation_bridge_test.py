#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/apply_brain_llm_force_mutations.py"

spec = importlib.util.spec_from_file_location("force_mutations", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "automation").mkdir(parents=True)
    (root / "scripts/provider_patches").mkdir(parents=True)
    (root / "providers").mkdir(parents=True)

    runtime_source = (
        "/* BEGIN NIAKVIO_PROVIDER */\n"
        "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        "function resolve(){return oldResolver();}\n"
        "/* END NIAKVIO_PROVIDER */\n"
    )
    (root / "providers/demo.js").write_text(runtime_source, encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps({
            "scrapers": [
                {"id": "demo", "filename": "providers/demo.js"},
                {"id": "healthy", "filename": "providers/demo.js"},
            ]
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    patch = root / "scripts/provider_patches/demo_runtime_v1.py"
    patch.write_text("def apply(value):\n    return value\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    overrides = {
        "schema_version": 7,
        "provider_patches": {
            "demo": {
                "capability": "html_scraper",
                "learned_routes": ["/old"],
                "provider_lego_scripts": [
                    "scripts/provider_patches/demo_runtime_v1.py"
                ],
            },
            "healthy": {
                "capability": "html_scraper",
                "learned_routes": ["/healthy"],
            },
        },
    }
    (root / "provider-overrides.json").write_text(
        json.dumps(overrides, indent=2) + "\n",
        encoding="utf-8",
    )

    mod.ROOT = root
    mod.source_drift = lambda *_args, **_kwargs: ([], set())

    mutations = [
        {
            "scope": "provider_data",
            "operation": "append",
            "path": "learned_routes",
            "value": "/new",
        }
    ]
    payload = {
        "schemaVersion": 1,
        "sourceNiakvioSha": "a" * 40,
        "brainLlmSha": "b" * 40,
        "sandboxMutationAuthority": True,
        "publicationAuthority": False,
        "proofAuthority": False,
        "privateContentRetained": False,
        "rows": [
            {
                "providerId": "demo",
                "mutations": mutations,
                "mutationFingerprint": mod._fingerprint(mutations),
                "mutationContextFingerprint": mod._mutation_context_fingerprint(
                    "demo", overrides["provider_patches"]["demo"], mutations
                ),
            },
            {
                "providerId": "healthy",
                "mutations": mutations,
                "mutationFingerprint": mod._fingerprint(mutations),
                "mutationContextFingerprint": mod._mutation_context_fingerprint(
                    "healthy", overrides["provider_patches"]["healthy"], mutations
                ),
            },
        ],
    }

    report = mod.apply_payload(
        payload,
        current_sha="c" * 40,
        selected={"demo"},
    )
    assert report["appliedProviders"] == ["demo"], report
    assert any(
        row["provider"] == "healthy"
        and row["reason"] == "outside-current-repair-scope"
        for row in report["skipped"]
    ), report
    updated = json.loads((root / "provider-overrides.json").read_text())
    assert updated["provider_patches"]["demo"]["learned_routes"] == ["/old", "/new"]
    assert updated["provider_patches"]["healthy"]["learned_routes"] == ["/healthy"]

    safe = {
        "scope": "provider_patch",
        "operation": "unified_diff",
        "path": "scripts/provider_patches/demo_runtime_v1.py",
        "diff": (
            # Brain-LLM public mutations use exact repo paths rather than
            # git's conventional a/ and b/ prefixes. The bridge must normalize
            # these headers before git apply, without changing the signed row.
            "--- scripts/provider_patches/demo_runtime_v1.py\n"
            "+++ scripts/provider_patches/demo_runtime_v1.py\n"
            "@@ -1,2 +1,2 @@\n"
            " def apply(value):\n"
            "-    return value\n"
            "+    return str(value)\n"
        ),
    }
    changed = mod._apply_file_mutation(
        "demo",
        updated["provider_patches"]["demo"],
        safe,
    )
    assert changed == "scripts/provider_patches/demo_runtime_v1.py"
    assert "return str(value)" in patch.read_text(encoding="utf-8")

    generated_mutations = [
        {
            "scope": "provider_bloc",
            "operation": "upsert",
            "family": "terminal_resolution",
            "find": "return oldResolver();",
            "replace": "return resolveTerminalMedia();",
        }
    ]
    current_entry = updated["provider_patches"]["demo"]
    generated_payload = {
        "schemaVersion": 1,
        "sourceNiakvioSha": "a" * 40,
        "brainLlmSha": "b" * 40,
        "sandboxMutationAuthority": True,
        "publicationAuthority": False,
        "proofAuthority": False,
        "privateContentRetained": False,
        "rows": [
            {
                "providerId": "demo",
                "mutations": generated_mutations,
                "mutationFingerprint": mod._fingerprint(generated_mutations),
                "mutationContextFingerprint": mod._mutation_context_fingerprint(
                    "demo", current_entry, generated_mutations
                ),
            }
        ],
    }
    # A generated provider Bloc may replace a complete bounded function and
    # therefore needs the same 1800-char ceiling as compact Force function units.
    long_replace = "return oldResolver();/*" + ("x" * 1250) + "*/"
    long_mutation = {
        "scope": "provider_bloc",
        "operation": "upsert",
        "family": "bounded_function_rewrite",
        "find": "return oldResolver();",
        "replace": long_replace,
    }
    family, find, replace, _fp = mod._validate_generated_bloc_mutation("demo", long_mutation)
    assert family == "bounded_function_rewrite"
    assert find == "return oldResolver();"
    assert replace == long_replace
    assert len(replace) > 1200 and len(replace) <= 1800

    long_find = 'function resolve(page){const marker="' + ("a" * 900) + '";return page.url;}'
    long_find_replace = 'function resolve(page){const marker="' + ("b" * 900) + '";return page.finalUrl||page.url;}'
    long_find_mutation = {
        "scope": "provider_bloc",
        "operation": "upsert",
        "family": "long_exact_function_anchor",
        "find": long_find,
        "replace": long_find_replace,
    }
    # Receiver bounds match Brain's complete function-unit contract. Exact-byte
    # uniqueness is still checked against the real provider runtime at apply time.
    original_surface = mod._provider_runtime_surface
    original_owned = mod._provider_owned_source
    try:
        mod._provider_runtime_surface = lambda provider: ("demo.js", "providers/demo.js", long_find)
        mod._provider_owned_source = lambda source: source
        family2, find2, replace2, _fp2 = mod._validate_generated_bloc_mutation("demo", long_find_mutation)
    finally:
        mod._provider_runtime_surface = original_surface
        mod._provider_owned_source = original_owned
    assert family2 == "long_exact_function_anchor"
    assert find2 == long_find
    assert replace2 == long_find_replace
    assert len(find2) > 320 and len(find2) <= 1800

    generated_report = mod.apply_payload(
        generated_payload,
        current_sha="c" * 40,
        selected={"demo"},
    )
    assert generated_report["appliedProviders"] == ["demo"], generated_report
    generated_overrides = json.loads(
        (root / "provider-overrides.json").read_text(encoding="utf-8")
    )
    generated_entry = generated_overrides["provider_patches"]["demo"]
    generated_paths = [
        value
        for value in generated_entry.get("patch_scripts") or []
        if value.startswith("scripts/provider_patches/brain_runtime_terminal_resolution_")
    ]
    assert len(generated_paths) == 1, generated_entry
    generated_path = generated_paths[0]
    assert "scripts/provider_patches/demo_runtime_v1.py" in generated_entry["patch_scripts"]
    assert generated_path in generated_report["changedFiles"]
    generated_file = root / generated_path
    assert generated_file.is_file()

    namespace: dict[str, object] = {}
    generated_source = generated_file.read_text(encoding="utf-8")
    compile(generated_source, generated_path, "exec")
    exec(compile(generated_source, generated_path, "exec"), namespace)
    first = namespace["apply"](runtime_source)
    assert "return oldResolver();" not in first
    assert "return resolveTerminalMedia();" in first
    assert "STARTFIX:PROVIDER.BRAIN.RUNTIME.TERMINAL_RESOLUTION" in first
    assert namespace["apply"](first) == first

    import apply_provider_overrides as provider_overrides
    baseline = namespace["managed_fix_insertion_baseline"](runtime_source)
    provider_overrides._assert_v3_patch_ownership(
        runtime_source,
        first,
        generated_path,
        namespace["MANAGED_FIX_ID"],
        baseline,
    )

    # Simulate a later canonical current-byte state and evolve the same family.
    # The old content-addressed file stays immutable, while provider registration
    # moves to a new file and the stable ownership rectangle is edited in place.
    (root / "providers/demo.js").write_text(first, encoding="utf-8")
    evolution = {
        "scope": "provider_bloc",
        "operation": "upsert",
        "family": "terminal_resolution",
        "find": "resolveTerminalMedia()",
        "replace": "resolveTerminalMediaStrict()",
    }
    evolved_path, evolved_created = mod._apply_generated_bloc(
        "demo", generated_entry, evolution
    )
    assert evolved_created is True
    assert evolved_path != generated_path
    assert generated_file.is_file()
    active_generated = [
        value
        for value in generated_entry.get("patch_scripts") or []
        if value.startswith("scripts/provider_patches/brain_runtime_terminal_resolution_")
    ]
    assert active_generated == [evolved_path], generated_entry

    evolved_namespace: dict[str, object] = {}
    evolved_source = (root / evolved_path).read_text(encoding="utf-8")
    compile(evolved_source, evolved_path, "exec")
    exec(compile(evolved_source, evolved_path, "exec"), evolved_namespace)
    evolved = evolved_namespace["apply"](first)
    assert "resolveTerminalMediaStrict()" in evolved
    assert "resolveTerminalMedia()" not in evolved
    assert evolved_namespace["apply"](evolved) == evolved
    provider_overrides._assert_v3_patch_ownership(
        first,
        evolved,
        evolved_path,
        evolved_namespace["MANAGED_FIX_ID"],
    )

    try:
        mod._apply_generated_bloc(
            "demo",
            generated_entry,
            {
                "scope": "provider_bloc",
                "operation": "upsert",
                "family": "terminal_resolution",
                "find": "resolveTerminalMediaStrict()",
                "replace": "eval(payload)",
            },
        )
    except ValueError as exc:
        assert "forbidden runtime capability" in str(exc)
    else:
        raise AssertionError("generated Bloc introduced a forbidden runtime capability")

    try:
        mod._reject_placeholders("line\n/* clipped */")
    except ValueError as exc:
        assert "placeholder or synthetic" in str(exc)
    else:
        raise AssertionError("clipped Force mutation content was accepted")

    try:
        mod._reject_provider_bloc_semantic_collapse(
            "demo",
            'const response=await fetch(url,options);if(!response.ok)throw new Error("http");return response;',
            'if(row.referer&&!headers.Referer)headers.Referer=recipe.referer;',
        )
    except ValueError as exc:
        assert "return semantics" in str(exc)
    else:
        raise AssertionError("network helper return collapse was accepted")

    # Existing provider helper declarations are immutable under authored
    # Force edits: making a synchronous request parser async changes every
    # un-awaited caller from an object to a Promise and is not a body repair.
    original_js = "function req(a){return {tmdbId:a};}\nasync function resolve(a){var q=req(a);return q.tmdbId;}\n"
    safe_js = "function req(a){return {tmdbId:String(a)};}\nasync function resolve(a){var q=req(a);return q.tmdbId;}\n"
    mod._reject_function_signature_drift(original_js, safe_js, "demo", "demo.js")
    helper_addition = safe_js + "function newTerminalHelper(v){return v;}\n"
    mod._reject_function_signature_drift(original_js, helper_addition, "demo", "demo.js")
    async_drift = "async function req(a){return {tmdbId:a};}\nasync function resolve(a){var q=req(a);return q.tmdbId;}\n"
    try:
        mod._reject_function_signature_drift(original_js, async_drift, "demo", "demo.js")
    except ValueError as exc:
        assert "declaration/signature" in str(exc)
    else:
        raise AssertionError("sync-to-async helper drift was accepted")

    unsafe = {
        "scope": "provider_patch",
        "operation": "unified_diff",
        "path": "scripts/provider_patches/other_runtime_v1.py",
        "diff": (
            "--- a/scripts/provider_patches/other_runtime_v1.py\n"
            "+++ b/scripts/provider_patches/other_runtime_v1.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
    }
    try:
        mod._apply_file_mutation(
            "demo",
            updated["provider_patches"]["demo"],
            unsafe,
        )
    except ValueError as exc:
        assert "not a registered Bloc" in str(exc)
    else:
        raise AssertionError("unregistered provider Bloc mutation was accepted")


    mod.source_drift = lambda *_args, **_kwargs: ([], set())
    duplicate_payload = {
        **payload,
        "rows": [
            payload["rows"][0],
            {
                **payload["rows"][0],
                "mutationFingerprint": mod._fingerprint([
                    {
                        "scope": "provider_data",
                        "operation": "set",
                        "path": "notes",
                        "value": "alternate-candidate",
                    }
                ]),
                "mutationContextFingerprint": mod._mutation_context_fingerprint(
                    "demo",
                    updated["provider_patches"]["demo"],
                    [{
                        "scope": "provider_data",
                        "operation": "set",
                        "path": "notes",
                        "value": "alternate-candidate",
                    }],
                ),
                "mutations": [
                    {
                        "scope": "provider_data",
                        "operation": "set",
                        "path": "notes",
                        "value": "alternate-candidate",
                    }
                ],
            },
        ],
    }
    try:
        mod.apply_payload(
            duplicate_payload,
            current_sha="c" * 40,
            selected={"demo"},
        )
    except ValueError as exc:
        assert "multiple concrete Force candidates" in str(exc)
    else:
        raise AssertionError("stacked same-provider Force candidates were accepted")

    mod.source_drift = lambda *_args, **_kwargs: ([], {"demo"})
    unchanged = json.loads((root / "provider-overrides.json").read_text())
    report = mod.apply_payload(
        {
            **payload,
            "rows": [payload["rows"][0]],
        },
        current_sha="c" * 40,
        selected={"demo"},
    )
    assert report["appliedProviderCount"] == 0, report
    assert report["skipped"][0]["reason"] == "provider-drift-since-guidance"
    assert json.loads((root / "provider-overrides.json").read_text()) == unchanged

print("Brain LLM Force mutation bridge tests passed")
