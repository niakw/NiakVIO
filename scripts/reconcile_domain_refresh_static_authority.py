#!/usr/bin/env python3
"""Keep Provider-v3 static address authority aligned with Domain Refresh.

Domain Refresh owns the current provider site address. The durable static knowledge
is also consumed by targeted rematerialization, so a stale static officialSite or
knownSite must never overwrite a freshly resolved hub terminal later.

Only address-owned fields are changed. Route/proof evidence remains untouched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
STATIC = ROOT / "automation" / "provider-v3-static-knowledge.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def host(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    return (urlparse(raw).hostname or "").casefold().strip(".")


def rewrite_host(value: object, old_hosts: set[str], terminal: str) -> str:
    raw = str(value or "").strip()
    if not raw or host(raw) not in old_hosts:
        return raw
    old = urlparse(raw if "://" in raw else "https://" + raw)
    new = urlparse(terminal)
    if not new.hostname:
        return raw
    netloc = new.hostname
    if new.port:
        netloc += f":{new.port}"
    return urlunparse((new.scheme or old.scheme or "https", netloc, old.path, old.params, old.query, old.fragment))


def sync_model(model: dict[str, Any], patch: dict[str, Any]) -> list[str]:
    terminal = str(patch.get("official_site") or "").strip().rstrip("/")
    if not terminal or not host(terminal):
        return []
    old_hosts = {h for h in (host(model.get("officialSite")), host(model.get("knownSite"))) if h}
    changed: list[str] = []

    for key in ("officialSite", "knownSite"):
        if str(model.get(key) or "").strip().rstrip("/") != terminal:
            model[key] = terminal
            changed.append(key)

    official_hub = str(patch.get("official_hub") or "").strip()
    if official_hub and str(model.get("officialHub") or "").strip() != official_hub:
        model["officialHub"] = official_hub
        changed.append("officialHub")

    recipe = model.get("apiRecipe")
    if isinstance(recipe, dict):
        for key in ("referer", "referrer"):
            value = recipe.get(key)
            if value and host(value) in old_hosts:
                next_value = rewrite_host(value, old_hosts, terminal)
                if next_value != value:
                    recipe[key] = next_value
                    changed.append(f"apiRecipe.{key}")

    # Origins/observedUrls are address hints, not route proof. Replace only the
    # previous canonical site host; unrelated API/player origins remain intact.
    for key in ("origins", "observedUrls"):
        values = model.get(key)
        if not isinstance(values, list):
            continue
        next_values: list[Any] = []
        touched = False
        for value in values:
            if isinstance(value, str) and host(value) in old_hosts:
                rewritten = rewrite_host(value, old_hosts, terminal)
                next_values.append(rewritten)
                touched = touched or rewritten != value
            else:
                next_values.append(value)
        if key == "origins" and terminal not in [str(v).rstrip("/") for v in next_values if isinstance(v, str)]:
            next_values.insert(0, terminal)
            touched = True
        if touched:
            # Stable de-dup while preserving source order.
            seen: set[str] = set()
            deduped: list[Any] = []
            for value in next_values:
                identity = json.dumps(value, ensure_ascii=False, sort_keys=True)
                if identity in seen:
                    continue
                seen.add(identity)
                deduped.append(value)
            model[key] = deduped
            changed.append(key)

    return sorted(set(changed))


def selected_ids(args: argparse.Namespace, changes: dict[str, Any] | None) -> set[str]:
    out = {canon(value) for value in args.provider if canon(value)}
    if changes is not None:
        out.update(canon(value) for value in changes.get("changed") or [] if canon(value))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes")
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changes = load(Path(args.changes)) if args.changes else None
    scope = selected_ids(args, changes)
    if not scope:
        print("FIELD_DOMAIN_STATIC_AUTHORITY scope=- changed=0 providers=-")
        return 0

    overrides = load(OVERRIDES)
    static = load(STATIC)
    patches = overrides.get("provider_patches") or {}
    providers = static.get("providers") or {}
    if not isinstance(patches, dict) or not isinstance(providers, dict):
        raise SystemExit("provider patches/static providers object required")

    unknown = sorted(pid for pid in scope if pid not in patches or pid not in providers)
    if unknown:
        raise SystemExit("domain static authority missing provider state: " + ",".join(unknown))

    mutated: dict[str, list[str]] = {}
    for pid in sorted(scope):
        row = providers[pid]
        patch = patches[pid]
        if not isinstance(row, dict) or not isinstance(patch, dict):
            raise SystemExit(f"{pid}: invalid static/patch row")
        model = row.get("model")
        if not isinstance(model, dict):
            raise SystemExit(f"{pid}: static model missing")
        fields = sync_model(model, patch)
        if fields:
            mutated[pid] = fields

    if args.check and mutated:
        raise SystemExit("domain static authority drift: " + json.dumps(mutated, sort_keys=True))
    if mutated:
        write(STATIC, static)

    print(
        "FIELD_DOMAIN_STATIC_AUTHORITY "
        f"scope={','.join(sorted(scope))} changed={len(mutated)} "
        f"providers={','.join(sorted(mutated)) if mutated else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
