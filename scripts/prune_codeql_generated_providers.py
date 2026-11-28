#!/usr/bin/env python3
"""Prune retained generated provider versions from the CodeQL workspace only."""
from __future__ import annotations
import argparse, json
from pathlib import Path

MANIFESTS=("manifest.json","vf/manifest.json","no-anime/manifest.json","vf-no-anime/manifest.json")


def _manifest_provider_path(root: Path, manifest_relative: str, filename: str) -> str:
    """Resolve a manifest-relative provider filename without permitting escape.

    Root manifests normally store providers/x.js while nested vf/no-anime
    manifests legitimately store ../providers/x.js. Security scope is based on
    the resolved repository path, not on whether the serialized path contains ..
    """
    raw=str(filename or "").strip().replace("\\","/")
    if not raw:
        return ""
    path=Path(raw)
    if path.is_absolute() or path.suffix!=".js":
        raise ValueError(f"{manifest_relative}: invalid provider filename {raw!r}")
    repo=root.resolve()
    manifest=(repo/manifest_relative).resolve()
    try:
        manifest.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"{manifest_relative}: manifest escaped repository") from exc
    resolved=(manifest.parent/path).resolve()
    try:
        relative=resolved.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"{manifest_relative}: provider path escaped repository {raw!r}") from exc
    normalized=relative.as_posix()
    parts=relative.parts
    if len(parts)==2 and parts[0] in {"provider-disabled","provider-old"}:
        return normalized
    if len(parts)!=2 or parts[0]!="providers":
        raise ValueError(f"{manifest_relative}: unexpected published-provider path {raw!r}")
    return normalized


def published_provider_paths(root:Path)->set[str]:
    active:set[str]=set()
    root=root.resolve()
    for relative in MANIFESTS:
        manifest=root/relative
        data=json.loads(manifest.read_text(encoding="utf-8"))
        rows=data.get("scrapers") if isinstance(data,dict) else None
        if not isinstance(rows,list):
            raise ValueError(f"{relative}: scrapers must be a list")
        for row in rows:
            if not isinstance(row,dict):
                continue
            filename=str(row.get("filename") or "").strip()
            if not filename:
                continue
            normalized=_manifest_provider_path(root,relative,filename)
            if normalized.startswith("provider-disabled/") or normalized.startswith("provider-old/"):
                continue
            active.add(normalized)
    if not active:
        raise ValueError("production manifests expose no provider JS")
    missing=sorted(path for path in active if not (root/path).is_file())
    if missing:
        raise FileNotFoundError("published provider JS missing: "+",".join(missing[:10]))
    return active


def prune_workspace(root:Path)->tuple[int,int]:
    root=root.resolve()
    active=published_provider_paths(root)
    provider_root=root/"providers"
    removed=0
    for path in sorted(provider_root.glob("*.js")):
        if path.is_file() and path.relative_to(root).as_posix() not in active:
            path.unlink()
            removed+=1
    remaining={path.relative_to(root).as_posix() for path in provider_root.glob("*.js") if path.is_file()}
    if remaining!=active:
        raise RuntimeError("CodeQL active-provider projection does not equal production manifests")
    return len(active),removed


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path("."))
    args=ap.parse_args()
    active,removed=prune_workspace(args.root.resolve())
    print(
        f"FIELD_CODEQL_ACTIVE_PROVIDER_SCOPE active={active} "
        f"retained_removed_from_workspace={removed} repository_retention_unchanged=true"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
