#!/usr/bin/env python3
"""Apply the repository-wide playback-integrity upgrade.

This is a deterministic migration, not a provider blacklist. It:
- adds HLS master-audio preservation and bounded playlist validation to every
  published provider that declares or contains HLS handling;
- hardens the VF catalogue fallback against empty/unknown metadata and fuzzy
  cross-title matches;
- makes the new regression tests part of the normal npm test suite.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"
VF_RECOVERY = ROOT / "scripts/provider_patches/vf_catalogue_recovery.py"
PACKAGE = ROOT / "package.json"

AUDIO_PATCH = "scripts/provider_patches/hls_master_audio_preserver_v1.py"
HLS_PATCH = "scripts/provider_patches/hls_runtime_integrity_v1.py"
VF_PATCH = "scripts/provider_patches/vf_catalogue_recovery.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hls_provider(entry: dict) -> bool:
    formats = entry.get("formats") or []
    if isinstance(formats, str):
        formats = [formats]
    if any(str(v).casefold() in {"m3u8", "hls", "mpegurl", "application/vnd.apple.mpegurl"} for v in formats):
        return True
    filename = str(entry.get("filename") or "")
    path = (ROOT / filename).resolve()
    if ROOT not in path.parents or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").casefold()
    return any(marker in text for marker in (".m3u8", "#extm3u", "mpegurl", "/hls/", "/hls2/"))


def upgrade_overrides() -> tuple[int, list[str]]:
    cfg = load(OVERRIDES)
    manifest = load(MANIFEST)
    provider_patches = cfg.setdefault("provider_patches", {})
    changed = 0
    targets: list[str] = []

    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict) or not hls_provider(entry):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        targets.append(provider_id)
        specific = provider_patches.setdefault(provider_id, {})
        scripts = specific.get("patch_scripts")
        if scripts is None:
            scripts = []
            specific["patch_scripts"] = scripts
        if not isinstance(scripts, list):
            raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
        for patch in (AUDIO_PATCH, HLS_PATCH):
            if patch not in scripts:
                scripts.append(patch)
                changed += 1
        options = specific.setdefault("patch_script_options", {})
        if not isinstance(options, dict):
            raise ValueError(f"provider_patches.{provider_id}.patch_script_options must be an object")
        wanted = {"timeout_ms": 6500, "max_children": 2}
        if options.get(HLS_PATCH) != wanted:
            options[HLS_PATCH] = wanted
            changed += 1

    cfg["playback_integrity_policy"] = {
        "version": 1,
        "provider_disabling_is_not_a_repair": True,
        "hls_targets": sorted(set(targets)),
        "hls_master_external_audio": "preserve_master_playlist",
        "hls_payload_validation": "top_level_plus_bounded_child_and_audio_playlist",
        "conclusive_invalid_stream_action": "drop_stream_not_provider",
        "inconclusive_network_action": "preserve_stream",
        "vf_catalogue_identity": "tmdb_metadata_plus_strict_title_year_match",
        "unknown_metadata_action": "return_no_recovery_match",
    }
    dump(OVERRIDES, cfg)
    return changed, sorted(set(targets))


def upgrade_vf_recovery() -> int:
    text = VF_RECOVERY.read_text(encoding="utf-8")
    original = text

    if '"implementationVersion": 2,' not in text:
        text = text.replace(
            '    payload = {\n',
            '    payload = {\n        "implementationVersion": 2,\n',
            1,
        )

    text = text.replace('    if(!title&&req.tmdbId){', '    if(req.tmdbId){', 1)
    text = text.replace(
        'if(data){title=clean(data.title||data.name);original=clean(data.original_title||data.original_name);',
        'if(data){title=clean(data.title||data.name)||title;original=clean(data.original_title||data.original_name);',
        1,
    )

    strict_score = r'''  function significant(v){
    var noise={film:1,films:1,movie:1,movies:1,serie:1,series:1,streaming:1,watch:1,regarder:1,voir:1,vf:1,vff:1,vfq:1,vostfr:1,vo:1,hd:1,full:1,complet:1,complete:1,saison:1,season:1,episode:1,ep:1,french:1,francais:1};
    return normalize(v).split(" ").filter(function(x){return x.length>1&&!noise[x]});
  }
  function score(label,meta,url){
    var a=normalize(label),wanted=normalize(meta.title),original=normalize(meta.original),urlText=normalize(url);
    if(!a||(!wanted&&!original))return -100;
    if(meta.year){
      var years=String(label||"").match(/\b(?:19|20)\d{2}\b/g)||[];
      if(years.length&&years.indexOf(String(meta.year))<0)return -100;
    }
    function one(title){
      if(!title)return -100;
      if(a===title)return 120;
      var wantedWords=significant(title),labelWords=significant(a),hay=significant(a+" "+urlText);
      if(!wantedWords.length)return -100;
      var all=wantedWords.every(function(x){return hay.indexOf(x)>=0});
      if(!all)return -100;
      var extras=labelWords.filter(function(x){return wantedWords.indexOf(x)<0});
      if(extras.length>Math.max(4,wantedWords.length+2))return -100;
      return extras.length<=2?92:84;
    }
    var s=Math.max(one(wanted),one(original));
    if(s<0)return s;
    if(meta.year&&String(label+" "+url).indexOf(String(meta.year))>=0)s+=15;
    return s;
  }
  function links'''

    pattern = re.compile(r"  function score\(label,meta,url\)\{[\s\S]*?\n  \}\n  function links")
    text, count = pattern.subn(lambda _match: strict_score, text, count=1)
    if count != 1 and "function significant(v)" not in text:
        raise ValueError("could not locate VF catalogue score function")
    text = text.replace("if(s>=38)rows.push", "if(s>=80)rows.push", 1)

    if text != original:
        VF_RECOVERY.write_text(text, encoding="utf-8")
        return 1
    return 0


def upgrade_package_test() -> int:
    package = load(PACKAGE)
    scripts = package.setdefault("scripts", {})
    test = str(scripts.get("test") or "")
    additions = [
        "python3 tests/hls_playback_integrity_test.py",
        "python3 tests/vf_catalogue_identity_hardening_test.py",
        "python3 tests/language_manifest_metadata_consistency_test.py",
    ]
    changed = False
    for command in additions:
        if command not in test:
            test = (test + " && " + command).strip(" &")
            changed = True
    if changed:
        scripts["test"] = test
        dump(PACKAGE, package)
        return 1
    return 0


def main() -> int:
    override_changes, targets = upgrade_overrides()
    vf_changes = upgrade_vf_recovery()
    package_changes = upgrade_package_test()
    print(
        "playback integrity migration complete: "
        f"hls_targets={len(targets)} override_changes={override_changes} "
        f"vf_source_changed={vf_changes} package_changed={package_changes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
