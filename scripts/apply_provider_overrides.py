#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply durable provider overrides and reusable structural patch profiles.

Stable literal/domain replacements are applied during discovery and promotion.
Structural profiles can declare ``phase: runtime``; those profiles are only
applied by the deep-repair loop after a matching runtime failure signature has
been observed. This keeps the build provider-agnostic while preventing blind
rewrites of every downloaded bundle.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"


def load_overrides() -> dict[str, Any]:
    if not CONFIG.exists():
        return {}
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value


def _load_patch_module(patch_script: str, provider_id: str):
    patch_path = (ROOT / str(patch_script)).resolve()
    if ROOT not in patch_path.parents or not patch_path.is_file():
        raise ValueError(f"invalid provider patch script: {patch_script}")
    module_name = (
        f"nuvio_provider_patch_{provider_id}_"
        f"{hashlib.sha256(str(patch_path).encode()).hexdigest()[:8]}"
    )
    spec = importlib.util.spec_from_file_location(module_name, patch_path)
    if not spec or not spec.loader:
        raise ValueError(f"cannot load provider patch script: {patch_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_matches(text: str, profile: dict[str, Any]) -> bool:
    """Return whether a profile's structural capability markers match a bundle."""
    all_markers = [str(v) for v in profile.get("detect_all") or []]
    any_markers = [str(v) for v in profile.get("detect_any") or []]
    none_markers = [str(v) for v in profile.get("detect_none") or []]
    if all_markers and not all(marker in text for marker in all_markers):
        return False
    if any_markers and not any(marker in text for marker in any_markers):
        return False
    if none_markers and any(marker in text for marker in none_markers):
        return False
    return bool(all_markers or any_markers or profile.get("auto_apply"))


def _apply_patch_script(
    text: str,
    provider_id: str,
    patch_script: str,
    options: dict[str, Any],
    profile_name: str | None,
) -> str:
    module = _load_patch_module(patch_script, provider_id)
    apply_fn = getattr(module, "apply", None)
    if not callable(apply_fn):
        raise ValueError(f"provider patch {patch_script} has no callable apply()")
    kwargs = {
        "options": options,
        "context": {"provider_id": provider_id, "profile": profile_name},
    }
    signature = inspect.signature(apply_fn)
    if "options" in signature.parameters or any(
        parameter.kind == parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        result = apply_fn(text, **kwargs)
    else:
        result = apply_fn(text)
    if not isinstance(result, str):
        raise TypeError(f"provider patch {patch_script} must return str")
    return result


def _normalize_profile_names(values: Iterable[str] | None) -> set[str]:
    return {str(value) for value in (values or []) if str(value).strip()}



def _replace_named_function(text: str, function_name: str, replacement: str) -> tuple[str, bool]:
    """Replace a classic named JavaScript function using balanced braces."""
    import re

    match = re.search(rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = brace
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char in "\r\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char in ("'", '"', "`"):
                quote = char
            elif char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[:start] + replacement + text[index + 1 :], True
        index += 1
    raise ValueError(f"unterminated function body: {function_name}")


def _apply_fixed_endpoint(text: str, provider_id: str, config: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    fixed = config.get("fixed_endpoint")
    if not isinstance(fixed, dict):
        return text, None
    function_name = str(fixed.get("resolver_function") or "").strip()
    api = str(fixed.get("api") or "").rstrip("/")
    referer = str(fixed.get("referer") or "").rstrip("/") + "/"
    if not function_name or not api:
        raise ValueError(f"provider_patches.{provider_id}.fixed_endpoint is incomplete")
    marker = f"NUVIO_FIXED_ENDPOINT:{api}"
    if marker in text:
        return text, None
    replacement = (
        f"function {function_name}(){{"
        f"/* {marker} */"
        f"return Promise.resolve({{api:{json.dumps(api)},referer:{json.dumps(referer)}}});"
        "}"
    )
    output, changed = _replace_named_function(text, function_name, replacement)
    if not changed:
        return text, None
    return output, {
        "type": "fixed_endpoint",
        "resolver_function": function_name,
        "api": api,
        "referer": referer,
    }


def _inject_runtime_domain_overrides(text: str, replacements: dict[str, Any]) -> tuple[str, int]:
    """Embed host rewriting into the provider JavaScript artifact itself."""
    from urllib.parse import urlparse

    rules: dict[str, str] = {}
    for old, new in replacements.items():
        old_value = str(old).lower().strip().rstrip("/")
        new_value = str(new).lower().strip().rstrip("/")
        old_host = urlparse(old_value).hostname if "://" in old_value else old_value
        new_host = urlparse(new_value).hostname if "://" in new_value else new_value
        if old_host and new_host and old_host != new_host:
            rules[old_host] = new_host
    if not rules:
        return text, 0
    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"
    if marker in text:
        return text, 0
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
    return bootstrap + text, len(rules)



def _strip_legacy_global_stream_guards(text: str) -> tuple[str, int]:
    """Remove the obsolete one-size-fits-all output guards.

    Playback semantics are provider-capability specific. The global guards
    changed iframe players, direct-media providers and API resolvers in the same
    way, which could make valid results disappear in Nuvio. Only the appended
    markers owned by this repository are removed; provider source code is left
    untouched.
    """
    pattern = re.compile(
        r"\n?/\* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V(?:1|2|3) \*/[\s\S]*$",
        re.MULTILINE,
    )
    output, count = pattern.subn("", text)
    return output.rstrip() + ("\n" if output else ""), count


def apply_overrides(
    provider_id: str,
    data: bytes,
    *,
    phase: str = "discovery",
    profile_names: Iterable[str] | None = None,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Apply stable replacements and profiles allowed for the selected phase.

    ``profile_names`` is used by the runtime repair engine to request an exact
    provider-agnostic strategy after its failure signature has matched. Passing
    explicit names never bypasses structural capability detection.
    """
    config = load_overrides()
    text = data.decode("utf-8")
    applied: list[dict[str, Any]] = []
    provider_id = provider_id.casefold()
    specific = (config.get("provider_patches") or {}).get(provider_id, {})
    if not isinstance(specific, dict):
        raise ValueError(f"provider_patches.{provider_id} must be an object")

    replacements = dict(config.get("domain_replacements") or {})
    replacements.update(specific.get("replacements") or {})
    replacements.update(specific.get("route_replacements") or {})
    for old, new in replacements.items():
        old_text, new_text = str(old), str(new)
        count = text.count(old_text)
        if count:
            text = text.replace(old_text, new_text)
            applied.append(
                {
                    "type": "replace",
                    "from": old_text,
                    "to": new_text,
                    "count": count,
                    "phase": phase,
                }
            )

    text, fixed_record = _apply_fixed_endpoint(text, provider_id, specific)
    if fixed_record:
        fixed_record["phase"] = phase
        applied.append(fixed_record)

    runtime_replacements = specific.get("runtime_domain_replacements") or {}
    if not isinstance(runtime_replacements, dict):
        raise ValueError(f"provider_patches.{provider_id}.runtime_domain_replacements must be an object")
    text, runtime_rule_count = _inject_runtime_domain_overrides(text, runtime_replacements)
    if runtime_rule_count:
        applied.append({"type": "runtime_domain_overrides", "count": runtime_rule_count, "phase": phase})

    profiles = config.get("patch_profiles") or {}
    if not isinstance(profiles, dict):
        raise ValueError("patch_profiles must be an object")

    explicitly_requested = _normalize_profile_names(profile_names)
    explicitly_requested.update(str(value) for value in (specific.get("profiles") or []))
    unknown = explicitly_requested - set(profiles)
    if unknown:
        raise ValueError("unknown patch profile(s): " + ", ".join(sorted(unknown)))

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        profile_phase = str(profile.get("phase") or "discovery")
        requested = profile_name in explicitly_requested
        automatic = bool(profile.get("auto_apply")) and profile_phase == phase
        if not (requested or automatic):
            continue
        if not profile_matches(text, profile):
            if requested:
                # A requested runtime strategy that does not match the bundle is
                # a normal non-applicable repair, not a build-wide exception.
                continue
            continue
        patch_script = profile.get("patch_script")
        if not patch_script:
            raise ValueError(f"patch profile {profile_name} has no patch_script")
        options = dict(profile.get("options") or {})
        options.setdefault("detect_all", profile.get("detect_all") or [])
        options.setdefault("detect_any", profile.get("detect_any") or [])
        before = text
        text = _apply_patch_script(
            text,
            provider_id,
            str(patch_script),
            options,
            str(profile_name),
        )
        if text != before:
            applied.append(
                {
                    "type": "patch_profile",
                    "profile": str(profile_name),
                    "path": str(patch_script),
                    "phase": profile_phase,
                }
            )

    # Legacy per-provider hooks remain supported only for existing repositories.
    # New structural repairs belong in reusable patch_profiles.
    patch_script = specific.get("patch_script")
    if patch_script and phase == "discovery":
        before = text
        text = _apply_patch_script(
            text,
            provider_id,
            str(patch_script),
            dict(specific.get("patch_options") or {}),
            None,
        )
        if text != before:
            applied.append(
                {"type": "patch_script", "path": str(patch_script), "phase": phase}
            )

    text, removed_guards = _strip_legacy_global_stream_guards(text)
    if removed_guards:
        applied.append({"type": "remove_legacy_global_stream_guard", "count": removed_guards, "phase": phase})
    return text.encode("utf-8"), applied


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
