#!/usr/bin/env python3
"""Recover manifest/cache regressions and harden automatic provider promotion."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_provider_overrides import apply_overrides  # noqa: E402


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing patch anchor: {label}")
    return text.replace(old, new, 1)


def bump_patch(value: object) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def patch_worker() -> None:
    path = ROOT / "scripts/provider_worker.cjs"
    text = path.read_text(encoding="utf-8")
    marker = "NUVIO_NON_MEDIA_ASSET_GUARD_V1"
    if marker in text:
        return
    guard = r'''
// NUVIO_NON_MEDIA_ASSET_GUARD_V1
// A technically valid media payload is not sufficient when it is a social,
// store or decorative asset unrelated to the requested title.
function isNonMediaAssetHost(host) {
  const value = String(host || '').toLowerCase();
  const exact = new Set([
    'play-games.googleusercontent.com',
    'play-lh.googleusercontent.com',
    'video.twimg.com',
    'pbs.twimg.com',
  ]);
  return exact.has(value)
    || value.endsWith('.twimg.com')
    || (value.endsWith('.googleusercontent.com') && /^(play-games|play-lh)\./.test(value));
}

'''
    text = replace_once(
        text,
        "function sanitizeStream(stream) {",
        guard + "function sanitizeStream(stream) {",
        "worker sanitizer function",
    )
    anchor = "  const url = typeof stream.url === 'string' ? stream.url.trim() : '';\n  if (!url) return { stream: null, disallowed: null };\n"
    replacement = anchor + (
        "  let streamHost = '';\n"
        "  try { streamHost = new URL(url).hostname.toLowerCase(); } "
        "catch { return { stream: null, disallowed: 'invalid_stream_url' }; }\n"
        "  if (isNonMediaAssetHost(streamHost)) "
        "return { stream: null, disallowed: 'non_media_asset_host' };\n"
    )
    text = replace_once(text, anchor, replacement, "worker stream URL validation")
    path.write_text(text, encoding="utf-8")


def patch_runtime_repair() -> None:
    path = ROOT / "scripts/runtime_repair.py"
    text = path.read_text(encoding="utf-8")
    if "required_category_playable_proof" in text:
        return
    anchor = "\ndef compare_results(parent: dict[str, Any], repaired: dict[str, Any]) -> tuple[bool, str]:\n"
    helper = '''\ndef _fixture_categories(result: dict[str, Any], key: str) -> set[str]:
    evidence = result.get("evidence") or {}
    return {
        str(value).casefold()
        for value in evidence.get(key) or []
        if str(value).strip()
    }


'''
    text = replace_once(text, anchor, helper + anchor, "runtime compare function")
    target = '    if malformed_request_count(repaired) > malformed_request_count(parent):\n        return False, "introduced_malformed_request"\n\n'
    insert = '''    required_categories = _fixture_categories(repaired, "required_fixture_categories")
    healthy_categories = _fixture_categories(repaired, "healthy_fixture_categories")
    if required_categories and not required_categories.issubset(healthy_categories):
        missing = sorted(required_categories - healthy_categories)
        return False, "required_category_playable_proof:" + ",".join(missing)

'''
    text = replace_once(text, target, target + insert, "runtime category proof")
    path.write_text(text, encoding="utf-8")


def patch_stream_sanitizer() -> None:
    path = ROOT / "scripts/provider_patches/stream_output_sanitizer.py"
    text = path.read_text(encoding="utf-8")
    if '"implementationVersion": 5' not in text:
        anchor = '            "blockedPathPatterns": blocked_paths,\n'
        text = replace_once(
            text,
            anchor,
            anchor + '            "implementationVersion": 5,\n',
            "sanitizer implementation version",
        )
    if "NUVIO_EMBED_HTML_ALLOWLIST_V1" not in text:
        old = r'''      if(/\.(?:js|mjs|css|json|xml|txt|html?|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;'''
        new = r'''      // NUVIO_EMBED_HTML_ALLOWLIST_V1
      // External-player pages often legitimately end in .html. Preserve them
      // only when their path has an explicit player/embed/watch role.
      var embedLike=/\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path);
      if(/\.(?:js|mjs|css|json|xml|txt|map|woff2?|ttf|otf|ico|jpe?g|png|gif|webp|svg)(?:$|[?#])/i.test(path))return true;
      if(/\.html?(?:$|[?#])/i.test(path)&&!embedLike)return true;'''
        text = replace_once(text, old, new, "sanitizer HTML player rule")
    path.write_text(text, encoding="utf-8")


def write_regression_test() -> None:
    path = ROOT / "tests/provider_repair_promotion_guard_test.py"
    path.write_text(
        '''#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from runtime_repair import compare_results

parent = {"status": "no_streams", "score": 10, "evidence": {"streams_playable": 0}, "tests": []}
false_positive = {
    "status": "healthy",
    "score": 72,
    "evidence": {
        "streams_playable": 1,
        "required_fixture_categories": ["movie", "anime"],
        "healthy_fixture_categories": ["movie"],
    },
    "tests": [{"streams_playable": 1}],
}
accepted, reason = compare_results(parent, false_positive)
assert not accepted and reason == "required_category_playable_proof:anime", (accepted, reason)
root = Path(__file__).resolve().parents[1]
worker = (root / "scripts/provider_worker.cjs").read_text(encoding="utf-8")
sanitizer = (root / "scripts/provider_patches/stream_output_sanitizer.py").read_text(encoding="utf-8")
assert "NUVIO_NON_MEDIA_ASSET_GUARD_V1" in worker
assert "non_media_asset_host" in worker
assert '"implementationVersion": 5' in sanitizer
assert "NUVIO_EMBED_HTML_ALLOWLIST_V1" in sanitizer
assert "embedLike" in sanitizer
print("provider repair promotion guard tests passed")
''',
        encoding="utf-8",
    )


def manifest_paths() -> tuple[Path, Path]:
    return ROOT / "manifest.json", ROOT / "vf/manifest.json"


def correct_manifest_state() -> dict[str, str]:
    main_path, vf_path = manifest_paths()
    rollbacks = {
        "french-manga": "french-manga--nuvio--b088114476c8e08f.js",
        "voiranime-rip": "voiranime-rip--published-baseline--cbf14d7c8fe2e76e.js",
    }
    desired_versions: dict[str, str] = {}
    for manifest_path, prefix in ((main_path, "providers/"), (vf_path, "../providers/")):
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        seen: set[str] = set()
        for provider in data.get("scrapers", []):
            provider_id = str(provider.get("id") or "").casefold()
            if provider_id in {"goated", "purstream", "wookafr"}:
                seen.add(provider_id)
                was_enabled = bool(provider.get("enabled"))
                provider["enabled"] = True
                if provider_id == "goated" and str(provider.get("version")) == "1.0.0":
                    provider["version"] = "1.0.1"
                elif not was_enabled:
                    provider["version"] = bump_patch(provider.get("version"))
                desired_versions[provider_id] = str(provider.get("version"))
            if provider_id in rollbacks:
                seen.add(provider_id)
                target = prefix + rollbacks[provider_id]
                changed = bool(provider.get("enabled")) or str(provider.get("filename") or "") != target
                provider["enabled"] = False
                provider["filename"] = target
                if changed:
                    provider["version"] = bump_patch(provider.get("version"))
                desired_versions[provider_id] = str(provider.get("version"))
        missing = {"goated", "purstream", "wookafr"} - seen
        if missing:
            raise RuntimeError(f"{manifest_path}: protected providers missing: {sorted(missing)}")
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for filename in rollbacks.values():
        if not (ROOT / "providers" / filename).is_file():
            raise RuntimeError(f"missing rollback bundle: {filename}")
    return desired_versions


def repatch_sanitized_bundles() -> dict[str, str]:
    main_path, vf_path = manifest_paths()
    main = json.loads(main_path.read_text(encoding="utf-8"))
    changed: dict[str, tuple[str, str]] = {}

    for provider in main.get("scrapers", []):
        provider_id = str(provider.get("id") or "").casefold()
        filename = str(provider.get("filename") or "")
        source = ROOT / filename
        if not provider_id or not source.is_file():
            continue
        source_text = source.read_text(encoding="utf-8", errors="strict")
        if "NUVIO_STREAM_OUTPUT_SANITIZER_V4" not in source_text:
            continue
        patched, _records = apply_overrides(provider_id, source.read_bytes(), phase="discovery")
        if patched == source.read_bytes():
            continue
        digest = hashlib.sha256(patched).hexdigest()
        safe_id = re.sub(r"[^a-z0-9._-]+", "-", provider_id).strip("-") or "provider"
        target_name = f"{safe_id}--repatched--{digest[:16]}.js"
        target = ROOT / "providers" / target_name
        target.write_bytes(patched)
        new_version = bump_patch(provider.get("version"))
        provider["filename"] = f"providers/{target_name}"
        provider["version"] = new_version
        changed[provider_id] = (target_name, new_version)

    main_path.write_text(json.dumps(main, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    vf = json.loads(vf_path.read_text(encoding="utf-8"))
    for provider in vf.get("scrapers", []):
        provider_id = str(provider.get("id") or "").casefold()
        if provider_id in changed:
            target_name, new_version = changed[provider_id]
            provider["filename"] = f"../providers/{target_name}"
            provider["version"] = new_version
    vf_path.write_text(json.dumps(vf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {provider_id: version for provider_id, (_filename, version) in changed.items()}


def write_cineby_report() -> None:
    historical = "00d235578083b3b87870ceabfc9639ccdbb7e839"
    historical_path = "providers/cineby--nuvio--a423440cec70666c.js"
    result = subprocess.run(
        ["git", "show", f"{historical}:{historical_path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    temp = ROOT / ".cineby-historical.js"
    temp.write_bytes(result.stdout)
    fixture = json.dumps({
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
        "label": "Interstellar (2014)",
        "category": "movie",
    })
    context = json.dumps({
        "locale": "fr-FR",
        "language": "fr",
        "languages": ["fr-FR", "fr", "en"],
        "platform": "android",
        "settings": {},
        "storage": {},
        "maxSettingsProfiles": 8,
    })
    worker = subprocess.run(
        ["node", "--max-old-space-size=1024", "scripts/provider_worker.cjs", str(temp), fixture, context],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
    )
    payload: dict[str, object] = {}
    for line in worker.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            payload = json.loads(line.split("=", 1)[1])
    temp.unlink(missing_ok=True)
    report = {
        "historical_commit": historical,
        "historical_version": "1.9.2",
        "fixture": "Interstellar (2014)",
        "worker_ok": bool(payload.get("ok")),
        "streams_returned": len(payload.get("streams") or []),
        "restored": False,
        "reason": "historical_bundle_returned_no_streams" if not payload.get("streams") else "playback_not_reverified",
    }
    output = ROOT / "automation/cineby-recovery.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    patch_worker()
    patch_runtime_repair()
    patch_stream_sanitizer()
    write_regression_test()
    state_versions = correct_manifest_state()
    repatched = repatch_sanitized_bundles()
    write_cineby_report()
    print("protected versions:", json.dumps(state_versions, sort_keys=True))
    print("repatched bundles:", json.dumps(repatched, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
