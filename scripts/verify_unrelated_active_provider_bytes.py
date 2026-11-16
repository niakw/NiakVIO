#!/usr/bin/env python3
"""Capture/verify proof-bound active provider bytes across provider onboarding.\n\nSingle or bulk onboarding may create/replace only request targets. Existing active\nproviders outside the request are publication evidence and must not be rematerialized\nmerely to satisfy a global formatting/minimizer invariant.\n"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (("global", ROOT / "manifest.json"), ("france", ROOT / "vf" / "manifest.json"))


def canon(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_targets(path: Path) -> set[str]:
    raw = load(path)
    if isinstance(raw, dict):
        if isinstance(raw.get("providers"), list):
            rows = raw.get("providers") or []
        elif raw.get("id") or raw.get("provider"):
            rows = [raw]
        else:
            rows = []
    else:
        rows = raw if isinstance(raw, list) else []
    return {
        canon(row.get("id") or row.get("provider"))
        for row in rows
        if isinstance(row, dict) and canon(row.get("id") or row.get("provider"))
    }


def manifest_file(manifest_path: Path, filename: str) -> Path:
    resolved = (manifest_path.parent / filename).resolve()
    resolved.relative_to(ROOT.resolve())
    return resolved


def current_rows() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for scope, manifest_path in MANIFESTS:
        payload = load(manifest_path)
        for row in payload.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            pid = canon(row.get("id"))
            if not pid:
                continue
            out[f"{scope}:{pid}"] = {
                "scope": scope,
                "provider": pid,
                "enabled": row.get("enabled") is not False,
                "filename": str(row.get("filename") or ""),
                "manifest": str(manifest_path.relative_to(ROOT)),
            }
    return out


def capture(request: Path, baseline: Path) -> dict[str, Any]:
    targets = request_targets(request)
    rows = current_rows()
    protected: list[dict[str, Any]] = []
    for key, row in sorted(rows.items()):
        if not row["enabled"] or row["provider"] in targets:
            continue
        manifest_path = ROOT / row["manifest"]
        path = manifest_file(manifest_path, row["filename"])
        if not path.is_file():
            raise SystemExit(f"{key}: active provider artifact missing: {row['filename']}")
        if "providers" not in path.parts or "provider-disabled" in path.parts:
            raise SystemExit(f"{key}: active provider artifact is not in providers/: {row['filename']}")
        protected.append({**row, "sha256": digest(path)})
    payload = {
        "schemaVersion": 1,
        "role": "bulk-onboarding-unrelated-active-byte-baseline",
        "publicationAuthority": False,
        "requestTargets": sorted(targets),
        "protected": protected,
    }
    baseline.parent.mkdir(parents=True, exist_ok=True)
    baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_BULK_ACTIVE_BYTE_BASELINE protected={len(protected)} targets={len(targets)}")
    return payload


def verify(baseline: Path) -> None:
    payload = load(baseline)
    rows = current_rows()
    failures: list[str] = []
    protected = payload.get("protected") or []
    for prior in protected:
        if not isinstance(prior, dict):
            continue
        key = f"{prior.get('scope')}:{canon(prior.get('provider'))}"
        now = rows.get(key)
        if not now:
            failures.append(f"{key}: manifest row disappeared")
            continue
        if not now["enabled"]:
            failures.append(f"{key}: unrelated active provider became disabled")
        if now["filename"] != prior.get("filename"):
            failures.append(f"{key}: filename drift {prior.get('filename')} -> {now['filename']}")
            continue
        manifest_path = ROOT / str(prior.get("manifest") or "")
        path = manifest_file(manifest_path, now["filename"])
        if not path.is_file():
            failures.append(f"{key}: provider artifact missing")
            continue
        actual = digest(path)
        if actual != str(prior.get("sha256") or ""):
            failures.append(f"{key}: exact provider bytes changed")
    if failures:
        raise SystemExit("bulk onboarding mutated unrelated active provider bytes:\n" + "\n".join(failures))
    print(f"FIELD_BULK_ACTIVE_BYTE_STABILITY_OK protected={len(protected)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.capture == args.verify:
        raise SystemExit("choose exactly one of --capture or --verify")
    if args.capture:
        capture(args.request, args.baseline)
    else:
        verify(args.baseline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
