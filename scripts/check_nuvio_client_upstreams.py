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
SOURCES_PATH = ROOT / "sources.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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


def path_matches(filename: str, rules: list[str]) -> bool:
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


def changed_lines(patch: str) -> str:
    lines: list[str] = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            lines.append(line[1:])
    return "\n".join(lines)


def semantic_hits(patch: str, tokens: list[str]) -> list[str]:
    changed = changed_lines(patch).casefold()
    return [token for token in tokens if str(token).casefold() in changed]


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
        contract_paths = row.get("contract_paths") or []
        semantic_paths = row.get("semantic_review_paths") or []
        semantic_tokens = row.get("semantic_review_tokens") or []
        if "/" not in repository:
            errors.append(f"{key}: invalid repository {repository!r}")
        if not branch:
            errors.append(f"{key}: missing branch")
        if len(verified_ref) != 40:
            errors.append(f"{key}: verified_ref must be a full 40-character SHA")
        if not isinstance(contract_paths, list) or not contract_paths:
            errors.append(f"{key}: contract_paths is empty")
        if not isinstance(semantic_paths, list):
            errors.append(f"{key}: semantic_review_paths must be a list")
        if semantic_paths and (not isinstance(semantic_tokens, list) or not semantic_tokens):
            errors.append(f"{key}: semantic_review_tokens is empty")

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


def is_infrastructure_transport_error(error: Exception | str) -> bool:
    """Classify transient transport failures without weakening drift review.

    Only explicit network/TLS/DNS signatures are treated as inconclusive. Git
    history divergence, missing contract refs, malformed configuration and any
    other unexpected failure remain blocking verification errors.
    """
    text = str(error).casefold()
    signatures = (
        "server certificate verification failed",
        "ssl certificate problem",
        "certificate verify failed",
        "tls handshake",
        "temporary failure in name resolution",
        "could not resolve host",
        "couldn't resolve host",
        "could not resolve hostname",
        "network is unreachable",
        "failed to connect",
        "connection timed out",
        "operation timed out",
        "connection reset by peer",
        "connection reset",
        "remote end hung up unexpectedly",
        "http 502",
        "http 503",
        "http 504",
    )
    return any(signature in text for signature in signatures)


def resilient_inspect_client(
    key: str, row: dict[str, Any], sources: dict[str, Any] | None = None
) -> dict[str, Any]:
    sources = sources or {}
    try:
        return inspect_client(key, row, sources)
    except Exception as error:
        if not is_infrastructure_transport_error(error):
            raise
        contract_ref = str(row.get("verified_ref") or "")
        return {
            "id": key,
            "repository": row.get("repository"),
            "branch": row.get("branch"),
            "verified_ref": contract_ref,
            "contract_ref": contract_ref,
            "accepted_ref": accepted_ref_for(sources, key, contract_ref),
            "current_head": None,
            "status": "verification_inconclusive",
            "review_required": False,
            "auto_advance_safe": False,
            "infrastructure_error": True,
            "error": f"{type(error).__name__}: {error}",
        }


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
        for ref, local in ((base, "base"), (head, "head")):
            run_git(
                [
                    "-c",
                    "protocol.version=2",
                    "fetch",
                    "--quiet",
                    "--no-tags",
                    "--filter=blob:none",
                    "--depth=128",
                    "origin",
                    ref,
                ],
                cwd=work,
                timeout=90,
            )
            fetched = run_git(["rev-parse", "FETCH_HEAD"], cwd=work).strip()
            run_git(["update-ref", f"refs/niakvio/{local}", fetched], cwd=work)

        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "refs/niakvio/base", "refs/niakvio/head"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        status = "ahead" if ancestry.returncode == 0 else "history_divergence"
        names = run_git(
            ["diff", "--name-only", "refs/niakvio/base", "refs/niakvio/head"],
            cwd=work,
            timeout=30,
        )
        files = [name.strip() for name in names.splitlines() if name.strip()]
        patches: dict[str, str] = {}
        for filename in files[:250]:
            patch = run_git(
                [
                    "diff",
                    "--unified=0",
                    "refs/niakvio/base",
                    "refs/niakvio/head",
                    "--",
                    filename,
                ],
                cwd=work,
                timeout=30,
            )
            patches[filename] = patch[:100_000]

    return {
        "status": status,
        "files": [{"filename": name} for name in files],
        "patches": patches,
    }


def compatibility_state(sources: dict[str, Any], key: str) -> dict[str, Any]:
    root = sources.get("nuvio_client_compatibility") or {}
    clients = root.get("clients") or {}
    row = clients.get(key) or {}
    return row if isinstance(row, dict) else {}


def accepted_ref_for(sources: dict[str, Any], key: str, contract_ref: str) -> str:
    state = compatibility_state(sources, key)
    accepted_ref = str(state.get("accepted_ref") or "")
    state_contract_ref = str(state.get("contract_ref") or "")
    if state_contract_ref == contract_ref and len(accepted_ref) == 40:
        return accepted_ref
    return contract_ref


def inspect_client(key: str, row: dict[str, Any], sources: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = sources or {}
    repository = str(row["repository"])
    branch = str(row["branch"])
    contract_ref = str(row["verified_ref"])
    accepted_ref = accepted_ref_for(sources, key, contract_ref)
    contract_rules = [str(value) for value in row.get("contract_paths") or []]
    semantic_rules = [str(value) for value in row.get("semantic_review_paths") or []]
    tokens = [str(value) for value in row.get("semantic_review_tokens") or []]
    head = current_head(repository, branch)
    result: dict[str, Any] = {
        "id": key,
        "repository": repository,
        "branch": branch,
        "verified_ref": contract_ref,
        "contract_ref": contract_ref,
        "accepted_ref": accepted_ref,
        "current_head": head,
        "platforms": row.get("platforms") or [],
        "status": "verified",
        "changed_file_count": 0,
        "contract_changed_files": [],
        "semantic_changed_files": [],
        "semantic_token_hits": {},
        "observed_sensitive_changed_files": [],
        "unrelated_changed_files": [],
        "review_required": False,
        "auto_advance_safe": False,
    }
    if head == accepted_ref:
        return result

    comparison = compare(repository, accepted_ref, head)
    status = str(comparison.get("status") or "unknown")
    patches = comparison.get("patches") or {}
    files = [
        str(item.get("filename") or "")
        for item in comparison.get("files") or []
        if isinstance(item, dict) and str(item.get("filename") or "")
    ]
    contract_changed = [name for name in files if path_matches(name, contract_rules)]
    semantic_candidates = [
        name for name in files if name not in contract_changed and path_matches(name, semantic_rules)
    ]
    semantic_hit_map: dict[str, list[str]] = {}
    for name in semantic_candidates:
        hits = semantic_hits(str(patches.get(name) or ""), tokens)
        if hits:
            semantic_hit_map[name] = hits
    semantic_changed = sorted(semantic_hit_map)
    observed_sensitive = [name for name in semantic_candidates if name not in semantic_hit_map]
    unrelated = [
        name
        for name in files
        if name not in contract_changed and name not in semantic_candidates
    ]

    result.update(
        {
            "compare_status": status,
            "changed_file_count": len(files),
            "contract_changed_files": contract_changed,
            "semantic_changed_files": semantic_changed,
            "semantic_token_hits": semantic_hit_map,
            "observed_sensitive_changed_files": observed_sensitive,
            "unrelated_changed_files": unrelated,
        }
    )

    if status == "ahead" and not contract_changed and not semantic_changed:
        result["status"] = "safe_advance_available"
        result["auto_advance_safe"] = True
        return result

    result["status"] = "contract_review_required"
    result["review_required"] = True
    reasons: list[str] = []
    if contract_changed:
        reasons.append("hard runtime contract paths changed")
    if semantic_changed:
        reasons.append("player/dependency changes touched runtime-sensitive semantics")
    if status != "ahead":
        reasons.append(f"history status is {status}")
    result["reasons"] = reasons or ["unclassified client repository drift"]
    return result


def annotation(kind: str, title: str, message: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        safe = message.replace("\n", "%0A")
        print(f"::{kind} title={title}::{safe}")


def apply_safe_state(
    sources: dict[str, Any],
    config: dict[str, Any],
    results: dict[str, dict[str, Any]],
    now: str,
) -> list[str]:
    root = sources.setdefault("nuvio_client_compatibility", {})
    root["schema_version"] = 1
    root["policy"] = "accepted_ref may advance automatically only when hard and semantic runtime contract checks remain unchanged"
    clients = root.setdefault("clients", {})
    advanced: list[str] = []

    for key, row in (config.get("clients") or {}).items():
        result = results[key]
        contract_ref = str(row.get("verified_ref") or "")
        state = clients.get(key)
        if not isinstance(state, dict) or str(state.get("contract_ref") or "") != contract_ref:
            state = {
                "contract_ref": contract_ref,
                "accepted_ref": contract_ref,
                "accepted_at": now,
                "acceptance": "contract-audited-baseline",
            }
            clients[key] = state

        if result.get("status") != "safe_advance_available":
            continue
        head = str(result.get("current_head") or "")
        if len(head) != 40:
            continue
        state.update(
            {
                "contract_ref": contract_ref,
                "accepted_ref": head,
                "accepted_at": now,
                "acceptance": "automatic-contract-safe-advance",
                "changed_file_count": int(result.get("changed_file_count") or 0),
                "observed_sensitive_changed_files": result.get("observed_sensitive_changed_files") or [],
                "unrelated_changed_files": result.get("unrelated_changed_files") or [],
            }
        )
        advanced.append(key)
    return advanced


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check official Nuvio client repositories for runtime-contract drift."
    )
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--sources", default=str(SOURCES_PATH))
    parser.add_argument(
        "--output",
        default=str(ROOT / "health-output" / "nuvio-client-upstream-status.json"),
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Report contract drift without a non-zero exit code.",
    )
    parser.add_argument(
        "--apply-safe-advance",
        action="store_true",
        help="Persist safe accepted_ref advances in sources.json. Never advances the audited contract_ref.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    sources_path = Path(args.sources)
    if not sources_path.is_absolute():
        sources_path = ROOT / sources_path

    config = load(config_path)
    sources = load(sources_path) if sources_path.is_file() else {}
    config_errors = validate_config(config)
    if config_errors:
        for error in config_errors:
            annotation("error", "Nuvio client upstream configuration", error)
        raise SystemExit(
            "Nuvio client upstream configuration invalid:\n- " + "\n- ".join(config_errors)
        )

    now = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "schema_version": 3,
        "generated_at": now,
        "transport": "git-ls-remote-plus-partial-tree-diff",
        "policy": config.get("policy") or {},
        "clients": {},
        "review_required": [],
        "safe_advance_available": [],
        "auto_advanced": [],
        "verified": [],
        "inconclusive": [],
    }

    failures: list[str] = []
    for key, row in (config.get("clients") or {}).items():
        try:
            result = resilient_inspect_client(str(key), row, sources)
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
            print(
                f"{key}: accepted head verified at {str(result.get('current_head'))[:12]} "
                f"(contract {str(result.get('contract_ref'))[:12]})"
            )
        elif status == "safe_advance_available":
            report["safe_advance_available"].append(key)
            print(
                f"{key}: safe upstream advance {str(result.get('accepted_ref'))[:12]} -> "
                f"{str(result.get('current_head'))[:12]}; contract paths unchanged"
            )
            annotation(
                "notice",
                "Nuvio client safe advance",
                f"{key} advanced without hard/semantic contract drift; eligible for automatic accepted_ref update.",
            )
        elif status == "verification_inconclusive":
            report["inconclusive"].append(key)
            message = f"{key}: upstream transport verification inconclusive; preserving accepted_ref"
            annotation("warning", "Nuvio client upstream check inconclusive", message)
            print(message)
        else:
            report["review_required"].append(key)
            hard = result.get("contract_changed_files") or []
            semantic = result.get("semantic_changed_files") or []
            message = f"{key}: {status}"
            if hard:
                message += "; hard contract files: " + ", ".join(hard[:12])
            if semantic:
                message += "; semantic-sensitive files: " + ", ".join(semantic[:12])
            if result.get("error"):
                message += "; " + str(result["error"])
            failures.append(message)
            annotation("error", "Nuvio client runtime re-audit required", message)
            print(message, file=sys.stderr)

    if args.apply_safe_advance and not failures and not report["inconclusive"]:
        advanced = apply_safe_state(sources, config, report["clients"], now)
        if advanced or "nuvio_client_compatibility" not in load(sources_path):
            dump(sources_path, sources)
        report["auto_advanced"] = advanced
        for key in advanced:
            report["clients"][key]["status"] = "auto_advanced"
            annotation(
                "notice",
                "Nuvio client baseline auto-advanced",
                f"{key} accepted_ref advanced to {report['clients'][key].get('current_head')}; audited contract_ref remains pinned.",
            )
            print(
                f"{key}: accepted_ref auto-advanced to "
                f"{str(report['clients'][key].get('current_head'))[:12]}"
            )

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
        f"safe={','.join(report['safe_advance_available']) or '-'}; "
        f"auto_advanced={','.join(report['auto_advanced']) or '-'}; "
        f"inconclusive={','.join(report['inconclusive']) or '-'}; "
        f"review_required={','.join(report['review_required']) or '-'}"
    )
    if failures and not args.no_fail:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
