#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_nuvio_client_upstreams.py'
TEST = ROOT / 'tests' / 'nuvio_client_upstream_drift_guard_test.py'

source = SCRIPT.read_text(encoding='utf-8')

anchor = '''def repo_url(repository: str) -> str:\n    return f"https://github.com/{repository}.git"\n\n\n'''
insert = '''def repo_url(repository: str) -> str:\n    return f"https://github.com/{repository}.git"\n\n\ndef is_infrastructure_transport_error(error: Exception | str) -> bool:\n    """Classify transient transport failures without weakening drift review.\n\n    Only explicit network/TLS/DNS signatures are treated as inconclusive. Git\n    history divergence, missing contract refs, malformed configuration and any\n    other unexpected failure remain blocking verification errors.\n    """\n    text = str(error).casefold()\n    signatures = (\n        "server certificate verification failed",\n        "ssl certificate problem",\n        "certificate verify failed",\n        "tls handshake",\n        "temporary failure in name resolution",\n        "could not resolve host",\n        "couldn't resolve host",\n        "could not resolve hostname",\n        "network is unreachable",\n        "failed to connect",\n        "connection timed out",\n        "operation timed out",\n        "connection reset by peer",\n        "connection reset",\n        "remote end hung up unexpectedly",\n        "http 502",\n        "http 503",\n        "http 504",\n    )\n    return any(signature in text for signature in signatures)\n\n\ndef resilient_inspect_client(\n    key: str, row: dict[str, Any], sources: dict[str, Any] | None = None\n) -> dict[str, Any]:\n    sources = sources or {}\n    try:\n        return inspect_client(key, row, sources)\n    except Exception as error:\n        if not is_infrastructure_transport_error(error):\n            raise\n        contract_ref = str(row.get("verified_ref") or "")\n        return {\n            "id": key,\n            "repository": row.get("repository"),\n            "branch": row.get("branch"),\n            "verified_ref": contract_ref,\n            "contract_ref": contract_ref,\n            "accepted_ref": accepted_ref_for(sources, key, contract_ref),\n            "current_head": None,\n            "status": "verification_inconclusive",\n            "review_required": False,\n            "auto_advance_safe": False,\n            "infrastructure_error": True,\n            "error": f"{type(error).__name__}: {error}",\n        }\n\n\n'''
if 'def is_infrastructure_transport_error(' not in source:
    if anchor not in source:
        raise SystemExit('repo_url anchor missing')
    source = source.replace(anchor, insert, 1)

source = source.replace('''        "auto_advanced": [],\n        "verified": [],\n    }\n''', '''        "auto_advanced": [],\n        "verified": [],\n        "inconclusive": [],\n    }\n''', 1)

source = source.replace('''        try:\n            result = inspect_client(str(key), row, sources)\n        except Exception as error:\n''', '''        try:\n            result = resilient_inspect_client(str(key), row, sources)\n        except Exception as error:\n''', 1)

status_anchor = '''        elif status == "safe_advance_available":\n            report["safe_advance_available"].append(key)\n            print(\n                f"{key}: safe upstream advance {str(result.get('accepted_ref'))[:12]} -> "\n                f"{str(result.get('current_head'))[:12]}; contract paths unchanged"\n            )\n            annotation(\n                "notice",\n                "Nuvio client safe advance",\n                f"{key} advanced without hard/semantic contract drift; eligible for automatic accepted_ref update.",\n            )\n        else:\n'''
status_replacement = '''        elif status == "safe_advance_available":\n            report["safe_advance_available"].append(key)\n            print(\n                f"{key}: safe upstream advance {str(result.get('accepted_ref'))[:12]} -> "\n                f"{str(result.get('current_head'))[:12]}; contract paths unchanged"\n            )\n            annotation(\n                "notice",\n                "Nuvio client safe advance",\n                f"{key} advanced without hard/semantic contract drift; eligible for automatic accepted_ref update.",\n            )\n        elif status == "verification_inconclusive":\n            report["inconclusive"].append(key)\n            message = f"{key}: upstream transport verification inconclusive; preserving accepted_ref"\n            annotation("warning", "Nuvio client upstream check inconclusive", message)\n            print(message)\n        else:\n'''
if 'upstream transport verification inconclusive' not in source:
    if status_anchor not in source:
        raise SystemExit('status branch anchor missing')
    source = source.replace(status_anchor, status_replacement, 1)

source = source.replace(
    'if args.apply_safe_advance and not failures:',
    'if args.apply_safe_advance and not failures and not report["inconclusive"]:',
    1,
)

summary_anchor = '''        f"auto_advanced={','.join(report['auto_advanced']) or '-'}; "\n        f"review_required={','.join(report['review_required']) or '-'}"\n'''
summary_replacement = '''        f"auto_advanced={','.join(report['auto_advanced']) or '-'}; "\n        f"inconclusive={','.join(report['inconclusive']) or '-'}; "\n        f"review_required={','.join(report['review_required']) or '-'}"\n'''
if "f\"inconclusive={','.join(report['inconclusive'])" not in source:
    if summary_anchor not in source:
        raise SystemExit('summary anchor missing')
    source = source.replace(summary_anchor, summary_replacement, 1)

SCRIPT.write_text(source, encoding='utf-8')

test = TEST.read_text(encoding='utf-8')
insert_test = '''\n    assert module.is_infrastructure_transport_error(\n        RuntimeError("fatal: unable to access https://github.com/x/y: server certificate verification failed")\n    )\n    assert module.is_infrastructure_transport_error(\n        RuntimeError("fatal: unable to access https://github.com/x/y: Could not resolve host: github.com")\n    )\n    assert not module.is_infrastructure_transport_error(RuntimeError("history status is history_divergence"))\n\n    old_head = module.current_head\n    try:\n        module.current_head = lambda repository, branch: (_ for _ in ()).throw(\n            RuntimeError("server certificate verification failed")\n        )\n        inconclusive = module.resilient_inspect_client("client", sample(), sources("b" * 40))\n    finally:\n        module.current_head = old_head\n    assert inconclusive["status"] == "verification_inconclusive", inconclusive\n    assert inconclusive["review_required"] is False\n    assert inconclusive["auto_advance_safe"] is False\n    assert inconclusive["accepted_ref"] == "b" * 40\n    assert inconclusive["contract_ref"] == "a" * 40\n\n    old_head = module.current_head\n    try:\n        module.current_head = lambda repository, branch: (_ for _ in ()).throw(RuntimeError("logic exploded"))\n        try:\n            module.resilient_inspect_client("client", sample(), {})\n        except RuntimeError as error:\n            assert "logic exploded" in str(error)\n        else:\n            raise AssertionError("non-infrastructure verification error was incorrectly suppressed")\n    finally:\n        module.current_head = old_head\n'''
marker = '\n    payload: dict = {}\n'
if 'non-infrastructure verification error was incorrectly suppressed' not in test:
    if marker not in test:
        raise SystemExit('test insertion anchor missing')
    test = test.replace(marker, insert_test + marker, 1)
TEST.write_text(test, encoding='utf-8')

print('client upstream transport resilience migration applied')
