#!/usr/bin/env python3
"""Record and validate resumable Android-TV native route evidence.

A checkpoint is reusable only when the exact route inputs still match: fixture,
manifest bytes, official NuvioTV commit, provider scope, stream scope and route-log
bytes. A timeout/failure is recorded for diagnostics but is never reusable as a
completed proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def client_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip().lower()
    if len(value) != 40:
        raise ValueError(f"invalid client commit SHA: {value!r}")
    return value


def identity(args: argparse.Namespace) -> dict[str, Any]:
    manifest = args.manifest.resolve()
    client_root = args.client_root.resolve()
    if not manifest.is_file():
        raise FileNotFoundError(manifest)
    if not client_root.is_dir():
        raise FileNotFoundError(client_root)
    return {
        "fixture": args.fixture,
        "manifestSha256": sha256_file(manifest),
        "clientSha": client_sha(client_root),
        "providerScope": args.provider_scope,
        "streamScope": args.stream_scope,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def record(args: argparse.Namespace) -> int:
    log = args.log.resolve()
    statuses = {
        "runtime": args.runtime_status,
        "collection": args.collection_status,
        "coverage": args.coverage_status,
        "readerObserved": args.reader_status,
    }
    complete = log.is_file() and log.stat().st_size > 0 and all(value == 0 for value in statuses.values())
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        **identity(args),
        "complete": complete,
        "statuses": statuses,
        "logSha256": sha256_file(log) if log.is_file() and log.stat().st_size > 0 else None,
    }
    atomic_write_json(args.checkpoint.resolve(), payload)
    print(
        "FIELD_NATIVE_TV_ROUTE_CHECKPOINT_RECORDED "
        f"fixture={args.fixture} complete={str(complete).lower()} runtime={args.runtime_status} "
        f"collection={args.collection_status} coverage={args.coverage_status} reader={args.reader_status}"
    )
    return 0


def verify(args: argparse.Namespace) -> int:
    checkpoint = args.checkpoint.resolve()
    log = args.log.resolve()
    reason = "ok"
    valid = False
    try:
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        expected = identity(args)
        if not isinstance(payload, dict) or payload.get("schemaVersion") != SCHEMA_VERSION:
            reason = "schema_mismatch"
        elif payload.get("complete") is not True:
            reason = "checkpoint_incomplete"
        elif any(payload.get(key) != value for key, value in expected.items()):
            reason = "input_identity_mismatch"
        elif not log.is_file() or log.stat().st_size <= 0:
            reason = "route_log_missing"
        elif payload.get("logSha256") != sha256_file(log):
            reason = "route_log_hash_mismatch"
        else:
            statuses = payload.get("statuses") or {}
            if not isinstance(statuses, dict) or any(int(statuses.get(key, 1)) != 0 for key in ("runtime", "collection", "coverage", "readerObserved")):
                reason = "status_not_complete"
            else:
                valid = True
    except FileNotFoundError:
        reason = "checkpoint_missing"
    except (json.JSONDecodeError, OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        reason = f"invalid_checkpoint_{type(exc).__name__}"

    print(
        "FIELD_NATIVE_TV_ROUTE_CHECKPOINT_VERIFY "
        f"fixture={args.fixture} reusable={str(valid).lower()} reason={reason}"
    )
    return 0 if valid else 1


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--provider-scope", required=True)
    parser.add_argument("--stream-scope", required=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify")
    common(verify_parser)

    record_parser = subparsers.add_parser("record")
    common(record_parser)
    record_parser.add_argument("--runtime-status", type=int, required=True)
    record_parser.add_argument("--collection-status", type=int, required=True)
    record_parser.add_argument("--coverage-status", type=int, required=True)
    record_parser.add_argument("--reader-status", type=int, required=True)

    args = parser.parse_args()
    if args.command == "verify":
        return verify(args)
    return record(args)


if __name__ == "__main__":
    raise SystemExit(main())
