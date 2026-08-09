#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "automation" / "nuvio-client-upstreams.json"
PLATFORM_CONTRACTS = ROOT / "automation" / "platform-runtime-contracts.json"
TV_CONTRACT = ROOT / "automation" / "nuvio-tv-runtime-contract.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def run_git(args: list[str], *, cwd: Path | None = None, timeout: int = 45) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr.strip()[-1200:]
        raise RuntimeError(f"git {' '.join(args)} failed ({process.returncode}): {stderr}")
    return process.stdout


def is_sensitive(filename: str, rules: list[str]) -> bool:
    normalized = filename.strip().lstrip("/")
    for raw in rules:
        rule = str(raw or "").strip().lstrip("/")
        if not rule:
            continue
        if rule.endswith("/"):
            if normalized.startswith(rule):
                return True
        elif normalized == rule:
            return True
    return False


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    clients = config.get("clients") or {}
    if not isinstance(clients, dict) or not clients:
        return ["client upstream registry is empty"]

    platform = load(PLATFORM_CONTRACTS)
    platform_clients = platform.get("clients") or {}
    tv = load(TV_CONTRACT)

    for key, row in clients.items():
        if not isinstance(row, dict):
            errors.append(f"{key}: registry row is not an object")
            continue
        repository = str(row.get("repository") or "")
        branch = str(row.get("branch") or "")
        verified_ref = str(row.get("verified_ref") or "")
        sensitive = row.get("sensitive_paths") or []
        if "/" not in repository:
            errors.append(f"{key}: invalid repository {repository!r}")
        if not branch:
            errors.append(f"{key}: missing branch")
        if len(verified_ref) != 40:
            errors.append(f"{key}: verified_ref must be a full 40-character SHA")
        if not isinstance(sensitive, list) or not sensitive:
            errors.append(f"{key}: sensitive_paths is empty")

        if key == "nuvio-tv":
            if tv.get("source_repository") != repository:
                errors.append(f"{key}: TV contract repository mismatch")
            if tv.get("source_branch") != branch:
                errors.append(f"{key}: TV contract branch mismatch")
            if tv.get("source_ref") != verified_ref:
                errors.append(f"{key}: TV contract verified ref mismatch")
            continue

        matching = [
            value
            for value in platform_clients.values()
            if isinstance(value, dict) and value.get("source_repository") == repository
        ]
        if not matching:
            errors.append(f"{key}: no matching platform runtime contract")
            continue
        refs = {str(value.get("source_ref") or "") for value in matching}
        if refs != {verified_ref}:
            errors.append(f"{key}: platform contract refs differ from registry: {sorted(refs)}")
    return errors


def repo_url(repository: str) -> str:
    return f"https://github.com/{repository}.git"


def current_head(repository: str, branch: str) -> str:
    output = run_git(
        ["ls-remote", "--heads", repo_url(repository), f"refs/heads/{branch}"],
        timeout=30,
    )
    line = next((line for line in output.splitlines() if line.strip()), "")
    sha = line.split("\t", 1)[0].strip() if line else ""
    if len(sha) != 40:
        raise RuntimeError(f"{repository}@{branch}: could not resolve a full branch HEAD")
    return sha


def compare(repository: str, base: str, head: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="niakvio-client-drift-") as tmp:
        work = Path(tmp)
        run_git(["init", "--quiet"], cwd=work)
        run_git(["remote", "add", "origin", repo_url(repository)], cwd=work)
        run_git(
            [
                "-c",
                "protocol.version=2",
                "fetch",
                "--quiet",
                "--no-tags",
                "--filter=blob:none",
                "--depth=1",
                "origin",
                base,
            ],
            cwd=work,
            timeout=60,
        )
        base_sha = run_git(["rev-parse", "FETCH_HEAD"], cwd=work).strip()
        run_git(["update-ref", "refs/niakvio/base", base_sha], cwd=work)
        run_git(
            [
                "-c",
                "protocol.version=2",
                "fetch",
                "--quiet",
                "--no-tags",
                "--filter=blob:none",
                "--depth=1",
                "origin",
                head,
            ],
            cwd=work,
            timeout=60,
        )
        head_sha = run_git(["rev-parse", "FETCH_HEAD"], cwd=work).strip()
        run_git(["update-ref", "refs/niakvio/head", head_sha], cwd=work)
        names = run_git(
            ["diff", "--name-only", "refs/niakvio/base", "refs/niakvio/head"],
            cwd=work,
            timeout=30,
        )
    files = [name.strip() for name in names.splitlines() if name.strip()]
    return {
        "status": "tree_changed",
        "ahead_by": None,
        "behind_by": None,
        "total_commits": None,
        "files": [{"filename": name} for name in files],
    }


def inspect_client(key: str, row: dict[str, Any]) -> dict[str, Any]:
    repository = str(row["repository"])
    branch = str(row["branch"])
    verified_ref = str(row["verified_ref"])
    rules = [str(value) for value in row.get("sensitive_paths") or []]
    head = current_head(repository, branch)
    result: dict[str, Any] = {
        "id": key,
        "repository": repository,
        "branch": branch,
        "verified_ref": verified_ref,
        "current_head": head,
        "platforms": row.get("platforms") or [],
        "status": "verified",
        "changed_file_count": 0,
        "sensitive_changed_files": [],
        "unrelated_changed_files": [],
        "review_required": False,
    }
    if head == verified_ref:
        return result

    comparison = compare(repository, verified_ref, head)
    status = str(comparison.get("status") or "unknown")
    files = [
        str(item.get("filename") or "")
        for item in comparison.get("files") or []
        if isinstance(item, dict) and str(item.get("filename") or "")
    ]
    sensitive = [name for name in files if is_sensitive(name, rules)]
    unrelated = [name for name in files if name not in sensitive]

    result.update(
        {
            "compare_status": status,
            "changed_file_count": len(files),
            "sensitive_changed_files": sensitive,
            "unrelated_changed_files": unrelated,
        }
    )

    if status in {"ahead", "tree_changed"} and not sensitive:
        result["status"] = "advanced_unrelated"
        return result

    result["status"] = "contract_review_required"
    result["review_required"] = True
    reasons: list[str] = []
    if sensitive:
        reasons.append("contract-sensitive paths changed")
    if status not in {"ahead", "tree_changed"}:
        reasons.append(f"history status is {status}")
    result["reasons"] = reasons or ["unclassified client repository drift"]
    return result


def annotation(kind: str, title: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", "%0A")
        print(f"::{kind} title={title}::{safe}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check official Nuvio client repositories for runtime-contract drift."
    )
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument(
        "--output",
        default=str(ROOT / "health-output" / "nuvio-client-upstream-status.json"),
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Report sensitive drift without a non-zero exit code.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    config = load(config_path)
    config_errors = validate_config(config)
    if config_errors:
        for error in config_errors:
            annotation("error", "Nuvio client upstream configuration", error)
        raise SystemExit(
            "Nuvio client upstream configuration invalid:\n- " + "\n- ".join(config_errors)
        )

    report: dict[str, Any] = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transport": "git-ls-remote-plus-partial-tree-diff",
        "policy": config.get("policy") or {},
        "clients": {},
        "review_required": [],
        "advanced_unrelated": [],
        "verified": [],
    }

    failures: list[str] = []
    for key, row in (config.get("clients") or {}).items():
        try:
            result = inspect_client(str(key), row)
        except Exception as error:
            result = {
                "id": key,
                "repository": row.get("repository"),
                "branch": row.get("branch"),
                "verified_ref": row.get("verified_ref"),
                "status": "verification_error",
                "review_required": True,
                "error": f"{type(error).__name__}: {error}",
            }
        report["clients"][key] = result
        status = result.get("status")
        if status == "verified":
            report["verified"].append(key)
            print(f"{key}: verified at {str(result.get('current_head'))[:12]}")
        elif status == "advanced_unrelated":
            report["advanced_unrelated"].append(key)
            print(
                f"{key}: repository advanced, but no tracked runtime/plugin/player path changed"
            )
            annotation(
                "notice",
                "Nuvio client repository advanced",
                f"{key} advanced without contract-sensitive changes; verified baseline remains pinned.",
            )
        else:
            report["review_required"].append(key)
            sensitive = result.get("sensitive_changed_files") or []
            message = f"{key}: {status}"
            if sensitive:
                message += "; sensitive files: " + ", ".join(sensitive[:12])
            if result.get("error"):
                message += "; " + str(result["error"])
            failures.append(message)
            annotation("error", "Nuvio client runtime re-audit required", message)
            print(message, file=sys.stderr)

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        "Nuvio client upstream drift check: "
        f"verified={','.join(report['verified']) or '-'}; "
        f"advanced_unrelated={','.join(report['advanced_unrelated']) or '-'}; "
        f"review_required={','.join(report['review_required']) or '-'}"
    )
    if failures and not args.no_fail:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
