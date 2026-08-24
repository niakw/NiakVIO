#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from provider_engine_normalizer import sanitize_provider_hooks, strip_foreign_provider_wrappers

ROOT = Path(__file__).resolve().parents[1]
OVR = ROOT / "provider-overrides.json"
MANIFESTS = [ROOT / "manifest.json"] + sorted(ROOT.glob("*/manifest.json"))
URL_RE = re.compile(r"https?://[^\s\"'`<>\\)]+", re.I)
HOST_RE = re.compile(r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)
INFRA = {
    "api.themoviedb.org", "raw.githubusercontent.com", "github.com", "www.github.com",
    "cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com", "image.tmdb.org",
    "api.github.com", "objects.githubusercontent.com",
}


def origin(url: str) -> str | None:
    try:
        parsed = urlparse(url.rstrip(".,;"))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None
        host = parsed.hostname.lower().strip(".")
        if host in INFRA or not HOST_RE.fullmatch(host):
            return None
        if any(token in host for token in ("${", "}", "_")):
            return None
        return f"{parsed.scheme}://{host}"
    except Exception:
        return None


def provider_owned_origins(provider_id: str, origins: list[str]) -> list[str]:
    key = re.sub(r"[^a-z0-9]", "", provider_id.lower())
    if len(key) < 4:
        return []
    owned: list[str] = []
    for value in origins:
        host = (urlparse(value).hostname or "").lower()
        normalized = re.sub(r"[^a-z0-9]", "", host)
        if key in normalized or normalized.split("www", 1)[-1].startswith(key):
            owned.append(value)
    return owned


def classify(item: dict, text: str, origins: list[str]) -> str:
    provider_id = str(item.get("id") or item.get("canonical_id") or "").casefold()
    if provider_id == "vidfast":
        return "iframe_player"
    lowered = text.lower()
    if item.get("supportsExternalPlayer") or any(token in lowered for token in ("postmessage", "<iframe", "/embed", "/e/")):
        return "mixed_embed_resolver"
    if any("/api/" in value or ((urlparse(value).hostname or "").startswith("api.")) for value in origins):
        return "api_stream_resolver"
    if any(token in lowered for token in (".m3u8", ".mp4", "master.m3u8")) and not any(
        token in lowered for token in ("cheerio", "queryselector", "htmlparser")
    ):
        return "direct_media"
    return "html_scraper"


def load_data() -> tuple[dict, list[dict[str, str]]]:
    if not OVR.exists():
        return {}, []
    loaded = json.loads(OVR.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return {}, []
    return sanitize_provider_hooks(loaded, ROOT)


def collect_published() -> dict[str, tuple[dict, Path]]:
    seen: dict[str, tuple[dict, Path]] = {}
    for manifest_path in MANIFESTS:
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for item in manifest.get("scrapers") or []:
            if not isinstance(item, dict):
                continue
            provider_id = str(item.get("id") or "").strip().casefold()
            filename = item.get("filename")
            if not provider_id or not isinstance(filename, str) or not filename:
                continue
            path = (manifest_path.parent / filename).resolve()
            if ROOT not in path.parents or not path.exists():
                continue
            seen.setdefault(provider_id, (item, path))
    return seen


def collect_staged(stage: Path) -> tuple[dict[str, tuple[dict, Path]], dict | None]:
    registry_path = stage / "candidates.json"
    if not registry_path.exists():
        return {}, None
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    seen: dict[str, tuple[dict, Path]] = {}
    for candidate in registry.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        provider_id = str(candidate.get("canonical_id") or "").strip().casefold()
        local_path = candidate.get("local_path")
        if not provider_id or not isinstance(local_path, str):
            continue
        path = (stage / local_path).resolve()
        if stage.resolve() not in path.parents or not path.exists():
            continue
        metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
        item = dict(metadata)
        item.setdefault("id", provider_id)
        item["canonical_id"] = provider_id
        seen.setdefault(provider_id, (item, path))
    return seen, registry


def validate_provider_file(path: Path) -> None:
    result = subprocess.run(
        ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = "\n".join(value.strip() for value in (result.stdout, result.stderr) if value.strip())
        raise ValueError(f"provider isolation migration produced invalid artifact {path}:\n{detail}")


def isolate_provider_bundles(data: dict, providers: dict[str, tuple[dict, Path]]) -> list[dict[str, str]]:
    removed: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    for provider_id, (_item, path) in sorted(providers.items()):
        if path in seen_paths:
            continue
        seen_paths.add(path)
        source = path.read_text(encoding="utf-8", errors="strict")
        cleaned, records = strip_foreign_provider_wrappers(source, provider_id, data)
        if cleaned == source:
            continue
        path.write_text(cleaned, encoding="utf-8")
        validate_provider_file(path)
        removed.extend({**record, "bundle": path.relative_to(ROOT).as_posix() if ROOT in path.parents else str(path)} for record in records)
    return removed


def build_profiles(data: dict, providers: dict[str, tuple[dict, Path]]) -> int:
    patches = data.setdefault("provider_patches", {})
    caps = data.setdefault("provider_capabilities", {})
    profiles = data.setdefault("patch_profiles", {})
    generated_names = {
        name for name in profiles
        if isinstance(name, str) and name.startswith("adaptive_domain_")
    }
    for name in generated_names:
        profiles.pop(name, None)
    for patch in patches.values():
        if not isinstance(patch, dict):
            continue
        selected = patch.get("profiles")
        if isinstance(selected, list):
            patch["profiles"] = [name for name in selected if name not in generated_names]

    for provider_id, (item, path) in sorted(providers.items()):
        provider_id = provider_id.casefold()
        text = path.read_text(encoding="utf-8", errors="ignore")
        origins: list[str] = []
        for url in URL_RE.findall(text):
            candidate = origin(url)
            if candidate and candidate not in origins:
                origins.append(candidate)
        existing = caps.get(provider_id) if isinstance(caps.get(provider_id), dict) else {}
        strategy = existing.get("strategy") or classify(item, text, origins)
        capability = dict(existing)
        capability.setdefault("strategy", strategy)
        capability.setdefault("validation", {
            "iframe_player": "embed_page",
            "mixed_embed_resolver": "provider_native",
            "api_stream_resolver": "api_and_provider_native",
            "direct_media": "media_url",
            "html_scraper": "provider_native",
        }.get(strategy, "provider_native"))
        capability.setdefault("allow_html_url", strategy in {"iframe_player", "mixed_embed_resolver", "html_scraper"})
        capability.setdefault("requires_direct_media", strategy == "direct_media")
        # Explicit inert quarantine bundles intentionally contain no runtime
        # origins. Preserve prior real-provider evidence only while the actual
        # quarantine wrapper is present. A historical quarantine filename alone
        # is provenance and must never freeze a recovered provider's live profile.
        explicit_inert_quarantine = "NUVIO_PROVIDER_QUARANTINE_V1" in text
        if origins or not explicit_inert_quarantine:
            capability["observed_origins"] = origins[:24]
        else:
            prior_origins = existing.get("observed_origins") if isinstance(existing.get("observed_origins"), list) else []
            capability["observed_origins"] = [str(value) for value in prior_origins if str(value)][:24]
        capability["generated_from_manifest_or_stage"] = True
        caps[provider_id] = capability
        patch = patches.setdefault(provider_id, {})
        patch.setdefault("capability", strategy)
        selected = patch.get("profiles")
        if isinstance(selected, list):
            patch["profiles"] = [name for name in selected if not str(name).startswith("adaptive_domain_")]
    return len(providers)


def reapply_stage(stage: Path, registry: dict) -> int:
    from apply_provider_overrides import apply_overrides
    changed = 0
    for candidate in registry.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        provider_id = str(candidate.get("canonical_id") or "").strip().casefold()
        local_path = candidate.get("local_path")
        if not provider_id or not isinstance(local_path, str):
            continue
        path = (stage / local_path).resolve()
        if stage.resolve() not in path.parents or not path.exists():
            continue
        original = path.read_bytes()
        patched, applied = apply_overrides(provider_id, original)
        if patched != original:
            path.write_bytes(patched)
            validate_provider_file(path)
            changed += 1
        candidate["sha256"] = hashlib.sha256(patched).hexdigest()
        current = candidate.get("local_patches") if isinstance(candidate.get("local_patches"), list) else []
        merged = []
        seen_patch_keys = set()
        for value in [*current, *applied]:
            key = json.dumps(value, sort_keys=True, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            if key in seen_patch_keys:
                continue
            seen_patch_keys.add(key)
            merged.append(value)
        candidate["local_patches"] = merged
    (stage / "candidates.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default=None, help="Also profile candidates in this staging directory.")
    parser.add_argument("--apply-stage", action="store_true", help="Reapply generated profiles to staged candidates immediately.")
    args = parser.parse_args()

    data, removed_hooks = load_data()
    providers = collect_published()
    stage_path: Path | None = None
    registry = None
    staged_count = 0
    if args.stage:
        stage_path = (ROOT / args.stage).resolve() if not Path(args.stage).is_absolute() else Path(args.stage).resolve()
        staged, registry = collect_staged(stage_path)
        staged_count = len(staged)
        providers.update(staged)

    removed_wrappers = isolate_provider_bundles(data, providers)
    count = build_profiles(data, providers)
    normalization = data.setdefault("provider_engine_normalization", {})
    normalization.update({
        "removed_cross_provider_hooks": len(removed_hooks),
        "removed_cross_provider_wrappers": len(removed_wrappers),
        "isolation_applied_before_profiles": True,
    })
    data["provider_profile_generation"] = {
        "schema_version": 4,
        "provider_count": count,
        "staged_provider_count": staged_count,
        "source": "manifest_published_bundles_and_current_staging",
        "same_deep_new_provider_support": True,
        "automatic_bundle_rewrite": False,
        "provider_backend_isolation": True,
    }
    OVR.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    repatched = 0
    if args.apply_stage:
        if stage_path is None or registry is None:
            raise SystemExit("--apply-stage requires --stage with candidates.json")
        repatched = reapply_stage(stage_path, registry)

    print(
        f"provider runtime profiles generated: {count} (staged={staged_count}, repatched={repatched}, "
        f"isolated_hooks={len(removed_hooks)}, isolated_wrappers={len(removed_wrappers)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
