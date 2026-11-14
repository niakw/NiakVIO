#!/usr/bin/env python3
"""Diagnose reusable NiakVIO Legos against exact pinned, terminal-positive upstream cases.

This is an independent bounded *oracle* for Brain: it does not publish a
provider, repair provider code manually or trust a returned URL as media.
Source evidence is current upstream terminal media; a historical Lego is a
hypothesis, not an accepted fix. No URL, token or response body is persisted.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rotating_corpus import fixture_by_slug  # noqa: E402
import run_provider_upstream_parity_v3 as parity3  # noqa: E402

DEFAULT_CONFIG = ROOT / "automation/provider-intake-lego-oracle.json"
DEFAULT_REPORT = ROOT / "automation/provider-intake-lego-oracle-report.json"
ALLOWED_REPOS = {"NuvioPlugin/All-in-One-Nuvio", "Gowaru/gowaru-nuvio-providers"}


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def inputs(config: Path) -> list[dict[str, Any]]:
    value = json.loads(config.read_text(encoding="utf-8"))
    if int(value.get("schemaVersion") or 0) != 1:
        raise ValueError("invalid oracle schema")
    evidence = json.loads((ROOT / str(value["sourceEvidence"])).read_text(encoding="utf-8"))
    if evidence.get("promotionsAllowed") or evidence.get("promotionAllowed") is not False:
        raise ValueError("upstream evidence must not authorize promotion")
    positive = {
        (cid(row.get("id")), str(row.get("region")))
        for row in evidence.get("providerResults") or []
        if int(row.get("terminalPositiveTasks") or 0) > 0
    }
    pinned = json.loads((ROOT / "automation/provider-intake-top-global-france.json").read_text(encoding="utf-8"))
    sources = {
        (cid(row.get("id")), str(row.get("region"))): row.get("source") or {}
        for row in pinned.get("providers") or []
    }
    result = []
    for row in value.get("providers") or []:
        pid = cid(row.get("id"))
        region = str(row.get("region") or "")
        key = (pid, region)
        if key not in positive or key not in sources:
            raise ValueError(f"{pid}: oracle requires prior terminal-positive evidence")
        lego = str(row.get("lego") or "")
        if not re.fullmatch(r"scripts/provider_patches/[a-z0-9_]+[.]py", lego):
            raise ValueError(f"{pid}: untrusted patch path")
        local = (ROOT / lego).resolve()
        if ROOT / "scripts/provider_patches" not in local.parents:
            raise ValueError(f"{pid}: patch escaped allowlisted directory")
        if not local.is_file():
            raise ValueError(f"{pid}: missing trusted local patch")
        if str(row.get("mode")) not in {"resolver", "replace-export"}:
            raise ValueError(f"{pid}: unsupported diagnostic mode")
        for fixture in row.get("fixtures") or []:
            if not isinstance(fixture, str) or not re.fullmatch(r"[a-z0-9-]{4,95}", fixture):
                raise ValueError(f"{pid}: malformed fixture")
            fixture_by_slug(fixture)
        src = sources[key]
        if src.get("repository") not in ALLOWED_REPOS or not re.fullmatch(r"[a-f0-9]{40}", str(src.get("sha") or "")):
            raise ValueError(f"{pid}: source is not immutable pinned upstream")
        result.append({**row, "source": src, "id": pid, "region": region})
    if not result or len(result) != len({(x["id"], x["region"]) for x in result}):
        raise ValueError("empty or duplicate oracle source")
    return result


def clean_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "terminal": bool(result.get("terminal_verified")),
        "terminalCount": max(0, int(result.get("stream_count") or 0)),
        "candidateCount": max(0, int(result.get("candidate_stream_count") or 0)),
        "kinds": [str(k)[:30] for k in result.get("terminal_kinds") or []][:5],
        "httpStatuses": [int(n) for n in result.get("http_statuses") or [] if isinstance(n, int)][:8],
        "errorClass": str(result.get("error_class") or "")[:80] or None,
        "timeout": bool(result.get("timeout")),
    }


def compile_lego(row: dict[str, Any], directory: Path) -> Path:
    path = ROOT / row["lego"]
    name = "niakvio_oracle_" + row["id"].replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load local Lego")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if row["mode"] == "resolver":
        # Production resolves this hook through its Provider v3 Core wrapper.
        # The diagnostic shim exists only to isolate the Lego's own network
        # traversal from compilation/materialization/client behavior.
        source = """module.exports={getStreams:async function(){
          var resolver=globalThis.__niakvioProviderRuntimeResolverV1;
          if (!resolver || typeof resolver.resolve!=='function') return [];
          return await resolver.resolve(arguments);
        }};"""
    else:
        source = "module.exports={getStreams:async function(){return []}};"
    patched = module.apply(source, options=dict(row.get("options") or {}))
    if not isinstance(patched, str) or len(patched) <= len(source) or len(patched) > 600_000:
        raise RuntimeError("invalid Lego patch output")
    target = directory / f"niakvio-lego-{row['id']}.js"
    target.write_text(patched, encoding="utf-8")
    syntax = subprocess.run(["node", "--check", str(target)], cwd=ROOT, text=True, capture_output=True, timeout=15)
    if syntax.returncode != 0:
        raise RuntimeError("compiled Lego syntax rejected")
    return target


def pinned_source(row: dict[str, Any], directory: Path) -> Path:
    source = row["source"]
    url = f"https://raw.githubusercontent.com/{source['repository']}/{source['sha']}/{source['file']}"
    req = urllib.request.Request(url, headers={"User-Agent": "NiakVIO-Lego-Oracle/1"})
    with urllib.request.urlopen(req, timeout=22) as response:
        payload = response.read(900_001)
    if len(payload) > 900_000:
        raise RuntimeError("upstream too large for oracle")
    target = directory / f"upstream-{row['id']}.js"
    target.write_bytes(payload)
    syntax = subprocess.run(["node", "--check", str(target)], cwd=ROOT, capture_output=True, text=True, timeout=15)
    if syntax.returncode != 0:
        raise RuntimeError("upstream script syntax rejected")
    return target


def one(row: dict[str, Any], directory: Path, timeout: int) -> dict[str, Any]:
    result = {
        "provider": row["id"],
        "region": row["region"],
        "legos": [row["lego"]],
        "sourceSha": row["source"]["sha"],
        "fixtures": [],
        "status": "inconclusive",
        "publicationEligible": False,
    }
    try:
        local = compile_lego(row, directory)
        upstream = pinned_source(row, directory)
    except Exception as exc:
        result["status"] = "compile_or_source_failure"
        result["stageError"] = type(exc).__name__[:90]
        return result
    for fixture_slug in row["fixtures"]:
        f = fixture_by_slug(fixture_slug)
        lane = f["lane"]
        a = parity3.fixture_payload(f, lane, upstream=False)
        b = parity3.fixture_payload(f, lane, upstream=True)
        try:
            local_res = clean_result(parity3._run_verified(local, a, timeout))
            upstream_res = clean_result(parity3._run_verified(upstream, b, timeout))
        except Exception as exc:
            local_res, upstream_res = {}, {}
            stage_error = type(exc).__name__[:90]
        else:
            stage_error = None
        result["fixtures"].append({
            "slug": fixture_slug,
            "lane": lane,
            "localLego": local_res,
            "upstream": upstream_res,
            "stageError": stage_error,
        })
    pairs = result["fixtures"]
    local_positive = sum(bool(x["localLego"].get("terminal")) for x in pairs)
    upstream_positive = sum(bool(x["upstream"].get("terminal")) for x in pairs)
    result["localPositiveTasks"] = local_positive
    result["upstreamPositiveTasks"] = upstream_positive
    result["status"] = (
        "lego_terminal_observed_requires_native_acceptance" if local_positive > 0
        else "upstream_positive_lego_zero_brain_reconstruction_gap" if upstream_positive > 0
        else "both_zero_or_transport_inconclusive"
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    rows = inputs(args.config)
    if args.dry_run:
        print("FIELD_LEGO_ORACLE_PREFLIGHT " + ",".join(row["id"] for row in rows), flush=True)
        return 0
    result = []
    with tempfile.TemporaryDirectory(prefix="niakvio-lego-oracle-") as directory:
        for row in rows:
            # Completely independent temporary bytes per provider, not applied
            # or selected by the current release.
            result.append(one(row, Path(directory), max(10, min(args.timeout, 65))))
            print(
                f"FIELD_LEGO_ORACLE provider={row['id']} status={result[-1]['status']} "
                f"local_terminal={result[-1].get('localPositiveTasks', 0)} "
                f"upstream_terminal={result[-1].get('upstreamPositiveTasks', 0)}",
                flush=True,
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "schemaVersion": 1,
        "date": "2026-11-14",
        "mode": "ephemeral-local-lego-versus-current-upstream",
        "productionMutation": False,
        "providerPromotion": False,
        "nativePlaybackProven": False,
        "providers": result,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
